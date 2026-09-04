#!/usr/bin/env python3
"""He Sapa in Folio — asset pipeline.

Geologic Atlas of the United States, Folio 219 (N. H. Darton and Sidney
Paige, 1925): the areal-geology sheet of the Central Black Hills, whose
southern half — the HARNEY PEAK and HERMOSA quadrangles joined at 103°30′ —
is draped over Terrarium elevations, with the 1901 engraved editions of the
same two quadrangles as the middle layer and the southern Hills' named
mines (GNIS) riding the terrain as data.

The 1901 bases are HTMC GeoTIFFs and carry their own polyconic
georeference.  The folio plate is rasterised from the pubs.usgs.gov PDF at
300 dpi (10.5 m/px, the scale the quads were scanned at), seeded from two
of its own printed neat corners and registered by correlation against both
base quads at once — the folio's topography *is* these quadrangles
("Topography from U.S. Geological Survey maps of Deadwood, Harney Peak,
Hermosa, and Rapid quadrangles.  Surveyed in 1891-1899.  Partially revised
in 1913-1915." is printed under the plate) — so the fit is folio-tight.

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
WORK = os.environ.get('BH_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27, poly_basis
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, FAMOUS_MINES

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/SD/'
PLATE_PDF = 'https://pubs.usgs.gov/gf/219/quad-1_area.pdf'   # 16.6 MB
PLATE_JPG = 'gf219_q1_area.jpg'
PLATE_DPI = 300
GNIS_2021 = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
             'Archive/MainDomestic/SD_Features_20210825.txt')
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'DomesticNames/DomesticNames_SD_Text.zip')

QUADS = [  # the folio's two southern sheets; neat (W, E, S, N) in NAD27
    dict(id='harney1901', url=S3+'SD_Harney%20Peak_344786_1901_125000_geo.tif',
         neat=(-104.0, -103.5, 43.5, 44.0)),
    dict(id='hermosa1901', url=S3+'SD_Hermosa_344793_1901_125000_geo.tif',
         neat=(-103.5, -103.0, 43.5, 44.0)),
]
BLOCK = (-104.0, -103.0, 43.5, 44.0)         # the union, W E S N

# The plate covers a full degree, 43°30′–44°30′ × 103°–104°; this sheet is
# its southern half.  Two printed neat corners, read once off the 300 dpi
# raster with a ruler grid, seed the registration — everything after is
# correlation.  PLATE_S_BODY is the southern half's frame: masking the ink
# to it keeps the legend, the collar and the Deadwood/Rapid half out of the
# correlation.  PLATE_FRAME is the whole plate's neat frame, a safety net
# for the drape — the printed map runs straight across 44° without a seam,
# so nothing needs clipping there.
ANCHORS = [((44.0, -104.0), (697.0, 5921.0)),      # left neat at 44°00′
           ((43.5, -103.0), (8345.0, 11185.0))]    # SE neat corner
PLATE_S_BODY = (700, 5935, 8390, 11175)            # x0, y0, x1, y1
PLATE_FRAME = (682, 650, 8408, 11189)

LCC = Lcc(43.6, 43.9, -103.5)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2560, 1707, 1792
DEM_ZOOM, DEM_BOX = 12, (-104.16, -102.84, 43.38, 44.12)
CLAMP = (700, 2400)
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]],
                       MARGIN, TEX_W)

def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its
    12-px neighbourhood.  Sees the engraved culture and contours the two
    editions share straight through the folio's colour washes and pattern
    rulings, where the black+blue mask of lib/reg goes nearly blind."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

# ------------------------------------------------------------------ stage 1
def fetch():
    for q in QUADS:
        tif = path(q['id'] + '.tif')
        if not os.path.exists(tif):
            p('· downloading the %s base quad…' % q['id'])
            req = urllib.request.Request(q['url'], headers={'User-Agent': 'old-time-maps/1.0'})
            with urllib.request.urlopen(req, timeout=600) as r, open(tif, 'wb') as f:
                f.write(r.read())
    if not os.path.exists(path(PLATE_JPG)):
        pdf = path('gf219_q1_area.pdf')
        if not os.path.exists(pdf):
            p('· downloading folio 219 areal plate…')
            req = urllib.request.Request(PLATE_PDF, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=900) as r:
                open(pdf, 'wb').write(r.read())
        p('· rasterising the plate at %d dpi…' % PLATE_DPI)
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(pdf)[0]
        page.render(scale=PLATE_DPI/72).to_pil().convert('RGB') \
            .save(path(PLATE_JPG), quality=95)
    if not os.path.exists(path('gnis_sd_2021.txt')):
        p('· downloading GNIS South Dakota features (2021 archive — has the mines)…')
        req = urllib.request.Request(GNIS_2021, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_sd_2021.txt'), 'wb').write(r.read())
    if not os.path.exists(path('gnis_sd.zip')):
        # not read at build time: this is the gazetteer places.py's summits,
        # towns and features were taken from, kept so they can be checked.
        p('· downloading GNIS domestic names (SD)…')
        req = urllib.request.Request(GNIS, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_sd.zip'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register the folio plate against both 1901 base quads at once.

    The plate's mask is clamped to the southern half's neat frame, so the
    legend, the collar and the Deadwood/Rapid half above 44° have nothing
    to correlate with; each base quad is masked to its own neatline."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed
    p('· reading the folio plate…')
    rgb = np.asarray(Image.open(path(PLATE_JPG)), dtype=np.uint8)
    plate_f = ink(rgb); del rgb
    fx0, fy0, fx1, fy1 = PLATE_S_BODY
    plate_f[:fy0, :] = 0; plate_f[fy1:, :] = 0
    plate_f[:, :fx0] = 0; plate_f[:, fx1:] = 0

    targets = []
    for q in QUADS:
        p('· reading the %s quad…' % q['id'])
        qim = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(qim)
        qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
        qf = ink(qrgb); del qrgb
        W, E, S, N = q['neat']
        x0, y0 = qr.to_px(W, N); x1, y1 = qr.to_px(E, S)
        qf[:int(y0)+8, :] = 0; qf[int(y1)-8:, :] = 0
        qf[:, :int(x0)+8] = 0; qf[:, int(x1)-8:] = 0
        targets.append(dict(name=q['id'], feat=qf, to_px=qr.to_px,
                            m_per_px=qr.scale[0]))

    # similarity seed from the two printed neat corners, in the LCC plane
    (llA, pxA), (llB, pxB) = ANCHORS
    XA, YA = LCC.fwd(llA[1], llA[0]); XB, YB = LCC.fwd(llB[1], llB[0])
    vC = np.array([XB-XA, -(YB-YA)]); vP = np.array([pxB[0]-pxA[0], pxB[1]-pxA[1]])
    s_ = np.linalg.norm(vP)/np.linalg.norm(vC)
    th = math.atan2(vP[1], vP[0]) - math.atan2(vC[1], vC[0])
    Rm_ = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    m_scan = 6371000.0*np.linalg.norm(vC)/np.linalg.norm(vP)   # unit-sphere Lcc!
    class SeedAff:
        def apply(self, X, Y):
            dX = np.asarray(X, float)-XA; dY = np.asarray(Y, float)-YA
            vx = Rm_[0, 0]*dX + Rm_[0, 1]*(-dY)
            vy = Rm_[1, 0]*dX + Rm_[1, 1]*(-dY)
            return pxA[0] + vx*s_, pxA[1] + vy*s_
    p('· anchor seed: %.2f m/px, rotation %.3f°' % (m_scan, math.degrees(th)))

    lons = np.arange(-103.955, -103.03, 0.045)
    lats = np.arange(43.545, 43.97, 0.045)
    p('· correlating the plate against the 1901 quads…')
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=SeedAff(),
                               pw=150, sw=200, log=p)
    if len(gx) < 20: raise SystemExit('too few GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='folio pass 1',
                          m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit1,
                               pw=150, sw=90, log=p)
    if len(gx) < 20: raise SystemExit('too few GCPs after refine')
    fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name='folio pass 2',
                          m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit2,
                               pw=150, sw=45, log=p)
    if len(gx) < 24: raise SystemExit('too few GCPs after tighten')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='folio fit',
                            m_per_px=m_scan, log=p)
    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   worst=round(fit.worst, 2), m_per_px=round(m_scan, 3),
                   n=int(keep.sum())),
              open(path('fit.json'), 'w'))
    im = Image.open(path(PLATE_JPG))
    overlay(im, {(255, 40, 40): list(zip(gx[keep], gy[keep]))},
            path('qa_georef.png'), 1500)
    p('  QA overlay in work/qa_georef.png')

class SavedFit:
    def __init__(self, d):
        self.d = d
    def apply(self, X, Y):
        d = self.d
        A = poly_basis((np.asarray(X, float)-d['Xm'])/d['sX'],
                       (np.asarray(Y, float)-d['Ym'])/d['sX'], d['deg'])
        return A@np.array(d['cx']), A@np.array(d['cy'])

def tone_match(tex, regions, label, log):
    """Even out the two printings: scale each quad's channels so its paper
    white (92nd percentile) meets the mosaic's median paper white."""
    whites = {k: np.array([np.percentile(tex[:, :, c][m], 92) for c in range(3)])
              for k, m in regions.items() if m.any()}
    target = np.median(np.stack(list(whites.values())), axis=0)
    for k, m in regions.items():
        if k not in whites: continue
        s = np.clip(target/np.maximum(whites[k], 1), 0.90, 1.11)
        log('  %s %s: paper × %s' % (label, k, np.round(s, 3)))
        for c in range(3):
            tex[:, :, c][m] *= s[c]

