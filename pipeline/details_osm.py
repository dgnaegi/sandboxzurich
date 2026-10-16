"""Street-detail layer from OSM tags (ODbL, data/raw/osm/kreise.json): advertising columns, phone booths, post boxes,
recycling points, guideposts (Velo/Wander-Wegweiser), clocks, info boards, charging posts, freestanding kiosks, gates,
hedges and fences. Hand corrections: pipeline/overrides/details.json. Rows go to web/src/world/details.ts.

Hooks (build_testarea.py):
    details_osm.prepare(nodes, els)                         once, before the tiles are built (forked workers share it)
    details_osm.tile_meta(tb, H, S, C, P, inside_any)       -> {"details": {objs, lines, leaves}, "_colliders": [...]}
Row format objs: [type, x, y, z, heading_rad(CCW from east, object +x along it), a, b, c]. Lines: {t, h, w, pts[[x,y,z]]}.
Leaves (autumn litter under deciduous trees): see details_leaves.py.
"""
import json
import math

import numpy as np
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

from config import ROOT
from styles import h32
import details_facade
import details_leaves

OVR = ROOT / "pipeline" / "overrides" / "details.json"
_D = None  # prepared OSM features
SEG = 3.0  # line sampling step (m)


def _num(v, d):
    try:
        return float(str(v).replace(",", ".").split()[0])
    except (TypeError, ValueError, IndexError):
        return d


def prepare(nodes, els):
    """Pick the relevant OSM nodes/ways once (local metres)."""
    global _D
    pts, lines, way_of = [], [], {}
    for e in els:
        t = e.get("tags") or {}
        if not t:
            continue
        if e["type"] == "node" and e["id"] in nodes:
            x, y = nodes[e["id"]]
            kind = None
            if t.get("advertising") == "column":
                kind = "column"
            elif t.get("amenity") == "telephone":
                kind = "phone"
            elif t.get("amenity") == "post_box":
                kind = "postbox"
            elif t.get("amenity") == "recycling" and t.get("recycling_type") != "centre" and t.get("location") != "underground":
                kind = "recycling"
            elif t.get("information") == "guidepost":
                kind = "guidepost"
            elif t.get("information") in ("board", "map") and t.get("tourism") == "information":
                kind = "infoboard"
            elif t.get("amenity") == "clock" and t.get("support") == "pole":
                kind = "clock"
            elif t.get("amenity") == "charging_station":
                kind = "charger"
            elif t.get("amenity") == "drinking_water":
                kind = "dwater"
            elif t.get("shop") == "kiosk":
                kind = "kiosk"
            elif t.get("barrier") in ("gate", "swing_gate"):
                kind = "gate"
            if kind:
                pts.append((kind, x, y, t, e["id"]))
        elif e["type"] == "way" and e.get("nodes"):
            b = t.get("barrier")
            if b in ("hedge", "fence") or t.get("natural") == "hedge":
                xy = [nodes[n] for n in e["nodes"] if n in nodes]
                if len(xy) >= 2:
                    lines.append(("hedge" if b == "hedge" or t.get("natural") == "hedge" else b, xy, t))
                    for n in e["nodes"]:
                        way_of.setdefault(n, len(lines) - 1)
            elif t.get("shop") == "kiosk" and len(e["nodes"]) >= 4:
                xy = [nodes[n] for n in e["nodes"] if n in nodes]
                if len(xy) >= 4:
                    c = np.mean(xy, axis=0)
                    pts.append(("kiosk", float(c[0]), float(c[1]), t, e["id"]))
    _D = {"pts": pts, "lines": lines, "way_of": way_of, "ovr": json.load(open(OVR)) if OVR.exists() else {}}
    print(f"details_osm: {len(pts)} points, {len(lines)} barrier ways", flush=True)


def _road_angle(S, tree, x, y):
    """Direction (math angle, radians) of the nearest street at (x, y)."""
    ln = S["ways"][int(tree.nearest(Point(x, y)))]["line"]
    s = ln.project(Point(x, y))
    a, b = ln.interpolate(max(0, s - 1.5)), ln.interpolate(s + 1.5)
    return math.atan2(b.y - a.y, b.x - a.x)


