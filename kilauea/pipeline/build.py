#!/usr/bin/env python3
"""Kīlauea and Mauna Loa — asset pipeline.

Four engraved 15-minute quadrangles of the island of Hawaiʻi tiled into one
half-degree block — MAUNA LOA (1928), KILAUEA (1921), HONUAPO (1924) and
PAHALA (1923), all 1:62,500, contour interval 50 feet — draped over
Terrarium elevations from the Kaʻū surf to Mokuʻāweoweo at 13,678 feet,
with Harold T. Stearns' geologic map of the Kaʻū district (USGS
Water-Supply Paper 616, Plate 1, geology 1924, published 1930) as the
middle layer.

The quads carry their own polyconic georeference.  **They are not NAD27.**
HTMC stages every Hawaii sheet with a NAD27 datum geokey, but the graticule
printed on them is the Old Hawaiian Datum, and on this island the two are
575 m apart — a third of a mile, thirty texels.  `wgs84_to_ohd` below
applies the island-of-Hawaiʻi Molodensky shift instead, and the `datum`
stage draws the DEM's own shoreline over the Honuapo sheet under each
candidate so the choice can be looked at rather than believed
(work/qa_datum.png).

Stearns' plate was drawn on these very quadrangles ("Base from U. S.
Geological Survey maps of Puna, Kilauea, Mauna Loa, Pahala, Honuapo, and
Kalae quadrangles, surveyed in 1912-1922"), so it registers same-lineage:
correlation on the local high-pass ink mask, no hand-picked points, and the
residual belongs in single-digit plate pixels.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, datum, georef, resample, encode.
"""
import json, os, sys, urllib.request, zipfile

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('KI_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import (Lcc, polyconic, _molodensky,
                  CLARKE_A, CLARKE_INVF, WGS_A, WGS_INVF)
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, DATED_FLOWS

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/HI/'
PLATE_PDF = 'https://pubs.usgs.gov/wsp/0616/plate-1.pdf'
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'DomesticNames/DomesticNames_HI_Text.zip')
GNIS_2021 = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
             'Archive/MainDomestic/HI_Features_20210825.txt')

QUADS = [  # id, url, neat (W, E, S, N) on the sheets' own printed graticule
    dict(id='maunaloa1928', url=S3+'HI_Mauna%20Loa_349891_1928_62500_geo.tif',
         neat=(-155.75, -155.50, 19.25, 19.50)),
    dict(id='kilauea1921', url=S3+'HI_Kilauea_349872_1921_62500_geo.tif',
         neat=(-155.50, -155.25, 19.25, 19.50)),
    dict(id='honuapo1924', url=S3+'HI_Honuapo_349835_1924_62500_geo.tif',
         neat=(-155.75, -155.50, 19.00, 19.25)),
    dict(id='pahala1923', url=S3+'HI_Pahala_349895_1923_62500_geo.tif',
         neat=(-155.50, -155.25, 19.00, 19.25)),
]
BLOCK = (-155.75, -155.25, 19.00, 19.50)

# Plate 1 is 43.0 × 43.5 inches; rasterised at 300 dpi it lands on the
# quads' own 5.29 m/px, so the correlation runs at scale 1.  Two printed
# panels sit inside the block and must never drape: Stearns' EXPLANATION,
# which floats in the unmapped white above 8,000 ft on Mauna Loa, and the
# four cross-sections, which he drew out in the Pacific.
PLATE_DPI = 300
M_PX = 62500*0.0254/PLATE_DPI          # 5.292 m per plate pixel
PLON0, PLAT0 = -155.5, 19.25           # a polyconic origin near the plate's
LEGEND   = (1920,  980,  3140,  5200)
SECTIONS = (6400, 8240, 12400, 11240)

LCC = Lcc(19.1, 19.4, -155.5)
MARGIN = 0.0006                        # ~3.8 km of paper apron round the block
TEX_W, HGT_W, ALT_W = 2816, 1877, 1920
DEM_ZOOM, DEM_BOX = 13, (-155.92, -155.08, 18.84, 19.67)
CLAMP = (0, 4300)          # below 0 is open-Pacific bathymetry — void it
                           # before the mosaic is smoothed, or the shoreline
                           # gets a two-kilometre trench dug along it; the
                           # sea is then held dead flat at zero (see below)
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]], MARGIN, TEX_W)

