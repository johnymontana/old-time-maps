#!/usr/bin/env python3
"""Montana by Rail — asset pipeline.

Two railroad maps of the whole state, twenty-eight years apart, on the
montana sheet's terrain: Rand McNally's New Commercial Atlas map of MONTANA
(1912 — four transcontinental routes, branch webs, the electric lines
already in the legend) as the face, and Cram's RAILROAD AND COUNTY MAP OF
MONTANA TY. (1884 — the Northern Pacific one year old, the Utah & Northern
narrow gauge, and almost nothing else) one slider-stop behind.  Passes,
tunnels and the Gold Creek last-spike site ride the terrain as data.

Neither map carries coordinates we can trust blindly; each is seeded from
two printed townsites and then registered by correlation against the
already-georeferenced montana drape on the shared drainage ink.  The 1912
sheet is an atlas spread with a binding gutter — its two pages are fitted
separately and rejoined at the fold, like a two-quad mosaic.

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
WORK = os.environ.get('RA_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')
MONTANA = os.path.join(REPO, 'montana', 'assets')
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
from proj import Lcc, poly_basis
from georef import Fit, overlay
from encode import Grid, encode_drape, encode_height, snap_places, write_meta
from places import PEAKS, CITIES, FEATURES, TOURS, RAILPOINTS

RM_URL = 'https://archive.org/download/dr_montana-2790233/2790233.jp2'
CRAM_URL = 'https://tile.loc.gov/storage-services/service/gmd/gmd425/g4251/g4251p/ct012068.jp2'

# printed townsites that seed each alignment (see flathead's Somers/Polson)
ANCHORS_RM = [((47.5002, -111.3008), (5247.0, 2992.0)),   # Great Falls
              ((45.4311, -108.5326), (7352.0, 5298.0))]   # Pryor
ANCHORS_CR = [((46.5927, -112.0361), (2645.0, 3098.0)),   # Helena
              ((47.8219, -110.6677), (3340.0, 2152.0))]   # Fort Benton
RM_BODY = (1570, 650, 10870, 7310)         # x0 y0 x1 y1, the atlas neatline
CR_BODY = (470, 480, 7030, 5240)           # map body; index booklet below

LCC = Lcc(45.0, 49.0, -109.5)
MMETA = json.load(open(os.path.join(MONTANA, 'meta.json')))
TEX_W, ALT_W, HGT_W = 3584, 2688, 2048

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(WORK, exist_ok=True); os.makedirs(BUILD, exist_ok=True)

def make_grid(w=TEX_W):
    g = MMETA['grid']
    return Grid(LCC, g['X0'], g['X1'], g['Y0'], g['Y1'], w)

def ink(rgb):
    m = rgb.mean(2, dtype=np.float32)
    f = (ndimage.gaussian_filter(m, 12) - m) > 30
    return ndimage.gaussian_filter(f.astype(np.float32), 1.4)

# ------------------------------------------------------------------ stage 1
def fetch():
    for url, jp2, jpg in ((RM_URL, 'rm1912.jp2', 'rm1912.jpg'),
                          (CRAM_URL, 'rail1884.jp2', 'rail1884.jpg')):
        if not os.path.exists(path(jpg)):
            if not os.path.exists(path(jp2)):
                p('· downloading %s…' % jp2)
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=600) as r:
                    open(path(jp2), 'wb').write(r.read())
            Image.open(path(jp2)).convert('RGB').save(path(jpg), quality=95)

# ------------------------------------------------------------------ stage 2
def montana_target():
    """The 1991 sheet's drape, already on the state grid, as the reference."""
    dr = np.asarray(Image.open(os.path.join(MONTANA, 'drape.webp')).convert('RGB'),
                    dtype=np.uint8)
    g = MMETA['grid']
    H, W = dr.shape[:2]
    def to_px(lon, lat):
        rho = g['F']/np.power(np.tan(np.pi/4 + np.radians(lat)/2), g['NN'])
        th = g['NN']*(np.radians(lon) - g['LON0'])
        X = rho*np.sin(th); Y = -rho*np.cos(th)
        u = (X-g['X0'])/(g['X1']-g['X0']); v = (g['Y1']-Y)/(g['Y1']-g['Y0'])
        return u*W, v*H
    m_per_px = MMETA['kmw']*1000.0/W
    return dict(name='montana1991', feat=ink(dr), to_px=to_px, m_per_px=m_per_px)

def seed_from(anchors):
    (llA, pxA), (llB, pxB) = anchors
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
    return SeedAff(), m_scan

