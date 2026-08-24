#!/usr/bin/env python3
"""The Silverton Folio — asset pipeline.

Geologic Atlas of the United States, Folio 120 (Cross, Howe & Ransome, 1905):
the Economic Geology sheet of the Silverton quadrangle — every lode, tunnel
and mill of the San Juan silver country drawn in red over the engraved base —
draped over Terrarium elevations, with the folio's Areal Geology sheet (the
caldera volcanics in colour) as the middle layer and the district's named
mines (GNIS) riding the terrain as data.

The 1901 Silverton 15-minute base is an HTMC GeoTIFF and carries its own
polyconic georeference; both folio plates are rasterised from the
pubs.usgs.gov PDFs and registered by correlation against that one base —
same survey, same engraving lineage, so the fits are tight.  The base is a
registration target only; the two folio sheets are the layers.

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
WORK = os.environ.get('SV_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, FAMOUS_MINES, MARQUEE_MINES

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CO/'
BASE_URL = S3 + 'CO_Silverton_234428_1901_62500_geo.tif'
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'DomesticNames/DomesticNames_CO_Text.zip')
# The live GNIS dropped man-made features in 2021; the mines live on in the
# frozen archive file, same S3 bucket, elevations included.
GNIS2021 = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
            'Archive/MainDomestic/CO_Features_20210825.txt')
PLATES = [  # the folio's two quadrangle sheets, both over the one 1901 base
    dict(id='econ', url='https://pubs.usgs.gov/gf/120/quad-economic.pdf'),
    dict(id='area', url='https://pubs.usgs.gov/gf/120/quad-area.pdf'),
]
NEAT = (-107.75, -107.5, 37.75, 38.0)        # the quad's graticule box (NAD27)
BLOCK = NEAT

LCC = Lcc(37.8, 37.95, -107.625)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2560, 1707, 2048
DEM_ZOOM, DEM_BOX = 12, (-107.91, -107.34, 37.59, 38.16)
CLAMP = (2500, 4320)                         # Handies Peak (14,048 ft) is in-block
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]],
                       MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 1
def fetch():
    if not os.path.exists(path('silverton1901.tif')):
        p('· downloading the 1901 base quad…')
        req = urllib.request.Request(BASE_URL, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, \
                open(path('silverton1901.tif'), 'wb') as f:
            f.write(r.read())
    for q in PLATES:
        jpg = path('gf120_%s.jpg' % q['id'])
        if not os.path.exists(jpg):
            pdf = path('gf120_%s.pdf' % q['id'])
            if not os.path.exists(pdf):
                p('· downloading folio %s sheet…' % q['id'])
                req = urllib.request.Request(q['url'],
                                             headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=600) as r:
                    open(pdf, 'wb').write(r.read())
            p('· rasterising the %s sheet at 300 dpi…' % q['id'])
            import pypdfium2 as pdfium
            page = pdfium.PdfDocument(pdf)[0]
            page.render(scale=300/72).to_pil().convert('RGB').save(jpg, quality=95)
    if not os.path.exists(path('gnis_co.zip')):
        p('· downloading GNIS domestic names (CO)…')
        req = urllib.request.Request(GNIS, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_co.zip'), 'wb').write(r.read())
    if not os.path.exists(path('gnis_co_2021.txt')):
        p('· downloading GNIS 2021 archive (CO, has the mines)…')
        req = urllib.request.Request(GNIS2021, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_co_2021.txt'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register both folio plates against the one 1901 base quad.

    The target is masked to its own neatline, so the plates' collars and
    legends have nothing to correlate with; only the page edges (scanner
    junk) are blanked on the plate side."""
    if os.path.exists(path('fits.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed

    def ink(rgb):
        """Linework as a local high-pass: anything markedly darker than its
        12-px neighbourhood — sees the shared engraved culture and contours
        through the areal sheet's colour washes and the economic sheet's
        red vein overprint alike."""
        m = rgb.mean(2, dtype=np.float32)
        f = (ndimage.gaussian_filter(m, 12) - m) > 30
        return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

    qim = Image.open(path('silverton1901.tif'))
    qr = QuadGeoref(qim)
    qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
    qf = ink(qrgb); del qrgb
    W, E, S, N = NEAT
    x0, y0 = qr.to_px(W, N); x1, y1 = qr.to_px(E, S)
    qf[:int(y0)+8, :] = 0; qf[int(y1)-8:, :] = 0
    qf[:, :int(x0)+8] = 0; qf[:, int(x1)-8:] = 0
    target = [dict(name='silverton1901', feat=qf, to_px=qr.to_px,
                   m_per_px=qr.scale[0])]
    p('· base scan %.2f m/px' % qr.scale[0])
    # run the lattice out to ~400 m of the neat so the fit never has to
    # extrapolate far at the sheet edges
    lons = np.arange(W+0.005, E-0.004, 0.011)
    lats = np.arange(S+0.005, N-0.004, 0.011)

    fits = {}
    for q in PLATES:
        p('· [%s] reading the plate…' % q['id'])
        rgb = np.asarray(Image.open(path('gf120_%s.jpg' % q['id'])), dtype=np.uint8)
        plate_f = ink(rgb); del rgb
        ph, pw2 = plate_f.shape
        plate_f[:int(ph*0.03), :] = 0; plate_f[int(ph*0.97):, :] = 0
        plate_f[:, :int(pw2*0.03)] = 0; plate_f[:, int(pw2*0.97):] = 0

        # plate ≈ 300 dpi of a 1:62,500 sheet → 5.29 m/px, and the HTMC
        # base scan is the same resolution, so z sweeps around 1
        X, Y, gx, gy, m_per_px = register(plate_f, target, LCC, lons, lats,
                                          m_scan_hint=5.29, z_lo=0.86, z_hi=1.16,
                                          pw=150, sw=130, log=p)
        if len(gx) < 12: raise SystemExit('%s: too few GCPs' % q['id'])
        fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name=q['id']+' pass 1',
                              m_per_px=m_per_px, log=p)
        X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                                   m_scan_hint=m_per_px, seed_fit=fit1,
                                   pw=150, sw=200, log=p)
        fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name=q['id']+' pass 2',
                              m_per_px=m_per_px, log=p)
        # The displacement between the folio lithograph and the quad
        # engraving varies at sub-kilometre scale: big patches average it
        # and plateau near 10 px.  Shrinking the patch down a pyramid —
        # 150 → 90 → 70 → 55 px — halves the residual twice over.
        fitn = fit2
        for pw_, sw_ in ((90, 32), (70, 24), (55, 20)):
            X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                                       m_scan_hint=m_per_px, seed_fit=fitn,
                                       pw=pw_, sw=sw_, log=p)
            if len(gx) < 14: raise SystemExit('%s: too few GCPs' % q['id'])
            fitn, keep = fit_trimmed(X, Y, gx, gy, 3, k=2.2,
                                     name='%s pw%d' % (q['id'], pw_),
                                     m_per_px=m_per_px, log=p)
        fit = fitn
        fits[q['id']] = dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                             cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                             rms=round(fit.rms, 2), median=round(fit.median, 2),
                             m_per_px=round(m_per_px, 3), n=int(keep.sum()))
        im = Image.open(path('gf120_%s.jpg' % q['id']))
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

