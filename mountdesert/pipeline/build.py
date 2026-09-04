#!/usr/bin/env python3
"""Pemetic — Mount Desert Island, asset pipeline.

The island the Wabanaki call Pemetic, drawn twice.  The primary drape is the
1904 USGS survey at 1:62,500 — BAR HARBOR and MOUNT DESERT joined at 68°15′ —
in the state the plates were reprinted in after February 1919, with
LAFAYETTE NATIONAL PARK lettered across the mountains and every summit
carrying its new name.  One slider-stop behind sits the 1942 edition of the
same two cells: a wholly new plane-table survey run in 1934-35 and 1939-40,
printed under a War Department imprint, with ACADIA NATIONAL PARK hatched in
red, Schoodic Peninsula inside it, and the motor roads and carriage roads
drawn for the first time.

All four scans are HTMC GeoTIFFs carrying their own polyconic georeference
(the 1904 plates on the old North American datum, the 1942 plates on NAD 1927),
so **both layers drape by passthrough — nothing is fitted.**
What the georef stage does instead is measure how far apart the two surveys
actually are: the 1904 sheet's ink is correlated against the 1942 sheet's ink
on a lattice over the island, and the scatter of those matches against each
sheet's own georeference is reported in pixels and metres.  That number is
the distance between a 1904 reconnaissance and a 1940 plane-table survey, and
it is stated in the About panel rather than fitted away.

The sea: Terrarium's bathymetry is kept through the mosaic (nothing is
voided over water) and then flattened at zero, so the ocean is exactly flat
and the depth curves you see belong to the 1942 sheet, not the model.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import json, os, sys, urllib.request, zipfile

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('MD_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, ISLANDS

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/ME/'
GNIS = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
        'DomesticNames/DomesticNames_ME_Text.zip')

# The four scans, two cells × two editions.  Neat lines were read back out of
# each GeoTIFF with QuadGeoref corner probes before anything else was done;
# all four agree on 44°15′–44°30′ N and their own 15′ of longitude.
QUADS = [   # the 1904 plates, Lafayette National Park state — the drape
    dict(id='bar1904',  url=S3+'ME_Bar%20Harbor_807360_1904_62500_geo.tif',
         neat=(-68.25, -68.00, 44.25, 44.50), scan='807360'),
    dict(id='mtd1904',  url=S3+'ME_Mount%20Desert_807575_1904_62500_geo.tif',
         neat=(-68.50, -68.25, 44.25, 44.50), scan='807575'),
]
ALTQUADS = [  # the 1942 War Department resurvey — the middle slider stop
    dict(id='bar1942',  url=S3+'ME_Bar%20Harbor_460150_1942_62500_geo.tif',
         neat=(-68.25, -68.00, 44.25, 44.50), scan='460150', pair='bar1904'),
    dict(id='mtd1942',  url=S3+'ME_Mount%20Desert_460635_1942_62500_geo.tif',
         neat=(-68.50, -68.25, 44.25, 44.50), scan='460635', pair='mtd1904'),
]
BLOCK = (-68.50, -68.00, 44.25, 44.50)     # W, E, S, N — the joined neat

LCC = Lcc(44.30, 44.45, -68.25)
MARGIN = 0.0006                            # ~3.8 km of paper around the block
TEX_W, HGT_W, ALT_W = 4096, 2048, 3072
DEM_ZOOM, DEM_BOX = 12, (-68.66, -67.84, 44.09, 44.66)
CLAMP = (-260, 600)                        # keep the Gulf of Maine's real floor…
SEA = 0.0                                  # …then flatten it: the sheet is tidal
PAPER = (240, 228, 198)                    # the table both editions lie on

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]], MARGIN, TEX_W)

def ink(rgb):
    """Local high-pass ink: darker than its 12-px neighbourhood by >30.

    lib/reg.feature_mask goes blind on these plates — the 1904 sheet is brown
    contours under a buff wash and the 1942 sheet is brown contours under an
    olive woodland tint, and neither reads as 'black culture + blue drainage'.
    """
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

# ------------------------------------------------------------------ stage 1
def fetch():
    for q in QUADS + ALTQUADS:
        tif = path(q['id'] + '.tif')
        if not os.path.exists(tif):
            p('· downloading %s (scan %s)…' % (q['id'], q['scan']))
            req = urllib.request.Request(q['url'], headers={'User-Agent': 'old-time-maps/1.0'})
            with urllib.request.urlopen(req, timeout=600) as r, open(tif, 'wb') as f:
                f.write(r.read())
    if not os.path.exists(path('gnis_me.zip')):
        p('· downloading GNIS domestic names (ME)…')
        req = urllib.request.Request(GNIS, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            open(path('gnis_me.zip'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

def georef_of(q):
    """The scan's own embedded polyconic georeference, corner-checked."""
    im = Image.open(path(q['id'] + '.tif'))
    gr = QuadGeoref(im)
    W, E, S, N = q['neat']
    x0, y0 = gr.to_px(W, N); x1, y1 = gr.to_px(E, S)
    if not (0 < x0 < x1 < im.width and 0 < y0 < y1 < im.height):
        raise SystemExit('%s: neat line falls outside the scan' % q['id'])
    return im, gr, (x0, y0, x1, y1)

