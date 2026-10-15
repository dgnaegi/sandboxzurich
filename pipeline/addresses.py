"""House numbers at facades and street-name signs at junctions (OSM ODbL + swissBUILDINGS3D).

address_rows(area, heights) -> [x, y, z, tx, ty, text]   (outward normal = (ty, -tx))
sign_rows(area, heights)    -> [x, y, z, heading, text]  (tangent = (cos h, sin h), outward normal = (sin h, -cos h))
"""
import math
from collections import defaultdict

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

import sources

NUM_Z, SIGN_Z, OFF = 2.2, 3.0, 0.05
NON_ROAD = {"footway", "path", "cycleway", "steps", "service", "track", "pedestrian", "corridor", "bridleway", "proposed", "construction"}
_cache = {}


def _data():
    if not _cache:
        nodes, els = sources.osm()
        fps = []
        for b in sources.buildings(margin=30):
            rings = [Polygon(p[:, :2]).buffer(0) for k, p in b["polys"] if k == 0 and len(p) >= 4]
            rings = [r for r in rings if not r.is_empty]
            if rings:
                u = shapely.union_all(rings).simplify(0.3)
                fps += [g for g in getattr(u, "geoms", [u]) if g.geom_type == "Polygon" and g.area > 8]
        _cache.update(nodes=nodes, els=els, fps=fps, tree=STRtree(fps))
    return _cache


def _wall_at(poly, pt):
    """Nearest wall point to pt on poly exterior -> (x, y, tx, ty) with outward normal (ty, -tx)."""
    ring = poly.exterior
    d = ring.project(Point(pt))
    c = ring.interpolate(d)
    best = None
    co = np.asarray(ring.coords)
    for a, b in zip(co[:-1], co[1:]):
        v = b - a
        L = float(np.hypot(*v))
        if L < 1e-6:
            continue
        t = np.clip(np.dot(np.array([c.x, c.y]) - a, v) / L**2, 0, 1)
        dist = float(np.hypot(*(a + t * v - [c.x, c.y])))
        if best is None or dist < best[0]:
            best = (dist, v / L, L)
    _, tg, L = best
    # outward check: a point slightly along the normal must lie outside
    if poly.contains(Point(c.x + tg[1] * 0.3, c.y - tg[0] * 0.3)):
        tg = -tg
    return c.x, c.y, float(tg[0]), float(tg[1]), L


def _streets(area):
    d = _data()
    x0, y0, x1, y1 = area
    ways = []
    for e in d["els"]:
        t = e.get("tags", {})
        if e["type"] != "way" or "highway" not in t or t["highway"] in NON_ROAD or not t.get("name"):
            continue
        pts = [d["nodes"][n] for n in e["nodes"] if n in d["nodes"]]
        if len(pts) >= 2 and any(x0 - 40 <= p[0] <= x1 + 40 and y0 - 40 <= p[1] <= y1 + 40 for p in pts):
            ways.append((t["name"], e["nodes"], pts))
    return ways


