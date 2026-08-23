#!/usr/bin/env python3
"""The Bitterroot — asset pipeline.

Two engraved 30-minute quadrangles joined at 46°30′ — HAMILTON (surveyed
1899–1900, edition of 1901) and MISSOULA (surveyed 1900–01, edition of 1912)
— one 0.5° × 1° strip of valley from the Como moraines to the Hellgate,
draped over Terrarium elevations, with J.B. Leiberg's 1898 Bitterroot Forest
Reserve land-classification map (USGS 20th Annual Report, part V) as the
middle layer and the valley's recorded mines (MRDS) as data.

Both quads carry their own polyconic georeference.  Leiberg's plate is a
sketch-contour compilation, not the quad engraving — it is seeded from two
town anchors (printed symbols with GNIS coordinates, the flathead sheet's
move) and refined by correlation on the high-pass ink mask; the reserve
ends at the Lolo divide, so the layer fades to paper north of it.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import json, math, os, shutil, sys, urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('BR_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/'
PLATE_PDF = 'https://pubs.usgs.gov/ar/20-5/plate-59.pdf'   # plate CXIV
QUADS = [  # id, url, neat (W, E, S, N)
    dict(id='hamilton1901', url=S3+'MT_Hamilton_268555_1901_125000_geo.tif',
         neat=(-114.5, -114.0, 46.0, 46.5)),
    dict(id='missoula1912', url=S3+'MT_Missoula_268581_1912_125000_geo.tif',
         neat=(-114.5, -114.0, 46.5, 47.0)),
]
BLOCK = (-114.5, -114.0, 46.0, 47.0)
SEAM_LAT = 46.5

# Leiberg plate: town symbols with GNIS coordinates seed the alignment,
# like the flathead sheet's Somers/Polson anchors.
ANCHORS = [((46.5099, -114.0931), (6945.0, 1520.0)),   # Stevensville
           ((46.2466, -114.1603), (6785.0, 2965.0))]   # Hamilton
PLATE_FRAME = (200, 270, 7395, 7900)                   # x0, y0, x1, y1

LCC = Lcc(46.2, 46.8, -114.25)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 1920, 1280, 1440
DEM_ZOOM, DEM_BOX = 12, (-114.68, -113.82, 45.88, 47.12)
CLAMP = (850, 3100)
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]], MARGIN, TEX_W)

def ink(rgb):
    """Local high-pass linework mask (see yellowstone/) — works across the
    quads' engraving and Leiberg's lithography alike."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

# ------------------------------------------------------------------ stage 1
def fetch():
    for q in QUADS:
        tif = path(q['id'] + '.tif')
        if not os.path.exists(tif):
            p('· downloading %s…' % q['id'])
            req = urllib.request.Request(q['url'], headers={'User-Agent': 'old-time-maps/1.0'})
            with urllib.request.urlopen(req, timeout=300) as r, open(tif, 'wb') as f:
                f.write(r.read())
    if not os.path.exists(path('leiberg1898.jpg')):
        pdf = path('leiberg1898.pdf')
        if not os.path.exists(pdf):
            p('· downloading Leiberg plate CXIV…')
            req = urllib.request.Request(PLATE_PDF, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=600) as r:
                open(pdf, 'wb').write(r.read())
        p('· rasterising the plate at 300 dpi…')
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(pdf)[0]
        page.render(scale=300/72).to_pil().convert('RGB').save(path('leiberg1898.jpg'), quality=95)
    if not os.path.exists(path('mrds.json')):
        gold = os.path.join(REPO, 'gold', 'work', 'mrds.json')
        if not os.path.exists(gold):
            raise SystemExit('run gold/pipeline/build.py fetch first (MRDS cache)')
        shutil.copy(gold, path('mrds.json'))
        p('· MRDS borrowed from gold/work')
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register Leiberg's plate against both quads, anchor-seeded."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed
    p('· reading the plate…')
    rgb = np.asarray(Image.open(path('leiberg1898.jpg')), dtype=np.uint8)
    plate_f = ink(rgb); del rgb
    x0, y0, x1, y1 = PLATE_FRAME
    plate_f[:y0, :] = 0; plate_f[y1:, :] = 0
    plate_f[:, :x0] = 0; plate_f[:, x1:] = 0

    targets, lonsA, latsA = [], [], []
    for q in QUADS:
        qim = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(qim)
        qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
        qf = ink(qrgb); del qrgb
        W, E, S, N = q['neat']
        qx0, qy0 = qr.to_px(W, N); qx1, qy1 = qr.to_px(E, S)
        qf[:int(qy0)+8, :] = 0; qf[int(qy1)-8:, :] = 0
        qf[:, :int(qx0)+8] = 0; qf[:, int(qx1)-8:] = 0
        targets.append(dict(name=q['id'], feat=qf, to_px=qr.to_px,
                            m_per_px=qr.scale[0]))

    # similarity seed from the two town anchors, in the LCC plane
    (llA, pxA), (llB, pxB) = ANCHORS
    XA, YA = LCC.fwd(llA[1], llA[0]); XB, YB = LCC.fwd(llB[1], llB[0])
    vC = np.array([XB-XA, -(YB-YA)]); vP = np.array([pxB[0]-pxA[0], pxB[1]-pxA[1]])
    s_ = np.linalg.norm(vP)/np.linalg.norm(vC)
    th = math.atan2(vP[1], vP[0]) - math.atan2(vC[1], vC[0])
    Rm_ = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    m_scan = 6371000.0*np.linalg.norm(vC)/np.linalg.norm(vP)
    class SeedAff:
        def apply(self, X, Y):
            dX = np.asarray(X, float)-XA; dY = np.asarray(Y, float)-YA
            vx = Rm_[0, 0]*dX + Rm_[0, 1]*(-dY)
            vy = Rm_[1, 0]*dX + Rm_[1, 1]*(-dY)
            return pxA[0] + vx*s_, pxA[1] + vy*s_
    p('· anchor seed: %.2f m/px, rotation %.2f°' % (m_scan, math.degrees(th)))

    # candidates in the valley strip only: Leiberg's mountain interior is
    # generalised hatching, but the valley carries the township grid, roads
    # and drainage both maps share
    lons = np.arange(-114.28, -113.96, 0.035)
    lats = np.arange(46.02, 46.74, 0.045)
    p('· correlating Leiberg against the quads (valley strip)…')
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=SeedAff(),
                               pw=220, sw=260, log=p)
    if len(gx) < 10: raise SystemExit('too few GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='leiberg pass 1', floor=8.0,
                          k=2.0, rounds=4, m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit1,
                               pw=220, sw=110, log=p)
    if len(gx) < 10: raise SystemExit('too few GCPs after refine')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='leiberg fit', floor=8.0,
                            k=2.0, rounds=4, m_per_px=m_scan, log=p)
    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   m_per_px=round(m_scan, 2), n=int(keep.sum())),
              open(path('fit.json'), 'w'))
    im = Image.open(path('leiberg1898.jpg'))
    overlay(im, {(255, 40, 40): list(zip(gx[keep], gy[keep]))},
            path('qa_georef.png'), 1500)
    p('  QA overlay in work/qa_georef.png')

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