# ------------------------------------------------------------------ stage 2
def georef():
    """No fitting — both editions carry their own georeference.  What we do
    here is *measure* the two surveys against each other by correlation, so
    the About panel can quote the real disagreement."""
    if os.path.exists(path('fit.json')):
        p('· cross-era measurement cached'); return
    fetch()
    from reg import register, fit_trimmed
    out = {}
    for aq in ALTQUADS:
        oq = next(q for q in QUADS if q['id'] == aq['pair'])
        p('· %s (1942) against %s (1904)…' % (aq['id'], oq['id']))
        aim, agr, abox = georef_of(aq)
        argb = np.asarray(aim.convert('RGB'), dtype=np.uint8); del aim
        af = ink(argb); del argb
        ax0, ay0, ax1, ay1 = abox
        af[:int(ay0)+8, :] = 0; af[int(ay1)-8:, :] = 0
        af[:, :int(ax0)+8] = 0; af[:, int(ax1)-8:] = 0

        oim, ogr, obox = georef_of(oq)
        orgb = np.asarray(oim.convert('RGB'), dtype=np.uint8)
        of = ink(orgb); del orgb
        ox0, oy0, ox1, oy1 = obox
        of[:int(oy0)+8, :] = 0; of[int(oy1)-8:, :] = 0
        of[:, :int(ox0)+8] = 0; of[:, int(ox1)-8:] = 0

        class Seed:                       # LCC → 1942 scan pixels, by its own georef
            def apply(self, X, Y):
                lon, lat = LCC.inv(X, Y)
                return agr.to_px(lon, lat)

        W, E, S, N = oq['neat']
        lons = np.arange(W+0.018, E-0.017, 0.020)
        lats = np.arange(S+0.018, N-0.017, 0.020)
        X, Y, gx, gy, _ = register(
            af, [dict(name=oq['id'], feat=of, to_px=ogr.to_px, m_per_px=ogr.scale[0])],
            LCC, lons, lats, m_scan_hint=agr.scale[0], seed_fit=Seed(),
            pw=110, sw=70, log=p)
        if len(gx) < 12:
            raise SystemExit('%s: too few cross-era matches' % aq['id'])
        px, py = Seed().apply(X, Y)
        d = np.hypot(gx-px, gy-py)
        keep = d < max(8.0, float(np.median(d))*3.0)
        rms = float(np.sqrt((d[keep]**2).mean()))
        p('  %d/%d matches · %.2f px rms · %.0f m rms · median %.0f m' % (
            int(keep.sum()), len(d), rms, rms*agr.scale[0],
            float(np.median(d[keep]))*agr.scale[0]))
        # a degree-1 fit says how much of that is a plain shift/rotation
        fit, fkeep = fit_trimmed(X, Y, gx, gy, 1, name='  %s deg-1' % aq['id'],
                                 floor=4.0, k=2.6, rounds=4, m_per_px=agr.scale[0], log=p)
        out[aq['id']] = dict(n=int(keep.sum()), of=len(d),
                             rms_px=round(rms, 2),
                             rms_m=round(rms*agr.scale[0], 1),
                             med_m=round(float(np.median(d[keep]))*agr.scale[0], 1),
                             resid_px=round(fit.rms, 2),
                             resid_m=round(fit.rms*agr.scale[0], 1),
                             m_per_px=round(agr.scale[0], 3))
        overlay(Image.open(path(aq['id'] + '.tif')),
                {(255, 40, 40): list(zip(gx[keep], gy[keep]))},
                path('qa_georef_%s.png' % aq['id']), 1500)
        del of, af
    json.dump(out, open(path('fit.json'), 'w'))
    p('  QA overlays in work/qa_georef_*.png')

