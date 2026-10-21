"""Real construction sites (research/sites.md).

Sources (all local, data/raw):
  - Stadt Zürich OGD «Aktuelle Tiefbauprojekte im öffentlichen Grund» (CC0): road works as polygons -> trench zones with
    barriers, cones, excavators, containers, signs, workers.
  - Stadt Zürich OGD «Hochbauprojekte in Ausführung» (AHB, CC0): building sites -> fence with banners, containers, crane.
  - OSM building=construction / landuse=construction -> fence, containers, excavator/crane depending on size.
Everything is planned once (deterministic, cached in data/build/sites.json) and cut into tiles by tile_meta().

Item rows of meta["sites"]: [type, x, y, z, yaw, a, b]
  0 cone  1 barrier(2 m)  2 excavator  3 container  4 fence panel(3 m; a = banner variant or -1)  5 «Baustelle» sign
  6 blinker  7 trench(a = length, b = width)  8 gravel pile  9 portable toilet  10 pallet with bricks
meta["cranes"]: [x, y, z, yaw, height, jib]     meta["workers"]: [x, y, z, yaw, kind]  (kind 0 stands, 1 looks at the trench)
"""
import json
import math
import os
import random

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.strtree import STRtree

from config import POLYGON, ROOT

CACHE = ROOT / "data" / "build" / "sites.json"
EXCL = ROOT / "pipeline" / "overrides" / "sites_excl.json"   # sites no longer active (User feedback)
RAW = ROOT / "data" / "raw" / "stadtzh_all"
TIEF = RAW / "geo_aktuelle_tiefbauprojekte_im_oeffentlichen_grund__aer_baustellen_a.geojson"
HOCH = RAW / "geo_ahb_hochbauprojekte_in_ausfuehrung_ogd__ahb_projekte_ogd.geojson"
Z = {"cone": 0, "barrier": 1, "excavator": 2, "container": 3, "fence": 4, "sign": 5, "blinker": 6, "trench": 7, "pile": 8,
     "toilet": 9, "pallet": 10}
MAX_PER_TILE = 90


def _local(coords):
    import sources
    a = np.asarray(coords, float)
    x, y = sources.geo.to_local(a[:, 0], a[:, 1])
    return list(zip(x.tolist(), y.tolist()))


def _geom(g):
    """GeoJSON (WGS84) -> shapely in local metres."""
    polys = []
    for p in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
        poly = Polygon(_local(p[0]), [_local(h) for h in p[1:]]).buffer(0)
        polys.extend(poly.geoms if poly.geom_type == "MultiPolygon" else [poly])
    return polys


def load():
    """All sites inside the play area (+ margin) as dicts {kind, name, text, poly(shapely), osm}. Cached as WKT."""
    excl = json.load(open(EXCL))["exclude"] if EXCL.exists() else {}
    if CACHE.exists():
        return [{**s, "poly": __import__("shapely.wkt").wkt.loads(s["wkt"])} for s in json.load(open(CACHE)) if s["id"] not in excl]
    import sources
    play = Polygon(POLYGON).buffer(260)
    out = []
    for f in json.load(open(TIEF))["features"]:
        pr = f["properties"]
        for poly in _geom(f["geometry"]):
            if poly.is_empty or not play.intersects(poly):
                continue
            today = __import__("datetime").date.today().isoformat()   # only works running on the build date (not yet started / finished ones out)
            if (pr.get("baubeginn") or "")[:10] > today or ((pr.get("bauende") or "9999")[:10] < today):
                continue
            txt = (pr.get("projektbeschrieb") or "").strip()
            out.append({"kind": "road", "id": f"t{pr.get('baunr')}", "name": pr.get("titel") or "", "text": txt,
                        "area": pr.get("baubereich") or "", "from": pr.get("baubeginn") or "", "to": pr.get("bauende") or "",
                        "wkt": poly.wkt})
    seen = set()
    for f in json.load(open(HOCH))["features"]:
        pr = f["properties"]
        for poly in _geom(f["geometry"]):
            if poly.is_empty or not play.intersects(poly):
                continue
            key = (pr.get("projektbezeichnung"), round(poly.centroid.x), round(poly.centroid.y))
            if key in seen:
                continue
            seen.add(key)
            out.append({"kind": "build", "id": f"h{pr.get('objectid')}", "name": pr.get("projektbezeichnung") or "", "text": "",
                        "wkt": poly.wkt, "ogd": 1})
    nodes, els = sources.osm()
    for e in els:
        t = e.get("tags") or {}
        if e["type"] != "way" or not e.get("nodes") or not (t.get("building") == "construction" or t.get("landuse") == "construction"):
            continue
        pts = [nodes[n] for n in e["nodes"] if n in nodes]
        if len(pts) < 4 or pts[0] != pts[-1]:
            continue
        poly = Polygon(pts).buffer(0)
        if poly.is_empty or poly.area < 60 or not play.contains(poly.centroid):
            continue
        out.append({"kind": "build", "id": f"o{e['id']}", "name": t.get("name", ""), "text": "", "wkt": poly.wkt,
                    "open": int(t.get("landuse") == "construction")})
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(CACHE, "w"), ensure_ascii=False, separators=(",", ":"))
    import shapely.wkt
    return [{**s, "poly": shapely.wkt.loads(s["wkt"])} for s in out if s["id"] not in excl]