# ------------------------------------------------------------------ stage 3
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    fit = SavedFit(json.load(open(path('fit.json'))))
    g = make_grid()
    p('· conic grid %d × %d  (%.0f × %.0f km, %.1f m/texel)'
      % (g.TW, g.TH, g.kmw, g.kmh, g.m_per_texel))
    GX, GY, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    p('  elevation %.0f – %.0f m  (%.0f – %.0f ft)'
      % (hgt.min(), hgt.max(), hgt.min()/0.3048, hgt.max()/0.3048))
    np.save(path('hgt.npy'), hgt)

    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    inside = ((lon27 >= BLOCK[0]) & (lon27 <= BLOCK[1]) &
              (lat27 >= BLOCK[2]) & (lat27 <= BLOCK[3]))
    np.save(path('mask.npy'), inside)
    X27, Y27 = LCC.fwd(lon27, lat27)

    p('· resampling the folio geology…')
    src = np.asarray(Image.open(path(PLATE_JPG)).convert('RGB'), dtype=np.float32)
    SX, SY = fit.apply(X27, Y27)
    fx0, fy0, fx1, fy1 = PLATE_FRAME
    ok = inside & (SX > fx0) & (SX < fx1) & (SY > fy0) & (SY < fy1)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    for c in range(3):
        tex[:, :, c][ok] = ndimage.map_coordinates(
            src[:, :, c], [SY[ok], SX[ok]], order=1, mode='nearest')
    del src
    p('  %d of %d in-block texels drawn from the plate'
      % (int(ok.sum()), int(inside.sum())))
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p('· resampling the 1901 topography…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32); alt[:] = PAPER
    regions2 = {}
    for q in QUADS:
        W, E, S, N = q['neat']
        inq = (lo2 >= W) & (lo2 <= E) & (la2 >= S) & (la2 <= N)
        qim = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(qim)
        qsrc = np.asarray(qim.convert('RGB'), dtype=np.float32); del qim
        QX, QY = qr.to_px(lo2[inq], la2[inq])
        np.clip(QX, 0, qsrc.shape[1]-1, out=QX)
        np.clip(QY, 0, qsrc.shape[0]-1, out=QY)
        for c in range(3):
            alt[:, :, c][inq] = ndimage.map_coordinates(
                qsrc[:, :, c], [QY, QX], order=1, mode='nearest')
        del qsrc
        regions2[q['id']] = inq
        p('  %s: %d texels' % (q['id'], int(inq.sum())))
    tone_match(alt, regions2, 'topo', p)
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def mines(g):
    """The southern Hills' named mines from GNIS (2021 archive — the current
    DomesticNames product dropped the Mine class).

    Two passes of cell thinning: the named lodes of FAMOUS_MINES on a fine
    grid, so the Keystone pegmatite cluster keeps its own names, and the
    rest on a coarse one, so the belt reads as a belt instead of an
    alphabet."""
    f = open(path('gnis_sd_2021.txt'), encoding='utf-8-sig')
    hdr = f.readline().strip().split('|')
    ix = {k: hdr.index(k) for k in ('FEATURE_NAME', 'FEATURE_CLASS',
                                    'PRIM_LAT_DEC', 'PRIM_LONG_DEC')}
    rows = []
    for ln in f:
        c = ln.split('|')
        if c[ix['FEATURE_CLASS']] != 'Mine': continue
        try:
            lat, lon = float(c[ix['PRIM_LAT_DEC']]), float(c[ix['PRIM_LONG_DEC']])
        except ValueError:
            continue
        u, v = g.uv(lon, lat)
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        short = c[ix['FEATURE_NAME']].strip().replace(' (historical)', '')
        for suf in (' Group Mine', ' Lode Mine', ' Claim Mine', ' Mines', ' Mine',
                    ' Lode Claim', ' Lode', ' Claim'):
            if short.endswith(suf): short = short[:-len(suf)]; break
        if not short or len(short) > 20 or short[-1:].isdigit(): continue
        if 'Number' in short: continue
        score = (len(FAMOUS_MINES) - FAMOUS_MINES.index(short)
                 if short in FAMOUS_MINES else 0)
        rows.append((score, short, u, v))

    def thin(items, nx, ny):
        picks = {}
        for score, short, u, v in items:
            cell, good = (int(u*nx), int(v*ny)), (score, -len(short))
            if cell not in picks or good > picks[cell][0]:
                picks[cell] = (good, dict(n=short, u=round(u, 5), v=round(v, 5)))
        return [t[1] for t in picks.values()]

    out, seen = thin([r for r in rows if r[0]], 64, 44), set()
    for m in out: seen.add(m['n'])
    for m in thin([r for r in rows if not r[0]], 24, 17):
        if m['n'] not in seen:
            seen.add(m['n']); out.append(m)
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
    p('· encoding the 1901 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [2650 + 330*i for i in range(len(ramp))]

    p('· picking the mines…')
    M = mines(g)
    p('  %d mines kept' % len(M))

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=1.9, exagMax=7.0, contourM=30.48, mineDist=0.55,
                       mineGlyph='⚒', rampLo=2650, rampHi=7270,
                       sheetA='1925 geology', altName='1901 topography',
                       tourEx=[1.05, 0.01, 1.15, 2.4]),
               fit=dict(rms=fitd['rms'], median=fitd['median'], n=fitd['n']))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
