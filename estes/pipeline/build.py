#!/usr/bin/env python3
"""Rocky Mountain National Park — asset pipeline.

The one classic USGS park special that survives complete and georeferenced
in the Historical Topographic Map Collection: *Topographic map of Rocky
Mountain National Park, Colorado*, 1:125,000, surveyed 1912–15 — draped over
Terrarium elevations, with the **Longs Peak** 30-minute quadrangle of the
same survey (engraved February 1915, edition of May 1915) as the middle
layer.  The two sheets share one half-degree neat, 40°00′–40°30′ N by
105°30′–106°00′ W, and one field party; they differ by a contour interval,
a park boundary, a highway and two reservoirs.

Both files are HTMC GeoTIFFs carrying their own polyconic / NAD27
georeference, so **nothing here is fitted**.  The `georef` stage is a
verification stage instead: it reads both transforms, probes the printed
neatline corners through each, and then measures — without applying — how
far the two embedded georeferences disagree, by correlating the park
special's engraving into the Longs Peak scan at positions the Longs Peak
geokeys predict on their own.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import json, os, sys, urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('ES_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, GNIS_NAME

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/CO/'
# The live GNIS product is used here only to audit places.py: every summit's
# coordinates and feet must come from a GNIS record, never from memory.
GNIS2021 = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
            'Archive/MainDomestic/CO_Features_20210825.txt')
SHEETS = [  # id, file, url — both 1:125,000, both on the same neat
    dict(id='park1915', name='park special',
         url=S3 + 'CO_Rocky%20Mountain%20National%20Park_234287_1915_125000_geo.tif'),
    dict(id='longs1915', name='Longs Peak quad',
         url=S3 + 'CO_Longs%20Peak_402456_1915_125000_geo.tif'),
]
NEAT = (-106.0, -105.5, 40.0, 40.5)          # the printed graticule box (NAD27)
BLOCK = NEAT

LCC = Lcc(40.1, 40.4, -105.75)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2560, 1707, 1920
DEM_ZOOM, DEM_BOX = 12, (-106.22, -105.28, 39.85, 40.66)
CLAMP = (1400, 4500)                         # Longs Peak (14,259 ft) is in-block
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]],
                       MARGIN, TEX_W)

def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its 12-px
    neighbourhood.  The park special prints its relief in brown under no wash
    at all and the quadrangle prints it in orange-brown under a green
    woodland tint — lib/reg's black+blue mask goes blind on both, this does
    not."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

def scan(sheet):
    """(PIL image, QuadGeoref) for one sheet, opened lazily from work/."""
    im = Image.open(path(sheet['id'] + '.tif'))
    return im, QuadGeoref(im)

# ------------------------------------------------------------------ stage 1
def fetch():
    for s in SHEETS:
        tif = path(s['id'] + '.tif')
        if not os.path.exists(tif):
            p('· downloading the %s…' % s['name'])
            req = urllib.request.Request(s['url'],
                                         headers={'User-Agent': 'old-time-maps/1.0'})
            with urllib.request.urlopen(req, timeout=600) as r, open(tif, 'wb') as f:
                f.write(r.read())
    if not os.path.exists(path('gnis_co_2021.txt')):
        p('· downloading GNIS 2021 archive (CO — it still carries elevations)…')
        req = urllib.request.Request(GNIS2021, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=600) as r:
            open(path('gnis_co_2021.txt'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Read both embedded georeferences; verify, do not fit.

    Check 1 — the printed neat.  The four corners of the 30-minute block are
    pushed through each scan's own geokeys and reported in scan pixels; both
    sheets must put the block wholly inside their map body.

    Check 2 — agreement.  Patches of the park special are correlated into the
    Longs Peak scan at the positions the Longs Peak geokeys predict.  The
    residual is *measured and printed*; it is never applied to anything.
    """
    if os.path.exists(path('georef.json')):
        p('· georeference cached'); return
    fetch()
    W, E, S, N = NEAT
    out = dict(neat=list(NEAT), sheets={})
    for s in SHEETS:
        im, qr = scan(s)
        corners = {}
        for tag, (lo, la) in dict(NW=(W, N), NE=(E, N), SW=(W, S), SE=(E, S)).items():
            x, y = qr.to_px(lo, la)
            corners[tag] = [round(float(x), 1), round(float(y), 1)]
            assert 0 < x < im.width and 0 < y < im.height, \
                '%s: neat corner %s falls off the scan' % (s['id'], tag)
        wpx = corners['NE'][0] - corners['NW'][0]
        p('· %-16s %d × %d px, %.4f m/px, polyconic lon0 %.2f lat0 %.2f (%s)'
          % (s['id'], im.width, im.height, qr.scale[0], qr.lon0, qr.lat0, qr.datum))
        p('    neat NW %s  NE %s  SW %s  SE %s'
          % (corners['NW'], corners['NE'], corners['SW'], corners['SE']))
        p('    30′ of longitude = %.1f px = %.2f km' % (wpx, wpx*qr.scale[0]/1e3))
        out['sheets'][s['id']] = dict(px=[im.width, im.height],
                                      m_per_px=round(float(qr.scale[0]), 4),
                                      lon0=qr.lon0, lat0=qr.lat0, datum=qr.datum,
                                      corners=corners)
        im.close()

    # --- check 2: how far apart do the two embedded transforms place things?
    from reg import register
    p('· measuring the two georeferences against each other…')
    pim, pqr = scan(SHEETS[0])
    pf = ink(np.asarray(pim.convert('RGB'), dtype=np.uint8)); pim.close()
    px0, py0 = pqr.to_px(W, N); px1, py1 = pqr.to_px(E, S)
    pf[:int(py0)+8, :] = 0; pf[int(py1)-8:, :] = 0
    pf[:, :int(px0)+8] = 0; pf[:, int(px1)-8:] = 0
    lim, lqr = scan(SHEETS[1])
    lf = ink(np.asarray(lim.convert('RGB'), dtype=np.uint8)); lim.close()

    class Passthrough:
        """The Longs Peak sheet's own geokeys, in the shape register() wants."""
        def apply(self, X, Y):
            lo, la = LCC.inv(X, Y)
            return lqr.to_px(lo, la)

    lons = np.arange(W+0.03, E-0.029, 0.035)
    lats = np.arange(S+0.03, N-0.029, 0.035)
    X, Y, gx, gy, _ = register(lf, [dict(name='park1915', feat=pf, to_px=pqr.to_px,
                                         m_per_px=float(pqr.scale[0]))],
                               LCC, lons, lats, m_scan_hint=float(lqr.scale[0]),
                               seed_fit=Passthrough(), pw=150, sw=60, log=p)
    agree = None
    if len(gx) >= 20:
        sx, sy = Passthrough().apply(X, Y)
        d = np.hypot(gx-sx, gy-sy)
        keep = d < max(8.0, float(np.median(d))*3.0)   # drop contour-lock outliers
        d = d[keep]
        mpp = float(lqr.scale[0])
        agree = dict(n=int(keep.sum()),
                     rms=round(float(np.sqrt((d*d).mean())), 2),
                     median=round(float(np.median(d)), 2),
                     worst=round(float(d.max()), 2),
                     m_per_px=round(mpp, 3),
                     median_m=round(float(np.median(d))*mpp, 1),
                     rms_m=round(float(np.sqrt((d*d).mean()))*mpp, 1))
        p('  the two embedded georeferences agree to %.2f px median, %.2f px rms'
          ' (%d of %d points) — %.0f m on the ground, nothing adjusted'
          % (agree['median'], agree['rms'], agree['n'], len(gx), agree['median_m']))
        im = Image.open(path('longs1915.tif'))
        overlay(im, {(255, 40, 40): list(zip(gx[keep], gy[keep])),
                     (30, 90, 230): list(zip(sx[keep], sy[keep]))},
                path('qa_georef.png'), 1500)
        im.close()
        p('  QA overlay in work/qa_georef.png (red measured, blue predicted)')
    else:
        p('  ! only %d matches — agreement not measured (the drape does not '
          'depend on it)' % len(gx))
    out['agreement'] = agree
    json.dump(out, open(path('georef.json'), 'w'), indent=1)

