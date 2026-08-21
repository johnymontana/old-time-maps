#!/usr/bin/env python3
"""
Montana in Relief — asset pipeline.

Turns the American Geographical Society Library's scan of Allan Cartography's
1991 shaded-relief map of Montana into two textures that share one Lambert
conformal conic grid with an open elevation model:

    assets/drape.webp    the 1991 sheet, resampled onto the conic grid
    assets/height.webp   12-bit elevation + signed distance to the state line
    assets/meta.json     grid parameters, hypsometric ramp, place names, tours

Intermediates (the 5 MB scan, ~1,000 elevation tiles, the fitted polynomial)
land in work/, which is gitignored; the three files above are committed because
rebuilding them pulls ~250 MB.

Stages run in order and cache their outputs; re-running is cheap.

    python3 pipeline/build.py            # everything
    python3 pipeline/build.py resample   # this stage and the ones after it

Requires: pillow, numpy, scipy, pyshp.
"""
import base64, io, json, math, os, sys, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage, optimize
from scipy.spatial import cKDTree

Image.MAX_IMAGE_PIXELS = None

HERE  = os.path.dirname(os.path.abspath(__file__))
ROOT  = os.path.dirname(HERE)
WORK  = os.environ.get('MT_WORK', os.path.join(ROOT, 'work'))
BUILD = os.path.join(ROOT, 'assets')   # committed: regenerating needs a 250 MB download
sys.path.insert(0, HERE)
from places import PEAKS, CITIES, FEATURES, TOURS

# --- the scan -------------------------------------------------------------
IIIF   = 'https://collections.lib.uwm.edu/iiif/2/agdm:17587'   # joined sheet
SCAN_W = 7500                                                   # of 15000
# --- elevation ------------------------------------------------------------
TERRARIUM = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
ZOOM   = 10
BOX    = (-116.85, -103.00, 43.83, 49.58)      # W, E, S, N — generous margin
# --- projection: USGS state-base convention for Montana -------------------
SP1, SP2, LON0 = 45.0, 49.0, -109.5
# --- output ---------------------------------------------------------------
TEX_W   = 4096          # drape texture width
HGT_W   = 2730          # height raster width
MARGIN  = 0.0056        # radians of arc padded around the state, each side
R_EARTH = 6371000.0

def p(*a): print(*a, flush=True)
def path(*a): return os.path.join(WORK, *a)
os.makedirs(BUILD, exist_ok=True)

# ---------------------------------------------------------------- projection
def _t(phi): return math.tan(math.pi/4 + phi/2)
_P1, _P2 = math.radians(SP1), math.radians(SP2)
NN = math.log(math.cos(_P1)/math.cos(_P2)) / math.log(_t(_P2)/_t(_P1))
FF = math.cos(_P1)*_t(_P1)**NN / NN
LON0R = math.radians(LON0)

def lcc(lon, lat):
    """lon/lat (degrees) -> Lambert conformal conic on the unit sphere."""
    lon = np.radians(np.asarray(lon, float)); lat = np.radians(np.asarray(lat, float))
    rho = FF/np.power(np.tan(np.pi/4 + lat/2), NN)
    th  = NN*(lon - LON0R)
    return rho*np.sin(th), -rho*np.cos(th)

def inv_lcc(X, Y):
    rho = np.hypot(X, Y); th = np.arctan2(X, -Y)
    return (np.degrees(LON0R + th/NN),
            np.degrees(2*np.arctan(np.power(FF/rho, 1.0/NN)) - np.pi/2))

def poly_basis(Xs, Ys, deg):
    cols = [np.ones_like(Xs)]
    for d in range(1, deg+1):
        for i in range(d+1):
            cols.append(Xs**(d-i) * Ys**i)
    return np.stack(cols, -1)

# ------------------------------------------------------------------ stage 1
def fetch_map():
    dst = path('map%d.jpg' % SCAN_W)
    if os.path.exists(dst): return p('· scan cached'), dst
    p('· downloading the 1991 sheet (%d px wide)…' % SCAN_W)
    url = '%s/full/%d,/0/default.jpg' % (IIIF, SCAN_W)
    with urllib.request.urlopen(url, timeout=300) as r, open(dst, 'wb') as f:
        f.write(r.read())
    return None, dst

