#!/usr/bin/env python3
"""The Coeur d'Alene — asset pipeline.

Ransome and Calkins' geologic map of the Coeur d'Alene mining district
(USGS Professional Paper 62, Plate II, 1908) — the silver-lead lodes of the
South Fork and Canyon Creek painted across the Belt rocks that carry them —
draped over Terrarium elevations, with the 1906 special topographic base it
was engraved on as the middle layer and the district's named mines (GNIS)
riding the terrain as data.

The base is an HTMC GeoTIFF (a 30' × 15' special, 1:62,500) and carries its
own polyconic georeference; the plate is rasterised from the pubs.usgs.gov
PDF, seeded from its printed neat corners, and registered by correlation —
same Goode/Urquhart/Manning engraving under both editions, so the fit is
folio-tight.

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
WORK = os.environ.get('CDA_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, FAMOUS_MINES

PLATE_PDF = 'https://pubs.usgs.gov/pp/0062/plate-2.pdf'          # 338 MB
S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/ID/'
BASE_URL = S3 + 'ID_Coeur%20DAlene%20District_238988_1906_62500_geo.tif'
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'Archive/MainDomestic/ID_Features_20210825.txt')
NEAT = (-116.16667, -115.66667, 47.41667, 47.66667)  # the special's graticule (NAD27)

# printed neat corners measured on the 450 dpi raster (NW, SE) — the seed
ANCHORS = [((47.66667, -116.16667), (289.5, 372.0)),
           ((47.41667, -115.66667), (10999.5, 8241.0))]
PLATE_FRAME = (249, 332, 11040, 8281)                # x0, y0, x1, y1 + slack

LCC = Lcc(47.45, 47.63, -115.9167)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2560, 1707, 1920
DEM_ZOOM, DEM_BOX = 12, (-116.33, -115.50, 47.25, 47.83)
CLAMP = (600, 2100)
PAPER = (235, 227, 207)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [NEAT[0], NEAT[1]], [NEAT[2], NEAT[3]], MARGIN, TEX_W)

def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its
    12-px neighbourhood — sees the engraved culture and contours the two
    editions share straight through the geology's colour washes."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

# ------------------------------------------------------------------ stage 1
def fetch():
    if not os.path.exists(path('cda1906.tif')):
        p('· downloading the 1906 base special…')
        req = urllib.request.Request(BASE_URL, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, open(path('cda1906.tif'), 'wb') as f:
            f.write(r.read())
    if not os.path.exists(path('pp62_p2.jpg')):
        if not os.path.exists(path('pp62_p2.pdf')):
            p('· downloading PP 62 Plate II (338 MB — be patient)…')
            req = urllib.request.Request(PLATE_PDF, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=1800) as r:
                open(path('pp62_p2.pdf'), 'wb').write(r.read())
        p('· rasterising the plate at 450 dpi…')
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(path('pp62_p2.pdf'))[0]
        page.render(scale=450/72).to_pil().convert('RGB') \
            .save(path('pp62_p2.jpg'), quality=95)
    if not os.path.exists(path('gnis_id_2021.txt')):
        p('· downloading GNIS Idaho features (2021 archive — has the mines)…')
        req = urllib.request.Request(GNIS, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_id_2021.txt'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register the plate against the 1906 base it was engraved from."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed
    p('· reading the plate…')
    rgb = np.asarray(Image.open(path('pp62_p2.jpg')), dtype=np.uint8)
    plate_f = ink(rgb); del rgb
    fx0, fy0, fx1, fy1 = PLATE_FRAME
    plate_f[:fy0+8, :] = 0; plate_f[fy1-8:, :] = 0    # title above, sections below
    plate_f[:, :fx0+8] = 0; plate_f[:, fx1-8:] = 0    # taped edge left, legend right

    qim = Image.open(path('cda1906.tif'))
    qr = QuadGeoref(qim)
    qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
    qf = ink(qrgb); del qrgb
    x0, y0 = qr.to_px(NEAT[0], NEAT[3]); x1, y1 = qr.to_px(NEAT[1], NEAT[2])
    qf[:int(y0)+8, :] = 0; qf[int(y1)-8:, :] = 0
    qf[:, :int(x0)+8] = 0; qf[:, int(x1)-8:] = 0
    target = [dict(name='cda1906', feat=qf, to_px=qr.to_px, m_per_px=qr.scale[0])]

    # similarity seed from the printed neat corners, in the LCC plane
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
    p('· corner seed: %.2f m/px, rotation %.2f°' % (m_scan, math.degrees(th)))

    lons = np.arange(NEAT[0]+0.018, NEAT[1]-0.012, 0.03)
    lats = np.arange(NEAT[2]+0.018, NEAT[3]-0.012, 0.028)
    p('· correlating the geology against the 1906 base…')
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=SeedAff(),
                               pw=170, sw=240, log=p)
    if len(gx) < 12: raise SystemExit('too few GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='plate pass 1',
                          m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit1,
                               pw=170, sw=90, log=p)
    fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name='plate pass 2',
                          m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit2,
                               pw=170, sw=45, log=p)
    if len(gx) < 14: raise SystemExit('too few GCPs')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='plate fit',
                            m_per_px=m_scan, log=p)
    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   m_per_px=round(m_scan, 3), n=int(keep.sum())),
              open(path('fit.json'), 'w'))
    im = Image.open(path('pp62_p2.jpg'))
    overlay(im, {(255, 40, 40): list(zip(gx[keep], gy[keep]))},
            path('qa_georef.png'), 1800)
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
    inside = ((lon27 >= NEAT[0]) & (lon27 <= NEAT[1]) &
              (lat27 >= NEAT[2]) & (lat27 <= NEAT[3]))
    np.save(path('mask.npy'), inside)

    p('· resampling the geology…')
    src = np.asarray(Image.open(path('pp62_p2.jpg')).convert('RGB'), dtype=np.float32)
    X27, Y27 = LCC.fwd(lon27, lat27)
    SX, SY = fit.apply(X27, Y27)
    fx0, fy0, fx1, fy1 = PLATE_FRAME
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

    p('· resampling the 1906 base…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    qim = Image.open(path('cda1906.tif'))
    qr = QuadGeoref(qim)
    qsrc = np.asarray(qim.convert('RGB'), dtype=np.float32); del qim
    QX, QY = qr.to_px(lo2, la2)
    ok2 = ((lo2 >= NEAT[0]) & (lo2 <= NEAT[1]) & (la2 >= NEAT[2]) & (la2 <= NEAT[3]) &
           (QX > 1) & (QX < qsrc.shape[1]-2) & (QY > 1) & (QY < qsrc.shape[0]-2))
    np.clip(QX, 0, qsrc.shape[1]-1, out=QX); np.clip(QY, 0, qsrc.shape[0]-1, out=QY)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32); alt[:] = PAPER
    for c in range(3):
        alt[:, :, c][ok2] = ndimage.map_coordinates(
            qsrc[:, :, c], [QY[ok2], QX[ok2]], order=1, mode='nearest')
    del qsrc
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def mines(g):
    """The district's named mines from GNIS (2021 archive — the current
    DomesticNames product dropped the Mine class), famous lodes first."""
    f = open(path('gnis_id_2021.txt'), encoding='utf-8-sig')
    hdr = f.readline().strip().split('|')
    ix = {k: hdr.index(k) for k in ('FEATURE_NAME', 'FEATURE_CLASS',
                                    'PRIM_LAT_DEC', 'PRIM_LONG_DEC')}
    picks = {}
    for ln in f:
        c = ln.split('|')
        if c[ix['FEATURE_CLASS']] != 'Mine': continue
        try:
            lat, lon = float(c[ix['PRIM_LAT_DEC']]), float(c[ix['PRIM_LONG_DEC']])
        except ValueError:
            continue
        name = c[ix['FEATURE_NAME']].strip()
        if name == 'S Bridge' or name[-1:].isdigit(): continue   # stray records
        u, v = g.uv(lon, lat)
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        short = name.replace(' (historical)', '')
        for suf in (' Mines', ' Mine'):
            if short.endswith(suf): short = short[:-len(suf)]
        score = 3 if short in FAMOUS_MINES else 1
        cell = (int(u*52), int(v*40))
        good = (score, -len(short))
        if cell not in picks or good > picks[cell][0]:
            picks[cell] = (good, dict(n=short[:26], u=round(u, 5), v=round(v, 5)))
    out = sorted(picks.values(), key=lambda t: (-t[0][0], t[1]['n']))
    out = [t[1] for t in out[:60]]
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
    p('· encoding the 1906 base layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[233, 224, 202], [225, 216, 192], [215, 206, 180], [205, 196, 168],
            [196, 185, 156], [190, 175, 145], [186, 165, 134], [181, 154, 123],
            [174, 143, 112], [166, 133, 103], [158, 125, 97], [153, 121, 96],
            [158, 129, 107], [170, 145, 126], [185, 165, 149]]
    ramp_ft = [2100 + 340*i for i in range(len(ramp))]

    p('· picking the mines…')
    M = mines(g)
    p('  %d mines kept' % len(M))

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=1.7, exagMax=6.0, contourM=15.24, mineDist=0.55,
                       mineGlyph='⚒', rampLo=2100, rampHi=6860,
                       sheetA='1908 geology', altName='1906 base map',
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