def wgs84_to_ohd(lon, lat):
    """WGS84 → the Old Hawaiian Datum of the island of Hawaiʻi (Clarke 1866).

    NIMA TR8350.2 lists OHD→WGS84 for Hawaiʻi as dx +89, dy −279, dz −183 m;
    negated here for the reverse, exactly as lib/proj negates the CONUS
    three-parameter set for `wgs84_to_nad27`.  Using the CONUS numbers on
    this island puts the sheets 575 m out — see the `datum` stage.
    """
    return _molodensky(lon, lat, -89.0, 279.0, 183.0,
                       WGS_A, WGS_INVF, CLARKE_A, CLARKE_INVF)

def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its
    12-px neighbourhood.  These sheets are printed almost entirely in brown
    and blue under a green-and-pink geologic wash, where lib/reg's
    black-plus-blue mask sees nearly nothing."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

def get(url, out, note, ua='old-time-maps/1.0', timeout=600):
    if os.path.exists(out): return out
    p('· downloading %s…' % note)
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(out, 'wb') as f:
        f.write(r.read())
    return out

# ------------------------------------------------------------------ stage 1
def fetch():
    for q in QUADS:
        get(q['url'], path(q['id'] + '.tif'), 'the %s sheet' % q['id'])
    if not os.path.exists(path('wsp616_plate1.jpg')):
        pdf = get(PLATE_PDF, path('wsp616_plate1.pdf'),
                  'Water-Supply Paper 616, plate 1', ua='Mozilla/5.0')
        p('· rasterising Stearns\' plate at %d dpi…' % PLATE_DPI)
        import pypdfium2 as pdfium
        page = pdfium.PdfDocument(pdf)[0]
        im = page.render(scale=PLATE_DPI/72).to_pil().convert('RGB')
        p('  %d × %d px  (~%.2f m/px at 1:62,500)'
          % (im.width, im.height, 62500*0.0254/PLATE_DPI))
        im.save(path('wsp616_plate1.jpg'), quality=95)
    get(GNIS, path('gnis_hi.zip'), 'GNIS domestic names (HI)')
    get(GNIS_2021, path('gnis_hi_2021.txt'), 'the 2021 GNIS archive (elevations)')
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def datum():
    """Draw the DEM's own shoreline over the Honuapo sheet under each
    candidate datum shift, and keep the three panels side by side.  The one
    that lands the red line on the printed coast is the datum the scan is
    staged in; nothing here is fitted, and nothing is picked by hand."""
    if os.path.exists(path('qa_datum.png')):
        p('· datum check cached'); return
    fetch()
    from proj import wgs84_to_nad27
    box = (-155.578, -155.520, 19.068, 19.126)      # Honuʻapo Bay, ~6 km square
    gg = Grid.around(Lcc(19.07, 19.12, -155.549), [box[0], box[1]],
                     [box[2], box[3]], 0.0, 1400)
    _, _, LON, LAT = gg.lonlat()
    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, (-12000, 4300), log=p)
    h = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    lnd = h > 0
    shore = ndimage.binary_dilation(lnd, iterations=2) ^ ndimage.binary_erosion(lnd, iterations=2)
    im = Image.open(path('honuapo1924.tif')); qr = QuadGeoref(im)
    src = np.asarray(im.convert('RGB'), dtype=np.float32); del im
    panels = []
    for name, fn in (('as tagged (WGS84)', lambda a, b: (a, b)),
                     ('CONUS NAD27', wgs84_to_nad27),
                     ('Old Hawaiian', wgs84_to_ohd)):
        lo, la = fn(LON, LAT)
        QX, QY = qr.to_px(lo, la)
        np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
        out = np.zeros((gg.TH, gg.TW, 3), np.float32)
        for c in range(3):
            out[:, :, c] = ndimage.map_coordinates(src[:, :, c], [QY, QX],
                                                   order=1, mode='nearest')
        out[shore] = [225, 20, 20]
        panels.append((name, np.clip(out, 0, 255).astype(np.uint8)))
        p('  panel: %s' % name)
    from PIL import ImageDraw
    w = 620
    tiles = [Image.fromarray(a).resize((w, int(w*a.shape[0]/a.shape[1])), Image.LANCZOS)
             for _, a in panels]
    sheet = Image.new('RGB', (w*3+40, tiles[0].height+34), (245, 242, 235))
    d = ImageDraw.Draw(sheet)
    for i, (t, (name, _)) in enumerate(zip(tiles, panels)):
        sheet.paste(t, (i*(w+20), 30))
        d.text((i*(w+20)+6, 10), name, fill=(20, 20, 20))
    sheet.save(path('qa_datum.png'))
    p('  QA in work/qa_datum.png — Old Hawaiian is the one that fits')

