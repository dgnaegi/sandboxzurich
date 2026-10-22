"""Zone 2 point 'Viadukt (Markthalle)': east end of the stone viaduct arcade (OSM building 'Markthalle "Im Viadukt"', swissBUILDINGS3D ID_09F3B948).
The older k45_viadukt model only covers the Viaduktstrasse units (start_date 2010 with addr:street); this stretch was left as a plain shop box under a grey deck.
Same look as k45_viadukt (rough ashlar, round arches with recessed glazed shopfront, pale aluminium fascia, cornice, deck railing), units cut from the
OSM outline along its long axis (~6.6 m per arch). Photos: research/zones/zone2_cam_photos.json (viadukt_markthalle 0-6, 15), protocol research/zones/z2/area_josef.md.
Registers into overrides/landmarks_z2b.json."""
import math
import numpy as np
import common
from common import *
import lm
from lm import *
import detail as D
import osmq
from shapely.geometry import LineString, MultiLineString, Point, box
from shapely.affinity import rotate

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z2b.json"
TITLE = "Markthalle Im Viadukt (Bogenreihe Ost)"
NAME = "z2b_markthalle"


def build():
    common.OVR = OVRZ
    hall = [Polygon(p).buffer(0) for t, p in osmq.rows if t.get("name") == 'Markthalle "Im Viadukt"'][0]
    streets = [pts for t, pts in osmq.rows if t.get("name") in ("Viaduktstrasse", "Ottostrasse") and "building" not in t]
    street = MultiLineString([LineString(p) for p in streets])
    rr = hall.minimum_rotated_rectangle; rc = list(rr.exterior.coords)[:4]
    e0, e1 = math.dist(rc[0], rc[1]), math.dist(rc[1], rc[2])
    (a, b), Ls = ((rc[0], rc[1]), e0) if e0 >= e1 else ((rc[1], rc[2]), e1)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    c0 = hall.centroid
    h2 = rotate(hall, -math.degrees(ang), origin=(c0.x, c0.y))       # long axis along +x
    minx, miny, maxx, maxy = h2.bounds
    n = max(4, int(round((maxx - minx) / 6.6))); step = (maxx - minx) / n
    units = []
    for i in range(n):
        piece = h2.intersection(box(minx + i * step, miny - 1, minx + (i + 1) * step, maxy + 1))
        if piece.is_empty or piece.area < 20: continue
        if piece.geom_type != "Polygon": piece = max(piece.geoms, key=lambda g: g.area)
        units.append(rotate(piece, math.degrees(ang), origin=(c0.x, c0.y)))
    cx = float(np.mean([u.centroid.x for u in units])); cy = float(np.mean([u.centroid.y for u in units]))
    ox, oy = round(cx, 1), round(cy, 1); oz = ground(ox, oy)
    units.sort(key=lambda u: (u.centroid.x, u.centroid.y))
    rng = np.random.default_rng(5)
    m = Model(NAME)
    mw = m.mat("stone", D.ashlar(hexc("#a39580"), rows=8, rough=0.13, joint=0.62, seed=6))
    regions = [(i * 64, (i + 1) * 64, "", "#1e1e1e", "#dcdcd8", (200, 190, 170)) for i in range(16)]
    ga = D.glass_atlas_g(frame="#1c1c1c", glass="#25323a", sky="#8ea4b2", cols=4, rows=2, seed=12, bar=3, lit_p=0.7, curtains=False,
                         sign=D.letters_strip(regions, size=26, max_gap=2))
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid((255, 255, 255, 255)))
    H = 10.0; ST, ALU = D.hexl("#8f8573"), D.hexl("#dcdcd8")
    WC = (232, 228, 218, 255)
    for i, u in enumerate(units):
        r = u.minimum_rotated_rectangle; rc = list(r.exterior.coords)[:4]
        e0 = math.dist(rc[0], rc[1]); e1 = math.dist(rc[1], rc[2])
        edges = [(rc[0], rc[1]), (rc[2], rc[3])] if e0 <= e1 else [(rc[1], rc[2]), (rc[3], rc[0])]
        best = min(edges, key=lambda ab: street.distance(Point((ab[0][0] + ab[1][0]) / 2, (ab[0][1] + ab[1][1]) / 2)))
        a, b = best; c = u.centroid; mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        nx_, ny_ = (b[1] - a[1]), -(b[0] - a[0])
        if nx_ * (mid[0] - c.x) + ny_ * (mid[1] - c.y) < 0: a, b = b, a
        gz = ground(c.x, c.y) - oz
        P = localize(Polygon(rc), ox, oy)
        al = (a[0] - ox, a[1] - oy); bl = (b[0] - ox, b[1] - oy)
        L, t, nn = D.frame_of(al, bl)
        aw = min(5.2, L - 1.4); uc = L / 2
        hole = D.arch_pts(uc - aw / 2, gz + 0.05, uc + aw / 2, gz + 5.4)
        org = (al[0], al[1])
        D.bay(m, mw, mg, mf, org, t, nn, 0, L, gz, gz + H, hole, 0.8, int(rng.integers(0, D.NV)), WC, D.hexl("#7b7262"), (3.2, 3.2), None)
        D.surround(m, mw, org, t, nn, hole, 0.5, (255, 255, 255, 255), 0.1)
        D.poly_wall(m, mw, Polygon(D.rect_pts(0, gz - 2.5, L, gz)), org, t, nn, 0.0, WC, lambda u_, z_: (u_ / 3.2, z_ / 3.2))
        D.band(m, mf, D.P3(org, t, nn, uc - aw / 2 + 0.05, 0, -0.75)[:2], D.P3(org, t, nn, uc + aw / 2 - 0.05, 0, -0.75)[:2], gz + 3.1, gz + 4.3, 0.25, ALU)
        D.band(m, mw, org, D.P3(org, t, nn, L, 0, 0)[:2], gz + H - 0.7, gz + H + 0.1, 0.3, (255, 255, 255, 255))
        for q in range(int(L // 1.8) + 1):
            p = D.P3(org, t, nn, min(L - 0.05, q * 1.8), 0, -0.2); m.box(mf, p[0], p[1], 0.05, 0.05, gz + H + 0.1, gz + H + 1.2, col=D.hexl("#5a5f5e"))
        pm = D.P3(org, t, nn, L / 2, 0, -0.2); m.box(mf, pm[0], pm[1], L, 0.04, gz + H + 1.1, gz + H + 1.18, rot=math.atan2(t[1], t[0]), col=D.hexl("#5a5f5e"))
        if i % 3 == 1:
            pm = (org[0] + t[0] * L / 2 - nn[0] * 3.2, org[1] + t[1] * L / 2 - nn[1] * 3.2)
            m.box(mf, pm[0], pm[1], 0.35, 0.35, gz + H, gz + H + 7.6, col=D.hexl("#7d8184"))
        def skip(j, p, q, al=al, bl=bl):
            return (abs(p[0] - al[0]) < 0.3 and abs(p[1] - al[1]) < 0.3 and abs(q[0] - bl[0]) < 0.3 and abs(q[1] - bl[1]) < 0.3) or \
                   (abs(q[0] - al[0]) < 0.3 and abs(q[1] - al[1]) < 0.3 and abs(p[0] - bl[0]) < 0.3 and abs(p[1] - bl[1]) < 0.3)
        m.extrude(mw, mf, P, gz - 2.5, gz + H, mod=(3.2, 3.2), col=WC, rcol=D.hexl("#6e675c"), skip=skip)
    hide = [[round(p.representative_point().x, 1), round(p.representative_point().y, 1)] for p in (bid("ID_09F3B948")["fp"], hall)]
    finish(m, NAME, TITLE, ox, oy, oz, hide_union(TITLE, hide), reg=False)
    d = json.load(open(OVRZ)) if OVRZ.exists() else {"landmarks": []}
    d["landmarks"] = [e for e in d["landmarks"] if e["name"] != TITLE]
    d["landmarks"].append({"name": TITLE, "model": f"/models/landmarks/{NAME}.glb", "x": round(ox, 2), "y": round(oy, 2), "z": round(oz, 2), "heading": 0, "hide": hide_union(TITLE, hide)})
    json.dump(d, open(OVRZ, "w"), indent=1)


if __name__ == "__main__":
    build()
