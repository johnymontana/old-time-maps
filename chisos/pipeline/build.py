#!/usr/bin/env python3
"""The Big Bend — asset pipeline.

Two 1903 quadrangles of the Rio Grande's great bend, joined at 103°30′ —
**TERLINGUA** (30′, surveyed 1902–03 in cooperation with the University of
Texas Mineral Survey) and **CHISOS MOUNTAINS** (a non-standard 45′ × 30′
sheet, surveyed 1903) — both 1:125,000, both drawn by Arthur Stiles and
J. E. Blackburn under E. M. Douglas, and between them nearly the whole of
the national park that would not exist until 1944.  They drape over
Terrarium elevations, with the **1985 Chisos Mountains** and **1984
Boquillas** 1:100,000 metric sheets one slider-stop behind: the same
country after the park, the roads and the aerial photograph.

Nothing here is fitted.  All four scans are HTMC GeoTIFFs carrying their
own georeference — the 1903 pair polyconic on NAD27, the 1980s pair
transverse Mercator on NAD27 (`TmGeoref` below reads their geokeys, since
lib/georef's QuadGeoref accepts polyconic only).  The `georef` stage is a
verification stage: it pushes the printed neatline corners through every
embedded transform, then *measures without applying* how far apart a 1903
plane-table survey and a 1980s photogrammetric compilation put the same
ground.

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
WORK = os.environ.get('CH_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27, _marc
from georef import QuadGeoref, _geokeys, overlay
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, LABEL_ONLY, GNIS_NAME

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/TX/'
# The live GNIS product dropped elevations (and the Mine class); the frozen
# 2021 archive still carries both, and every coordinate and foot in places.py
# is audited against it at encode time.  Never from memory.
GNIS2021 = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/GeographicNames/'
            'Archive/MainDomestic/TX_Features_20210825.txt')

BLOCK = (-104.0, -102.75, 29.0, 29.5)      # 104°W–102°45′W × 29°–29°30′N

QUADS = [  # the drape: two 1903 sheets, polyconic, joined at 103°30′
    dict(id='terlingua1903', name='Terlingua 1903',
         url=S3 + 'TX_Terlingua_121887_1903_125000_geo.tif',
         neat=(-104.0, -103.5, 29.0, 29.5)),
    dict(id='chisos1903', name='Chisos Mountains 1903',
         url=S3 + 'TX_Chisos%20Mountains_108199_1903_125000_geo.tif',
         neat=(-103.5, -102.75, 29.0, 29.5)),
]
ALTS = [   # the middle layer: the 100k metric pair, transverse Mercator
    dict(id='chisos1985', name='Chisos Mountains 1985',
         url=S3 + 'TX_Chisos%20Mountains_122109_1985_100000_geo.tif',
         neat=(-104.0, -103.0, 29.0, 29.5)),
    dict(id='boquillas1984', name='Boquillas 1984',
         url=S3 + 'TX_Boquillas_121986_1984_100000_geo.tif',
         neat=(-103.0, -102.75, 29.0, 29.5)),   # clipped to the block's east
]

LCC = Lcc(29.1, 29.4, -103.375)
MARGIN = 0.0012
TEX_W, HGT_W, ALT_W = 4096, 2560, 3072
DEM_ZOOM, DEM_BOX = 12, (-104.16, -102.59, 28.84, 29.66)
CLAMP = (450, 2700)                        # measured: 496 – 2,355 m on the grid
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]],
                       MARGIN, TEX_W)

def ink(rgb):
    """Linework as a local high-pass: anything markedly darker than its 12-px
    neighbourhood.  Both printings carry their relief in brown — the 1903
    sheets under a cream wash, the 1980s sheets under green woodland tint and
    red road casings — and lib/reg's black+blue mask goes blind on both."""
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