class SeedAff:
    """Plate pixels straight out of the sheets' own projection.

    Stearns' plate is the same American Polyconic at the same 1:62,500 as
    the quadrangles under it, printed north-up, so at 300 dpi the scale is
    known (5.292 m/px) and the rotation is zero: the only unknown is where
    the paper's origin sits, and `seed_offset` finds that with one
    normalised correlation.  Choosing a polyconic origin other than the
    plate's own costs at most ~19 m of non-translational error across this
    block — well inside the search window, and the polynomial fit that
    follows absorbs it.
    """
    def __init__(self, ox, oy):
        self.ox, self.oy = float(ox), float(oy)
    def apply(self, X, Y):
        lon, lat = LCC.inv(X, Y)
        x, y = polyconic(lon, lat, PLON0, PLAT0)
        return self.ox + x/M_PX, self.oy - y/M_PX

def seed_offset(plate_f, targets, log=print):
    """Slide the block's own ink over the plate at 1/8 resolution.

    lib/reg's stage A sweeps scale with an *unnormalised* correlation and,
    on a sheet that is two-thirds dense contour and one-third blank paper,
    it walks straight into the dense third: it put this block's northwest
    corner on the plate's northeast one.  Here the scale is not a free
    parameter, so a single normalised cross-correlation settles it.
    """
    from scipy.signal import fftconvolve
    D = 8
    n = 2200
    LO, LA = np.meshgrid(np.linspace(BLOCK[0], BLOCK[1], n),
                         np.linspace(BLOCK[3], BLOCK[2], n))
    px, py = polyconic(LO, LA, PLON0, PLAT0)
    U = px/(M_PX*D); V = -py/(M_PX*D)
    umin, vmin = U.min(), V.min()
    iu = np.round(U-umin).astype(np.int32); iv = np.round(V-vmin).astype(np.int32)
    Hh, Ww = int(iv.max())+1, int(iu.max())+1
    idx = (iv*Ww + iu).ravel()
    acc = np.zeros(Hh*Ww, np.float64); cnt = np.zeros(Hh*Ww, np.float64)
    for t in targets:
        qx, qy = t['to_px'](LO, LA)
        ok = ((qx > 1) & (qx < t['feat'].shape[1]-2) &
              (qy > 1) & (qy < t['feat'].shape[0]-2))
        val = np.zeros(LO.shape, np.float32)
        val[ok] = ndimage.map_coordinates(t['feat'], [qy[ok], qx[ok]], order=1)
        acc += np.bincount(idx, weights=np.where(ok, val, 0.0).ravel(), minlength=Hh*Ww)
        cnt += np.bincount(idx, weights=ok.astype(np.float64).ravel(), minlength=Hh*Ww)
    B = (acc/np.maximum(cnt, 1)).reshape(Hh, Ww).astype(np.float32)
    M = (cnt.reshape(Hh, Ww) > 0).astype(np.float32)
    Bz = np.where(M > 0, B - float(B[M > 0].mean()), 0.0).astype(np.float32)

    A = np.ascontiguousarray(plate_f[::D, ::D])
    num = fftconvolve(A, Bz[::-1, ::-1], 'valid')
    s1 = fftconvolve(A, M[::-1, ::-1], 'valid')
    s2 = fftconvolve(A*A, M[::-1, ::-1], 'valid')
    k = float(M.sum())
    sd = np.sqrt(np.maximum(s2 - s1*s1/k, 1e-4))
    score = num/sd
    j = np.unravel_index(np.argmax(score), score.shape)
    peak = float(score[j]); med = float(np.median(score))
    ox, oy = D*(j[1] - umin), D*(j[0] - vmin)
    log('  seed: plate origin (%.0f, %.0f) px, peak %.1f vs median %.1f'
        % (ox, oy, peak, med))
    return ox, oy

