"""Georeferencing: GeoTIFF passthrough and polynomial GCP fits.

Two ways a sheet learns where it is:

    QuadGeoref   reads the transform embedded in an HTMC/TopoView GeoTIFF
                 (polyconic on NAD27 is what the series uses) — strategy A
    fit_poly     least-squares polynomial from control points whose true
                 coordinates are printed on the sheet (neatline corners,
                 graticule intersections) — strategies B and C
"""
import numpy as np
from PIL import Image, ImageDraw

from proj import polyconic, poly_basis

# ------------------------------------------------- GeoTIFF embedded georef
def _geokeys(tags):
    kd = tags.get(34735)
    if not kd: raise ValueError('no GeoKeyDirectory tag — not a GeoTIFF')
    dbl = tags.get(34736, ())
    asc = tags.get(34737, '')
    keys = {}
    for i in range(4, len(kd), 4):
        kid, loc, cnt, val = kd[i:i+4]
        if loc == 0:            keys[kid] = val
        elif loc == 34736:      keys[kid] = dbl[val] if cnt == 1 else dbl[val:val+cnt]
        elif loc == 34737:      keys[kid] = asc[val:val+cnt].rstrip('|')
    return keys

class QuadGeoref:
    """Embedded georeference of an HTMC quad scan (polyconic / NAD27)."""
    def __init__(self, pil_image):
        t = pil_image.tag_v2
        sx, sy = t[33550][0], t[33550][1]
        _, _, _, gx, gy, _ = t[33922]
        self.scale = (sx, sy)
        self.origin = (gx, gy)                    # map metres at pixel (0,0)
        k = _geokeys(t)
        if k.get(1024) != 1 or k.get(3075) != 22:
            raise ValueError('expected a projected polyconic GeoTIFF, got keys %r' % k)
        self.lon0 = float(k[3080]); self.lat0 = float(k[3081])
        self.datum = k.get(2049, 'NAD27')

    def to_px(self, lon, lat):
        """NAD27 lon/lat → scan pixel (x right, y down)."""
        x, y = polyconic(lon, lat, self.lon0, self.lat0)
        return ((x - self.origin[0])/self.scale[0],
                (self.origin[1] - y)/self.scale[1])

# ---------------------------------------------------------------- GCP fits
class Fit:
    """px = poly(deg) of normalised projected coordinates."""
    def __init__(self, X, Y, PX, PY, deg):
        X = np.asarray(X, float); Y = np.asarray(Y, float)
        self.Xm, self.Ym, self.sX = X.mean(), Y.mean(), max(X.std(), 1e-12)
        A = poly_basis((X-self.Xm)/self.sX, (Y-self.Ym)/self.sX, deg)
        self.cx, res_x, *_ = np.linalg.lstsq(A, np.asarray(PX, float), rcond=None)
        self.cy, res_y, *_ = np.linalg.lstsq(A, np.asarray(PY, float), rcond=None)
        self.deg = deg
        px, py = self.apply(X, Y)
        d = np.hypot(px-PX, py-PY)
        self.rms, self.median, self.worst = float(np.sqrt((d*d).mean())), \
            float(np.median(d)), float(d.max())

    def apply(self, X, Y):
        A = poly_basis((np.asarray(X, float)-self.Xm)/self.sX,
                       (np.asarray(Y, float)-self.Ym)/self.sX, self.deg)
        return A@self.cx, A@self.cy

def fit_report(name, fit, ground_m_per_px=None):
    s = '  %s: deg %d  rms %.2f px  median %.2f px  worst %.2f px' % (
        name, fit.deg, fit.rms, fit.median, fit.worst)
    if ground_m_per_px:
        s += '  (~%.0f m rms on the ground)' % (fit.rms*ground_m_per_px)
    print(s, flush=True)

# -------------------------------------------------------------- QA overlay
def overlay(im, groups, path, width=1600):
    """Draw point groups {colour: [(x, y), …]} on a resized copy of im."""
    out = im.convert('RGB').copy()
    s = min(1.0, width/out.width)
    out = out.resize((int(out.width*s), int(out.height*s)), Image.BILINEAR)
    d = ImageDraw.Draw(out)
    for colour, pts in groups.items():
        for x, y in pts:
            x, y = x*s, y*s
            d.line([(x-7, y), (x+7, y)], fill=colour, width=2)
            d.line([(x, y-7), (x, y+7)], fill=colour, width=2)
    out.save(path)
    return path
