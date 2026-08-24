"""Encode a sheet's three assets: drape.webp, height.webp, meta.json.

Same packing as the montana build: height is 12-bit elevation in R+G-high,
signed distance to the sheet/park boundary in B (texels × 8, biased 128);
the viewer decodes both into a half-float RG texture.
"""
import json, os

import numpy as np
from PIL import Image
from scipy import ndimage

def encode_height(hgt, mask, out_path, hgt_w, log=print):
    """hgt: float32 metres on the grid; mask: bool inside-sheet on the grid."""
    TH, TW = hgt.shape
    hmin, hmax = float(hgt.min()), float(hgt.max())
    z = hgt_w/TW
    log('· encoding the height raster (%d px wide)…' % hgt_w)
    hs = ndimage.zoom(ndimage.gaussian_filter(hgt, 0.35/z), z, order=1)
    hs = ndimage.gaussian_filter(hs, 0.5)
    HH, HW = hs.shape
    q = np.round((hs-hmin)/(hmax-hmin)*4095).astype(np.uint16)
    m = ndimage.zoom(mask.astype(np.float32), z, order=1) > .5
    sd = np.clip(128 + (ndimage.distance_transform_edt(m)
                        - ndimage.distance_transform_edt(~m))*8.0, 0, 255).astype(np.uint8)
    hm = np.dstack([(q >> 4).astype(np.uint8), ((q & 15) << 4).astype(np.uint8), sd])
    Image.fromarray(hm).save(out_path, lossless=True, quality=100, method=6)
    return HW, HH, hmin, hmax

def encode_drape(tex, out_path, quality=88, log=print):
    log('· encoding the drape…')
    Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8)).save(
        out_path, quality=quality, method=6)

class Grid:
    """A sheet's conic grid: extents in LCC units + texture size + sampler."""
    def __init__(self, lcc, X0, X1, Y0, Y1, TW, R=6371000.0):
        self.lcc = lcc
        self.X0, self.X1, self.Y0, self.Y1 = X0, X1, Y0, Y1
        self.TW = TW
        self.TH = int(round(TW*(Y1-Y0)/(X1-X0)))
        self.R = R
        self.kmw = (X1-X0)*R/1e3
        self.kmh = (Y1-Y0)*R/1e3
        self.m_per_texel = (X1-X0)*R/TW

    @classmethod
    def around(cls, lcc, lons, lats, margin, TW):
        X, Y = lcc.fwd(np.asarray(lons, float), np.asarray(lats, float))
        return cls(lcc, X.min()-margin, X.max()+margin, Y.min()-margin, Y.max()+margin, TW)

    def lonlat(self):
        gx = self.X0 + (np.arange(self.TW)+0.5)*(self.X1-self.X0)/self.TW
        gy = self.Y1 - (np.arange(self.TH)+0.5)*(self.Y1-self.Y0)/self.TH
        GX, GY = np.meshgrid(gx, gy)
        LON, LAT = self.lcc.inv(GX, GY)
        return GX, GY, LON, LAT

    def uv(self, lon, lat):
        X, Y = self.lcc.fwd(lon, lat)
        return ((X-self.X0)/(self.X1-self.X0), (self.Y1-Y)/(self.Y1-self.Y0))

    def px(self, lon, lat):
        u, v = self.uv(lon, lat)
        return u*self.TW, v*self.TH

    def meta(self):
        return dict(X0=self.X0, X1=self.X1, Y0=self.Y0, Y1=self.Y1,
                    NN=self.lcc.n, F=self.lcc.f,
                    LON0=float(np.radians(self.lcc.lon0_deg)), R=self.R)

def snap_places(grid, hgt, peaks, cities, features, log=print):
    """montana-style label records, peaks snapped to the local summit."""
    TH, TW = hgt.shape
    def snap(lon, lat, radius_m):
        u, v = grid.uv(lon, lat)
        x = min(max(int(round(u*TW)), 0), TW-1)
        y = min(max(int(round(v*TH)), 0), TH-1)
        if not radius_m: return u, v, float(hgt[y, x])
        r = max(1, int(radius_m/grid.m_per_texel))
        w = hgt[max(0, y-r):y+r+1, max(0, x-r):x+r+1]
        j = np.unravel_index(np.argmax(w), w.shape)
        return (max(0, x-r)+j[1])/TW, (max(0, y-r)+j[0])/TH, float(w[j])
    P = []
    for n, la, lo, ft, rng in peaks:
        u, v, e = snap(lo, la, 1500)
        if abs(e - ft*0.3048) > 250:
            log('  ! %s is %.0f m off the model — check its coordinates' % (n, e-ft*0.3048))
        P.append(dict(n=n, u=round(u, 5), v=round(v, 5), ft=ft, r=rng, lat=la, lon=lo))
    C = []
    for n, la, lo, t in cities:
        u, v, e = snap(lo, la, 0)
        C.append(dict(n=n, u=round(u, 5), v=round(v, 5), t=t, lat=la, lon=lo,
                      ft=round(e/0.3048/10)*10))
    F = []
    for n, la, lo, k in features:
        u, v, _ = snap(lo, la, 0)
        F.append(dict(n=n, u=round(u, 5), v=round(v, 5), k=k, lat=la, lon=lo))
    return P, C, F

def write_meta(build_dir, grid, hm_size, hmin, hmax, ramp, ramp_ft,
               peaks, cities, features, tours, log=print, **extra):
    meta = dict(grid=grid.meta(), tex=dict(w=grid.TW, h=grid.TH),
                hm=dict(w=hm_size[0], h=hm_size[1]), hmin=hmin, hmax=hmax,
                kmw=grid.kmw, kmh=grid.kmh, ramp=ramp, rampFt=ramp_ft,
                peaks=peaks, cities=cities, features=features, tours=tours)
    meta.update(extra)
    json.dump(meta, open(os.path.join(build_dir, 'meta.json'), 'w'))
    for f in ('drape.webp', 'height.webp', 'meta.json'):
        p = os.path.join(build_dir, f)
        if os.path.exists(p):
            log('  %-12s %6.2f MB' % (f, os.path.getsize(p)/1e6))
