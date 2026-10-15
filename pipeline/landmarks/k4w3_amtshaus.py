"""Amtshaus Helvetiaplatz (Molkenstrasse 5 / Helvetiaplatz), 1963: two 5+1-storey concrete office blocks on pilotis. Grey off-form concrete spandrels,
beige-brown stone piers every ~4.4 m, ribbon windows with white 1.45 m mullions + transom, open arcade at ground level (columns, glazed recess),
set-back light attic. Photos: research/v3/amtshaus_helvetia.md"""
from k4w3_kit import *


def build():
    Bs, ox, oy, oz = setup(["ID_880D30BC", "ID_160893D0"])
    rng = np.random.default_rng(4)
    m = Model("amtshaus_helvetia")
    mw = m.mat("wall", K.concrete_tex("#8d8a85", panel=(2, 1)).convert("RGBA"))
    ga = D.glass_atlas_g(frame="#e9e7e0", glass="#4a5559", sky="#8fa0a8", cols=1, rows=2, seed=7, lit_p=0.3, curtains=True, cw=96, ch=96, bar=3, curtain_cols=[(228, 226, 220), (200, 200, 196), (170, 176, 182), (214, 206, 190)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W))
    PIER, DARK, SLAB = hx("#a29a8b"), hx("#55524e"), hx("#7c7a75")
    for B in Bs:
        H = B["zmax"] - oz
        ring = ring_of(B, ox, oy); Pl = Polygon(ring)
        eg = 4.7; fh = 3.55; nf = max(3, int(round((H - eg - 2.6) / fh))); z1 = 0.3 + eg; ztop = z1 + nf * fh
        r = list(ring.exterior.coords)[:-1]
        m.extrude(mf, mf, Pl, -3, 0.3, col=hx("#6a6863"), roof=False)
        for i, a, b, L, t, n in edge_iter(r):
            if L < 2.5: m.wall(mw, a, b, z1, ztop, (4, 4), W); continue
            # upper floors: spandrel + ribbon window, white mullions every 1.45 m
            D.ribbon_floors(m, mw, mg, mf, a, b, z1, nf, fh, 1.0, 1.35, 0.14, W, hx("#e4e2da"), rng, wmod=(4.0, 3.55), seg=L / max(3, round(L / 1.45)), slab_out=0.06, slab_col=hx("#9b9891"), pier=0.03)
            pilasters(m, mf, a, b, z1, ztop, 4.35, 0.5, 0.2, PIER, skip_end=0.0)
            # arcade: columns in front, glazed recess behind
            nb = max(1, int(round(L / 6.4))); ang = math.atan2(t[1], t[0])
            for k in range(nb + 1):
                p = D.P3(a, t, n, k * L / nb, 0, -0.9); m.box(mf, p[0], p[1], 0.75, 0.75, 0.3, z1, rot=ang, col=DARK)
            D.band(m, mf, a, b, z1 - 0.55, z1, 0.05, SLAB)
        # recessed ground floor: inner ring, glazed shopfront/dark concrete
        Pin = Pl.buffer(-4.3, join_style=2)
        if Pin.is_empty: Pin = Pl.buffer(-2.5, join_style=2)
        if Pin.geom_type == "MultiPolygon": Pin = max(Pin.geoms, key=lambda p: p.area)
        Pin = orient(Pin.simplify(0.4), 1.0)
        ri = list(Pin.exterior.coords)[:-1]
        for i, a, b, L, t, n in edge_iter(ri):
            if L < 2: m.wall(mw, a, b, 0.3, z1, (4, 4), W); continue
            D.ribbon_floors(m, mw, mg, mf, a, b, 0.3, 1, eg, 0.25, 3.0, 0.12, hx("#6b6965"), hx("#444"), rng, wmod=(4, 4), seg=2.4, pier=0.05)
        m.flat(mf, Pl.difference(Pin.buffer(0.01)), z1 - 0.01, hx("#6d6b67"), up=False)
        # set-back attic
        At = Pl.buffer(-2.2, join_style=2)
        if At.geom_type == "MultiPolygon": At = max(At.geoms, key=lambda p: p.area)
        At = orient(At.simplify(0.4), 1.0)
        m.flat(mf, Pl, ztop, hx("#8a8984"), up=True)
        for i, a, b, L, t, n in edge_iter(r):
            D.band(m, mf, a, b, ztop - 0.3, ztop + 0.3, 0.12, hx("#9b9891"))
        ra = list(At.exterior.coords)[:-1]
        for i, a, b, L, t, n in edge_iter(ra):
            if L < 2: m.wall(mw, a, b, ztop, ztop + 2.8, (4, 4), W); continue
            D.ribbon_floors(m, mw, mg, mf, a, b, ztop, 1, 2.8, 0.55, 1.6, 0.1, hx("#a9a79f"), hx("#e4e2da"), rng, wmod=(4, 3), seg=1.45, pier=0.03)
        m.flat(mf, At, ztop + 2.8, hx("#a4a39d"))
    # posters at the arcade (red / yellow / blue)
    B0 = ring_of(Bs[0], ox, oy); r0 = list(B0.exterior.coords)[:-1]
    best = max(edge_iter(r0), key=lambda e: e[3]); _, a, b, L, t, n = best
    for k, c in enumerate(["#c8372d", "#f0c020", "#2f6fb5"]):
        p0 = D.P3(a, t, n, L - 6.0 + k * 1.3, 1.0, -4.15); p1 = D.P3(a, t, n, L - 5.2 + k * 1.3, 1.0, -4.15)
        m.quad(mf, [p0, p1, (p1[0], p1[1], 2.2), (p0[0], p0[1], 2.2)], col=hx(c), n=(n[0], n[1], 0))
    info(m, "amtshaus")
    finish(m, "amtshaus_helvetia", "Amtshaus Helvetiaplatz", ox, oy, oz, hide_union("Amtshaus Helvetiaplatz", hide_of(Bs)))


if __name__ == "__main__":
    build()
