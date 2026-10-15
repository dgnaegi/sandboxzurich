"""Volkshaus Zuerich (Stauffacherstrasse 60 / Helvetiaplatz): 1910 Heimatstil. Recessed windows with reveals and sills,
arched ground floor, string courses, quoins, double mansard with dormers, plastic lettering plate, entrance canopy."""
import math
from PIL import Image, ImageDraw
from common import *
from lm import *
import detail as D
from shapely.geometry import Polygon, Point


def plaster(color, seed=3, size=128, stains=0.06):
    rng = np.random.default_rng(seed)
    a = np.full((size, size, 4), 255, np.uint8); a[..., :3] = color[:3]
    n = rng.normal(0, 5, (size, size, 1)); a[..., :3] = np.clip(a[..., :3] + n, 0, 255).astype(np.uint8)
    for _ in range(14):   # soft blotches (render patches)
        x, y, r = rng.integers(0, size), rng.integers(0, size), rng.integers(8, 26); f = 1 + rng.normal(0, stains)
        yy, xx = np.ogrid[:size, :size]; mk = ((xx - x) ** 2 + (yy - y) ** 2) < r * r
        a[mk, :3] = np.clip(a[mk, :3] * f, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def build():
    B = bid("ID_B4A079F1")
    P = outline(B["fp"], 0.5)
    c = P.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    Pl = orient(localize(P, ox, oy), 1.0)
    rng = np.random.default_rng(11)
    m = Model("volkshaus")
    mw = m.mat("wall", plaster(hexc("#b4533e"))); ga = D.glass_atlas(frame="#efe6cf", glass="#26323d", sky="#8fa9bb", seed=5, sign=D.text_sign("VOLKSHAUS", "#4a1a16", "#f4ecd6", 27))
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", solid((255, 255, 255, 255)))
    CREAM, STONE, REV = hexc("#e3d9c0"), hexc("#8f8a80"), hexc("#d8cdb2")
    WALLC = (255, 255, 255, 255)
    GH, FH, NF = 5.0, 3.3, 4
    z_gf1 = 0.9 + GH; zc = z_gf1 + NF * FH
    ring = list(Pl.exterior.coords)[:-1]; ne = len(ring)
    # sandstone plinth skirt
    m.extrude(mf, mf, Pl, -3, 0.9, col=STONE, roof=False)
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b)
        if L < 1.8:
            m.wall(mw, a, b, 0.9, zc, (4, 4), WALLC); continue
        bw = 3.4
        def hole(u0, u1, f0, f1, fl):
            w = u1 - u0
            if fl == 0: return D.arch_pts(u0 + 0.7, f0 + 0.15, u1 - 0.7, f0 + 3.6)
            return D.rect_pts(u0 + (w - 1.35) / 2, f0 + 0.75, u0 + (w + 1.35) / 2, f0 + 2.65)
        # ground floor (arched) then upper floors
        D.wall_run(m, mw, mg, mf, a, b, 0.9, 1, GH, bw, hole, 0.45, WALLC, REV, rng, sill=None)
        D.wall_run(m, mw, mg, mf, a, b, z_gf1, NF, FH, bw, lambda u0, u1, f0, f1, fl: hole(u0, u1, f0, f1, 1), 0.3, WALLC, REV, rng, sill=0.14)
        D.band(m, mf, a, b, z_gf1 - 0.2, z_gf1 + 0.2, 0.16, CREAM)                  # string course
        D.band(m, mf, a, b, zc - 0.55, zc + 0.05, 0.28, CREAM)                      # eave cornice
        D.band(m, mf, a, b, zc + 0.05, zc + 0.35, 0.5, shade(CREAM, 0.9))
    # quoins at corners
    for i in range(ne):
        p = ring[i]; q = ring[(i + 1) % ne]; r_ = ring[i - 1]
        ang = math.atan2(q[1] - p[1], q[0] - p[0])
        m.box(mf, p[0], p[1], 0.45, 0.45, 0.9, zc, rot=ang, col=CREAM)
    # double mansard roof
    roof, roof2 = hexc("#6a2f27"), hexc("#5c2a23")
    A = Pl.buffer(0.45, join_style=2)
    q1 = taper(m, mf, A, zc + 0.35, zc + 4.2, 0.9, roof, cap=False)
    q2 = taper(m, mf, q1, zc + 4.2, zc + 9.0, 0.5, roof2, cap=True)
    # dormers on the lower mansard
    cc = (A.centroid.x, A.centroid.y); ringA = list(orient(A, 1.0).exterior.coords)[:-1]
    for i in range(len(ringA)):
        a, b = ringA[i], ringA[(i + 1) % len(ringA)]; L, t, n = D.frame_of(a, b)
        if L < 4: continue
        nd = max(1, int(L // 6.8)); step = L / nd
        for j in range(nd):
            u = (j + 0.5) * step; px, py = a[0] + t[0] * u, a[1] + t[1] * u
            tt = 0.45; bx = cc[0] + (px - cc[0]) * (1 - 0.1 * tt); by = cc[1] + (py - cc[1]) * (1 - 0.1 * tt)
            zd = zc + 0.35 + 3.85 * tt
            ang = math.atan2(t[1], t[0])
            m.box(mf, bx, by, 1.7, 1.5, zd - 0.4, zd + 1.5, rot=ang, col=hexc("#7b3b31"))
            fx, fy = bx + n[0] * 0.76, by + n[1] * 0.76
            hw = 0.6; k = int(rng.integers(0, 8)); cu0, cu1 = k / 8, (k + 1) / 8
            m.quad(mg, [(fx - t[0] * hw, fy - t[1] * hw, zd - 0.2), (fx + t[0] * hw, fy + t[1] * hw, zd - 0.2), (fx + t[0] * hw, fy + t[1] * hw, zd + 1.2), (fx - t[0] * hw, fy - t[1] * hw, zd + 1.2)],
                   [(cu0, 0.25), (cu1, 0.25), (cu1, 1.0), (cu0, 1.0)], n=(n[0], n[1], 0))
            pts = [(bx - n[0] * 0.75 - t[0] * 0.85, by - n[1] * 0.75 - t[1] * 0.85), (bx - n[0] * 0.75 + t[0] * 0.85, by - n[1] * 0.75 + t[1] * 0.85),
                   (bx + n[0] * 0.75 + t[0] * 0.85, by + n[1] * 0.75 + t[1] * 0.85), (bx + n[0] * 0.75 - t[0] * 0.85, by + n[1] * 0.75 - t[1] * 0.85)]
            m.hip(mf, pts, zd + 1.5, 1.1, roof2, ridge_frac=0.3)
    # chimneys
    for fx, fy in [(0.35, 0.2), (-0.3, -0.25), (0.1, -0.4), (-0.15, 0.3)]:
        px, py = q2.centroid.x + fx * (q2.bounds[2] - q2.bounds[0]), q2.centroid.y + fy * (q2.bounds[3] - q2.bounds[1])
        m.box(mf, px, py, 1.2, 1.2, zc + 5, zc + 10.5, col=hexc("#9a5a45")); m.box(mf, px, py, 1.5, 1.5, zc + 10.5, zc + 10.9, col=hexc("#5a5a58"))
    # main facade: longest edge facing Helvetiaplatz (783,-881)
    best = None; tgt = (783 - ox, -881 - oy)
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); dt = (tgt[0] - mid[0], tgt[1] - mid[1]); dn = math.hypot(*dt)
        sc = L * max(0, (n[0] * dt[0] + n[1] * dt[1]) / dn)
        if best is None or sc > best[0]: best = (sc, a, b)
    _, a, b = best; L, t, n = D.frame_of(a, b)
    ang = math.atan2(t[1], t[0]); u = L / 2
    # plastic lettering plate, 0.35 m deep, framed
    w, h, zz = min(15.5, L * 0.72), 2.2, z_gf1 + 2 * FH + 0.55
    D.band(m, mf, (a[0] + t[0] * (u - w / 2 - 0.3), a[1] + t[1] * (u - w / 2 - 0.3)), (a[0] + t[0] * (u + w / 2 + 0.3), a[1] + t[1] * (u + w / 2 + 0.3)), zz - 0.3, zz + h + 0.3, 0.3, hexc("#d6c79a"))
    p0 = P = D.P3(a, t, n, u - w / 2, zz, 0.33); p1 = D.P3(a, t, n, u + w / 2, zz, 0.33)
    m.quad(mg, [p0, p1, (p1[0], p1[1], zz + h), (p0[0], p0[1], zz + h)], D.SIGN_UV()[:4], n=(n[0], n[1], 0))
    # entrance: canopy on slim posts + three steps
    cw, cd = 5.6, 2.6
    for s in (-1, 1):
        m.box(mf, *(D.P3(a, t, n, u + s * (cw / 2 - 0.2), 0, cd - 0.2)[:2]), 0.25, 0.25, 0.0, 4.3, rot=ang, col=hexc("#2b2d2f"))
    cp = D.P3(a, t, n, u, 0, cd / 2)
    m.box(mf, cp[0], cp[1], cw, cd, 4.3, 4.65, rot=ang, col=hexc("#3a3c3e"))
    for k in range(3):
        sp = D.P3(a, t, n, u, 0, 0.5 + (2 - k) * 0.38)
        m.box(mf, sp[0], sp[1], 3.6, 0.38 * (3 - k) + 0.2, 0.9 - (k + 1) * 0.3 - 0.1, 0.9 - k * 0.3, rot=ang, col=hexc("#a29c90"))
    hide = [[round(p.x, 1), round(p.y, 1)] for p in (g_.representative_point() for g_ in (B["fp"].geoms if hasattr(B["fp"], "geoms") else [B["fp"]]))]
    finish(m, "volkshaus", "Volkshaus", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
