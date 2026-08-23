#!/usr/bin/env python3
"""The Gold Regions, 1865 — asset pipeline.

W.W. de Lacy's map of Montana Territory, drawn for its First Legislature the
year after the territory was created: "showing the gulch or placer diggings
actually worked and districts where quartz (gold & silver) lodes have been
discovered to January 1st 1865."  Scanned by the Library of Congress at
8,984 × 6,634 px.  The sheet is georeferenced from its own 1° graticule —
line positions found by comb-matched ink profiles, the degree labelling
resolved automatically by testing which assignment lays the surveyed state
boundary along the map's heavy territory line — and draped over the montana
sheet's grid: the terrain, and the height texture itself, are shared with
`montana/` verbatim, because the footprint is the same state.

Mines come along as data: gold and silver producers from the USGS Mineral
Resources Data System (MRDS), fetched over WFS and thinned to the strongest
site per few kilometres.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import io, json, math, os, re, shutil, sys, urllib.request, zipfile

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('GO_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
MONTANA = os.path.join(REPO, 'montana', 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
from proj import Lcc, poly_basis
from georef import Fit, fit_report, overlay
from encode import Grid, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS

SCAN_URL = 'https://tile.loc.gov/storage-services/service/gmd/gmd425/g4251/g4251h/ct001858.jp2'
CENSUS = 'https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_500k.zip'
WFS = ('https://mrdata.usgs.gov/wfs/mrds?service=WFS&version=2.0.0&request=GetFeature'
       '&typenames=mrds&count=5000&startindex=%d'
       '&bbox=44.30,-116.20,49.05,-104.00,urn:ogc:def:crs:EPSG::4326')

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

# the montana sheet's grid, reused verbatim
LCC = Lcc(45.0, 49.0, -109.5)
MMETA = json.load(open(os.path.join(MONTANA, 'meta.json')))
def make_grid():
    g = MMETA['grid']
    return Grid(LCC, g['X0'], g['X1'], g['Y0'], g['Y1'], 3584)

# ------------------------------------------------------------------ stage 1
def fetch():
    dst = path('scan.jpg')
    if not os.path.exists(dst):
        p('· downloading the 1865 map from the Library of Congress…')
        req = urllib.request.Request(SCAN_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=600) as r:
            open(path('scan.jp2'), 'wb').write(r.read())
        Image.open(path('scan.jp2')).convert('RGB').save(dst, quality=96)
    else:
        p('· scan cached')
    if not os.path.exists(path('mt_boundary.json')):
        p('· downloading the surveyed state boundary (US Census 2021)…')
        req = urllib.request.Request(CENSUS, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=180) as r:
            z = zipfile.ZipFile(io.BytesIO(r.read()))
        d = path('states'); os.makedirs(d, exist_ok=True); z.extractall(d)
        import shapefile
        sf = shapefile.Reader(os.path.join(d, 'cb_2021_us_state_500k.shp'))
        i = [k for k, rec in enumerate(sf.records()) if rec['NAME'] == 'Montana'][0]
        sh = sf.shape(i)
        json.dump({'points': [[round(x, 6), round(y, 6)] for x, y in sh.points],
                   'parts': list(sh.parts)}, open(path('mt_boundary.json'), 'w'))
    if not os.path.exists(path('mrds.json')):
        p('· fetching MRDS sites over WFS…')
        sites, start = [], 0
        while True:
            req = urllib.request.Request(WFS % start,
                                         headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=300) as r:
                gml = r.read().decode('utf-8', 'replace')
            members = re.findall(r'<wfs:member>(.*?)</wfs:member>', gml, re.S)
            for m in members:
                pos = re.search(r'<gml:pos>([-\d.]+) ([-\d.]+)</gml:pos>', m)
                name = re.search(r'<ms:site_name>(.*?)</ms:site_name>', m)
                stat = re.search(r'<ms:dev_stat>(.*?)</ms:dev_stat>', m)
                code = re.search(r'<ms:code_list>(.*?)</ms:code_list>', m)
                if pos and stat and code:
                    sites.append(dict(lat=float(pos.group(1)), lon=float(pos.group(2)),
                                      n=(name.group(1) if name else '').strip(),
                                      s=stat.group(1).strip(), c=code.group(1).strip()))
            p('  … %d sites' % (start + len(members)))
            if len(members) < 5000: break
            start += 5000
        json.dump(sites, open(path('mrds.json'), 'w'))
    else:
        p('· MRDS cached')

def boundary_ring():
    b = json.load(open(path('mt_boundary.json')))
    pts = np.array(b['points']); parts = list(b['parts']) + [len(pts)]
    rings = [pts[parts[i]:parts[i+1]] for i in range(len(parts)-1)]
    rings.sort(key=len, reverse=True)
    return rings[0]

# ------------------------------------------------------------------ stage 2
def _peaks_1d(profile, min_gap, k=1.6):
    base = ndimage.median_filter(profile, 151)
    r = profile - base
    thr = k*float(np.std(r))
    out = []
    for i in range(3, len(r)-3):
        if r[i] > thr and r[i] == r[i-3:i+4].max():
            if not out or i-out[-1] >= min_gap: out.append(i)
    return np.array(out), r

def _comb(peaks, d_range, n_min):
    """Arithmetic comb through 1-D peaks; returns (d, [(k, pos), …]) where k
    is the integer tooth index of each matched peak (gaps allowed)."""
    best = None
    for i in range(len(peaks)):
        for j in range(i+1, len(peaks)):
            for span in range(1, 15):
                d = (peaks[j]-peaks[i])/span
                if not (d_range[0] <= d <= d_range[1]): continue
                k0 = peaks[i] - np.floor((peaks[i]-peaks.min()+d)/d)*d
                teeth = np.arange(k0, peaks.max()+2*d, d)
                hits = [(int(k), float(peaks[np.argmin(np.abs(peaks-t))]))
                        for k, t in enumerate(teeth)
                        if np.min(np.abs(peaks-t)) < d*0.08]
                score = (len(hits), -abs(d-np.mean(d_range)))
                if best is None or score > best[0]:
                    best = (score, float(d), hits)
    if best is None or best[0][0] < n_min:
        raise SystemExit('graticule comb failed (peaks %s)' % peaks)
    d, hits = best[1], best[2]
    k_min = min(k for k, _ in hits)
    return d, [(k-k_min, pos) for k, pos in hits]

def _border_clusters(prof, thresh=0.5):
    on = np.nonzero(prof > thresh)[0]
    splits = np.nonzero(np.diff(on) > 12)[0]
    return [ (g[0], g[-1]) for g in np.split(on, splits+1) ]

def _strip_blobs(ink, strip, axis, d_range, n_min):
    """Blob comb along a border strip; returns (d, [(k, pos), …])."""
    if axis == 0:   # horizontal strip: blobs along x
        L = ink[strip[0]:strip[1], :].mean(0)
    else:           # vertical strip: blobs along y
        L = ink[:, strip[0]:strip[1]].mean(1)
    L = ndimage.gaussian_filter1d(L, 6)
    on = L > 0.055
    blobs = []
    i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]: j += 1
            if 8 < (j-i) < 420:
                blobs.append(float(np.average(np.arange(i, j), weights=L[i:j])))
            i = j
        else:
            i += 1
    return _comb(np.array(blobs), d_range, n_min)

def georef():
    """Fit the 1865 sheet from its border ticks.

    The map draws no internal graticule — only degree numbers on short ticks
    along the four borders (Greenwich longitudes above, Washington longitudes
    below, latitudes on the sides).  Tick combs on the top and side borders
    solve a similarity; the degree labelling is chosen automatically as the
    one that lays the surveyed state boundary along the map's heavy red
    territory line; bottom ticks then join and the final fit is affine.
    """
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    p('· reading the scan…')
    rgb = np.asarray(Image.open(path('scan.jpg')), dtype=np.uint8)
    H, W = rgb.shape[:2]
    mx = rgb.max(2).astype(np.int16); mn = rgb.min(2).astype(np.int16)
    mean = rgb.mean(2, dtype=np.float32)
    ink = ((255.0 - mean - 1.2*(mx-mn)) > 80).astype(np.float32)
    red = ((rgb[:, :, 0].astype(np.int16) - (rgb[:, :, 1].astype(np.int16)
            + rgb[:, :, 2])//2) > 28) & (rgb[:, :, 0] > 110)

    p('· finding the borders and their ticks…')
    vprof = ink[int(H*0.2):int(H*0.8), :].mean(0)
    hprof = ink[:, int(W*0.2):int(W*0.8)].mean(1)
    vcl = _border_clusters(vprof); hcl = _border_clusters(hprof)
    xL, xR = vcl[0][1], vcl[-1][0]              # inner faces of the side borders
    yT, yB = hcl[0][1], hcl[-1][0]
    p('  borders: x %d/%d  y %d/%d' % (xL, xR, yT, yB))
    dlon, top = _strip_blobs(ink, (yT+10, yT+95), 0, (500, 640), 8)
    dlat, left = _strip_blobs(ink, (xL+10, xL+95), 1, (740, 920), 3)
    _, bottom = _strip_blobs(ink, (yB-95, yB-10), 0, (dlon*0.97, dlon*1.03), 6)
    try:
        _, right = _strip_blobs(ink, (xR-95, xR-10), 1, (dlat*0.97, dlat*1.03), 3)
    except SystemExit:
        right = []
    p('  ticks: %d top, %d bottom, %d left, %d right  (Δlon %.0f px, Δlat %.0f px)'
      % (len(top), len(bottom), len(left), len(right), dlon, dlat))

    # similarity from top + side ticks, tested over integer degree labellings
    ring = boundary_ring()
    dens = ring[::3]
    rX, rY = LCC.fwd(dens[:, 0], dens[:, 1])
    red_blur = ndimage.maximum_filter(red[::2, ::2], 9)
    ymid_top = yT + 55.0
    xmid_side = xL + 55.0
    def solve(lon0, lat0, extra_x=(), extra_y=()):
        rows, rhs = [], []
        for k, pos in top:
            X, Y = LCC.fwd(lon0+k, 49.35)
            rows.append([1, 0, X, Y]); rhs.append(pos)
        for k, pos in left:
            X, Y = LCC.fwd(-116.2, lat0-k)
            rows.append([0, 1, -Y, X]); rhs.append(pos)
        for k, pos in right:
            X, Y = LCC.fwd(-103.6, lat0-k)
            rows.append([0, 1, -Y, X]); rhs.append(pos)
        c, *_ = np.linalg.lstsq(np.array(rows, float), np.array(rhs, float), rcond=None)
        return c    # x = c0 + c2 X + c3 Y ;  y = c1 + c3 X - c2 Y
    best = None
    for lon0 in range(-119, -113):
        for lat0 in range(47, 51):
            c = solve(lon0, lat0)
            px = c[0] + c[2]*rX + c[3]*rY
            py = c[1] + c[3]*rX - c[2]*rY
            ok = (px > 0) & (px < W-1) & (py > 0) & (py < H-1)
            if ok.mean() < 0.7: continue
            score = float(red_blur[np.clip(py[ok].astype(int)//2, 0, red_blur.shape[0]-1),
                                   np.clip(px[ok].astype(int)//2, 0, red_blur.shape[1]-1)].mean())
            if best is None or score > best[0]:
                best = (score, lon0, lat0, c)
    if best is None or best[0] < 0.22:
        raise SystemExit('no labelling lays the boundary on the red line (best %r)'
                         % (best and best[:3],))
    score, lon0, lat0, c = best
    p('  labelling: top ticks start %d°, side ticks start %d°  (boundary score %.2f)'
      % (lon0, lat0, score))

    # exact inverse of the similarity gives each border's true coordinate
    A_, B_ = float(c[2]), float(c[3])
    det = -(A_*A_ + B_*B_)
    def inv_sim(x, y):
        dx, dy = x-float(c[0]), y-float(c[1])
        X = (-A_*dx - B_*dy)/det
        Y = (-B_*dx + A_*dy)/det
        lo, la = LCC.inv(X, Y)
        return float(lo), float(la)
    lat_top = inv_sim(W/2, ymid_top)[1]
    lat_bot = inv_sim(W/2, yB-55.0)[1]
    lon_left = inv_sim(xmid_side, H/2)[0]
    lon_right = inv_sim(xR-55.0, H/2)[0]

    # final affine, each axis solved from the ticks that actually measure it:
    # top+bottom ticks fix x(lon); left+right ticks fix y(lat)
    rx_A, rx_b, ry_A, ry_b, nb = [], [], [], [], 0
    for k, pos in top:
        X, Y = LCC.fwd(lon0+k, lat_top)
        rx_A.append([1, X, Y]); rx_b.append(pos)
    # the bottom scale is from the WASHINGTON meridian — measure its offset
    # from Greenwich on the sheet itself, then join the ticks
    lons_g = np.arange(lon0-2, lon0+16)*1.0
    Xg, Yg = LCC.fwd(lons_g, np.full(18, lat_bot))
    pxg = c[0] + c[2]*Xg + c[3]*Yg
    offs = []
    for k, pos in bottom:
        j = int(np.argmin(np.abs(pxg-pos)))
        if abs(pxg[j]-pos) < dlon*0.45: offs.append(pos-pxg[j])
    dwash = float(np.median(offs))/dlon if offs else 0.0
    p('  Washington meridian offset on the sheet: %.3f° (77°%02.0f′ W of Greenwich)'
      % (dwash, abs(dwash)*60 + 3*0))
    for k, pos in bottom:
        j = int(np.argmin(np.abs(pxg-pos)))
        if abs(pxg[j]-pos) < dlon*0.45:
            X, Y = LCC.fwd(lons_g[j]+dwash, lat_bot)
            rx_A.append([1, X, Y]); rx_b.append(pos); nb += 1
    for k, pos in left:
        X, Y = LCC.fwd(lon_left, lat0-k)
        ry_A.append([1, X, Y]); ry_b.append(pos)
    for k, pos in right:
        X, Y = LCC.fwd(lon_right, lat0-k)
        ry_A.append([1, X, Y]); ry_b.append(pos)
    def solve_trim(Ar, br):
        Ar = np.array(Ar, float); br = np.array(br, float)
        cc, *_ = np.linalg.lstsq(Ar, br, rcond=None)
        r = np.abs(Ar@cc - br)
        k = r < max(12.0, float(np.median(r))*3.0)
        cc, *_ = np.linalg.lstsq(Ar[k], br[k], rcond=None)
        return cc, Ar[k], br[k]
    cx, rx_A, rx_b = solve_trim(rx_A, rx_b)
    cy, ry_A, ry_b = solve_trim(ry_A, ry_b)
    resx = rx_A@cx - rx_b
    resy = ry_A@cy - ry_b
    p('  affine: %d x-ticks rms %.1f px · %d y-ticks rms %.1f px (%d bottom joined)'
      % (len(rx_b), float(np.sqrt((resx**2).mean())),
         len(ry_b), float(np.sqrt((resy**2).mean())), nb))
    fit = dict(Xm=0.0, Ym=0.0, sX=1.0, deg=1,
               cx=[float(v) for v in cx], cy=[float(v) for v in cy],
               rms=round(float(np.sqrt((np.concatenate([resx, resy])**2).mean())), 1),
               median=round(float(np.median(np.abs(np.concatenate([resx, resy])))), 1),
               n=len(rx_b)+len(ry_b))
    json.dump(fit, open(path('fit.json'), 'w'))
    gx = [pos for _, pos in top] + [xmid_side]*len(left)
    gy = [ymid_top]*len(top) + [pos for _, pos in left]

    sf = SavedFit(fit)
    bx, by = sf.apply(rX, rY)
    im = Image.open(path('scan.jpg'))
    overlay(im, {(255, 40, 40): list(zip(gx, gy)),
                 (30, 120, 255): list(zip(bx[::4], by[::4]))},
            path('qa_georef.png'), 2000)
    p('  QA overlay in work/qa_georef.png')

class SavedFit:
    def __init__(self, d):
        self.Xm, self.Ym, self.sX, self.deg = d['Xm'], d['Ym'], d['sX'], d['deg']
        self.cx, self.cy = np.array(d['cx']), np.array(d['cy'])
    def apply(self, X, Y):
        A = poly_basis((np.asarray(X, float)-self.Xm)/self.sX,
                       (np.asarray(Y, float)-self.Ym)/self.sX, self.deg)
        return A@self.cx, A@self.cy

# --------------------------------------------- the manuscript, registered
MS_URL = 'https://www.mtmemory.org/assets/downloadwiz/741286'

def manuscript():
    """De Lacy's pen-on-linen original (MHS), registered against the print."""
    if os.path.exists(path('alt.npy')):
        p('· manuscript cached'); return
    georef()
    from reg import smooth_feature, register, fit_trimmed
    if not os.path.exists(path('manuscript.jpg')):
        p('· downloading the manuscript from the Montana History Portal…')
        req = urllib.request.Request(MS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=600) as r:
            open(path('manuscript.jpg'), 'wb').write(r.read())
    p('· reading the manuscript…')
    ms = np.asarray(Image.open(path('manuscript.jpg')).convert('RGB'), dtype=np.uint8)
    msf = smooth_feature(ms, blue=False)
    mh, mw = int(msf.shape[0]*0.03), int(msf.shape[1]*0.03)
    msf[:mh, :] = 0; msf[-mh:, :] = 0; msf[:, :mw] = 0; msf[:, -mw:] = 0

    fitd = json.load(open(path('fit.json')))
    pfit = SavedFit(fitd)
    prg = np.asarray(Image.open(path('scan.jpg')).convert('RGB'), dtype=np.uint8)
    pf = smooth_feature(prg, blue=False)
    del prg
    def print_px(lon, lat):
        x, y = pfit.apply(*LCC.fwd(lon, lat))
        return float(x), float(y)
    xa, _ = print_px(-110.0, 46.5); xb, _ = print_px(-109.0, 46.5)
    m_print = 76500.0/abs(xb-xa)
    p('  print ≈ %.0f m/px' % m_print)
    target = [dict(name='1865 print', feat=pf, to_px=print_px, m_per_px=m_print)]

    lons = np.arange(-115.6, -104.1, 0.75)
    lats = np.arange(44.75, 48.95, 0.65)
    p('· correlating the manuscript against the print…')
    X, Y, gx, gy, m_ms = register(msf, target, LCC, lons, lats,
                                  m_scan_hint=m_print*1.25, z_lo=0.55, z_hi=1.1,
                                  pw=130, sw=130, log=p)
    if len(gx) < 8: raise SystemExit('too few manuscript GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='manuscript pass 1',
                          m_per_px=m_ms, log=p)
    X, Y, gx, gy, _ = register(msf, target, LCC, lons, lats,
                               m_scan_hint=m_ms, seed_fit=fit1,
                               pw=130, sw=200, log=p)
    fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name='manuscript pass 2',
                          m_per_px=m_ms, log=p)
    X, Y, gx, gy, _ = register(msf, target, LCC, lons, lats,
                               m_scan_hint=m_ms, seed_fit=fit2,
                               pw=130, sw=60, log=p)
    if len(gx) < 10: raise SystemExit('too few manuscript GCPs')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='manuscript fit',
                            floor=10.0, k=2.0, m_per_px=m_ms, log=p)

    g = make_grid()
    from encode import Grid as _Grid
    g2 = _Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, g.TW//2)
    _, _, LON, LAT = g2.lonlat()
    SX, SY = fit.apply(*LCC.fwd(LON, LAT))
    inside = (SX > 1) & (SX < ms.shape[1]-2) & (SY > 1) & (SY < ms.shape[0]-2)
    src = ms.astype(np.float32)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g2.TH, g2.TW, 3), np.float32)
    tex[:] = (205, 193, 168)
    for c in range(3):
        tex[:, :, c][inside] = ndimage.map_coordinates(
            src[:, :, c], [SY[inside], SX[inside]], order=1, mode='nearest')
    del src
    np.save(path('alt.npy'), tex.astype(np.uint8))
    json.dump(dict(rms=round(fit.rms, 2), median=round(fit.median, 2),
                   n=int(keep.sum())), open(path('alt_fit.json'), 'w'))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//2, g2.TH//2)).save(path('qa_alt.png'))
    p('  QA in work/qa_alt.png')

