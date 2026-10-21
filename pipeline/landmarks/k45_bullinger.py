"""Bullingerkirche = Rathaus Hard: church volume in rathaus_hard.py (pilaster gable front, porch, screens, lions hook);
separate slender concrete bell tower here (corner piers, clock faces, bell chamber, cross). research/rathaus_hard/notes.md."""
import math
from common import *
from lm import *
import detail as D
import rathaus_hard as RH
from k45_volkshaus import plaster


def build():
    B = bid("ID_7B3577FB"); TW = bid("ID_3E370FAC")
    P = outline(B["fp"], 0.5); ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = orient(localize(P, ox, oy), 1.0); ring = list(Pl.exterior.coords)[:-1]; ne = len(ring)
    TP = outline(TW["fp"], 0.3); tcx, tcy = TP.centroid.x - ox, TP.centroid.y - oy
    (_, ux, uy, Lt, Wt) = rect_of(localize(TP, ox, oy)); tang = math.atan2(uy, ux); tz = ground(TP.centroid.x, TP.centroid.y) - oz
    rng = np.random.default_rng(9)
    m = Model("bullingerkirche"); m.max_mats = 6
    mw = m.mat("wall", plaster(hexc("#e2d6ae"), seed=5, stains=0.03))
    ga = D.glass_atlas_g(frame="#f0eee6", glass="#2b3844", sky="#8aa0b0", cols=2, rows=3, seed=3, bar=3, lit_p=0.0,
                         curtain_cols=[(236, 228, 210), (225, 215, 190), (240, 238, 232), (200, 190, 170)])
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", solid((255, 255, 255, 255)))
    ms = m.mat("screen", RH.screen_tex()); mc = m.mat("cobble", RH.cobble_tex(), rough=0.95); md = m.mat("dark", solid((118, 113, 105, 255)))
    li = max(range(ne), key=lambda i: math.dist(ring[i], ring[(i + 1) % ne]))
    RH.church(m, dict(wall=mw, glass=mg, flat=mf, screen=ms, dark=md, cobble=mc), Pl, ring, rng, li, gz=lambda x, y: ground(x + ox, y + oy) - oz,
               others=[orient(localize(outline(b['fp'], 0.3), ox, oy), 1.0) for b in near(ox, oy, 70) if b['id'] not in (B['id'], TW['id'])])
    A = Pl.buffer(1.1, join_style=2)
    q1 = taper(m, mf, A, RH.EAVE + 0.1, RH.EAVE + 4.6, 0.5, D.hexl("#85817a"), cap=True)
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