def restrict_to_shared_ink(targets, plate_f, seed, log=print):
    """Blind each quad wherever Stearns' paper is blank.

    A third of this block is not on his map — the unmapped white above about
    8,000 feet on Mauna Loa, the Pacific south of the Kaʻū cliffs, and the
    two panels he printed inside the neat.  Left in, the lattice offers the
    correlator patches with nothing to match, and it answers anyway.
    """
    D = 8
    cov = ndimage.uniform_filter(plate_f[::D, ::D], 11) > 0.012
    ch, cw = cov.shape
    for t in targets:
        qh, qw = t['feat'].shape
        ys, xs = np.mgrid[0:qh:24, 0:qw:24]
        # quad px -> plate px is all but affine over one 15-minute sheet;
        # fit that affine from the seed on a coarse lattice, then invert it
        lo, la = np.meshgrid(np.linspace(-155.80, -155.20, 40),
                             np.linspace(18.95, 19.55, 40))
        qx, qy = t['to_px'](lo, la)
        X, Y = LCC.fwd(lo, la)
        sx, sy = seed.apply(X, Y)
        A = np.stack([qx.ravel(), qy.ravel(), np.ones(qx.size)], 1)
        cx, *_ = np.linalg.lstsq(A, sx.ravel(), rcond=None)
        cy, *_ = np.linalg.lstsq(A, sy.ravel(), rcond=None)
        PX = (cx[0]*xs + cx[1]*ys + cx[2])/D
        PY = (cy[0]*xs + cy[1]*ys + cy[2])/D
        keep = np.zeros(PX.shape, bool)
        inb = (PX >= 0) & (PX < cw-1) & (PY >= 0) & (PY < ch-1)
        keep[inb] = cov[PY[inb].astype(int), PX[inb].astype(int)]
        big = ndimage.zoom(keep.astype(np.float32), (qh/keep.shape[0], qw/keep.shape[1]),
                           order=1)[:qh, :qw]
        if big.shape != (qh, qw):
            big = np.pad(big, ((0, qh-big.shape[0]), (0, qw-big.shape[1])))
        before = float((t['feat'] > 0.02).mean())
        t['feat'] *= (big > 0.5)
        log('  %s: %.0f%% of its ink is on Stearns\' paper'
            % (t['name'], 100*float((t['feat'] > 0.02).mean())/max(before, 1e-6)))