def _segments(xy, step=SEG):
    """Densify a polyline to about `step` metres."""
    out = [xy[0]]
    for a, b in zip(xy[:-1], xy[1:]):
        n = max(1, round(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        out += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]
    return out


def _sq(x, y, hx, hy):
    return [[round(x + dx, 2), round(y + dy, 2)] for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]


def tile_meta(tb, H, S, C, P, inside_any, segs=(), curb=0.12):
    if _D is None:
        return {"_colliders": []}
    roads = S["roads"]
    z = lambda x, y: round(float(H.at(x, y)), 2)
    tree = STRtree([w["line"] for w in S["ways"]])
    fount = [(r[0], r[1]) for r in C.get("fountains", [])]
    ovr = _D["ovr"]
    drop = [Point(*p).buffer(ovr.get("drop_r", 1.5)) for p in ovr.get("drop", [])]
    objs, colliders = [], []

    def add(t, x, y, h, a=0, b=0, c=0):
        objs.append([t, round(x, 2), round(y, 2), z(x, y), round(h, 3), a, b, c])

    for kind, x, y, t, oid in _D["pts"]:
        if not tb.contains(Point(x, y)) or any(d.contains(Point(x, y)) for d in drop):
            continue
        k = h32(f"{kind}{oid}")
        if kind == "column":
            add("column", x, y, 0, k % 4, 1 if t.get("lit") == "yes" else 0)
            colliders.append(_sq(x, y, .5, .5))
            continue
        if kind == "clock":
            add("clock", x, y, (k % 628) / 100)
            continue
        if kind == "guidepost":
            bike = t.get("bicycle") == "yes" and t.get("hiking") != "yes"
            add("guidepost", x, y, (k % 628) / 100, 1 if bike else 0, 1 + k % 2)
            continue
        if kind == "dwater" and any(math.hypot(x - fx, y - fy) < 6 for fx, fy in fount):
            continue  # already a Stadt-Zürich fountain (OGD) here
        if kind in ("postbox", "recycling", "infoboard", "kiosk", "gate") and inside_any(x, y):
            continue  # indoor / on a building footprint
        if kind == "gate":
            li = _D["way_of"].get(oid)
            if li is None:
                continue
            ln = LineString(_D["lines"][li][1])
            s = ln.project(Point(x, y))
            a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(s + 1)
            w = _num(t.get("width"), 3.0 if t.get("access") != "private" and t.get("vehicle") != "no" else 1.2)
            add("gate", x, y, math.atan2(b.y - a.y, b.x - a.x), round(min(max(w, 0.9), 5.0), 1), 1 if t.get("material") == "wood" else 0)
            continue
        if kind == "kiosk" and roads.contains(Point(x, y)):
            continue
        ang = _road_angle(S, tree, x, y)
        if kind == "dwater":
            add("dwater", x, y, ang, 1 if t.get("material") == "metal" else 0)
        elif kind == "phone":
            add("phone", x, y, ang)
        elif kind == "postbox":
            add("postbox", x, y, ang, 1 if t.get("post_box:type") == "lamp" else 0)
        elif kind == "recycling":
            glass = t.get("recycling:glass_bottles") == "yes" or t.get("recycling:glass") == "yes"
            cans = t.get("recycling:cans") == "yes" or t.get("recycling:aluminium") == "yes"
            cloth = t.get("recycling:clothes") == "yes"
            add("recycling", x, y, ang, (1 if glass else 0) | (2 if cans else 0) | (4 if cloth else 0))
            colliders.append(_sq(x, y, 1.2, .5))
        elif kind == "infoboard":
            add("infoboard", x, y, ang + math.pi / 2, 1 if t.get("information") == "map" else 0)
        elif kind == "charger":
            add("charger", x, y, ang)
        elif kind == "kiosk":
            add("kiosk", x, y, ang, 1 if "kiosk" in (t.get("brand") or "").lower() else 0)
            colliders.append(_sq(x, y, 1.6, 1.2))
    for o in ovr.get("add", []):  # hand-placed from photos: {t, p:[x,y], h(deg), a, b, c}
        if tb.contains(Point(*o["p"])):
            add(o["t"], o["p"][0], o["p"][1], math.radians(o.get("h", 0)), o.get("a", 0), o.get("b", 0), o.get("c", 0))

    objs += details_facade.rows(segs, tb, H, roads)
    lines = []
    for kind, xy, t in _D["lines"]:
        if t.get("area") == "yes":
            continue
        ls = LineString(xy)
        if not ls.intersects(tb):
            continue
        if kind == "hedge":
            h, w, k = _num(t.get("height"), 1.4), _num(t.get("width"), 0.8), "hedge"
        else:
            k = {"chain_link": "mesh", "wire": "mesh", "wood": "wood", "wood_panel": "wood"}.get(t.get("fence_type", ""), "rail")
            h, w = _num(t.get("height"), {"mesh": 1.8, "wood": 1.2, "rail": 1.1}[k]), 0
        part = ls.intersection(tb)
        for g in getattr(part, "geoms", [part]):
            if g.geom_type != "LineString" or g.length < 1.0:
                continue
            pts = _segments(list(g.coords))
            keep, run = [], []
            for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):  # cut out road / building / gate parts
                m = Point((x0 + x1) / 2, (y0 + y1) / 2)
                if roads.contains(m) or inside_any(m.x, m.y) or any(d.contains(m) for d in drop):
                    if len(run) > 1:
                        keep.append(run)
                    run = []
                    continue
                if not run:
                    run = [(x0, y0)]
                run.append((x1, y1))
            if len(run) > 1:
                keep.append(run)
            for run in keep:
                lines.append({"t": k, "h": round(h, 2), "w": round(w, 2), "pts": [[round(x, 2), round(y, 2), z(x, y)] for x, y in run]})
    leaves = details_leaves.rows(P.get("trees", []), H, roads, inside_any, curb)
    out = {"objs": objs, "lines": lines, "leaves": leaves}
    return {"details": out, "_colliders": colliders} if objs or lines or leaves else {"_colliders": []}