def fetch_boundary():
    dst = path('mt_boundary.json')
    if os.path.exists(dst): return dst
    p('· downloading the surveyed state boundary (US Census 2021)…')
    url = 'https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_state_500k.zip'
    with urllib.request.urlopen(url, timeout=180) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    d = path('states'); os.makedirs(d, exist_ok=True); z.extractall(d)
    import shapefile
    sf = shapefile.Reader(os.path.join(d, 'cb_2021_us_state_500k.shp'))
    i = [k for k, rec in enumerate(sf.records()) if rec['NAME'] == 'Montana'][0]
    sh = sf.shape(i)
    json.dump({'points': [[round(x, 6), round(y, 6)] for x, y in sh.points],
               'parts': list(sh.parts)}, open(dst, 'w'))
    return dst

def boundary_ring():
    b = json.load(open(fetch_boundary()))
    pts = np.array(b['points']); parts = list(b['parts']) + [len(pts)]
    rings = [pts[parts[i]:parts[i+1]] for i in range(len(parts)-1)]
    rings.sort(key=len, reverse=True)
    return rings[0]

def fetch_dem():
    d = path('dem'); os.makedirs(d, exist_ok=True)
    N = 2**ZOOM
    lon2x = lambda lo: (lo+180.0)/360.0*N
    lat2y = lambda la: (1.0 - math.asinh(math.tan(math.radians(la)))/math.pi)/2.0*N
    W, E, S, Nn = BOX
    x0, x1 = int(math.floor(lon2x(W))), int(math.floor(lon2x(E)))
    y0, y1 = int(math.floor(lat2y(Nn))), int(math.floor(lat2y(S)))
    tiles = [(x, y) for x in range(x0, x1+1) for y in range(y0, y1+1)]
    todo  = [t for t in tiles if not os.path.exists(os.path.join(d, '%d_%d_%d.png' % (ZOOM, *t)))]
    if todo:
        p('· downloading %d Terrarium tiles…' % len(todo))
        def get(t):
            url = TERRARIUM.format(z=ZOOM, x=t[0], y=t[1])
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(url, timeout=40) as r: data = r.read()
                    open(os.path.join(d, '%d_%d_%d.png' % (ZOOM, *t)), 'wb').write(data)
                    return 1
                except Exception:
                    if attempt == 3: raise
            return 0
        with ThreadPoolExecutor(24) as ex: list(ex.map(get, todo))
    else:
        p('· DEM tiles cached')
    open(path('dem_meta.txt'), 'w').write('%d %d %d %d %d\n' % (ZOOM, x0, x1, y0, y1))
    return x0, x1, y0, y1

# ------------------------------------------------------------------ stage 2
def make_mask():
    """Isolate the printed map body: it is tinted, the paper around it is not."""
    dst = path('mask.npy')
    if os.path.exists(dst): return p('· mask cached') or np.load(dst)
    _, scan = fetch_map()
    p('· isolating the printed map body by colour…')
    a = np.asarray(Image.open(scan).convert('RGB'), dtype=np.float32)
    mx, mn = a.max(2), a.min(2)
    sat = (mx-mn)/np.maximum(mx, 1e-3)
    m = (sat > 0.085) | (mx/255.0 < 0.72)
    m = ndimage.binary_closing(m, structure=np.ones((9, 9)))
    m = ndimage.binary_fill_holes(m)
    m = ndimage.binary_opening(m, structure=np.ones((15, 15)))
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n+1))
    m = ndimage.binary_fill_holes(lab == int(np.argmax(sizes))+1)
    np.save(dst, m)
    return m