# ------------------------------------------------- transverse Mercator scans
class TmGeoref:
    """Embedded georeference of a 1:100,000 metric scan (TM / NAD27).

    The 1980s sheets are printed on UTM zone 13 but topoView stages them
    re-projected to a local transverse Mercator (central meridian on the
    sheet, k0 = 1, no false origin), which QuadGeoref refuses.  Same idea as
    QuadGeoref: read ModelPixelScale + ModelTiepoint + the projection
    geokeys, then Snyder's forward TM series (8-1…8-5) for lon/lat → pixel.
    Verified by round-trip against lib/proj.tm_inverse (1e-11°) and by the
    printed neatline: 1° of longitude measures 96.98 km at 29°15′.
    """
    def __init__(self, pil_image):
        t = pil_image.tag_v2
        sx, sy = t[33550][0], t[33550][1]
        _, _, _, gx, gy, _ = t[33922]
        self.scale, self.origin = (sx, sy), (gx, gy)
        k = _geokeys(t)
        if k.get(1024) != 1 or k.get(3075) != 1:
            raise ValueError('expected a projected transverse Mercator '
                             'GeoTIFF, got keys %r' % k)
        self.lon0, self.lat0 = float(k[3080]), float(k[3081])
        self.k0 = float(k.get(3092, 1.0))
        self.fe, self.fn = float(k.get(3082, 0.0)), float(k.get(3083, 0.0))
        self.a, self.invf = float(k[2057]), float(k[2059])
        self.datum = k.get(2049, 'NAD27')

    def fwd(self, lon, lat):
        f = 1.0/self.invf; e2 = 2*f - f*f; ep2 = e2/(1-e2); a = self.a
        phi = np.radians(np.asarray(lat, float))
        lam = np.radians(np.asarray(lon, float) - self.lon0)
        sp, cp = np.sin(phi), np.cos(phi)
        N = a/np.sqrt(1 - e2*sp*sp)
        T = np.tan(phi)**2; C = ep2*cp*cp; A = lam*cp
        M = _marc(phi, a, e2); M0 = _marc(math.radians(self.lat0), a, e2)
        x = self.k0*N*(A + (1-T+C)*A**3/6
                       + (5-18*T+T*T+72*C-58*ep2)*A**5/120)
        y = self.k0*(M - M0 + N*np.tan(phi)*(
            A*A/2 + (5-T+9*C+4*C*C)*A**4/24
            + (61-58*T+T*T+600*C-330*ep2)*A**6/720))
        return x + self.fe, y + self.fn

    def to_px(self, lon, lat):
        x, y = self.fwd(lon, lat)
        return ((x - self.origin[0])/self.scale[0],
                (self.origin[1] - y)/self.scale[1])

def scan(sheet):
    """(PIL image, georeference) for one sheet, opened lazily from work/."""
    im = Image.open(path(sheet['id'] + '.tif'))
    G = TmGeoref if sheet in ALTS else QuadGeoref
    return im, G(im)

