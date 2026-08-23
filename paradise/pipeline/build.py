#!/usr/bin/env python3
"""The Livingston Sheet — asset pipeline.

Geologic Atlas of the United States, Folio 1 (Iddings & Weed, 1894): the
areal-geology plate of the Livingston degree sheet — Paradise Valley, Tom
Miner Basin, the Boulder and the southern Crazies, one full degree of
country north of Yellowstone Park — draped over Terrarium elevations, with
the 1891 engraved topographic edition as the middle layer and the corridor's
recorded mines (MRDS) riding the terrain as data.

The 1891 base is an HTMC GeoTIFF and carries its own polyconic georeference;
the folio plate is rasterised from the pubs.usgs.gov PDF and registered to it
by correlation on a local high-pass ink mask — same engraving lineage, so the
fit is tight (the same move that put Folio 30 on the park).

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
WORK = os.environ.get('PD_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS

PLATE_PDF = 'https://pubs.usgs.gov/gf/001/quad-area.pdf'
S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/'
BASE_URL = S3 + 'MT_Livingston_268784_1891_250000_geo.tif'
NEAT = (-111.0, -110.0, 45.0, 46.0)          # the degree sheet's graticule box

LCC = Lcc(45.2, 45.8, -110.5)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2560, 1707, 1920
DEM_ZOOM, DEM_BOX = 12, (-111.16, -109.84, 44.88, 46.12)
CLAMP = (1000, 3600)
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [NEAT[0], NEAT[1]], [NEAT[2], NEAT[3]], MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 1
def fetch():
    if not os.path.exists(path('livingston1891.tif')):
        p('· downloading the 1891 degree sheet…')
        req = urllib.request.Request(BASE_URL, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, open(path('livingston1891.tif'), 'wb') as f:
            f.write(r.read())
    if not os.path.exists(path('gf1_area.jpg')):
        pdf = path('gf1_area.pdf')
        if not os.path.exists(pdf):
            p('· downloading folio 1, areal-geology plate…')
            req = urllib.request.Request(PLATE_PDF, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=600) as r:
                open(pdf, 'wb').write(r.read())
        p('· rasterising the plate at 300 dpi…')
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(pdf)[0]
        page.render(scale=300/72).to_pil().convert('RGB').save(path('gf1_area.jpg'), quality=95)
    if not os.path.exists(path('mrds.json')):
        gold = os.path.join(REPO, 'gold', 'work', 'mrds.json')
        if not os.path.exists(gold):
            raise SystemExit('run gold/pipeline/build.py fetch first (MRDS cache)')
        shutil.copy(gold, path('mrds.json'))
        p('· MRDS borrowed from gold/work')
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register the folio plate against the 1891 base it reprints."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed

    def ink(rgb):
        """Local high-pass: anything markedly darker than its 12-px
        neighbourhood — the engraved linework the two printings share,
        visible through paper tone and colour wash alike."""
        m = rgb.mean(2, dtype=np.float32)
        f = (ndimage.gaussian_filter(m, 12) - m) > 30
        return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

    p('· reading the plate…')
    rgb = np.asarray(Image.open(path('gf1_area.jpg')), dtype=np.uint8)
    plate_f = ink(rgb); del rgb
    ph, pw2 = plate_f.shape
    plate_f[:int(ph*0.03), :] = 0; plate_f[int(ph*0.97):, :] = 0
    plate_f[:, :int(pw2*0.03)] = 0; plate_f[:, int(pw2*0.97):] = 0

    qim = Image.open(path('livingston1891.tif'))
    qr = QuadGeoref(qim)
    qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
    qf = ink(qrgb); del qrgb
    W, E, S, N = NEAT
    x0, y0 = qr.to_px(W, N); x1, y1 = qr.to_px(E, S)
    qf[:int(y0)+8, :] = 0; qf[int(y1)-8:, :] = 0
    qf[:, :int(x0)+8] = 0; qf[:, int(x1)-8:] = 0
    target = [dict(name='livingston1891', feat=qf, to_px=qr.to_px,
                   m_per_px=qr.scale[0])]
    lons = np.arange(W+0.05, E-0.04, 0.09)
    lats = np.arange(S+0.05, N-0.04, 0.09)
    p('· correlating the geology against the degree sheet…')
    X, Y, gx, gy, m_per_px = register(plate_f, target, LCC, lons, lats,
                                      m_scan_hint=21.2, z_lo=0.86, z_hi=1.16,
                                      pw=150, sw=130, log=p)
    if len(gx) < 12: raise SystemExit('too few GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='plate pass 1',
                          m_per_px=m_per_px, log=p)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                               m_scan_hint=m_per_px, seed_fit=fit1,
                               pw=150, sw=200, log=p)
    fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name='plate pass 2',
                          m_per_px=m_per_px, log=p)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                               m_scan_hint=m_per_px, seed_fit=fit2,
                               pw=150, sw=45, log=p)
    if len(gx) < 14: raise SystemExit('too few GCPs')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='plate fit',
                            m_per_px=m_per_px, log=p)
    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   m_per_px=round(m_per_px, 3), n=int(keep.sum())),
              open(path('fit.json'), 'w'))
    im = Image.open(path('gf1_area.jpg'))
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

    p('· resampling the folio geology…')
    src = np.asarray(Image.open(path('gf1_area.jpg')).convert('RGB'), dtype=np.float32)
    X27, Y27 = LCC.fwd(lon27, lat27)
    SX, SY = fit.apply(X27, Y27)
    ok = inside & (SX > 1) & (SX < src.shape[1]-2) & (SY > 1) & (SY < src.shape[0]-2)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    for c in range(3):
        tex[:, :, c][ok] = ndimage.map_coordinates(
            src[:, :, c], [SY[ok], SX[ok]], order=1, mode='nearest')
    del src
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p('· resampling the 1891 topography…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    qim = Image.open(path('livingston1891.tif'))
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
    """Recorded producers from MRDS: metals, plus the corridor's coal."""
    sites = json.load(open(path('mrds.json')))
    rank = {'Producer': 3, 'Past Producer': 2}
    keepc = ('AU', 'AG', 'PB', 'CU', 'ZN', 'W', 'AS', 'C')
    label = {'AU': 'gold', 'AG': 'silver', 'PB': 'lead', 'CU': 'copper',
             'ZN': 'zinc', 'W': 'tungsten', 'AS': 'arsenic', 'C': 'coal'}
    picks = {}
    for s in sites:
        codes = s['c'].split()
        if not any(c in codes for c in keepc): continue
        r = rank.get(s['s'], 0)
        if r < 2: continue
        u, v = g.uv(s['lon'], s['lat'])
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        cell = (int(u*52), int(v*72))
        name = (s['n'] or 'Unnamed').title()
        good = (r, name != 'Unnamed', -len(name))
        if cell not in picks or good > picks[cell][0]:
            com = next(label[c] for c in keepc if c in codes)
            picks[cell] = (good, dict(n=name[:26], u=round(u, 5), v=round(v, 5), c=com))
    out = [v[1] for v in picks.values()]
    out.sort(key=lambda m: m['n'])
    return out[:80]

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
    p('· encoding the 1891 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [3800 + 500*i for i in range(len(ramp))]

    p('· thinning the MRDS mines…')
    M = mines(g)
    p('  %d mines kept' % len(M))

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=1.8, exagMax=6.0, contourM=60.96, mineDist=0.50,
                       rampLo=3800, rampHi=11300,
                       sheetA='1894 geology', altName='1891 topography',
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
