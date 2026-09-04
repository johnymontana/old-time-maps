#!/usr/bin/env python3
"""The Stony Man Quadrangle — asset pipeline.

Forty-four years of the Blue Ridge, in two printings of one fifteen-minute
block: 38°30′–38°45′ N by 78°15′–78°30′ W, the southwest quarter of the USGS
**LURAY SHEET**.

    drape  — the Luray sheet, Virginia, 1:125,000, surveyed 1884–86 by
             W. T. Griswold under Gilbert Thompson, edition of May 1893
             reprinted October 1898, J. W. Powell still Director.  100-foot
             contours; the later printings of this same engraving carry the
             admission *Surveyed by reconnaissance methods*.
    alt    — STONY MAN, VA., 1:62,500, resurveyed 1927–29 by Hersey Munroe,
             Fred Graff Jr., K. W. Trimble, W. K. McKinley, H. B. Smith and
             F. W. Cook for the Virginia Conservation Commission, edition of
             1933 reprinted 1944.  Contours at 20 and 50 feet, Skyline Drive
             in red along the crest, and the Shenandoah National Park
             boundary drawn as a hatched red band.
    data   — every place inside the neat that GNIS marks *(historical)*:
             schools, churches, stores, ferries, a post office, and the
             hamlet of Old Rag.

Both files are Historical Topographic Map Collection GeoTIFFs carrying their
own polyconic / NAD27 georeference, so **nothing here is fitted**.  The
`georef` stage is a verification stage instead: it probes the printed neat
corners through each transform, then measures — without applying — how far
the 1884–86 reconnaissance puts the country from the 1927–29 resurvey, by
correlating patches of the later sheet into the older one at the positions
the older sheet's own geokeys predict.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py encode     # this stage and after

Stages: fetch, georef, resample, encode.
"""
import json, os, sys, urllib.parse, urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
WORK = os.environ.get('LU_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, GNIS_NAME

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/VA/'
# The frozen 2021 GNIS archive: it still carries ELEV_IN_FT, and places.py is
# audited against this very file at encode time so no coordinate is ever
# remembered rather than read.
GNIS2021 = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
            'Archive/MainDomestic/VA_Features_20210825.txt')
SHEETS = [
    dict(id='luray1893', name='1893 Luray sheet',
         url=S3 + 'VA_Luray_189048_1893_125000_geo.tif'),
    dict(id='stonyman1933', name='1933 Stony Man sheet',
         url=S3 + urllib.parse.quote('VA_Stony Man_188599_1933_62500_geo.tif')),
]
NEAT = (-78.5, -78.25, 38.5, 38.75)   # the Stony Man 15′ graticule box (NAD27)
BLOCK = NEAT

LCC = Lcc(38.55, 38.70, -78.375)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 2560, 1707, 2560
DEM_ZOOM, DEM_BOX = 13, (-78.66, -78.09, 38.36, 38.89)
CLAMP = (40, 1400)                    # Shenandoah River ~170 m to Hawksbill 1,228 m
PAPER = (252, 228, 165)               # the 1893 sheet's tan stock, measured
ALT_PAPER = (250, 247, 216)           # the 1944 printing's cream stock, measured

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]],
                       MARGIN, TEX_W)

