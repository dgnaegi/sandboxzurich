"""Bullingerkirche (Bullingerplatz): ochre-plaster church/parish hall block with hip roof + separate slender open concrete bell tower
(corner piers, clock faces, bell chamber with bells, cross). research/v3/bullingerkirche.md."""
import math
from common import *
from lm import *
import detail as D
from k45_volkshaus import plaster


def build():
    B = bid("ID_7B3577FB"); TW = bid("ID_3E370FAC")
    P = outline(B["fp"], 0.5); ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = orient(localize(P, ox, oy), 1.0); ring = list(Pl.exterior.coords)[:-1]; ne = len(ring)
    TP = outline(TW["fp"], 0.3); tcx, tcy = TP.centroid.x - ox, TP.centroid.y - oy
    (_, ux, uy, Lt, Wt) = rect_of(localize(TP, ox, oy)); tang = math.atan2(uy, ux); tz = ground(TP.centroid.x, TP.centroid.y) - oz
    rng = np.random.default_rng(9)
    m = Model("bullingerkirche")
    mw = m.mat("wall", plaster(hexc("#e0d19c"), seed=5, stains=0.03))
    ga = D.glass_atlas_g(frame="#f0eee6", glass="#2b3844", sky="#8aa0b0", cols=2, rows=3, seed=3, bar=3, lit_p=0.35,
                         curtain_cols=[(236, 228, 210), (225, 215, 190), (240, 238, 232), (200, 190, 170)])
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", solid((255, 255, 255, 255)))
    W = (255, 255, 255, 255)
    PL, FH, NF = 1.0, 4.5, 3; eave = PL + NF * FH
    m.extrude(mf, mf, Pl, -3, PL, col=D.hexl("#a9a398"), roof=False)
    li = max(range(ne), key=lambda i: math.dist(ring[i], ring[(i + 1) % ne]))
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b)
        if L < 1.5: m.wall(mw, a, b, PL, eave, (4, 4), W); continue
        nb = max(1, int(round(L / 2.8))); bw = L / nb
        for f in range(NF):
            fb = PL + f * FH
            for k in range(nb):
                u0, u1 = k * bw, (k + 1) * bw; uc = (u0 + u1) / 2
                if i == li and f == 0 and k == nb // 2: hole = D.rect_pts(uc - 1.2, fb, uc + 1.2, fb + 3.3)
                else: hole = D.rect_pts(uc - 0.65, fb + 0.9, uc + 0.65, fb + 3.4)
                D.bay(m, mw, mg, mf, a, t, n, u0, u1, fb, fb + FH, hole, 0.25, int(rng.integers(0, D.NV)), W, hexc("#eee6c8"), (4, 4.5), None)
                D.surround(m, mw, a, t, n, hole, 0.1, (255, 252, 238, 255), 0.03, sill=0.08 if not (i == li and f == 0 and k == nb // 2) else 0)
        D.band(m, mw, a, b, eave - 0.4, eave + 0.1, 0.35, (255, 252, 238, 255))
        if i == li:                    # entrance canopy
            u = L / 2
            D.band(m, mf, D.P3(a, t, n, u - 2.2, 0, 0)[:2], D.P3(a, t, n, u + 2.2, 0, 0)[:2], PL + 3.7, PL + 4.0, 2.0, D.hexl("#6d6a64"))
    A = Pl.buffer(0.6, join_style=2)
    q1 = taper(m, mf, A, eave + 0.1, eave + 4.8, 0.45, D.hexl("#8a5a3c"), cap=True)
    # ---- bell tower ----
    z0 = tz; H = 45.0; w = Wt * 0.5
    def tbox(cx, cy, bw, bd, za, zb, col, rot=tang):
        m.box(mw if False else mf, tcx + cx * math.cos(rot) - cy * math.sin(rot), tcy + cx * math.sin(rot) + cy * math.cos(rot), bw, bd, z0 + za, z0 + zb, rot=rot, col=col)
    CR = D.hexl("#e8e0b8"); h = Wt / 2 - 0.45
    for sx in (-1, 1):
        for sy in (-1, 1): tbox(sx * h, sy * h, 0.9, 0.9, -3, H, CR)
    for za in (0.5, 7.0, 14.0, 24.0, 33.0, 43.0):
        tbox(0, 0, Wt, Wt, za, za + 0.4, D.hexl("#d8cfa4"))              # floor slabs/ring beams
    tbox(0, 0, Wt - 0.9, Wt - 0.9, 14.4, 33.0, D.hexl("#e0d7ac"))        # shaft core
    for k in range(4):                                                   # slit windows (dark) on the shaft + louvres in the bell chamber
        a_ = tang + k * math.pi / 2; nx_, ny_ = math.cos(a_), math.sin(a_); tx_, ty_ = -ny_, nx_
        for off in (-0.9, 0.9):
            c0 = (tcx + nx_ * (Wt / 2 - 0.3 + 0.05) + tx_ * off, tcy + ny_ * (Wt / 2 - 0.3 + 0.05) + ty_ * off)
            m.quad(mf, [(c0[0] - tx_ * 0.2, c0[1] - ty_ * 0.2, z0 + 17), (c0[0] + tx_ * 0.2, c0[1] + ty_ * 0.2, z0 + 17), (c0[0] + tx_ * 0.2, c0[1] + ty_ * 0.2, z0 + 22.5), (c0[0] - tx_ * 0.2, c0[1] - ty_ * 0.2, z0 + 22.5)], col=D.hexl("#2a2c30"), n=(nx_, ny_, 0))
        # bell chamber: dark back + two bells visible
        c1 = (tcx + nx_ * (Wt / 2 - 0.6), tcy + ny_ * (Wt / 2 - 0.6))
        m.quad(mf, [(c1[0] - tx_ * (h - 0.5), c1[1] - ty_ * (h - 0.5), z0 + 34), (c1[0] + tx_ * (h - 0.5), c1[1] + ty_ * (h - 0.5), z0 + 34), (c1[0] + tx_ * (h - 0.5), c1[1] + ty_ * (h - 0.5), z0 + 43), (c1[0] - tx_ * (h - 0.5), c1[1] - ty_ * (h - 0.5), z0 + 43)], col=D.hexl("#1e1f22"), n=(nx_, ny_, 0))
        # clock face on the shaft top (two sides in the real tower; we put all four, small)
        cc = (tcx + nx_ * (Wt / 2 - 0.3 + 0.08), tcy + ny_ * (Wt / 2 - 0.3 + 0.08)); zc = z0 + 28.0
        for q in range(16):
            q0, q1_ = 2 * math.pi * q / 16, 2 * math.pi * (q + 1) / 16
            for r0, r1, col in ((0.0, 1.35, D.hexl("#2a5aa0")), (1.35, 1.6, D.hexl("#caa24c"))):
                pts = [(cc[0] + tx_ * r * math.cos(qq), cc[1] + ty_ * r * math.cos(qq), zc + r * math.sin(qq)) for r, qq in ((r0, q0), (r1, q0), (r1, q1_), (r0, q1_))]
                if r0 == 0: m.tri(mf, pts[:3], col=col)
                else: m.quad(mf, pts, col=col, n=(nx_, ny_, 0))
        for ha, hl in ((math.radians(100), 1.0), (math.radians(-10), 1.25)):
            p0 = (cc[0] + nx_ * 0.04, cc[1] + ny_ * 0.04, zc); p1 = (cc[0] + nx_ * 0.04 + tx_ * hl * math.cos(ha), cc[1] + ny_ * 0.04 + ty_ * hl * math.cos(ha), zc + hl * math.sin(ha))
            m.quad(mf, [(p0[0], p0[1], p0[2] - 0.06), (p1[0], p1[1], p1[2] - 0.06), (p1[0], p1[1], p1[2] + 0.06), (p0[0], p0[1], p0[2] + 0.06)], col=D.hexl("#caa24c"), n=(nx_, ny_, 0))
    for bx in (-0.9, 0.9):
        m.cylinder(mf, tcx + bx * math.cos(tang), tcy + bx * math.sin(tang), 0.55, z0 + 38.0, z0 + 40.6, n=10, col=D.hexl("#8c6a3a"), r1=0.28)
    tbox(0, 0, Wt + 0.4, Wt + 0.4, H, H + 0.5, D.hexl("#d8cfa4"))
    m.cylinder(mf, tcx, tcy, 0.1, z0 + H + 0.5, z0 + H + 4.5, n=6, col=D.hexl("#3a3a3a"))
    m.box(mf, tcx, tcy, 1.4, 0.1, z0 + H + 3.2, z0 + H + 3.4, rot=tang, col=D.hexl("#3a3a3a"))
    hide = [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for bb in (B, TW) for g in (bb["fp"].geoms if hasattr(bb["fp"], "geoms") else [bb["fp"]])]
    finish(m, "bullingerkirche", "Bullingerkirche", ox, oy, oz, hide_union("Bullingerkirche", hide))


if __name__ == "__main__":
    build()
