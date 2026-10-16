"""Parks and green areas -> pipeline/overrides/places_detail_parks.json (places_detail schema).
Input: research/parks/parks.json (hand-authored list + per-park options), OSM (ODbL) for real positions of
picnic tables, grills/fire pits, drinking water, fitness stations, shelters, toilets, table tennis; SWISSIMAGE (ortho_ground)
for lawn / gravel / paved classes. Manual additions per park: parks.json -> "ground", "objs", "paved".
Run: .venv/bin/python pipeline/parks_gen.py"""
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon

from config import ROOT
import sources

SPEC = ROOT / "research" / "parks" / "parks.json"
OUT = ROOT / "pipeline" / "overrides" / "places_detail_parks.json"


def main():
    nodes, els = sources.osm()
    ways = {e["id"]: e for e in els if e["type"] == "way" and "nodes" in e}
    poly = lambda i: Polygon([nodes[n] for n in ways[i]["nodes"] if n in nodes]).buffer(0)
    pts = []  # (x, y, tags)
    for e in els:
        t = e.get("tags", {})
        if not t:
            continue
        if e["type"] == "node" and e["id"] in nodes:
            pts.append((*nodes[e["id"]], t))
        elif e["type"] == "way" and "nodes" in e and e["nodes"][0] == e["nodes"][-1] and (t.get("sport") == "table_tennis" or t.get("amenity") in ("shelter", "toilets", "bbq")):
            c = poly(e["id"]).centroid
            pts.append((c.x, c.y, t))
    import stadtzh_pts
    ogd = stadtzh_pts.load()
    places, summary = [], []
    for p in json.load(open(SPEC))["parks"]:
        if p.get("photos_from") and p["id"] in ("baeckeranlage", "josefwiese", "kasernenwiese") and not p.get("regen"):
            continue  # hand-authored in places_detail_<id>.json
        for k, oid in enumerate(p["osm"]):
            shp = poly(oid)
            c = shp.centroid
            cen = [round(c.x, 1), round(c.y, 1)]
            reach = int(max(shp.bounds[2] - shp.bounds[0], shp.bounds[3] - shp.bounds[1]) / 2 + 60)
            zone = shp.buffer(4)
            objs = []
            for x, y, t in pts:
                if not zone.contains(Point(x, y)):
                    continue
                rel = [round(x - cen[0], 2), round(y - cen[1], 2)]
                if t.get("leisure") == "picnic_table":
                    objs.append({"t": "tbench", "p": rel, "h": 0, "a": 2.0, "sit": 1})
                elif t.get("leisure") == "firepit" or t.get("amenity") == "bbq":
                    objs.append({"t": "grill", "p": rel, "h": 0})
                elif t.get("amenity") == "drinking_water":
                    objs.append({"t": "dfount", "p": rel, "h": 0})
                elif t.get("leisure") == "fitness_station":
                    objs.append({"t": "fitness", "p": rel, "h": 0})
                elif t.get("sport") == "table_tennis":
                    objs.append({"t": "pingpong", "p": rel, "h": 0})
                elif t.get("amenity") == "shelter":
                    objs.append({"t": "pavilion", "p": rel, "a": 5, "b": 3.5, "c": 2.6, "col": "#6b6258"})
                elif t.get("amenity") == "toilets":
                    objs.append({"t": "kiosk", "p": rel, "a": 3, "b": 2.4, "c": 2.4, "col": "#cfcac0"})
            for x, y, kind, title in ogd:
                if zone.contains(Point(x, y)):
                    rel = [round(x - cen[0], 2), round(y - cen[1], 2)]
                    if kind == "wc":
                        objs.append({"t": "kiosk", "p": rel, "a": 2.2, "b": 2.2, "c": 2.4, "col": "#9aa19d"})
                    elif title == "Y":
                        objs.append({"t": "ysculpt", "p": rel, "a": 9})
                    elif "Pyramide" in title:
                        objs.append({"t": "pyramid", "p": rel, "a": 4, "b": 3})
                    elif "Brunnen" not in title and "Relief" not in title:
                        objs.append({"t": "sculpt", "p": rel, "a": 1.8, "d": 1, "col": "#6b5a3a"})
            pl = {"id": f"park_{p['id']}" + (f"_{k}" if k else ""), "center": cen, "reach": reach, "src": f"OSM way {oid}; SWISSIMAGE; research/parks/{p['id']}.md",
                  "ground": p.get("ground", []) if k == 0 else [], "objs": objs + (p.get("objs", []) if k == 0 else []),
                  "ortho_ground": {"within": {"osm": oid, "buf": p.get("buf", 1.0)}, "paved": p.get("paved", "asphalt"), "lift": 0.03,
                                   **{q: p[q] for q in ("exg", "warm", "gravel", "grass") if q in p}}}
            for extra in ("lines", "scatter", "convert", "slabs"):
                if extra in p and k == 0:
                    pl[extra] = p[extra]
            places.append(pl)
            summary.append(f"{pl['id']}: {int(shp.area)} m2, {len(objs)} objs, reach {reach}")
    OUT.write_text(json.dumps({"places": places}, ensure_ascii=False, indent=1))
    print("\n".join(summary))


if __name__ == "__main__":
    main()
