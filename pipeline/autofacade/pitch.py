"""Camera pitch/roll from near-vertical edge convergence (vertical vanishing point). Returns tan(pitch up), roll rad, support."""
import math

import numpy as np


def estimate(L, f):
    H, W = L.shape
    g = L
    gx = np.zeros_like(g); gy = np.zeros_like(g)
    gx[:, 1:-1] = g[:, 2:] - g[:, :-2]
    gy[1:-1, :] = g[2:, :] - g[:-2, :]
    mag = np.hypot(gx, gy)
    thr = np.percentile(mag, 92)
    m = mag > max(thr, 6)
    ys, xs = np.nonzero(m)
    gxs, gys, ws = gx[ys, xs], gy[ys, xs], mag[ys, xs]
    # up-pointing line direction perpendicular to gradient
    dx = np.where(-gxs < 0, gys, -gys)
    dyv = np.where(-gxs < 0, -gxs, gxs)
    phi = np.arctan2(dx, -dyv)
    k = np.abs(phi) < math.radians(22)
    xs, phi, ws = xs[k], phi[k], ws[k]
    if len(xs) < 400:
        return None
    xo = xs - W / 2
    edges = np.linspace(-W / 2, W / 2, 11)
    px, pp, pw = [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        s = (xo >= a) & (xo < b)
        if s.sum() < 60:
            continue
        o = np.argsort(phi[s]); c = np.cumsum(ws[s][o])
        pp.append(phi[s][o][np.searchsorted(c, c[-1] / 2)]); px.append(xo[s].mean()); pw.append(s.sum())
    if len(px) < 5:
        return None
    px, pp = np.array(px), np.array(pp)
    best = None
    for i in range(len(px)):  # Theil-Sen
        for j in range(i + 1, len(px)):
            if abs(px[j] - px[i]) > W * 0.25:
                sl = (pp[j] - pp[i]) / (px[j] - px[i])
                best = [sl] if best is None else best + [sl]
    if not best:
        return None
    a = float(np.median(best))
    roll = float(np.median(pp - a * px))
    res = np.abs(pp - a * px - roll)
    return -a * f, roll, float(np.mean(res < math.radians(2.5)))