# ------------------------------------------------------------------ stage 3
def georef():
    """Register Stearns' plate against the four quads it was printed on."""
    if os.path.exists(path('fit.json')):
        p('· georeference cached'); return
    datum()
    from reg import register, fit_trimmed
    p('· reading the plate (%d dpi)…' % PLATE_DPI)
    rgb = np.asarray(Image.open(path('wsp616_plate1.jpg')), dtype=np.uint8)
    plate_f = ink(rgb); ph, pw2 = plate_f.shape; del rgb
    plate_f[:int(ph*0.03), :] = 0; plate_f[int(ph*0.97):, :] = 0
    plate_f[:, :int(pw2*0.03)] = 0; plate_f[:, int(pw2*0.97):] = 0
    for x0, y0, x1, y1 in (LEGEND, SECTIONS):
        plate_f[y0:y1, x0:x1] = 0
    p('  %d × %d, legend and sections blanked' % (pw2, ph))

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

    p('· seeding from the sheets\' own projection…')
    seed = SeedAff(*seed_offset(plate_f, targets, log=p))
    restrict_to_shared_ink(targets, plate_f, seed, log=p)
    mpp = M_PX

    lons = np.arange(BLOCK[0]+0.012, BLOCK[1]-0.008, 0.016)
    lats = np.arange(BLOCK[2]+0.012, BLOCK[3]-0.008, 0.016)
    p('· correlating the plate against the four sheets…')
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=mpp, seed_fit=seed,
                               pw=200, sw=200, log=p)
    if len(gx) < 20: raise SystemExit('too few GCPs on pass 1')
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name='Stearns pass 1', floor=4.0,
                          k=2.2, rounds=4, m_per_px=mpp, log=p)
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=mpp, seed_fit=fit1,
                               pw=200, sw=240, log=p)
    fit2, _ = fit_trimmed(X, Y, gx, gy, 2, name='Stearns pass 2', floor=4.0,
                          k=2.2, rounds=4, m_per_px=mpp, log=p)
    X, Y, gx, gy, _ = register(plate_f, targets, LCC, lons, lats,
                               m_scan_hint=mpp, seed_fit=fit2,
                               pw=200, sw=55, log=p)
    if len(gx) < 24: raise SystemExit('too few GCPs after refine')
    fit, keep = fit_trimmed(X, Y, gx, gy, 2, name='Stearns fit', floor=4.0,
                            k=2.2, rounds=4, m_per_px=mpp, log=p)
    json.dump(dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                   cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                   rms=round(fit.rms, 2), median=round(fit.median, 2),
                   worst=round(fit.worst, 2),
                   m_per_px=round(mpp, 3), n=int(keep.sum())),
              open(path('fit.json'), 'w'))
    overlay(Image.open(path('wsp616_plate1.jpg')),
            {(255, 40, 40): list(zip(gx[keep], gy[keep]))},
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
    """Even out four printings from four years: scale each sheet's channels
    so its paper white (94th percentile) meets the mosaic's median.

    The clip is wider than the gallery's usual 0.90–1.11 because it has to
    be: the 1921 Kilauea printing is on markedly whiter stock than its three
    neighbours — 245 against 211 in blue — and at the usual clip the seam
    down 155°30′ stayed visible.
    """
    whites = {k: np.array([np.percentile(tex[:, :, c][m], 94) for c in range(3)])
              for k, m in regions.items() if m.any()}
    target = np.median(np.stack(list(whites.values())), axis=0)
    for k, m in regions.items():
        if k not in whites: continue
        s = np.clip(target/np.maximum(whites[k], 1), 0.82, 1.22)
        log('  %s %s: paper × %s' % (label, k, np.round(s, 3)))
        for c in range(3):
            tex[:, :, c][m] *= s[c]

# ------------------------------------------------------------------ stage 4
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    fit = SavedFit(json.load(open(path('fit.json'))))
    g = make_grid()
    p('· conic grid %d × %d  (%.0f × %.0f km, %.1f m/texel)'
      % (g.TW, g.TH, g.kmw, g.kmh, g.m_per_texel))
    GX, GY, LON, LAT = g.lonlat()

    # two passes over the same tiles: one keeps the bathymetry only long
    # enough to say where the sea is, the other is the land surface with the
    # bathymetry voided out before smoothing.
    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, (-12000, 4300), log=p)
    sea = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT) < 0.0; del mos
    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    hgt[sea] = 0.0
    p('  elevation %.0f – %.0f m  (%.1f%% of the block is sea)'
      % (hgt.min(), hgt.max(), 100*sea.mean()))
    np.save(path('hgt.npy'), hgt)

    lonH, latH = wgs84_to_ohd(LON, LAT)
    inside = ((lonH >= BLOCK[0]) & (lonH <= BLOCK[1]) &
              (latH >= BLOCK[2]) & (latH <= BLOCK[3]))
    np.save(path('mask.npy'), inside)
    XH, YH = LCC.fwd(lonH, latH)

    p('· resampling the four sheets…')
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    regions = {}
    for q in QUADS:
        W, E, S, N = q['neat']
        inq = inside & (lonH >= W) & (lonH <= E) & (latH >= S) & (latH <= N)
        qim = Image.open(path(q['id'] + '.tif'))
        qr = QuadGeoref(qim)
        src = np.asarray(qim.convert('RGB'), dtype=np.uint8); del qim
        QX, QY = qr.to_px(lonH[inq], latH[inq])
        np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
        for c in range(3):
            # the sheets are 5.3 m/px and the drape is ~19; pre-smooth or the
            # 50-foot contours alias into moiré on Mauna Loa's flanks
            ch = ndimage.gaussian_filter(src[:, :, c].astype(np.float32), 1.1)
            tex[:, :, c][inq] = ndimage.map_coordinates(ch, [QY, QX], order=1,
                                                        mode='nearest')
            del ch
        del src
        regions[q['id']] = inq
        p('  %s: %d texels' % (q['id'], int(inq.sum())))
    tone_match(tex, regions, 'sheet', p)
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))
    del tex

    p('· resampling the Kaʻū geology…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_ohd(LON2, LAT2)
    X2, Y2 = LCC.fwd(lo2, la2)
    SX, SY = fit.apply(X2, Y2)
    src = np.asarray(Image.open(path('wsp616_plate1.jpg')).convert('RGB'), dtype=np.uint8)
    ok2 = ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) &
           (la2 >= BLOCK[2]) & (la2 <= BLOCK[3]) &
           (SX > 4) & (SX < src.shape[1]-5) & (SY > 4) & (SY < src.shape[0]-5))
    for x0b, y0b, x1b, y1b in (LEGEND, SECTIONS):
        ok2 &= ~((SX >= x0b) & (SX < x1b) & (SY >= y0b) & (SY < y1b))
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32); alt[:] = PAPER
    for c in range(3):
        ch = ndimage.gaussian_filter(src[:, :, c].astype(np.float32), 1.8)
        alt[:, :, c][ok2] = ndimage.map_coordinates(ch, [SY[ok2], SX[ok2]],
                                                    order=1, mode='nearest')
        del ch
    del src
    p('  %d of %d alt texels carry the plate (%.0f%%)'
      % (int(ok2.sum()), ok2.size, 100*ok2.mean()))
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 5
def gnis_rows():
    """Current GNIS names (which carry the ʻokina and kahakō) joined to the
    2021 archive, the last edition that still published elevations."""
    z = zipfile.ZipFile(path('gnis_hi.zip'))
    f = z.open('Text/DomesticNames_HI.txt')
    hdr = f.readline().decode('utf-8-sig').strip().split('|')
    ix = {k: hdr.index(k) for k in ('feature_id', 'feature_name', 'feature_class',
                                    'prim_lat_dec', 'prim_long_dec')}
    cur = {}
    for ln in f:
        c = ln.decode('utf-8', 'replace').rstrip('\n').split('|')
        try:
            lat, lon = float(c[ix['prim_lat_dec']]), float(c[ix['prim_long_dec']])
        except ValueError:
            continue
        cur[c[ix['feature_id']]] = dict(n=c[ix['feature_name']].strip(),
                                        cls=c[ix['feature_class']], lat=lat, lon=lon)
    with open(path('gnis_hi_2021.txt'), encoding='utf-8-sig') as fh:
        h = fh.readline().strip().split('|')
        j = {k: h.index(k) for k in ('FEATURE_ID', 'ELEV_IN_FT')}
        for ln in fh:
            c = ln.rstrip('\n').split('|')
            r = cur.get(c[j['FEATURE_ID']])
            if r is not None:
                try: r['ft'] = int(c[j['ELEV_IN_FT']])
                except ValueError: pass
    return list(cur.values())