# ------------------------------------------------------------------ stage 3
def fit_projection():
    """Fit scan pixels = poly3(LCC(lon,lat)) by ICP against the state silhouette."""
    if os.path.exists(path('coef3.npy')) and os.path.exists(path('geonorm.json')):
        p('· projection fit cached'); return
    mask = make_mask()
    inner = ndimage.binary_erosion(mask, structure=np.ones((7, 7)))  # centre the drawn line
    edge  = inner ^ ndimage.binary_erosion(inner)
    ey, ex = np.nonzero(edge)
    tree = cKDTree(np.column_stack([ex, ey]))
    ys, xs = np.nonzero(mask)

    ring = boundary_ring()
    dens = []
    for i in range(len(ring)-1):
        a, b = ring[i], ring[i+1]
        k = max(1, int(math.hypot(*(b-a))/0.004))
        for j in range(k): dens.append(a + (b-a)*j/k)
    dens.append(ring[-1]); ring = np.array(dens)

    X, Y = lcc(ring[:, 0], ring[:, 1])
    P = np.column_stack([X, Y])
    Xm, Ym, sX = X.mean(), Y.mean(), X.std()
    Xs, Ys = (X-Xm)/sX, (Y-Ym)/sX

    # crude similarity from the two bounding boxes, then refine on IoU
    s = ((xs.max()-xs.min())/(X.max()-X.min()) + (ys.max()-ys.min())/(Y.max()-Y.min()))/2
    par0 = np.array([s, 0.0, 0.0, -s, xs.min()-s*X.min(), ys.min()+s*Y.max()])
    small = mask[::4, ::4]
    def raster(par):
        q = (np.column_stack([par[0]*P[:, 0]+par[1]*P[:, 1]+par[4],
                              par[2]*P[:, 0]+par[3]*P[:, 1]+par[5]]))/4
        img = Image.new('1', (small.shape[1], small.shape[0]), 0)
        ImageDraw.Draw(img).polygon([tuple(v) for v in q], fill=1)
        return np.asarray(img, dtype=bool)
    def negiou(par):
        r = raster(par)
        return -np.count_nonzero(r & small)/max(np.count_nonzero(r | small), 1)
    scale = np.array([s*1e-2]*4 + [20, 20])
    p('· fitting the conic to the silhouette…')
    res = optimize.minimize(lambda z: negiou(par0+z*scale), np.zeros(6), method='Nelder-Mead',
                            options=dict(maxiter=4000, xatol=1e-4, fatol=1e-7))
    par = par0 + res.x*scale
    p('  similarity IoU %.4f' % -res.fun)

    cur = np.column_stack([par[0]*X+par[1]*Y+par[4], par[2]*X+par[3]*Y+par[5]])
    for deg in (1, 2, 3):
        A = poly_basis(Xs, Ys, deg)
        for _ in range(8):
            dist, idx = tree.query(cur, workers=-1)
            tgt = np.column_stack([ex[idx], ey[idx]])
            w = 1.0/(1.0 + (dist/12.0)**2)                    # robust weights
            Aw = A*w[:, None]
            cx = np.linalg.lstsq(Aw, tgt[:, 0]*w, rcond=None)[0]
            cy = np.linalg.lstsq(Aw, tgt[:, 1]*w, rcond=None)[0]
            cur = np.column_stack([A@cx, A@cy])
        dist, _ = tree.query(cur, workers=-1)
        p('  degree %d: rms %.2f px  median %.2f px' % (deg, math.sqrt((dist**2).mean()),
                                                        np.median(dist)))
        np.save(path('coef%d.npy' % deg), np.array([cx, cy]))
    json.dump(dict(Xm=float(Xm), Ym=float(Ym), sX=float(sX)), open(path('geonorm.json'), 'w'))

