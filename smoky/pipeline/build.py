#!/usr/bin/env python3
"""The Knoxville Folio — asset pipeline.

Geologic Atlas of the United States, Folio 16 (Arthur Keith, 1895): the
Knoxville sheet, 35°30'–36° N by 83°30'–84° W — the Great Valley of East
Tennessee in reds and pinks, the grey Ocoee mass of the Great Smoky
Mountains thrust over it, and the four limestone coves worn through that
thrust sheet — draped over Terrarium elevations, with the folio's own
engraved topography sheet as the middle layer and the crest's named gaps
(GNIS) riding the terrain as data.

Both plates are rasterised from the pubs.usgs.gov PDFs and registered by
correlation against the 1895 HTMC scan of the same quadrangle, which
carries the USGS's own polyconic georeference; the folio was printed on
that very base, so the fits are tight.

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
WORK = os.environ.get('SM_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, NOTABLE_GAPS

GF16 = 'https://pubs.usgs.gov/gf/016/%s.pdf'
S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/TN/'
BASE_URL = S3 + 'TN_Knoxville_153456_1895_125000_geo.tif'
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'Archive/MainDomestic/%s_Features_20210825.txt')
STATES = ('TN', 'NC')

# The two folio plates drawn on the same engraved base.  'area' is the
# primary drape, 'topo' the middle layer.
PLATES = [dict(id='area', pdf='quad-area'),
          dict(id='topo', pdf='quad-topography')]

NEAT = (-84.0, -83.5, 35.5, 36.0)   # the quad's graticule box (NAD27)
# The map body inside each plate raster, as fractions of the sheet: the
# folio prints a legend column either side of the neat, plus title and
# credit bands.  Measured on the areal plate at 300 dpi (neat at
# x 520–4790, y 560–5810 of 5512 × 6514) and padded inward a little.
FRAME = (0.090, 0.873, 0.082, 0.897)      # x0, x1, y0, y1

LCC = Lcc(35.6, 35.9, -83.75)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2560, 1365, 1664
DEM_ZOOM, DEM_BOX = 12, (-84.20, -83.30, 35.32, 36.18)
CLAMP = (180, 2150)
PAPER = (243, 224, 192)                   # the folio's warm cream
DPI = 300                                 # 1:125,000 at 300 dpi = 10.58 m/px

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [NEAT[0], NEAT[1]], [NEAT[2], NEAT[3]], MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 1
def fetch():
    if not os.path.exists(path('knoxville1895.tif')):
        p('· downloading the 1895 base quad…')
        req = urllib.request.Request(BASE_URL, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, open(path('knoxville1895.tif'), 'wb') as f:
            f.write(r.read())
    for q in PLATES:
        jpg = path('gf16_%s.jpg' % q['id'])
        if os.path.exists(jpg): continue
        pdf = path('gf016_%s.pdf' % q['pdf'])
        if not os.path.exists(pdf):
            p('· downloading folio plate %s…' % q['pdf'])
            req = urllib.request.Request(GF16 % q['pdf'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=600) as r:
                open(pdf, 'wb').write(r.read())
        p('· rasterising %s at %d dpi…' % (q['pdf'], DPI))
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(pdf)[0]
        page.render(scale=DPI/72).to_pil().convert('RGB').save(jpg, quality=95)
    for st in STATES:
        f = path('gnis_%s.txt' % st)
        if not os.path.exists(f):
            p('· downloading GNIS names (%s, 2021 archive)…' % st)
            req = urllib.request.Request(GNIS % st, headers={'User-Agent': 'old-time-maps/1.0'})
            with urllib.request.urlopen(req, timeout=300) as r:
                open(f, 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its
    12-px neighbourhood.  Sees the brown contour plate — the ink the folio
    and its base actually share — through the areal sheet's colour washes,
    where the black+blue mask of lib/reg goes nearly blind."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

def georef():
    """Register each folio plate against the 1895 base it was printed on.

    The target is masked to its own neatline and the plate to its printed
    frame, so the legend columns, the title band and the credit band have
    nothing to correlate with."""
    if os.path.exists(path('fits.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed

    qim = Image.open(path('knoxville1895.tif'))
    qr = QuadGeoref(qim)
    qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
    qf = ink(qrgb); del qrgb
    W, E, S, N = NEAT
    x0, y0 = qr.to_px(W, N); x1, y1 = qr.to_px(E, S)
    qf[:int(y0)+8, :] = 0; qf[int(y1)-8:, :] = 0
    qf[:, :int(x0)+8] = 0; qf[:, int(x1)-8:] = 0
    target = [dict(name='knoxville1895', feat=qf, to_px=qr.to_px,
                   m_per_px=qr.scale[0])]
    lons = np.arange(W+0.035, E-0.02, 0.045)
    lats = np.arange(S+0.035, N-0.02, 0.045)

    fits = {}
    for q in PLATES:
        p('· [%s] reading the plate…' % q['id'])
        rgb = np.asarray(Image.open(path('gf16_%s.jpg' % q['id'])), dtype=np.uint8)
        plate_f = ink(rgb); del rgb
        ph, pw2 = plate_f.shape
        fx0, fx1, fy0, fy1 = FRAME
        plate_f[:int(ph*fy0), :] = 0; plate_f[int(ph*fy1):, :] = 0
        plate_f[:, :int(pw2*fx0)] = 0; plate_f[:, int(pw2*fx1):] = 0

        X, Y, gx, gy, m_per_px = register(plate_f, target, LCC, lons, lats,
                                          m_scan_hint=10.58, z_lo=0.86, z_hi=1.16,
                                          pw=150, sw=130, log=p)
        if len(gx) < 12: raise SystemExit('%s: too few GCPs' % q['id'])
        fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name=q['id']+' pass 1',
                              m_per_px=m_per_px, log=p)
        X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                                   m_scan_hint=m_per_px, seed_fit=fit1,
                                   pw=150, sw=200, log=p)
        fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name=q['id']+' pass 2',
                              m_per_px=m_per_px, log=p)
        X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                                   m_scan_hint=m_per_px, seed_fit=fit2,
                                   pw=150, sw=45, log=p)
        if len(gx) < 14: raise SystemExit('%s: too few GCPs' % q['id'])
        fit, keep = fit_trimmed(X, Y, gx, gy, 2, name=q['id']+' fit',
                                m_per_px=m_per_px, log=p)
        fits[q['id']] = dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                             cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                             rms=round(fit.rms, 2), median=round(fit.median, 2),
                             worst=round(fit.worst, 2),
                             m_per_px=round(m_per_px, 3), n=int(keep.sum()))
        im = Image.open(path('gf16_%s.jpg' % q['id']))
        overlay(im, {(255, 40, 40): list(zip(gx[keep], gy[keep]))},
                path('qa_georef_%s.png' % q['id']), 1500)
    json.dump(fits, open(path('fits.json'), 'w'))
    p('  QA overlays in work/qa_georef_*.png')

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

# ------------------------------------------------------------------ stage 3
def _drape_plate(plate_id, fit, g, lon27, lat27, inside):
    """Resample one plate onto a grid, clamped to the plate's printed frame."""
    src = np.asarray(Image.open(path('gf16_%s.jpg' % plate_id)).convert('RGB'),
                     dtype=np.float32)
    sh, sw = src.shape[:2]
    fx0, fx1, fy0, fy1 = FRAME
    X27, Y27 = LCC.fwd(lon27, lat27)
    SX, SY = fit.apply(X27, Y27)
    ok = (inside & (SX > sw*fx0) & (SX < sw*fx1) &
          (SY > sh*fy0) & (SY < sh*fy1))
    np.clip(SX, 0, sw-1, out=SX); np.clip(SY, 0, sh-1, out=SY)
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    for c in range(3):
        tex[:, :, c][ok] = ndimage.map_coordinates(
            src[:, :, c], [SY[ok], SX[ok]], order=1, mode='nearest')
    del src
    p('  %s: %d texels drawn' % (plate_id, int(ok.sum())))
    return np.clip(tex, 0, 255)