def flows(g):
    """The data layer: every named lava flow and kīpuka GNIS carries inside
    the block.  Dated flows first — 1823 through 1974 — then the kīpuka, the
    islands of old ground the flows went round.  Thinned by cell so the
    Southwest Rift does not become a wall of type."""
    picks = {}
    for r in gnis_rows():
        if r['cls'] != 'Lava': continue
        u, v = g.uv(r['lon'], r['lat'])
        if not (0.008 < u < 0.992 and 0.008 < v < 0.992): continue
        name = r['n']
        dated = any(y in name for y in DATED_FLOWS)
        cell = (int(u*40), int(v*42))
        good = (2 if dated else (1 if 'Kīpuka' not in name else 0), -len(name))
        if cell not in picks or good > picks[cell][0]:
            picks[cell] = (good, dict(n=name[:26], u=round(u, 5), v=round(v, 5),
                                      c='flow' if dated else 'kipuka'))
    out = [t[1] for t in picks.values()]
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
    p('· encoding the Kaʻū geology layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [1 + 976*i for i in range(len(ramp))]   # 1 ft to Mauna Loa's 13,665

    p('· picking the named flows and kīpuka…')
    F = flows(g)
    p('  %d kept (%d dated flows)' % (len(F), sum(1 for m in F if m['c'] == 'flow')))

    fitd = json.load(open(path('fit.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=F,
               ui=dict(exagDef=1.6, exagMax=5.0, contourM=15.24, mineDist=0.46,
                       mineGlyph='≈', rampLo=1, rampHi=13665,
                       sheetA='1921–28 sheets', altName='1930 Kaʻū geology',
                       tourEx=[1.05, 0.01, 1.15, 2.4]),
               fit=dict(rms=fitd['rms'], median=fitd['median'], n=fitd['n']))

STAGES = [('fetch', fetch), ('datum', datum), ('georef', georef),
          ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
