"""OSM street layer: road/plaza/park/sidewalk areas, curbs, tram, markings, POIs."""
import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import substring

from config import AREA

WIDTH = {"primary": 13, "secondary": 11, "tertiary": 9, "residential": 7, "unclassified": 6,
         "service": 3.5, "primary_link": 7, "secondary_link": 7, "tertiary_link": 6}
PLAZA = {"pedestrian": 6, "living_street": 6}
MAIN = {"primary", "secondary", "tertiary"}
SIGN_TAGS = ("shop", "amenity", "craft", "office", "tourism", "leisure")
SIGN_AMENITY = {"restaurant", "cafe", "bar", "pub", "fast_food", "pharmacy", "bank", "ice_cream", "nightclub",
                "cinema", "theatre", "bakery", "doctors", "dentist", "post_office", "community_centre", "arts_centre", "fuel", "car_wash",
                "kindergarten", "childcare", "library", "veterinary"}


def _num(v, default):
    try:
        return float(str(v).split()[0].replace(",", "."))
    except (ValueError, IndexError):
        return default


def poi_checks():
    """Web-checked status per OSM id from research/pois_kreis*.csv (last row wins) and pois_testarea_details.csv."""
    import csv
    from config import ROOT
    out = {}
    for f in sorted((ROOT / "research").glob("pois_kreis?.csv")):
        for r in csv.DictReader(open(f)):
            if r.get("osm_id"):
                out[r["osm_id"]] = (r.get("status", ""), r.get("new_name", ""))
    det = ROOT / "research" / "pois_testarea_details.csv"
    if det.exists():
        for r in csv.DictReader(open(det)):
            if "zu" in (r.get("status") or "").lower() or "closed" in (r.get("status") or "").lower():
                out[r.get("osm_id", "")] = ("closed", "")
    return out


def parse(nodes, els):
    """Collect way records and point features inside the area (+margin)."""
    area = box(*AREA).buffer(40)
    checks = poi_checks()
    ways, plazas, cycle, tram, parks, trees, crossings, pois, benches = [], [], [], [], [], [], [], [], []
    extras = {"hydrants": [], "bollards": [], "pingpong": []}
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "node":
            if not t or e["id"] not in nodes:
                continue
            p = nodes[e["id"]]
            if not area.contains(Point(p)):
                continue
            if t.get("natural") == "tree":
                trees.append(p)
            elif t.get("highway") == "crossing" or t.get("footway") == "crossing":
                crossings.append((p, t.get("crossing", ""), e["id"]))
            elif t.get("amenity") == "bench":
                benches.append(p)
            elif t.get("emergency") == "fire_hydrant":
                extras["hydrants"].append(p)
            elif t.get("barrier") == "bollard":
                extras["bollards"].append(p)
            elif t.get("sport") == "table_tennis":
                extras["pingpong"].append(p)
            elif t.get("name") and (any(k in t for k in ("shop", "craft", "office")) or t.get("amenity") in SIGN_AMENITY):
                kind = t.get("shop") or t.get("amenity") or t.get("craft") or t.get("office")
                status, new = checks.get(f"n{e['id']}", ("", ""))
                if status == "closed":
                    continue  # verified closed (research/pois_kreis*.csv): no sign, empty shop
                name = new if status == "renamed" and new else t["name"]
                pois.append({"x": p[0], "y": p[1], "name": name, "kind": kind, "osm": e["id"], "checked": status})
            continue
        if e["type"] != "way" or len(e.get("nodes", [])) < 2:
            continue
        pts = [nodes[n] for n in e["nodes"] if n in nodes]
        if len(pts) < 2:
            continue
        line = LineString(pts)
        if not line.intersects(area):
            continue
        tunnel = t.get("tunnel") in ("yes", "building_passage") or str(t.get("layer", "0")).startswith("-")
        hw = t.get("highway")
        if hw in WIDTH and not tunnel and t.get("area") != "yes":
            w = _num(t.get("width"), _num(t.get("lanes"), 0) * 3.2 or WIDTH[hw])
            ways.append({"line": line, "w": w, "hw": hw, "oneway": t.get("oneway") == "yes", "name": t.get("name", ""),
                         "maxspeed": t.get("maxspeed", ""),
                         "cyc": {s: t.get(f"cycleway:{s}", t.get("cycleway:both", t.get("cycleway", "")))
                                 for s in ("left", "right")}, "nodes": e["nodes"]})
        elif hw in PLAZA and not tunnel:
            plazas.append(line.buffer(PLAZA[hw] / 2, cap_style="flat") if t.get("area") != "yes" or pts[0] != pts[-1]
                          else Polygon(pts).buffer(0))
        elif hw == "cycleway" and not tunnel:
            cycle.append(line.buffer(1.0, cap_style="flat"))
        if t.get("sport") == "table_tennis" and pts[0] == pts[-1]:
            c = Polygon(pts).centroid
            extras["pingpong"].append((c.x, c.y))
        if t.get("railway") == "tram" and not tunnel:
            tram.append(line)
        if (t.get("leisure") in ("park", "playground", "garden") or t.get("landuse") in ("grass", "village_green")) \
                and pts[0] == pts[-1] and len(pts) >= 4:
            parks.append(Polygon(pts).buffer(0))
    roads = shapely.union_all([w["line"].buffer(w["w"] / 2, cap_style="flat", join_style="round") for w in ways]
                              + cycle)
    plaza = shapely.union_all(plazas).difference(roads)
    return {"ways": ways, "roads": roads, "plaza": plaza, "parks": shapely.union_all(parks).difference(roads).difference(plaza),
            "tram": tram, "trees": trees, "crossings": crossings, "pois": pois, "benches": benches, **extras}