def fit_map(jpg, body, anchors, target, name, split_fold=False):
    from reg import register, fit_trimmed
    rgb = np.asarray(Image.open(path(jpg)), dtype=np.uint8)
    f = ink(rgb)
    gray = rgb.mean(2); del rgb
    x0, y0, x1, y1 = body
    f[:y0, :] = 0; f[y1:, :] = 0; f[:, :x0] = 0; f[:, x1:] = 0

    foldx = None
    if split_fold:
        mid = gray[y0:y1, x0+3500:x1-3500].mean(0)
        foldx = x0+3500 + int(np.argmin(ndimage.uniform_filter1d(mid, 40)))
        p('  %s: binding fold at x=%d' % (name, foldx))
        f[:, foldx-28:foldx+28] = 0
    del gray

    seed, m_scan = seed_from(anchors)
    p('  %s: seed %.0f m/px' % (name, m_scan))
    lons = np.arange(-115.9, -104.2, 0.42)
    lats = np.arange(44.62, 48.95, 0.36)
    X, Y, gx, gy, _ = register(f, [target], LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=seed,
                               pw=150, sw=170, log=p)
    if len(gx) < 14: raise SystemExit('%s: too few GCPs' % name)
    fit1, _ = fit_trimmed(X, Y, gx, gy, 1, name=name+' pass 1', floor=5.0,
                          k=2.2, rounds=4, m_per_px=m_scan, log=p)
    X, Y, gx, gy, _ = register(f, [target], LCC, lons, lats,
                               m_scan_hint=m_scan, seed_fit=fit1,
                               pw=150, sw=70, log=p)
    if len(gx) < 14: raise SystemExit('%s: too few GCPs after refine' % name)

    def dump(fit, keep, n):
        return dict(Xm=fit.Xm, Ym=fit.Ym, sX=fit.sX, deg=fit.deg,
                    cx=fit.cx.tolist(), cy=fit.cy.tolist(),
                    rms=round(fit.rms, 2), median=round(fit.median, 2),
                    m_per_px=round(m_scan, 1), n=n)
    if not split_fold:
        fit, keep = fit_trimmed(X, Y, gx, gy, 3, name=name+' fit', floor=5.0,
                                k=2.4, rounds=4, m_per_px=m_scan, log=p)
        return dict(kind='one', fit=dump(fit, keep, int(keep.sum()))), (gx, gy, keep)
    L = gx < foldx; R = ~L
    fits = {}
    for tag, sel in (('L', L), ('R', R)):
        fit, keep = fit_trimmed(X[sel], Y[sel], gx[sel], gy[sel], 3,
                                name='%s %s fit' % (name, tag), floor=5.0,
                                k=2.4, rounds=4, m_per_px=m_scan, log=p)
        fits[tag] = dump(fit, keep, int(keep.sum()))
    # the state-plane X of the fold, taken where the two fits meet
    from proj import poly_basis as _pb
    Xs = np.linspace(min(X), max(X), 400)
    Ys = np.full(400, np.median(Y))
    class _F:
        def __init__(s, d): s.d = d
        def apply(s, X, Y):
            A = _pb((np.asarray(X, float)-s.d['Xm'])/s.d['sX'],
                    (np.asarray(Y, float)-s.d['Ym'])/s.d['sX'], s.d['deg'])
            return A@np.array(s.d['cx']), A@np.array(s.d['cy'])
    xl, _ = _F(fits['L']).apply(Xs, Ys)
    splitX = float(Xs[int(np.argmin(np.abs(xl - foldx)))])
    return dict(kind='fold', L=fits['L'], R=fits['R'], splitX=splitX,
                foldx=foldx), (gx, gy, np.ones(len(gx), bool))

def georef():
    if os.path.exists(path('fits.json')):
        p('· georeference cached'); return
    fetch()
    target = montana_target()
    p('· registering the 1912 Rand McNally…')
    rm, (gx, gy, keep) = fit_map('rm1912.jpg', RM_BODY, ANCHORS_RM, target,
                                 'rm1912', split_fold=True)
    overlay(Image.open(path('rm1912.jpg')),
            {(255, 40, 40): list(zip(gx[keep], gy[keep]))}, path('qa_rm.png'), 1500)
    p('· registering the 1884 Cram…')
    cr, (gx, gy, keep) = fit_map('rail1884.jpg', CR_BODY, ANCHORS_CR, target,
                                 'cram1884')
    overlay(Image.open(path('rail1884.jpg')),
            {(255, 40, 40): list(zip(gx[keep], gy[keep]))}, path('qa_cram.png'), 1500)
    json.dump(dict(rm=rm, cram=cr), open(path('fits.json'), 'w'))

class SavedFit:
    def __init__(self, d):
        self.d = d
    def apply(self, X, Y):
        d = self.d
        A = poly_basis((np.asarray(X, float)-d['Xm'])/d['sX'],
                       (np.asarray(Y, float)-d['Ym'])/d['sX'], d['deg'])
        return A@np.array(d['cx']), A@np.array(d['cy'])