def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    fits = {k: SavedFit(d) for k, d in json.load(open(path('fits.json'))).items()}
    g = make_grid()
    p('· conic grid %d × %d  (%.0f × %.0f km, %.1f m/texel)'
      % (g.TW, g.TH, g.kmw, g.kmh, g.m_per_texel))
    GX, GY, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    p('  elevation %.0f – %.0f m' % (hgt.min(), hgt.max()))
    np.save(path('hgt.npy'), hgt)

    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    inside = ((lon27 >= NEAT[0]) & (lon27 <= NEAT[1]) &
              (lat27 >= NEAT[2]) & (lat27 <= NEAT[3]))
    np.save(path('mask.npy'), inside)
    p('  on-sheet maximum %.0f m' % hgt[inside].max())

    p('· resampling the folio geology…')
    tex = _drape_plate('area', fits['area'], g, lon27, lat27, inside)
    np.save(path('drape.npy'), tex.astype(np.uint8))
    Image.fromarray(tex.astype(np.uint8)).resize((g.TW//3, g.TH//3)) \
         .save(path('qa_drape.png'))
    del tex

    p('· resampling the folio topography…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    in2 = ((lo2 >= NEAT[0]) & (lo2 <= NEAT[1]) &
           (la2 >= NEAT[2]) & (la2 <= NEAT[3]))
    alt = _drape_plate('topo', fits['topo'], g2, lo2, la2, in2)
    np.save(path('alt.npy'), alt.astype(np.uint8))
    Image.fromarray(alt.astype(np.uint8)).resize((g2.TW//3, g2.TH//3)) \
         .save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def gaps(g):
    """The block's named gaps, from the 2021 GNIS archive, thinned by cell.

    A gap is the only way through a ridge here, and this sheet is nothing
    but ridges: the Great Valley's folded limestone combs, the long wall of
    Chilhowee Mountain, and the state-line crest of the Smokies."""
    picks, seen = {}, set()
    for st in STATES:
        with open(path('gnis_%s.txt' % st), encoding='utf-8-sig') as f:
            hdr = f.readline().rstrip('\n').split('|')
            ix = {k: hdr.index(k) for k in ('FEATURE_NAME', 'FEATURE_CLASS',
                                            'PRIM_LAT_DEC', 'PRIM_LONG_DEC',
                                            'ELEV_IN_FT')}
            for ln in f:
                c = ln.rstrip('\n').split('|')
                if c[ix['FEATURE_CLASS']] != 'Gap': continue
                name = c[ix['FEATURE_NAME']].strip()
                if 'Gap' not in name: continue      # 'Rye Patch', 'The Narrows'
                try:
                    lat, lon = float(c[ix['PRIM_LAT_DEC']]), float(c[ix['PRIM_LONG_DEC']])
                except ValueError:
                    continue
                if not (NEAT[0] <= lon <= NEAT[1] and NEAT[2] <= lat <= NEAT[3]):
                    continue
                key = (name, round(lat, 4), round(lon, 4))
                if key in seen: continue
                seen.add(key)
                u, v = g.uv(lon, lat)
                if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
                try: ft = int(c[ix['ELEV_IN_FT']])
                except ValueError: ft = 0
                cell = (int(u*40), int(v*52))
                good = (name in NOTABLE_GAPS, ft, -len(name))
                if cell not in picks or good > picks[cell][0]:
                    picks[cell] = (good, dict(n=name[:26], u=round(u, 5),
                                              v=round(v, 5), ft=ft))
    out = [t[1] for t in sorted(picks.values(),
                                key=lambda t: (not t[0][0], -t[0][1]))[:80]]
    out.sort(key=lambda m: m['n'])
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
    p('· encoding the 1895 topography layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)
    p('  on-sheet relief %.0f – %.0f m (grid %.0f – %.0f m)'
      % (hgt[mask].min(), hgt[mask].max(), hmin, hmax))

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [620 + 430*i for i in range(len(ramp))]

    p('· picking the gaps…')
    G = gaps(g)
    p('  %d gaps kept' % len(G))

    fits = json.load(open(path('fits.json')))
    worst = max(fits.values(), key=lambda d: d['rms'])
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=G,
               ui=dict(exagDef=1.8, exagMax=6.0, contourM=30.48, mineDist=0.52,
                       mineGlyph='∪', rampLo=620, rampHi=6640,
                       sheetA='1895 geology', altName='1895 topography',
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
