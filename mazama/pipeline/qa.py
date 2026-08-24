#!/usr/bin/env python3
"""Independent check of the printed-graticule fit against a modern quadrangle.

The sheet is registered from Kerr's printed 5' net and nothing else.  That
leaves an honest question the About panel has to answer with a number: how far
does an 1886 triangulation, taken at face value on a 1902 lithograph, land
from modern ground?

This script answers it with the one feature both maps draw the same way — the
shoreline of Crater Lake.  It resamples the USGS *Crater Lake West* and
*Crater Lake East* 7.5' quadrangles (1985, scans 279504 / 279501) onto this
sheet's own conic grid, lifts the lake from each by colour, and reports:

  * the offset between the two lake centroids,
  * the rigid shift that best overlaps them, and the overlap before and after,
  * the mean distance from the 1886 shoreline to the modern one.

The 1985 quads are Lambert conformal conic on NAD27 (GeoKey 3075 = 8), not
the polyconic that lib/georef.QuadGeoref reads, so the projection is rebuilt
here from the file's own geokeys — Snyder's ellipsoidal LCC 2SP on Clarke
1866, with the quad's per-sheet false origin.  Nothing in this module feeds
the build; it only produces numbers and work/qa_shoreline.png.

    python3 pipeline/qa.py
"""
import json, math, os, sys, urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
from proj import wgs84_to_nad27
from build import make_grid, path, WORK, BLOCK, p

S3 = ('https://prd-tnm.s3.amazonaws.com/StagedProducts/Maps/HistoricalTopo/'
      'GeoTIFF/OR/')
QUADS = {'htmc_cl_west_1985.tif': 'OR_Crater%20Lake%20West_279504_1985_24000_geo.tif',
         'htmc_cl_east_1985.tif': 'OR_Crater%20Lake%20East_279501_1985_24000_geo.tif'}


class LccQuad:
    """Embedded georeference of an HTMC quad staged as Lambert conformal conic.

    Snyder, *Map Projections — A Working Manual*, eqs. 15-1..15-9a, forward,
    on the ellipsoid named by the file's own geokeys (Clarke 1866 / NAD27 for
    every OR sheet checked)."""

    def __init__(self, pil_image):
        t = pil_image.tag_v2
        sx, sy = t[33550][0], t[33550][1]
        _, _, _, gx, gy, _ = t[33922]
        self.scale = (sx, sy); self.origin = (gx, gy)
        k = self._geokeys(t)
        if k.get(3075) != 8:
            raise ValueError('expected LCC 2SP (geokey 3075 = 8), got %r' % k.get(3075))
        self.a = float(k.get(2057, 6378206.4))
        invf = float(k.get(2059, 294.9786982138982))
        self.datum = k.get(2049, 'NAD27')
        sp1, sp2 = math.radians(k[3078]), math.radians(k[3079])
        self.lon0 = math.radians(k[3084]); lat0 = math.radians(k[3085])
        self.fe, self.fn = float(k.get(3086, 0.0)), float(k.get(3087, 0.0))
        f = 1.0/invf; self.e = math.sqrt(2*f - f*f)
        m = lambda phi: math.cos(phi)/math.sqrt(1 - (self.e*math.sin(phi))**2)
        self.n = (math.log(m(sp1)) - math.log(m(sp2))) / \
                 (math.log(self._t(sp1)) - math.log(self._t(sp2)))
        self.F = m(sp1)/(self.n*self._t(sp1)**self.n)
        self.rho0 = self.a*self.F*self._t(lat0)**self.n

    def _t(self, phi):
        es = self.e*math.sin(phi)
        return math.tan(math.pi/4 - phi/2)/((1-es)/(1+es))**(self.e/2)

    @staticmethod
    def _geokeys(tags):
        kd = tags.get(34735)
        if not kd: raise ValueError('no GeoKeyDirectory tag')
        dbl = tags.get(34736, ()); asc = tags.get(34737, '')
        keys = {}
        for i in range(4, len(kd), 4):
            kid, loc, cnt, val = kd[i:i+4]
            if loc == 0: keys[kid] = val
            elif loc == 34736: keys[kid] = dbl[val] if cnt == 1 else dbl[val:val+cnt]
            elif loc == 34737: keys[kid] = asc[val:val+cnt].rstrip('|')
        return keys

    def to_px(self, lon, lat):
        lon = np.asarray(lon, float); lat = np.asarray(lat, float)
        es = self.e*np.sin(np.radians(lat))
        tt = np.tan(np.pi/4 - np.radians(lat)/2)/np.power((1-es)/(1+es), self.e/2)
        rho = self.a*self.F*np.power(tt, self.n)
        th = self.n*(np.radians(lon) - self.lon0)
        x = self.fe + rho*np.sin(th)
        y = self.fn + self.rho0 - rho*np.cos(th)
        return ((x - self.origin[0])/self.scale[0], (self.origin[1] - y)/self.scale[1])


def ensure(name):
    f = path(name)
    if not os.path.exists(f):
        p('· downloading %s…' % name)
        req = urllib.request.Request(S3 + QUADS[name], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=900) as r:
            open(f, 'wb').write(r.read())
    return f


