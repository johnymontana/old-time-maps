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
import json, os, sys, urllib.request

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

# ------------------------------------------------------------------ stage 3
def encode():
    resample()
    g = make_grid()
    hgt = np.load(path('hgt.npy'))
    mask = np.load(path('mask.npy'))
    HW, HH, hmin, hmax = encode_height(hgt, mask, os.path.join(BUILD, 'height.webp'),
                                       HGT_W, log=p)
    encode_drape(np.load(path('drape.npy')), os.path.join(BUILD, 'drape.webp'), log=p)
    card = Image.open(os.path.join(BUILD, 'drape.webp'))
    card = card.resize((640, int(card.height*640/card.width)), Image.LANCZOS)
    card.save(os.path.join(BUILD, 'card.webp'), quality=82, method=6)
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
                       rampHi=10000, sheetA='Army sheets',
                       tourEx=[1.1, 0.008, 1.2, 2.6]))

STAGES = [('fetch', fetch), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