def dashes(line, dash, gap, start=0.0):
    out, s, L = [], start, line.length
    while s < L:
        seg = substring(line, s, min(s + dash, L))
        if seg.length > 0.05:
            out.append(seg)
        s += dash + gap
    return out


def markings(S):
    """Return (white, yellow) marking polygons."""
    white, yellow = [], []
    for w in S["ways"]:
        ln = w["line"]
        if w["hw"] in MAIN and not w["oneway"] and w["w"] >= 7:
            white += [d.buffer(0.07, cap_style="flat") for d in dashes(ln, 3, 6, 4)]
        for side, sgn in (("left", 1), ("right", -1)):
            if "lane" in w["cyc"][side]:
                off = ln.offset_curve(sgn * (w["w"] / 2 - 1.5))
                if not off.is_empty and off.geom_type == "LineString":
                    # Swiss Radstreifen: continuous yellow line (here long dashes with short gaps at 6 m)
                    yellow += [d.buffer(0.08, cap_style="flat") for d in dashes(off, 6.0, 0.6)]
    # pedestrian crossings: yellow stripes across the road at crossing nodes
    for (x, y), kind, nid in S["crossings"]:
        if kind in ("traffic_signals", "no", "unmarked"):
            continue
        w = next((w for w in S["ways"] if nid in w["nodes"]), None)
        if w is None:
            continue
        ln = w["line"]
        s = ln.project(Point(x, y))
        a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(min(ln.length, s + 1))
        d = np.array([b.x - a.x, b.y - a.y])
        d /= np.linalg.norm(d) + 1e-9
        n = np.array([-d[1], d[0]])
        half = w["w"] / 2 - 0.3
        for k in np.arange(-half + 0.25, half, 1.0):  # 0.5 m stripes, 0.5 m gaps, 4 m long
            c = np.array([x, y]) + n * k
            yellow.append(Polygon([c - d * 2 - n * 0.25, c + d * 2 - n * 0.25, c + d * 2 + n * 0.25, c - d * 2 + n * 0.25]))
    return shapely.union_all(white), shapely.union_all(yellow)


def curb_faces(roads, tb):
    """Boundary segments of road areas inside tile (oriented so the road is on the left)."""
    segs = []
    for poly in getattr(roads, "geoms", [roads]):
        if poly.geom_type != "Polygon":
            continue
        poly = shapely.geometry.polygon.orient(poly, 1.0)
        for ring in [poly.exterior, *poly.interiors]:
            c = np.asarray(ring.coords)
            for a, b in zip(c[:-1], c[1:]):
                m = (a + b) / 2
                if tb.contains(Point(m)) and np.hypot(*(b - a)) > 0.02:
                    segs.append((a, b))
    return segs
