"""Haus zum Korn (1941) + Haus zum Schimmeltor (1948), Wiedikon Hochhaeuser at Bahnhof Wiedikon: 7 floors, light plaster,
paired tall windows with dark-red frames, stone-clad pillar arcade at ground floor, flat roof with attic setback. research/v3/schimmeltor_korn.md"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def build(idp, name, title, seed):
    c = prep([idp], 0.5); rng = np.random.default_rng(seed)
    m = Model(name); ring = c.ring; P = c.P
    mw = m.mat("wall", plaster(hexc("#e4ddc9"), seed=seed, stains=0.03))
    ga = D.glass_atlas_g(frame="#7a2f2a", glass="#2a343e", sky="#8aa0b0", cols=2, rows=3, seed=seed, bar=3, lit_p=0.3,
                         curtain_cols=[(236, 228, 210), (205, 205, 200), (224, 190, 150), (200, 120, 100)])
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", D.ashlar(hexc("#a69f90"), rows=6, rough=0.07, seed=4))
    PL, GF, FH, NF = 0.5, 4.4, 2.9, 6           # plinth, tall arcade floor, regular floors
    z0 = PL; zt = z0 + GF + NF * FH
    m.extrude(mf, mf, P, -3, PL, col=W4, roof=False, mod=(3, 1.4))
    # arcade floor: pillars + recessed glazed shopfront
    li = max(range(len(ring)), key=lambda i: math.dist(ring[i], ring[(i + 1) % len(ring)]))
    stone = hexl("#b4ab98")
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]; L, t, n = D.frame_of(a, b)
        if L < 2: m.wall(mw, a, b, z0, zt, (4, 4), W4); continue
        ang = math.atan2(t[1], t[0]); nb = max(1, int(round(L / 3.4))); bw = L / nb
        # ground floor: glass shopfront recessed 1.0 behind pillar line
        m.wall(mf, (a[0] - n[0] * 1.0, a[1] - n[1] * 1.0), (b[0] - n[0] * 1.0, b[1] - n[1] * 1.0), z0, z0 + GF, (3, 3), (150, 150, 146, 255))
        D.poly_wall(m, mg, Polygon(D.rect_pts(0.2, 0.55, L - 0.2, 3.5)), a, t, n, -0.95, W4, lambda u, z: ((int(u / 1.5) % D.NV) / D.NV + 0.02, 0.25 + 0.75 * (z - 0.55) / 2.95))
        for k in range(nb + 1):
            p = D.P3(a, t, n, k * bw, z0, 0.0)
            m.box(mf, p[0] + (t[0] * (0.2 if k == 0 else -0.2 if k == nb else 0)), p[1] + (t[1] * (0.2 if k == 0 else -0.2 if k == nb else 0)), 0.55, 0.55, z0, z0 + GF, rot=ang, col=stone)
        D.band(m, mf, a, b, z0 + GF - 0.5, z0 + GF, 0.12, hexl("#a69f90"))     # architrave / soffit band
        # upper floors: paired tall windows
        nb2 = max(1, int(round(L / 3.1))); bw2 = L / nb2
        for f in range(NF):
            fb = z0 + GF + f * FH
            for k in range(nb2):
                u0, u1 = k * bw2, (k + 1) * bw2; uc = (u0 + u1) / 2
                hole = D.rect_pts(uc - 0.62, fb + 0.7, uc + 0.62, fb + 2.4)
                D.bay(m, mw, mg, mf, a, t, n, u0, u1, fb, fb + FH, hole, 0.25, int(rng.integers(0, D.NV)), W4, hexl("#cfc9b8"), (4, 4), None)
                D.surround(m, mw, a, t, n, hole, 0.09, (246, 242, 232, 255), 0.04, sill=0.08)
        D.band(m, mw, a, b, zt - 0.5, zt + 0.1, 0.3, (246, 242, 232, 255))
    # parapet + attic setback with lift head
    A = P.buffer(-1.8, join_style=2)
    if not A.is_empty and A.geom_type == "Polygon": m.extrude(mw, mf, A, zt, zt + 2.6, col=W4, rcol=hexl("#6f6c66"), mod=(4, 4))
    m.extrude(mw, mf, P, zt, zt + 0.35, col=(246, 242, 232, 255), rcol=hexl("#6f6c66"), roof=False)
    finish39(m, name, title, c.ox, c.oy, c.oz, c.hide)


if __name__ == "__main__":
    build("ID_D86AAFA7", "k39w3_korn", "Haus zum Korn", 5)
    build("ID_3CA27E0C", "k39w3_schimmeltor", "Haus zum Schimmeltor", 9)
