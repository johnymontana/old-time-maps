#!/usr/bin/env python3
"""Check every summit in places.py against the model, and re-read GNIS.

Two tests, both of which a peak must pass to stay on the sheet:

  · the coordinate and the printed feet still match the GNIS record they
    were taken from (current file for the name and position, the 2021
    archive for the elevation — the live product no longer publishes one);
  · the highest Terrarium sample within 600 m of that point is within
    130 m of the claimed feet.

On a shield volcano the second test bites hard: a named cone on Mauna Loa's
flank sits on ground that keeps climbing past it, so the local maximum is
not the cone at all.  Those are dropped rather than argued with.

    python3 pipeline/verify.py          (after pipeline/build.py resample)
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(REPO, 'lib')); sys.path.insert(0, HERE)
import build
from places import PEAKS, CITIES, FEATURES, GNIS_NAME

g = build.make_grid()
hgt = np.load(build.path('hgt.npy'))
TH, TW = hgt.shape
gn = {}
for r in build.gnis_rows():
    gn.setdefault(r['n'], []).append(r)

def hunt(lon, lat, radius_m):
    u, v = g.uv(lon, lat)
    x = min(max(int(round(u*TW)), 0), TW-1)
    y = min(max(int(round(v*TH)), 0), TH-1)
    r = max(1, int(radius_m/g.m_per_texel))
    w = hgt[max(0, y-r):y+r+1, max(0, x-r):x+r+1]
    return float(w.max()), float(hgt[y, x])

bad = 0
print('%-24s %8s %8s %8s  %s' % ('peak', 'claim ft', 'model ft', 'Δ m', 'GNIS'))
for n, la, lo, ft, rng in PEAKS:
    key = GNIS_NAME.get(n, n)
    rec = gn.get(key)
    tag = '—'
    if not rec:
        tag = 'NOT IN GNIS'; bad += 1
    else:
        r = min(rec, key=lambda r: abs(r['lat']-la)+abs(r['lon']-lo))
        d = np.hypot((r['lat']-la)*110900, (r['lon']-lo)*105100)
        tag = '%s ok' % r['cls'] if d < 2 and r.get('ft') == ft else \
              'MISMATCH %s %.0fm ft=%s' % (r['cls'], d, r.get('ft'))
        if 'MISMATCH' in tag: bad += 1
    top600, at = hunt(lo, la, 600)
    top1500, _ = hunt(lo, la, 1500)
    d600 = top600 - ft*0.3048
    d1500 = top1500 - ft*0.3048
    flag = ''
    if abs(d600) > 130: flag += '  DROP (600 m hunt off by %.0f m)' % d600; bad += 1
    if abs(d1500) > 250: flag += '  SNAP-WARN (%.0f m)' % d1500
    print('%-24s %8d %8.0f %+8.0f  %s%s' % (n, ft, top600/0.3048, d600, tag, flag))

print()
for label, rows in (('city', CITIES), ('feature', FEATURES)):
    for t in rows:
        n, la, lo = t[0], t[1], t[2]
        key = GNIS_NAME.get(n, n)
        rec = gn.get(key)
        if not rec:
            print('  ! %s %r is not a GNIS name' % (label, n)); bad += 1; continue
        r = min(rec, key=lambda r: abs(r['lat']-la)+abs(r['lon']-lo))
        d = np.hypot((r['lat']-la)*110900, (r['lon']-lo)*105100)
        if d > 2:
            print('  ! %s %r is %.0f m from its GNIS point' % (label, n, d)); bad += 1
        oh, ah = build.wgs84_to_ohd(np.array([r['lon']]), np.array([r['lat']]))
        oh, ah = float(oh[0]), float(ah[0])
        if not (build.BLOCK[0] < oh < build.BLOCK[1] and
                build.BLOCK[2] < ah < build.BLOCK[3]):
            print('  ! %s %r is outside the neat (%.5f %.5f on the sheets\' graticule)'
                  % (label, n, oh, ah))
            bad += 1
        else:
            m = min((oh-build.BLOCK[0]), (build.BLOCK[1]-oh))*105100, \
                min((ah-build.BLOCK[2]), (build.BLOCK[3]-ah))*110900
            if min(m) < 400:
                print('  · %s %r is %.0f m inside the neat' % (label, n, min(m)))
print('\n%d problems' % bad)
