"""Vector map data for the city map and the radar -> web/public/data/map/vec.json (+ meta in web/public/map/map.json).

Source: OSM (data/raw/osm/kreise.json, (c) OpenStreetMap contributors, ODbL), Kreis borders (Stadt Zuerich OGD),
landmarks.json of the game. Coordinates are local metres, quantised to 0.5 m and delta-encoded as flat int arrays.
Usage: .venv/bin/python pipeline/mapdata.py
"""
import json
from collections import defaultdict

import shapely
from shapely.geometry import LineString, MultiLineString, Point, Polygon
from shapely.ops import linemerge, polygonize
from shapely.prepared import prep

import sources
from build_map import kreise
from config import ROOT
from names import square

OUT = ROOT / "web" / "public" / "data" / "map"
Q = 2  # units per metre

ROAD = {"motorway": 0, "motorway_link": 0, "trunk": 0, "trunk_link": 0, "primary": 1, "primary_link": 1,
        "secondary": 2, "secondary_link": 2, "tertiary": 3, "tertiary_link": 3, "residential": 4, "living_street": 4,
        "unclassified": 4, "service": 5, "track": 5, "pedestrian": 6, "footway": 7, "path": 7, "cycleway": 7, "steps": 7}
GREEN = {("leisure", "park"): "g", ("leisure", "garden"): "g", ("landuse", "grass"): "g", ("landuse", "meadow"): "g",
         ("landuse", "recreation_ground"): "g", ("landuse", "flowerbed"): "g", ("leisure", "playground"): "p",
         ("leisure", "pitch"): "s", ("leisure", "track"): "s", ("leisure", "sports_centre"): "s",
         ("landuse", "cemetery"): "c", ("landuse", "allotments"): "a", ("landuse", "forest"): "w", ("natural", "wood"): "w",
         ("natural", "scrub"): "w", ("natural", "grassland"): "g", ("landuse", "railway"): "r"}
POI_AMENITY = {"place_of_worship": "church", "hospital": "hospital", "theatre": "culture", "arts_centre": "culture",
               "cinema": "culture", "library": "culture", "townhall": "civic", "university": "school", "college": "school",
               "school": "school", "community_centre": "civic", "police": "civic"}


def enc(pts, ox, oy):
    """Delta-encode a polyline into a flat int list (first point relative to origin)."""
    out, px, py = [], 0, 0
    for x, y in pts:
        ix, iy = round((x - ox) * Q), round((y - oy) * Q)
        out += [ix - px, iy - py]
        px, py = ix, iy
    return out


