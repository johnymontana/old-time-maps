#!/usr/bin/env python3
"""Glacier in Contours — asset pipeline.

The USGS-engraved sheet of Glacier National Park (surveyed 1900–1912; this is
the Interior Department's 1915 administrative printing, scanned by the Library
of Congress at 9,788 × 8,492 px), georeferenced from its own graticule and
draped over Terrarium elevations, with the park's named glaciers carried along
as vector margins — their Little-Ice-Age maxima and their 2015 outlines.

The scan carries no coordinates.  The georeference is fitted, not hand-picked:
the 49th-parallel boundary line is detected and its endpoints — the sheet's
printed 114°30′ and 113°10′ corners — seed a similarity; the sheet's shared
linework (black culture, blue drainage) is then correlated against four
georeferenced sibling quadrangles of the same survey (Chief Mountain 1904,
Kintla Lakes 1906, Nyack 1914, Marias Pass 1913), and a degree-2 polynomial in
a local conic chart is least-squared through the resulting control points.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.  Scan cache: work/scan.jpg (put the
LOC JP2 there yourself as scan.jpg, or let fetch download it).
"""
import json, math, os, sys, urllib.request, zipfile

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('GL_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27, tm_inverse
from georef import Fit, fit_report, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS

# --- the scan --------------------------------------------------------------
SCAN_URL = 'https://tile.loc.gov/storage-services/service/gmd/gmd425/g4252/g4252g/ct007663.jp2'
# --- the sheet's printed graticule (NAD27-era datum) -----------------------
LON_W, LON_E, LAT_N = -114.5, -113.0-1.0/6.0, 49.0     # corner labels
GRAT_STEP = 1.0/6.0                                     # 10-minute lines
# --- glacier margins (ScienceBase, public domain) --------------------------
MARGIN_ZIPS = [
    ('lia',  '5b194f1ce4b092d965237f5f', 'mid19thcent_GNPnamedglaciers'),
    ('g2015','58af7988e4b01ccd54f9f608', 'GNPglaciers_2015'),
]
UTM12_LON0 = -111.0
# --- grid ------------------------------------------------------------------
LCC = Lcc(48.35, 48.95, -113.8333)
MARGIN = 0.0011
TEX_W, HGT_W = 3328, 2219
DEM_ZOOM, DEM_BOX = 12, (-114.66, -113.00, 48.14, 49.10)
CLAMP = (750, 3400)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

# ------------------------------------------------------------------ stage 1
def fetch():
    dst = path('scan.jpg')
    if not os.path.exists(dst):
        p('· downloading the 1915 sheet from the Library of Congress…')
        req = urllib.request.Request(SCAN_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=600) as r:
            open(path('scan.jp2'), 'wb').write(r.read())
        Image.open(path('scan.jp2')).convert('RGB').save(dst, quality=96)
    else:
        p('· scan cached')
    for gid, sbid, name in MARGIN_ZIPS:
        z = path('sb_%s.zip' % sbid)
        if not os.path.exists(path(name, name + '.shp')):
            if not os.path.exists(z):
                p('· downloading glacier margins (%s)…' % gid)
                req = urllib.request.Request(
                    'https://www.sciencebase.gov/catalog/file/get/' + sbid,
                    headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=300) as r:
                    open(z, 'wb').write(r.read())
            zipfile.ZipFile(z).extractall(WORK)
    for name, url in REG_QUADS:
        dst = path(name + '.tif')
        if os.path.exists(dst): continue
        p('· downloading registration quad %s…' % name)
        req = urllib.request.Request(url, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, open(dst, 'wb') as f:
            f.write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def ink_mask(rgb):
    """Black-ink likelihood: dark and unsaturated (contours are brown)."""
    mx = rgb.max(2).astype(np.int16); mn = rgb.min(2).astype(np.int16)
    mean = rgb.mean(2, dtype=np.float32)
    return (255.0 - mean - 1.2*(mx-mn)) > 90

def _edge_line(mask, band, axis, thresh=0.42):
    """Strongest long straight line in a band; returns (a, b): coord = a·along + b.

    axis=0: vertical line (x as a function of y); axis=1: horizontal.
    """
    H, W = mask.shape
    if axis == 0:
        frac = mask[int(H*0.12):int(H*0.88), band[0]:band[1]].mean(0)
    else:
        frac = mask[band[0]:band[1], int(W*0.12):int(W*0.88)].mean(1)
    cand = np.nonzero(frac > thresh)[0]
    if not len(cand): raise SystemExit('no line found in band %r' % (band,))
    splits = np.nonzero(np.diff(cand) > 12)[0]
    groups = np.split(cand, splits+1)
    inner = max(groups, key=lambda gr: frac[gr].mean())
    c0 = band[0] + int(round(inner.mean()))
    # refine: dark peak within ±7 px at samples along the line
    n, pts = 60, []
    for i in range(n):
        t = int((H if axis == 0 else W)*(0.10 + 0.80*i/(n-1)))
        seg = mask[t, c0-7:c0+8] if axis == 0 else mask[c0-7:c0+8, t]
        if seg.sum() == 0: continue
        pts.append((t, c0-7 + np.average(np.arange(15), weights=seg)))
    pts = np.array(pts)
    a, b = np.polyfit(pts[:, 0], pts[:, 1], 1)
    return a, b

def _offset_line(mask, ref, drange, thresh=0.10):
    """A horizontal-ish line parallel to ref (a, b), found at a constant
    offset within drange, then refined per-column and refitted."""
    H, W = mask.shape
    xs = np.arange(int(W*0.08), int(W*0.92), 6)
    ry = ref[0]*xs + ref[1]
    scores = []
    for dlt in range(drange[0], drange[1]):
        yy = (ry + dlt).astype(int)
        scores.append(mask[yy, xs].mean())
    scores = ndimage.gaussian_filter1d(np.array(scores), 1.5)
    if scores.max() < thresh:
        raise SystemExit('offset line not found (best %.2f)' % scores.max())
    d0 = drange[0] + int(np.argmax(scores))
    pts = []
    for x in xs:
        c = int(ref[0]*x + ref[1] + d0)
        seg = mask[c-8:c+9, x]
        if not seg.any(): continue
        pts.append((x, c-8 + np.average(np.arange(17), weights=seg)))
    pts = np.array(pts)
    for _ in range(2):
        a, b = np.polyfit(pts[:, 0], pts[:, 1], 1)
        r = np.abs(pts[:, 1] - (a*pts[:, 0] + b))
        pts = pts[r < max(3.0, np.median(r)*3)]
    return float(a), float(b)

def _line_endpoints(mask, line, axis, step=24, need=4):
    """Walk along a fitted line; return (along0, along1) where ink persists."""
    H, W = mask.shape
    n = (W if axis == 1 else H)
    hits = []
    for t in range(200, n-200, step):
        c = int(round(line[0]*t + line[1]))
        seg = mask[c-5:c+6, t] if axis == 1 else mask[t, c-5:c+6]
        hits.append(1 if seg.any() else 0)
    hits = np.array(hits)
    run = np.convolve(hits, np.ones(need), 'same')
    on = np.nonzero(run >= need)[0]
    if not len(on): raise SystemExit('line endpoints not found')
    return 200 + on[0]*step, 200 + on[-1]*step

def _cross(v, h):
    """Intersection of x = av*y + bv and y = ah*x + bh."""
    av, bv = v; ah, bh = h
    y = (ah*bv + bh)/(1 - ah*av)
    return av*y + bv, y

# sibling quadrangles of the same survey, used as registration targets
S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/'
REG_QUADS = [
    ('cm1904',     S3+'MT_Chief%20Mountain_268508_1904_125000_geo.tif'),
    ('kintla1906', S3+'MT_Kintla%20Lakes_268572_1906_125000_geo.tif'),
    ('nyack1914',  S3+'MT_Nyack_268586_1914_125000_geo.tif'),
    ('marias1913', S3+'MT_Marias%20Pass_268578_1913_125000_geo.tif'),
]

def feature_mask(rgb):
    """Linework shared between editions: black ink or blue drainage."""
    mx = rgb.max(2).astype(np.int16); mn = rgb.min(2).astype(np.int16)
    mean = rgb.mean(2, dtype=np.float32)
    black = (255.0 - mean - 1.2*(mx-mn)) > 90
    b = rgb[:, :, 2].astype(np.float32)
    blue = (b - 0.5*rgb[:, :, 0] - 0.5*rgb[:, :, 1]) > 16
    return black | blue

def _quad_targets():
    """The sibling quadrangles as registration targets (cropped to overlap)."""
    from georef import QuadGeoref
    from reg import smooth_feature
    targets = []
    for name, _url in REG_QUADS:
        qim = Image.open(path(name + '.tif'))
        qr = QuadGeoref(qim)
        qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8)
        qf = smooth_feature(qrgb)
        del qrgb
        _, y_lo_q = qr.to_px(qr.lon0, 48.265)      # rows above the sheet's foot
        qf = qf[:int(min(y_lo_q, qf.shape[0])), :]
        targets.append(dict(name=name, feat=qf, to_px=qr.to_px,
                            m_per_px=qr.scale[0]))
    return targets

REG_LONS = np.arange(LON_W+0.05, LON_E-0.04, 0.115)
REG_LATS = np.arange(48.30, 48.99, 0.095)

def georef():
    """Register the sheet against the survey's own 30′ quadrangles."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    from reg import smooth_feature, register, fit_trimmed
    p('· reading the scan…')
    rgb = np.asarray(Image.open(path('scan.jpg')), dtype=np.uint8)
    H, W = rgb.shape[:2]
    mask = ink_mask(rgb)
    p('· correlating against the sibling quadrangles…')
    sheet_f = smooth_feature(rgb)
    X, Y, gx, gy, m_per_px = register(sheet_f, _quad_targets(), LCC,
                                      REG_LONS, REG_LATS, m_scan_hint=11.0, log=p)
    if len(gx) < 14: raise SystemExit('too few correlation GCPs')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='quad-registration fit',
                            m_per_px=m_per_px, log=p)

    # content foot: where map ink stops, as a latitude through the fit
    anyink = np.asarray(Image.open(path('scan.jpg')).convert('L')) < 225
    frame_b = _edge_line(mask, (H-1100, H-250), 1)
    yB = frame_b[1] + frame_b[0]*W/2
    ybs = []
    for fx in (0.30, 0.45, 0.60, 0.75):
        col = int(W*fx)
        dens = ndimage.uniform_filter1d(anyink[:, col-9:col+10].mean(1).astype(float), 25)
        rows = np.nonzero(dens > 0.12)[0]
        rows = rows[rows < yB - 55]
        if len(rows): ybs.append(rows[-1])
    y_b = float(np.median(ybs))
    lon_mid = (LON_W+LON_E)/2
    lo, hi = 48.05, 48.6
    for _ in range(48):
        mid = (lo+hi)/2
        _, pyv = fit.apply(*LCC.fwd(lon_mid, mid))
        if pyv > y_b: lo = mid
        else: hi = mid
    s_content = round((lo+hi)/2, 4)
    p('  content foot at %.4f° N (y %.0f)' % (s_content, y_b))

    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   n=int(keep.sum()), s_content=s_content),
              open(path('fit.json'), 'w'))
    im = Image.open(path('scan.jpg'))
    overlay(im, {(255, 40, 40): list(zip(gx[keep], gy[keep])),
                 (30, 120, 255): list(zip(gx[~keep], gy[~keep]))},
            path('qa_georef.png'), 2000)
    p('  QA overlay in work/qa_georef.png')

# ------------------------------------------------------- the 1959 geology
GEO_PDF = 'https://pubs.usgs.gov/pp/0296/plate-1.pdf'
ALT_W = TEX_W//2

def geology():
    """Ross's PP 296 plate 1 — the park's geology — as the middle layer."""
    if os.path.exists(path('alt.npy')):
        p('· geology cached'); return
    resample()
    from reg import smooth_feature, register, fit_trimmed
    if not os.path.exists(path('pp296_p1.jpg')):
        if not os.path.exists(path('pp296_p1.pdf')):
            p('· downloading PP 296 plate 1…')
            req = urllib.request.Request(GEO_PDF, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=600) as r:
                open(path('pp296_p1.pdf'), 'wb').write(r.read())
        p('· rasterising the plate…')
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(path('pp296_p1.pdf'))[0]
        scale = min(9000/page.get_width(), 6.0)
        page.render(scale=scale).to_pil().convert('RGB') \
            .save(path('pp296_p1.jpg'), quality=95)
    p('· reading the plate…')
    rgb = np.asarray(Image.open(path('pp296_p1.jpg')), dtype=np.uint8)
    p('· correlating the geology against the 1915 sheet…')
    plate_f = smooth_feature(rgb)
    ph, pw2 = plate_f.shape
    plate_f = plate_f[:int(ph*0.79)]               # map body only — sections below
    plate_f[int(ph*0.29):int(ph*0.78),
            int(pw2*0.10):int(pw2*0.23)] = 0       # blank the legend inset
    fitd0 = json.load(open(path('fit.json')))
    sfit = SavedFit(fitd0)
    sheet_rgb = np.asarray(Image.open(path('scan.jpg')), dtype=np.uint8)
    sheet_feat = smooth_feature(sheet_rgb)
    del sheet_rgb
    def sheet_px(lon, lat):
        x, y = sfit.apply(*LCC.fwd(lon, lat))
        return float(x), float(y)
    target = [dict(name='1915 sheet', feat=sheet_feat, to_px=sheet_px,
                   m_per_px=11.5)]
    X, Y, gx, gy, m_per_px = register(plate_f, target, LCC,
                                      REG_LONS, REG_LATS, m_scan_hint=11.4, log=p)
    if len(gx) < 10: raise SystemExit('too few geology GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 2, name='geology pass 1',
                          m_per_px=m_per_px, log=p)
    lons2 = np.arange(LON_W+0.04, LON_E-0.03, 0.065)
    lats2 = np.arange(48.28, 49.0, 0.055)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons2, lats2,
                               m_scan_hint=m_per_px, seed_fit=fit1,
                               pw=200, sw=260, log=p)
    if len(gx) < 14: raise SystemExit('too few geology GCPs')
    fit2, _ = fit_trimmed(X, Y, gx, gy, 1, name='geology pass 2',
                          m_per_px=m_per_px, log=p)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons2, lats2,
                               m_scan_hint=m_per_px, seed_fit=fit2,
                               pw=200, sw=90, log=p)
    if len(gx) < 14: raise SystemExit('too few geology GCPs')
    fit3, _ = fit_trimmed(X, Y, gx, gy, 2, name='geology pass 3',
                          m_per_px=m_per_px, log=p)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons2, lats2,
                               m_scan_hint=m_per_px, seed_fit=fit3,
                               pw=160, sw=45, log=p)
    if len(gx) < 14: raise SystemExit('too few geology GCPs')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='geology fit',
                            m_per_px=m_per_px, log=p)
    fitd = json.load(open(path('fit.json')))
    g = make_grid()
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON, LAT = g2.lonlat()
    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    SX, SY = fit.apply(*LCC.fwd(lon27, lat27))
    inside = ((lon27 >= LON_W) & (lon27 <= LON_E) &
              (lat27 <= LAT_N) & (lat27 >= fitd['s_content']) &
              (SX > 1) & (SX < rgb.shape[1]-2) & (SY > 1) & (SY < rgb.shape[0]-2))
    src = rgb.astype(np.float32)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g2.TH, g2.TW, 3), np.float32)
    tex[:] = (234, 226, 205)
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

class SavedFit:
    def __init__(self, d):
        self.Xm, self.Ym, self.sX, self.deg = d['Xm'], d['Ym'], d['sX'], d['deg']
        self.cx, self.cy = np.array(d['cx']), np.array(d['cy'])
        self.s_content = d['s_content']
    def apply(self, X, Y):
        from proj import poly_basis
        A = poly_basis((np.asarray(X, float)-self.Xm)/self.sX,
                       (np.asarray(Y, float)-self.Ym)/self.sX, self.deg)
        return A@self.cx, A@self.cy

def make_grid():
    lons = [LON_W, LON_E]; lats = [LAT_N, 48.24]      # content foot ≈ 48°15.5′
    return Grid.around(LCC, lons, lats, MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 3
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy')):
        p('· grid cached'); return
    georef()
    fit = SavedFit(json.load(open(path('fit.json'))))
    g = make_grid()
    p('· conic grid %d × %d  (%.0f × %.0f km)' % (g.TW, g.TH, g.kmw, g.kmh))
    GX, GY, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    p('  elevation %.0f – %.0f m' % (hgt.min(), hgt.max()))
    np.save(path('hgt.npy'), hgt)

    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    X27, Y27 = LCC.fwd(lon27, lat27)
    SX, SY = fit.apply(X27, Y27)
    inside = ((lon27 >= LON_W) & (lon27 <= LON_E) &
              (lat27 <= LAT_N) & (lat27 >= fit.s_content))

    p('· resampling the sheet…')
    src = np.asarray(Image.open(path('scan.jpg')).convert('RGB'), dtype=np.float32)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g.TH, g.TW, 3), np.float32)
    tex[:] = (234, 226, 205)
    for c in range(3):
        tex[:, :, c][inside] = ndimage.map_coordinates(
            src[:, :, c], [SY[inside], SX[inside]], order=1, mode='nearest')
    del src
    np.save(path('drape.npy'), tex.astype(np.uint8))
    np.save(path('mask.npy'), inside)

    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//4, g.TH//4)).save(path('qa_drape.png'))
    p('  QA drape in work/qa_drape.png')

# ------------------------------------------------------------------ stage 4
def _simplify(pts, tol):
    """Iterative Douglas–Peucker on an (N,2) ring."""
    keep = np.zeros(len(pts), bool); keep[0] = keep[-1] = True
    stack = [(0, len(pts)-1)]
    while stack:
        i0, i1 = stack.pop()
        if i1 <= i0+1: continue
        seg = pts[i1]-pts[i0]; L = np.hypot(*seg)
        rel = pts[i0+1:i1]-pts[i0]
        if L == 0:
            d = np.hypot(rel[:, 0], rel[:, 1])
        else:
            d = np.abs(seg[0]*rel[:, 1] - seg[1]*rel[:, 0])/L
        j = int(np.argmax(d))
        if d[j] > tol:
            k = i0+1+j; keep[k] = True
            stack.append((i0, k)); stack.append((k, i1))
    return pts[keep]

def glacier_lines(g):
    import shapefile
    out = []
    style = dict(lia=dict(name='Ice at its 1850 peak', color='#a9dcec'),
                 g2015=dict(name='Ice in 2015', color='#e0655a'))
    for gid, sbid, name in MARGIN_ZIPS:
        shp = path(name, name + '.shp')
        sf = shapefile.Reader(shp=open(shp, 'rb'),
                              shx=open(shp[:-4]+'.shx', 'rb'))
        rings = 0
        for sh in sf.shapes():
            pts = np.array(sh.points)
            parts = list(sh.parts) + [len(pts)]
            for i in range(len(parts)-1):
                ring = pts[parts[i]:parts[i+1]]
                if len(ring) < 8: continue
                lon, lat = tm_inverse(ring[:, 0], ring[:, 1], UTM12_LON0)
                u, v = g.uv(lon, lat)
                uv = np.column_stack([u, v])
                # tolerance ≈ 45 m in grid u units
                uv = _simplify(uv, 45.0/(g.kmw*1000))
                if len(uv) < 6: continue
                per = np.hypot(*np.diff(uv, axis=0).T).sum()*g.kmw
                if per < 0.55: continue          # skip fragments under ~½ km
                out.append(dict(id=gid, chip=style[gid]['name'],
                                name=style[gid]['name'], color=style[gid]['color'],
                                dash=0,
                                pts=[[round(float(a), 4), round(float(b), 4)]
                                     for a, b in uv]))
                rings += 1
        p('  %s: %d rings' % (gid, rings))
    return out

def encode():
    geology()
    g = make_grid()
    hgt = np.load(path('hgt.npy'))
    mask = np.load(path('mask.npy'))
    HW, HH, hmin, hmax = encode_height(hgt, mask, os.path.join(BUILD, 'height.webp'),
                                       HGT_W, log=p)
    encode_drape(np.load(path('drape.npy')), os.path.join(BUILD, 'drape.webp'), log=p)
    card = Image.open(os.path.join(BUILD, 'drape.webp'))
    card = card.resize((640, int(card.height*640/card.width)), Image.LANCZOS)
    card.save(os.path.join(BUILD, 'card.webp'), quality=82, method=6)
    if os.path.exists(path('alt.npy')):
        p('· encoding the geology layer…')
        Image.fromarray(np.load(path('alt.npy'))).save(
            os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
        p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    # companion relief in the sheet's inks: cream, woodland green, engraved
    # brown, bare rock, then the glacier blue-white of the summits
    ramp = [[233, 224, 200], [222, 219, 190], [207, 213, 181], [198, 208, 176],
            [196, 200, 165], [199, 189, 152], [200, 176, 139], [196, 163, 126],
            [189, 150, 114], [180, 139, 105], [171, 130, 99], [166, 128, 100],
            [176, 144, 118], [196, 170, 146], [212, 196, 178], [222, 218, 210],
            [228, 232, 234]]
    ramp_ft = [3200 + 450*i for i in range(len(ramp))]

    p('· projecting the glacier margins…')
    lines = glacier_lines(g)

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               lines=lines,
               ui=dict(exagDef=1.4, exagMax=4.0, contourM=30.48, rampLo=3100,
                       rampHi=10600, sheetA='1915 sheet', altName='1959 geology',
                       tourEx=[1.0, 0.006, 1.05, 1.9]),
               fit=dict(rms=round(fitd['rms'], 2), median=round(fitd['median'], 2),
                        n=fitd['n']))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('geology', geology), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