# ------------------------------------------------------------------ stage 1
def fetch():
    for s in QUADS + ALTS:
        tif = path(s['id'] + '.tif')
        if not os.path.exists(tif):
            p('· downloading the %s sheet…' % s['name'])
            req = urllib.request.Request(s['url'],
                                         headers={'User-Agent': 'old-time-maps/1.0'})
            with urllib.request.urlopen(req, timeout=600) as r, open(tif, 'wb') as f:
                f.write(r.read())
    if not os.path.exists(path('gnis_tx_2021.txt')):
        p('· downloading GNIS 2021 archive (TX — it still carries elevations)…')
        req = urllib.request.Request(GNIS2021, headers={'User-Agent': 'old-time-maps/1.0'})
        with urllib.request.urlopen(req, timeout=900) as r:
            open(path('gnis_tx_2021.txt'), 'wb').write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """Read four embedded georeferences; verify, do not fit.

    Check 1 — the printed neat.  The graticule box each sheet contributes to
    the block (for Boquillas, the 15′ of it that the block reaches) is pushed
    through that sheet's own geokeys and reported in scan pixels; it must
    fall wholly inside the map body, and its longitude span must measure the
    right number of kilometres.

    Check 2 — agreement across eighty-two years.  Patches of the 1903
    engraving are correlated into the 1985 metric sheet at the positions the
    1985 geokeys predict on their own.  The residual is measured and
    printed; it is never applied to anything.
    """
    if os.path.exists(path('georef.json')):
        p('· georeference cached'); return
    fetch()
    out = dict(block=list(BLOCK), sheets={})
    for s in QUADS + ALTS:
        im, gr = scan(s)
        W, E, S, N = s['neat']
        corners = {}
        for tag, (lo, la) in dict(NW=(W, N), NE=(E, N), SW=(W, S), SE=(E, S)).items():
            x, y = gr.to_px(lo, la)
            corners[tag] = [round(float(x), 1), round(float(y), 1)]
            assert 0 < x < im.width and 0 < y < im.height, \
                '%s: neat corner %s falls off the scan' % (s['id'], tag)
        wpx = corners['NE'][0] - corners['NW'][0]
        kind = 'transverse Mercator' if s in ALTS else 'polyconic'
        p('· %-14s %5d × %5d px, %.4f m/px, %s lon0 %.2f (%s)'
          % (s['id'], im.width, im.height, gr.scale[0], kind, gr.lon0, gr.datum))
        p('    neat NW %s  NE %s  SW %s  SE %s'
          % (corners['NW'], corners['NE'], corners['SW'], corners['SE']))
        p('    %.0f′ of longitude = %.1f px = %.2f km'
          % ((E-W)*60, wpx, wpx*gr.scale[0]/1e3))
        out['sheets'][s['id']] = dict(px=[im.width, im.height],
                                      m_per_px=round(float(gr.scale[0]), 4),
                                      projection=kind, lon0=gr.lon0,
                                      datum=gr.datum, corners=corners)
        im.close()

    # --- check 2: 1903 plane table against 1985 photogrammetry
    from reg import register
    p('· measuring the 1903 sheets against the 1985 metric sheet…')
    aim, agr = scan(ALTS[0])
    af = ink(np.asarray(aim.convert('RGB'), dtype=np.uint8)); aim.close()
    targets = []
    for q in QUADS:                            # both 1903 sheets as targets
        W, E, S, N = q['neat']
        if E > ALTS[0]['neat'][1]:             # only where the 1985 sheet reaches
            E = ALTS[0]['neat'][1]
        if E - W < 0.05: continue
        qim, qr = scan(q)
        qf = ink(np.asarray(qim.convert('RGB'), dtype=np.uint8)); qim.close()
        qx0, qy0 = qr.to_px(W, N); qx1, qy1 = qr.to_px(E, S)
        qf[:int(qy0)+8, :] = 0; qf[int(qy1)-8:, :] = 0
        qf[:, :int(qx0)+8] = 0; qf[:, int(qx1)-8:] = 0
        targets.append(dict(name=q['id'], feat=qf, to_px=qr.to_px,
                            m_per_px=float(qr.scale[0])))

    class Passthrough:
        """The 1985 sheet's own geokeys, in the shape register() wants."""
        def apply(self, X, Y):
            lo, la = LCC.inv(X, Y)
            return agr.to_px(lo, la)

    lons = np.arange(-103.95, -103.04, 0.045)
    lats = np.arange(29.05, 29.46, 0.045)
    X, Y, gx, gy, _ = register(af, targets, LCC, lons, lats,
                               m_scan_hint=float(agr.scale[0]),
                               seed_fit=Passthrough(), pw=150, sw=70, log=p)
    agree = None
    if len(gx) >= 20:
        sx, sy = Passthrough().apply(X, Y)
        d = np.hypot(gx-sx, gy-sy)
        keep = d < max(8.0, float(np.median(d))*3.0)   # drop contour-lock outliers
        d = d[keep]
        mpp = float(agr.scale[0])
        agree = dict(n=int(keep.sum()),
                     rms=round(float(np.sqrt((d*d).mean())), 2),
                     median=round(float(np.median(d)), 2),
                     worst=round(float(d.max()), 2),
                     m_per_px=round(mpp, 3),
                     median_m=round(float(np.median(d))*mpp, 1),
                     rms_m=round(float(np.sqrt((d*d).mean()))*mpp, 1))
        p('  the 1903 and 1985 georeferences agree to %.2f px median, %.2f px'
          ' rms (%d of %d points) — %.0f m on the ground, nothing adjusted'
          % (agree['median'], agree['rms'], agree['n'], len(gx), agree['median_m']))
        im = Image.open(path(ALTS[0]['id'] + '.tif'))
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

