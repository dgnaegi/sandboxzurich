"""Pfarrkirche St. Joseph (Roentgenstrasse / Kreis 5, 1890s neo-baroque): cream-white plaster nave with steep dark-brown tile gable roof, curved front gable at the SW end,
round-arched windows in stone-grey surrounds, rounded apse, slender square clock tower with louvred belfry and dark bulbous cupola.
Photos: research/v3/st_joseph.md (Mapillary #2 #11 #7 #6 #3, Panoramax #20, Commons #12-14)"""
from k4w4_kit import *
from k45_volkshaus import plaster

CH = "ID_D9A9CD22"


def build():
    setup4()
    B = bid(CH); Pm = outline(B["fp"], 0.5); c = Pm.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    (_, _), ux, uy, Lr, Wr = rect_of(Pm)
    A = math.atan2(uy, ux); rng = np.random.default_rng(97)
    m = Model4("stjoseph")
    mw = m.mat("wall", plaster(hexc("#ece4d1"), seed=12, stains=0.012), rough=0.95)
    ga = D.glass_atlas_g(frame="#e9e2d0", glass="#2c3a46", sky="#8aa0ae", cols=2, rows=3, seed=17, sign=both(clock_paint(700, face="#f4f0e2", ring="#c9a23a", dial="#f1eee4", hands="#2a2a2a"), clock_paint(740, dial="#f1eee4", hands="#2a2a2a")),
                         cw=128, ch=96, lit_p=0.3, curtain_cols=[(180, 150, 110), (210, 190, 150)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W4))
    SURR, TILE = hexl("#b9b4a6"), (88, 66, 54, 255)
    T = (855.0 - ox, 317.0 - oy); TS = 9.0
    Pl = orient(localize(Pm, ox, oy), 1.0)
    fr = frame_xy(T[0], T[1], A)
    Tsq = orient(Polygon([fr(-TS / 2, -TS / 2), fr(TS / 2, -TS / 2), fr(TS / 2, TS / 2), fr(-TS / 2, TS / 2)]), 1.0)
    N = Pl.difference(Tsq.buffer(0.05, join_style=2)); Ns = [g for g in polys_of(N) if g.area > 20]
    ZE = 11.5
    for g in Ns:
        g = orient(g.simplify(0.3), 1.0)
        for a, b in edges_of(g, 0.3): m.wall(mw, a, b, -3.0, 0.0, (4, 4), (150, 144, 130, 255))
        def hole(u0, u1, f0, f1, fi, L):
            uc = (u0 + u1) / 2; w = min(1.7, u1 - u0 - 1.0); return D.arch_pts(uc - w / 2, f0 + 2.6, uc + w / 2, f0 + 7.6)
        facade(m, (mw, mg, mf), g, 0.0, ZE, None, fh=ZE, bayw=5.0, hole=hole, depth=0.35, wall_col=W4, reveal_col=SURR, rng=rng, wmod=(4.0, 4.0),
               cornice=(hexl("#d6cfbd"), 0.45, 0.6), wsill=0.1, deep_z=99)
    (cx_, cy_), rux, ruy, L_, W_ = rect_of(Pl.difference(Tsq.buffer(1.5)))
    gable_roof(m, mf, mw, ((cx_, cy_), rux, ruy, L_, W_), ZE + 0.45, 8.0, TILE, W4, eave=0.6)
    # tower
    for a, b in edges_of(Tsq, 1.0):
        L, t, n = D.frame_of(a, b)
        m.wall(mw, a, b, 0.0, 12.0, (4, 4), W4)
        D.wall_run(m, mw, mg, mf, a, b, 12.0, 1, 8.0, L, lambda u0, u1, f0, f1, fi: D.arch_pts(L / 2 - 0.6, f0 + 2.0, L / 2 + 0.6, f0 + 5.0), 0.35, W4, SURR, rng, (4, 4))
        m.wall(mw, a, b, 20.0, 27.0, (4, 4), W4)
        strip_quad(m, mg, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), t, 3.0, 3.0, 22.5, 700, 732, off=0.12)
        D.wall_run(m, mw, mg, mf, a, b, 27.0, 1, 8.0, L, lambda u0, u1, f0, f1, fi: D.arch_pts(L / 2 - 1.0, f0 + 1.2, L / 2 + 1.0, f0 + 4.6), 0.5, W4, SURR, rng, (4, 4))
        for zz, o in ((12.0, 0.2), (20.0, 0.25), (27.0, 0.25), (35.0, 0.5)): D.band(m, mf, a, b, zz - 0.2, zz + 0.25, o, hexl("#d6cfbd"))
    m.flat(mf, Tsq, 35.3, (80, 82, 80, 255))
    dome8(m, mf, T[0], T[1], TS / 2 * 0.95, 35.3, 11.0, (58, 70, 66, 255), n=8, rot=A + math.pi / 8,
          rings=((0.55, 0.0), (1.0, 0.16), (0.92, 0.34), (0.55, 0.58), (0.22, 0.76), (0.12, 0.88), (0.0, 1.0)))
    m.box(mf, T[0], T[1], 0.2, 0.2, 46.0, 48.2, col=(200, 170, 60, 255))
    sinfo(m, "stjoseph")
    finish(m, "stjoseph", "Pfarrkirche St. Joseph Roentgenstrasse", ox, oy, oz, hide_pts([CH]))


if __name__ == "__main__":
    build()
