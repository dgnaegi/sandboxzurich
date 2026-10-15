"""Kirche St. Jakob (Stauffacher, 1898): ashlar nave with lancets + buttresses, stepped gable with rose window and portal, corner tower
with clock faces on four sides, belfry, copper-green octagonal spire with gablets and pinnacles. Photos: research/v3/st_jakob.md."""
import math
from common import *
from lm import *
import detail as D
from shapely.geometry import Polygon

TOWER_PT = (949, -1219)
TOTAL_H = 66.0


def build():
    B = bid("ID_B0FF1289"); P = outline(B["fp"], 0.5)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = localize(P, ox, oy)
    (cx, cy), ux, uy, L, W = rect_of(Pl); vx, vy = -uy, ux; ang = math.atan2(uy, ux)
    A = lambda a, b: (cx + ux * a + vx * b, cy + uy * a + vy * b)
    rng = np.random.default_rng(5)
    m = Model("st_jakob")
    mw = m.mat("wall", D.ashlar(hexc("#b8aa8c")))
    sign = None
    ga = D.glass_atlas_g(frame="#d8cfae", glass="#1f2c38", sky="#7f95a5", cols=2, rows=4, seed=9, bar=3, lit_p=0.5, curtains=False)
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid((255, 255, 255, 255)))
    W_ = (255, 255, 255, 255)
    SLATE, COP, COPD, STONEL, GOLD = D.hexl("#43444a"), D.hexl("#6c9f8e"), D.hexl("#55836f"), D.hexl("#e0d6b8"), D.hexl("#caa24c")
    NAVE_H = 14.0; RISE = 9.8; E = 0.9
    corners = [A(-L / 2, -W / 2), A(L / 2, -W / 2), A(L / 2, W / 2), A(-L / 2, W / 2)]
    s = 1 if ((TOWER_PT[0] - ox - cx) * ux + (TOWER_PT[1] - oy - cy) * uy) > 0 else -1
    sb = 1 if ((TOWER_PT[0] - ox - cx) * vx + (TOWER_PT[1] - oy - cy) * vy) > 0 else -1
    front = 1 if s > 0 else 3
    TW = 9.4
    m.extrude(mf, mf, Polygon(corners), -3, E, col=D.hexl("#9a9488"), roof=False)
    tc_a, tc_b = s * (L / 2 - TW / 2), sb * (W / 2 - TW / 2)
    tower_u = None
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]; Le, t, n = D.frame_of(a, b)
        long_ = i in (0, 2)
        nb = max(1, int(round(Le / (4.6 if long_ else 4.5)))); bw = Le / nb
        for f, (z0, fh) in enumerate([(E, 6.4), (E + 6.4, NAVE_H - E - 6.4)]):
            for k in range(nb):
                u0, u1 = k * bw, (k + 1) * bw; uc = (u0 + u1) / 2
                gp = A(*(0, 0))  # unused
                # skip the tower corner bays on the front end / near wall
                mid = (a[0] + t[0] * uc, a[1] + t[1] * uc)
                in_tower = math.hypot(mid[0] - A(tc_a, tc_b)[0], mid[1] - A(tc_a, tc_b)[1]) < TW / 2 + 1.5
                if in_tower:
                    D.poly_wall(m, mw, Polygon(D.rect_pts(u0, z0, u1, z0 + fh)), a, t, n, 0.0, W_, lambda u, z: (u / 5, z / 5)); continue
                if f == 0:
                    if i == front and abs(uc - Le / 2) < bw * 0.6 + (TW / 2 if sb * 0 == 0 else 0) * 0 and False: pass
                    ctr = (i == front) and abs(mid[0] - A(-tc_a * 0, -tc_b)[0]) < 99
                    hole = D.rect_pts(uc - 0.7, z0 + 1.6, uc + 0.7, z0 + 4.6)
                    if i == front and abs(uc - (Le / 2 - sb * 0 - (-1) * 0)) < 99 and k == (nb // 2 if sb > 0 else (nb - 1) // 2) - (0): hole = D.pointed_pts(uc - 1.4, z0, uc + 1.4, z0 + 3.8)
                else:
                    hole = D.pointed_pts(uc - 0.85, z0 + 0.9, uc + 0.85, z0 + 4.3)
                D.bay(m, mw, mg, mf, a, t, n, u0, u1, z0, z0 + fh, hole, 0.35, int(rng.integers(0, D.NV)), W_, hexc("#b9ad8c"), (5, 5), None)
                D.surround(m, mf, a, t, n, hole, 0.22, STONEL, 0.06)
            if long_ and f == 0:      # buttresses between bays
                pass
        if long_:
            for k in range(nb + 1):
                u = k * bw; p = D.P3(a, t, n, u, 0, 0.35)
                m.box(mf, p[0], p[1], 0.8, 0.7, E - 0.5, NAVE_H + 0.6, rot=ang + (0 if i in (0, 2) else math.pi / 2), col=D.hexl("#c4b794"))
        D.band(m, mf, a, b, E - 0.1, E + 0.25, 0.12, STONEL)
        D.band(m, mf, a, b, NAVE_H - 0.55, NAVE_H + 0.05, 0.3, STONEL)
    # stepped front gable + rose window, plain back gable, roof slopes
    for i, stepped in ((front, True), (3 if front == 1 else 1, False)):
        a, b = corners[i], corners[(i + 1) % 4]; Le, t, n = D.frame_of(a, b)
        if stepped:
            apex = NAVE_H + RISE + 1.4; steps = [(0, NAVE_H), (Le * 0.08, NAVE_H + 2.2), (Le * 0.18, NAVE_H + 4.2), (Le * 0.30, NAVE_H + 6.4), (Le * 0.40, NAVE_H + 8.4), (Le * 0.5, apex)]
            pts = [(0, NAVE_H)]
            for k in range(1, len(steps)):
                pts += [(steps[k][0], steps[k - 1][1] + (0 if k > 1 else 0)), (steps[k][0], steps[k][1])]
            half = pts[:]; mirror = [(Le - u, z) for u, z in reversed(half)]
            poly = Polygon(half + mirror[1:] + [(Le, NAVE_H)]).buffer(0)
            rose = Point(Le / 2, NAVE_H + 4.2).buffer(1.45, 16) if True else None
            from shapely.geometry import Point as _Pt
            poly = poly.difference(_Pt(Le / 2, NAVE_H + 4.4).buffer(1.5, 16)) if poly.is_valid else poly
            D.poly_wall(m, mw, poly, a, t, n, 0.0, W_, lambda u, z: (u / 5, z / 5))
            rp = [D.P3(a, t, n, Le / 2 + 1.5 * math.cos(q), NAVE_H + 4.4 + 1.5 * math.sin(q), -0.25) for q in np.linspace(0, 2 * math.pi, 17)[:-1]]
            cen = D.P3(a, t, n, Le / 2, NAVE_H + 4.4, -0.25)
            for q in range(16):
                m.tri(mg, [cen, rp[q], rp[(q + 1) % 16]], [(0.1, 0.5), (0.0, 0.3), (0.12, 0.3)], col=(255, 255, 255, 255))
            ring = [D.P3(a, t, n, Le / 2 + 1.7 * math.cos(q), NAVE_H + 4.4 + 1.7 * math.sin(q), 0.08) for q in np.linspace(0, 2 * math.pi, 17)]
            for q in range(16):
                m.quad(mf, [ring[q], ring[q + 1], D.P3(a, t, n, Le / 2 + 1.45 * math.cos(np.linspace(0, 2 * math.pi, 17)[q + 1]), NAVE_H + 4.4 + 1.45 * math.sin(np.linspace(0, 2 * math.pi, 17)[q + 1]), 0.08), D.P3(a, t, n, Le / 2 + 1.45 * math.cos(np.linspace(0, 2 * math.pi, 17)[q]), NAVE_H + 4.4 + 1.45 * math.sin(np.linspace(0, 2 * math.pi, 17)[q]), 0.08)], col=STONEL, n=(n[0], n[1], 0))
        else:
            D.poly_wall(m, mw, Polygon([(0, NAVE_H), (Le, NAVE_H), (Le / 2, NAVE_H + RISE)]), a, t, n, 0.0, W_, lambda u, z: (u / 5, z / 5))
    # slopes (long sides), slate
    a0, a1 = corners[0], corners[1]
    for sgn, (p0, p1) in ((1, (corners[0], corners[3])), (-1, (corners[1], corners[2]))):
        pass
    P_ = lambda a_, b_, z: (*A(a_, b_), z)
    m.quad(mf, [P_(-L / 2, -W / 2 - 0.4, NAVE_H - 0.3), P_(L / 2, -W / 2 - 0.4, NAVE_H - 0.3), P_(L / 2, 0, NAVE_H + RISE), P_(-L / 2, 0, NAVE_H + RISE)], col=SLATE)
    m.quad(mf, [P_(L / 2, W / 2 + 0.4, NAVE_H - 0.3), P_(-L / 2, W / 2 + 0.4, NAVE_H - 0.3), P_(-L / 2, 0, NAVE_H + RISE), P_(L / 2, 0, NAVE_H + RISE)], col=SLATE)
    m.box(mf, *A(0, 0), L, 0.35, NAVE_H + RISE - 0.1, NAVE_H + RISE + 0.35, rot=ang, col=D.hexl("#5a5b60"))
    # ---- tower ----
    TC = A(tc_a, tc_b); TWp = TW + 0.2
    h_a, h_b, h_c, h_d = 17.0, 27.0, 35.0, 42.0   # plain | slender windows | clock | belfry top
    tcorn = [A(tc_a + dx * TWp / 2, tc_b + dy * TWp / 2) for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4):
        a, b = tcorn[i], tcorn[(i + 1) % 4]; Le, t, n = D.frame_of(a, b)
        def mk(h0, h1, holefn, depth=0.3, surr=0.16):
            for z0, fh in ((h0, h1 - h0),):
                hole = holefn(Le / 2, z0, z0 + fh)
                if hole is None: D.poly_wall(m, mw, Polygon(D.rect_pts(0, z0, Le, z0 + fh)), a, t, n, 0.0, W_, lambda u, z: (u / 5, z / 5)); return
                D.bay(m, mw, mg, mf, a, t, n, 0, Le, z0, z0 + fh, hole, depth, int(rng.integers(0, D.NV)), W_, hexc("#b9ad8c"), (5, 5), None)
                if surr: D.surround(m, mf, a, t, n, hole, surr, STONEL, 0.06)
        D.poly_wall(m, mw, Polygon(D.rect_pts(0, E - 0.2, Le, h_a)), a, t, n, 0.0, W_, lambda u, z: (u / 5, z / 5))
        mk(h_a, h_b, lambda uc, z0, z1: D.pointed_pts(uc - 0.6, z0 + 2.2, uc + 0.6, z0 + 6.2))
        mk(h_b, h_c, lambda uc, z0, z1: D.pointed_pts(uc - 1.9, z0 + 1.2, uc - 0.3, z0 + 4.6), 0.6, 0.18)
        mk(h_c, h_d, lambda uc, z0, z1: None)
        # second belfry opening (right of the first)
        for off in (1.5,):
            hole = D.pointed_pts(Le / 2 + 0.3, h_b + 1.2, Le / 2 + 1.9, h_b + 4.6)
            D.poly_wall(m, mg, Polygon(hole), a, t, n, -0.6, (255, 255, 255, 255), lambda u, z: (0.55 + 0.05 * (u % 1), 0.3 + 0.7 * (z - h_b) / 8))
            D.surround(m, mf, a, t, n, hole, 0.18, STONEL, 0.06)
        D.band(m, mf, a, b, h_a - 0.2, h_a + 0.25, 0.2, STONEL); D.band(m, mf, a, b, h_b - 0.2, h_b + 0.25, 0.2, STONEL); D.band(m, mf, a, b, h_c - 0.6, h_c + 0.2, 0.55, STONEL)
        D.band(m, mf, a, b, h_d - 0.5, h_d + 0.2, 0.6, STONEL)
        # clock face
        cu = Le / 2; dz = h_c + 3.6; ctr = D.P3(a, t, n, cu, dz, 0.22)
        m.cylinder(mf, 0, 0, 1, 0, 0) if False else None
        cn = (n[0], n[1])
        ring_n = 20
        for q in range(ring_n):
            q0, q1 = 2 * math.pi * q / ring_n, 2 * math.pi * (q + 1) / ring_n
            for r0, r1, col in ((0, 1.9, D.hexl("#27475d")), (1.9, 2.2, GOLD)):
                pts = [D.P3(a, t, n, cu + r * math.cos(q_), dz + r * math.sin(q_), 0.18 if r0 else 0.2) for r, q_ in ((r0, q0), (r1, q0), (r1, q1), (r0, q1))]
                if r0 == 0: m.tri(mf, [pts[0], pts[1], pts[2]], col=col)
                else: m.quad(mf, pts, col=col, n=(n[0], n[1], 0))
        for ha, hl, hw in ((math.radians(100), 1.4, 0.09), (math.radians(-20), 1.8, 0.07)):
            p0 = D.P3(a, t, n, cu, dz, 0.24); p1 = D.P3(a, t, n, cu + hl * math.cos(ha), dz + hl * math.sin(ha), 0.24)
            q = [(p0[0] + t[0] * hw, p0[1] + t[1] * hw, p0[2]), (p1[0] + t[0] * hw, p1[1] + t[1] * hw, p1[2]), (p1[0] - t[0] * hw, p1[1] - t[1] * hw, p1[2]), (p0[0] - t[0] * hw, p0[1] - t[1] * hw, p0[2])]
            m.quad(mf, q, col=GOLD, n=(n[0], n[1], 0))
    # corner pilasters up the tower
    for k, (dx, dy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        p = A(tc_a + dx * (TWp / 2 - 0.1), tc_b + dy * (TWp / 2 - 0.1))
        m.box(mf, p[0], p[1], 1.0, 1.0, E, h_d - 0.4, rot=ang, col=D.hexl("#d6caa8"))
        m.cylinder(mf, p[0], p[1], 0.34, h_d + 0.2, h_d + 4.6, n=4, col=COPD, r1=0.04, smooth=False)       # corner pinnacles
    # gablets + octagonal spire
    z0 = h_d + 0.2
    m.box(mf, TC[0], TC[1], TW + 0.6, TW + 0.6, h_d - 0.2, z0, rot=ang, col=STONEL)
    sp_top = TOTAL_H - 2.6
    m.cylinder(mf, TC[0], TC[1], TW * 0.58, z0, z0 + 3.0, n=8, col=COP, r1=TW * 0.5, smooth=False)
    m.cylinder(mf, TC[0], TC[1], TW * 0.5, z0 + 3.0, sp_top, n=8, col=COP, r1=0.12, smooth=False)
    for k in range(4):
        aa = ang + k * math.pi / 2; nx_, ny_ = math.cos(aa), math.sin(aa); tx_, ty_ = -ny_, nx_
        c0 = (TC[0] + nx_ * (TW * 0.43), TC[1] + ny_ * (TW * 0.43))
        gw = 1.4
        base = [(c0[0] - tx_ * gw, c0[1] - ty_ * gw, z0 + 1.8), (c0[0] + tx_ * gw, c0[1] + ty_ * gw, z0 + 1.8)]
        ap = (c0[0] + nx_ * 0.5, c0[1] + ny_ * 0.5, z0 + 7.0)
        m.tri(mf, [base[0], base[1], (c0[0] + nx_ * 0.9, c0[1] + ny_ * 0.9, z0 + 1.8)], col=COPD) if False else None
        m.tri(mf, [(base[0][0] + nx_ * 0.8, base[0][1] + ny_ * 0.8, z0 + 1.8), (base[1][0] + nx_ * 0.8, base[1][1] + ny_ * 0.8, z0 + 1.8), ap], col=COPD)   # gablet front
        m.quad(mf, [(base[0][0], base[0][1], z0 + 0.5), (base[1][0], base[1][1], z0 + 0.5), (base[1][0] + nx_ * 0.8, base[1][1] + ny_ * 0.8, z0 + 1.8), (base[0][0] + nx_ * 0.8, base[0][1] + ny_ * 0.8, z0 + 1.8)], col=STONEL, n=(nx_, ny_, 0))
    m.cylinder(mf, TC[0], TC[1], 0.08, sp_top, TOTAL_H, n=6, col=GOLD)
    m.box(mf, TC[0], TC[1], 0.9, 0.08, TOTAL_H - 1.4, TOTAL_H - 0.5, rot=ang, col=GOLD)
    # portal steps on the front gable
    a, b = corners[front], corners[(front + 1) % 4]; Le, t, n = D.frame_of(a, b)
    hide = hide_union("Kirche St. Jakob", [[round(g_.representative_point().x, 1), round(g_.representative_point().y, 1)] for g_ in (B["fp"].geoms if hasattr(B["fp"], "geoms") else [B["fp"]])])
    finish(m, "st_jakob", "Kirche St. Jakob", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