# ------------------------------------------------------------------ stage 3
def resample():
    if os.path.exists(path('drape.npy')) and os.path.exists(path('alt.npy')):
        p('· drape cached'); return
    georef()
    fits = json.load(open(path('fits.json')))

    def sample(jpg, tex_w, body, fitd, out, paper):
        g = make_grid(tex_w)
        _, _, LON, LAT = g.lonlat()
        X, Y = LCC.fwd(LON, LAT)
        src = np.asarray(Image.open(path(jpg)).convert('RGB'), dtype=np.float32)
        tex = np.zeros((g.TH, g.TW, 3), np.float32); tex[:] = paper
        x0, y0, x1, y1 = body
        if fitd['kind'] == 'fold':
            parts = [(SavedFit(fitd['L']), X <= fitd['splitX']),
                     (SavedFit(fitd['R']), X > fitd['splitX'])]
        else:
            parts = [(SavedFit(fitd['fit']), np.ones(X.shape, bool))]
        for fit, sel in parts:
            SX, SY = fit.apply(X[sel], Y[sel])
            ok = (SX > x0+2) & (SX < x1-2) & (SY > y0+2) & (SY < y1-2)
            np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
            for c in range(3):
                band = tex[:, :, c][sel]
                band[ok] = ndimage.map_coordinates(src[:, :, c], [SY[ok], SX[ok]],
                                                   order=1, mode='nearest')
                tex[:, :, c][sel] = band
        del src
        np.save(path(out), np.clip(tex, 0, 255).astype(np.uint8))
        Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)) \
             .resize((g.TW//4, g.TH//4)).save(path(out.replace('.npy', '_qa.png')))

    p('· resampling the 1912 map…')
    sample('rm1912.jpg', TEX_W, RM_BODY, fits['rm'], 'drape.npy', (238, 231, 214))
    p('· resampling the 1884 map…')
    sample('rail1884.jpg', ALT_W, CR_BODY, fits['cram'], 'alt.npy', (233, 226, 206))

# ------------------------------------------------------------------ stage 4
def decode_height():
    hm = np.asarray(Image.open(os.path.join(MONTANA, 'height.webp')).convert('RGB'))
    q = (hm[:, :, 0].astype(np.uint16) << 4) | (hm[:, :, 1] >> 4)
    return MMETA['hmin'] + q/4095.0*(MMETA['hmax']-MMETA['hmin'])

def encode():
    resample()
    g = make_grid()
    p('· re-encoding the montana height field…')
    hgt = decode_height()
    hm = np.asarray(Image.open(os.path.join(MONTANA, 'height.webp')).convert('RGB'))
    HW, HH, hmin, hmax = encode_height(hgt, hm[:, :, 2] > 128,
                                       os.path.join(BUILD, 'height.webp'), HGT_W, log=p)
    encode_drape(np.load(path('drape.npy')), os.path.join(BUILD, 'drape.webp'), log=p)
    card = Image.open(os.path.join(BUILD, 'drape.webp'))
    card = card.resize((640, int(card.height*640/card.width)), Image.LANCZOS)
    card.save(os.path.join(BUILD, 'card.webp'), quality=82, method=6)
    p('· encoding the 1884 layer…')
    Image.fromarray(np.load(path('alt.npy'))).save(
        os.path.join(BUILD, 'alt.webp'), quality=80, method=6)
    p('  alt.webp      %6.2f MB' % (os.path.getsize(os.path.join(BUILD, 'alt.webp'))/1e6))
    peaks, cities, feats = snap_places(g, hgt, PEAKS, CITIES, FEATURES, log=p)

    ramp = [[229, 219, 196], [224, 213, 188], [218, 206, 180], [211, 198, 171],
            [203, 189, 161], [194, 179, 151], [185, 169, 141], [176, 159, 132],
            [167, 150, 123], [158, 141, 115], [150, 133, 108], [143, 126, 102],
            [139, 122, 98], [143, 127, 104], [152, 137, 116], [163, 149, 129],
            [176, 163, 144]]
    ramp_ft = [1500 + 500*i for i in range(len(ramp))]

    R = [dict(n=n, u=round(g.uv(lon, lat)[0], 5), v=round(g.uv(lon, lat)[1], 5), c=c)
         for n, lat, lon, c in RAILPOINTS]
    fits = json.load(open(path('fits.json')))
    worst = max(fits['rm']['L']['rms'], fits['rm']['R']['rms'], fits['cram']['fit']['rms'])
    n = fits['rm']['L']['n'] + fits['rm']['R']['n'] + fits['cram']['fit']['n']
    write_meta(BUILD, g, (HW, HH), hmin, hmax, ramp, ramp_ft,
               peaks, cities, feats, TOURS, log=p,
               mines=R,
               ui=dict(exagDef=5.0, exagMax=20.0, contourM=250, mineDist=0.85,
                       mineGlyph='∩', rampLo=1400, rampHi=10200,
                       sheetA='1912 network', altName='1884 territory',
                       tourEx=[1.7, 0.021, 2.1, 5.6]),
               fit=dict(rms=worst, median=worst, n=n))

STAGES = [('fetch', fetch), ('georef', georef), ('resample', resample), ('encode', encode)]
if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
