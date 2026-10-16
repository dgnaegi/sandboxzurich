"""Johanneskirche Limmatplatz (1898, neo-Romanesque/Renaissance): rusticated warm-grey sandstone, slate gable roof, tall arched nave windows, square tower at the SW end
with arched portal, paired windows, blue-dial clock stage, louvred belfry and a slender green copper spire; plus the octagonal fountain pavilion (cream sandstone,
dark-red cornice, verdigris copper dome, round oculi, shell niche + stone basin) at the street corner.
Photos: research/v3/johanneskirche.md (Commons #10 #11 #12 by Balise42 / Ralfhauser, Mapillary #2 Yha1, Panoramax #18 #19)"""
from k4w4_kit import *
from k45_volkshaus import plaster

CH, PAV = "ID_117A35C6", "ID_0D8FAAC7"


def build():
    setup4()
    B = bid(CH); Pm = outline(B["fp"], 0.5); c = Pm.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    A = math.radians(42); rng = np.random.default_rng(71)
    m = Model4("johanneskirche")
    mw = m.mat("wall", D.ashlar(hexc("#a89880"), rough=0.09, seed=5), rough=0.95)
    mp = m.mat("plaster", plaster(hexc("#d9c8a6"), seed=9, stains=0.02), rough=0.95)
    ga = D.glass_atlas_g(frame="#3a342f", glass="#2a3842", sky="#8aa0ae", cols=2, rows=4, seed=3, sign=both(clock_paint(700), clock_paint(740)), cw=128, ch=96, lit_p=0.35,
                         curtain_cols=[(190, 170, 130), (150, 120, 90)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W4))
    STONE, DRESS, SLATE, COPPER = hexl("#a89880"), hexl("#cdbf9f"), (66, 68, 74, 255), (104, 156, 132, 255)
    T = (1264.2 - ox, -30.2 - oy); TS = 7.2
    Pl = orient(localize(Pm, ox, oy), 1.0)
    fr = frame_xy(T[0], T[1], A)
    Tsq = orient(Polygon([fr(-TS / 2, -TS / 2), fr(TS / 2, -TS / 2), fr(TS / 2, TS / 2), fr(-TS / 2, TS / 2)]), 1.0)
    N = Pl.difference(Tsq.buffer(0.05, join_style=2))
    Ns = [g for g in polys_of(N) if g.area > 20]
    ZE = 14.0
    for g in Ns:
        g = orient(g.simplify(0.3), 1.0)
        for a, b in edges_of(g, 0.3): m.wall(mw, a, b, -3.0, 0.0, (4, 4), (120, 108, 92, 255))
        def hole(u0, u1, f0, f1, fi, L):
            uc = (u0 + u1) / 2; w = min(2.1, u1 - u0 - 1.2); return D.arch_pts(uc - w / 2, f0 + 3.4, uc + w / 2, f0 + 9.0)
        facade(m, (mw, mg, mf), g, 0.0, ZE, None, fh=ZE, bayw=5.4, hole=hole, depth=0.5, wall_col=W4, reveal_col=DRESS, rng=rng, wmod=(4.0, 4.0),
               cornice=(hexl("#bfb092"), 0.4, 0.55), wsill=0.1, deep_z=99)
        for a, b in edges_of(g, 2.0): D.band(m, mf, a, b, 3.0, 3.3, 0.12, hexl("#bcae92"))   # string course
    for g in Ns:
        g = orient(g.simplify(0.3), 1.0)
        D.band(m, mf, g.exterior.coords[0], g.exterior.coords[1], ZE, ZE, 0, SLATE) if False else None
        hip_roof(m, mf, g.buffer(0.4, join_style=2).simplify(0.4), ZE + 0.1, 6.0, 5.5, SLATE)
    # ---- tower ----
    for a, b in edges_of(Tsq, 1.0):
        L, t, n = D.frame_of(a, b); street = (n[0] * -0.55 + n[1] * -0.85) > 0.7
        def h1(u0, u1, f0, f1, fi):
            if street: return D.arch_pts(L / 2 - 1.3, f0, L / 2 + 1.3, f0 + 4.4)
            return D.rect_pts(L / 2 - 0.25, f0 + 3.0, L / 2 + 0.25, f0 + 6.5)
        D.wall_run(m, mw, mg, mf, a, b, 0.0, 1, 10.0, L, h1, 0.45, W4, DRESS, rng, (4, 4))
        D.wall_run(m, mw, mg, mf, a, b, 10.0, 1, 10.0, L, lambda u0, u1, f0, f1, fi: D.arch_pts(L / 2 - 0.55, f0 + 3.0, L / 2 + 0.55, f0 + 5.4), 0.4, W4, DRESS, rng, (4, 4))
        m.wall(mw, a, b, 20.0, 28.0, (4, 4), W4)
        D.wall_run(m, mw, mg, mf, a, b, 28.0, 1, 8.0, L, lambda u0, u1, f0, f1, fi: D.arch_pts(L / 2 - 1.1, f0 + 1.0, L / 2 + 1.1, f0 + 4.4), 0.5, W4, DRESS, rng, (4, 4))
        strip_quad(m, mg, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), t, 2.5, 2.5, 23.0, 700, 732, off=0.12)
        for zz, o in ((10.0, 0.25), (20.0, 0.3), (28.0, 0.25), (36.0, 0.55)): D.band(m, mf, a, b, zz - 0.2, zz + 0.25, o, hexl("#bcae92"))
    m.flat(mf, Tsq, 36.3, (90, 90, 88, 255))
    for k in range(4):
        sx, sy = (1 if k in (0, 3) else -1), (1 if k < 2 else -1); px, py = fr(sx * (TS / 2 - 0.4), sy * (TS / 2 - 0.4))
        cone8(m, mf, px, py, 0.55, 0.0, 36.3, 39.6, hexl("#bfb293"), n=4, rot=A + math.pi / 4)
    cone8(m, mf, T[0], T[1], TS / 2 * 1.02 / math.cos(math.pi / 8), 0.12, 36.3, 48.2, COPPER, n=8, rot=A + math.pi / 8)
    m.box(mf, T[0], T[1], 0.2, 0.2, 47.6, 49.4, col=(200, 170, 60, 255))
    # ---- fountain pavilion ----
    pb = bid(PAV); pc = pb["c"]; px, py = pc[0] - ox, pc[1] - oy; gz = ground(*pc) - oz; r = 1.95
    cone8(m, mp, px, py, r, r, gz - 0.4, gz + 3.0, W4, n=8, rot=math.pi / 8)
    cone8(m, mf, px, py, r + 0.25, r + 0.05, gz + 3.0, gz + 3.4, hexl("#7b2f26"), n=8, rot=math.pi / 8)
    dome8(m, mf, px, py, r + 0.3, gz + 3.4, 2.1, (118, 168, 142, 255), n=8, rot=math.pi / 8)
    fa = math.atan2(-1.0, 0.25)   # basin side (toward the street)
    for k in range(8):
        ang = math.pi / 8 + k * math.pi / 4 + math.pi / 8
        if k in (1, 5):
            qx, qy = px + (r + 0.02) * math.cos(ang), py + (r + 0.02) * math.sin(ang)
            m.box(mf, qx, qy, 0.75, 0.12, gz + 1.7, gz + 2.5, rot=ang + math.pi / 2, col=(40, 40, 42, 255))
    m.box(mf, px + (r + 0.1) * math.cos(fa), py + (r + 0.1) * math.sin(fa), 1.3, 0.5, gz + 0.5, gz + 2.5, rot=fa + math.pi / 2, col=(120, 100, 76, 255))
    m.cylinder(mf, px + (r + 0.8) * math.cos(fa), py + (r + 0.8) * math.sin(fa), 0.85, gz, gz + 0.65, n=12, col=(150, 146, 138, 255), cap=mf, capcol=(120, 130, 134, 255))
    sinfo(m, "johanneskirche")
    finish(m, "johanneskirche", "Johanneskirche Limmatplatz", ox, oy, oz, hide_pts([CH, PAV]))


if __name__ == "__main__":
    build()