# ------------------------------------------------------------------ stage 4
def resample():
    """Put the DEM and the scan on one conic grid."""
    if os.path.exists(path('hgt_full.npy')) and os.path.exists(path('drape_full.png')) \
       and os.path.exists(path('grid.json')):
        p('· grid cached'); return
    fit_projection()
    gn = json.load(open(path('geonorm.json')))
    Xm, Ym, sX = gn['Xm'], gn['Ym'], gn['sX']
    C = np.load(path('coef3.npy'))

    ring = boundary_ring()
    rX, rY = lcc(ring[:, 0], ring[:, 1])
    X0, X1 = rX.min()-MARGIN, rX.max()+MARGIN
    Y0, Y1 = rY.min()-MARGIN, rY.max()+MARGIN
    TW = TEX_W; TH = int(round(TW*(Y1-Y0)/(X1-X0)))
    p('· conic grid %d × %d  (%.0f × %.0f km)' % (TW, TH, (X1-X0)*R_EARTH/1e3,
                                                  (Y1-Y0)*R_EARTH/1e3))
    gx = X0 + (np.arange(TW)+0.5)*(X1-X0)/TW
    gy = Y1 - (np.arange(TH)+0.5)*(Y1-Y0)/TH
    GX, GY = np.meshgrid(gx, gy)
    LON, LAT = inv_lcc(GX, GY)

    x0, x1, y0, y1 = fetch_dem()
    NT = 2**ZOOM
    MW, MH = (x1-x0+1)*256, (y1-y0+1)*256
    p('· mosaicking %d × %d elevation samples…' % (MW, MH))
    mos = np.zeros((MH, MW), np.float32)
    for tx in range(x0, x1+1):
        for ty in range(y0, y1+1):
            a = np.asarray(Image.open(path('dem', '%d_%d_%d.png' % (ZOOM, tx, ty))).convert('RGB'),
                           dtype=np.float32)
            mos[(ty-y0)*256:(ty-y0+1)*256, (tx-x0)*256:(tx-x0+1)*256] = \
                a[:, :, 0]*256 + a[:, :, 1] + a[:, :, 2]/256 - 32768
    bad = (mos < 300) | (mos > 4200)          # voids/spikes: nothing here is that low
    if bad.any():
        p('  repairing %d void samples' % int(bad.sum()))
        ind = ndimage.distance_transform_edt(bad, return_indices=True, return_distances=False)
        mos = mos[tuple(ind)]
    mos = ndimage.gaussian_filter(mos, 0.9)

    mpx = (LON+180.0)/360.0*NT
    mpy = (1.0 - np.arcsinh(np.tan(np.radians(LAT)))/np.pi)/2.0*NT
    MPX, MPY = (mpx-x0)*256, (mpy-y0)*256
    assert MPX.min() > 1 and MPX.max() < MW-2 and MPY.min() > 1 and MPY.max() < MH-2, \
        'DEM box too small for the grid — widen BOX'
    hgt = ndimage.map_coordinates(mos, [MPY, MPX], order=1, mode='nearest').astype(np.float32)
    del mos
    np.save(path('hgt_full.npy'), hgt)
    p('  elevation %.0f – %.0f m' % (hgt.min(), hgt.max()))

    _, scan = fetch_map()
    p('· resampling the sheet onto the grid…')
    im = Image.open(scan).convert('RGB').filter(ImageFilter.GaussianBlur(0.55))
    src = np.asarray(im, dtype=np.float32); del im
    A = poly_basis((GX-Xm)/sX, (GY-Ym)/sX, 3)
    SX, SY = A@C[0], A@C[1]
    np.clip(SX, 0, src.shape[1]-1, out=SX); np.clip(SY, 0, src.shape[0]-1, out=SY)
    tex = np.empty((TH, TW, 3), np.float32)
    for c in range(3):
        tex[:, :, c] = ndimage.map_coordinates(src[:, :, c], [SY, SX], order=1, mode='nearest')
    del src
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)).save(path('drape_full.png'))

    qx = (rX-X0)/(X1-X0)*TW; qy = (Y1-rY)/(Y1-Y0)*TH
    mimg = Image.new('L', (TW, TH), 0)
    ImageDraw.Draw(mimg).polygon(list(zip(qx, qy)), fill=255)
    np.save(path('mask_grid.npy'), np.asarray(mimg))
    json.dump(dict(X0=X0, X1=X1, Y0=Y0, Y1=Y1, TW=TW, TH=TH, NN=NN, F=FF, LON0=LON0R,
                   hmin=float(hgt.min()), hmax=float(hgt.max()), R=R_EARTH),
              open(path('grid.json'), 'w'), indent=1)

# ------------------------------------------------------------------ stage 5
def legend_ramp():
    """Sample the hypsometric swatches printed at the bottom of the sheet."""
    _, scan = fetch_map()
    im = np.asarray(Image.open(scan).convert('RGB')).astype(float)
    if im.shape[1] != 7500:                       # swatch box is located for the 7500 px scan
        raise SystemExit('legend sampling assumes SCAN_W = 7500')
    row   = im[4245:4265, 4550:5700].mean(0)
    paper = im[4180:4200, 4550:5700].mean((0, 1))
    on = np.nonzero(np.abs(row-paper).sum(1) > 18)[0]
    a, b, N = on.min(), on.max(), 17
    out = []
    for i in range(N):
        cx = int(4550 + a + (i+0.5)*(b-a)/N)
        out.append([int(round(v)) for v in im[4240:4270, cx-8:cx+8].reshape(-1, 3).mean(0)])
    return out

