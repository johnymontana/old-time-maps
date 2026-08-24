#!/usr/bin/env python3
"""Ruler-grid crops for reading the plates' printed graticule by eye.

Both Nome plates are fitted from their PRINTED corners and crossings — there
is no georeferenced base to correlate against (the AK HTMC scans are
Transverse Mercator, which lib/georef rejects) — so the pixel position of
every graticule intersection is measured by vision from these crops:
magenta lines at every multiple of 100 plate-pixels, labelled in absolute
plate coordinates, rendered at 2× so a half-pixel is legible.

    python3 pipeline/measure.py            # writes work/m_*.png

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
    'plate-3': dict(TL=(275, 350), TR=(4875, 325), BL=(285, 5515), BR=(4875, 5500)),
    'plate-1': dict(TL=(310, 365), TR=(4825, 340), BL=(315, 5590), BR=(4815, 5565)),
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
# above (inner fine line = the graticule; the outer companion sits ~15-20 px
# outside it).  The rest of the 7 × 4 lattice of drawn 5' lines is seeded by
# bilinear interpolation and refined by a darkness-centroid profile, then
# cross-checked against the vision reads and the QA overlay.
CORNER_SEED = {   # (TL, TR, BL, BR) at (165°30'/00', 64°40'/25')
    'plate-3': ((313.3, 317.5), (4831.5, 322.5), (295.0, 5588.5), (4839.0, 5598.5)),
    'plate-1': ((322.5, 325.5), (4850.0, 347.0), (290.0, 5601.5), (4842.0, 5623.5)),
}
LONS = [-165.5 + i*(5/60.) for i in range(7)]          # 30' … 00'
LATS = [64.66667 - j*(5/60.) for j in range(4)]        # 40' … 25'

def refine(im, x0, y0, u, v, g=8, L=45, r=14):
    """Sub-pixel position of a graticule crossing near (x0, y0).

    im: float32 luminance.  u, v in [0,1] say which sides of the crossing
    are inside the map body (0/1 = on the west/north … edge)."""
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

def lattice(plate):
    im = np.asarray(Image.open(os.path.join(WORK, plate + '.jpg')).convert('L'),
                    dtype=np.float32)
    TL, TR, BL, BR = CORNER_SEED[plate]
    out = []
    for j, lat in enumerate(LATS):
        v = j/3.0
        for i, lon in enumerate(LONS):
            u = i/6.0
            sx = (1-u)*((1-v)*TL[0] + v*BL[0]) + u*((1-v)*TR[0] + v*BR[0])
            sy = (1-u)*((1-v)*TL[1] + v*BL[1]) + u*((1-v)*TR[1] + v*BR[1])
            X, Y = refine(im, sx, sy, u, v)
            out.append((round(lon, 6), round(lat, 5), round(X, 1), round(Y, 1),
                        round(X-sx, 1), round(Y-sy, 1)))
    return out

def final(plate):
    """The constants in build.py: two more refine rounds, each re-seeded from
    a deg-1 fit of the previous round, so a crossing that first caught the
    frame's companion line (they run ~15–20 px outside the graticule) is
    pulled back onto the net.  Points still >6 px off the final fit are the
    genuinely warped corners; build.py trims them the same way."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), 'lib'))
    from proj import Lcc
    from georef import Fit
    LCC = Lcc(64.47, 64.62, -165.25)
    im = np.asarray(Image.open(os.path.join(WORK, plate + '.jpg')).convert('L'),
                    dtype=np.float32)
    pts = lattice(plate)
    lon = np.array([p[0] for p in pts]); lat = np.array([p[1] for p in pts])
    PX = np.array([p[2] for p in pts]); PY = np.array([p[3] for p in pts])
    X, Y = LCC.fwd(lon, lat)
    for _ in range(2):
        f = Fit(X, Y, PX, PY, 1)
        qx, qy = f.apply(X, Y)
        for k in range(len(pts)):
            PX[k], PY[k] = refine(im, qx[k], qy[k], k % 7/6.0, k//7/3.0, r=8)
    return [(float(lon[k]), float(lat[k]), round(float(PX[k]), 1),
             round(float(PY[k]), 1)) for k in range(len(pts))]

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'fine':
        # fine: plate label cx cy   (4×, 20-px grid)
        _, _, plate, label, cx, cy = sys.argv
        ruler(plate, label, int(cx), int(cy), half=90, scale=4, step=20)
    elif len(sys.argv) > 1 and sys.argv[1] == 'profile':
        for plate in ('plate-3', 'plate-1'):
            print(plate)
            for row in lattice(plate):
                print('  (%.6f, %.5f): (%.1f, %.1f),   # moved %+.1f %+.1f' % row)
    elif len(sys.argv) > 1 and sys.argv[1] == 'final':
        # prints the GRAT3 / GRAT1 tables exactly as pasted into build.py
        for plate in ('plate-3', 'plate-1'):
            print(plate)
            for row in final(plate):
                print('    (%.6f, %.5f, %.1f, %.1f),' % row)
    else:
        for plate, spots in CROPS.items():
            for label, (cx, cy) in spots.items():
                ruler(plate, label, cx, cy)
