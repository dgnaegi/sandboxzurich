"""Playable area: Kreis 4 + 5, plus parts of Kreis 9 (Hohlstrasse/Badenerstrasse corridor, Lindenplatz, Bahnhof
Altstetten) and Kreis 3 (Bahnhof Wiedikon, Schmiede Wiedikon). Output data/build/playarea.json:
{polygon: [[x, y], ...], bbox: [x0, y0, x1, y1], tiles: [[ix, iy], ...]} in local metres. The edge is closed off
with construction fences in the game."""
import json

import numpy as np
import shapely
import shapely.ops
from shapely.geometry import LineString, Point, Polygon, box

import sources
from config import ROOT, TILE

OUT = ROOT / "data" / "build" / "playarea.json"


def kreise():
    d = json.load(open(ROOT / "research" / "kreise_poly_simplified.json"))
    out = {}
    for name, ll in d.items():
        a = np.array(ll)
        x, y = sources.geo.to_local(a[:, 1], a[:, 0])
        out[name] = Polygon(np.column_stack([x, y])).buffer(0)
    return out


def main():
    K = kreise()
    nodes, els = sources.osm()
    named_pts, named_lines = {}, {}
    for e in els:
        t = e.get("tags", {})
        nm = t.get("name")
        if not nm:
            continue
        if e["type"] == "node" and e["id"] in nodes:
            named_pts.setdefault(nm, []).append(nodes[e["id"]])
        elif e["type"] == "way":
            pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(pts) >= 2:
                named_pts.setdefault(nm, []).append(tuple(np.mean(pts, axis=0)))
                if "highway" in t:
                    named_lines.setdefault(nm, []).append(LineString(pts))
    k9 = K["Kreis 9"]

    def place(name, near=None):
        pts = named_pts.get(name, [])
        if near is not None:
            pts = [p for p in pts if near.contains(Point(p))] or pts
        return Point(np.median(np.array(pts), axis=0)) if pts else None

    parts = [K["Kreis 4"], K["Industriequartier"]]
    for nm, r, region in (("Lindenplatz", 260, k9), ("Zürich Altstetten", 320, k9), ("Zürich Wiedikon", 300, K["Kreis 3"]),
                          ("Schmiede Wiedikon", 250, K["Kreis 3"])):
        p = place(nm, region)
        print(nm, None if p is None else (round(p.x), round(p.y)))
        if p is not None:
            parts.append(p.buffer(r))
    # street corridors in Kreis 9 (Hohlstrasse and Badenerstrasse up to Lindenplatz/Altstetten)
    for street, w in (("Hohlstrasse", 140), ("Badenerstrasse", 110)):
        lines = [ln for ln in named_lines.get(street, []) if ln.intersects(k9)]
        if lines:  # only the stretch between Kreis 4 and Lindenplatz / Bahnhof Altstetten
            parts.append(shapely.union_all(lines).intersection(box(-2450, -900, 600, 1100)).buffer(w))
    sites = []
    # whole landmark sites that must be inside (User 2026-10-15): Friedhof Sihlfeld incl. Krematorium, Stadion Letzigrund
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way" and (("Sihlfeld" in t.get("name", "") and t.get("landuse") == "cemetery")
                                   or (t.get("leisure") == "stadium" and "Letzigrund" in t.get("name", ""))):
            pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(pts) >= 4:
                sites.append(Polygon(pts))
                print("site", t.get("name"), round(Polygon(pts).area))
    # manual extensions (pipeline/overrides/playarea_extra.json): oriented rects, e.g. Zuerich HB
    extra = ROOT / "pipeline" / "overrides" / "playarea_extra.json"
    if extra.exists():
        for r in json.load(open(extra)).get("rects", []):
            a, (cx, cy) = np.radians(r["angle_deg"]), r["center"]
            d, c = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
            parts.append(Polygon([(cx + d[0] * u + c[0] * v, cy + d[1] * u + c[1] * v)
                                  for u, v in ((r["d"][0], r["c"][0]), (r["d"][1], r["c"][0]), (r["d"][1], r["c"][1]), (r["d"][0], r["c"][1]))]))
            print("extra rect", r["name"])
    main = shapely.union_all(parts)
    for g in sites:  # site + a walkable connection to the main area (e.g. Sihlfeld quarter between Kreis 4 and the cemetery)
        a, b = shapely.ops.nearest_points(g, main)
        parts += [g.buffer(45), LineString([a, b]).buffer(170)]
    poly = shapely.union_all(parts).buffer(40).buffer(-40)
    if poly.geom_type == "MultiPolygon":  # keep the connected main part
        poly = max(poly.geoms, key=lambda g: g.area)
    poly = Polygon(poly.exterior).simplify(12)
    x0, y0, x1, y1 = poly.bounds
    # tiles touching the area, plus a 220 m ring of backdrop tiles (buildings only, seen over the fence)
    ring = poly.buffer(220)
    tiles = []
    for ix in range(int(np.floor((x0 - 220) / TILE)), int(np.ceil((x1 + 220) / TILE))):
        for iy in range(int(np.floor((y0 - 220) / TILE)), int(np.ceil((y1 + 220) / TILE))):
            tb = box(ix * TILE, iy * TILE, (ix + 1) * TILE, (iy + 1) * TILE)
            if poly.intersects(tb):
                tiles.append([ix, iy, 1])
            elif ring.intersects(tb):
                tiles.append([ix, iy, 0])
    json.dump({"polygon": np.round(np.asarray(poly.exterior.coords), 1).tolist(), "bbox": [round(v, 1) for v in poly.bounds],
               "tiles": tiles, "area_km2": round(poly.area / 1e6, 2)}, open(OUT, "w"))
    print(f"area {poly.area / 1e6:.2f} km², bbox {[round(v) for v in poly.bounds]}, {sum(t[2] for t in tiles)} play tiles + {sum(1 - t[2] for t in tiles)} backdrop")


if __name__ == "__main__":
    main()
