"""Kollerhof (Langstrasse / Kanzleistrasse corner), 1930s Neues Bauen: curved corner block in salmon-pink plaster with continuous horizontal ribbon windows
(white frames, grey piers every ~1.7 m), strongly projecting dark canopy over a recessed ground floor, KOLLERHOF lettering, flat roof with parapet.
Photos: research/v3/kollerhof.md (Mapillary #12 #5, Panoramax #22 #23)"""
from k4w3_kit import *
from k45_volkshaus import plaster


def build():
    Bs, ox, oy, oz = setup(["ID_0DFB60C4"])
    B = Bs[0]; H = B["zmax"] - oz
    rng = np.random.default_rng(61)
    Pl = orient(localize(outline(B["fp"], 0.4), ox, oy), 1.0); r = list(Pl.exterior.coords)[:-1]
    m = Model("kollerhof")
    PINK = hexc("#e3a995")
    mw = m.mat("wall", plaster(PINK, seed=14, stains=0.01))
    sign = strip([(0, 500, "KOLLERHOF", "#f3d9c8", "#d99a86", None)], size=24, fnt="Oswald-Var")
    ga = D.glass_atlas_g(frame="#f4f2ea", glass="#3a4650", sky="#8da1b0", cols=2, rows=2, seed=62, lit_p=0.4, sign=sign, cw=128, ch=96, curtain_cols=[(236, 232, 222), (210, 200, 188), (190, 180, 170)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W))
    PIER, CANOPY, DARK = hx("#b9b4ac"), hx("#3a3b3d"), hx("#2f3032")
    g = 0.3; e0 = 4.4; fh = 3.35; nf = max(4, int(round((H - e0 - 0.9) / fh))); z1 = g + e0; zt = z1 + nf * fh
    m.extrude(mf, mf, Pl, -3, g, col=hx("#8a8580"), roof=False)
    # recessed ground floor
    Pin = Pl.buffer(-1.9, join_style=2)
    if Pin.geom_type == "MultiPolygon": Pin = max(Pin.geoms, key=lambda p: p.area)
    Pin = orient(Pin.simplify(0.3), 1.0); ri = list(Pin.exterior.coords)[:-1]
    for i, a, b, L, t, n in edge_iter(ri):
        if L < 1.5: m.wall(mw, a, b, g, z1, (4, 4), (90, 90, 92, 255)); continue
        D.ribbon_floors(m, mw, mg, mf, a, b, g, 1, e0, 0.3, 3.2, 0.1, (90, 90, 92, 255), DARK, rng, wmod=(4, 4), seg=2.2, pier=0.06)
    # upper floors: curved ribbon windows
    for i, a, b, L, t, n in edge_iter(r):
        if L < 0.8: m.wall(mw, a, b, z1, zt, (4, 4), W); continue
        D.ribbon_floors(m, mw, mg, mf, a, b, z1, nf, fh, 1.05, 1.5, 0.12, W, hx("#e8e4d8"), rng, wmod=(4, 3.35), seg=1.75, slab_out=0.08, slab_col=hx("#e3a995"), pier=0.1)
        D.band(m, mf, a, b, z1 - 0.7, z1 + 0.05, 0.9, CANOPY)
        D.band(m, mf, a, b, zt - 0.1, zt + 0.6, 0.15, hx("#e6b4a2"))
    # lettering on the longest curved facade at the 2nd floor spandrel
    # KOLLERHOF letter strip along three consecutive curved edges
    seg = [e for e in edge_iter(r) if 4 < e[3] < 14][:1]
    for i, a, b, L, t, n in seg:
        txtq(m, mg, a, t, n, 0.4, L - 0.4, z1 + 0.1 + fh + 0.05, 0.5, 0, 500, off=0.12)
    m.flat(mf, Pl, zt + 0.55, hx("#8c8a86"))
    m.flat(mf, Pl.buffer(-0.5, join_style=2), zt + 0.6, hx("#76736e"))
    info(m, "kollerhof")
    finish(m, "kollerhof", "Kollerhof", ox, oy, oz, hide_union("Kollerhof", hide_of(Bs)))


if __name__ == "__main__":
    build()
