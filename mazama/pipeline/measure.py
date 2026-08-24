#!/usr/bin/env python3
"""Ruler-grid crops for reading the plates' printed graticule by eye.

Both Professional Paper 3 plates are fitted from their PRINTED graticule —
there is no early georeferenced base to correlate against (HTMC's oldest
Crater Lake sheets are 1985 24k / 1989 100k, ninety-nine years younger than
Kerr's survey) — so the pixel position of every graticule intersection is
measured by vision from these crops: magenta lines at every multiple of 100
plate-pixels, labelled in absolute plate coordinates, rendered at 2x so a
half-pixel is legible.

    python3 pipeline/measure.py            # writes work/m_*.png
    python3 pipeline/measure.py profile    # seeded darkness-centroid lattice
    python3 pipeline/measure.py final      # the tables pasted into build.py

Edit CROPS between rounds: first the four corners (coarse guesses), then
the interior 5' crossings predicted from the corner fit.
"""
import os
import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(os.path.dirname(HERE), 'work')

# label -> (cx, cy) estimated centre of the graticule intersection, plate px
CROPS = {
    'plate-1': dict(TL=(155, 142), TR=(2093, 142), BL=(155, 2636), BR=(2093, 2636)),
    'plate-6': dict(TL=(160, 145), TR=(2160, 145), BL=(160, 2700), BR=(2160, 2700)),
}
HALF = 230        # crop half-size, plate px
SCALE = 2         # rendered magnification


