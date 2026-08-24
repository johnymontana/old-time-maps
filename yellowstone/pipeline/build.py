#!/usr/bin/env python3
"""Yellowstone in Folio — asset pipeline.

Geologic Atlas of the United States, Folio 30 (Arnold Hague, 1896): the four
areal-geology sheets of the Yellowstone National Park quadrangles — Gallatin,
Canyon, Shoshone, Lake — mosaicked into one 1° × 1° drape over Terrarium
elevations, with the 1911 engraved topographic editions of the same four
quadrangles as the middle layer and the park's named geysers and springs
(GNIS) riding the terrain as data.

The 1911 bases are HTMC GeoTIFFs and carry their own polyconic georeference;
each folio plate is rasterised from the pubs.usgs.gov PDF and registered by
correlation against its own base quad — same survey, same engraving lineage,
so the fits are tight.

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
WORK = os.environ.get('YS_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, FAMOUS_THERMAL

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/WY/'
GF30 = 'https://pubs.usgs.gov/gf/030/quad-%d_area.pdf'
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'DomesticNames/DomesticNames_WY_Text.zip')
QUADS = [  # the folio's four sheets; neat (W, E, S, N) in the NAD27 graticule
    dict(id='gallatin', plate=1, url=S3+'WY_Gallatin_342460_1911_125000_geo.tif',
         neat=(-111.0, -110.5, 44.5, 45.0)),
    dict(id='canyon',   plate=2, url=S3+'WY_Canyon_342404_1911_125000_geo.tif',
         neat=(-110.5, -110.0, 44.5, 45.0)),
    dict(id='shoshone', plate=3, url=S3+'WY_Shoshone_342550_1911_125000_geo.tif',
         neat=(-111.0, -110.5, 44.0, 44.5)),
    dict(id='lake',     plate=4, url=S3+'WY_Lake_342496_1911_125000_geo.tif',
         neat=(-110.5, -110.0, 44.0, 44.5)),
]
BLOCK = (-111.0, -110.0, 44.0, 45.0)         # the union, W E S N

LCC = Lcc(44.2, 44.8, -110.5)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 3328, 1707, 2304
DEM_ZOOM, DEM_BOX = 12, (-111.16, -109.84, 43.88, 45.12)
CLAMP = (1300, 3600)
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]],
                       MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 1
def fetch():
    for q in QUADS:
        tif = path(q['id'] + '1911.tif')
        if not os.path.exists(tif):
            p('· downloading the %s base quad…' % q['id'])
            req = urllib.request.Request(q['url'], headers={'User-Agent': 'old-time-maps/1.0'})
            with urllib.request.urlopen(req, timeout=300) as r, open(tif, 'wb') as f:
                f.write(r.read())
        jpg = path('gf30_q%d.jpg' % q['plate'])
        if not os.path.exists(jpg):
            pdf = path('gf30_q%d_area.pdf' % q['plate'])
            if not os.path.exists(pdf):
                p('· downloading folio plate %d…' % q['plate'])
                req = urllib.request.Request(GF30 % q['plate'],
                                             headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=600) as r:
                    open(pdf, 'wb').write(r.read())
            p('· rasterising plate %d at 300 dpi…' % q['plate'])
            import pypdfium2 as pdfium
            page = pdfium.PdfDocument(pdf)[0]
            page.render(scale=300/72).to_pil().convert('RGB').save(jpg, quality=95)
    if not os.path.exists(path('gnis_wy.zip')):
        p('· downloading GNIS domestic names (WY)…')
        req = urllib.request.Request(GNIS, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_wy.zip'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register each folio plate against its own 1911 base quad.

    No frame detection: the target is masked to its own neatline, so the
    plate's collar and legends have nothing to correlate with, and the
    interior control-point grid keeps every patch window well inside the
    body.  Only the page edges (scanner junk, punch holes) are blanked."""
    if os.path.exists(path('fits.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed

    def ink(rgb):
        """Linework as a local high-pass: anything markedly darker than its
        12-px neighbourhood.  Sees the brown contour plate — the ink the two
        editions actually share — through any paper tone or colour wash,
        where the black+blue mask of lib/reg goes nearly blind."""
        m = rgb.mean(2, dtype=np.float32)
        f = (ndimage.gaussian_filter(m, 12) - m) > 30
        return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

    fits = {}
    for q in QUADS:
        p('· [%s] reading plate %d…' % (q['id'], q['plate']))
        rgb = np.asarray(Image.open(path('gf30_q%d.jpg' % q['plate'])), dtype=np.uint8)
        plate_f = ink(rgb); del rgb
        ph, pw2 = plate_f.shape
        plate_f[:int(ph*0.03), :] = 0; plate_f[int(ph*0.97):, :] = 0
        plate_f[:, :int(pw2*0.03)] = 0; plate_f[:, int(pw2*0.97):] = 0

        qim = Image.open(path(q['id'] + '1911.tif'))
        qr = QuadGeoref(qim)
        qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
        qf = ink(qrgb); del qrgb
        W, E, S, N = q['neat']
        x0, y0 = qr.to_px(W, N); x1, y1 = qr.to_px(E, S)
        qf[:int(y0)+8, :] = 0; qf[int(y1)-8:, :] = 0
        qf[:, :int(x0)+8] = 0; qf[:, int(x1)-8:] = 0
        target = [dict(name=q['id']+'1911', feat=qf, to_px=qr.to_px,
                       m_per_px=qr.scale[0])]
        lons = np.arange(W+0.03, E-0.02, 0.05)
        lats = np.arange(S+0.03, N-0.02, 0.05)
        X, Y, gx, gy, m_per_px = register(plate_f, target, LCC, lons, lats,
                                          m_scan_hint=10.6, z_lo=0.86, z_hi=1.16,
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
                             m_per_px=round(m_per_px, 3), n=int(keep.sum()))
        im = Image.open(path('gf30_q%d.jpg' % q['plate']))
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

def tone_match(tex, regions, label, log):
    """Even out the four printings: scale each quad's channels so its paper
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

    p('· resampling the folio geology…')
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    regions = {}
    for q in QUADS:
        W, E, S, N = q['neat']
        inq = inside & (lon27 >= W) & (lon27 <= E) & (lat27 >= S) & (lat27 <= N)
        src = np.asarray(Image.open(path('gf30_q%d.jpg' % q['plate'])).convert('RGB'),
                         dtype=np.float32)
        SX, SY = fits[q['id']].apply(X27[inq], Y27[inq])
        np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
        for c in range(3):
            tex[:, :, c][inq] = ndimage.map_coordinates(
                src[:, :, c], [SY, SX], order=1, mode='nearest')
        del src
        regions[q['id']] = inq
        p('  %s: %d texels' % (q['id'], int(inq.sum())))
    tone_match(tex, regions, 'geology', p)
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p('· resampling the 1911 topography…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32); alt[:] = PAPER
    regions2 = {}
    for q in QUADS:
        W, E, S, N = q['neat']
        inq = (lo2 >= W) & (lo2 <= E) & (la2 >= S) & (la2 <= N)
        qim = Image.open(path(q['id'] + '1911.tif'))
        qr = QuadGeoref(qim)
        src = np.asarray(qim.convert('RGB'), dtype=np.float32); del qim
        QX, QY = qr.to_px(lo2[inq], la2[inq])
        np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
        for c in range(3):
            alt[:, :, c][inq] = ndimage.map_coordinates(
                src[:, :, c], [QY, QX], order=1, mode='nearest')
        del src
        regions2[q['id']] = inq
    tone_match(alt, regions2, 'topo', p)
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA mosaics in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def thermal(g):
    """Named geysers and hot springs from GNIS, famous first, thinned by cell."""
    z = zipfile.ZipFile(path('gnis_wy.zip'))
    f = z.open('Text/DomesticNames_WY.txt')
    hdr = f.readline().decode('utf-8-sig').strip().split('|')
    ix = {k: hdr.index(k) for k in ('feature_name', 'feature_class',
                                    'prim_lat_dec', 'prim_long_dec')}
    skip = ('Basin', 'Group', 'Creek', 'Lake', 'Mammoth', 'Terrace')
    picks = {}
    for ln in f:
        c = ln.decode('utf-8', 'replace').split('|')
        if c[ix['feature_class']] != 'Spring': continue
        try:
            lat, lon = float(c[ix['prim_lat_dec']]), float(c[ix['prim_long_dec']])
        except ValueError:
            continue
        name = c[ix['feature_name']].strip()
        if any(s in name for s in skip): continue
        u, v = g.uv(lon, lat)
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        score = 3 if name in FAMOUS_THERMAL else (2 if 'Geyser' in name else 1)
        cell = (int(u*64), int(v*90))
        good = (score, -len(name))
        if cell not in picks or good > picks[cell][0]:
            kind = 'geyser' if 'Geyser' in name else 'spring'
            picks[cell] = (good, dict(n=name[:26], u=round(u, 5), v=round(v, 5),
                                      c=kind))
    out = sorted(picks.values(), key=lambda t: (-t[0][0], t[1]['n']))
    out = [t[1] for t in out[:70]]
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
    p('· encoding the 1911 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [4900 + 500*i for i in range(len(ramp))]

    p('· picking the thermal names…')
    T = thermal(g)
    p('  %d geysers & springs kept' % len(T))

    fits = json.load(open(path('fits.json')))
    worst = max(fits.values(), key=lambda d: d['rms'])
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=T,
               ui=dict(exagDef=1.7, exagMax=6.0, contourM=30.48, mineDist=0.50,
                       mineGlyph='♨', rampLo=4900, rampHi=11900,
                       sheetA='1896 geology', altName='1911 topography',
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
