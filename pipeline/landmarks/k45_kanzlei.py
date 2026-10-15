"""Kanzlei-Schulhaus (Kanzleistrasse, ~1900): light grey plaster, rusticated plinth, four floors + attic, white Sprossenfenster with
plaster surrounds and sills (some yellow blinds), corner pilasters, cornice, low hip roof, side entrance with steps. research/v3/kanzlei_schulhaus.md."""
import math
from common import *
from lm import *
import detail as D
from k45_volkshaus import plaster, front_edge


def build():
    B = bid("ID_3822D538"); P = outline(B["fp"], 0.5)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = orient(localize(P, ox, oy), 1.0); ring = list(Pl.exterior.coords)[:-1]; ne = len(ring)
    rng = np.random.default_rng(21)
    m = Model("kanzlei")
    mw = m.mat("wall", plaster(hexc("#d9d4c4"), seed=8, stains=0.025))
    ga = D.glass_atlas_g(frame="#f2f0e8", glass="#2a3641", sky="#8aa0b0", cols=2, rows=3, seed=7, bar=3, lit_p=0.3,
                         curtain_cols=[(236, 228, 210), (224, 160, 48), (236, 228, 210), (205, 205, 200), (224, 160, 48)])
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", D.ashlar(hexc("#a39f94"), rows=6, rough=0.08, seed=4))
    W = (255, 255, 255, 255)
    PL, FH, NF, FA = 1.4, 4.0, 4, 3.3
    z0 = PL; zt = z0 + NF * FH; eave = zt + FA
    PLINTH, TRIM, ROOF = D.hexl("#b0aca0"), D.hexl("#e6dfcb"), D.hexl("#5a534c")
    m.extrude(mf, mf, Pl, -3, PL, col=(255, 255, 255, 255), roof=False, mod=(3.0, 1.4))
    # entrance on the longest edge
    li = max(range(ne), key=lambda i: math.dist(ring[i], ring[(i + 1) % ne]))
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b)
        if L < 1.5: m.wall(mw, a, b, PL, eave, (4, 4), W); continue
        nb = max(1, int(round(L / 3.0))); bw = L / nb
        for f in range(NF + 1):
            fb = z0 + f * FH; fh = FH if f < NF else FA
            for k in range(nb):
                u0, u1 = k * bw, (k + 1) * bw; uc = (u0 + u1) / 2
                if i == li and f == 0 and k == 1:
                    hole = D.arch_pts(uc - 0.9, fb, uc + 0.9, fb + 2.1) if False else D.rect_pts(uc - 0.9, fb + 0.0, uc + 0.9, fb + 2.7)
                elif f == NF: hole = D.rect_pts(uc - 0.55, fb + 0.7, uc + 0.55, fb + 2.2)
                else: hole = D.rect_pts(uc - 0.7, fb + 0.85, uc + 0.7, fb + 3.05)
                D.bay(m, mw, mg, mf, a, t, n, u0, u1, fb, fb + fh, hole, 0.28, int(rng.integers(0, D.NV)), W, hexc("#cfc9b8"), (4, 4), None)
                if f < NF: D.surround(m, mw, a, t, n, hole, 0.13, (250, 248, 240, 255), 0.04, sill=0.1 if f > 0 or k != 1 or i != li else 0)
                else: D.surround(m, mw, a, t, n, hole, 0.1, (250, 248, 240, 255), 0.03)
        D.band(m, mw, a, b, z0 - 0.15, z0 + 0.15, 0.1, (250, 248, 240, 255))
        for f in (1, 3): D.band(m, mw, a, b, z0 + f * FH - 0.08, z0 + f * FH + 0.08, 0.05, (250, 248, 240, 255))
        D.band(m, mw, a, b, eave - 0.6, eave + 0.1, 0.4, (250, 248, 240, 255))
        if i == li:
            uc = bw * 1.5
            for k in range(4):
                p = D.P3(a, t, n, uc, 0, 0.45 + (3 - k) * 0.33)
                m.box(mf, p[0], p[1], 2.4, 0.33 * (4 - k) + 0.2, PL - 0.3 * (k + 1) - 0.05 if False else 0.0, PL - 0.3 * k * 0.0 + 0.0, rot=math.atan2(t[1], t[0]), col=D.hexl("#a8a49a")) if False else None
    # corner pilasters (rusticated)
    for i in range(ne):
        p = ring[i]; q = ring[(i + 1) % ne]
        m.box(mw, p[0], p[1], 0.6, 0.6, PL, eave - 0.6, rot=math.atan2(q[1] - p[1], q[0] - p[0]), col=(238, 232, 218, 255))
    # roof: low hip, brown-grey tiles + chimneys
    A = Pl.buffer(0.55, join_style=2)
    q1 = taper(m, mf, A, eave + 0.1, eave + 5.0, 0.38, ROOF, cap=True)
    for fx, fy in ((0.3, 0.1), (-0.3, -0.1)):
        px, py = q1.centroid.x + fx * (q1.bounds[2] - q1.bounds[0]), q1.centroid.y + fy * (q1.bounds[3] - q1.bounds[1])
        m.box(mf, px, py, 1.1, 1.1, eave + 3.8, eave + 6.6, col=D.hexl("#a87a62")); m.box(mf, px, py, 1.4, 1.4, eave + 6.6, eave + 6.9, col=D.hexl("#5a5a58"))
    hide = [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (B["fp"].geoms if hasattr(B["fp"], "geoms") else [B["fp"]])]
    finish(m, "kanzlei_schulhaus", "Kanzlei-Schulhaus", ox, oy, oz, hide_union("Kanzlei-Schulhaus", hide))


if __name__ == "__main__":
    build()
