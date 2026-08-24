#!/usr/bin/env python3
"""Tacoma: Ice and Iron — asset pipeline.

Geologic Atlas of the United States, Folio 54 (Bailey Willis & George Otis
Smith, 1899): the Historical Geology sheet of the Tacoma quadrangle — the
Vashon ice sheet's drift, the Osceola 'till', the coal measures of the Puget
group — draped over Terrarium elevations, with the 21st Annual Report's
land-classification plate of the same quadrangle (Rankine & Plummer's 1897
standing-timber survey, plate CXXIX) as the middle layer and the Survey's
own mapped mine workings (USMIN) as data.

Both plates were printed on the very engraving the USGS distributes as the
georeferenced 1897 Tacoma base quad (HTMC scan 244174); each is rasterised
from its pubs.usgs.gov PDF at the scan's native 300 dpi and registered by
correlation against that base — same survey, same engraving lineage.  The
base is a registration target only, not a displayed layer.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import json, math, os, re, sys, urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('TA_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/WA/'
BASE_URL = S3 + 'WA_Tacoma_244174_1897_125000_geo.tif'
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'DomesticNames/DomesticNames_WA_Text.zip')
USMIN = ('https://mrdata.usgs.gov/wfs/usmin?service=WFS&version=2.0.0&request=GetFeature'
         '&typenames=points&count=5000&startindex=%d'
         '&bbox=46.99,-122.51,47.51,-121.99,urn:ogc:def:crs:EPSG::4326')
PLATES = [  # both printed on the 1897 Tacoma engraving; frame = neatline px
    dict(id='gf54', jpg='gf54.jpg', pdf='gf54_historical.pdf',
         url='https://pubs.usgs.gov/gf/054/quad-1_historical.pdf',
         frame=(838, 706, 4436, 5938), sw_final=45),
    dict(id='ar21', jpg='ar21.jpg', pdf='ar21_p129.pdf',
         url='https://pubs.usgs.gov/ar/21-5/plate-129.pdf',
         frame=(378, 406, 3946, 5680), sw_final=70,
         # the plate is smaller than the base at stage A's 1/8 sweep, so the
         # global alignment is seeded from its measured neatline corners
         # (NAD27 graticule values, the flathead/bitterroot anchor move)
         corners=(((47.5, -122.5), (378.0, 406.0)),
                  ((47.0, -122.0), (3946.0, 5680.0)))),
]
NEAT = (-122.5, -122.0, 47.0, 47.5)          # the quad's graticule box (NAD27)

LCC = Lcc(47.1, 47.4, -122.25)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2560, 1707, 1920
DEM_ZOOM, DEM_BOX = 12, (-122.66, -121.84, 46.84, 47.66)
CLAMP = (0, 2900)          # below 0 is the Sound's patchy bathymetry — void
                           # it and infill from the surrounding sea surface;
                           # the ceiling sits above the DEM box's real 2708 m
                           # so no Cascade foothill in the apron is clipped

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [NEAT[0], NEAT[1]], [NEAT[2], NEAT[3]], MARGIN, TEX_W)

def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its
    12-px neighbourhood.  Sees the engraving's shared black and brown plates
    through the folio's colour washes and the timber plate's heavy green
    tints, where a colour mask goes blind."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

def paper_tone(img, frame):
    """A plate's own paper, sampled from the margin above the neatline."""
    x0, y0, x1, y1 = frame
    strip = np.asarray(img, dtype=np.float32)[y0//4:y0//2, x0:x1]
    return np.median(strip.reshape(-1, 3), axis=0)

# ------------------------------------------------------------------ stage 1
def fetch():
    if not os.path.exists(path('tacoma1897.tif')):
        p('· downloading the 1897 base quad…')
        req = urllib.request.Request(BASE_URL, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r, open(path('tacoma1897.tif'), 'wb') as f:
            f.write(r.read())
    for pl in PLATES:
        if not os.path.exists(path(pl['jpg'])):
            if not os.path.exists(path(pl['pdf'])):
                p('· downloading %s…' % pl['pdf'])
                req = urllib.request.Request(pl['url'], headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=600) as r:
                    open(path(pl['pdf']), 'wb').write(r.read())
            p('· rasterising %s at 300 dpi (the embedded scan is 300 dpi)…' % pl['id'])
            import pypdfium2 as pdfium
            page = pdfium.PdfDocument(path(pl['pdf']))[0]
            page.render(scale=300/72).to_pil().convert('RGB') \
                .save(path(pl['jpg']), quality=95)
    if not os.path.exists(path('gnis_wa.zip')):
        p('· downloading GNIS domestic names (WA)…')
        req = urllib.request.Request(GNIS, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_wa.zip'), 'wb').write(r.read())
    if not os.path.exists(path('usmin.json')):
        p('· fetching USMIN mine features over WFS…')
        sites, start = [], 0
        while True:
            req = urllib.request.Request(USMIN % start, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=300) as r:
                gml = r.read().decode('utf-8', 'replace')
            members = re.findall(r'<wfs:member>(.*?)</wfs:member>', gml, re.S)
            for m in members:
                pos = re.search(r'<gml:pos>([-\d.]+) ([-\d.]+)</gml:pos>', m)
                def g(tag):
                    mm = re.search(r'<ms:%s>(.*?)</ms:%s>' % (tag, tag), m, re.S)
                    return mm.group(1).strip() if mm else ''
                if pos:
                    sites.append(dict(lat=float(pos.group(1)), lon=float(pos.group(2)),
                                      n=g('ftr_name'), t=g('ftr_type'), q=g('topo_name')))
            if len(members) < 5000: break
            start += 5000
        json.dump(sites, open(path('usmin.json'), 'w'))
        p('  %d USMIN points' % len(sites))
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Register both plates against the 1897 base they were printed on.

    The target is masked to its own neatline, so plate collars and legends
    have nothing to correlate with; each plate's feature mask is clipped to
    its measured frame (legend column, titles and the timber plate's fold
    margins go dark)."""
    if os.path.exists(path('fits.json')):
        p('· georeference cached'); return
    fetch()
    from reg import register, fit_trimmed

    qim = Image.open(path('tacoma1897.tif'))
    qr = QuadGeoref(qim)
    qrgb = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
    qf = ink(qrgb); del qrgb
    W, E, S, N = NEAT
    x0, y0 = qr.to_px(W, N); x1, y1 = qr.to_px(E, S)
    qf[:int(y0)+8, :] = 0; qf[int(y1)-8:, :] = 0
    qf[:, :int(x0)+8] = 0; qf[:, int(x1)-8:] = 0
    target = [dict(name='tacoma1897', feat=qf, to_px=qr.to_px, m_per_px=qr.scale[0])]

    lons = np.arange(W+0.03, E-0.02, 0.04)
    lats = np.arange(S+0.03, N-0.02, 0.04)
    fits = {}
    for pl in PLATES:
        p('· [%s] reading the plate…' % pl['id'])
        rgb = np.asarray(Image.open(path(pl['jpg'])), dtype=np.uint8)
        plate_f = ink(rgb); del rgb
        fx0, fy0, fx1, fy1 = pl['frame']
        plate_f[:fy0-10, :] = 0; plate_f[fy1+10:, :] = 0
        plate_f[:, :fx0-10] = 0; plate_f[:, fx1+10:] = 0

        if 'corners' in pl:
            # similarity seed from the plate's neatline corners, in the LCC
            # plane — the SeedAff construction from bitterroot/pipeline
            (llA, pxA), (llB, pxB) = pl['corners']
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
            p('· %s anchor seed: %.2f m/px, rotation %.2f°'
              % (pl['id'], m_scan, math.degrees(th)))
            X, Y, gx, gy, m_per_px = register(plate_f, target, LCC, lons, lats,
                                              m_scan_hint=m_scan, seed_fit=SeedAff(),
                                              pw=150, sw=260, log=p)
        else:
            X, Y, gx, gy, m_per_px = register(plate_f, target, LCC, lons, lats,
                                              m_scan_hint=10.5, z_lo=0.86, z_hi=1.16,
                                              pw=150, sw=130, log=p)
        if len(gx) < 12: raise SystemExit('%s: too few GCPs' % pl['id'])
        fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name=pl['id']+' pass 1',
                              m_per_px=m_per_px, log=p)
        X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                                   m_scan_hint=m_per_px, seed_fit=fit1,
                                   pw=150, sw=200, log=p)
        fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name=pl['id']+' pass 2',
                              m_per_px=m_per_px, log=p)
        X, Y, gx, gy, _ = register(plate_f, target, LCC, lons, lats,
                                   m_scan_hint=m_per_px, seed_fit=fit2,
                                   pw=150, sw=pl['sw_final'], log=p)
        if len(gx) < 14: raise SystemExit('%s: too few GCPs' % pl['id'])
        fit, keep = fit_trimmed(X, Y, gx, gy, 2, name=pl['id']+' fit',
                                m_per_px=m_per_px, log=p)
        fits[pl['id']] = dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                              cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                              rms=round(fit.rms, 2), median=round(fit.median, 2),
                              m_per_px=round(m_per_px, 3), n=int(keep.sum()))
        im = Image.open(path(pl['jpg']))
        overlay(im, {(255, 40, 40): list(zip(gx[keep], gy[keep]))},
                path('qa_georef_%s.png' % pl['id']), 1500)
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
    inside = ((lon27 >= NEAT[0]) & (lon27 <= NEAT[1]) &
              (lat27 >= NEAT[2]) & (lat27 <= NEAT[3]))
    np.save(path('mask.npy'), inside)
    X27, Y27 = LCC.fwd(lon27, lat27)

    def drape_from(pl, grid, X, Y, ins):
        src_img = Image.open(path(pl['jpg']))
        paper = paper_tone(src_img, pl['frame'])
        src = np.asarray(src_img.convert('RGB'), dtype=np.float32); del src_img
        SX, SY = fits[pl['id']].apply(X, Y)
        fx0, fy0, fx1, fy1 = pl['frame']
        ok = ins & (SX > fx0-6) & (SX < fx1+6) & (SY > fy0-6) & (SY < fy1+6)
        np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
        tex = np.zeros((grid.TH, grid.TW, 3), np.float32)
        tex[:] = paper
        for c in range(3):
            tex[:, :, c][ok] = ndimage.map_coordinates(
                src[:, :, c], [SY[ok], SX[ok]], order=1, mode='nearest')
        del src
        p('  %s: %d texels, paper %s' % (pl['id'], int(ok.sum()), np.round(paper).astype(int)))
        return tex

    p('· resampling the folio geology…')
    tex = drape_from(PLATES[0], g, X27, Y27, inside)
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))

    p('· resampling the timber classification…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    ins2 = ((lo2 >= NEAT[0]) & (lo2 <= NEAT[1]) & (la2 >= NEAT[2]) & (la2 <= NEAT[3]))
    X272, Y272 = LCC.fwd(lo2, la2)
    alt = drape_from(PLATES[1], g2, X272, Y272, ins2)
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
MINING = {'Adit': 'adit', 'Mine Shaft': 'shaft', 'Coal Mine': 'coal',
          'Strip Mine': 'coal', 'Prospect Pit': 'prospect',
          'Clay Pit': 'clay', 'Quarry': 'quarry'}

def mines(g):
    """The Survey's own mapped mine workings (USMIN), thinned by cell.
    Gravel and borrow pits — the highway era — are left out."""
    sites = json.load(open(path('usmin.json')))
    picks = {}
    for s in sites:
        if s['t'] not in MINING: continue
        u, v = g.uv(s['lon'], s['lat'])
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        name = (s['n'] or s['t']).strip()
        cell = (int(u*40), int(v*56))
        good = (bool(s['n']), s['t'] != 'Prospect Pit', -len(name))
        if cell not in picks or good > picks[cell][0]:
            picks[cell] = (good, dict(n=name[:26], u=round(u, 5), v=round(v, 5),
                                      c=MINING[s['t']]))
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
    p('· encoding the 1900 timber layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[233, 224, 202], [225, 216, 192], [215, 206, 180], [205, 196, 168],
            [196, 185, 156], [190, 175, 145], [186, 165, 134], [181, 154, 123],
            [174, 143, 112], [166, 133, 103], [158, 125, 97], [153, 121, 96],
            [158, 129, 107], [170, 145, 126], [185, 165, 149]]
    ramp_ft = [360*i for i in range(len(ramp))]

    p('· thinning the USMIN workings…')
    M = mines(g)
    p('  %d workings kept' % len(M))

    fits = json.load(open(path('fits.json')))
    worst = max(fits.values(), key=lambda d: d['rms'])
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=M,
               ui=dict(exagDef=2.2, exagMax=6.0, contourM=15.24, mineDist=0.55,
                       mineGlyph='⚒', rampLo=1, rampHi=5400,
                       sheetA='1899 geology', altName='1900 timber survey',
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
