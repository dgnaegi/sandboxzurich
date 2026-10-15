"""Zwinglihaus / Zwinglikirche, Aemtlerstrasse 25: big cream-white plaster block, arched arcade windows at ground floor, oculi + small framed
windows on the middle floor, row of round-headed windows under a red hip roof; statue niche with fountain on the street face.
research/v3/zwinglihaus.md + wiedinghof (Commons #17/#18)"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def circle(u, z, r, n=14):
    return [(u + r * math.cos(2 * math.pi * i / n), z + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def build():
    c = prep(["ID_CEC98B4D"], 0.5); rng = np.random.default_rng(31); P = c.P; ring = c.ring
    m = Model("k39w3_zwingli")
    mw = m.mat("wall", plaster(hexc("#e9e3d2"), seed=6, stains=0.035))
    ga = D.glass_atlas_g(frame="#e8e2d2", glass="#2b3640", sky="#8aa0b0", cols=2, rows=3, seed=17, bar=3, lit_p=0.3, curtains=False)
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", D.ashlar(hexc("#b9b09c"), rows=6, rough=0.06, seed=9))
    PL, FH = 0.9, 7.0; z0 = PL; zE = z0 + 3 * FH
    STONE, ROOF = hexl("#b9b09c"), hexl("#a0462f")
    m.extrude(mf, mf, P, -3, PL, col=W4, roof=False, mod=(3, 1.4))
    def hole_override(k, nb, f, bw, fb, fh):
        if f == 1 and k % 2 == 1: return circle(bw / 2, fb + fh * 0.55, 0.65)       # oculus
        return None
    st = dict(bayw=4.3, kind="rect", ww=1.1, wh=2.3, so=0.32, depth=0.3, surr=hexl("#c9c1ad"), surr_w=0.16, sill=True,
              gf=dict(kind="arch", ww=2.1, wh=4.6, so=0.4, surr_w=0.22), top=dict(kind="arch", ww=1.5, wh=3.4, so=1.1, surr_w=0.15),
              hole_override=hole_override, bands=[(zE - 0.8, 0.8, 0.3, (236, 231, 218, 255)), (z0 + FH - 0.15, 0.3, 0.1, (236, 231, 218, 255))])
    # middle floor rect windows (not oculus) are smaller; oculus overrides ww/wh via hole_override
    facade(m, mw, mg, mf, ring, z0, 3, FH, st, rng)
    corner_pilasters(m, mf, ring, z0, zE, 0.8, hexl("#cdc5b1"))
    # statue niche + fountain on the longest edge
    li = max(range(len(ring)), key=lambda i: math.dist(ring[i], ring[(i + 1) % len(ring)]))
    a, b = ring[li], ring[(li + 1) % len(ring)]; L, t, n = D.frame_of(a, b); uc = L * 0.55
    D.poly_wall(m, mf, Polygon(D.arch_pts(uc - 0.7, z0 + 3.3, uc + 0.7, z0 + 5.4)), a, t, n, 0.06, hexl("#cfc7b3"), lambda u, z: (u * 0.3, z * 0.3))
    p = D.P3(a, t, n, uc, z0 + 3.4, 0.4); m.box(mf, p[0], p[1], 0.55, 0.3, z0 + 3.4, z0 + 5.0, rot=math.atan2(t[1], t[0]), col=hexl("#d8d2c4"))
    q = D.P3(a, t, n, uc, 0, 0.8); m.box(mf, q[0], q[1], 3.0, 1.2, 0, 0.8, rot=math.atan2(t[1], t[0]), col=hexl("#9b968a"))
    # hip roof, red tile, with ridge
    A = P.buffer(0.7, join_style=2)
    taper(m, mf, A, zE, zE + 8.5, 0.28, ROOF, cap=True)
    finish39(m, "k39w3_zwingli", "Zwinglihaus Aemtlerstrasse", c.ox, c.oy, c.oz, c.hide)


if __name__ == "__main__":
    build()
