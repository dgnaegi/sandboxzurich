"""Measured deck heights from the LiDAR rasters (not yet used by bridges.py; Phase B).

deck_profile(chain) -> dict(z, raw, src, n): per chain vertex (chain["p"] = [[x, y, z], ...], chain["w"] = deck width)
  raw  measured z (game metres): class-17 bridge top in a strip around the vertex; fallback class-2 ground (at-grade
       parts and rail decks that the classifier calls ground); NaN where nothing was measured
  z    raw after outlier rejection (running median) and light smoothing (NaN stays NaN)
  src  1 = bridge class 17, 2 = ground fallback, 3 = layer found but further than PRIOR_TOL from the chain z (raw=NaN, see alt),
       0 = none      n = number of raster cells used      alt = nearest-layer z for src 3
prior=True (default) uses the chain's own z only to choose between stacked layers (a road under a bridge, a bridge over a
rail cutting); with prior=False the bridge layer always wins.
Vehicles on the deck are removed by keeping only cells within CAR_TOL of the strip median and taking a low percentile;
wires/masts (class 15) are never part of the surface rasters.
"""
from __future__ import annotations

import numpy as np

import lidar

ALONG = (-2.0, 2.0)
MIN_CELLS = 6
CAR_TOL = 0.45     # m: cells further from the strip median are vehicles / railings / the road below
PCT = 40           # low percentile of the surviving cells
OUT_TOL = 0.5      # m: deviation from the running median that counts as outlier
OUT_WIN = 5
PRIOR_TOL = 4.0    # m: with prior=True a layer (bridge / ground) is only accepted within this distance of the chain's current z


def _strip(p, i, half):
    a = np.asarray(p, float)
    j0, j1 = max(i - 1, 0), min(i + 1, len(a) - 1)
    t = a[j1, :2] - a[j0, :2]
    t /= (np.hypot(*t) or 1.0)
    n = np.array([-t[1], t[0]])
    A = np.arange(ALONG[0], ALONG[1] + 1e-9, 0.5)
    O = np.arange(-half, half + 1e-9, 0.5)
    gx = a[i, 0] + A[:, None] * t[0] + O[None, :] * n[0]
    gy = a[i, 1] + A[:, None] * t[1] + O[None, :] * n[1]
    return gx.ravel(), gy.ravel()


def _robust(v):
    v = v[~np.isnan(v)]
    if len(v) < MIN_CELLS:
        return np.nan, len(v)
    m = np.median(v)
    k = v[np.abs(v - m) <= CAR_TOL]
    if len(k) < MIN_CELLS:
        k = v
    return float(np.percentile(k, PCT)), len(k)


def deck_profile(chain, smooth=True, prior=True):
    p = np.asarray(chain["p"], float)
    half = min(0.4 * float(chain.get("w", 6)), 5.0)
    nv = len(p)
    raw = np.full(nv, np.nan); alt = np.full(nv, np.nan); src = np.zeros(nv, int); cnt = np.zeros(nv, int)
    for i in range(nv):
        gx, gy = _strip(p, i, half)
        cand = []
        for code, arr in ((1, lidar.bridge(gx, gy)), (2, lidar.dtm(gx, gy))):
            z, c = _robust(arr)
            if not np.isnan(z):
                cand.append((code, z, c))
        if not cand:
            continue
        if prior:
            code, z, c = min(cand, key=lambda t: abs(t[1] - p[i, 2]))
            if abs(z - p[i, 2]) > PRIOR_TOL:
                src[i], alt[i], cnt[i] = 3, z, c
                continue
        else:
            code, z, c = cand[0]
        raw[i], src[i], cnt[i] = z, code, c
    z = raw.copy()
    ok = ~np.isnan(z)
    if ok.sum() >= 3:  # outliers vs running median of valid neighbours
        idx = np.where(ok)[0]
        v = z[idx]
        h = OUT_WIN // 2
        for k, i in enumerate(idx):
            nb = v[max(k - h, 0):k + h + 1]
            if abs(v[k] - np.median(nb)) > OUT_TOL:
                z[i] = np.nan
    if smooth:
        out = z.copy()
        for i in range(nv):
            if np.isnan(z[i]):
                continue
            w, s = 0.5, 0.5 * z[i]
            for d in (-1, 1):
                j = i + d
                if 0 <= j < nv and not np.isnan(z[j]):
                    w += 0.25; s += 0.25 * z[j]
            out[i] = s / w
        z = out
    return {"z": z, "raw": raw, "src": src, "n": cnt, "alt": alt}
