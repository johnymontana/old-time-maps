#!/usr/bin/env python3
"""The Flathead Country — asset pipeline.

Two Corps of Engineers Progressive Military Map advance sheets — FLATHEAD LAKE
(compiled 1915–20, printed 1920, tan paper) and KALISPELL (compiled 1919,
Army Map Service printing 1943, white paper) — joined at the 48th parallel
into one drape over Terrarium elevations on a local Lambert conformal grid.

Both scans carry their georeference (polyconic on NAD27, 10.58 m/px); the work
here is datum-shifting the grid into NAD27, cropping each sheet to its
neatline, tone-matching the 1943 printing to the 1920 paper, and drawing the
join honestly as a one-texel hairline.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, resample, encode.  Intermediates cache in work/ (gitignored);
DEM tiles share the repo-wide cache in ../work/dem/.
"""
import json, math, os, sys, urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('FH_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, LINES

# --- the scans (HTMC GeoTIFFs, georeferenced, public domain) ---------------
S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/'
QUADS = [  # id, file, neatline (W, E, S, N) in the sheet's own NAD27 graticule
    dict(id='flathead1920', url=S3+'MT_Flathead%20Lake_472710_1920_125000_geo.tif',
         neat=(-114.5, -114.0, 47.5, 48.0)),
    dict(id='kalispell1943', url=S3+'MT_Kalispell_472788_1943_125000_geo.tif',
         neat=(-114.5, -114.0, 48.0, 48.5)),
]
SEAM_LAT = 48.0
# --- grid ------------------------------------------------------------------
LCC = Lcc(47.7, 48.3, -114.25)
MARGIN = 0.0013                 # rad of arc around the neatlines (~8 km)
TEX_W, HGT_W = 2560, 1707
DEM_ZOOM, DEM_BOX = 12, (-114.68, -113.82, 47.38, 48.62)
CLAMP = (700, 3300)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    lons = [q['neat'][i] for q in QUADS for i in (0, 1)]
    lats = [q['neat'][i] for q in QUADS for i in (2, 3)]
    g = Grid.around(LCC, lons, lats, MARGIN, TEX_W)
    return g

# ------------------------------------------------------------------ stage 1
def fetch():
    for q in QUADS:
        dst = path(q['id'] + '.tif')
        if os.path.exists(dst):
            p('· %s cached' % q['id']); continue
        p('· downloading %s…' % q['id'])
        req = urllib.request.Request(q['url'], headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, open(dst, 'wb') as f:
            f.write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy')):
        p('· grid cached'); return
    fetch()
    g = make_grid()
    p('· conic grid %d × %d  (%.0f × %.0f km)' % (g.TW, g.TH, g.kmw, g.kmh))
    GX, GY, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT)
    del mos
    p('  elevation %.0f – %.0f m' % (hgt.min(), hgt.max()))
    np.save(path('hgt.npy'), hgt)

    # the grid in the sheets' datum, once
    lon27, lat27 = wgs84_to_nad27(LON, LAT)

    tex = np.zeros((g.TH, g.TW, 3), np.float32)
    tex[:] = (238, 228, 208)                       # paper tone under the collar
    mask = np.zeros((g.TH, g.TW), bool)
    stats = {}
    for q in QUADS:
        im = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(im)
        W, E, S, N = q['neat']
        inside = (lon27 >= W) & (lon27 <= E) & (lat27 >= S) & (lat27 <= N)
        px, py = qr.to_px(lon27[inside], lat27[inside])
        src = np.asarray(im.convert('RGB'), dtype=np.float32); del im
        px = np.clip(px, 0, src.shape[1]-1); py = np.clip(py, 0, src.shape[0]-1)
        p('· resampling %s (%d texels)…' % (q['id'], int(inside.sum())))
        for c in range(3):
            tex[:, :, c][inside] = ndimage.map_coordinates(
                src[:, :, c], [py, px], order=1, mode='nearest')
        del src
        mask |= inside
        # strip statistics for the tone match, taken 0.02°–0.10° off the seam
        strip = inside & (np.abs(lat27 - SEAM_LAT) > 0.02) & (np.abs(lat27 - SEAM_LAT) < 0.10)
        stats[q['id']] = [(tex[:, :, c][strip].mean(), tex[:, :, c][strip].std())
                          for c in range(3)]

    # tone-match the 1943 printing to the 1920 paper
    north = mask & (lat27 >= SEAM_LAT)
    p('· tone-matching the 1943 sheet to the 1920 paper…')
    for c in range(3):
        ms, ss = stats['flathead1920'][c]
        mn, sn = stats['kalispell1943'][c]
        a = float(np.clip(ss/max(sn, 1e-3), 0.7, 1.3)); b = ms - a*mn
        tex[:, :, c][north] = tex[:, :, c][north]*a + b

    # the join, drawn honestly: a quiet one-texel hairline at 48°
    texel_lat = (g.Y1-g.Y0)/g.TH * 57.29578
    seam = mask & (np.abs(lat27 - SEAM_LAT) < texel_lat*0.6)
    tex[seam] = tex[seam]*0.55 + np.array([96, 86, 74])*0.45

    np.save(path('drape.npy'), tex.astype(np.uint8))
    np.save(path('mask.npy'), mask)
    json.dump(dict(TW=g.TW, TH=g.TH), open(path('grid.json'), 'w'))

    # QA: landmarks through the full chain onto each scan
    for q in QUADS:
        im = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(im)
        pts = []
        for n, la, lo, *_ in CITIES:
            lo27, la27 = wgs84_to_nad27(lo, la)
            W, E, S, N = q['neat']
            if W <= lo27 <= E and S <= la27 <= N:
                pts.append(qr.to_px(lo27, la27))
        overlay(im, {(255, 40, 40): pts}, path('qa_%s.png' % q['id']))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//4, g.TH//4)).save(path('qa_drape.png'))
    p('  QA overlays in work/')

# ------------------------------------------------- the 1908 county map
JAQ_URL = 'https://www.mtmemory.org/assets/downloadwiz/741141'
ALT_W = TEX_W//2

def jaqueth():
    """Jaqueth & Walters' 1908 county map as the middle layer."""
    if os.path.exists(path('alt.npy')):
        p('· 1908 map cached'); return
    resample()
    import numpy as _np
    from reg import smooth_feature, register, fit_trimmed
    if not os.path.exists(path('jaqueth1908.jpg')):
        p('· downloading the 1908 map from the Montana History Portal…')
        req = urllib.request.Request(JAQ_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=600) as r:
            open(path('jaqueth1908.jpg'), 'wb').write(r.read())
    p('· reading the 1908 map…')
    rgb = np.asarray(Image.open(path('jaqueth1908.jpg')).convert('RGB'), dtype=np.uint8)
    jf = smooth_feature(rgb)
    # coarse alignment on darkness masses (the lake), not the township grid —
    # two 6-mile lattices correlate at false scales; the lake cannot
    dark = lambda a: ndimage.gaussian_filter(
        ((255.0 - a.mean(2, dtype=np.float32)) > 75).astype(np.float32), 1.5)
    jA = dark(rgb)
    # zero the sheets' frames and collars so borders can't register to borders
    mh, mw = int(jf.shape[0]*0.04), int(jf.shape[1]*0.04)
    for a in (jf, jA):
        a[:mh, :] = 0; a[-mh:, :] = 0; a[:, :mw] = 0; a[:, -mw:] = 0
    targets = []
    from georef import QuadGeoref
    for q in QUADS:
        qim = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(qim)
        qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8)
        W_, E_, S_, N_ = q['neat']
        x0, y0 = qr.to_px(W_, N_); x1, y1 = qr.to_px(E_, S_)
        box = (int(min(y0, y1))+8, int(max(y0, y1))-8,
               int(min(x0, x1))+8, int(max(x0, x1))-8)
        qfeat, qA = smooth_feature(qrgb), dark(qrgb)
        for a in (qfeat, qA):
            a[:box[0], :] = 0; a[box[1]:, :] = 0
            a[:, :box[2]] = 0; a[:, box[3]:] = 0
        targets.append(dict(name=q['id'], feat=qfeat, featA=qA,
                            to_px=qr.to_px, m_per_px=qr.scale[0]))
        del qrgb
    lons = np.arange(-114.55, -113.94, 0.09)
    lats = np.arange(47.47, 48.52, 0.085)
    # seed: two labelled townsites read once off the sheet — Somers at the
    # lake's head, Polson at its foot — set scale, rotation and shift; every
    # actual control point below is found by correlation, not by hand
    p('· seeding from Somers and Polson…')
    g = make_grid()
    ANCHORS = [((48.080, -114.221), (3744.0, 3050.0)),    # Somers
               ((47.693, -114.163), (3880.0, 4060.0))]    # Polson
    (llA, pxA), (llB, pxB) = ANCHORS
    cA = np.array(LCC.fwd(llA[1], llA[0]), float)
    cB = np.array(LCC.fwd(llB[1], llB[0]), float)
    pA = np.array(pxA); pB = np.array(pxB)
    dc, dp = cB-cA, pB-pA
    s_ = np.hypot(*dp)/np.hypot(*dc)
    th_ = math.atan2(dp[1], dp[0]) - math.atan2(-dc[1], dc[0])
    m_scan = 6371000.0*np.hypot(*dc)/np.hypot(*dp)
    Rm_ = np.array([[math.cos(th_), -math.sin(th_)], [math.sin(th_), math.cos(th_)]])
    p('  seed scale ≈ %.1f m/px' % m_scan)

    class SeedAff:
        def apply(self, X, Y):
            dX = np.asarray(X, float)-cA[0]; dY = np.asarray(Y, float)-cA[1]
            vx = Rm_[0, 0]*dX + Rm_[0, 1]*(-dY)
            vy = Rm_[1, 0]*dX + Rm_[1, 1]*(-dY)
            return pA[0] + vx*s_, pA[1] + vy*s_

    p('· correlating the 1908 map against the Army sheets…')
    X, Y, gx, gy, _ = register(jf, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=SeedAff(),
                               pw=110, sw=240, scan_A=jA, log=p)
    if len(gx) < 10: raise SystemExit('too few 1908 GCPs')
    fit2, _ = fit_trimmed(X, Y, gx, gy, 1, name='1908 pass 1',
                          m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(jf, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit2,
                               pw=110, sw=60, log=p)
    if len(gx) < 10: raise SystemExit('too few 1908 GCPs')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='1908 fit',
                            m_per_px=m_scan, log=p)

    g = make_grid()
    from encode import Grid as _Grid
    g2 = _Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON, LAT = g2.lonlat()
    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    SX, SY = fit.apply(*LCC.fwd(lon27, lat27))
    inside = (SX > 1) & (SX < rgb.shape[1]-2) & (SY > 1) & (SY < rgb.shape[0]-2)
    src = rgb.astype(np.float32)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g2.TH, g2.TW, 3), np.float32)
    tex[:] = (233, 224, 200)
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
def encode():
    jaqueth()
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
        p('· encoding the 1908 layer…')
        Image.fromarray(np.load(path('alt.npy'))).save(
            os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
        p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    # companion relief in the sheets' inks: valley paper up to sepia ridge
    ramp = [[236, 226, 202], [232, 220, 192], [224, 210, 178], [214, 198, 164],
            [202, 184, 150], [190, 171, 139], [178, 159, 130], [166, 148, 122],
            [155, 138, 115], [146, 130, 109], [140, 124, 105], [150, 136, 118],
            [168, 156, 138], [190, 180, 162]]
    ramp_ft = [2800 + 500*i for i in range(len(ramp))]

    lines = []
    for L in LINES:
        pts = [[round(float(u), 5), round(float(v), 5)]
               for u, v in (g.uv(lo, la) for la, lo in L['pts'])]
        lines.append(dict(id=L['id'], name=L['name'], color=L['color'],
                          dash=L.get('dash', 0), pts=pts))

    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               lines=lines,
               ui=dict(exagDef=1.7, exagMax=6.0, contourM=30.48, rampLo=2700,
                       rampHi=10000, sheetA='Army sheets', altName='1908 county map',
                       tourEx=[1.1, 0.008, 1.2, 2.6]))

STAGES = [('fetch', fetch), ('resample', resample), ('jaqueth', jaqueth), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