def modern_lake(grid):
    """Crater Lake as the 1985 quads draw it, on this sheet's grid."""
    _, _, LON, LAT = grid.lonlat()
    nlon, nlat = wgs84_to_nad27(LON, LAT)
    out = np.zeros(LON.shape, bool); seen = np.zeros(LON.shape, bool)
    for name in QUADS:
        im = Image.open(ensure(name))
        q = LccQuad(im)
        src = np.asarray(im.convert('RGB'), np.float32)
        X, Y = q.to_px(nlon, nlat)
        ok = (X > 1) & (X < src.shape[1]-2) & (Y > 1) & (Y < src.shape[0]-2)
        idx = [Y[ok], X[ok]]
        rgb = np.stack([ndimage.map_coordinates(src[:, :, c], idx, order=1) for c in range(3)], -1)
        # the quads print open water as a flat cyan wash
        water = (rgb[:, 2] - rgb[:, 0] > 22) & (rgb[:, 1] > 120) & (rgb[:, 2] > 150)
        out[ok] |= water; seen[ok] = True
        del src
    out = ndimage.binary_closing(out, np.ones((5, 5), bool))
    lab, n = ndimage.label(out)
    if n:
        sizes = ndimage.sum(out, lab, range(1, n+1))
        out = lab == (int(np.argmax(sizes)) + 1)
    return ndimage.binary_fill_holes(out), seen


def plate_lake(grid):
    """Crater Lake as Plate I draws it: the closed pale field inside the
    shoreline, flood-filled from the lake's centre on the drape itself.

    The drawn 5' graticule crosses the water, so the filled field is nicked by
    two hairline strips; a closing of eleven texels (~130 m) heals them without
    touching the shoreline, which is nowhere that thin."""
    tex = np.load(path('drape.npy')).astype(np.float32)
    g = tex.mean(2)
    ink = (ndimage.uniform_filter(g, 31) - g) > 16
    free = ~ndimage.binary_dilation(ink, np.ones((3, 3), bool))
    u, v = grid.uv(-122.106390, 42.942012)                      # GNIS Crater Lake
    lab, _ = ndimage.label(free)
    seed = lab[int(v*grid.TH), int(u*grid.TW)]
    lake = ndimage.binary_fill_holes(lab == seed)
    lake = ndimage.binary_closing(lake, np.ones((11, 11), bool))
    return ndimage.binary_fill_holes(lake)


def rim(mask):
    return mask ^ ndimage.binary_erosion(mask)


def main():
    g = make_grid()
    if not os.path.exists(path('drape.npy')):
        raise SystemExit('run pipeline/build.py resample first')
    p('· lifting Crater Lake from the 1985 quadrangles…')
    modern, seen = modern_lake(g)
    p('  %d texels of open water' % modern.sum())
    p('· lifting Crater Lake from Plate I…')
    plate = plate_lake(g)
    p('  %d texels inside the 1886 shoreline' % plate.sum())
    mpt = g.m_per_texel

    cy1, cx1 = ndimage.center_of_mass(plate)
    cy2, cx2 = ndimage.center_of_mass(modern)
    dx, dy = (cx1-cx2)*mpt, (cy1-cy2)*mpt
    p('\n  1886 lake centroid vs 1985: %+.0f m east, %+.0f m south (%.0f m)'
      % (dx, -dy, math.hypot(dx, dy)))
    p('  1886 area %.2f km²   1985 area %.2f km²'
      % (plate.sum()*mpt*mpt/1e6, modern.sum()*mpt*mpt/1e6))

    # mean signed distance from the 1886 shoreline to the modern water body
    dist = ndimage.distance_transform_edt(~modern) - ndimage.distance_transform_edt(modern)
    edge = rim(plate)
    d = dist[edge]*mpt
    p('  1886 shoreline vs 1985 shoreline: mean %+.0f m, |mean| %.0f m, '
      'median |d| %.0f m, 90th pct %.0f m'
      % (d.mean(), abs(d).mean(), np.median(abs(d)), np.percentile(abs(d), 90)))

    best = None
    for oy in range(-24, 25):
        for ox in range(-24, 25):
            s = np.roll(np.roll(plate, oy, 0), ox, 1)
            iou = (s & modern).sum()/float((s | modern).sum())
            if best is None or iou > best[0]: best = (iou, ox, oy)
    iou0 = (plate & modern).sum()/float((plate | modern).sum())
    p('  overlap as fitted: IoU %.3f   best rigid shift %+d, %+d texels '
      '(%+.0f m east, %+.0f m south) -> IoU %.3f'
      % (iou0, best[1], best[2], best[1]*mpt, -best[2]*mpt, best[0]))

    h, w = plate.shape
    rgb = np.zeros((h, w, 3), np.uint8); rgb[:] = 250
    rgb[modern] = (150, 190, 230)
    rgb[rim(plate)] = (200, 40, 40)
    Image.fromarray(rgb).resize((w//2, h//2)).save(path('qa_shoreline.png'))
    p('\n  work/qa_shoreline.png — red is Kerr 1886, blue is the 1985 quads')


if __name__ == '__main__':
    main()
