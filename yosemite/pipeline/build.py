#!/usr/bin/env python3
"""Yosemite before the dam — asset pipeline.

Four engraved 30-minute quadrangles at 1:125,000 — DARDANELLES (1898),
BRIDGEPORT (1911), YOSEMITE (1909) and MT. LYELL (1901) — tiled into the
block 37°30′–38°15′ N × 119°–120° W and draped over Terrarium elevations,
with François Matthes' 1930 *Topographic Map of Yosemite National Park*
(USGS Professional Paper 160, plate 2) as the middle layer.

Every quadrangle here was printed before the Raker Act of December 1913, so
Hetch Hetchy is still a valley on the drape; the 1930 plate draws the
reservoir over it in hatched blue.  The quads carry their own polyconic
NAD27 georeference; Matthes' plate is a compilation of those same surveys
printed on the older USGS datum (its own collar says "to place on North
American datum move projection lines 690 feet south and 300 feet west"), so
it is registered by correlation on the shared engraved ink and the fit
absorbs that shift.

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
WORK = os.environ.get('YO_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, polyconic, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CA/'
PLATE_PDF = 'https://pubs.usgs.gov/pp/0160/plate-2.pdf'
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'Archive/MainDomestic/CA_Features_20210825.txt')
QUADS = [  # id, url, neat (W, E, S, N) of the printed graticule
    dict(id='dardanelles1898', url=S3+'CA_Dardanelles_299315_1898_125000_geo.tif',
         neat=(-120.0, -119.5, 38.0, 38.5)),
    dict(id='bridgeport1911', url=S3+'CA_Bridgeport_299235_1911_125000_geo.tif',
         neat=(-119.5, -119.0, 38.0, 38.5)),
    dict(id='yosemite1909', url=S3+'CA_Yosemite_299699_1909_125000_geo.tif',
         neat=(-120.0, -119.5, 37.5, 38.0)),
    dict(id='lyell1901', url=S3+'CA_Mt%20Lyell_299480_1901_125000_geo.tif',
         neat=(-119.5, -119.0, 37.5, 38.0)),
]
# the block is Matthes' own sheet line: the plate is drawn 37°30′–38°15′ by
# 119°–120°, so the middle layer covers the drape corner to corner
BLOCK = (-120.0, -119.0, 37.5, 38.25)

# plate 2 rasterised at 300 dpi.  FRAME is just outside the neatline (the
# collar's heavy border sits at x 205–238 / y 188–202 and is excluded);
# TITLE is the plate's own title block, which the engraver set *inside* the
# neatline over the Bodie Hills.  It is masked out of the correlation
# features — but it is left in the drape, where it belongs.
PLATE_FRAME = (270, 300, 8800, 8230)                  # x0, y0, x1, y1
PLATE_TITLE = (6900, 300, 8800, 2150)

# The plate's printed graticule corners, read once from the scan and used
# only as a *seed*: the neatline of PP 160 plate 2 is 37°30′–38°15′ by
# 119°–120°, and these are the two opposite corners in scan pixels.  The
# correlation ladder below does the actual fitting.
PLATE_LON0, PLATE_LAT0 = -119.5, 37.5                 # its central meridian
PLATE_ANCHORS = [((-120.0, 38.25), (330.0, 320.0)),
                 ((-119.0, 37.50), (8770.0, 8205.0))]

LCC = Lcc(37.65, 38.10, -119.5)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 3200, 2112, 1984
DEM_ZOOM, DEM_BOX = 12, (-120.22, -118.78, 37.32, 38.45)
CLAMP = (120, 4200)
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]], MARGIN, TEX_W)

def clip(q):
    """A quad's neatline clipped to the block — the north pair are half sheets."""
    W, E, S, N = q['neat']
    return (max(W, BLOCK[0]), min(E, BLOCK[1]),
            max(S, BLOCK[2]), min(N, BLOCK[3]))

def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its 12-px
    neighbourhood.  Sees the brown contour plate — the ink these editions
    actually share — through paper tone and colour wash, where the black+blue
    mask of lib/reg goes nearly blind."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

def get(url, out, note, ua='old-time-maps/1.0'):
    if os.path.exists(out): return
    p('· downloading %s…' % note)
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    with urllib.request.urlopen(req, timeout=900) as r, open(out, 'wb') as f:
        f.write(r.read())

