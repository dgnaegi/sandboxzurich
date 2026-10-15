"""Sihlpost (Kasernenstrasse 95-97 at Europaallee), 1930 Neue Sachlichkeit post office: ~124 m long block, rough grey-beige stone plinth with tall barred windows,
cream stone-clad upper floors with narrow vertical windows between stone piers, set-back top floor, square clock tower (dark grey-brown stone) at the NE end.
Photos: research/v3/sihlpost.md (Mapillary #12 #0, Panoramax #24 #25)"""
from k4w3_kit import *
from k45_volkshaus import plaster


def build():
    Bs, ox, oy, oz = setup(["ID_9B59B82D"])
    B = Bs[0]; H = B["zmax"] - oz
    rng = np.random.default_rng(21)
    Pl = orient(localize(outline(B["fp"], 0.8), ox, oy), 1.0); r = list(Pl.exterior.coords)[:-1]
    m = Model("sihlpost")
    STONE = hexc("#d2c9b3")
    mw = m.mat("wall", plaster(STONE, seed=3, stains=0.008))
    sign = both(strip([(0, 560, "SIHLPOST", "#2a2a2a", "#d2c9b3", None)], size=22), clock_painter(700, face="#ece8d8", ring="#202020"), clock_painter(740, face="#ece8d8", ring="#202020"))
    ga = D.glass_atlas_g(frame="#e8e3d4", glass="#303a40", sky="#8da1ae", cols=2, rows=4, seed=22, lit_p=0.4, sign=sign, cw=64, ch=96,
                         curtain_cols=[(226, 222, 212), (200, 196, 186), (170, 176, 180)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W))
    run = make_run(m, mw, mg, mf, rng, W)
    PIER, PLINTH, BAND, DARK = hx("#cfc7b2"), hx("#a39b88"), hx("#bdb59f"), hx("#3b3a38")
    g = 0.3; e0 = 7.0; fh = 3.9; z1 = g + e0; zt = z1 + 4 * fh; za = zt + 3.4
    m.extrude(mf, mf, Pl, -3, g, col=hx("#8a8374"), roof=False)
    edges = list(edge_iter(r))
    # tower position: NE end (max x+y), placed on the longest edge's inner side
    big = max(edges, key=lambda e: e[3]); _, a0, b0, L0, t0, n0 = big
    end = b0 if (b0[0] + b0[1]) > (a0[0] + a0[1]) else a0
    sgn = -1 if end is b0 else 1
    tc = (end[0] + t0[0] * sgn * 6.0 - n0[0] * 5.5, end[1] + t0[1] * sgn * 6.0 - n0[1] * 5.5)
    for i, a, b, L, t, n in edges:
        if L < 2.5: m.wall(mw, a, b, g, za, (4, 4), W); continue
        # plinth floor: rough stone, big barred windows
        run(a, b, g, e0, 4.2, rect_hole(2.7, 3.9, 1.3), 0.4, 0.3, 0.0, PLINTH, reveal=hx("#4a4a48"))
        for f in range(4):
            run(a, b, z1 + f * fh, fh, 1.95, rect_hole(1.15, 2.6, 0.75), 0.3, 0.0, 0.0, PIER, reveal=hx("#d8d1bd"))
        # frames/piers
        pilasters(m, mf, a, b, z1, zt, 1.95, 0.55, 0.22, PIER)
        D.band(m, mf, a, b, z1 - 0.4, z1 + 0.25, 0.35, BAND)
        D.band(m, mf, a, b, zt - 0.1, zt + 0.4, 0.5, BAND)
    # recessed top floor
    At = Pl.buffer(-2.2, join_style=2)
    for g_ in ([At] if At.geom_type == "Polygon" else list(At.geoms)):
        if g_.area < 20: continue
        g_ = orient(g_.simplify(0.4), 1.0); ra = list(g_.exterior.coords)[:-1]
        for i, a, b, L, t, n in edge_iter(ra):
            if L < 2.5: m.wall(mw, a, b, zt + 0.4, za, (4, 4), W); continue
            D.ribbon_floors(m, mw, mg, mf, a, b, zt + 0.4, 1, za - zt - 0.4, 0.8, 1.8, 0.12, W, hx("#e8e3d4"), rng, wmod=(4, 3), seg=1.95, pier=0.04)
        m.flat(mf, g_, za, hx("#8a8984"))
    m.flat(mf, Pl, zt + 0.4, hx("#8a8984"))
    # clock tower
    ang = math.atan2(t0[1], t0[0]); TW = 8.5; zT = H - 0.4
    m.box(mw, tc[0], tc[1], TW, TW, g, zT, rot=ang, col=hx("#a89f8a"), mod=(4, 4), mr=mf, rcol=hx("#5a5750"))
    for sx, sy, nrm in ((0, 1, n0), (0, -1, (-n0[0], -n0[1])), (1, 0, t0), (-1, 0, (-t0[0], -t0[1]))):
        # vertical slit windows + clock on the upper part of every face
        c = (tc[0] + (n0[0] * sy + t0[0] * sx) * (TW / 2 + 0.06), tc[1] + (n0[1] * sy + t0[1] * sx) * (TW / 2 + 0.06))
        tan = (-nrm[1], nrm[0])
        for zz, hh in ((g + 6.0, 1.8), (g + 11.0, 1.8), (g + 16.0, 1.8)):
            for off in (-1.5, 1.5):
                p0 = (c[0] + tan[0] * (off - 0.3), c[1] + tan[1] * (off - 0.3), zz); p1 = (c[0] + tan[0] * (off + 0.3), c[1] + tan[1] * (off + 0.3), zz)
                m.quad(mg, [p0, p1, (p1[0], p1[1], zz + hh), (p0[0], p0[1], zz + hh)], [(0.0, 0.25), (1 / 8, 0.25), (1 / 8, 1.0), (0.0, 1.0)], n=(nrm[0], nrm[1], 0))
        zc = zT - 5.0; s = 3.2
        p0 = (c[0] - tan[0] * s / 2, c[1] - tan[1] * s / 2, zc - s / 2); p1 = (c[0] + tan[0] * s / 2, c[1] + tan[1] * s / 2, zc - s / 2)
        m.quad(mg, [p0, p1, (p1[0], p1[1], zc + s / 2), (p0[0], p0[1], zc + s / 2)], [(700 / 1024, 0.0), (732 / 1024, 0.0), (732 / 1024, 0.25), (700 / 1024, 0.25)], n=(nrm[0], nrm[1], 0))
    m.box(mf, tc[0], tc[1], TW + 0.6, TW + 0.6, zT, zT + 0.5, rot=ang, col=hx("#7c7566"))
    info(m, "sihlpost")
    finish(m, "sihlpost", "Sihlpost", ox, oy, oz, hide_union("Sihlpost", hide_of(Bs)))


if __name__ == "__main__":
    build()