def _rect(poly, cx, cy, r):
    """Orientation (yaw of long axis, length, width) of the road work polygon around (cx, cy)."""
    part = poly.intersection(Point(cx, cy).buffer(r))
    if part.is_empty or part.area < 4:
        part = poly
    m = part.minimum_rotated_rectangle
    if m.geom_type != "Polygon":
        return 0.0, 6.0, 3.0
    c = list(m.exterior.coords)
    a, b = np.array(c[1]) - np.array(c[0]), np.array(c[2]) - np.array(c[1])
    la, lb = np.hypot(*a), np.hypot(*b)
    v, L, W = (a, la, lb) if la >= lb else (b, lb, la)
    return math.atan2(v[1], v[0]), float(L), float(W)


def _ring(items, cx, cy, yaw, L, W, rnd, gap=True):
    """Barriers around a rectangle (long axis = yaw), cones in the corners."""
    c, s = math.cos(yaw), math.sin(yaw)
    hx, hy = L / 2 + 0.7, W / 2 + 0.7

    def put(t, u, v, ang, a=0, b=0):
        items.append([t, cx + u * c - v * s, cy + u * s + v * c, 0, ang, a, b])
    n = max(1, round(2 * hx / 2.0))
    for sgn in (-1, 1):  # long sides
        for i in range(n):
            if gap and sgn == 1 and i == n // 2 and rnd.random() < 0.5:
                continue
            put(Z["barrier"], -hx + (i + 0.5) * 2 * hx / n, sgn * hy, yaw)
    m = max(1, round(2 * hy / 2.0))
    for sgn in (-1, 1):  # short sides
        for i in range(m):
            put(Z["barrier"], sgn * hx, -hy + (i + 0.5) * 2 * hy / m, yaw + math.pi / 2)
    for u, v in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
        put(Z["cone"], u * 1.04, v * 1.1, 0)
    put(Z["blinker"], -hx, -hy, 0)
    put(Z["blinker"], hx, hy, 0)
    return c, s, hx, hy


def _road_zone(items, workers, poly, cx, cy, rnd, small):
    yaw, L, W = _rect(poly, cx, cy, 16)
    if small:
        L, W = min(max(L, 3.0), 9.0), min(max(W, 2.0), 4.0)
    else:
        L, W = min(max(L * 0.6, 5.0), 16.0), min(max(W * 0.5, 2.2), 3.4)
        if rnd.random() < 0.5:  # not every dig is lined up with the road
            yaw += rnd.uniform(-0.2, 0.2)
    c, s, hx, hy = _ring(items, cx, cy, yaw, L, W, rnd)
    items.append([Z["trench"], cx, cy, 0, yaw, L, W])
    # sign at the approach end, excavator / container / pile beyond the other end
    items.append([Z["sign"], cx - (hx + 1.6) * c, cy - (hx + 1.6) * s, 0, yaw + math.pi / 2, 0, 0])
    if not small and rnd.random() < 0.55:
        items.append([Z["excavator"], cx + (hx + 3.0) * c + rnd.uniform(-1, 1) * s, cy + (hx + 3.0) * s, 0, yaw + rnd.uniform(-0.6, 0.6) + math.pi, 0, 0])
    if not small and rnd.random() < 0.4:
        items.append([Z["container"], cx + (hy + 2.0) * -s - (hx - 1) * c, cy + (hy + 2.0) * c - (hx - 1) * s, 0, yaw, 0, 0])
    if rnd.random() < 0.5:
        items.append([Z["pile"], cx + (hy + 2.2) * s + 0.5 * c, cy - (hy + 2.2) * c + 0.5 * s, 0, rnd.uniform(0, 6), rnd.uniform(0.8, 1.4), 0])
    if small and rnd.random() < 0.5:
        items.append([Z["toilet"], cx + (hy + 2.5) * s, cy - (hy + 2.5) * c, 0, yaw, 0, 0])
    for i in range(rnd.choice((1, 2, 2, 3)) if not small else 1):
        u = rnd.uniform(-L / 2, L / 2)
        side = rnd.choice((-1, 1))
        workers.append([cx + u * c + side * (hy + 0.9) * -s, cy + u * s + side * (hy + 0.9) * c, 0, yaw - side * math.pi / 2, 1])


