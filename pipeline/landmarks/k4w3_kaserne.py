"""Kaserne Zuerich (Kasernenstrasse 49/Kasernenareal), 1875 Neurenaissance barracks: long four-storey wings in yellow sandstone-plaster with stone bands,
rect windows with stone surrounds, central pavilion on the main facade with four crenellated turrets, clock and crest, grey hip roofs.
Photos: research/v3/kaserne.md (Commons #11 #12 #0, Mapillary/Panoramax #8)"""
from k4w3_kit import *
from k45_volkshaus import plaster


def build():
    Bs, ox, oy, oz = setup(["ID_50C915A2"])
    B = Bs[0]; H = B["zmax"] - oz
    rng = np.random.default_rng(12)
    Pl = orient(localize(outline(B["fp"], 1.2), ox, oy), 1.0); r = list(Pl.exterior.coords)[:-1]
    m = Model("kaserne")
    SAND = hexc("#d3c391")
    mw = m.mat("wall", plaster(SAND, seed=6, stains=0.012))
    sign = both(strip([(0, 640, "KASERNE", "#2b2a28", "#d3c391", None)], size=22), clock_painter(700))
    ga = D.glass_atlas_g(frame="#efe9d8", glass="#2a343d", sky="#8da3b3", cols=2, rows=3, seed=13, lit_p=0.3, sign=sign, curtain_cols=[(226, 222, 210), (190, 180, 160), (170, 176, 182)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W))
    run = make_run(m, mw, mg, mf, rng, W)
    STN, BAND, ROOF, DARK = hx("#b8a77c"), hx("#c4b588"), hx("#7b463a"), hx("#4a4642")
    g = 0.3; fhs = [4.6, 4.3, 4.0, 3.7]; zs = [g]
    for h in fhs: zs.append(zs[-1] + h)
    zt = zs[-1]
    m.extrude(mf, mf, Pl, -3, g, col=hx("#8a826e"), roof=False)
    edges = list(edge_iter(r)); main = max(edges, key=lambda e: e[3])[0]
    for i, a, b, L, t, n in edges:
        if L < 2.5: m.wall(mw, a, b, g, zt, (4, 4), W); continue
        run(a, b, zs[0], fhs[0], 3.4, rect_hole(1.5, 2.9, 0.9), 0.35, 0.2, 0.1, STN)
        for f in (1, 2, 3):
            run(a, b, zs[f], fhs[f], 3.4, rect_hole(1.5, 2.5, 0.8), 0.3, 0.18, 0.1, STN)
        for f in (1, 2, 3): D.band(m, mf, a, b, zs[f] - 0.15, zs[f] + 0.12, 0.1, BAND)
        D.band(m, mf, a, b, zt - 0.6, zt + 0.2, 0.45, BAND)
    # main facade: central pavilion with 4 turrets, clock and crest
    _, a, b, L, t, n = edges[main]; ang = math.atan2(t[1], t[0]); u = L / 2; pw = min(16.0, L * 0.4)
    z_p = zt + 1.2
    p = D.P3(a, t, n, u, 0, 0.35); m.box(mw, p[0], p[1], pw, 0.7, g, z_p, rot=ang, col=W, mod=(4, 4))
    p = D.P3(a, t, n, u, 0, 0.6); m.box(mf, p[0], p[1], pw + 0.4, 0.3, z_p - 0.2, z_p + 0.15, rot=ang, col=BAND)
    p = D.P3(a, t, n, u, 0, 0.75); m.box(mf, p[0], p[1], 3.0, 0.5, g, 3.4, rot=ang, col=hx("#3b302a"))   # portal
    m.box(mf, p[0], p[1], 3.8, 1.4, 3.4, 3.7, rot=ang, col=hx("#7a6f5a"))   # canopy
    UV = [(0.0, 0.25), (1 / 8, 0.25), (1 / 8, 1.0), (0.0, 1.0)]
    for uo in (-pw / 2, -pw / 6, pw / 6, pw / 2):   # four full-height turrets
        q = D.P3(a, t, n, u + uo, 0, 0.9)
        m.box(mw, q[0], q[1], 2.0, 2.0, g, z_p + 2.2, rot=ang, col=W, mod=(4, 4))
        m.box(mf, q[0], q[1], 2.3, 2.3, z_p + 2.2, z_p + 2.5, rot=ang, col=BAND)
        for k in range(3):   # crenellations
            for l_ in (-0.95, 0.95):
                cx = q[0] + t[0] * (-0.8 + k * 0.8) + n[0] * l_; cy = q[1] + t[1] * (-0.8 + k * 0.8) + n[1] * l_
                m.box(mf, cx, cy, 0.4, 0.4, z_p + 2.5, z_p + 3.0, rot=ang, col=BAND)
        q0 = D.P3(a, t, n, u + uo - 0.3, z_p - 7.0, 1.91); q1 = D.P3(a, t, n, u + uo + 0.3, z_p - 7.0, 1.91)
        m.quad(mg, [q0, q1, (q1[0], q1[1], z_p - 5.2), (q0[0], q0[1], z_p - 5.2)], UV, n=(n[0], n[1], 0))
    for zz, hh in ((zs[1] + 0.8, 2.6), (zs[2] + 0.8, 2.4)):   # pavilion windows
        for k in (-1, 0, 1):
            q0 = D.P3(a, t, n, u + k * 3.6 - 0.7, zz, 0.72); q1 = D.P3(a, t, n, u + k * 3.6 + 0.7, zz, 0.72)
            m.quad(mg, [q0, q1, (q1[0], q1[1], zz + hh), (q0[0], q0[1], zz + hh)], UV, n=(n[0], n[1], 0))
    clock_quad(m, mg, a, t, n, u, zs[3] + 1.8, 2.8, 700, off=0.74)
    q = D.P3(a, t, n, u, z_p + 1.4, 0.74)
    m.box(mf, q[0], q[1], 2.2, 0.3, z_p + 0.2, z_p + 2.4, rot=ang, col=hx("#a8905a"))   # crest
    # roofs: hip-like slope over the ring, pavilion flat-topped
    slope_roof(m, mf, Pl.buffer(0.5, join_style=2), zt + 0.2, 6.8, 7.0, ROOF)
    info(m, "kaserne")
    finish(m, "kaserne", "Kaserne Zuerich", ox, oy, oz, hide_union("Kaserne Zuerich", hide_of(Bs)))


if __name__ == "__main__":
    build()
