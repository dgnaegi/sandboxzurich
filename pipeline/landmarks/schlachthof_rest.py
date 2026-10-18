"""Restaurant Schlachthof extras (photos 4/5 in research/schlachthof.md): curved central gable with stone coping and three windows,
sign field «RESTAURANT SCHLACHTHOF», pitched dormers on the roof, brick chimneys on the ridge. Called from schlachthof.py after the walls."""
import math
import numpy as np
from shapely.geometry import Polygon, box as sbox
from shapely.affinity import translate
import detail as D
import schlachthof_tex as T
from k39w3_kit import W4, hexl
from lm import taper

STONE = hexl("#b9b3a4"); ROOF = hexl("#9a4a34"); DARK = hexl("#5d5a56")


def gable_outline():
    pts = [(-4.4, -2.0), (-4.4, 2.2)]
    pts += [(-4.4 + 1.8 * t / 8, 2.2 + 1.5 * math.sin(math.pi / 2 * t / 8)) for t in range(1, 9)]
    pts += [(-2.6 * math.cos(math.pi * i / 16), 3.7 + 1.6 * math.sin(math.pi * i / 16)) for i in range(1, 16)]
    pts += [(2.6 - 1.8 * t / 8 + 0.0, 3.7) for t in range(0, 1)]
    right = [(4.4 - 1.8 * t / 8, 2.2 + 1.5 * math.sin(math.pi / 2 * t / 8)) for t in range(8, 0, -1)]
    pts += [(2.6, 3.7)] + right + [(4.4, 2.2), (4.4, -2.0)]
    return Polygon(pts).buffer(0)


def dormer(m, mp, mt, mf, mdc, a, tt, nh, u, ze, step=0.0):
    """Small pitched dormer: window face 1.0 m inside the wall plane, side cheeks, two tile slopes."""
    P = lambda uu, d, z: (a[0] + tt[0] * uu + nh[0] * d, a[1] + tt[1] * uu + nh[1] * d, z)
    n = (nh[0], nh[1], 0); hw = 0.7; d0 = -1.0; d1 = -2.6; zb, zs, zr = ze + 0.4, ze + 2.3, ze + 3.1
    D._oriented(m, mp, [P(u - hw, d0, zb), P(u + hw, d0, zb), P(u + hw, d0, zs), P(u - hw, d0, zs)], n, [(0, 0), (.4, 0), (.4, .5), (0, .5)], W4)
    D._oriented(m, mp, [P(u - hw, d0, zs), P(u + hw, d0, zs), P(u, d0, zr)], n, [(0, 0), (.4, 0), (.2, .2)], W4)
    D._oriented(m, mdc, [P(u - 0.45, d0 + 0.03, zb + 0.5), P(u + 0.45, d0 + 0.03, zb + 0.5), P(u + 0.45, d0 + 0.03, zs - 0.15), P(u - 0.45, d0 + 0.03, zs - 0.15)], n, T.uvr("win_mod"), W4)
    for s in (-1, 1):
        sn = (tt[0] * s, tt[1] * s, 0)
        D._oriented(m, mf, [P(u + s * hw, d0, zb), P(u + s * hw, d1, zb), P(u + s * hw, d1, zs), P(u + s * hw, d0, zs)], sn, [(0, 0), (1, 0), (1, 1), (0, 1)], DARK)
        D._oriented(m, mf, [P(u + s * hw, d0, zs), P(u + s * hw, d1, zs), P(u, d1, zr), P(u, d0, zr)], (sn[0] * .6, sn[1] * .6, .8), [(0, 0), (1, 0), (1, 1), (0, 1)], ROOF)
        D._oriented(m, mf, [P(u + s * hw, d0, zs), P(u + s * (hw + 0.25), d0 - 0.15, zs - 0.05), P(u + s * (hw + 0.25), d1, zs - 0.05), P(u + s * hw, d1, zs)], (0, 0, -1), [(0, 0), (1, 0), (1, 1), (0, 1)], DARK)


def restaurant_extras(m, mp, mt, mf, mdc, info, rp, loc, oz):
    # ---- curved gable + sign on the longest street-facing wall --------------------------------------
    poly0 = gable_outline()
    for (a, b, nh, tt, w, ze, is_long, g) in info:
        if not is_long: continue
        pz = translate(poly0, 0, ze); 
        cu = w / 2; org = (a[0] + tt[0] * cu, a[1] + tt[1] * cu)
        ring = translate(poly0.buffer(0.3).difference(poly0).intersection(sbox(-6, -0.4, 6, 8)), 0, ze)
        D.poly_wall(m, mp, pz, org, tuple(tt), tuple(nh), 0.06, W4, lambda u, z: ((u + 4.4) / 4.0, z / 4.0))
        D.poly_wall(m, mf, ring, org, tuple(tt), tuple(nh), 0.14, STONE, lambda u, z: (0, 0))
        P = lambda u, z, off=0.12: (a[0] + tt[0] * u + nh[0] * off, a[1] + tt[1] * u + nh[1] * off, z)
        for k in (-2.4, 0.0, 2.4):                                                                      # three windows in the gable
            D._oriented(m, mdc, [P(cu + k - 0.55, ze + 0.5), P(cu + k + 0.55, ze + 0.5), P(cu + k + 0.55, ze + 2.3), P(cu + k - 0.55, ze + 2.3)], (nh[0], nh[1], 0), T.uvr("win_shut"), W4)
        D._oriented(m, mdc, [P(cu - 0.7, ze + 3.5), P(cu + 0.7, ze + 3.5), P(cu + 0.7, ze + 4.7), P(cu - 0.7, ze + 4.7)], (nh[0], nh[1], 0), T.uvr("win_mod"), W4)
        zs_ = g + 3.55                                                                                   # sign field over the entrance
        D._oriented(m, mdc, [P(cu - 4.2, zs_, 0.07), P(cu + 4.2, zs_, 0.07), P(cu + 4.2, zs_ + 0.95, 0.07), P(cu - 4.2, zs_ + 0.95, 0.07)], (nh[0], nh[1], 0), T.uvr("sign"), W4)
    # ---- dormers on every long wall (not under the gable) ----------------------------------------
    for (a, b, nh, tt, w, ze, is_long, g) in info:
        if w < 7: continue
        nd = max(1, int((w - 2.0) // 4.4)); sp = (w - 2.0) / nd
        for k in range(nd):
            u = 1.0 + (k + 0.5) * sp
            if is_long and abs(u - w / 2) < 5.6: continue
            dormer(m, mp, mt, mf, mdc, a, tt, nh, u, ze)
    # ---- chimneys: on the ridge, found from the highest roof vertices -------------------------------
    pts = np.array([x for k, p in rp if k == 2 for x in loc(p)])
    ridge = pts[pts[:, 2] > pts[:, 2].max() - 0.5]
    if len(ridge) < 2: return
    c = ridge[:, :2].mean(0); u_, s_, vt = np.linalg.svd(ridge[:, :2] - c); ax = vt[0]; pr = (ridge[:, :2] - c) @ ax
    zt = float(pts[:, 2].max())
    for f in (0.2, 0.8):
        p = c + ax * (pr.min() + f * (pr.max() - pr.min()))
        m.box(mf, p[0], p[1], 1.0, 1.0, zt - 1.2, zt + 1.7, col=hexl("#a8553b"))
        m.box(mf, p[0], p[1], 1.3, 1.3, zt + 1.7, zt + 2.0, col=hexl("#8e8a84"))
