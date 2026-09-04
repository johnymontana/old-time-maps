#!/usr/bin/env python3
"""Bright Angel — asset pipeline.

Two 1:48,000 plane-table specials of the Grand Canyon joined at 112°W —
BRIGHT ANGEL (surveyed 1902-03, edition of 1903) and VISHNU (edition of
Sept. 1907), both drawn by François E. Matthes with fifty-foot contours —
over Terrarium elevations, with the Powell-era 1:250,000 reconnaissance
sheets of 1886 (KAIBAB and ECHO CLIFFS) one slider-stop behind, and the
canyon's named rapids, springs and waterfalls riding the terrain as data.

Every layer is an HTMC GeoTIFF carrying its own polyconic/NAD27
georeference, so nothing here is fitted: the stage below reads the
embedded transforms, probes each sheet's four neatline corners, and the
resample is a straight passthrough clipped to the neat.  The two printings
in each pair are tone-matched at their paper whites before they meet.

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
WORK = os.environ.get('BA_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import dem
from proj import Lcc, wgs84_to_nad27
from georef import QuadGeoref
from encode import Grid, encode_height, encode_drape, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, WATERS

S3 = 'https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/GeoTIFF/AZ/'

# The block: two 15-minute specials side by side, 112°15′–111°45′ W,
# 36°00′–36°15′ N — river to rim, Point Sublime to the Little Colorado.
BLOCK = (-112.25, -111.75, 36.0, 36.25)

# The Matthes specials.  neat = (W, E, S, N) of the printed graticule.
QUADS = [
    # scan 314253 of the 1903 edition, not the memo's 314251: same plate,
    # same press, but a cleaner white paper whose ink sits far closer to the
    # Vishnu sheet's, so the two halves meet at 112°W without a colour step.
    dict(id='brightangel1903', scan=314253,
         url=S3 + 'AZ_Bright%20Angel_314253_1903_48000_geo.tif',
         neat=(-112.25, -112.0, 36.0, 36.25)),
    # scan 464981 is the plain "Edition of Sept. 1907"; scan 314292 of the
    # same quad is the 1919 reprint, printed with brown shaded relief on a
    # dark ochre paper that no tone match can bring to the 1903 sheet.
    dict(id='vishnu1907', scan=464981,
         url=S3 + 'AZ_Vishnu_464981_1907_48000_geo.tif',
         neat=(-112.0, -111.75, 36.0, 36.25)),
]
# The 1886 reconnaissance, J. W. Powell director — 1:250,000 degree sheets.
# KAIBAB covers 113°–112° W and stops dead at the block's midline, so ECHO
# CLIFFS (the next sheet east, same series, same year) carries the other
# half: the Powell-era layer is a pair, not a single sheet.
RECON = [
    dict(id='kaibab1886', scan=315511,
         url=S3 + 'AZ_Kaibab_315511_1886_250000_geo.tif',
         neat=(-112.25, -112.0, 36.0, 36.25)),
    dict(id='echocliffs1886', scan=315475,
         url=S3 + 'AZ_Echo%20Cliffs_315475_1886_250000_geo.tif',
         neat=(-112.0, -111.75, 36.0, 36.25)),
]

LCC = Lcc(36.05, 36.20, -112.0)
MARGIN = 0.00047                       # rad of arc around the neat (~3 km)
TEX_W, HGT_W, ALT_W = 2560, 1707, 1920
DEM_ZOOM, DEM_BOX = 12, (-112.37, -111.63, 35.88, 36.37)
CLAMP = (600, 2900)                    # river ~730 m to the Kaibab rim ~2,650 m
PAPER = (233, 224, 200)

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid():
    return Grid.around(LCC, [BLOCK[0], BLOCK[1]], [BLOCK[2], BLOCK[3]], MARGIN, TEX_W)

# ------------------------------------------------------------------ stage 1
def fetch():
    for q in QUADS + RECON:
        tif = path(q['id'] + '.tif')
        if not os.path.exists(tif):
            p('· downloading %s…' % q['id'])
            req = urllib.request.Request(q['url'], headers={'User-Agent': 'old-time-maps/1.0'})
            with urllib.request.urlopen(req, timeout=600) as r, open(tif, 'wb') as f:
                f.write(r.read())
    dem.fetch(DEM_BOX, DEM_ZOOM, log=p)

# ------------------------------------------------------------------ stage 2
def georef():
    """No fitting — read each scan's embedded transform and prove it.

    Every sheet in this block is an HTMC GeoTIFF whose GeoKeyDirectory
    carries a polyconic projection on NAD27, so `QuadGeoref` is the whole
    registration.  What is worth checking is that the transform actually
    lands on the printed neatline: for each sheet we probe the four corners
    of its own quarter of the block and confirm they fall inside the raster
    with the sheet's nominal ground scale.  The numbers land in
    work/probe.json and in the About panel."""
    if os.path.exists(path('probe.json')):
        p('· neatline probes cached'); return
    fetch()
    out = {}
    for q in QUADS + RECON:
        im = Image.open(path(q['id'] + '.tif'))
        gr = QuadGeoref(im)
        W, E, S, N = q['neat']
        corners = {}
        for lon, lat in ((W, N), (E, N), (W, S), (E, S)):
            x, y = gr.to_px(lon, lat)
            inside = 0 <= x < im.size[0] and 0 <= y < im.size[1]
            corners['%.4f,%.4f' % (lon, lat)] = [round(float(x), 1), round(float(y), 1), bool(inside)]
            if not inside:
                raise SystemExit('%s: neat corner %.4f,%.4f falls outside the scan'
                                 % (q['id'], lon, lat))
        out[q['id']] = dict(scan=q['scan'], size=list(im.size), datum=gr.datum,
                            lon0=gr.lon0, lat0=gr.lat0,
                            m_per_px=round(float(gr.scale[0]), 3), corners=corners)
        p('  %-16s %5d × %5d px · %6.3f m/px · polyconic %s, lon0 %.3f — 4/4 corners inside'
          % (q['id'], im.size[0], im.size[1], gr.scale[0], gr.datum, gr.lon0))
        im.close()
    json.dump(out, open(path('probe.json'), 'w'), indent=1)

def tone_match(tex, regions, label, log):
    """Even out two printings across the seam.

    The usual paper-white match is not enough here: the 1903 Bright Angel
    sheet is a warm tan press run and the 1907 Vishnu sheet a pale pink one,
    so their *inks* disagree as much as their papers.  Each region therefore
    gets a two-point linear match per channel — its paper white (92nd
    percentile) and its deepest ink (4th percentile) are both carried to the
    pair's median — with the gain clamped so a bad histogram can never blow
    a sheet out."""
    stats = {k: np.array([[np.percentile(tex[:, :, c][m], 4),
                           np.percentile(tex[:, :, c][m], 92)] for c in range(3)])
             for k, m in regions.items() if m.any()}
    target = np.median(np.stack(list(stats.values())), axis=0)      # 3 × 2
    for k, m in regions.items():
        if k not in stats: continue
        lo, hi = stats[k][:, 0], stats[k][:, 1]
        gain = np.clip((target[:, 1]-target[:, 0])/np.maximum(hi-lo, 1.0), 0.80, 1.25)
        log('  %s %s: ink %s → %s · gain %s'
            % (label, k, np.round(lo, 0), np.round(target[:, 0], 0), np.round(gain, 3)))
        for c in range(3):
            v = tex[:, :, c][m]
            tex[:, :, c][m] = np.clip((v-lo[c])*gain[c] + target[c, 0], 0, 255)

def mosaic_sheets(sheets, lon27, lat27, inside, shape, label):
    """Passthrough-resample a list of quads onto one texture, clipped to
    each sheet's own neat, then tone-match the printings to each other."""
    tex = np.zeros(shape, np.float32); tex[:] = PAPER
    regions = {}
    for q in sheets:
        W, E, S, N = q['neat']
        inq = inside & (lon27 >= W) & (lon27 <= E) & (lat27 >= S) & (lat27 <= N)
        im = Image.open(path(q['id'] + '.tif'))
        gr = QuadGeoref(im)
        src = np.asarray(im.convert('RGB'), dtype=np.float32); del im
        QX, QY = gr.to_px(lon27[inq], lat27[inq])
        np.clip(QX, 0, src.shape[1]-1, out=QX); np.clip(QY, 0, src.shape[0]-1, out=QY)
        for c in range(3):
            tex[:, :, c][inq] = ndimage.map_coordinates(
                src[:, :, c], [QY, QX], order=1, mode='nearest')
        del src
        regions[q['id']] = inq
        p('  %s: %d texels' % (q['id'], int(inq.sum())))
    tone_match(tex, regions, label, p)
    return np.clip(tex, 0, 255).astype(np.uint8)

