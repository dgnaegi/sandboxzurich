"""Real gate openings for the two barrel-hall portals: holes cut into the portal wall (arched, 0.8 m reveals in stone), doors set back (main gate:
two steel leaves with the middle open, side gates: closed timber/steel decal doors) and a simple hall interior seen through the main gate
(floor, side walls, columns, barrel-vault soffit, bright far end). Called from schlachthof.py build()."""
import math
from shapely.geometry import Polygon, box as sbox
from shapely.ops import unary_union
import numpy as np
import detail as D
import schlachthof_tex as T
from k39w3_kit import W4, hexl

GATES = [(0.0, 7.8, 9.6), (-9.7, 4.4, 7.4), (9.7, 4.4, 7.4)]       # (u centre, width, height of the opening above z0 = ground + 1.5), same as the portal texture
STONEC, STEEL, TIMBER = hexl("#a7a396"), hexl("#4d5a56"), hexl("#6a4a32")


def arch_poly(uc, w, zg, top, n=16):
    zs = top - w / 2
    pts = [(uc - w / 2, zg), (uc + w / 2, zg), (uc + w / 2, zs)] + [(uc + w / 2 * math.cos(math.pi * i / n), zs + w / 2 * math.sin(math.pi * i / n)) for i in range(1, n)] + [(uc - w / 2, zs)]
    return Polygon(pts).buffer(0)


def holes(gl_abs):
    return [arch_poly(uc, w, gl_abs + 0.02, gl_abs + 1.5 + h) for uc, w, h in GATES]


def fill(m, mf, mdc, hs, org, tf, nrm, gl_abs, var, sp_l, Rv, zc, HALF):
    """hs: hole polygons (u,z); org/tf/nrm: wall frame (nrm = outward). Builds reveals, doors, interior."""
    P = lambda u, z, d: (org[0] + tf[0] * u + nrm[0] * d, org[1] + tf[1] * u + nrm[1] * d, z)
    inn = (-nrm[0], -nrm[1], 0)
    for gi, (hp, (uc, w, h)) in enumerate(zip(hs, GATES)):
        c = hp.centroid; ring = list(hp.exterior.coords)
        for (u0, z0), (u1, z1) in zip(ring[:-1], ring[1:]):
            if abs(u0 - u1) < 1e-6 and abs(z0 - z1) < 1e-6: continue
            if z0 <= gl_abs + 0.05 and z1 <= gl_abs + 0.05: continue                    # no reveal across the threshold
            du, dz = u1 - u0, z1 - z0; nx, nz = -dz, du; L = math.hypot(nx, nz); nx, nz = nx / L, nz / L
            if (c.x - u0) * nx + (c.y - z0) * nz < 0: nx, nz = -nx, -nz
            nw = (tf[0] * nx, tf[1] * nx, nz)
            D._oriented(m, mf, [P(u0, z0, 0.0), P(u1, z1, 0.0), P(u1, z1, -0.8), P(u0, z0, -0.8)], nw, [(0, 0), (1, 0), (1, 1), (0, 1)], STONEC)
        x0, z0_, x1, z1_ = hp.bounds
        uvf = lambda u, z, b=(x0, z0_, x1, z1_): ((u - b[0]) / (b[2] - b[0]), (z - b[1]) / (b[3] - b[1]))
        if gi == 0:                                                                       # main gate: two steel leaves, middle open
            lw = w * 0.27; zs = gl_abs + 1.5 + h - w / 2
            for sd in (-1, 1):
                ua, ub = (uc - w / 2, uc - w / 2 + lw) if sd < 0 else (uc + w / 2 - lw, uc + w / 2)
                for k in range(4):
                    uu0 = ua + (ub - ua) * k / 4; uu1 = ua + (ub - ua) * (k + 1) / 4; col = STEEL if k % 2 else tuple(int(v * 1.25) for v in STEEL[:3]) + (255,)
                    D._oriented(m, mf, [P(uu0, gl_abs + 0.02, -0.9), P(uu1, gl_abs + 0.02, -0.9), P(uu1, zs, -0.9), P(uu0, zs, -0.9)], (nrm[0], nrm[1], 0), [(0, 0), (1, 0), (1, 1), (0, 1)], col)
            # interior hall seen through the opening
            Lh = 30.0; fz = gl_abs + 0.02; gc = hexl("#6b6a66"); wc = hexl("#a79b83"); cc = hexl("#c9c6bd")
            D._oriented(m, mf, [P(-HALF, fz, -0.8), P(HALF, fz, -0.8), P(HALF, fz, -Lh), P(-HALF, fz, -Lh)], (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)], gc)
            for sd in (-1, 1):
                D._oriented(m, mf, [P(sd * HALF, fz, -0.8), P(sd * HALF, fz, -Lh), P(sd * HALF, sp_l, -Lh), P(sd * HALF, sp_l, -0.8)], (-tf[0] * sd, -tf[1] * sd, 0), [(0, 0), (1, 0), (1, 1), (0, 1)], wc)
            NS = 10; th = math.asin(HALF / Rv)
            for i in range(NS):
                a0 = -th + 2 * th * i / NS; a1 = -th + 2 * th * (i + 1) / NS
                q = lambda a, d: P(Rv * math.sin(a), zc + Rv * math.cos(a), d)
                D._oriented(m, mf, [q(a0, -0.8), q(a1, -0.8), q(a1, -Lh), q(a0, -Lh)], (0, 0, -1), [(0, 0), (1, 0), (1, 1), (0, 1)], cc)
            for d in np.arange(-5.0, -Lh + 2, -7.0):
                for sd in (-1, 1):
                    u = sd * 6.0; zt = zc + math.sqrt(Rv * Rv - u * u); p = P(u, 0, d)
                    m.box(mf, p[0], p[1], 0.55, 0.55, fz, zt, col=hexl("#8f8a7e"))
            D._oriented(m, mf, [P(-HALF, fz, -Lh), P(HALF, fz, -Lh), P(HALF, sp_l + 6, -Lh), P(-HALF, sp_l + 6, -Lh)], (nrm[0], nrm[1], 0), [(0, 0), (1, 0), (1, 1), (0, 1)], hexl("#e8ecec"))
        else:                                                                             # side gates: closed doors, timber at the NW portal (var 1), steel at the SE (var 0)
            base = TIMBER if var == 1 else STEEL; dark = tuple(int(v * 0.7) for v in base[:3]) + (255,)
            uvz = lambda u, z: (0, 0)
            D.poly_wall(m, mf, hp, org, tuple(tf), tuple(nrm), -0.9, base, uvz)
            for k in range(int(w / 0.55) + 1):
                u = uc - w / 2 + 0.2 + k * 0.55; bt = hp.intersection(sbox(u - 0.04, gl_abs, u + 0.04, gl_abs + 30))
                for g_ in (getattr(bt, "geoms", [bt])):
                    if not g_.is_empty and g_.geom_type == "Polygon": D.poly_wall(m, mf, g_, org, tuple(tf), tuple(nrm), -0.86, dark, uvz)
            zb_ = gl_abs + 2.2
            D.poly_wall(m, mf, hp.intersection(sbox(uc - w, zb_, uc + w, zb_ + 0.15)), org, tuple(tf), tuple(nrm), -0.85, dark, uvz)