def frame_box(fit, gray, span=160, inset=3, log=p):
    """The plate's map-body box in plate pixels.

    The fitted corner positions are only a guess — a degree-3 fit
    extrapolating the last few hundred metres to the neat can drift tens of
    pixels into the collar.  So each edge is snapped to the engraved border
    itself: the darkest long straight line within ±span of the guess."""
    W, E, S, N = NEAT
    cx, cy = LCC.fwd([W, E, W, E], [S, S, N, N])
    PX, PY = fit.apply(cx, cy)
    gx0, gx1 = float(PX.min()), float(PX.max())
    gy0, gy1 = float(PY.min()), float(PY.max())
    dark = np.maximum(0.0, 150.0 - gray)
    H, Wp = dark.shape
    yin = slice(int(gy0+300), int(gy1-300))
    xin = slice(int(gx0+300), int(gx1-300))
    def line_x(guess):
        a = max(0, int(guess-span)); b = min(Wp, int(guess+span))
        return a + int(np.argmax(dark[yin, a:b].sum(0)))
    def line_y(guess):
        a = max(0, int(guess-span)); b = min(H, int(guess+span))
        return a + int(np.argmax(dark[a:b, xin].sum(1)))
    x0, x1, y0, y1 = line_x(gx0), line_x(gx1), line_y(gy0), line_y(gy1)
    log('  frame: fit corners (%.0f,%.0f)-(%.0f,%.0f) → engraved (%d,%d)-(%d,%d)'
        % (gx0, gy0, gx1, gy1, x0, y0, x1, y1))
    return x0+inset, y0+inset, x1-inset, y1-inset

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

    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    inside = ((lon27 >= BLOCK[0]) & (lon27 <= BLOCK[1]) &
              (lat27 >= BLOCK[2]) & (lat27 <= BLOCK[3]))
    np.save(path('mask.npy'), inside)
    X27, Y27 = LCC.fwd(lon27, lat27)

    p('· resampling the economic sheet…')
    src = np.asarray(Image.open(path('gf120_econ.jpg')).convert('RGB'),
                     dtype=np.float32)
    SX, SY = fits['econ'].apply(X27, Y27)
    fx0, fy0, fx1, fy1 = frame_box(fits['econ'], src.mean(2))
    ok = inside & (SX > fx0) & (SX < fx1) & (SY > fy0) & (SY < fy1)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    for c in range(3):
        tex[:, :, c][ok] = ndimage.map_coordinates(
            src[:, :, c], [SY[ok], SX[ok]], order=1, mode='nearest')
    del src
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p('· resampling the areal sheet…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    src = np.asarray(Image.open(path('gf120_area.jpg')).convert('RGB'),
                     dtype=np.float32)
    X2, Y2 = LCC.fwd(lo2, la2)
    AX, AY = fits['area'].apply(X2, Y2)
    ax0, ay0, ax1, ay1 = frame_box(fits['area'], src.mean(2))
    ok2 = ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) &
           (la2 >= BLOCK[2]) & (la2 <= BLOCK[3]) &
           (AX > ax0) & (AX < ax1) & (AY > ay0) & (AY < ay1))
    np.clip(AX, 0, src.shape[1]-1, out=AX); np.clip(AY, 0, src.shape[0]-1, out=AY)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32); alt[:] = PAPER
    for c in range(3):
        alt[:, :, c][ok2] = ndimage.map_coordinates(
            src[:, :, c], [AY[ok2], AX[ok2]], order=1, mode='nearest')
    del src
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def mines(g):
    """Named mines from the 2021 GNIS archive, famous producers first,
    thinned by cell — 406 inside the neat; about eighty are kept, the tail
    chosen by name-hash so the cut isn't alphabetical."""
    import hashlib
    picks = {}
    with open(path('gnis_co_2021.txt'), encoding='utf-8-sig') as f:
        hdr = f.readline().strip().split('|')
        ix = {k: hdr.index(k) for k in ('FEATURE_NAME', 'FEATURE_CLASS',
                                        'PRIM_LAT_DEC', 'PRIM_LONG_DEC')}
        for ln in f:
            c = ln.split('|')
            if c[ix['FEATURE_CLASS']] != 'Mine': continue
            try:
                lat = float(c[ix['PRIM_LAT_DEC']]); lon = float(c[ix['PRIM_LONG_DEC']])
            except ValueError:
                continue
            if not (NEAT[0] <= lon <= NEAT[1] and NEAT[2] <= lat <= NEAT[3]):
                continue                     # on the sheet, not the margin
            name = c[ix['FEATURE_NAME']].strip()
            u, v = g.uv(lon, lat)
            if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
            score = (4 if name in MARQUEE_MINES else
                     3 if name in FAMOUS_MINES else
                     2 if 'Tunnel' not in name else 1)
            cell = (int(u*46), int(v*54))
            good = (score, -len(name))
            if cell not in picks or good > picks[cell][0]:
                kind = 'tunnel' if 'Tunnel' in name else 'mine'
                picks[cell] = (good, dict(n=name[:26], u=round(u, 5),
                                          v=round(v, 5), c=kind))
    out = sorted(picks.values(), key=lambda t: (
        -t[0][0], hashlib.md5(t[1]['n'].encode()).hexdigest()))
    out = [t[1] for t in out[:80]]
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
    p('· encoding the areal-geology layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [8300 + 410*i for i in range(len(ramp))]

    p('· picking the mine names…')
    M = mines(g)
    p('  %d mines kept' % len(M))

    fits = json.load(open(path('fits.json')))
    worst = max(fits.values(), key=lambda d: d['rms'])
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=1.9, exagMax=6.0, contourM=30.48, mineDist=0.50,
                       mineGlyph='⚒', rampLo=8300, rampHi=14040,
                       sheetA='1905 veins & mills', altName='1905 areal geology',
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