def tone(rgb, label, log):
    """Report a sheet's paper white — the two printings are left as printed."""
    w = [float(np.percentile(rgb[:, :, c], 96)) for c in range(3)]
    log('  %s paper white %s' % (label, np.round(w, 1)))
    return w

# ------------------------------------------------------------------ stage 3
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    g = make_grid()
    p('· conic grid %d × %d  (%.1f × %.1f km, %.1f m per texel)'
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
    p('  block covers %.1f%% of the grid' % (100.0*inside.mean()))

    p('· resampling the park special…')
    im, qr = scan(SHEETS[0])
    src = np.asarray(im.convert('RGB'), dtype=np.float32); im.close()
    tone(src, 'park special', p)
    QX, QY = qr.to_px(lon27[inside], lat27[inside])
    np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
    tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = PAPER
    for c in range(3):
        tex[:, :, c][inside] = ndimage.map_coordinates(
            src[:, :, c], [QY, QX], order=1, mode='nearest')
    del src, QX, QY
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))
    del tex

    p('· resampling the Longs Peak quadrangle…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    ok2 = ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) &
           (la2 >= BLOCK[2]) & (la2 <= BLOCK[3]))
    im, qr = scan(SHEETS[1])
    src = np.asarray(im.convert('RGB'), dtype=np.float32); im.close()
    tone(src, 'Longs Peak quad', p)
    AX, AY = qr.to_px(lo2[ok2], la2[ok2])
    np.clip(AX, 0, src.shape[1]-1, out=AX); np.clip(AY, 0, src.shape[0]-1, out=AY)
    alt = np.zeros((g2.TH, g2.TW, 3), np.float32); alt[:] = PAPER
    for c in range(3):
        alt[:, :, c][ok2] = ndimage.map_coordinates(
            src[:, :, c], [AY, AX], order=1, mode='nearest')
    del src
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def audit_places():
    """Every summit and town in places.py must be a GNIS record, to the digit.

    Memory once put Electric Peak 13 km wrong on another sheet; this makes
    the rule machine-checked instead of promised.  Keyed on feature class as
    well as name, because 'Grand Lake' is both a village and a lake."""
    want = {}                                  # (gnis name, classes) -> expected
    for n, la, lo, ft, _ in PEAKS:
        want[(GNIS_NAME.get(n, n), ('Summit',))] = (n, la, lo, ft)
    for n, la, lo, _ in CITIES:
        want[(GNIS_NAME.get(n, n), ('Populated Place', 'Locale'))] = (n, la, lo, None)
    found = {}
    with open(path('gnis_co_2021.txt'), encoding='utf-8-sig') as f:
        hdr = f.readline().strip().split('|')
        ix = {k: hdr.index(k) for k in ('FEATURE_NAME', 'FEATURE_CLASS',
                                        'PRIM_LAT_DEC', 'PRIM_LONG_DEC',
                                        'ELEV_IN_FT')}
        for ln in f:
            c = ln.split('|')
            nm = c[ix['FEATURE_NAME']].strip(); fc = c[ix['FEATURE_CLASS']]
            for key in want:
                if key[0] != nm or fc not in key[1] or key in found: continue
                try:
                    la = float(c[ix['PRIM_LAT_DEC']]); lo = float(c[ix['PRIM_LONG_DEC']])
                except ValueError:
                    continue
                if not (BLOCK[0] <= lo <= BLOCK[1] and BLOCK[2] <= la <= BLOCK[3]):
                    continue
                try: ft = int(c[ix['ELEV_IN_FT']])
                except ValueError: ft = None
                found[key] = (la, lo, ft)
    bad = []
    for key, (n, la, lo, ft) in want.items():
        g = found.get(key)
        if g is None:
            bad.append('%s: no GNIS %s record in the block' % (key[0], '/'.join(key[1])))
            continue
        if abs(g[0]-la) > 2e-5 or abs(g[1]-lo) > 2e-5:
            bad.append('%s: GNIS has %.5f %.5f, places.py has %.5f %.5f'
                       % (n, g[0], g[1], la, lo))
        if ft is not None and g[2] is not None and ft != g[2]:
            bad.append('%s: GNIS has %d ft, places.py has %d ft' % (n, g[2], ft))
    if bad:
        for b in bad: p('  ! ' + b)
        raise SystemExit('places.py disagrees with GNIS — fix it, do not guess')
    p('  %d summits and towns audited against GNIS: all exact' % len(want))