def address_rows(area, heights):
    d = _data()
    x0, y0, x1, y1 = area
    roads = _streets(area)
    rtree = STRtree([LineString(p) for _, _, p in roads]) if roads else None
    rows, seen = [], set()
    stats = {"points": 0, "snapped": 0}
    for e in d["els"]:
        t = e.get("tags", {})
        if "addr:housenumber" not in t:
            continue
        if e["type"] == "node":
            if e["id"] not in d["nodes"]:
                continue
            p = d["nodes"][e["id"]]
        elif e["type"] == "way":
            pts = [d["nodes"][n] for n in e.get("nodes", []) if n in d["nodes"]]
            if len(pts) < 3:
                continue
            p = tuple(Polygon(pts).buffer(0).centroid.coords[0])
        else:
            continue
        if not (x0 <= p[0] < x1 and y0 <= p[1] < y1):
            continue
        stats["points"] += 1
        pt = Point(p)
        cand = d["tree"].query(pt.buffer(10))
        if not len(cand):
            continue
        poly = min((d["fps"][i] for i in cand), key=lambda g: g.distance(pt))
        if poly.distance(pt) > 10:
            continue
        target = p
        if poly.contains(pt) and rtree is not None:  # interior point: use the wall facing the street
            street = t.get("addr:street")
            lines = [LineString(q) for n, _, q in roads if n == street] or [rtree.geometries[rtree.nearest(pt)]]
            ln = min(lines, key=lambda l: l.distance(pt))
            target = ln.interpolate(ln.project(pt)).coords[0]
        wx, wy, tx, ty, L = _wall_at(poly, target)
        text = t["addr:housenumber"].replace(" ", "")
        key = (round(wx), round(wy), text)
        if key in seen or L < 1.0:
            continue
        seen.add(key)
        stats["snapped"] += 1
        z = float(heights.at(wx, wy)) + NUM_Z
        rows.append([round(wx + ty * OFF, 2), round(wy - tx * OFF, 2), round(z, 2), round(tx, 3), round(ty, 3), text])
    nb = sum(1 for g in d["fps"] if x0 <= g.centroid.x < x1 and y0 <= g.centroid.y < y1)
    # one sign per wall segment; spread so two numbers never overlap
    rows.sort(key=lambda r: (r[0], r[1]))
    keep = []
    for r in rows:
        if all(math.hypot(r[0] - k[0], r[1] - k[1]) > 0.5 for k in keep):
            keep.append(r)
    nb_num = len({(round(r[0] / 8), round(r[1] / 8)) for r in keep})
    print(f"address_rows: {stats['points']} OSM address objects, {len(keep)} signs, "
          f"{nb} buildings in area, ~{nb_num} 8m-cells with a number")
    return keep


def sign_rows(area, heights):
    d = _data()
    x0, y0, x1, y1 = area
    ways = _streets(area)
    by_node = defaultdict(list)  # node -> [(name, direction)]
    for name, ids, pts in ways:
        loc = [(n, d["nodes"][n]) for n in ids if n in d["nodes"]]
        for i, (n, p) in enumerate(loc):
            q = loc[i + 1][1] if i + 1 < len(loc) else loc[i - 1][1]
            v = np.array(q) - p
            if np.hypot(*v) > 0.1:
                by_node[n].append((name, p, v / np.hypot(*v)))
    rows, used = [], set()
    junctions = 0
    for n, items in by_node.items():
        names = {i[0] for i in items}
        p = items[0][1]
        if len(names) < 2 or not (x0 <= p[0] < x1 and y0 <= p[1] < y1):
            continue
        junctions += 1
        for name in sorted(names):
            dirv = next(i[2] for i in items if i[0] == name)
            best = None
            for gi in d["tree"].query(Point(p).buffer(28)):
                g = d["fps"][gi]
                co = np.asarray(g.exterior.coords)
                for vi in range(len(co) - 1):
                    v = co[vi]
                    dist = float(np.hypot(*(v - p)))
                    if dist > 28:
                        continue
                    a, b = co[vi - 1], co[vi + 1]
                    for w, nb in ((b, 1), (a, -1)):
                        e = w - v
                        L = float(np.hypot(*e))
                        if L < 2.0 or (gi, vi, nb) in used:
                            continue
                        tg = e / L
                        # wall roughly parallel to the street, sign faces the junction side
                        par = abs(float(np.dot(tg, dirv)))
                        score = dist + (1 - par) * 12
                        if best is None or score < best[0]:
                            best = (score, gi, vi, nb, v, tg)
            if not best:
                continue
            _, gi, vi, nb, v, tg = best
            used.add((gi, vi, nb))
            g = d["fps"][gi]
            if g.contains(Point(v[0] + tg[1] * 0.3, v[1] - tg[0] * 0.3)):
                tg = -tg
            e = np.array(g.exterior.coords)[(vi + nb) % (len(g.exterior.coords) - 1)] - v
            e /= max(np.hypot(*e), 1e-6)
            pos = v + e * 0.9
            nx, ny = tg[1], -tg[0]
            z = float(heights.at(pos[0], pos[1])) + SIGN_Z
            rows.append([round(float(pos[0] + nx * OFF), 2), round(float(pos[1] + ny * OFF), 2), round(z, 2),
                         round(math.atan2(tg[1], tg[0]), 3), name])
    print(f"sign_rows: {junctions} junctions, {len(rows)} signs")
    return rows


if __name__ == "__main__":
    from config import AREA
    from build_testarea import heights_from
    H = heights_from(sources.buildings(margin=150))
    a = address_rows(AREA, H)
    s = sign_rows(AREA, H)
    print("sample", a[:3], s[:3])