def tone_match(tex, regions, label, log):
    """Pull both cells of a joined block onto one paper white."""
    whites = {k: np.array([np.percentile(tex[:, :, c][m], 92) for c in range(3)])
              for k, m in regions.items() if m.any()}
    target = np.median(np.stack(list(whites.values())), axis=0)
    for k, m in regions.items():
        if k not in whites: continue
        s = np.clip(target/np.maximum(whites[k], 1), 0.90, 1.11)
        log('  %s %s: paper × %s' % (label, k, np.round(s, 3)))
        for c in range(3):
            tex[:, :, c][m] *= s[c]
    return target

def drape_pair(quads, grid, lon27, lat27, inside, label, log):
    """Resample a two-cell edition onto the grid and tone-match the seam."""
    tex = np.zeros((grid.TH, grid.TW, 3), np.float32); tex[:] = PAPER
    regions = {}
    for q in quads:
        W, E, S, N = q['neat']
        inq = inside & (lon27 >= W) & (lon27 <= E) & (lat27 >= S) & (lat27 <= N)
        im, gr, _ = georef_of(q)
        src = np.asarray(im.convert('RGB'), dtype=np.float32); del im
        QX, QY = gr.to_px(lon27[inq], lat27[inq])
        np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
        for c in range(3):
            tex[:, :, c][inq] = ndimage.map_coordinates(
                src[:, :, c], [QY, QX], order=1, mode='nearest')
        del src
        regions[q['id']] = inq
        log('  %s: %d texels' % (q['id'], int(inq.sum())))
    tone_match(tex, regions, label, log)
    tex[~inside] = PAPER          # one table tone under both editions
    return tex

# ------------------------------------------------------------------ stage 3
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    g = make_grid()
    p('· conic grid %d × %d  (%.1f × %.1f km, %.1f m/texel)' % (
        g.TW, g.TH, g.kmw, g.kmh, g.m_per_texel))
    GX, GY, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    p('  raw elevation %.0f – %.0f m' % (hgt.min(), hgt.max()))
    sea = float((hgt < SEA).mean())
    np.maximum(hgt, SEA, out=hgt)          # a flat Atlantic; see the docstring
    p('  %.0f%% of the grid is sea, flattened at %g m; land to %.0f m' % (
        100*sea, SEA, hgt.max()))
    np.save(path('hgt.npy'), hgt)

    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    inside = ((lon27 >= BLOCK[0]) & (lon27 <= BLOCK[1]) &
              (lat27 >= BLOCK[2]) & (lat27 <= BLOCK[3]))
    np.save(path('mask.npy'), inside)

    p('· resampling the 1904 plates…')
    tex = drape_pair(QUADS, g, lon27, lat27, inside, '1904', p)
    np.save(path('drape.npy'), np.clip(tex, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
         .resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))
    del tex

    p('· resampling the 1942 resurvey…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    in2 = ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) &
           (la2 >= BLOCK[2]) & (la2 <= BLOCK[3]))
    alt = drape_pair(ALTQUADS, g2, lo2, la2, in2, '1942', p)
    np.save(path('alt.npy'), np.clip(alt, 0, 255).astype(np.uint8))
    Image.fromarray(np.clip(alt, 0, 255).astype(np.uint8)) \
         .resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def islands(g):
    """The archipelago: the named islands of the block, keyed by GNIS id.

    Four separate islands in this one block are called "Bar Island", so the
    table in places.py carries feature_ids; the coordinates and the names both
    come out of the federal file, and a mismatch against the table is shouted
    about rather than shipped.
    """
    z = zipfile.ZipFile(path('gnis_me.zip'))
    f = z.open('Text/DomesticNames_ME.txt')
    hdr = f.readline().decode('utf-8-sig').strip().split('|')
    ix = {k: hdr.index(k) for k in ('feature_id', 'feature_name', 'feature_class',
                                    'prim_lat_dec', 'prim_long_dec')}
    out, seen = [], set()
    for ln in f:
        c = ln.decode('utf-8', 'replace').split('|')
        if c[ix['feature_class']] != 'Island': continue
        try:
            fid = int(c[ix['feature_id']])
        except ValueError:
            continue
        if fid not in ISLANDS or fid in seen: continue
        name = c[ix['feature_name']].strip()
        if name != ISLANDS[fid]:
            p('  ! GNIS %d is "%s", the table says "%s"' % (fid, name, ISLANDS[fid]))
        lat = float(c[ix['prim_lat_dec']]); lon = float(c[ix['prim_long_dec']])
        if not (BLOCK[0] <= lon <= BLOCK[1] and BLOCK[2] <= lat <= BLOCK[3]):
            p('  ! %s (%d) falls outside the block' % (name, fid)); continue
        u, v = g.uv(lon, lat)
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        seen.add(fid)
        out.append(dict(n=name[:26], u=round(u, 5), v=round(v, 5), c='island'))
    missing = set(ISLANDS) - seen
    if missing:
        p('  ! not found in GNIS in-block: %s' % ', '.join(
            '%s (%d)' % (ISLANDS[i], i) for i in sorted(missing)))
    out.sort(key=lambda m: m['n'])
    return out