def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its 12-px
    neighbourhood.  Both sheets print their relief in brown — the 1893 under
    no wash, the 1944 under a red road and boundary overprint — and lib/reg's
    black+blue mask goes blind on both; this does not."""
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
    if not os.path.exists(path('gnis_va_2021.txt')):
        p('· downloading GNIS 2021 archive (VA — it still carries elevations)…')
        req = urllib.request.Request(GNIS2021, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=600) as r:
            open(path('gnis_va_2021.txt'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Read both embedded georeferences; verify, do not fit.

    Check 1 — the printed neat.  The four corners of the fifteen-minute block
    are pushed through each scan's own geokeys and reported in scan pixels;
    both sheets must put the block wholly inside their map body.

    Check 2 — agreement.  Patches of the 1933 resurvey are correlated into
    the 1893 scan at the positions the 1893 geokeys predict on their own.
    The residual is *measured and printed*; it is never applied to anything.
    It is the honest size of the difference between a reconnaissance survey
    of 1884–86 and a plane-table resurvey of 1927–29 over the same ridge.
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
        p('· %-14s %d × %d px, %.4f m/px, polyconic lon0 %.3f lat0 %.3f (%s)'
          % (s['id'], im.width, im.height, qr.scale[0], qr.lon0, qr.lat0, qr.datum))
        p('    neat NW %s  NE %s  SW %s  SE %s'
          % (corners['NW'], corners['NE'], corners['SW'], corners['SE']))
        p('    15′ of longitude = %.1f px = %.2f km' % (wpx, wpx*qr.scale[0]/1e3))
        out['sheets'][s['id']] = dict(px=[im.width, im.height],
                                      m_per_px=round(float(qr.scale[0]), 4),
                                      lon0=qr.lon0, lat0=qr.lat0, datum=qr.datum,
                                      corners=corners)
        im.close()

    # --- check 2: how far apart do the two embedded transforms place things?
    from reg import register
    p('· measuring the 1884–86 reconnaissance against the 1927–29 resurvey…')
    oim, oqr = scan(SHEETS[0])                       # 1893, the scan being probed
    of = ink(np.asarray(oim.convert('RGB'), dtype=np.uint8)); oim.close()
    ox0, oy0 = oqr.to_px(W, N); ox1, oy1 = oqr.to_px(E, S)   # blank the collar
    of[:max(0, int(oy0)-40), :] = 0; of[int(oy1)+40:, :] = 0
    of[:, :max(0, int(ox0)-40)] = 0; of[:, int(ox1)+40:] = 0
    nim, nqr = scan(SHEETS[1])                       # 1933/44, the patch source
    nf = ink(np.asarray(nim.convert('RGB'), dtype=np.uint8)); nim.close()

    class Passthrough:
        """The 1893 sheet's own geokeys, in the shape register() wants."""
        def apply(self, X, Y):
            lo, la = LCC.inv(X, Y)
            return oqr.to_px(lo, la)

    lons = np.arange(W+0.014, E-0.013, 0.014)
    lats = np.arange(S+0.014, N-0.013, 0.014)
    X, Y, gx, gy, _ = register(of, [dict(name='stonyman1933', feat=nf,
                                         to_px=nqr.to_px,
                                         m_per_px=float(nqr.scale[0]))],
                               LCC, lons, lats, m_scan_hint=float(oqr.scale[0]),
                               seed_fit=Passthrough(), pw=140, sw=110, log=p)
    agree = None
    if len(gx) >= 20:
        sx, sy = Passthrough().apply(X, Y)
        d = np.hypot(gx-sx, gy-sy)
        keep = d < max(10.0, float(np.median(d))*3.0)   # drop contour-lock outliers
        dk = d[keep]
        mpp = float(oqr.scale[0])
        # is the disagreement a shift or a scatter?  Split it: the median
        # offset vector is what the whole sheet is out by, the residual about
        # that vector is how much the reconnaissance wandered locally.
        ex = float(np.median((gx-sx)[keep]))*mpp      # + = 1893 ink lies east
        ny = -float(np.median((gy-sy)[keep]))*mpp     # + = 1893 ink lies north
        about = np.hypot((gx-sx)[keep]*mpp - ex, (gy-sy)[keep]*mpp + ny)
        agree = dict(n=int(keep.sum()), tried=int(len(gx)),
                     rms=round(float(np.sqrt((dk*dk).mean())), 2),
                     median=round(float(np.median(dk)), 2),
                     worst=round(float(dk.max()), 2),
                     m_per_px=round(mpp, 3),
                     median_m=round(float(np.median(dk))*mpp, 1),
                     rms_m=round(float(np.sqrt((dk*dk).mean()))*mpp, 1),
                     shift_e_m=round(ex, 1), shift_n_m=round(ny, 1),
                     shift_m=round(float(np.hypot(ex, ny)), 1),
                     scatter_m=round(float(np.median(about)), 1))
        p('  the 1893 engraving sits %.2f px from the 1933 resurvey at the median,'
          ' %.2f px rms (%d of %d points) — %.0f m on the ground, nothing adjusted'
          % (agree['median'], agree['rms'], agree['n'], len(gx), agree['median_m']))
        p('  of which %.0f m is one shift (%.0f m east, %.0f m north) and %.0f m'
          ' is local wander about it'
          % (agree['shift_m'], ex, ny, agree['scatter_m']))
        im = Image.open(path('luray1893.tif'))
        overlay(im, {(220, 30, 30): list(zip(gx[keep], gy[keep])),
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

def lay(sheet, grid, lon27, lat27, inside, paper, label):
    """Resample one self-georeferenced sheet onto the grid through its own
    geokeys.  Sources finer than the grid are pre-blurred before sampling, so
    a 1:62,500 engraving does not alias into speckle on the way down."""
    im, qr = scan(sheet)
    src = np.asarray(im.convert('RGB'), dtype=np.float32); im.close()
    tone(src, label, p)
    ratio = grid.m_per_texel/float(qr.scale[0])
    if ratio > 1.5:
        p('  pre-blurring %.2f× (σ %.2f source px) before the downsample'
          % (ratio, 0.5*ratio))
        for c in range(3):
            src[:, :, c] = ndimage.gaussian_filter(src[:, :, c], 0.5*ratio)
    QX, QY = qr.to_px(lon27[inside], lat27[inside])
    np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
    tex = np.zeros((grid.TH, grid.TW, 3), np.float32); tex[:] = paper
    for c in range(3):
        tex[:, :, c][inside] = ndimage.map_coordinates(
            src[:, :, c], [QY, QX], order=1, mode='nearest')
    del src, QX, QY
    return np.clip(tex, 0, 255).astype(np.uint8)

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

    p('· resampling the 1893 Luray sheet…')
    tex = lay(SHEETS[0], g, lon27, lat27, inside, PAPER, '1893 Luray sheet')
    np.save(path('drape.npy'), tex)
    Image.fromarray(tex).resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))
    del tex

    p('· resampling the 1933 Stony Man sheet…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    ok2 = ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) &
           (la2 >= BLOCK[2]) & (la2 <= BLOCK[3]))
    alt = lay(SHEETS[1], g2, lo2, la2, ok2, ALT_PAPER, '1933 Stony Man sheet')
    np.save(path('alt.npy'), alt)
    Image.fromarray(alt).resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def gnis_rows():
    """Every GNIS 2021 record whose point falls inside the printed neat."""
    rows = []
    with open(path('gnis_va_2021.txt'), encoding='utf-8-sig') as f:
        hdr = f.readline().rstrip('\n').split('|')
        ix = {k: hdr.index(k) for k in ('FEATURE_NAME', 'FEATURE_CLASS',
                                        'PRIM_LAT_DEC', 'PRIM_LONG_DEC',
                                        'ELEV_IN_FT')}
        for ln in f:
            c = ln.rstrip('\n').split('|')
            try:
                la = float(c[ix['PRIM_LAT_DEC']]); lo = float(c[ix['PRIM_LONG_DEC']])
            except ValueError:
                continue
            if not (BLOCK[0] <= lo <= BLOCK[1] and BLOCK[2] <= la <= BLOCK[3]):
                continue
            try: ft = int(c[ix['ELEV_IN_FT']])
            except ValueError: ft = None
            rows.append((c[ix['FEATURE_NAME']].strip(), c[ix['FEATURE_CLASS']],
                         la, lo, ft))
    return rows

