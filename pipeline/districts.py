"""HUD location data: real Stadtkreis/Quartier polygons (Stadt Zürich OGD, statistische Quartiere, CC0) plus named streets
and squares from OSM. Output: web/public/data/districts.json. Usage: .venv/bin/python pipeline/districts.py"""
import json

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box

import sources
from config import AREA, ROOT

RAW = ROOT / "data" / "raw" / "stadtzh_all" / "geo_statistische_quartiere__adm_statistische_quartiere_v.geojson"
ROADS = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "living_street", "pedestrian", "service", "cycleway", "footway", "path", "steps"}
HUBS = {"Zürich HB", "Limmatplatz", "Stauffacher", "Hardplatz", "Escher-Wyss-Platz", "Bahnhof Hardbrücke", "Zürich Hardbrücke", "Albisriederplatz", "Röntgenplatz", "Helvetiaplatz", "Lochergut", "Bahnhof Wiedikon", "Bahnhof Altstetten", "Idaplatz", "Schiffbau"}


def r1(v):
    return round(float(v), 1)


def main():
    nodes, els = sources.osm()
    gx0, gy0, gx1, gy1 = AREA
    play = box(gx0 - 300, gy0 - 300, gx1 + 300, gy1 + 300)
    quart = []
    for ft in json.load(open(RAW))["features"]:
        pr, g = ft["properties"], ft["geometry"]
        rings = [g["coordinates"][0]] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
        for ring in rings:
            a = np.array(ring)
            x, y = sources.geo.to_local(a[:, 0], a[:, 1])
            poly = Polygon(np.column_stack([x, y])).buffer(0)
            if not poly.intersects(play):
                continue
            poly = poly.simplify(2.0)
            if poly.geom_type == 'MultiPolygon':
                poly = max(poly.geoms, key=lambda q: q.area)
            quart.append({"k": int(pr["knr"]), "q": pr["qname"], "ring": [[r1(px), r1(py)] for px, py in poly.exterior.coords]})
    streets, squares, stops = [], [], {}
    for e in els:
        t = e.get("tags", {})
        nm = t.get("name")
        if not nm:
            continue
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes] if e["type"] == "way" else ([nodes[e["id"]]] if e["id"] in nodes else [])
        if not pts:
            continue
        closed = len(pts) > 3 and pts[0] == pts[-1]
        if e["type"] == "way" and t.get("highway") in ROADS and not (closed and t.get("area") == "yes"):
            if t["highway"] in ("footway", "path", "steps", "cycleway") and not t.get("name"):
                continue
            ln = LineString(pts)
            if ln.intersects(play):
                ln = ln.simplify(1.5)
                streets.append({"n": nm, "p": [[r1(a), r1(b)] for a, b in ln.coords]})
        if e["type"] == "way" and closed and (t.get("place") == "square" or (t.get("highway") == "pedestrian" and t.get("area") == "yes")):
            pg = Polygon(pts).buffer(0)
            if pg.geom_type == 'MultiPolygon':
                pg = max(pg.geoms, key=lambda q: q.area)
            if pg.intersects(play) and pg.area > 150:
                squares.append({"n": nm, "ring": [[r1(a), r1(b)] for a, b in pg.simplify(1.5).exterior.coords]})
        if e["type"] == "node" and t.get("place") == "square":
            squares.append({"n": nm, "x": r1(pts[0][0]), "y": r1(pts[0][1]), "r": 30})
        if e["type"] == "node" and (t.get("railway") in ("tram_stop", "station", "halt") or t.get("public_transport") == "stop_position") and nm in HUBS:
            stops.setdefault(nm, []).append(pts[0])
    hubs = []
    for nm, ps in stops.items():
        a = np.array(ps)
        hubs.append({"n": nm, "x": r1(a[:, 0].mean()), "y": r1(a[:, 1].mean()), "r": 70 if nm.startswith(("Zürich HB", "Bahnhof", "Zürich Hard")) else 45})
    if not any(h["n"] == "Zürich HB" for h in hubs):  # HB lies outside the OSM extract nodes list: position from the HB landmark (docs/MAP_SPEC)
        hubs.append({"n": "Zürich HB", "x": 1760.0, "y": -650.0, "r": 130})
    out = {"quartiere": quart, "streets": streets, "squares": squares, "hubs": hubs}
    json.dump(out, open(ROOT / "web" / "public" / "data" / "districts.json", "w"), ensure_ascii=False, separators=(",", ":"))
    print(len(quart), "quartier polys,", len(streets), "street ways,", len(squares), "squares,", [h["n"] for h in hubs])


if __name__ == "__main__":
    main()