def ruler(plate, label, cx, cy, half=HALF, scale=SCALE, step=100):
    im = Image.open(os.path.join(WORK, plate + '.jpg'))
    x0, y0 = max(0, cx-half), max(0, cy-half)
    crop = im.crop((x0, y0, min(im.width, cx+half), min(im.height, cy+half)))
    crop = crop.resize((crop.width*scale, crop.height*scale), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    M = (255, 0, 220)
    for gx in range((x0//step+1)*step, x0 + crop.width//scale, step):
        X = (gx-x0)*scale
        d.line([(X, 0), (X, crop.height)], fill=M, width=1)
        d.text((X+3, 3), str(gx), fill=M)
    for gy in range((y0//step+1)*step, y0 + crop.height//scale, step):
        Y = (gy-y0)*scale
        d.line([(0, Y), (crop.width, Y)], fill=M, width=1)
        d.text((3, Y+3), str(gy), fill=M)
    out = os.path.join(WORK, 'm_%s_%s.png' % (plate, label))
    crop.save(out)
    print(out)


# ---------------------------------------------------------------- profiler
# The four corner seeds per plate are VISION READS from the ruler crops
# above (the neat corner is the graticule corner: 122 deg 16' / 122 deg 00'
# by 43 deg 04' / 42 deg 48').  The rest of the drawn lattice is seeded by
# bilinear interpolation and refined by a darkness-centroid profile, then
# cross-checked against the QA overlay.  Note the LONS are NOT evenly
# spaced: the sheet's west neat falls on 16', one minute west of the first
# drawn 5' meridian.
CORNER_SEED = {   # (TL, TR, BL, BR)
    'plate-1': ((234.0, 156.0), (2068.0, 156.0), (234.0, 2651.0), (2068.0, 2651.0)),
    'plate-6': ((178.0, 160.0), (2007.0, 160.0), (178.0, 2630.0), (2007.0, 2630.0)),
}
LONS = [-122.0 - m/60.0 for m in (16, 15, 10, 5, 0)]
LATS = [43.0 + m/60.0 for m in (4, 0, -5, -10, -12)]


def refine(im, x0, y0, u, v, g=8, L=45, r=14):
    """Sub-pixel position of a graticule crossing near (x0, y0).

    im: float32 luminance.  u, v in [0,1] say which sides of the crossing
    are inside the map body (0/1 = on the west/north ... edge)."""
    H, W = im.shape
    def band(c, lo_ok, hi_ok):
        rows = []
        if lo_ok: rows.append((int(c)-g-L, int(c)-g))
        if hi_ok: rows.append((int(c)+g, int(c)+g+L))
        return rows
    # vertical line: average over row bands, profile across columns
    acc = np.zeros(2*r+1); n = 0
    for (a, b) in band(y0, v > 0.001, v < 0.999):
        seg = im[max(0, a):b, int(x0)-r:int(x0)+r+1]
        if seg.shape == (b-max(0, a), 2*r+1): acc += seg.mean(0); n += 1
    px = acc/n
    i = int(np.argmin(px[2:-2])) + 2
    d = (px[i-1]-px[i+1])/(2*(px[i-1]-2*px[i]+px[i+1])+1e-9)
    X = int(x0)-r + i + np.clip(d, -1, 1)
    # horizontal line
    acc = np.zeros(2*r+1); n = 0
    for (a, b) in band(x0, u > 0.001, u < 0.999):
        seg = im[int(y0)-r:int(y0)+r+1, max(0, a):b]
        if seg.shape == (2*r+1, b-max(0, a)): acc += seg.mean(1); n += 1
    py = acc/n
    j = int(np.argmin(py[2:-2])) + 2
    d = (py[j-1]-py[j+1])/(2*(py[j-1]-2*py[j]+py[j+1])+1e-9)
    Y = int(y0)-r + j + np.clip(d, -1, 1)
    return float(X), float(Y)


def _seed_grid(plate):
    """Bilinear seeds at the drawn lattice, in the sheet's own u/v fractions."""
    TL, TR, BL, BR = CORNER_SEED[plate]
    lo0, lo1 = LONS[0], LONS[-1]
    la0, la1 = LATS[0], LATS[-1]
    out = []
    for lat in LATS:
        v = (la0-lat)/(la0-la1)
        for lon in LONS:
            u = (lon-lo0)/(lo1-lo0)
            sx = (1-u)*((1-v)*TL[0] + v*BL[0]) + u*((1-v)*TR[0] + v*BR[0])
            sy = (1-u)*((1-v)*TL[1] + v*BL[1]) + u*((1-v)*TR[1] + v*BR[1])
            out.append((lon, lat, u, v, sx, sy))
    return out


def lattice(plate):
    im = np.asarray(Image.open(os.path.join(WORK, plate + '.jpg')).convert('L'),
                    dtype=np.float32)
    out = []
    for lon, lat, u, v, sx, sy in _seed_grid(plate):
        X, Y = refine(im, sx, sy, u, v)
        out.append((round(lon, 6), round(lat, 6), round(X, 1), round(Y, 1),
                    round(X-sx, 1), round(Y-sy, 1)))
    return out


def final(plate, rounds=2, r=8):
    """The constants in build.py: two more refine rounds, each re-seeded from
    a deg-1 fit of the previous round, so a crossing that first caught a
    contour or a label is pulled back onto the net.  Points still far off the
    final fit are trimmed the same way build.py trims them."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'lib'))
    from proj import Lcc
    from georef import Fit
    LCC = Lcc(42.85, 43.02, -122.13)
    im = np.asarray(Image.open(os.path.join(WORK, plate + '.jpg')).convert('L'),
                    dtype=np.float32)
    seeds = _seed_grid(plate)
    pts = lattice(plate)
    lon = np.array([p[0] for p in pts]); lat = np.array([p[1] for p in pts])
    PX = np.array([p[2] for p in pts]); PY = np.array([p[3] for p in pts])
    X, Y = LCC.fwd(lon, lat)
    for _ in range(rounds):
        f = Fit(X, Y, PX, PY, 1)
        qx, qy = f.apply(X, Y)
        for k, (_, _, u, v, _, _) in enumerate(seeds):
            PX[k], PY[k] = refine(im, qx[k], qy[k], u, v, r=r)
    return [(float(lon[k]), float(lat[k]), round(float(PX[k]), 1),
             round(float(PY[k]), 1)) for k in range(len(pts))]


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'fine':
        # fine: plate label cx cy   (4x, 20-px grid)
        _, _, plate, label, cx, cy = sys.argv
        ruler(plate, label, int(cx), int(cy), half=90, scale=4, step=20)
    elif len(sys.argv) > 1 and sys.argv[1] == 'profile':
        for plate in ('plate-1', 'plate-6'):
            print(plate)
            for row in lattice(plate):
                print('  (%.6f, %.6f): (%.1f, %.1f),   # moved %+.1f %+.1f' % row)
    elif len(sys.argv) > 1 and sys.argv[1] == 'final':
        # prints the GRAT1 / GRAT6 tables exactly as pasted into build.py
        for plate in ('plate-1', 'plate-6'):
            print(plate)
            for row in final(plate):
                print('    (%.6f, %.6f, %.1f, %.1f),' % row)
    else:
        for plate, spots in CROPS.items():
            for label, (cx, cy) in spots.items():
                ruler(plate, label, cx, cy)