# ------------------------------------------------------------------ stage 1
def fetch():
    for q in QUADS:
        get(q['url'], path(q['id'] + '.tif'), 'the %s quadrangle' % q['id'])
    if not os.path.exists(path('park1930.jpg')):
        get(PLATE_PDF, path('pp160_p2.pdf'), 'PP 160 plate 2', ua='Mozilla/5.0')
        p('· rasterising the park map at 300 dpi…')
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(path('pp160_p2.pdf'))[0]
        page.render(scale=300/72).to_pil().convert('RGB').save(
            path('park1930.jpg'), quality=95)
    get(GNIS, path('gnis_ca_2021.txt'), 'GNIS domestic names (CA, 2021 archive)')
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def corner_seed(log=print):
    """A similarity on the plate's own polyconic, from its two printed
    corners.  Built exactly like bitterroot's SeedAff — the vector between
    the anchors sets scale and rotation — except that here the anchors are
    graticule corners, so the seed is the projection itself and only the
    plate's datum shift (its collar admits 690 ft south, 300 ft west of the
    North American datum) and press distortion are left for correlation."""
    (llA, pxA), (llB, pxB) = PLATE_ANCHORS
    XA, YA = polyconic(llA[0], llA[1], PLATE_LON0, PLATE_LAT0)
    XB, YB = polyconic(llB[0], llB[1], PLATE_LON0, PLATE_LAT0)
    vC = np.array([XB-XA, -(YB-YA)])
    vP = np.array([pxB[0]-pxA[0], pxB[1]-pxA[1]])
    s_ = np.linalg.norm(vP)/np.linalg.norm(vC)              # px per metre
    th = math.atan2(vP[1], vP[0]) - math.atan2(vC[1], vC[0])
    Rm = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    m_scan = 1.0/s_
    log('· corner seed: %.2f m/px, rotation %.3f°' % (m_scan, math.degrees(th)))

    class SeedPoly:
        def apply(self, X, Y):
            lon, lat = LCC.inv(X, Y)
            x, y = polyconic(lon, lat, PLATE_LON0, PLATE_LAT0)
            dX = np.asarray(x, float) - XA; dY = -(np.asarray(y, float) - YA)
            vx = Rm[0, 0]*dX + Rm[0, 1]*dY
            vy = Rm[1, 0]*dX + Rm[1, 1]*dY
            return pxA[0] + vx*s_, pxA[1] + vy*s_
    return SeedPoly(), m_scan