def landmark_stars():
    """Landmarks worth a star on the map (rules: overrides/map_pois.json; schools get a school dot); stars closer than merge_m keep the first one."""
    import re
    cfg = json.load(open(ROOT / "pipeline" / "overrides" / "map_pois.json"))
    rx = re.compile("|".join(cfg["hide_re"]))
    out = []
    for lm in json.load(open(ROOT / "web" / "public" / "data" / "landmarks.json"))["landmarks"]:
        if lm["name"] in cfg["hide"]:
            continue
        nm = lm["name"].split(" + ")[0].replace("-Kamin Josefstrasse", "").replace("Westpark (Galaxus)", "Digitec Galaxus")
        nm = re.sub(r"\s*\((Lighthouse|Bogen)\)", "", nm)
        if rx.search(nm) or any(abs(o[1] - lm["x"]) + abs(o[2] - lm["y"]) < cfg["merge_m"] for o in out):
            continue
        nm = cfg["rename"].get(nm, nm)
        out.append([nm, round(lm["x"]), round(lm["y"]), "school" if re.match(cfg["school_re"], lm["name"]) else "lm"])
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    K = kreise()
    allk = shapely.union_all(list(K.values()))
    clip = prep(allk.buffer(250))
    ox, oy = allk.buffer(250).bounds[0], allk.buffer(250).bounds[1]
    nodes, els = sources.osm()
    ways = {e["id"]: [nodes[n] for n in e["nodes"] if n in nodes] for e in els if e["type"] == "way"}
    wtags = {e["id"]: e.get("tags", {}) for e in els if e["type"] == "way"}
    inbox = lambda g: clip.intersects(g)

    areas = defaultdict(list)  # kind -> list of polygons (shapely)
    roads, rails, names, lab_src = [], [], [], defaultdict(list)
    tram_refs = defaultdict(set)
    for e in els:
        if e["type"] == "relation" and e.get("tags", {}).get("route") == "tram":
            for m in e["members"]:
                if m["type"] == "way":
                    tram_refs[m["ref"]].add(e["tags"].get("ref", ""))

    def add_area(kind, poly, name=None):
        if poly.is_empty or not inbox(poly):
            return
        for g in (poly.geoms if poly.geom_type == "MultiPolygon" else [poly]):
            if g.geom_type == "Polygon" and g.area > 4:
                areas[kind].append((g, name))

    for wid, t in wtags.items():
        pts = ways[wid]
        if len(pts) < 2:
            continue
        closed = pts[0] == pts[-1] and len(pts) >= 4
        kind = None
        if closed:
            if "building" in t:
                kind = "b"
            elif t.get("natural") == "water" or t.get("waterway") == "riverbank" or t.get("landuse") == "basin":
                kind = "water"
            else:
                for (k, v), c in GREEN.items():
                    if t.get(k) == v:
                        kind = c
                        break
            if kind == "b" and False:
                pass
            if kind:
                p = Polygon(pts).buffer(0)
                add_area(kind, p, t.get("name"))
                if t.get("highway") == "pedestrian":
                    pass
            elif t.get("highway") == "pedestrian" and t.get("area") == "yes":
                add_area("sq", Polygon(pts).buffer(0), t.get("name"))
            elif t.get("place") == "square":
                add_area("sq", Polygon(pts).buffer(0), t.get("name"))
        hw = t.get("highway")
        if hw in ROAD and not (closed and t.get("area") == "yes"):
            if hw == "footway" and t.get("footway") in ("sidewalk", "crossing", "traffic_island"):
                continue
            if hw == "service" and t.get("service") in ("driveway", "parking_aisle") and not t.get("name"):
                cls = 5
            if hw == "footway" and not t.get("name"):
                continue
            if t.get("access") in ("private", "no") and ROAD[hw] == 5:
                continue
            ls = LineString(pts)
            if inbox(ls):
                fl = (1 if t.get("tunnel") in ("yes", "building_passage", "covered") else 0) | (2 if t.get("bridge") in ("yes", "viaduct") else 0)
                nm = t.get("name", "")
                roads.append((ROAD[hw], fl, pts, nm))
                if nm and ROAD[hw] <= 6:
                    lab_src[(nm, ROAD[hw] if ROAD[hw] < 5 else 4)].append(ls)
        elif t.get("railway") in ("rail", "tram") and t.get("service") not in ("crossover",):
            ls = LineString(pts)
            if inbox(ls) and not (t.get("railway") == "rail" and t.get("usage") == "industrial" and False):
                fl = 1 if t.get("tunnel") == "yes" else 0
                rails.append((0 if t["railway"] == "rail" else 1, fl | (4 if t.get("service") else 0), pts, sorted(r for r in tram_refs.get(wid, ()) if r)))
        elif t.get("waterway") in ("river", "canal", "stream"):
            if t.get("tunnel") in ("yes", "culvert") or t.get("waterway") == "stream" and not t.get("name") and False:
                continue
            ls = LineString(pts)
            if inbox(ls):
                roads.append((10 + {"river": 0, "canal": 1, "stream": 2}[t["waterway"]], 0, pts, t.get("name", "")))
                if t.get("name") and t["waterway"] != "stream":
                    lab_src[(t["name"], 10)].append(ls)

    # multipolygon relations (buildings, water, parks)
    for e in els:
        if e["type"] != "relation":
            continue
        t = e.get("tags", {})
        if t.get("type") != "multipolygon":
            continue
        kind = "b" if "building" in t else ("water" if t.get("natural") == "water" else None)
        if not kind:
            for (k, v), c in GREEN.items():
                if t.get(k) == v:
                    kind = c
        if not kind:
            continue
        outer = [LineString(ways[m["ref"]]) for m in e["members"] if m["type"] == "way" and m["role"] == "outer" and len(ways.get(m["ref"], [])) > 1]
        inner = [LineString(ways[m["ref"]]) for m in e["members"] if m["type"] == "way" and m["role"] == "inner" and len(ways.get(m["ref"], [])) > 1]
        if not outer:
            continue
        try:
            os_ = list(polygonize(linemerge(outer))) if len(outer) > 1 else [Polygon(outer[0].coords).buffer(0)]
            ins = list(polygonize(linemerge(inner))) if len(inner) > 1 else ([Polygon(inner[0].coords).buffer(0)] if inner else [])
            g = shapely.union_all(os_)
            if ins:
                g = g.difference(shapely.union_all(ins))
            add_area(kind, g, t.get("name"))
        except Exception:
            continue

    # points of interest / labels
    stops, pois, places = {}, [], []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "node" and e["id"] in nodes:
            x, y = nodes[e["id"]]
            if not clip.contains(Point(x, y)):
                continue
            nm = t.get("name")
            if t.get("railway") == "tram_stop" and nm:
                stops.setdefault(nm, []).append((x, y, "t"))
            elif t.get("railway") in ("station", "halt") and nm:
                stops.setdefault(nm, []).append((x, y, "s"))
            elif t.get("place") in ("suburb", "quarter", "neighbourhood") and nm:
                places.append([nm, round(x), round(y), {"suburb": "s", "quarter": "u", "neighbourhood": "n"}[t["place"]]])
            elif t.get("place") == "square" and nm:
                places.append([square(nm), round(x), round(y), "q"])
            elif nm and (t.get("amenity") in POI_AMENITY or t.get("tourism") == "museum"):
                pois.append([nm, round(x), round(y), POI_AMENITY.get(t.get("amenity"), "culture")])
    stop_list = []
    for nm, v in stops.items():
        if nm.startswith("Zürich, "):
            nm = nm[8:]
        stop_list.append([nm, round(sum(a[0] for a in v) / len(v)), round(sum(a[1] for a in v) / len(v)), v[0][2]])
    # named areas -> labels (squares, parks, notable buildings)
    seen = set()
    for kind, items in areas.items():
        for g, nm in items:
            if not nm or (nm, kind) in seen:
                continue
            c = g.representative_point()
            if kind == "sq":
                places.append([square(nm), round(c.x), round(c.y), "q"]); seen.add((nm, kind))
            elif kind in ("g", "w", "c", "s") and g.area > 2500:
                places.append([nm, round(c.x), round(c.y), "k"]); seen.add((nm, kind))
            elif kind == "b" and g.area > 1800:
                pois.append([nm, round(c.x), round(c.y), "bld"]); seen.add((nm, kind))
    pois += landmark_stars()
    # dedupe by name
    dd = {}
    for p in places:
        dd.setdefault((p[0], p[3]), p)
    places = list(dd.values())
    pd = {}
    for p in pois:
        pd.setdefault(p[0], p)
    pois = list(pd.values())

    # merged street label lines
    labels = []
    for (nm, cls), lines in lab_src.items():
        m = linemerge(MultiLineString(lines)) if len(lines) > 1 else lines[0]
        for g in (m.geoms if m.geom_type == "MultiLineString" else [m]):
            g = g.simplify(1.5)
            if g.length > 25:
                labels.append([nm, cls, enc(g.coords, ox, oy)])

    out = {"ox": ox, "oy": oy, "q": Q,
           "areas": {}, "roads": defaultdict(list), "rails": [], "labels": labels, "stops": stop_list, "places": places, "pois": pois}
    for kind, items in areas.items():
        arr = []
        for g, _ in items:
            g = g.simplify(0.3 if kind == "b" else 0.5)
            if g.is_empty or g.geom_type != "Polygon":
                continue
            rings = [enc(g.exterior.coords[:-1], ox, oy)] + [enc(r.coords[:-1], ox, oy) for r in g.interiors]
            arr.append(rings if len(rings) > 1 else rings[0])
        out["areas"][kind] = arr
    for cls, fl, pts, nm in roads:
        out["roads"][str(cls)].append([fl, enc(pts, ox, oy)])
    for cls, fl, pts, refs in rails:
        out["rails"].append([cls, fl, enc(pts, ox, oy), ",".join(refs)])
    out["roads"] = dict(out["roads"])
    json.dump(out, open(OUT / "vec.json", "w"), separators=(",", ":"), ensure_ascii=False)
    n = {k: len(v) for k, v in out["areas"].items()}
    print("areas", n, "roads", {k: len(v) for k, v in out["roads"].items()}, "rails", len(out["rails"]),
          "labels", len(labels), "stops", len(stop_list), "places", len(places), "pois", len(pois),
          "size KB", (OUT / "vec.json").stat().st_size // 1024)


if __name__ == "__main__":
    main()