def tone_match(tex, regions, label, log):
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

    p('· resampling the two quads…')
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    regions = {}
    for q in QUADS:
        W, E, S, N = q['neat']
        inq = inside & (lon27 >= W) & (lon27 <= E) & (lat27 >= S) & (lat27 <= N)
        qim = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(qim)
        src = np.asarray(qim.convert('RGB'), dtype=np.float32); del qim
        QX, QY = qr.to_px(lon27[inq], lat27[inq])
        np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
        for c in range(3):
            tex[:, :, c][inq] = ndimage.map_coordinates(
                src[:, :, c], [QY, QX], order=1, mode='nearest')
        del src
        regions[q['id']] = inq
        p('  %s: %d texels' % (q['id'], int(inq.sum())))
    tone_match(tex, regions, 'quad', p)
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p('· resampling Leiberg…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    src = np.asarray(Image.open(path('leiberg1898.jpg')).convert('RGB'), dtype=np.float32)
    X27, Y27 = LCC.fwd(lo2, la2)
    SX, SY = fit.apply(X27, Y27)
    fx0, fy0, fx1, fy1 = PLATE_FRAME
    ok2 = ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) & (la2 >= BLOCK[2]) & (la2 <= BLOCK[3]) &
           (SX > fx0+4) & (SX < fx1-4) & (SY > fy0+4) & (SY < fy1-4))
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32); alt[:] = PAPER
    for c in range(3):
        alt[:, :, c][ok2] = ndimage.map_coordinates(
            src[:, :, c], [SY[ok2], SX[ok2]], order=1, mode='nearest')
    del src
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def mines(g):
    sites = json.load(open(path('mrds.json')))
    rank = {'Producer': 3, 'Past Producer': 2}
    keepc = ('AU', 'AG', 'PB', 'CU', 'ZN')
    label = {'AU': 'gold', 'AG': 'silver', 'PB': 'lead', 'CU': 'copper', 'ZN': 'zinc'}
    picks = {}
    for s in sites:
        codes = s['c'].split()
        if not any(c in codes for c in keepc): continue
        r = rank.get(s['s'], 0)
        if r < 2: continue
        u, v = g.uv(s['lon'], s['lat'])
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        cell = (int(u*40), int(v*94))
        name = (s['n'] or 'Unnamed').title()
        good = (r, name != 'Unnamed', -len(name))
        if cell not in picks or good > picks[cell][0]:
            com = next(label[c] for c in keepc if c in codes)
            picks[cell] = (good, dict(n=name[:26], u=round(u, 5), v=round(v, 5), c=com))
    out = [v[1] for v in picks.values()]
    out.sort(key=lambda m: m['n'])
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
    p('· encoding the Leiberg layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [3000 + 450*i for i in range(len(ramp))]

    p('· thinning the MRDS mines…')
    M = mines(g)
    p('  %d mines kept' % len(M))

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=1.8, exagMax=6.0, contourM=30.48, mineDist=0.50,
                       rampLo=3000, rampHi=9300,
                       sheetA='1901 & 1912 sheets', altName='1898 forest survey',
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