def verify_summits(g, hgt):
    """Each summit must stand up in the model where GNIS puts it.

    Two ways a peak can be wrong and one of them is invisible: a bad
    elevation (caught at ±130 m of the printed feet) and a bad *position* —
    `snap_places` hunts the local maximum in a ±1.5 km window, so a peak
    with a taller neighbour inside that window silently borrows its
    neighbour's summit.  Anything that walks more than 700 m is not this
    peak; drop it rather than mislabel a mountain."""
    TH, TW = hgt.shape
    r = max(1, int(1500/g.m_per_texel))
    bad, worst = [], 0.0
    for n, la, lo, ft, _ in PEAKS:
        u, v = g.uv(lo, la)
        x = min(max(int(round(u*TW)), 0), TW-1)
        y = min(max(int(round(v*TH)), 0), TH-1)
        w = hgt[max(0, y-r):y+r+1, max(0, x-r):x+r+1]
        j = np.unravel_index(np.argmax(w), w.shape)
        e = float(w[j])
        moved = float(np.hypot(max(0, x-r)+j[1]-x, max(0, y-r)+j[0]-y))*g.m_per_texel
        err = e - ft*0.3048
        worst = max(worst, abs(err))
        if abs(err) > 130: bad.append('%s: model is %+.0f m off %d ft' % (n, err, ft))
        if moved > 700: bad.append('%s: snaps %.0f m away — that is a neighbour' % (n, moved))
    if bad:
        for b in bad: p('  ! ' + b)
        raise SystemExit('summits fail the model check — drop them, do not guess')
    p('  %d summits verified against the model (worst %.0f m of their printed feet)'
      % (len(PEAKS), worst))

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
    p('· encoding the Longs Peak layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))

    p('· auditing places against GNIS and the model…')
    audit_places()
    verify_summits(g, hgt)
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    # the sheets' own inks: valley paper, sepia slope, mauve on the tundra
    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [7400 + 495*i for i in range(len(ramp))]

    gj = json.load(open(path('georef.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=[],
               ui=dict(exagDef=1.8, exagMax=6.0, contourM=30.48,
                       rampLo=7400, rampHi=14300,
                       sheetA='1915 park sheet', altName='Longs Peak 1915',
                       tourEx=[1.05, 0.01, 1.15, 2.4]),
               georef=gj.get('agreement'))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