def tone_match(tex, regions, label, log):
    """Bring two printings to a common paper white at their seam."""
    whites = {k: np.array([np.percentile(tex[:, :, c][m], 92) for c in range(3)])
              for k, m in regions.items() if m.any()}
    target = np.median(np.stack(list(whites.values())), axis=0)
    for k, m in regions.items():
        if k not in whites: continue
        s = np.clip(target/np.maximum(whites[k], 1), 0.90, 1.11)
        log('  %s %s: paper × %s' % (label, k, np.round(s, 3)))
        for c in range(3):
            tex[:, :, c][m] *= s[c]

def lay(grid, sheets, label):
    """Resample a set of self-georeferenced sheets onto one grid."""
    _, _, LON, LAT = grid.lonlat()
    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    inside = ((lon27 >= BLOCK[0]) & (lon27 <= BLOCK[1]) &
              (lat27 >= BLOCK[2]) & (lat27 <= BLOCK[3]))
    tex = np.zeros((grid.TH, grid.TW, 3), np.float32); tex[:] = PAPER
    regions = {}
    for s in sheets:
        W, E, S, N = s['neat']
        inq = inside & (lon27 >= W) & (lon27 <= E) & (lat27 >= S) & (lat27 <= N)
        im, gr = scan(s)
        src = np.asarray(im.convert('RGB'))          # uint8: the 100k scans
        im.close()                                   # are 13k × 7k px
        QX, QY = gr.to_px(lon27[inq], lat27[inq])
        np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
        for c in range(3):
            tex[:, :, c][inq] = ndimage.map_coordinates(
                src[:, :, c], [QY, QX], order=1, mode='nearest',
                output=np.float32)
        del src, QX, QY
        regions[s['id']] = inq
        p('  %-14s %8d texels' % (s['id'], int(inq.sum())))
    tone_match(tex, regions, label, p)
    return np.clip(tex, 0, 255).astype(np.uint8), inside