def audit_places():
    """Every summit and town in places.py must be a GNIS record, to the digit.

    Memory once put Electric Peak 13 km wrong on another sheet; this makes the
    rule machine-checked instead of promised.  Keyed on feature class as well
    as name, because 'Big Meadows' is a populated place, a flat and a wayside
    all at once."""
    want = {}                                  # (gnis name, classes) -> expected
    for n, la, lo, ft, _ in PEAKS:
        want[(GNIS_NAME.get(n, n), ('Summit',))] = (n, la, lo, ft)
    for n, la, lo, _ in CITIES:
        want[(GNIS_NAME.get(n, n), ('Populated Place', 'Locale'))] = (n, la, lo, None)
    found = {}
    for nm, fc, la, lo, ft in gnis_rows():
        for key in want:
            if key[0] != nm or fc not in key[1] or key in found: continue
            found[key] = (la, lo, ft)
    bad = []
    for key, (n, la, lo, ft) in want.items():
        gg = found.get(key)
        if gg is None:
            bad.append('%s: no GNIS %s record in the block' % (key[0], '/'.join(key[1])))
            continue
        if abs(gg[0]-la) > 2e-5 or abs(gg[1]-lo) > 2e-5:
            bad.append('%s: GNIS has %.5f %.5f, places.py has %.5f %.5f'
                       % (n, gg[0], gg[1], la, lo))
        if ft is not None and gg[2] is not None and ft != gg[2]:
            bad.append('%s: GNIS has %d ft, places.py has %d ft' % (n, gg[2], ft))
    if bad:
        for b in bad: p('  ! ' + b)
        raise SystemExit('places.py disagrees with GNIS — fix it, do not guess')
    p('  %d summits and towns audited against GNIS: all exact' % len(want))