def snap_summits(g, hgt, peaks, radius_m=200, log=print):
    """Peak labels snapped to the local summit — with a tight hunt radius.

    lib/encode.snap_places walks 1,500 m looking for the local maximum, which
    is right on a Montana sheet and wrong here: Dorr stands 800 m from
    Cadillac and Huguenot Head 900 m from Champlain, so the wide hunt piles
    four labels onto two summits.  Radius cut to 200 m, and then the gate the
    house rules ask for: each printed elevation is checked against the model
    and anything more than 130 m out is dropped, never guessed.
    """
    TH, TW = hgt.shape
    r = max(1, int(radius_m/g.m_per_texel))
    out = []
    for n, la, lo, ft, rng in peaks:
        u, v = g.uv(lo, la)
        x = min(max(int(round(u*TW)), 0), TW-1); y = min(max(int(round(v*TH)), 0), TH-1)
        w = hgt[max(0, y-r):y+r+1, max(0, x-r):x+r+1]
        j = np.unravel_index(np.argmax(w), w.shape)
        e = float(w[j])
        d = e - ft*0.3048
        if abs(d) > 130:
            log('  ! %s: model %.0f ft vs printed %d ft — dropped' % (n, e/0.3048, ft))
            continue
        log('    %-24s %5d ft printed · model %5.0f ft · %+5.0f m' % (n, ft, e/0.3048, d))
        out.append(dict(n=n, u=round((max(0, x-r)+j[1])/TW, 5),
                        v=round((max(0, y-r)+j[0])/TH, 5),
                        ft=ft, r=rng, lat=la, lon=lo))
    log('  %d/%d summits kept (hunt radius %.0f m)' % (len(out), len(peaks), r*g.m_per_texel))
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
    p('· encoding the 1942 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    # the house checker still runs over the peaks (it must stay silent); its
    # peak records are then replaced by the tight-radius snap below
    _, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)
    p('· checking the summits against the model…')
    peaks = snap_summits(g, hgt, PEAKS, log=p)

    ramp = [[233, 224, 202], [225, 216, 192], [215, 206, 180], [205, 196, 168],
            [196, 185, 156], [190, 175, 145], [186, 165, 134], [181, 154, 123],
            [174, 143, 112], [166, 133, 103], [158, 125, 97], [153, 121, 96],
            [158, 129, 107], [170, 145, 126], [185, 165, 149]]
    ramp_ft = [1 + 110*i for i in range(len(ramp))]    # sea level to ~1,540 ft

    p('· gathering the archipelago…')
    ISL = islands(g)
    p('  %d islands kept' % len(ISL))

    fits = json.load(open(path('fit.json')))
    worst = max(fits.values(), key=lambda d: d['rms_px'])
    best = min(fits.values(), key=lambda d: d['rms_px'])
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=ISL,
               ui=dict(exagDef=3.0, exagMax=6.0, contourM=6.096, mineDist=0.42,
                       mineGlyph='⚓', rampLo=1, rampHi=1540,
                       sheetA='1904 sheets', altName='1942 resurvey',
                       tourEx=[1.5, 0.02, 1.6, 3.2]),
               fit=dict(method='passthrough — every layer rides its own '
                               'GeoTIFF georeference; the numbers below are the '
                               'measured disagreement between the 1904 and 1942 '
                               'surveys, not a fit residual',
                        rms=worst['rms_px'], rms_px_lo=best['rms_px'],
                        rms_m=worst['rms_m'], rms_m_lo=best['rms_m'],
                        median=round(max(d['med_m'] for d in fits.values()), 1),
                        n=sum(d['n'] for d in fits.values()),
                        per_cell=fits))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