def encode():
    resample()
    g = json.load(open(path('grid.json')))
    X0, X1, Y0, Y1, TW, TH = g['X0'], g['X1'], g['Y0'], g['Y1'], g['TW'], g['TH']
    hgt = np.load(path('hgt_full.npy'))
    hmin, hmax = float(hgt.min()), float(hgt.max())

    z = HGT_W/TW
    p('· encoding the height raster (%d px wide)…' % HGT_W)
    hs = ndimage.zoom(ndimage.gaussian_filter(hgt, 0.35/z), z, order=1)
    hs = ndimage.gaussian_filter(hs, 0.5)
    HH, HW = hs.shape
    q  = np.round((hs-hmin)/(hmax-hmin)*4095).astype(np.uint16)   # 12-bit, ~0.9 m
    mask = ndimage.zoom((np.load(path('mask_grid.npy')) > 128).astype(np.float32), z, order=1) > .5
    sd = np.clip(128 + (ndimage.distance_transform_edt(mask)
                        - ndimage.distance_transform_edt(~mask))*8.0, 0, 255).astype(np.uint8)
    hm = np.dstack([(q >> 4).astype(np.uint8), ((q & 15) << 4).astype(np.uint8), sd])
    Image.fromarray(hm).save(os.path.join(BUILD, 'height.webp'), lossless=True,
                             quality=100, method=6)

    p('· encoding the drape…')
    Image.open(path('drape_full.png')).save(os.path.join(BUILD, 'drape.webp'),
                                            quality=88, method=6)

    # place names, snapped to the local summit where it matters
    mper = (X1-X0)*R_EARTH/TW
    def grid_uv(lon, lat):
        X, Y = lcc(lon, lat)
        return float((X-X0)/(X1-X0)), float((Y1-Y)/(Y1-Y0))
    def snap(lon, lat, radius_m):
        u, v = grid_uv(lon, lat)
        x, y = int(round(u*TW)), int(round(v*TH))
        if not radius_m: return u, v, float(hgt[y, x])
        r = max(1, int(radius_m/mper))
        w = hgt[y-r:y+r+1, x-r:x+r+1]
        j = np.unravel_index(np.argmax(w), w.shape)
        return (x-r+j[1])/TW, (y-r+j[0])/TH, float(w[j])

    peaks = []
    for n, la, lo, ft, rng in PEAKS:
        u, v, e = snap(lo, la, 1500)
        if abs(e - ft*0.3048) > 250:
            p('  ! %s is %.0f m off the model — check its coordinates' % (n, e - ft*0.3048))
        peaks.append(dict(n=n, u=round(u, 5), v=round(v, 5), ft=ft, r=rng, lat=la, lon=lo))
    cities = []
    for n, la, lo, t in CITIES:
        u, v, e = snap(lo, la, 0)
        cities.append(dict(n=n, u=round(u, 5), v=round(v, 5), t=t, lat=la, lon=lo,
                           ft=round(e/0.3048/10)*10))
    feats = []
    for n, la, lo, k in FEATURES:
        u, v, _ = snap(lo, la, 0)
        feats.append(dict(n=n, u=round(u, 5), v=round(v, 5), k=k, lat=la, lon=lo))

    ramp = legend_ramp()
    meta = dict(grid=dict(X0=X0, X1=X1, Y0=Y0, Y1=Y1, NN=NN, F=FF, LON0=g['LON0'], R=R_EARTH),
                tex=dict(w=TW, h=TH), hm=dict(w=int(HW), h=int(HH)),
                hmin=hmin, hmax=hmax,
                kmw=(X1-X0)*R_EARTH/1000.0, kmh=(Y1-Y0)*R_EARTH/1000.0,
                ramp=ramp, rampFt=[1500+500*i for i in range(len(ramp))],
                peaks=peaks, cities=cities, features=feats, tours=TOURS)
    json.dump(meta, open(os.path.join(BUILD, 'meta.json'), 'w'))
    for f in ('drape.webp', 'height.webp', 'meta.json'):
        p('  %-12s %6.2f MB' % (f, os.path.getsize(os.path.join(BUILD, f))/1e6))

STAGES = [('fetch', lambda: (fetch_map(), fetch_dem(), fetch_boundary())),
          ('mask', make_mask), ('fit', fit_projection),
          ('resample', resample), ('encode', encode)]

if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else STAGES[0][0]
    names = [n for n, _ in STAGES]
    if start not in names: raise SystemExit('stages: ' + ', '.join(names))
    for name, fn in STAGES[names.index(start):]:
        p('\n[%s]' % name); fn()
    p('\nnow: python3 src/assemble.py')