# ------------------------------------------------------------------ stage 3
def resample():
    if os.path.exists(path('drape.npy')):
        p('· drape cached'); return
    georef()
    fit = SavedFit(json.load(open(path('fit.json'))))
    g = make_grid()
    p('· conic grid %d × %d  (%.0f × %.0f km)' % (g.TW, g.TH, g.kmw, g.kmh))
    GX, GY, LON, LAT = g.lonlat()
    SX, SY = fit.apply(*LCC.fwd(LON, LAT))
    p('· resampling the map…')
    im = Image.open(path('scan.jpg')).convert('RGB')
    from PIL import ImageFilter
    src = np.asarray(im.filter(ImageFilter.GaussianBlur(0.55)), dtype=np.float32)
    del im
    inside = (SX > 1) & (SX < src.shape[1]-2) & (SY > 1) & (SY < src.shape[0]-2)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g.TH, g.TW, 3), np.float32)
    tex[:] = (231, 222, 200)
    for c in range(3):
        tex[:, :, c][inside] = ndimage.map_coordinates(
            src[:, :, c], [SY[inside], SX[inside]], order=1, mode='nearest')
    del src
    np.save(path('drape.npy'), tex.astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//4, g.TH//4)).save(path('qa_drape.png'))
    p('  QA drape in work/qa_drape.png')

# ------------------------------------------------------------------ stage 4
def decode_height():
    hm = np.asarray(Image.open(os.path.join(MONTANA, 'height.webp')).convert('RGB'))
    q = (hm[:, :, 0].astype(np.uint16) << 4) | (hm[:, :, 1] >> 4)
    return MMETA['hmin'] + q/4095.0*(MMETA['hmax']-MMETA['hmin'])

def mines(g):
    sites = json.load(open(path('mrds.json')))
    picks = {}
    rank = {'Producer': 3, 'Past Producer': 2, 'Prospect': 1}
    for s in sites:
        codes = s['c'].split()
        if not ('AU' in codes or 'AG' in codes): continue
        r = rank.get(s['s'], 0)
        if r < 2: continue
        u, v = g.uv(s['lon'], s['lat'])
        if not (0.005 < u < 0.995 and 0.005 < v < 0.995): continue
        cell = (int(u*140), int(v*85))
        name = s['n'] or 'Unnamed'
        good = (r, 'AU' in codes, name != 'Unnamed', -len(name))
        if cell not in picks or good > picks[cell][0]:
            com = 'gold' if 'AU' in codes else 'silver'
            picks[cell] = (good, dict(n=name.title()[:26], u=round(u, 5),
                                      v=round(v, 5), c=com))
    out = [v[1] for v in picks.values()]
    out.sort(key=lambda m: (m['n'] == 'Unnamed', m['n']))
    return out[:400]

def encode():
    resample()
    manuscript()
    g = make_grid()
    p('· re-encoding the montana height field (same grid, lighter raster)…')
    hgt = decode_height()
    hm = np.asarray(Image.open(os.path.join(MONTANA, 'height.webp')).convert('RGB'))
    from encode import encode_height
    HW, HH, hmin, hmax = encode_height(hgt, hm[:, :, 2] > 128,
                                       os.path.join(BUILD, 'height.webp'), 2048, log=p)
    encode_drape(np.load(path('drape.npy')), os.path.join(BUILD, 'drape.webp'), log=p)
    card = Image.open(os.path.join(BUILD, 'drape.webp'))
    card = card.resize((640, int(card.height*640/card.width)), Image.LANCZOS)
    card.save(os.path.join(BUILD, 'card.webp'), quality=82, method=6)
    if os.path.exists(path('alt.npy')):
        p('· encoding the manuscript layer…')
        Image.fromarray(np.load(path('alt.npy'))).save(
            os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
        p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    # sepia relief in the lithograph's own greys
    ramp = [[229, 219, 196], [224, 213, 188], [218, 206, 180], [211, 198, 171],
            [203, 189, 161], [194, 179, 151], [185, 169, 141], [176, 159, 132],
            [167, 150, 123], [158, 141, 115], [150, 133, 108], [143, 126, 102],
            [139, 122, 98], [143, 127, 104], [152, 137, 116], [163, 149, 129],
            [176, 163, 144]]
    ramp_ft = [1500 + 500*i for i in range(len(ramp))]

    p('· thinning the MRDS mines…')
    M = mines(g)
    p('  %d mines kept' % len(M))

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=5.0, exagMax=20.0, contourM=250, mineDist=0.62, altName='The manuscript', rampLo=1400,
                       rampHi=10200, sheetA='1865 map',
                       tourEx=[1.7, 0.021, 2.1, 5.6]),
               fit=dict(rms=fitd['rms'], median=fitd['median'], n=fitd['n']))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('manuscript', manuscript), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
