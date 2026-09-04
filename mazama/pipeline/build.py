#!/usr/bin/env python3
"""Mazama — Crater Lake in Professional Paper 3 — asset pipeline.

USGS Professional Paper 3, *The Geology and Petrography of Crater Lake
National Park* (J. S. Diller and H. B. Patton, 1902).  Plate I, "Mt. Mazama
and Crater Lake National Park" — Mark B. Kerr's 1886 plane-table topography
with Diller's specimen localities numbered in red — draped over Terrarium
elevations, with Diller's coloured geologic map (Plate VI, same base) as the
middle layer and the 1886 Cleetwood soundings, printed inside the lake, as
the data layer.

Both plates are fitted from their own PRINTED GRATICULE.  There is no early
georeferenced base to correlate against: HTMC's oldest Crater Lake sheets are
the 1985 24k quads and a 1989 100k, ninety-nine years younger than the
survey, and they are Lambert conformal on NAD27 rather than the polyconic
lib/georef.QuadGeoref reads.  So the sheet is registered the way `nome/` is —
every drawn crossing of the plate's 5' net measured once by ruler-grid crops
and a darkness-centroid profile (pipeline/measure.py), then a polynomial fit
in the sheet's own conic plane.

The net is the park.  The act of 22 May 1902 bounded Crater Lake National
Park "north by the parallel forty-three degrees four minutes north latitude,
south by forty-two degrees forty-eight minutes north latitude, east by the
meridian one hundred and twenty-two degrees west longitude, and west by the
meridian one hundred and twenty-two degrees sixteen minutes west longitude,
having an area of two hundred and forty-nine square miles" — and those four
lines are the plate's neat lines.  Fitting the graticule georeferences the
statute.

The printed net is taken at face value: whatever offset the 1886 triangulation
carries against modern datums rides along.  It is measurable, and this sheet
measures it — see pipeline/qa.py, which correlates the drape against the 1985
Crater Lake West quad.  Diller's own vertical is honest about itself: his lake
surface is 6,239 feet where the model reads about sixty feet less.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import json, math, os, sys, urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('MZ_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc
from georef import Fit, fit_report, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, SOUNDINGS

REPORT = 'https://pubs.usgs.gov/pp/0003/report.pdf'          # 72.9 MB
PLATES = {'plate-1': 17,     # PL. I   1886 topography, specimen localities
          'plate-6': 37}     # PL. VI  Diller's areal geology, same base
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'DomesticNames/DomesticNames_OR_Text.zip')
BLOCK = (-122.266667, -122.0, 42.8, 43.066667)   # W, E, S, N — the 1902 park

# The printed graticule, read once (measure.py): every drawn crossing of the
# 5' net as (lon, lat, x_px, y_px) on the 300-dpi rasterisation.  Note the
# west column is the neat line at 122d16', one minute west of the first drawn
# 5' meridian, and the south row is the neat line at 42d48', two minutes below
# 42d50' — the park's statutory box is not a whole number of 5' cells.
GRAT1 = [   # Plate I, 1886 topography (2249 x 3217 px)
    (-122.266667, 43.066667, 236.2, 158.0), (-122.250000, 43.066667, 348.6, 157.8),
    (-122.166667, 43.066667, 918.2, 155.1), (-122.083333, 43.066667, 1485.4, 149.3),
    (-122.000000, 43.066667, 2060.2, 147.8),
    (-122.266667, 43.000000, 236.0, 778.0), (-122.250000, 43.000000, 348.9, 777.9),
    (-122.166667, 43.000000, 917.3, 777.2), (-122.083333, 43.000000, 1486.4, 775.0),
    (-122.000000, 43.000000, 2061.6, 775.3),
    (-122.266667, 42.916667, 233.5, 1556.2), (-122.250000, 42.916667, 347.6, 1556.2),
    (-122.166667, 42.916667, 916.9, 1556.4), (-122.083333, 42.916667, 1488.2, 1556.9),
    (-122.000000, 42.916667, 2062.6, 1557.6),
    (-122.266667, 42.833333, 233.8, 2334.2), (-122.250000, 42.833333, 347.1, 2334.6),
    (-122.166667, 42.833333, 917.1, 2334.9), (-122.083333, 42.833333, 1490.6, 2336.8),
    (-122.000000, 42.833333, 2064.5, 2339.0),
    (-122.266667, 42.800000, 233.5, 2642.6), (-122.250000, 42.800000, 347.3, 2642.8),
    (-122.166667, 42.800000, 916.3, 2646.7), (-122.083333, 42.800000, 1490.6, 2648.9),
    (-122.000000, 42.800000, 2063.9, 2650.3),
]
GRAT6 = [   # Plate VI, Diller's geology (2338 x 3266 px)
    (-122.266667, 43.066667, 176.9, 160.0), (-122.250000, 43.066667, 289.4, 159.4),
    (-122.166667, 43.066667, 862.3, 157.2), (-122.083333, 43.066667, 1432.6, 158.3),
    (-122.000000, 43.066667, 2002.7, 158.6),
    (-122.266667, 43.000000, 176.9, 776.4), (-122.250000, 43.000000, 289.9, 776.4),
    (-122.166667, 43.000000, 863.0, 775.4), (-122.083333, 43.000000, 1434.9, 774.5),
    (-122.000000, 43.000000, 2005.4, 774.5),
    (-122.266667, 42.916667, 175.7, 1550.1), (-122.250000, 42.916667, 289.7, 1550.3),
    (-122.166667, 42.916667, 862.7, 1549.7), (-122.083333, 42.916667, 1437.3, 1548.3),
    (-122.000000, 42.916667, 2007.9, 1548.0),
    (-122.266667, 42.833333, 175.7, 2322.8), (-122.250000, 42.833333, 289.7, 2323.1),
    (-122.166667, 42.833333, 862.1, 2323.1), (-122.083333, 42.833333, 1437.5, 2321.9),
    (-122.000000, 42.833333, 2009.2, 2320.8),
    (-122.266667, 42.800000, 175.5, 2631.4), (-122.250000, 42.800000, 289.5, 2631.6),
    (-122.166667, 42.800000, 862.0, 2632.5), (-122.083333, 42.800000, 1437.2, 2631.8),
    (-122.000000, 42.800000, 2011.3, 2631.7),
]

LCC = Lcc(42.85, 43.02, -122.13)
MARGIN = 0.0005                       # ~3.2 km of paper apron around the park
TEX_W, HGT_W, ALT_W = 2560, 1707, 1920
# The block is 22 x 30 km — the smallest in the gallery — so the terrain is
# sampled a zoom deeper than the usual 12: at z12 a Terrarium post is ~28 m
# here, which rounds the Devils Backbone and Llao Rock off the rim.
DEM_ZOOM, DEM_BOX = 13, (-122.43, -121.84, 42.64, 43.23)
CLAMP = (900, 3000)                   # Annie Creek's mouth to Mount Scott
PAPER = (250, 238, 210)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]], MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 1
def fetch():
    """PP 3 ships as one 73 MB report.pdf; the plates are pages inside it."""
    want = [k for k in PLATES if not os.path.exists(path(k + '.jpg'))]
    if want:
        pdf = path('pp0003_report.pdf')
        if not os.path.exists(pdf):
            p('· downloading Professional Paper 3 (73 MB)…')
            req = urllib.request.Request(REPORT, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=900) as r:
                open(pdf, 'wb').write(r.read())
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(pdf)
        for key in want:
            p('· rasterising %s at 300 dpi (PDF page %d)…' % (key, PLATES[key]))
            im = doc[PLATES[key]].render(scale=300/72).to_pil().convert('RGB')
            im.save(path(key + '.jpg'), quality=95)
    if not os.path.exists(path('gnis_or.zip')):
        p('· downloading GNIS domestic names (OR)…')
        req = urllib.request.Request(GNIS, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_or.zip'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def graticule_fit(rows, name):
    """Printed graticule -> plate pixels, in the sheet's own conic plane.

    Degree 1 first, so the residuals are readable as paper: Plate VI sits on
    its net at 1.2 px, Plate I at 3.1 px because its sheet carries a ~0.7 %
    keystone (its east edge is eighteen pixels taller than its west).  The
    degree-2 fit that follows absorbs exactly that and lands both plates
    inside a pixel and a half.  Nothing is trimmed: all 25 crossings are used.
    """
    lon = np.array([r[0] for r in rows]); lat = np.array([r[1] for r in rows])
    PX = np.array([r[2] for r in rows]); PY = np.array([r[3] for r in rows])
    X, Y = LCC.fwd(lon, lat)
    lin = Fit(X, Y, PX, PY, 1)
    fit = Fit(X, Y, PX, PY, 2)
    # ground scale of the plate, from the fit itself
    x0, y0 = fit.apply(*LCC.fwd(-122.13, 42.9333))
    x1, y1 = fit.apply(*LCC.fwd(-122.12, 42.9333))
    mpp = 0.01*111320*math.cos(math.radians(42.9333))/float(np.hypot(x1-x0, y1-y0))
    fit_report('%s deg 1 (%d crossings)' % (name, len(rows)), lin, mpp)
    fit_report('%s deg 2 (%d crossings)' % (name, len(rows)), fit, mpp)
    d = dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
             cx=fit.cx.tolist(), cy=fit.cy.tolist(),
             rms=round(fit.rms, 2), median=round(fit.median, 2),
             worst=round(fit.worst, 2), rms1=round(lin.rms, 2),
             m_per_px=round(mpp, 3), n=len(rows))
    # and the inverse, for reading printed values off the plate (the soundings)
    inv = Fit(PX, PY, X, Y, 2)
    d['inv'] = dict(Xm=inv.Xm, Ym=inv.Ym, sX=inv.sX, deg=inv.deg,
                    cx=inv.cx.tolist(), cy=inv.cy.tolist())
    return fit, d

def georef():
    """Fit both plates from their printed graticules — there is nothing
    already-georeferenced from this century, let alone that one, to correlate
    against."""
    if os.path.exists(path('fits.json')):
        p('· georeference cached'); return
    fetch()
    fits = {}
    for key, rows in (('plate-1', GRAT1), ('plate-6', GRAT6)):
        fit, d = graticule_fit(rows, key)
        fits[key] = d
        im = Image.open(path(key + '.jpg'))
        lon = np.array([r[0] for r in rows]); lat = np.array([r[1] for r in rows])
        fx, fy = fit.apply(*LCC.fwd(lon, lat))
        overlay(im, {(255, 40, 40): list(zip(fx, fy))},
                path('qa_georef_%s.png' % key), 1400)
    json.dump(fits, open(path('fits.json'), 'w'))
    p('  QA overlays in work/qa_georef_plate-*.png — crosses must sit on the net')

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

def frame_of(rows):
    xs = [r[2] for r in rows]; ys = [r[3] for r in rows]
    return min(xs), min(ys), max(xs), max(ys)

def resample_plate(fit, jpg, grid, frame, log):
    """Pull one plate onto the conic grid; clamp to its graticule frame so the
    collar, the title and the legend never drape."""
    _, _, LON, LAT = grid.lonlat()
    src = np.asarray(Image.open(jpg).convert('RGB'), dtype=np.float32)
    X, Y = LCC.fwd(LON, LAT)
    SX, SY = fit.apply(X, Y)
    inside = ((LON >= BLOCK[0]) & (LON <= BLOCK[1]) &
              (LAT >= BLOCK[2]) & (LAT <= BLOCK[3]))
    fx0, fy0, fx1, fy1 = frame
    ok = inside & (SX > fx0-3) & (SX < fx1+3) & (SY > fy0-3) & (SY < fy1+3)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((grid.TH, grid.TW, 3), np.float32); tex[:] = PAPER
    for c in range(3):
        tex[:, :, c][ok] = ndimage.map_coordinates(
            src[:, :, c], [SY[ok], SX[ok]], order=1, mode='nearest')
    del src
    log('  %d texels draped (%.0f%% of the grid)' % (int(ok.sum()), 100*ok.mean()))
    return tex, inside

# ------------------------------------------------------------------ stage 3
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    fits = {k: SavedFit(d) for k, d in json.load(open(path('fits.json'))).items()}
    g = make_grid()
    p('· conic grid %d × %d  (%.1f × %.1f km, %.1f m/texel)'
      % (g.TW, g.TH, g.kmw, g.kmh, g.m_per_texel))
    GX, GY, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    p('  elevation %.0f – %.0f m  (%.0f – %.0f ft)'
      % (hgt.min(), hgt.max(), hgt.min()/0.3048, hgt.max()/0.3048))
    np.save(path('hgt.npy'), hgt)

    p("· resampling Kerr's 1886 topography (Pl. I)…")
    tex, inside = resample_plate(fits['plate-1'], path('plate-1.jpg'), g,
                                 frame_of(GRAT1), p)
    np.save(path('mask.npy'), inside)
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p("· resampling Diller's geology (Pl. VI)…")
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    alt, _ = resample_plate(fits['plate-6'], path('plate-6.jpg'), g2,
                            frame_of(GRAT6), p)
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def soundings(g):
    """The 1886 Cleetwood soundings, off Plate I and onto the grid.

    Each depth is a figure printed inside the lake on the plate; the pixel
    positions in places.SOUNDINGS came from the same ruler-grid reading that
    produced the graticule tables, and the inverse of the plate's own
    graticule fit turns them into ground coordinates.  Dutton's party made
    168 casts; the plate prints these.
    """
    d = json.load(open(path('fits.json')))['plate-1']['inv']
    inv = SavedFit(d)
    px = np.array([s[0] for s in SOUNDINGS], float)
    py = np.array([s[1] for s in SOUNDINGS], float)
    X, Y = inv.apply(px, py)
    lon, lat = LCC.inv(X, Y)
    out = []
    for k, (_, _, ft) in enumerate(SOUNDINGS):
        u, v = g.uv(float(lon[k]), float(lat[k]))
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        out.append(dict(n='%s ft' % format(ft, ','), u=round(float(u), 5),
                        v=round(float(v), 5), c='sounding'))
    out.sort(key=lambda m: m['v'])
    return out

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
    p("· encoding Diller's geology layer…")
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    # the gallery's paper-toned hypsometric ramp, stretched over this block's
    # own range (Annie Creek's canyon mouth to Mount Scott)
    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    lo = int(hmin/0.3048/100)*100
    hi = int(hmax/0.3048/100 + 1)*100
    ramp_ft = [lo + round((hi-lo)*i/len(ramp)) for i in range(len(ramp))]

    p('· placing the 1886 soundings…')
    S = soundings(g)
    p('  %d depth figures placed' % len(S))

    fits = json.load(open(path('fits.json')))
    worst = max(fits.values(), key=lambda d: d['rms'])
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=S,
               ui=dict(exagDef=1.8, exagMax=6.0, contourM=30.48, mineDist=0.30,
                       mineGlyph='↧', rampLo=lo, rampHi=hi,
                       sheetA='1886 topography', altName="Diller's geology",
                       tourEx=[1.1, 0.02, 1.2, 2.2]),
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
