"""Terrarium elevation tiles: fetch, mosaic, sample.

Tiles land in a cache shared by every sheet (repo-root work/dem/, gitignored;
override with OTM_DEM_CACHE) so two sheets over the same country never
download the same tile twice.
"""
import math, os, urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image
from scipy import ndimage

from proj import merc_x, merc_y

TERRARIUM = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'

def _cache_dir():
    d = os.environ.get('OTM_DEM_CACHE')
    if not d:
        d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'work', 'dem')
    os.makedirs(d, exist_ok=True)
    return d

def tile_range(box, zoom):
    W, E, S, N = box
    x0, x1 = int(math.floor(merc_x(W, zoom))), int(math.floor(merc_x(E, zoom)))
    y0, y1 = int(math.floor(merc_y(N, zoom))), int(math.floor(merc_y(S, zoom)))
    return x0, x1, y0, y1

def fetch(box, zoom, log=print):
    """Download any missing tiles for box=(W,E,S,N); returns (x0,x1,y0,y1)."""
    d = _cache_dir()
    x0, x1, y0, y1 = tile_range(box, zoom)
    tiles = [(x, y) for x in range(x0, x1+1) for y in range(y0, y1+1)]
    todo = [t for t in tiles
            if not os.path.exists(os.path.join(d, '%d_%d_%d.png' % (zoom, *t)))]
    if todo:
        log('· downloading %d Terrarium tiles (z%d)…' % (len(todo), zoom))
        def get(t):
            url = TERRARIUM.format(z=zoom, x=t[0], y=t[1])
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(url, timeout=40) as r:
                        data = r.read()
                    open(os.path.join(d, '%d_%d_%d.png' % (zoom, *t)), 'wb').write(data)
                    return
                except Exception:
                    if attempt == 3: raise
        with ThreadPoolExecutor(24) as ex:
            list(ex.map(get, todo))
    else:
        log('· DEM tiles cached (z%d)' % zoom)
    return x0, x1, y0, y1

def mosaic(box, zoom, clamp, log=print):
    """Decode the tiles into one float32 metre array; repair voids, soften.

    clamp=(lo, hi): elevations outside are treated as voids and infilled.
    Returns (elev, x0, y0) where pixel (r, c) is web-mercator
    (x0*256+c, y0*256+r) at this zoom.
    """
    d = _cache_dir()
    x0, x1, y0, y1 = fetch(box, zoom, log)
    MW, MH = (x1-x0+1)*256, (y1-y0+1)*256
    log('· mosaicking %d × %d elevation samples…' % (MW, MH))
    mos = np.zeros((MH, MW), np.float32)
    for tx in range(x0, x1+1):
        for ty in range(y0, y1+1):
            a = np.asarray(Image.open(os.path.join(d, '%d_%d_%d.png' % (zoom, tx, ty)))
                           .convert('RGB'), dtype=np.float32)
            mos[(ty-y0)*256:(ty-y0+1)*256, (tx-x0)*256:(tx-x0+1)*256] = \
                a[:, :, 0]*256 + a[:, :, 1] + a[:, :, 2]/256 - 32768
    bad = (mos < clamp[0]) | (mos > clamp[1])
    if bad.any():
        log('  repairing %d void samples' % int(bad.sum()))
        ind = ndimage.distance_transform_edt(bad, return_indices=True,
                                             return_distances=False)
        mos = mos[tuple(ind)]
    return ndimage.gaussian_filter(mos, 0.9), x0, y0

def sample(mos, x0, y0, zoom, LON, LAT):
    """Bilinear elevations at WGS84 lon/lat grids, from a mosaic() result."""
    px = (merc_x(LON, zoom) - x0)*256
    py = (merc_y(LAT, zoom) - y0)*256
    assert px.min() > 1 and px.max() < mos.shape[1]-2 and \
           py.min() > 1 and py.max() < mos.shape[0]-2, \
        'DEM box too small for the grid — widen it'
    return ndimage.map_coordinates(mos, [py, px], order=1, mode='nearest') \
                  .astype(np.float32)
