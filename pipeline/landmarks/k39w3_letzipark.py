"""Letzipark (Baslerstrasse 50, Einkaufszentrum): 150 m box, 2 levels, light-blue panel facade with grey ribbon band, arcade of round blue
columns + grey metal canopy over glazed shopfronts, rooftop stair/lift volumes with LETZIPARK lettering. research/v3/letzipark.md"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def build():
    c = prep(["ID_9DCBF65B"], 0.8); rng = np.random.default_rng(3)
    m = Model("k39w3_letzipark"); ring = c.ring; P = c.P
    mw = m.mat("wall", panels("#a9cdea", nx=4, ny=3, gap="#7ea8c8", seed=2))
    sign = strip([(0, 1024, "LETZIPARK", "#1d5fae", "#e8f0f6", (200, 225, 255))], size=28, gap_max=6)
    ga = D.glass_atlas_g(frame="#3b4e5c", glass="#2c3b46", sky="#9bb3c4", cols=4, rows=1, seed=11, bar=3, lit_p=0.6, curtains=False, sign=sign)
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", panels("#d6d9dc", nx=2, ny=2, gap="#9aa0a4", seed=5))
    FL, UP, TOP = 4.6, 12.0, 0.0
    GREY, BLUE, DARK = hexl("#9aa0a6"), hexl("#3f86d6"), hexl("#5d6064")
    li = max(range(len(ring)), key=lambda i: math.dist(ring[i], ring[(i + 1) % len(ring)]))
    m.extrude(mf, mf, P, -4, 0.3, col=W4, roof=False)
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]; L, t, n = D.frame_of(a, b)
        # upper level: blue panels, a white ribbon band, thin dark window slits
        m.wall(mw, a, b, FL, UP, (8, 6), W4)
        D.band(m, mf, a, b, FL, FL + 0.7, 0.4, hexl("#8f969c"))                  # canopy fascia / beam
        D.band(m, mf, a, b, UP - 0.9, UP + 0.4, 0.2, hexl("#e6eaee"))            # parapet cornice
        if L < 6: m.wall(mw, a, b, 0.3, FL, (4, 4), W4); continue
        # ground level: recessed glazed shopfront with lit cells, round blue columns, canopy
        a2 = (a[0] - n[0] * 2.2, a[1] - n[1] * 2.2); b2 = (b[0] - n[0] * 2.2, b[1] - n[1] * 2.2)
        m.wall(mf, a2, b2, 0.3, FL - 0.1, (3, 3), (120, 124, 128, 255))
        nb = max(1, int(round((L - 1) / 3.0))); bw = (L - 1.0) / nb
        for k in range(nb):
            u0 = 0.5 + k * bw
            D.poly_wall(m, mg, Polygon(D.rect_pts(u0 + 0.05, 0.4, u0 + bw - 0.05, 3.4)), a, t, n, -2.15, W4,
                        (lambda kk: (lambda u, z: ((kk % D.NV) / D.NV + (u - u0) / bw / D.NV, 0.25 + 0.75 * (z - 0.4) / 3.0)))(int(rng.integers(0, D.NV))))
        q = D.P3(a, t, n, 0, 0, 0); ang = math.atan2(t[1], t[0])
        for k in range(int(L // 6) + 1):
            u = min(L - 0.4, 0.4 + k * 6.0); p = D.P3(a, t, n, u, 0.3, -0.2)
            m.cylinder(mf, p[0], p[1], 0.32, 0.3, FL - 0.1, n=8, col=BLUE, mod=(2, 6))
        # canopy slab and underside
        pts = [D.P3(a, t, n, 0, FL - 0.1, 0.1), D.P3(b, (0, 0), n, 0, 0, 0)] if False else None
        m.quad(mf, [D.P3(a, t, n, 0, FL - 0.1, -2.2), D.P3(a, t, n, L, FL - 0.1, -2.2), D.P3(a, t, n, L, FL - 0.1, 0.5), D.P3(a, t, n, 0, FL - 0.1, 0.5)], col=DARK, n=(0, 0, -1))
    # rooftop: parapet slab, stair/lift volumes (blue) with sign
    m.extrude(mw, mf, P, UP, UP + 0.2, col=(215, 225, 235, 255), rcol=hexl("#7d8186"), roof=True, mod=(8, 6))
    for (x, y, w, d, h) in ((-18, 6, 17, 18, 8.5), (-6, 12, 14, 14, 8.0), (27, -8, 14, 18, 6.5), (8, 44, 12, 9, 5.5)):
        if P.buffer(-3).contains(Point(x, y)):
            m.box(mw, x, y, w, d, UP, UP + h, mr=mf, rcol=hexl("#8d9196"), col=W4, mod=(8, 6))
    # LETZIPARK sign wall on the tallest volume (south face)
    sx, sy = -18, 6
    sgn = [(sx - 8, sy - 9.05, UP + 5.4), (sx + 8, sy - 9.05, UP + 5.4), (sx + 8, sy - 9.05, UP + 7.4), (sx - 8, sy - 9.05, UP + 7.4)]
    m.quad(mg, sgn, [(0.37, 0.0), (0.63, 0.0), (0.63, 0.25), (0.37, 0.25)], n=(0, -1, 0))
    finish39(m, "k39w3_letzipark", "Letzipark", c.ox, c.oy, c.oz, c.hide)


if __name__ == "__main__":
    build()
