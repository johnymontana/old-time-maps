#!/usr/bin/env python3
"""Nome, the Golden Beach — asset pipeline.

USGS Bulletin 533 (Moffit, 1913), the Nome quadrangle at 1:62,500 —
Plate III, the geologic map of the beach placers' source rocks, over
Plate I, Gerdine's 1904 topographic map of the same footprint, draped on
Terrarium elevations, with the district's GNIS-named placer creeks and
gulches riding the terrain as data.

There is no georeferenced base to correlate against — the Alaska HTMC
scans are Transverse Mercator, which lib/georef's QuadGeoref rejects — so
BOTH plates are fitted from their own printed graticule: the 5-minute net
of 64°25'–64°40' N × 165°00'–165°30' W drawn across each sheet.  The
crossings were located once with ruler-grid crops read by eye and refined
by a darkness-centroid profile (pipeline/measure.py); the measured pixel
positions live in the tables below, and a degree-1 fit in the sheet's
conic plane lands on every drawn crossing to about two pixels (~11 m).
The printed graticule is taken at face value: whatever offset the 1904
Coast-and-Geodetic control carries against modern datums rides along, and
the plate's own confession is kept: "Railroad unsurveyed; position
approximate."

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import json, math, os, sys, urllib.request, zipfile

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('NM_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc
from georef import Fit, fit_report, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS

PLATES = {  # Bulletin 533's two Nome-quadrangle plates, same footprint
    'plate3': 'https://pubs.usgs.gov/bul/0533/plate-3.pdf',   # 1913 geology
    'plate1': 'https://pubs.usgs.gov/bul/0533/plate-1.pdf',   # 1904 topography
}
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'DomesticNames/DomesticNames_AK_Text.zip')
BLOCK = (-165.5, -165.0, 64.4166667, 64.6666667)   # W, E, S, N — the printed neat

# The printed graticule, read once (measure.py): every drawn 5' crossing as
# (lon, lat, x_px, y_px) on the 300-dpi rasterisation.  The two top-left
# corners sit ~6 px off the net — engraving, or a century of paper — and the
# fit trims them; everything else holds to ~2 px.
GRAT3 = [  # Plate III, geologic map (5798 × 6285 px)
    (-165.500000, 64.66667, 313.2, 317.7), (-165.416667, 64.66667, 1070.1, 316.7),
    (-165.333333, 64.66667, 1820.8, 317.8), (-165.250000, 64.66667, 2573.4, 320.9),
    (-165.166667, 64.66667, 3323.9, 320.8), (-165.083333, 64.66667, 4077.0, 322.0),
    (-165.000000, 64.66667, 4829.2, 323.8),
    (-165.500000, 64.58334, 308.4, 2076.4), (-165.416667, 64.58334, 1065.3, 2076.8),
    (-165.333333, 64.58334, 1817.4, 2079.4), (-165.250000, 64.58334, 2571.7, 2083.2),
    (-165.166667, 64.58334, 3323.4, 2084.0), (-165.083333, 64.58334, 4078.8, 2083.3),
    (-165.000000, 64.58334, 4831.8, 2084.0),
    (-165.500000, 64.50000, 300.3, 3834.3), (-165.416667, 64.50000, 1057.3, 3836.2),
    (-165.333333, 64.50000, 1814.0, 3838.4), (-165.250000, 64.50000, 2569.9, 3841.1),
    (-165.166667, 64.50000, 3323.5, 3841.1), (-165.083333, 64.50000, 4080.5, 3840.9),
    (-165.000000, 64.50000, 4836.2, 3841.7),
    (-165.500000, 64.41667, 292.6, 5590.6), (-165.416667, 64.41667, 1050.3, 5592.7),
    (-165.333333, 64.41667, 1807.8, 5595.0), (-165.250000, 64.41667, 2566.7, 5598.7),
    (-165.166667, 64.41667, 3322.7, 5599.2), (-165.083333, 64.41667, 4081.4, 5599.1),
    (-165.000000, 64.41667, 4837.8, 5600.4),
]
GRAT1 = [  # Plate I, topographic map (5175 × 6229 px)
    (-165.500000, 64.66667, 334.0, 326.7), (-165.416667, 64.66667, 1092.5, 329.8),
    (-165.333333, 64.66667, 1842.8, 335.0), (-165.250000, 64.66667, 2595.0, 341.3),
    (-165.166667, 64.66667, 3348.3, 343.2), (-165.083333, 64.66667, 4101.7, 345.9),
    (-165.000000, 64.66667, 4853.7, 347.8),
    (-165.500000, 64.58334, 322.5, 2083.8), (-165.416667, 64.58334, 1080.5, 2089.2),
    (-165.333333, 64.58334, 1831.8, 2095.1), (-165.250000, 64.58334, 2586.2, 2101.1),
    (-165.166667, 64.58334, 3340.1, 2103.4), (-165.083333, 64.58334, 4095.3, 2104.3),
    (-165.000000, 64.58334, 4848.2, 2106.3),
    (-165.500000, 64.50000, 306.1, 3844.0), (-165.416667, 64.50000, 1065.3, 3850.2),
    (-165.333333, 64.50000, 1819.9, 3855.1), (-165.250000, 64.50000, 2576.3, 3859.3),
    (-165.166667, 64.50000, 3330.9, 3862.2), (-165.083333, 64.50000, 4087.9, 3864.1),
    (-165.000000, 64.50000, 4851.1, 3866.4),
    (-165.500000, 64.41667, 288.2, 5601.3), (-165.416667, 64.41667, 1049.1, 5608.8),
    (-165.333333, 64.41667, 1805.7, 5614.0), (-165.250000, 64.41667, 2564.7, 5618.9),
    (-165.166667, 64.41667, 3322.3, 5622.7), (-165.083333, 64.41667, 4081.6, 5624.9),
    (-165.000000, 64.41667, 4838.1, 5625.9),
]

LCC = Lcc(64.47, 64.62, -165.25)
MARGIN = 0.0007
TEX_W, HGT_W, ALT_W = 2560, 1707, 2048
DEM_ZOOM, DEM_BOX = 12, (-165.66, -164.84, 64.2567, 64.8267)
CLAMP = (0, 700)                      # Norton Sound holds the floor at sea level
PAPER = (250, 236, 204)

# The district's placer creeks and gulches — the workings Bulletin 533
# describes stream by stream.  The current GNIS Alaska file carries no
# feature_class=Mine at all (the class was retired), so the named placer
# ground itself is the data layer; coordinates come from GNIS rows of these
# exact names in-block.
PLACERS = {
    'Anvil Creek', 'Snow Gulch', 'Glacier Creek', 'Dexter Creek',
    'Left Fork Dexter Creek', 'Dry Creek', 'Osborn Creek', 'Grass Gulch',
    'Buster Creek', 'Newton Gulch', 'Specimen Gulch', 'Little Specimen Gulch',
    'Nekula Gulch', 'Holyoke Creek', 'Saturday Creek', 'Bourbon Creek',
    'Center Creek', 'Little Creek', 'Cooper Gulch', 'Peluk Creek',
    'Hastings Creek', 'Nugget Creek', 'Rock Creek', 'Lindblom Creek',
    'Mountain Creek', 'Gold Creek', 'Banner Creek', 'Bonanza Gulch',
    'Quartz Gulch', 'Moonlight Creek', 'Flat Creek', 'Sledge Creek',
    'Boulder Creek', 'Balto Creek', 'Goldengate Creek', 'Grouse Gulch',
    'American Creek', 'American Gulch',
}
DITCHES = {'Seward Ditch'}

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]], MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 1
def fetch():
    for key, url in PLATES.items():
        jpg = path(key.replace('plate', 'plate-') + '.jpg')
        if not os.path.exists(jpg):
            pdf = jpg[:-4] + '.pdf'
            if not os.path.exists(pdf):
                p('· downloading %s…' % key)
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=600) as r:
                    open(pdf, 'wb').write(r.read())
            p('· rasterising %s at 300 dpi…' % key)
            import pypdfium2 as pdfium
            page = pdfium.PdfDocument(pdf)[0]
            page.render(scale=300/72).to_pil().convert('RGB').save(jpg, quality=95)
    if not os.path.exists(path('gnis_ak.zip')):
        p('· downloading GNIS domestic names (AK)…')
        req = urllib.request.Request(GNIS, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_ak.zip'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def graticule_fit(rows, name):
    """Degree-1 fit, printed graticule → plate pixels, in the LCC plane."""
    lon = np.array([r[0] for r in rows]); lat = np.array([r[1] for r in rows])
    PX = np.array([r[2] for r in rows]); PY = np.array([r[3] for r in rows])
    X, Y = LCC.fwd(lon, lat)
    fit = Fit(X, Y, PX, PY, 1)
    px, py = fit.apply(X, Y)
    keep = np.hypot(px-PX, py-PY) < 6.0            # trims the two warped corners
    fit = Fit(X[keep], Y[keep], PX[keep], PY[keep], 1)
    # ground scale of the plate from the fit itself
    x0, y0 = fit.apply(*LCC.fwd(-165.25, 64.54167))
    x1, y1 = fit.apply(*LCC.fwd(-165.24, 64.54167))
    mpp = 0.01*111320*math.cos(math.radians(64.54))/float(np.hypot(x1-x0, y1-y0))
    fit_report('%s (%d/%d crossings)' % (name, int(keep.sum()), len(rows)), fit, mpp)
    d = dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
             cx=fit.cx.tolist(), cy=fit.cy.tolist(),
             rms=round(fit.rms, 2), median=round(fit.median, 2),
             m_per_px=round(mpp, 3), n=int(keep.sum()))
    return fit, d, (PX, PY, keep)

def georef():
    """Fit both plates from their printed graticules (no correlation —
    there is nothing already-georeferenced here to correlate against)."""
    if os.path.exists(path('fits.json')):
        p('· georeference cached'); return
    fetch()
    fits = {}
    for key, rows in (('plate3', GRAT3), ('plate1', GRAT1)):
        fit, d, (PX, PY, keep) = graticule_fit(rows, key)
        fits[key] = d
        im = Image.open(path(key.replace('plate', 'plate-') + '.jpg'))
        lon = np.array([r[0] for r in rows]); lat = np.array([r[1] for r in rows])
        fx, fy = fit.apply(*LCC.fwd(lon, lat))
        overlay(im, {(255, 40, 40): list(zip(fx, fy))},
                path('qa_georef_%s.png' % key), 1400)
    json.dump(fits, open(path('fits.json'), 'w'))
    p('  QA overlays in work/qa_georef_plate*.png — crosses must sit on the net')

class SavedFit:
    def __init__(self, d):
        from proj import poly_basis
        self.Xm, self.Ym, self.sX, self.deg = d['Xm'], d['Ym'], d['sX'], d['deg']
        self.cx, self.cy = np.array(d['cx']), np.array(d['cy'])
        self._pb = poly_basis
    def apply(self, X, Y):
        A = self._pb((np.asarray(X, float)-self.Xm)/self.sX,
                     (np.asarray(Y, float)-self.Ym)/self.sX, self.deg)
        return A@self.cx, A@self.cy

def resample_plate(fit, jpg, grid, frame, log):
    """Pull one plate onto the conic grid; clamp to its graticule frame."""
    _, _, LON, LAT = grid.lonlat()
    src = np.asarray(Image.open(jpg).convert('RGB'), dtype=np.float32)
    X, Y = LCC.fwd(LON, LAT)
    SX, SY = fit.apply(X, Y)
    inside = ((LON >= BLOCK[0]) & (LON <= BLOCK[1]) &
              (LAT >= BLOCK[2]) & (LAT <= BLOCK[3]))
    fx0, fy0, fx1, fy1 = frame
    ok = inside & (SX > fx0-8) & (SX < fx1+8) & (SY > fy0-8) & (SY < fy1+8)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((grid.TH, grid.TW, 3), np.float32); tex[:] = PAPER
    for c in range(3):
        tex[:, :, c][ok] = ndimage.map_coordinates(
            src[:, :, c], [SY[ok], SX[ok]], order=1, mode='nearest')
    del src
    log('  %d texels draped' % int(ok.sum()))
    return tex, inside

def frame_of(rows):
    xs = [r[2] for r in rows]; ys = [r[3] for r in rows]
    return min(xs), min(ys), max(xs), max(ys)

# ------------------------------------------------------------------ stage 3
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    fits = {k: SavedFit(d) for k, d in json.load(open(path('fits.json'))).items()}
    g = make_grid()
    p('· conic grid %d × %d  (%.0f × %.0f km)' % (g.TW, g.TH, g.kmw, g.kmh))
    GX, GY, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    p('  elevation %.0f – %.0f m' % (hgt.min(), hgt.max()))
    np.save(path('hgt.npy'), hgt)

    p('· resampling the 1913 geology…')
    tex, inside = resample_plate(fits['plate3'], path('plate-3.jpg'), g,
                                 frame_of(GRAT3), p)
    np.save(path('mask.npy'), inside)
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p('· resampling the 1904 topography…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    alt, _ = resample_plate(fits['plate1'], path('plate-1.jpg'), g2,
                            frame_of(GRAT1), p)
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def placers(g):
    """The named placer creeks and gulches, straight from GNIS."""
    z = zipfile.ZipFile(path('gnis_ak.zip'))
    f = z.open('Text/DomesticNames_AK.txt')
    hdr = f.readline().decode('utf-8-sig').strip().split('|')
    ix = {k: hdr.index(k) for k in ('feature_name', 'feature_class',
                                    'prim_lat_dec', 'prim_long_dec')}
    out = []
    for ln in f:
        c = ln.decode('utf-8', 'replace').split('|')
        name = c[ix['feature_name']].strip()
        if name not in PLACERS and name not in DITCHES: continue
        if c[ix['feature_class']] not in ('Stream', 'Valley', 'Canal'): continue
        try:
            lat = float(c[ix['prim_lat_dec']]); lon = float(c[ix['prim_long_dec']])
        except ValueError:
            continue
        if not (BLOCK[0] <= lon <= BLOCK[1] and BLOCK[2] <= lat <= BLOCK[3]): continue
        u, v = g.uv(lon, lat)
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        kind = 'ditch' if name in DITCHES else 'placer'
        out.append(dict(n=name[:26], u=round(u, 5), v=round(v, 5), c=kind))
    out.sort(key=lambda m: (m['n'], m['v']))
    return out[:60]

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
    p('· encoding the 1904 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[233, 224, 202], [225, 216, 192], [215, 206, 180], [205, 196, 168],
            [196, 185, 156], [190, 175, 145], [186, 165, 134], [181, 154, 123],
            [174, 143, 112], [166, 133, 103], [158, 125, 97], [153, 121, 96],
            [158, 129, 107], [170, 145, 126], [185, 165, 149]]
    ramp_ft = [1 + 150*i for i in range(len(ramp))]    # sea level to ~2,100 ft

    p('· gathering the placer creeks…')
    M = placers(g)
    p('  %d placer names kept' % len(M))

    fits = json.load(open(path('fits.json')))
    worst = max(fits.values(), key=lambda d: d['rms'])
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=2.0, exagMax=6.0, contourM=7.62, mineDist=0.50,
                       mineGlyph='⚒', rampLo=1, rampHi=2100,
                       sheetA='1913 geology', altName='1904 topography',
                       tourEx=[1.05, 0.01, 1.15, 2.4]),
               fit=dict(rms=worst['rms'], median=worst['median'],
                        n=sum(d['n'] for d in fits.values())))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
