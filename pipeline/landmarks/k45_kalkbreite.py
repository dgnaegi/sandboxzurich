"""Kalkbreite (2014): six-storey perimeter block over the tram depot. Grey plaster, regular window grid with deep reveals, concrete floor
bands, shopfront ground floor + two tram-depot portals, roof garden with planters and pavilions. (Few photos: research/v3/kalkbreite.md)"""
import math
from common import *
from lm import *
import detail as D
from k45_volkshaus import plaster


def build():
    B = bid("ID_E2807877"); P = outline(B["fp"], 0.6)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = orient(localize(P, ox, oy), 1.0); H = B["zmax"] - ground(P.centroid.x, P.centroid.y)
    ring = list(Pl.exterior.coords)[:-1]; ne = len(ring)
    rng = np.random.default_rng(14)
    m = Model("kalkbreite")
    mw = m.mat("wall", plaster(hexc("#cac5b9"), seed=12, stains=0.03))
    sign = D.letters_strip([(0, 1024, "KALKBREITE", "#1e1e1e", "#cac5b9", None)], size=28)
    ga = D.glass_atlas_g(frame="#4a4a46", glass="#2f3b44", sky="#8da3b2", cols=2, rows=2, seed=15, bar=3, lit_p=0.4, sign=sign, curtain_cols=[(232, 228, 216), (210, 206, 196), (240, 238, 232), (180, 186, 190), (200, 190, 170)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid((255, 255, 255, 255)))
    W = (255, 255, 255, 255)
    GF = 6.0; FH = 3.1; nf = max(3, int(round((H - GF) / FH))); top = GF + nf * FH
    BAND, CONC = D.hexl("#b9b4a8"), D.hexl("#8d8a82")
    m.extrude(mf, mf, Pl, -3, 0.0, col=CONC, roof=False)
    li = max(range(ne), key=lambda i: math.dist(ring[i], ring[(i + 1) % ne]))
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b)
        if L < 3: m.wall(mw, a, b, 0, top, (4, 4), W); continue
        # ground floor: shopfront bays (pier + large glazing); depot portals on the longest edge
        nb = max(1, int(round(L / 6.0))); bw = L / nb
        for k in range(nb):
            u0, u1 = k * bw, (k + 1) * bw; uc = (u0 + u1) / 2
            portal = i == li and k in (nb // 3, (2 * nb) // 3)
            hole = D.rect_pts(uc - 3.4, 0.0, uc + 3.4, 5.2) if portal else D.rect_pts(uc - 2.4, 0.4, uc + 2.4, 4.4)
            D.bay(m, mw, mg, mf, a, t, n, u0, u1, 0.0, GF, hole, 0.9 if portal else 0.4, int(rng.integers(0, D.NV)), W, D.hexl("#8d8a82"), (4, 4), None)
            D.surround(m, mw, a, t, n, hole, 0.25, (240, 236, 226, 255), 0.05)
        D.band(m, mw, a, b, GF - 0.45, GF + 0.1, 0.25, (225, 220, 208, 255))
        # upper floors
        nb = max(1, int(round(L / 3.0))); bw = L / nb
        for f in range(nf):
            fb = GF + f * FH
            for k in range(nb):
                u0, u1 = k * bw, (k + 1) * bw; uc = (u0 + u1) / 2
                hole = D.rect_pts(uc - 0.8, fb + 0.55, uc + 0.8, fb + 2.55) if (k + f) % 5 else D.rect_pts(uc - 0.8, fb + 0.1, uc + 0.8, fb + 2.55)   # some French windows
                D.bay(m, mw, mg, mf, a, t, n, u0, u1, fb, fb + FH, hole, 0.32, int(rng.integers(0, D.NV)), W, D.hexl("#7d7a72"), (4, 3.1), None)
            if f % 2 == 1: D.band(m, mw, a, b, fb - 0.12, fb + 0.12, 0.08, (225, 220, 208, 255))
        D.band(m, mw, a, b, top - 0.2, top + 0.5, 0.2, (225, 220, 208, 255))
    # name lettering on the eave of the longest edge
    a, b = ring[li], ring[(li + 1) % ne]; L, t, n = D.frame_of(a, b)
    p0, p1 = D.P3(a, t, n, L * 0.5 - 6, GF + 0.1, 0.1), D.P3(a, t, n, L * 0.5 + 6, GF + 0.1, 0.1)
    # roof garden: parapet surface, planters, pavilions
    m.flat(mf, Pl, top + 0.5, D.hexl("#7a7f78"))
    cc = Pl.centroid
    for k in range(10):
        ang = k * 0.9; r_ = 12 + 4 * k
        px, py = cc.x + math.cos(ang) * r_ * 0.7, cc.y + math.sin(ang) * r_ * 0.7
        if Pl.buffer(-4).contains(Point(px, py)):
            m.box(mf, px, py, 5.0, 2.2, top + 0.5, top + 1.0, rot=ang, col=D.hexl("#5a4a3a")); m.box(mf, px, py, 4.7, 1.9, top + 1.0, top + 1.5, rot=ang, col=D.hexl("#5f8a4a"))
    m.box(mf, cc.x, cc.y, 14, 8, top + 0.5, top + 3.5, rot=0.5, col=D.hexl("#b8b4a8"))
    hide = [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (B["fp"].geoms if hasattr(B["fp"], "geoms") else [B["fp"]])]
    finish(m, "kalkbreite", "Kalkbreite", ox, oy, oz, hide_union("Kalkbreite", hide))


if __name__ == "__main__":
    build()
