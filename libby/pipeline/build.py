#!/usr/bin/env python3
"""The Libby Quadrangle — asset pipeline.

Gibson's 1948 geologic map of the Libby 30-minute quadrangle (USGS Bulletin
956, plate 1) — the Cabinet Mountains' Belt rocks, granite stocks and the
silver-lead veins south of Libby, keyed to a printed List of Mines — draped
over Terrarium elevations, with the 1932 topographic base it was printed on
as the middle layer and the district's recorded mines as data.

The plate PDF is rasterised and registered by correlation against the 1932
base quad, which the USGS distributes already georeferenced; the geology was
printed on that very base, so the fit is tight.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import json, math, os, re, shutil, sys, urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('LB_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS

PLATE_PDF = 'https://pubs.usgs.gov/bul/0956/plate-1.pdf'
S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/MT/'
BASE_URL = S3 + 'MT_Libby_268577_1932_125000_geo.tif'
NEAT = (-116.0, -115.5, 48.0, 48.5)          # the quad's graticule box (NAD27)
WFS = ('https://mrdata.usgs.gov/wfs/mrds?service=WFS&version=2.0.0&request=GetFeature'
       '&typenames=mrds&count=5000&startindex=%d'
       '&bbox=44.30,-116.20,49.05,-104.00,urn:ogc:def:crs:EPSG::4326')

LCC = Lcc(48.05, 48.45, -115.75)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2048, 1365, 1536
DEM_ZOOM, DEM_BOX = 12, (-116.17, -115.33, 47.88, 48.62)
CLAMP = (450, 2900)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [NEAT[0], NEAT[1]], [NEAT[2], NEAT[3]], MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 1
def fetch():
    if not os.path.exists(path('libby1932.tif')):
        p('· downloading the 1932 base quad…')
        req = urllib.request.Request(BASE_URL, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, open(path('libby1932.tif'), 'wb') as f:
            f.write(r.read())
    if not os.path.exists(path('b956_p1.jpg')):
        if not os.path.exists(path('b956_p1.pdf')):
            p('· downloading Bulletin 956 plate 1…')
            req = urllib.request.Request(PLATE_PDF, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=600) as r:
                open(path('b956_p1.pdf'), 'wb').write(r.read())
        p('· rasterising the plate…')
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(path('b956_p1.pdf'))[0]
        scale = min(9000/page.get_width(), 6.0)
        page.render(scale=scale).to_pil().convert('RGB') \
            .save(path('b956_p1.jpg'), quality=95)
    if not os.path.exists(path('mrds.json')):
        gold = os.path.join(REPO, 'gold', 'work', 'mrds.json')
        if os.path.exists(gold):
            shutil.copy(gold, path('mrds.json'))
            p('· MRDS borrowed from gold/work')
        else:
            p('· fetching MRDS sites over WFS…')
            sites, start = [], 0
            while True:
                req = urllib.request.Request(WFS % start,
                                             headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=300) as r:
                    gml = r.read().decode('utf-8', 'replace')
                members = re.findall(r'<wfs:member>(.*?)</wfs:member>', gml, re.S)
                for m in members:
                    pos = re.search(r'<gml:pos>([-\d.]+) ([-\d.]+)</gml:pos>', m)
                    name = re.search(r'<ms:site_name>(.*?)</ms:site_name>', m)
                    stat = re.search(r'<ms:dev_stat>(.*?)</ms:dev_stat>', m)
                    code = re.search(r'<ms:code_list>(.*?)</ms:code_list>', m)
                    if pos and stat and code:
                        sites.append(dict(lat=float(pos.group(1)), lon=float(pos.group(2)),
                                          n=(name.group(1) if name else '').strip(),
                                          s=stat.group(1).strip(), c=code.group(1).strip()))
                if len(members) < 5000: break
                start += 5000
            json.dump(sites, open(path('mrds.json'), 'w'))
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register the plate against the 1932 base it was printed on."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    fetch()
    from reg import smooth_feature, register, fit_trimmed
    p('· reading the plate…')
    rgb = np.asarray(Image.open(path('b956_p1.jpg')), dtype=np.uint8)
    plate_f = smooth_feature(rgb)
    ph, pw2 = plate_f.shape
    plate_f[:int(ph*0.03), :] = 0                   # margins and titles
    plate_f[int(ph*0.68):, :] = 0                   # sections strip below
    plate_f[:, int(pw2*0.78):] = 0                  # legend + mines list column
    plate_f[:, :int(pw2*0.03)] = 0

    qim = Image.open(path('libby1932.tif'))
    qr = QuadGeoref(qim)
    qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8)
    qf = smooth_feature(qrgb); del qrgb
    x0, y0 = qr.to_px(NEAT[0], NEAT[3]); x1, y1 = qr.to_px(NEAT[1], NEAT[2])
    qf[:int(y0)+8, :] = 0; qf[int(y1)-8:, :] = 0
    qf[:, :int(x0)+8] = 0; qf[:, int(x1)-8:] = 0
    target = [dict(name='libby1932', feat=qf, to_px=qr.to_px, m_per_px=qr.scale[0])]

    lons = np.arange(NEAT[0]+0.03, NEAT[1]-0.02, 0.055)
    lats = np.arange(NEAT[2]+0.03, NEAT[3]-0.02, 0.05)
    p('· correlating the geology against the base quad…')
    X, Y, gx, gy, m_per_px = register(plate_f, target, LCC, lons, lats,
                                      m_scan_hint=7.35, z_lo=1.2, z_hi=1.7,
                                      pw=170, sw=140, log=p)
    if len(gx) < 10: raise SystemExit('too few GCPs')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='plate pass 1',
                          m_per_px=m_per_px, log=p)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                               m_scan_hint=m_per_px, seed_fit=fit1,
                               pw=170, sw=260, log=p)
    fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name='plate pass 2',
                          m_per_px=m_per_px, log=p)
    X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                               m_scan_hint=m_per_px, seed_fit=fit2,
                               pw=170, sw=55, log=p)
    if len(gx) < 12: raise SystemExit('too few GCPs')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='plate fit',
                            m_per_px=m_per_px, log=p)
    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   n=int(keep.sum())),
              open(path('fit.json'), 'w'))
    im = Image.open(path('b956_p1.jpg'))
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
    src = np.asarray(Image.open(path('b956_p1.jpg')).convert('RGB'), dtype=np.float32)
    X27, Y27 = LCC.fwd(lon27, lat27)
    SX, SY = fit.apply(X27, Y27)
    ok = inside & (SX > 1) & (SX < src.shape[1]-2) & (SY > 1) & (SY < src.shape[0]-2)
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.zeros((g.TH, g.TW, 3), np.float32)
    tex[:] = (235, 227, 207)
    for c in range(3):
        tex[:, :, c][ok] = ndimage.map_coordinates(
            src[:, :, c], [SY[ok], SX[ok]], order=1, mode='nearest')
    del src
    np.save(path('drape.npy'), tex.astype(np.uint8))

    p('· resampling the 1932 base…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    qim = Image.open(path('libby1932.tif'))
    qr = QuadGeoref(qim)
    qsrc = np.asarray(qim.convert('RGB'), dtype=np.float32); del qim
    QX, QY = qr.to_px(lo2, la2)
    ok2 = ((lo2 >= NEAT[0]) & (lo2 <= NEAT[1]) & (la2 >= NEAT[2]) & (la2 <= NEAT[3]) &
           (QX > 1) & (QX < qsrc.shape[1]-2) & (QY > 1) & (QY < qsrc.shape[0]-2))
    np.clip(QX, 0, qsrc.shape[1]-1, out=QX); np.clip(QY, 0, qsrc.shape[0]-1, out=QY)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32)
    alt[:] = (235, 227, 207)
    for c in range(3):
        alt[:, :, c][ok2] = ndimage.map_coordinates(
            qsrc[:, :, c], [QY[ok2], QX[ok2]], order=1, mode='nearest')
    del qsrc
    np.save(path('alt.npy'), alt.astype(np.uint8))

    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))
    p('  QA drape in work/qa_drape.png')

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
        cell = (int(u*44), int(v*60))
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
    p('· encoding the 1932 base layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[233, 224, 202], [225, 216, 192], [215, 206, 180], [205, 196, 168],
            [196, 185, 156], [190, 175, 145], [186, 165, 134], [181, 154, 123],
            [174, 143, 112], [166, 133, 103], [158, 125, 97], [153, 121, 96],
            [158, 129, 107], [170, 145, 126], [185, 165, 149]]
    ramp_ft = [1700 + 500*i for i in range(len(ramp))]

    p('· thinning the MRDS mines…')
    M = mines(g)
    p('  %d mines kept' % len(M))

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=1.6, exagMax=6.0, contourM=30.48, mineDist=0.55,
                       rampLo=1600, rampHi=9200, sheetA='1948 geology',
                       altName='1932 base map', tourEx=[1.05, 0.01, 1.15, 2.4]),
               fit=dict(rms=fitd['rms'], median=fitd['median'], n=fitd['n']))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