# ------------------------------------------------------------------ stage 3
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    g = make_grid()
    p('· conic grid %d × %d  (%.1f × %.1f km, %.1f m per texel)'
      % (g.TW, g.TH, g.kmw, g.kmh, g.m_per_texel))
    _, _, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    p('  elevation %.0f – %.0f m  (%.0f – %.0f ft)'
      % (hgt.min(), hgt.max(), hgt.min()/0.3048, hgt.max()/0.3048))
    np.save(path('hgt.npy'), hgt)

    p('· resampling the 1903 sheets…')
    tex, inside = lay(g, QUADS, 'sheet')
    np.save(path('mask.npy'), inside)
    p('  block covers %.1f%% of the grid' % (100.0*inside.mean()))
    hin = hgt[inside]
    p('  on the block: %.0f – %.0f m  (%.0f – %.0f ft)'
      % (hin.min(), hin.max(), hin.min()/0.3048, hin.max()/0.3048))
    np.save(path('drape.npy'), tex)
    Image.fromarray(tex).resize((g.TW//3, g.TH//3)).save(path('qa_drape.png'))
    del tex

    p('· resampling the 1984–85 metric sheets…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    alt, _ = lay(g2, ALTS, 'metric')
    np.save(path('alt.npy'), alt)
    Image.fromarray(alt).resize((g2.TW//3, g2.TH//3)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

# ------------------------------------------------------------------ stage 4
def gnis_rows():
    """The frozen 2021 GNIS file as (name, class) -> (lat, lon, ft) in-block."""
    rows = {}
    with open(path('gnis_tx_2021.txt'), encoding='utf-8-sig') as f:
        hdr = f.readline().strip().split('|')
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
            key = (c[ix['FEATURE_NAME']].strip(), c[ix['FEATURE_CLASS']].strip())
            rows.setdefault(key, (la, lo, ft))
    return rows

def audit_places():
    """Every summit, town and feature in places.py must be a GNIS record.

    Memory once put Electric Peak 13 km wrong on another sheet; this makes
    the rule machine-checked instead of promised.  Keyed on feature class as
    well as name, because 'Hot Springs' here is both a village and a spring.
    LABEL_ONLY names are label points placed on the course the sheets draw
    inside the neat — the Rio Grande's GNIS point is 500 miles downstream —
    and they are exempt by name, in the open."""
    rows = gnis_rows()
    want = {}
    for n, la, lo, ft, _ in PEAKS:
        want[(GNIS_NAME.get(n, n), ('Summit',))] = (la, lo, ft)
    for n, la, lo, _ in CITIES:
        want[(GNIS_NAME.get(n, n),
              ('Populated Place', 'Locale', 'Mine'))] = (la, lo, None)
    for n, la, lo, _ in FEATURES:
        if n in LABEL_ONLY: continue
        want[(GNIS_NAME.get(n, n),
              ('Valley', 'Range', 'Stream', 'Basin', 'Flat', 'Plain', 'Summit',
               'Ridge', 'Cliff', 'Gap', 'Lake', 'Spring', 'Locale',
               'Park'))] = (la, lo, None)
    bad = []
    for (n, classes), (la, lo, ft) in want.items():
        g = next((rows[(n, c)] for c in classes if (n, c) in rows), None)
        if g is None:
            bad.append('%s: no GNIS %s record in the block' % (n, '/'.join(classes)))
            continue
        if abs(g[0]-la) > 2e-5 or abs(g[1]-lo) > 2e-5:
            bad.append('%s: GNIS has %.5f %.5f, places.py has %.5f %.5f'
                       % (n, g[0], g[1], la, lo))
        if ft is not None and g[2] is not None and ft != g[2]:
            bad.append('%s: GNIS has %d ft, places.py has %d ft' % (n, g[2], ft))
    if bad:
        for b in bad: p('  ! ' + b)
        raise SystemExit('places.py disagrees with GNIS — fix it, do not guess')
    p('  %d places audited against the 2021 GNIS archive: all exact' % len(want))

def verify_summits(g, hgt):
    """Each summit must stand up in the model where GNIS puts it.

    Two ways a peak can be wrong and one of them is invisible: a bad
    elevation (caught at ±130 m of the GNIS feet) and a bad *position* —
    snap_places hunts the local maximum in a ±1.5 km window, so a peak with
    a taller neighbour inside that window silently borrows its neighbour's
    summit.  Anything that walks more than 700 m is not this peak; drop it
    rather than mislabel a mountain."""
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

def waters(g):
    """The data layer: every named spring in the block, plus the tinajas.

    In the Chihuahuan Desert the map of water is the map of everything — the
    1903 sheets letter spring after spring, tinaja after tinaja, because
    that is what a survey party had to know.  Straight from the 2021 GNIS
    archive (class Spring, plus the Lake/Reservoir records whose names are
    tinajas or waterholes), thinned one to a cell so the basins stay
    readable."""
    picks = {}
    for (name, cls), (la, lo, _) in gnis_rows().items():
        tinaja = ('Tinaja' in name or 'Waterhole' in name or 'Tanks' in name)
        if cls == 'Spring': kind = 'spring'
        elif cls in ('Lake', 'Reservoir') and tinaja: kind = 'tinaja'
        else: continue
        u, v = g.uv(lo, la)
        if not (0.01 < u < 0.99 and 0.01 < v < 0.99): continue
        cell = (int(u*70), int(v*40))
        good = (2 if kind == 'tinaja' else 1, -len(name))
        if cell not in picks or good > picks[cell][0]:
            picks[cell] = (good, dict(n=name.replace(' (historical)', '')[:26],
                                      u=round(u, 5), v=round(v, 5), c=kind))
    out = sorted((t[1] for t in picks.values()), key=lambda m: m['n'])
    p('  %d springs and tinajas from GNIS' % len(out))
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
    p('· encoding the 1984–85 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))

    p('· auditing places against GNIS and the model…')
    audit_places()
    verify_summits(g, hgt)
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)
    W = waters(g)

    # the sheets' own inks: cream paper, sepia slope, mauve on the high rock
    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    lo_ft = 1600
    ramp_ft = [lo_ft + 450*i for i in range(len(ramp))]

    gj = json.load(open(path('georef.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=W,
               ui=dict(exagDef=1.9, exagMax=6.0, contourM=30.48, mineDist=0.55,
                       mineGlyph='○', rampLo=lo_ft, rampHi=ramp_ft[-1],
                       sheetA='1903 sheets', altName='1984–85 sheets',
                       tourEx=[1.05, 0.012, 1.15, 2.4]),
               georef=gj.get('agreement'))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
