"""Frau Gerolds Garten (Geroldstrasse 23): gravel yard garden. Colourful stacked containers (2-3 levels) as bars/kitchens, timber pergolas and
stalls, planter boxes, tables, string lights (emissive) and bunting across the yard. Photos: research/v3/frau_gerolds_garten.md.
The existing low buildings on the plots are hidden; the model draws a gravel patch + wooden deck itself."""
import math
from k5w3_kit import *
import k5w3_freitag as F

IDS = ["ID_6999753E", "ID_38727667", "ID_B9E3EE20"]


def build():
    setup()
    U = unary_union([bid(p)["fp"] for p in IDS]); c = U.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    m = Model("frau_gerolds_garten"); rng = np.random.default_rng(31)
    ma = m.mat("cont", *F.atlas(), rough=0.6); mf = m.mat("flat", solid(W4))
    Ht = 2 * F.CHPX + 64
    def cont(cx, cy, z0, rot, k, L=F.CL, Wd=F.CW):
        hl, hw = L / 2, Wd / 2; cr, sr = math.cos(rot), math.sin(rot)
        P = [(cx + x * cr - y * sr, cy + x * sr + y * cr) for x, y in [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]]
        col = hexl(F.COLS[k]); z1 = z0 + F.CH
        cu0, cv0 = (k % 4) / 4, 1 - ((k // 4) + 1) * F.CHPX / Ht; dv = F.CHPX / Ht
        for i in range(4):
            a, b = P[i], P[(i + 1) % 4]
            if i in (0, 2): m.quad(ma, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], [(cu0, cv0), (cu0 + .25, cv0), (cu0 + .25, cv0 + dv), (cu0, cv0 + dv)], W4)
            else: m.wall(mf, a, b, z0, z1, (3, 3), tuple(int(v * .8) for v in col[:3]) + (255,))
        m.flat(mf, Polygon(P), z1, tuple(min(255, int(v * 1.1)) for v in col[:3]) + (255,))
    # gravel patch + deck
    yard = sbox(150 - ox, 135 - oy, 260 - ox, 200 - oy)
    m.flat(mf, yard, 0.03, hexl("#a8a294"))
    cols_ok = [0, 1, 2, 3, 5, 6, 7, 4]
    n_c = 0
    for p in IDS:
        poly = localize(bid(p)["fp"], ox, oy)
        for g in polys_of(poly):
            (cx, cy), ux, uy, L, W = rect_of(g.simplify(0.5))
            ang = math.atan2(uy, ux); lv = 3 if p == "ID_6999753E" else 2
            nl = max(1, int(L // F.CL)); nr = max(1, min(3, int(W // F.CW)))
            for i in range(nl):
                for j in range(nr):
                    u = (i - (nl - 1) / 2) * F.CL; v = (j - (nr - 1) / 2) * F.CW
                    x, y = cx + ux * u - uy * v, cy + uy * u + ux * v
                    for z in range(lv if (i + j) % 3 else lv - 1):
                        cont(x, y, 0.12 + z * F.CH, ang, cols_ok[int(rng.integers(0, 8))]); n_c += 1
    # pergolas (4 posts + slat roof) and stalls, planters, tables
    def pergola(cx, cy, w, d, h, rot):
        cr, sr = math.cos(rot), math.sin(rot)
        for sx in (-1, 1):
            for sy in (-1, 1):
                m.box(mf, cx + sx * w / 2 * cr - sy * d / 2 * sr, cy + sx * w / 2 * sr + sy * d / 2 * cr, 0.18, 0.18, 0, h, col=hexl("#7a5a3a"))
        for k in range(7):
            v = -d / 2 + k * d / 6; m.box(mf, cx - v * sr, cy + v * cr, w + 0.6, 0.12, h, h + 0.1, rot=rot, col=hexl("#8a6a48"))
    for px, py, r in [(214, 150, 0.1), (214, 175, -0.05), (172, 168, 0.3)]:
        pergola(px - ox, py - oy, 7.0, 4.0, 2.8, r)
    for k in range(18):
        x, y = 160 + rng.random() * 95 - ox, 142 + rng.random() * 52 - oy
        if rng.random() < 0.5: m.box(mf, x, y, 1.2, 0.7, 0.0, 0.55, col=hexl("#8a6a48")); m.box(mf, x, y, 1.1, 0.6, 0.55, 1.0, col=hexl("#3f7a3a"))
        else: m.box(mf, x, y, 0.9, 0.9, 0.7, 0.76, col=hexl("#6a4a2e")); m.box(mf, x, y, 0.12, 0.12, 0, 0.7, col=hexl("#3a3a3a"))
    # string lights + bunting
    lines = [((190 - ox, 144 - oy, 5.2), (240 - ox, 152 - oy, 5.0)), ((196 - ox, 166 - oy, 4.6), (236 - ox, 160 - oy, 4.8)), ((194 - ox, 154 - oy, 5.6), (238 - ox, 156 - oy, 5.4))]
    fl = ["#d9362c", "#f0c02a", "#2f7fb8", "#3f9a4e", "#e8e4da", "#d4772a"]
    for li, (a, b) in enumerate(lines):
        for i in range(24):
            P = lambda ff: (a[0] + (b[0] - a[0]) * ff, a[1] + (b[1] - a[1]) * ff, a[2] + (b[2] - a[2]) * ff - 1.2 * 4 * ff * (1 - ff))
            p0, p1 = P(i / 24), P((i + 1) / 24)
            if li < 2:
                m.box(mf, p0[0], p0[1], 0.18, 0.18, p0[2] - 0.09, p0[2] + 0.09, col=hexl("#ffe3a0"))
            else:
                mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, p0[2] - 0.55)
                m.tri(mf, [p0, p1, mid], col=hexl(fl[i % 6])); m.tri(mf, [p1, p0, mid], col=hexl(fl[i % 6]))
    for px, py in [(190, 144), (240, 152), (196, 166), (236, 160)]: m.box(mf, px - ox, py - oy, 0.14, 0.14, 0, 5.4, col=hexl("#5a4a3a"))
    finish(m, "frau_gerolds_garten", "Frau Gerolds Garten", ox, oy, oz, hide_pts(IDS))


if __name__ == "__main__":
    build()
