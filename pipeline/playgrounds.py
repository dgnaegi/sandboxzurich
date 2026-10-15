"""Playground equipment at real playgrounds (public and in residential courtyards).

Sources: OSM leisure=playground areas/points and playground=* equipment nodes (exact positions, ODbL);
Stadt Zürich OGD Spielplätze (points with the official equipment list «geraete», CC0).
Areas without mapped equipment get the official list (nearest OGD point <= 60 m) or a size-based default.
Rows: [x, y, z, heading, type]
"""
import hashlib
import json
import math

import numpy as np
from shapely.geometry import Point, Polygon

from config import ROOT

TYPES = ("swing", "slide", "sandpit", "climb", "seesaw", "springy", "roundabout", "tower", "basketswing", "playhouse")
OSM_EQ = {"swing": "swing", "slide": "slide", "sandpit": "sandpit", "climbingframe": "climb", "seesaw": "seesaw",
          "springy": "springy", "roundabout": "roundabout", "structure": "tower", "basketswing": "basketswing",
          "playhouse": "playhouse", "climbing_frame": "climb", "zipwire": "climb", "rope_traverse": "climb"}
OGD_EQ = (("schaukel", "swing"), ("rutsch", "slide"), ("sand", "sandpit"), ("kletter", "climb"), ("wippe", "seesaw"),
          ("feder", "springy"), ("karussell", "roundabout"), ("drehscheibe", "roundabout"), ("spielturm", "tower"),
          ("nestschaukel", "basketswing"), ("spielhaus", "playhouse"), ("hütte", "playhouse"))
FOOT = {"swing": 3.6, "slide": 4.0, "sandpit": 3.6, "climb": 4.5, "seesaw": 3.6, "springy": 1.4, "roundabout": 2.6,
        "tower": 5.0, "basketswing": 3.4, "playhouse": 2.6}


def _h(s):
    return int(hashlib.md5(str(s).encode()).hexdigest()[:8], 16)


def _ogd():
    f = ROOT / "data" / "raw" / "stadtzh_extra" / "spielplaetze.geojson"
    if not f.exists():
        return []
    import sources
    out = []
    for ft in json.load(open(f))["features"]:
        g = ft.get("geometry")
        if not g:
            continue
        txt = " ".join(str(ft["properties"].get(k) or "") for k in ("geraete", "elemente")).lower()
        kinds = [t for k, t in OGD_EQ if k in txt]
        x, y = g["coordinates"][:2]
        p = Point(x - 2681400, y - 1248700) if x > 1e5 else Point(sources.geo.to_local(x, y))  # LV95 or WGS84
        out.append((p, list(dict.fromkeys(kinds))))
    return out


def _default(area):
    if area < 80:
        return ["sandpit", "springy"]
    if area < 300:
        return ["sandpit", "swing", "slide", "springy"]
    return ["sandpit", "swing", "slide", "climb", "seesaw", "springy", "basketswing"]


def _place(poly, kinds, seed, taken):
    """Greedy placement inside the (shrunk) area; returns [(x, y, heading, kind)]."""
    inner = poly.buffer(-1.2)
    if inner.is_empty:
        inner = poly
    x0, y0, x1, y1 = inner.bounds
    rnd = np.random.default_rng(seed % (2 ** 31))
    out = []
    for kind in kinds:
        r = FOOT[kind] / 2
        for _ in range(60):
            p = Point(rnd.uniform(x0, x1), rnd.uniform(y0, y1))
            if not inner.contains(p):
                continue
            if any(math.hypot(p.x - q[0], p.y - q[1]) < r + q[2] + 0.8 for q in taken):
                continue
            taken.append((p.x, p.y, r))
            out.append((p.x, p.y, float(rnd.uniform(0, math.pi)), kind))
            break
    return out


def rows(nodes, els, H, buildings_tree=None):
    ogd = _ogd()
    areas, eq = [], []
    for e in els:
        t = e.get("tags") or {}
        if t.get("playground") and e["type"] == "node" and e["id"] in nodes:
            k = OSM_EQ.get(t["playground"])
            if k:
                eq.append((nodes[e["id"]], k))
        if t.get("leisure") != "playground":
            continue
        if e["type"] == "way":
            pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(pts) >= 4:
                g = Polygon(pts).buffer(0)
                if not g.is_empty and g.area > 15:
                    areas.append((e["id"], g))
        elif e["type"] == "node" and e["id"] in nodes:
            areas.append((e["id"], Point(nodes[e["id"]]).buffer(9)))
    for p, _ in ogd:  # official playgrounds not mapped as OSM areas
        if not any(g.distance(p) < 25 for _, g in areas):
            areas.append((f"ogd{int(p.x)}_{int(p.y)}", p.buffer(10)))
    out, taken = [], []
    for (x, y), k in eq:
        taken.append((x, y, FOOT[k] / 2))
        out.append([x, y, k, _h((x, y)) % 314 / 100])
    for aid, g in areas:
        if any(g.contains(Point(q[0], q[1])) for q in taken):
            continue  # equipment mapped individually
        if buildings_tree is not None:
            g = g.difference(buildings_tree(g))
            if g.is_empty or g.area < 12:
                continue
            if g.geom_type == "MultiPolygon":
                g = max(g.geoms, key=lambda q: q.area)
        near = [k for p, k in ogd if p.distance(g) < 60 and k]
        kinds = near[0] if near else _default(g.area)
        for x, y, hd, k in _place(g, kinds, _h(aid), taken):
            out.append([x, y, k, hd])
    rows_ = [[round(float(x), 2), round(float(y), 2), round(float(H.at(x, y)), 2), round(float(hd), 2), k] for x, y, k, hd in out]
    from collections import Counter
    print(f"playgrounds: {len(areas)} areas, {len(rows_)} items {dict(Counter(r[4] for r in rows_))}")
    return rows_