def _fence_ring(items, poly, rnd, variant):
    """Site fence panels (3 m) around the outline, one gap for the gate."""
    ring = poly.buffer(2.2, join_style=2).simplify(0.6)
    if ring.geom_type == "MultiPolygon":
        ring = max(ring.geoms, key=lambda g: g.area)
    ln = LineString(ring.exterior.coords)
    if ln.length > 420:  # huge sites: only fence part of it
        ln = LineString([ln.interpolate(d) for d in np.linspace(0, 420, 130)])
    n = int(ln.length // 3)
    gate = rnd.randrange(max(1, n))
    for i in range(n):
        if i == gate or i == gate + 1:
            continue
        a, b = ln.interpolate(i * 3.0), ln.interpolate(i * 3.0 + 3.0)
        yaw = math.atan2(b.y - a.y, b.x - a.x)
        v = (variant + i // 3) % 5 if i % 3 == 1 else -1
        items.append([Z["fence"], (a.x + b.x) / 2, (a.y + b.y) / 2, 0, yaw, v, 0])
    g = ln.interpolate(gate * 3.0 + 3.0)
    items.append([Z["sign"], g.x, g.y, 0, 0, 0, 0])
    return ring


def _build_site(items, workers, cranes, s, rnd):
    poly = s["poly"]
    if poly.area < 40:
        return
    ring = _fence_ring(items, poly, rnd, rnd.randrange(5))
    inner = poly.buffer(-1.0) if poly.area > 120 else poly
    if inner.is_empty:
        inner = poly
    rp = inner.representative_point()
    items.append([Z["container"], rp.x, rp.y, 0, rnd.uniform(0, 6.28), 0, 0])
    if poly.area > 250:
        q = poly.exterior.interpolate(rnd.random() * poly.exterior.length)
        items.append([Z["container"], q.x, q.y, 0, rnd.uniform(0, 6.28), 0, 0])
    if s.get("open") or s.get("ogd") is None and poly.area > 500:
        items.append([Z["excavator"], rp.x + 4, rp.y, 0, rnd.uniform(0, 6.28), 0, 0])
        items.append([Z["pile"], rp.x - 5, rp.y + 3, 0, rnd.uniform(0, 6), 1.4, 0])
    items.append([Z["pallet"], rp.x + 3, rp.y - 4, 0, rnd.uniform(0, 6.28), 0, 0])
    if rnd.random() < 0.5:
        items.append([Z["toilet"], rp.x - 3, rp.y - 3, 0, rnd.uniform(0, 6.28), 0, 0])
    big = poly.area > 900 or (poly.area > 400 and rnd.random() < 0.35) or (s.get("ogd") and poly.area > 1100)
    if big:
        h = 34 + rnd.uniform(0, 14)
        cranes.append([rp.x, rp.y, 0, rnd.uniform(0, 6.28), round(h, 1), round(24 + min(poly.area, 3000) ** 0.5 * 0.35 + rnd.uniform(0, 8), 1)])
    for _ in range(2 + int(poly.area > 300)):
        p = poly.buffer(1.2).exterior.interpolate(rnd.random() * poly.buffer(1.2).exterior.length)
        workers.append([p.x, p.y, 0, rnd.uniform(0, 6.28), 0])


_PLAN = None


def plan():
    """Deterministic plan for the whole area: (items, workers, cranes) with z = 0."""
    global _PLAN
    if _PLAN:
        return _PLAN
    items, workers, cranes = [], [], []
    rnd = random.Random(7)
    for s in load():
        poly = s["poly"]
        if s["kind"] == "road":
            area = poly.area
            if area < 400:
                pts = [poly.representative_point()]
            else:
                n = int(min(14, max(1, area / 650)))
                inner = poly.buffer(-1.5)
                inner = inner if not inner.is_empty else poly
                minx, miny, maxx, maxy = inner.bounds
                cand = [Point(x, y) for x in np.arange(minx, maxx, 8.0) for y in np.arange(miny, maxy, 8.0) if inner.contains(Point(x, y))]
                pts = []
                while cand and len(pts) < n:
                    best = max(cand, key=lambda p: min([p.distance(q) for q in pts], default=1e9) + rnd.random())
                    if pts and min(p.distance(best) for p in pts) < 24:
                        break
                    pts.append(best)
                    cand.remove(best)
                pts = pts or [poly.representative_point()]
            for p in pts:
                _road_zone(items, workers, poly, p.x, p.y, rnd, area < 400)
        else:
            _build_site(items, workers, cranes, s, rnd)
    _PLAN = (items, workers, cranes)
    return _PLAN


def blocked_zones(clear=1.0):
    """Shapes the traffic must not drive through: trench + barrier ring of road works, site fence panels, excavators and
    containers standing on the carriageway. Used by roadgraph.py to cut car / bike lanes (buffer `clear` m)."""
    items, _, _ = plan()
    zones = []
    for r in items:
        t, x, y, yaw = r[0], r[1], r[2], r[4]
        c, s = math.cos(yaw), math.sin(yaw)
        if t == Z["trench"]:
            hx, hy = r[5] / 2 + 0.7, r[6] / 2 + 0.7
            zones.append(Polygon([(x + u * c - v * s, y + u * s + v * c) for u, v in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]).buffer(clear))
        elif t == Z["fence"]:
            zones.append(LineString([(x - 1.5 * c, y - 1.5 * s), (x + 1.5 * c, y + 1.5 * s)]).buffer(clear))
        elif t in (Z["excavator"], Z["container"], Z["toilet"], Z["pile"], Z["pallet"]):
            zones.append(Point(x, y).buffer(1.8 + clear))
    return zones


def tile_meta(tb, H):
    """Meta fields for one tile: {"sites": rows, "cranes": rows, "workers": rows, "colliders": [...]}.
    Integration (build_testarea.py): SM = sites.tile_meta(tb, H); colliders += SM.pop("colliders") before meta is built,
    then `**SM` inside the meta dict."""
    items, workers, cranes = plan()
    inside = lambda r: tb.contains(Point(r[1], r[2]))  # noqa: E731
    rows = []
    cols = []
    for r in items:
        if not tb.contains(Point(r[1], r[2])):
            continue
        z = round(float(H.at(r[1], r[2])), 2)
        rows.append([r[0], round(r[1], 2), round(r[2], 2), z, round(r[3 + 1], 3), round(r[5], 2), round(r[6], 2)])
        if r[0] in (2, 3, 9):  # excavators, containers, toilets block the player
            w, d = (3.2, 2.6) if r[0] == 2 else (6.0, 2.4) if r[0] == 3 else (1.2, 1.2)
            c, s = math.cos(r[4]), math.sin(r[4])
            cols.append([[round(r[1] + u * c - v * s, 2), round(r[2] + u * s + v * c, 2)] for u, v in
                         ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))])
    rows = rows[:MAX_PER_TILE * 6]
    return {
        "sites": rows,
        "cranes": [[round(r[0], 2), round(r[1], 2), round(float(H.at(r[0], r[1])), 2), round(r[3], 2), r[4], r[5]]
                   for r in cranes if tb.contains(Point(r[0], r[1]))],
        "workers": [[round(r[0], 2), round(r[1], 2), round(float(H.at(r[0], r[1])), 2), round(r[3], 2), r[4]]
                    for r in workers if tb.contains(Point(r[0], r[1]))],
        "colliders": cols,
    }


