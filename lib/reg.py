"""Registration by correlation against already-georeferenced rasters.

The move that georeferenced the Glacier sheet, made reusable: a scan with no
usable graticule is aligned to one or more reference rasters whose georef is
known (HTMC quads, or another sheet this pipeline already fitted).  Stage A
finds each reference's global similarity by a scale sweep at 1/8 resolution;
stage B correlates feature patches at full resolution around a lon/lat grid,
yielding control points for a trimmed polynomial fit.

Feature masks keep only linework both editions share — black culture and
(optionally) blue drainage — so recolouring between editions doesn't matter.
"""
import math

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.signal import fftconvolve

from georef import Fit, fit_report


def feature_mask(rgb, blue=True):
    """Linework shared between editions: black ink, optionally blue drainage."""
    mx = rgb.max(2).astype(np.int16); mn = rgb.min(2).astype(np.int16)
    mean = rgb.mean(2, dtype=np.float32)
    m = (255.0 - mean - 1.2*(mx-mn)) > 90
    if blue:
        b = rgb[:, :, 2].astype(np.float32)
        m = m | ((b - 0.5*rgb[:, :, 0] - 0.5*rgb[:, :, 1]) > 16)
    return m


def smooth_feature(rgb, blue=True):
    return ndimage.gaussian_filter(feature_mask(rgb, blue).astype(np.float32), 1.5)


def register(scan_f, targets, lcc, lons, lats, m_scan_hint=None,
             z_lo=0.80, z_hi=1.22, pw=120, sw=90, ambig=0.86,
             seed_fit=None, scan_A=None, log=print):
    """Correlate scan_f (smoothed feature raster) against reference targets.

    targets: iterable of dicts with
        name    — for logging
        feat    — the reference's smoothed feature raster
        to_px   — fn(lon, lat) -> (x, y) into feat
        m_per_px— the reference's ground resolution
    lons/lats: 1-D arrays of candidate control-point coordinates.
    Returns (X, Y, gx, gy, m_per_px) — chart coords and scan pixels of the
    accepted control points, plus the consensus scan resolution.
    """
    D = 8
    scan_8 = (scan_A if scan_A is not None else scan_f)[::D, ::D].copy()
    gx, gy, gl, scales = [], [], [], []
    for t in targets:
        qf = t['feat']
        if seed_fit is None:
            q8 = t.get('featA', qf)[::D, ::D].copy()
            bestA = None
            z_range = np.arange(z_lo, z_hi+0.001, 0.02)
            if len(scales) >= 1:
                zc = t['m_per_px']/float(np.median(scales))
                z_range = np.arange(zc-0.021, zc+0.022, 0.01)
            elif m_scan_hint:
                zc = t['m_per_px']/m_scan_hint
                z_range = np.arange(max(z_lo, zc-0.13), min(z_hi, zc+0.13)+0.001, 0.02)
            for z in z_range:
                qz = ndimage.zoom(q8, z, order=1)
                if qz.shape[0] >= scan_8.shape[0] or qz.shape[1] >= scan_8.shape[1]:
                    continue
                corr = fftconvolve(scan_8 - scan_8.mean(),
                                   (qz - qz.mean())[::-1, ::-1], 'valid')
                iy, ix = np.unravel_index(np.argmax(corr), corr.shape)
                sc = corr[iy, ix]/math.sqrt(float((qz*qz).sum()) + 1e-9)
                if bestA is None or sc > bestA[0]:
                    bestA = (sc, float(z), ix, iy)
            if bestA is None:
                log('  %s: no global alignment' % t['name']); continue
            _, zA, oxA, oyA = bestA
            scales.append(t['m_per_px']/zA)
            log('  %s: aligned, z=%.2f (scan ≈ %.2f m/px)' % (t['name'], zA, t['m_per_px']/zA))
        else:
            zA = t['m_per_px']/(m_scan_hint or t['m_per_px'])
            scales.append(m_scan_hint or t['m_per_px'])
        got = 0
        for lon in lons:
            for lat in lats:
                qx, qy = t['to_px'](lon, lat)
                r = int(pw/zA) + 4
                if not (r < qx < qf.shape[1]-r and r < qy < qf.shape[0]-r):
                    continue
                patch = qf[int(qy)-r:int(qy)+r, int(qx)-r:int(qx)+r]
                if not (0.015 < patch.mean() < 0.30): continue
                patch = ndimage.zoom(patch, zA, order=1)
                ph, pwd = patch.shape
                if seed_fit is None:
                    sx, sy = D*oxA + qx*zA, D*oyA + qy*zA
                else:
                    Xs, Ys = lcc.fwd(lon, lat)
                    sx, sy = (float(v) for v in seed_fit.apply(Xs, Ys))
                x_lo, y_lo = int(sx)-pw-sw, int(sy)-pw-sw
                win = scan_f[y_lo:y_lo+2*(pw+sw), x_lo:x_lo+2*(pw+sw)]
                if win.shape != (2*(pw+sw), 2*(pw+sw)): continue
                pz = patch - patch.mean()
                corr = fftconvolve(win - win.mean(), pz[::-1, ::-1], 'valid')
                cy_, cx_ = np.unravel_index(np.argmax(corr), corr.shape)
                peak = corr[cy_, cx_]
                if peak <= 0: continue
                blot = corr.copy()
                blot[max(0, cy_-14):cy_+15, max(0, cx_-14):cx_+15] = -1e9
                if blot.max() > ambig*peak: continue
                gx.append(x_lo + cx_ + pwd/2.0)
                gy.append(y_lo + cy_ + ph/2.0)
                gl.append((lon, lat)); got += 1
        log('  %s: %d control points' % (t['name'], got))
    m_per_px = float(np.median(scales)) if scales else (m_scan_hint or 0.0)
    log('  %d control points total, scan ≈ %.2f m/px' % (len(gx), m_per_px))
    X, Y = lcc.fwd([g[0] for g in gl], [g[1] for g in gl])
    return np.asarray(X), np.asarray(Y), np.array(gx), np.array(gy), m_per_px


def fit_trimmed(X, Y, gx, gy, deg=2, rounds=3, floor=6.0, k=2.8,
                name='registration fit', m_per_px=None, log=print):
    """Iteratively trimmed polynomial fit; returns (fit, keep_mask)."""
    keep = np.ones(len(gx), bool)
    fit = None
    for _ in range(rounds):
        fit = Fit(X[keep], Y[keep], gx[keep], gy[keep], deg)
        px, py = fit.apply(X, Y)
        dres = np.hypot(px-gx, py-gy)
        keep = dres < max(floor, float(np.median(dres[keep]))*k)
    fit = Fit(X[keep], Y[keep], gx[keep], gy[keep], deg)
    fit_report('%s (%d/%d kept)' % (name, int(keep.sum()), len(gx)), fit, m_per_px)
    return fit, keep