def verify_summits(g, hgt):
    """Each summit must stand up in the model where GNIS puts it.

    Two ways a peak can be wrong and one of them is invisible: a bad elevation
    (caught at ±130 m of its GNIS feet) and a bad *position* — `snap_places`
    hunts the local maximum in a ±1.5 km window, so a peak with a taller
    neighbour inside that window silently borrows its neighbour's summit.
    Anything that walks more than 700 m is not this peak; drop it rather than
    mislabel a mountain."""
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
    p('  %d summits verified against the model (worst %.0f m of their GNIS feet)'
      % (len(PEAKS), worst))

def vanished(g):
    """The data layer: every place inside the neat that GNIS marks *(historical)*.

    GNIS keeps the record and appends that word when the thing itself is no
    longer there.  Inside this fifteen-minute block that is twenty schools,
    five churches, three Shenandoah ferries, two stores, two trail shelters,
    a post office at Skyland, Aaron Nicholson's house in the hollow that bore
    his family's name, and the hamlet of Old Rag.  Some of them closed when
    Page County consolidated its schools; the ones up on the ridge closed
    because the people were condemned out from under them between 1935 and
    1938.  No editorial selection: the filter is the parenthesis."""
    out = []
    for nm, fc, la, lo, ft in gnis_rows():
        if '(historical)' not in nm: continue
        u, v = g.uv(lo, la)
        if not (0.005 < u < 0.995 and 0.005 < v < 0.995): continue
        out.append(dict(n=nm.replace(' (historical)', '')[:26],
                        u=round(float(u), 5), v=round(float(v), 5), ft=ft or 0))
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
    p('· encoding the 1933 Stony Man layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))

    p('· auditing places against GNIS and the model…')
    audit_places()
    verify_summits(g, hgt)
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)
    p('  on-sheet relief %.0f – %.0f m (grid %.0f – %.0f m)'
      % (hgt[mask].min(), hgt[mask].max(), hmin, hmax))

    p('· gathering the places GNIS marks (historical)…')
    V = vanished(g)
    p('  %d vanished places kept' % len(V))

    # the sheets' own inks: the 1893 tan stock, its brown contours, and the
    # grey-green the hardwood ridge reads as under them
    ramp = [[247, 231, 190], [242, 225, 182], [237, 218, 173], [232, 211, 164],
            [227, 203, 154], [221, 195, 145], [215, 186, 136], [208, 177, 128],
            [200, 167, 120], [191, 157, 113], [181, 147, 108], [171, 138, 105],
            [162, 132, 105], [156, 130, 110], [154, 132, 118]]
    ramp_ft = [520 + 255*i for i in range(len(ramp))]

    gj = json.load(open(path('georef.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=V,
               ui=dict(exagDef=2.0, exagMax=6.0, contourM=30.48,
                       rampLo=520, rampHi=4090, mineDist=0.46, mineGlyph='⌂',
                       sheetA='1893 Luray sheet', altName='1933 park survey',
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