def scaffold_rows(tb, segs, ogd_only=True):
    """Facade scaffolding rows (construction.ts format) on buildings that lie inside a Hochbau site polygon."""
    sites = [s for s in load() if s["kind"] == "build"]
    tree = STRtree([s["poly"].buffer(2.0) for s in sites])
    out, per = [], {}
    for sg in sorted(segs, key=lambda q: -q["w"]):
        if sg["w"] < 6 or not tb.contains(Point(sg["x"], sg["y"])):
            continue
        pt = Point(sg["x"], sg["y"])
        for i in tree.query(pt):
            if sites[i]["poly"].buffer(2.0).contains(pt) and per.get(i, 0) < 2:
                per[i] = per.get(i, 0) + 1
                out.append([round(sg["x"], 2), round(sg["y"], 2), round(sg["z"] - (3.45 if not sg.get("blank") else 1.75), 2),
                            round(sg["tx"], 4), round(sg["ty"], 4), round(min(sg["w"], 16), 1), 14.0])
                break
    return out


def infos():
    """Road work info for easter eggs: [{id, x, y, title, text}] (real OGD text)."""
    out = []
    for s in load():
        if s["kind"] != "road" or not s["text"]:
            continue
        p = s["poly"].representative_point()
        out.append({"id": s["id"], "x": round(p.x, 1), "y": round(p.y, 1), "title": s["name"], "text": s["text"],
                    "area": s.get("area", ""), "to": s.get("to", "")})
    return out


if __name__ == "__main__":
    ss = load()
    it, wk, cr = plan()
    import collections
    print("sites:", collections.Counter(s["kind"] for s in ss), "items", len(it), "workers", len(wk), "cranes", len(cr))
    cnt = collections.Counter((int(r[1] // 200), int(r[2] // 200)) for r in it)
    print("tiles with sites:", len(cnt), "max items/tile:", max(cnt.values()), "infos:", len(infos()))
