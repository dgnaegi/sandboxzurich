"""Kirche St. Peter und Paul (Werdstrasse 57, Aussersihl), 1873-74 neo-Gothic: white plastered nave with tall pointed windows in grey stone tracery, steep dark slate gable
roof, lower side wing, square sandstone-yellow clock tower with louvred belfry and a thin dark slate spire (57 m).
Photos: research/v3/peter_paul.md (Commons #11-#14, #4 door)"""
from k4w3_kit import *
from k45_volkshaus import plaster


def build():
    Bs, ox, oy, oz = setup(["ID_89927E57"])
    B = Bs[0]; H = B["zmax"] - oz
    rng = np.random.default_rng(31)
    Pl = orient(localize(outline(B["fp"], 0.5), ox, oy), 1.0); r = list(Pl.exterior.coords)[:-1]
    m = Model("peterpaul")
    WHITE = hexc("#f4f0e6")
    mw = m.mat("wall", plaster(WHITE, seed=9, stains=0.01))
    sign = clock_painter(700, face="#f4f0e2", ring="#2a2a2a")
    ga = D.glass_atlas_g(frame="#bdbdb8", glass="#33404b", sky="#7b92a8", cols=2, rows=4, seed=32, lit_p=0.25, sign=sign, curtains=False)
    mg = m.mat("glass", *ga, rough=0.25); mf = m.mat("flat", solid(W))
    run = make_run(m, mw, mg, mf, rng, W)
    GREY, SLATE, SAND = hx("#a8a8a2"), hx("#3c3e44"), hx("#d6c59a")
    g = 0.3; eave = 13.0; ridge_rise = 9.5; low = 8.0
    # frame: u along the nave toward NW, v across toward east; origin = SE end of the west wall
    O = (0.7, -24.2); tx, ty = -0.416, 0.909; nx, ny = 0.909, 0.416
    uv = lambda x, y: ((x - O[0]) * tx + (y - O[1]) * ty, (x - O[0]) * nx + (y - O[1]) * ny)
    xy = lambda u, v: (O[0] + tx * u + nx * v, O[1] + ty * u + ny * v)
    m.extrude(mf, mf, Pl, -3, g, col=hx("#8a8579"), roof=False)
    for i, a, b, L, t, n in edge_iter(r):
        mu, mv = uv((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        hgt = eave if mv < 17.5 else low
        if L < 3.0 or (mu > 40.5 and L < 18):   # short edges / tower base: plain wall (tower is added separately)
            m.wall(mw, a, b, g, hgt, (4, 4), W); continue
        def pw(u0, u1, f0, f1, k, nb, L_, hh=hgt):
            uc = (u0 + u1) / 2; w = 1.7
            return D.pointed_pts(uc - w / 2, f0 + (3.2 if hh > 10 else 2.6), uc + w / 2, f0 + (7.6 if hh > 10 else 5.0))
        run(a, b, g, hgt - g, 4.6, pw, 0.35, 0.22, 0.0, GREY)
        D.band(m, mf, a, b, hgt - 0.35, hgt + 0.2, 0.3, hx("#d8d4c8"))
        # buttress-like piers between windows (nave only)
        if hgt > 10: pilasters(m, mf, a, b, g, hgt - 0.35, 4.6, 0.45, 0.35, hx("#dcd8cc"))
    # nave gable roof
    nave = Polygon([xy(0, 0), xy(0, 16), xy(50, 16), xy(50, 0)])
    rc = rect_of(nave)
    gable_roof(m, mf, mw, rc, eave + 0.1, ridge_rise, SLATE, hexl_ := hx("#ece8de"), eave=0.35)
    # clerestory wall above the low side wing (east side of the nave)
    ca, cb = xy(0.0, 16.0), xy(19.5, 16.0)
    run(ca, cb, low, eave - low, 4.6, lambda u0, u1, f0, f1, k, nb, L_: D.pointed_pts((u0 + u1) / 2 - 0.8, f0 + 0.8, (u0 + u1) / 2 + 0.8, f0 + 3.6), 0.3, 0.2, 0.0, GREY)
    D.band(m, mf, ca, cb, eave - 0.35, eave + 0.2, 0.3, hx("#d8d4c8"))
    # side wing: flat dark roof
    wing = Pl.difference(nave.buffer(0.3)); 
    for g_ in ([wing] if wing.geom_type == "Polygon" else list(wing.geoms)):
        if g_.area > 5: m.flat(mf, g_, low + 0.05, hx("#4a4b4f"))
    # tower at the NW end
    tcx, tcy = xy(45.2, 8.0); ang = math.atan2(ty, tx); TW = 9.6; zb = 36.0
    m.box(mw, tcx, tcy, TW, TW, g, zb, rot=ang, col=hx("#f2ecd2"), mod=(4, 4))
    for k in range(4):   # faces: belfry louvres, small windows, clock
        a_ = ang + k * math.pi / 2; nrm = (math.cos(a_ + math.pi / 2), math.sin(a_ + math.pi / 2)); tan = (-nrm[1], nrm[0])
        c = (tcx + nrm[0] * (TW / 2 + 0.05), tcy + nrm[1] * (TW / 2 + 0.05))
        # Note: nrm rotates with k; tx,ty axis = (ang) so face k=0 normal points +90deg from axis
        for zz, hh, w_ in ((10.0, 3.0, 0.9), (22.0, 2.2, 0.9)):
            p0 = (c[0] - tan[0] * w_ / 2, c[1] - tan[1] * w_ / 2, zz); p1 = (c[0] + tan[0] * w_ / 2, c[1] + tan[1] * w_ / 2, zz)
            m.quad(mg, [p0, p1, (p1[0], p1[1], zz + hh), (p0[0], p0[1], zz + hh)], [(0.0, 0.25), (1 / 8, 0.25), (1 / 8, 1.0), (0.0, 1.0)], n=(nrm[0], nrm[1], 0))
        zc = 29.0; s = 3.4
        p0 = (c[0] - tan[0] * s / 2, c[1] - tan[1] * s / 2, zc - s / 2); p1 = (c[0] + tan[0] * s / 2, c[1] + tan[1] * s / 2, zc - s / 2)
        m.quad(mg, [p0, p1, (p1[0], p1[1], zc + s / 2), (p0[0], p0[1], zc + s / 2)], [(700 / 1024, 0.0), (732 / 1024, 0.0), (732 / 1024, 0.25), (700 / 1024, 0.25)], n=(nrm[0], nrm[1], 0))
        # belfry louvre opening (dark)
        for off in (-1.6, 1.6):
            q0 = (c[0] + tan[0] * (off - 0.8) + nrm[0] * 0.02, c[1] + tan[1] * (off - 0.8) + nrm[1] * 0.02, zb - 5.2); q1 = (c[0] + tan[0] * (off + 0.8) + nrm[0] * 0.02, c[1] + tan[1] * (off + 0.8) + nrm[1] * 0.02, zb - 5.2)
            m.quad(mf, [q0, q1, (q1[0], q1[1], zb - 0.9), (q0[0], q0[1], zb - 0.9)], col=hx("#2a2a2c"), n=(nrm[0], nrm[1], 0))
    m.box(mf, tcx, tcy, TW + 0.5, TW + 0.5, zb - 0.1, zb + 0.4, rot=ang, col=hx("#bdb8a6"))
    # spire: octagonal pyramid, slate; pinnacles at the corners
    m.cylinder(mf, tcx, tcy, TW * 0.5, zb + 0.4, H - 4.0, n=8, col=SLATE, r1=0.25, cap=None, smooth=False)
    m.cylinder(mf, tcx, tcy, 0.2, H - 4.2, H, n=6, col=hx("#b8a040"))
    for k in range(4):
        a_ = ang + math.pi / 4 + k * math.pi / 2; px, py = tcx + math.cos(a_) * TW * 0.62, tcy + math.sin(a_) * TW * 0.62
        m.cylinder(mf, px, py, 0.55, zb + 0.4, zb + 4.0, n=6, col=hx("#cfc7a8"), r1=0.05)
    # portal at the SE end (dark door + stone frame)
    q = xy(0.0, 8.0); m.box(mf, q[0], q[1], 3.0, 0.4, g, g + 4.6, rot=ang, col=hx("#2d2a28"))
    info(m, "peterpaul")
    finish(m, "peterpaul", "Kirche St. Peter und Paul", ox, oy, oz, hide_union("Kirche St. Peter und Paul", hide_of(Bs)))


if __name__ == "__main__":
    build()
