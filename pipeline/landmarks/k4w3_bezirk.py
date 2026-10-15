"""Bezirksgebaeude Zuerich (Badenerstrasse 90 / Hohlstrasse), ~1914: four-storey block with rotated courtyard wings. Cream-yellow plaster wings (3 window rows,
white frames, cornice) under a slate mansard with eyebrow dormers; central pavilion in pale grey artificial stone: 5 window axes between giant
pilasters, three round-headed portals with black iron doors, gable pediment with medallion. Photos: research/v3/bezirksgebaeude.md"""
from k4w3_kit import *
from k45_volkshaus import plaster


def build():
    Bs, ox, oy, oz = setup(["ID_5F951F04"])
    B = Bs[0]; H = B["zmax"] - oz
    rng = np.random.default_rng(8)
    ring = ring_of(B, ox, oy); Pl = Polygon(ring); r = list(ring.exterior.coords)[:-1]
    m = Model("bezirksgebaeude")
    CREAM, STONE = hexc("#ede4bd"), hexc("#b9b6ae")
    mw = m.mat("wall", plaster(CREAM, seed=5, stains=0.012))
    sign = strip([(0, 640, "BEZIRKSGERICHT", "#e8e4d8", "#2b2a28", None)], size=22)
    ga = D.glass_atlas_g(frame="#f3f1e8", glass="#27323c", sky="#8da3b3", cols=2, rows=3, seed=9, lit_p=0.35, sign=sign, curtain_cols=[(228, 226, 218), (210, 196, 170), (190, 196, 202)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W))
    run = make_run(m, mw, mg, mf, rng, W)
    WHITE, GREY, SLATE = hx("#ece8dc"), hx("#c9c3b2"), hx("#706e6c")
    g = 0.3; e0, e1, e2 = 4.9, 4.7, 4.4; z1 = g + e0; z2 = z1 + e1; z3 = z2 + e2
    m.extrude(mf, mf, Pl, -3, g, col=hx("#8d8a82"), roof=False)
    # pavilion edge = edge whose midpoint is closest to the photo viewpoint axis
    tgt = (718.5 - ox, -1081 - oy); pi = min(range(len(r)), key=lambda i: math.hypot((r[i][0] + r[(i + 1) % len(r)][0]) / 2 - tgt[0], (r[i][1] + r[(i + 1) % len(r)][1]) / 2 - tgt[1]))
    SB = hx("#a9a597")
    for i, a, b, L, t, n in edge_iter(r):
        if L < 2.2: m.wall(mw, a, b, g, z3, (4, 4), W); continue
        if i == pi:   # stone pavilion
            ang = math.atan2(t[1], t[0])
            sm = m.mat("wall")
            nb = 5; bw = L / nb
            run(a, b, g, e0, L / 5, lambda u0, u1, f0, f1, k, nb_, L_: D.rect_pts((u0 + u1) / 2 - 0.9, f0 + 1.2, (u0 + u1) / 2 + 0.9, f0 + 3.7) if k in (0, 4) else None, 0.4, 0.22, 0.0, SB)
            run(a, b, z1, e1, 4.0, rect_hole(1.5, 3.1, 0.8), 0.3, 0.28, 0.14, SB)
            run(a, b, z2, e2, 4.0, rect_hole(1.4, 2.6, 0.8), 0.3, 0.24, 0.12, SB)
            pilasters(m, mf, a, b, g, z3, L / 5, 1.1, 0.35, hx("#bdbab2"))
            # three iron-door portals on the ground floor (dark insets) + medallion pediment
            for k in (1, 2, 3):
                p = D.P3(a, t, n, L * (k + 0.5) / 5, 0, 0.5)
                m.box(mf, p[0], p[1], 2.4, 0.22, g, g + 3.6, rot=ang, col=hx("#1d1d1f"))
            D.band(m, mf, a, b, z3 - 0.5, z3 + 0.4, 0.5, hx("#c6c3bb"))
            D.band(m, mf, a, b, g + e0 - 0.15, g + e0 + 0.15, 0.25, hx("#c6c3bb"))
            # pediment
            uc = L / 2
            A = D.P3(a, t, n, 0, z3 + 0.4, 0.5); Bp = D.P3(a, t, n, L, z3 + 0.4, 0.5); T = D.P3(a, t, n, uc, z3 + 0.4 + 4.6, 0.5)
            m.tri(mf, [A, Bp, T], col=hx("#bdbab2"))
            continue
        run(a, b, g, e0, 3.9, rect_hole(1.5, 2.9, 0.9), 0.3, 0.2, 0.1, GREY)
        run(a, b, z1, e1, 3.9, rect_hole(1.5, 3.0, 0.8), 0.3, 0.22, 0.12, GREY)
        run(a, b, z2, e2, 3.9, rect_hole(1.5, 2.6, 0.8), 0.3, 0.2, 0.1, GREY)
        D.band(m, mf, a, b, z1 - 0.15, z1 + 0.12, 0.1, GREY)
        D.band(m, mf, a, b, z3 - 0.5, z3 + 0.15, 0.55, hx("#d6ceb7"))
        # eyebrow dormers on the mansard slope
        nd = max(1, int(L // 3.9)); ang = math.atan2(t[1], t[0])
        for k in range(nd):
            p = D.P3(a, t, n, (k + 0.5) * L / nd, 0, -0.7)
            m.box(mf, p[0], p[1], 1.5, 1.3, z3 + 0.4, z3 + 3.3, rot=ang, col=hx("#6c6a68"))
            q0 = D.P3(a, t, n, (k + 0.5) * L / nd - 0.55, z3 + 0.8, -0.03); q1 = D.P3(a, t, n, (k + 0.5) * L / nd + 0.55, z3 + 0.8, -0.03)
            m.quad(mg, [q0, q1, (q1[0], q1[1], z3 + 2.9), (q0[0], q0[1], z3 + 2.9)], [(0.0, 0.25), (1 / 8, 0.25), (1 / 8, 1.0), (0.0, 1.0)], n=(n[0], n[1], 0))
    # mansard roof in two slopes + flat deck
    A = Pl.buffer(0.45, join_style=2)
    q1 = taper(m, mf, A, z3 + 0.15, z3 + 5.8, 0.9, SLATE, cap=False)
    top = g + H - 0.4
    q2 = taper(m, mf, q1, z3 + 5.8, max(top, z3 + 7.0), 0.55, hx("#66645f"), cap=True)
    info(m, "bezirk")
    finish(m, "bezirksgebaeude", "Bezirksgebaeude Badenerstrasse", ox, oy, oz, hide_union("Bezirksgebaeude Badenerstrasse", hide_of(Bs)))


if __name__ == "__main__":
    build()
