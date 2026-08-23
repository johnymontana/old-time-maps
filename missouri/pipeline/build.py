#!/usr/bin/env python3
"""The Head of Navigation — asset pipeline.

The Missouri where it earned its keep: the GREAT FALLS (1886) and FORT
BENTON (1890) degree sheets joined at 111°W — the five falls, the portage
plain, the Sun and the Marias, Fort Benton's levee at the head of steamboat
navigation, and the start of the White Cliffs — with Mortson's 1890
OFFICIAL MAP OF CASCADE COUNTY (mining regions of the Belt Mountains and
all) one slider-stop behind, and the river's own landmarks riding the
terrain as data under an anchor glyph.

Both degree sheets are HTMC GeoTIFFs with their own georeference.  The
county map is a township-plat compilation: seeded from the printed symbols
of Great Falls and Neihart, then registered by correlation on the shared
ink of rivers and the section grid.

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
WORK = os.environ.get('MO_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27, poly_basis
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, RIVERPOINTS

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/'
CASC_URL = 'https://tile.loc.gov/storage-services/service/gmd/gmd425/g4253/g4253c/la000413.jp2'
QUADS = [
    dict(id='greatfalls1886', url=S3+'MT_Great%20Falls_268740_1886_250000_geo.tif',
         neat=(-112.0, -111.0, 47.0, 48.0)),
    dict(id='fortbenton1890', url=S3+'MT_Fort%20Benton_268718_1890_250000_geo.tif',
         neat=(-111.0, -110.0, 47.0, 48.0)),
]
BLOCK = (-112.0, -110.0, 47.0, 48.0)

ANCHORS = [((47.5002, -111.3008), (5430.0, 3030.0)),   # Great Falls
           ((46.9333, -110.7358), (8000.0, 6985.0))]   # Neihart
CASC_BODY = (2230, 1590, 12330, 8510)

LCC = Lcc(47.2, 47.8, -111.0)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 4096, 2048, 3072
DEM_ZOOM, DEM_BOX = 12, (-112.16, -109.84, 46.88, 48.12)
CLAMP = (700, 2700)
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]], MARGIN, TEX_W)

def ink(rgb):
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
    if not os.path.exists(path('cascade1890.jpg')):
        jp2 = path('cascade1890.jp2')
        if not os.path.exists(jp2):
            p('· downloading the Cascade County map…')
            req = urllib.request.Request(CASC_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=600) as r:
                open(jp2, 'wb').write(r.read())
        Image.open(jp2).convert('RGB').save(path('cascade1890.jpg'), quality=95)
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register the county map against the two degree sheets."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed
    p('· reading the county map…')
    rgb = np.asarray(Image.open(path('cascade1890.jpg')), dtype=np.uint8)
    cf = ink(rgb); del rgb
    x0, y0, x1, y1 = CASC_BODY
    cf[:y0, :] = 0; cf[y1:, :] = 0; cf[:, :x0] = 0; cf[:, x1:] = 0

    targets = []
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

    lons = np.arange(-111.96, -110.24, 0.07)
    lats = np.arange(47.04, 47.97, 0.065)
    p('· correlating the county map against the degree sheets…')
    X, Y, gx, gy, _ = register(cf, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=SeedAff(),
                               pw=200, sw=220, log=p)
    if len(gx) < 12: raise SystemExit('too few GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='cascade pass 1', floor=6.0,
                          k=2.0, rounds=4, m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(cf, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit1,
                               pw=200, sw=80, log=p)
    if len(gx) < 12: raise SystemExit('too few GCPs after refine')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='cascade fit', floor=6.0,
                            k=2.2, rounds=4, m_per_px=m_scan, log=p)
    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   m_per_px=round(m_scan, 2), n=int(keep.sum())),
              open(path('fit.json'), 'w'))
    im = Image.open(path('cascade1890.jpg'))
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

    p('· resampling the two degree sheets…')
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
    tone_match(tex, regions, 'sheet', p)
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p('· resampling the county map…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    src = np.asarray(Image.open(path('cascade1890.jpg')).convert('RGB'), dtype=np.float32)
    X27, Y27 = LCC.fwd(lo2, la2)
    SX, SY = fit.apply(X27, Y27)
    fx0, fy0, fx1, fy1 = CASC_BODY
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
    p('· encoding the county layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [2300 + 420*i for i in range(len(ramp))]

    R = [dict(n=n, u=round(g.uv(lon, lat)[0], 5), v=round(g.uv(lon, lat)[1], 5), c=c)
         for n, lat, lon, c in RIVERPOINTS]
    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=R,
               ui=dict(exagDef=2.2, exagMax=8.0, contourM=60.96, mineDist=0.65,
                       mineGlyph='⚓', rampLo=2300, rampHi=8200,
                       sheetA='1886 & 1890 sheets', altName='1890 county map',
                       tourEx=[1.1, 0.012, 1.25, 2.8]),
               fit=dict(rms=fitd['rms'], median=fitd['median'], n=fitd['n']))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