def georef():
    """Register Matthes' 1930 park map against the four quadrangles.

    Same lineage — the plate was compiled from these very surveys and
    engraved at the same scale — but four 30′ quads inside one 1° plate is
    a self-similar haystack, and lib/reg's blind scale sweep walks off the
    end of its z range on it (it settled on 9.3 m/px against a truth near
    10.5).  So every pass is seeded: the printed corners start the ladder,
    then sw 130 → deg 1 → sw 200 → deg 2 → sw 45 → deg 2."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed
    p('· reading the 1930 park map…')
    rgb = np.asarray(Image.open(path('park1930.jpg')), dtype=np.uint8)
    plate_f = ink(rgb); del rgb
    x0, y0, x1, y1 = PLATE_FRAME
    plate_f[:y0, :] = 0; plate_f[y1:, :] = 0
    plate_f[:, :x0] = 0; plate_f[:, x1:] = 0
    tx0, ty0, tx1, ty1 = PLATE_TITLE
    plate_f[ty0:ty1, tx0:tx1] = 0
    p('  plate %d × %d px' % (plate_f.shape[1], plate_f.shape[0]))

    targets = []
    for q in QUADS:
        qim = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(qim)
        qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
        qf = ink(qrgb); del qrgb
        W, E, S, N = clip(q)
        qx0, qy0 = qr.to_px(W, N); qx1, qy1 = qr.to_px(E, S)
        qf[:int(qy0)+8, :] = 0; qf[int(qy1)-8:, :] = 0
        qf[:, :int(qx0)+8] = 0; qf[:, int(qx1)-8:] = 0
        targets.append(dict(name=q['id'], feat=qf, to_px=qr.to_px,
                            m_per_px=qr.scale[0]))

    seed, m_scan = corner_seed(p)
    lons = np.arange(-119.96, -119.03, 0.05)
    lats = np.arange(37.54, 38.22, 0.05)
    p('· correlating the park map against the quads…')
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=seed,
                               pw=150, sw=130, log=p)
    if len(gx) < 20: raise SystemExit('too few GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='park map pass 1',
                          m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit1,
                               pw=150, sw=200, log=p)
    fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name='park map pass 2',
                          m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit2,
                               pw=150, sw=45, log=p)
    if len(gx) < 30: raise SystemExit('too few GCPs after refine')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='park map fit',
                            m_per_px=m_scan, log=p)
    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   worst=round(fit.worst, 2),
                   m_per_px=round(m_scan, 3), n=int(keep.sum())),
              open(path('fit.json'), 'w'))
    im = Image.open(path('park1930.jpg'))
    overlay(im, {(255, 40, 40): list(zip(gx[keep], gy[keep]))},
            path('qa_georef.png'), 1600)
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
    """Even out four printings from four decades: scale each quad's channels
    so its paper white (92nd percentile) meets the mosaic's median white."""
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

    mos, mx0, my0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, mx0, my0, DEM_ZOOM, LON, LAT); del mos
    p('  elevation %.0f – %.0f m  (%.0f – %.0f ft)'
      % (hgt.min(), hgt.max(), hgt.min()/0.3048, hgt.max()/0.3048))
    np.save(path('hgt.npy'), hgt)

    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    inside = ((lon27 >= BLOCK[0]) & (lon27 <= BLOCK[1]) &
              (lat27 >= BLOCK[2]) & (lat27 <= BLOCK[3]))
    np.save(path('mask.npy'), inside)

    p('· resampling the four quadrangles…')
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    regions = {}
    for q in QUADS:
        W, E, S, N = clip(q)
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
    del tex

    p('· resampling the 1930 park map…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    X27, Y27 = LCC.fwd(lo2, la2)
    SX, SY = fit.apply(X27, Y27)
    fx0, fy0, fx1, fy1 = PLATE_FRAME
    ok2 = ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) &
           (la2 >= BLOCK[2]) & (la2 <= BLOCK[3]) &
           (SX > fx0+4) & (SX < fx1-4) & (SY > fy0+4) & (SY < fy1-4))
    p('  %.1f%% of the block is covered by the plate' % (100.0*ok2.mean()/
        ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) &
         (la2 >= BLOCK[2]) & (la2 <= BLOCK[3])).mean()))
    src = np.asarray(Image.open(path('park1930.jpg')).convert('RGB'), dtype=np.uint8)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32); alt[:] = PAPER
    for c in range(3):
        alt[:, :, c][ok2] = ndimage.map_coordinates(
            src[:, :, c].astype(np.float32), [SY[ok2], SX[ok2]], order=1, mode='nearest')
    del src
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
FAMOUS_FALLS = {
    'Yosemite Falls', 'Upper Yosemite Falls', 'Lower Yosemite Fall',
    'Bridalveil Fall', 'Nevada Fall', 'Vernal Fall', 'Illilouette Falls',
    'Ribbon Fall', 'Sentinel Fall', 'Wapama Falls', 'Tueeulala Falls',
    'Rancheria Falls', 'Waterwheel Falls', 'Chilnualna Fall', 'Rainbow Falls',
}

def falls(g):
    """Named falls and cascades from GNIS, riding the cliffs that make them."""
    out = []
    with open(path('gnis_ca_2021.txt'), encoding='utf-8-sig', errors='replace') as f:
        hdr = f.readline().strip().split('|')
        ix = {k: hdr.index(k) for k in ('FEATURE_NAME', 'FEATURE_CLASS',
                                        'PRIM_LAT_DEC', 'PRIM_LONG_DEC')}
        for ln in f:
            c = ln.rstrip('\n').split('|')
            if len(c) < len(hdr) or c[ix['FEATURE_CLASS']] != 'Falls': continue
            try:
                lat = float(c[ix['PRIM_LAT_DEC']]); lon = float(c[ix['PRIM_LONG_DEC']])
            except ValueError:
                continue
            if not (BLOCK[0] <= lon <= BLOCK[1] and BLOCK[2] <= lat <= BLOCK[3]):
                continue                      # the grid's margin is not the sheet
            u, v = g.uv(lon, lat)
            name = c[ix['FEATURE_NAME']].strip()
            out.append(dict(n=name[:26], u=round(float(u), 5), v=round(float(v), 5),
                            c='falls', f=1 if name in FAMOUS_FALLS else 0))
    out.sort(key=lambda m: (-m['f'], m['n']))
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
    p('· encoding the 1930 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [1000 + 880*i for i in range(len(ramp))]   # 1,000 – 13,320 ft

    p('· picking the named falls…')
    F = falls(g)
    p('  %d falls and cascades kept' % len(F))

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=F,
               ui=dict(exagDef=1.7, exagMax=6.0, contourM=30.48, mineDist=0.55,
                       mineGlyph='⇊', rampLo=1000, rampHi=13320,
                       sheetA='1898–1911 quads', altName='1930 park map',
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