# ------------------------------------------------------------------ stage 3
def resample():
    if all(os.path.exists(path(f)) for f in ('hgt.npy', 'drape.npy', 'mask.npy', 'alt.npy')):
        p('· grid cached'); return
    georef()
    g = make_grid()
    p('· conic grid %d × %d  (%.1f × %.1f km, %.1f m/texel)'
      % (g.TW, g.TH, g.kmw, g.kmh, g.m_per_texel))
    GX, GY, LON, LAT = g.lonlat()

    mos, x0, y0 = dem.mosaic(DEM_BOX, DEM_ZOOM, CLAMP, log=p)
    hgt = dem.sample(mos, x0, y0, DEM_ZOOM, LON, LAT); del mos
    p('  elevation %.0f – %.0f m' % (hgt.min(), hgt.max()))
    np.save(path('hgt.npy'), hgt)

    lon27, lat27 = wgs84_to_nad27(LON, LAT)
    inside = ((lon27 >= BLOCK[0]) & (lon27 <= BLOCK[1]) &
              (lat27 >= BLOCK[2]) & (lat27 <= BLOCK[3]))
    np.save(path('mask.npy'), inside)

    p('· resampling the 1903 & 1907 specials…')
    tex = mosaic_sheets(QUADS, lon27, lat27, inside, (g.TH, g.TW, 3), 'special')
    np.save(path('drape.npy'), tex)
    Image.fromarray(tex).resize((g.TW//2, g.TH//2)).save(path('qa_drape.png'))
    del tex

    p('· resampling the 1886 reconnaissance…')
    g2 = Grid(LCC, g.X0, g.X1, g.Y0, g.Y1, ALT_W)
    _, _, LON2, LAT2 = g2.lonlat()
    lo2, la2 = wgs84_to_nad27(LON2, LAT2)
    in2 = ((lo2 >= BLOCK[0]) & (lo2 <= BLOCK[1]) &
           (la2 >= BLOCK[2]) & (la2 <= BLOCK[3]))
    alt = mosaic_sheets(RECON, lo2, la2, in2, (g2.TH, g2.TW, 3), 'recon')
    np.save(path('alt.npy'), alt)
    Image.fromarray(alt).resize((g2.TW//2, g2.TH//2)).save(path('qa_alt.png'))
    p('  QA renders in work/qa_drape.png, work/qa_alt.png')

def measure(g, log=print):
    """The two numbers the About panel quotes, computed from the drape.

    Nothing on this sheet is fitted, so there is no residual to report —
    but there is still disagreement worth stating, and it can be measured
    off the finished layers instead of asserted:

    1. *1886 against 1902-03.*  Take the drawn Colorado on each layer (the
       blue plate is the only ink the two eras share) and, for every texel
       of Powell's river, the distance to the nearest texel of Matthes'.
       That is the reconnaissance-to-survey gap, in metres.
    2. *The pre-1927 datum.*  The Bright Angel sheet's own note reads "to
       place on 1927 North American datum move projection lines 420 feet
       south and 350 feet west".  We drape the HTMC georeference as staged
       rather than nudging it, so that correction should still be visible.
       Through the west half the river runs east-west, so comparing the
       drawn channel with the elevation model's channel column by column
       measures it directly."""
    if os.path.exists(path('measure.json')):
        return json.load(open(path('measure.json')))
    from scipy import ndimage as ndi
    drape = np.load(path('drape.npy')).astype(np.int16)
    alt = np.load(path('alt.npy')).astype(np.int16)
    hgt = np.load(path('hgt.npy')); mask = np.load(path('mask.npy'))
    TH, TW = hgt.shape; mpt = g.m_per_texel

    def blue(img, dr, bmin):
        r, gg, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
        return (b.astype(int)-r > dr) & (b > bmin)

    river = blue(drape, 10, 110) & mask & (hgt < 1150)
    dy = []
    for x in range(int(TW*0.55)):                    # the west half, river E–W
        ys = np.nonzero(river[:, x])[0]
        if len(ys) == 0 or len(ys) > 60: continue
        yr = ys.mean(); lo = int(max(0, yr-40)); hi = int(min(TH, yr+41))
        dy.append(lo + np.argmin(hgt[lo:hi, x]) - yr)
    south = -float(np.median(dy))*mpt

    old = blue(alt, 6, 100)
    old = ndi.zoom(old.astype(np.float32), (TH/alt.shape[0], TW/alt.shape[1]), order=1) > 0.4
    dist = ndi.distance_transform_edt(~river)[old & mask & (hgt < 1400)]
    out = dict(river1886_median_m=round(float(np.median(dist))*mpt),
               river1886_p75_m=round(float(np.percentile(dist, 75))*mpt),
               river1886_n=int(dist.size),
               datum_south_m=round(south), datum_south_n=len(dy))
    log('· 1886 river vs 1903–07 river: median %d m, 75th %d m (n=%d)'
        % (out['river1886_median_m'], out['river1886_p75_m'], out['river1886_n']))
    log('· drawn Colorado vs model channel, west half: %d m south (n=%d columns)'
        % (out['datum_south_m'], out['datum_south_n']))
    json.dump(out, open(path('measure.json'), 'w'), indent=1)
    return out

HUNT_M = 300     # summit search radius — see snap_peaks
GATE_M = 130     # a summit must agree with the model to this, or it is dropped

def snap_peaks(g, hgt, peaks, log=print):
    """Snap each summit to the model and verify it against GNIS.

    `lib.encode.snap_places` hunts the local maximum inside 1,500 m, which
    is right for a Montana range and wrong here: this block's rims stand
    300–400 m above the buttes that rise off the canyon floor within a
    kilometre and a half of them, so the shared radius walks Horseshoe Mesa,
    O'Neill Butte and half the temples up onto the Coconino rim — labels
    2 km from the thing they name.  So peaks are snapped in-sheet at
    HUNT_M instead, which is enough to correct a GNIS point that sits on a
    shoulder and not enough to leave the butte.  Every summit must then
    agree with its GNIS elevation to within GATE_M or the build stops:
    nothing here is guessed.  Cities and features still go through
    `snap_places`, which places them with no hunt at all."""
    TH, TW = hgt.shape
    r = max(1, int(HUNT_M/g.m_per_texel))
    out, worst = [], 0.0
    for n, lat, lon, ft, rng in peaks:
        u, v = g.uv(lon, lat)
        x = min(max(int(round(u*TW)), 0), TW-1); y = min(max(int(round(v*TH)), 0), TH-1)
        w = hgt[max(0, y-r):y+r+1, max(0, x-r):x+r+1]
        j = np.unravel_index(np.argmax(w), w.shape)
        gx, gy = max(0, x-r)+j[1], max(0, y-r)+j[0]
        e = float(w[j]); d = e - ft*0.3048
        if abs(d) > GATE_M:
            raise SystemExit('%s: model %.0f m vs GNIS %d ft — %.0f m out, drop it' % (n, e, ft, d))
        worst = max(worst, abs(d))
        out.append(dict(n=n, u=round(gx/TW, 5), v=round(gy/TH, 5), ft=ft, r=rng,
                        lat=lat, lon=lon))
    log('· %d summits snapped at %d m; worst model-vs-GNIS gap %.0f m (gate %d m)'
        % (len(out), HUNT_M, worst, GATE_M))
    return out

# ------------------------------------------------------------------ stage 4
def encode():
    resample()
    g = make_grid()
    hgt = np.load(path('hgt.npy'))
    mask = np.load(path('mask.npy'))
    HW, HH, hmin, hmax = encode_height(hgt, mask, os.path.join(BUILD, 'height.webp'),
                                       HGT_W, log=p)
    p('  on-sheet relief %.0f – %.0f m' % (hgt[mask].min(), hgt[mask].max()))
    encode_drape(np.load(path('drape.npy')), os.path.join(BUILD, 'drape.webp'),
                 quality=90, log=p)
    card = Image.open(os.path.join(BUILD, 'drape.webp'))
    card = card.resize((640, int(card.height*640/card.width)), Image.LANCZOS)
    card.save(os.path.join(BUILD, 'card.webp'), quality=82, method=6)
    p('· encoding the 1886 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks = snap_peaks(g, hgt, PEAKS, log=p)
    _, cities, feats = snap_places(g, hgt, [], CITIES, FEATURES, log=p)

    ramp = [[234, 226, 202], [227, 218, 193], [219, 209, 182], [211, 199, 170],
            [203, 189, 158], [196, 179, 147], [190, 169, 136], [184, 158, 125],
            [177, 147, 114], [169, 136, 104], [161, 128, 98], [156, 124, 97],
            [162, 133, 110], [175, 150, 131], [190, 170, 154]]
    ramp_ft = [2300 + 450*i for i in range(len(ramp))]

    W = [dict(n=n, u=round(g.uv(lon, lat)[0], 5), v=round(g.uv(lon, lat)[1], 5), c=c)
         for n, lat, lon, c in WATERS]
    p('  %d rapids, springs & falls' % len(W))
    md = measure(g, log=p)
    probe = json.load(open(path('probe.json')))
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=W,
               ui=dict(exagDef=1.5, exagMax=5.0, contourM=76.2, mineDist=0.60,
                       mineGlyph='≈', rampLo=2300, rampHi=8600,
                       sheetA='1903 & 1907 specials', altName='1886 reconnaissance',
                       tourEx=[1.05, 0.02, 1.15, 2.0]),
               probe={k: dict(scan=v['scan'], m_per_px=v['m_per_px']) for k, v in probe.items()},
               fit=md)

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
