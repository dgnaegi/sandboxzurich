"""Im Viadukt: 1894 stone viaduct arcade along Viaduktstrasse. One round arch per OSM unit: rough ashlar with voussoir ring, recessed
shopfront glazing (mullions, door), pale aluminium fascia with house number plaque, cornice, deck railing. Photos: research/v3/viadukt.md."""
import math
from PIL import Image, ImageDraw
from common import *
from lm import *
import detail as D
import osmq
from shapely.geometry import LineString, MultiLineString, Point


def build():
    streets = [pts for t, pts in osmq.rows if t.get("name") == "Viaduktstrasse" and "building" not in t]
    street = MultiLineString([LineString(p) for p in streets])
    units = []
    for t, pts in osmq.rows:
        if t.get("addr:street") == "Viaduktstrasse" and t.get("start_date") == "2010" and t.get("building") == "commercial":
            units.append(Polygon(pts).buffer(0))
    cx = float(np.mean([u.centroid.x for u in units])); cy = float(np.mean([u.centroid.y for u in units]))
    ox, oy = round(cx, 1), round(cy, 1); oz = ground(ox, oy)
    units.sort(key=lambda u: (u.centroid.x, u.centroid.y))
    rng = np.random.default_rng(3)
    m = Model("viadukt")
    mw = m.mat("stone", D.ashlar(hexc("#a39580"), rows=8, rough=0.13, joint=0.62, seed=6))
    regions = [(i * 64, (i + 1) * 64, "%d" % (i + 1 if i < 9 else 10 + i), "#1e1e1e", "#dcdcd8", (200, 190, 170)) for i in range(16)]
    ga = D.glass_atlas_g(frame="#1c1c1c", glass="#25323a", sky="#8ea4b2", cols=4, rows=2, seed=12, bar=3, lit_p=0.7, curtains=False,
                         sign=D.letters_strip(regions, size=26, max_gap=2))
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid((255, 255, 255, 255)))
    H = 10.0; ST, ALU = D.hexl("#8f8573"), D.hexl("#dcdcd8")
    WC = (232, 228, 218, 255)
    for i, u in enumerate(units):
        r = u.minimum_rotated_rectangle; rc = list(r.exterior.coords)[:4]
        e0 = math.dist(rc[0], rc[1]); e1 = math.dist(rc[1], rc[2])
        edges = [(rc[0], rc[1]), (rc[2], rc[3])] if e0 <= e1 else [(rc[1], rc[2]), (rc[3], rc[0])]
        w = min(e0, e1)
        best = min(edges, key=lambda ab: street.distance(Point((ab[0][0] + ab[1][0]) / 2, (ab[0][1] + ab[1][1]) / 2)))
        a, b = best; c = u.centroid; mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        nx_, ny_ = (b[1] - a[1]), -(b[0] - a[0])
        if nx_ * (mid[0] - c.x) + ny_ * (mid[1] - c.y) < 0: a, b = b, a
        gz = ground(c.x, c.y) - oz
        P = localize(Polygon(rc), ox, oy)
        al = (a[0] - ox, a[1] - oy); bl = (b[0] - ox, b[1] - oy)
        L, t, n = D.frame_of(al, bl)
        # facade: stone wall with arched opening (recessed shopfront)
        aw = min(5.2, L - 1.4); uc = L / 2
        hole = D.arch_pts(uc - aw / 2, gz + 0.05, uc + aw / 2, gz + 5.4)
        org = (al[0], al[1])
        # shift z so the wall spans gz..gz+H: D.* use absolute z
        D.bay(m, mw, mg, mf, org, t, n, 0, L, gz, gz + H, hole, 0.8, int(rng.integers(0, D.NV)), WC, D.hexl("#7b7262"), (3.2, 3.2), None)
        D.surround(m, mw, org, t, n, hole, 0.5, (255, 255, 255, 255), 0.1)
        D.poly_wall(m, mw, Polygon(D.rect_pts(0, gz - 2.5, L, gz)), org, t, n, 0.0, WC, lambda u_, z_: (u_ / 3.2, z_ / 3.2))
        # aluminium fascia + number plaque inside the arch
        D.band(m, mf, D.P3(org, t, n, uc - aw / 2 + 0.05, 0, -0.75)[:2], D.P3(org, t, n, uc + aw / 2 - 0.05, 0, -0.75)[:2], gz + 3.1, gz + 4.3, 0.25, ALU)
        k = i % 16
        p0, p1 = D.P3(org, t, n, uc - aw / 2 + 0.35, gz + 3.35, -0.49), D.P3(org, t, n, uc - aw / 2 + 2.15, gz + 3.35, -0.49)
        m.quad(mg, [p0, p1, (p1[0], p1[1], gz + 4.05), (p0[0], p0[1], gz + 4.05)], [(k / 16, 0), ((k + 1) / 16, 0), ((k + 1) / 16, 0.25), (k / 16, 0.25)], n=(n[0], n[1], 0))
        D.band(m, mw, org, D.P3(org, t, n, L, 0, 0)[:2], gz + H - 0.7, gz + H + 0.1, 0.3, (255, 255, 255, 255))          # cornice
        # deck railing along the front edge
        for q in range(int(L // 1.8) + 1):
            p = D.P3(org, t, n, min(L - 0.05, q * 1.8), 0, -0.2); m.box(mf, p[0], p[1], 0.05, 0.05, gz + H + 0.1, gz + H + 1.2, col=D.hexl("#5a5f5e"))
        pm = D.P3(org, t, n, L / 2, 0, -0.2); m.box(mf, pm[0], pm[1], L, 0.04, gz + H + 1.1, gz + H + 1.18, rot=math.atan2(t[1], t[0]), col=D.hexl("#5a5f5e"))
        def skip(j, p, q):
            return (abs(p[0] - al[0]) < 0.3 and abs(p[1] - al[1]) < 0.3 and abs(q[0] - bl[0]) < 0.3 and abs(q[1] - bl[1]) < 0.3) or \
                   (abs(q[0] - al[0]) < 0.3 and abs(q[1] - al[1]) < 0.3 and abs(p[0] - bl[0]) < 0.3 and abs(p[1] - bl[1]) < 0.3)
        m.extrude(mf, mf, P, gz - 2.5, gz + H, col=ST, rcol=D.hexl("#5e5a52"), skip=skip)
    finish(m, "viadukt_arches", "Im Viadukt (Bogen)", ox, oy, oz, hide_union("Im Viadukt (Bogen)", [[round(u.representative_point().x, 1), round(u.representative_point().y, 1)] for u in units]))


if __name__ == "__main__":
    build()
