"""OSM street layer: road/plaza/park/sidewalk areas, curbs, tram, markings, POIs."""
import sys
import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely import STRtree
from shapely.ops import substring

from config import AREA
import carriageway

WIDTH = {"primary": 13, "secondary": 11, "tertiary": 9, "residential": 7, "unclassified": 6,
         "service": 3.5, "primary_link": 7, "secondary_link": 7, "tertiary_link": 6}
PLAZA = {"pedestrian": 6, "living_street": 6}
MAIN = {"primary", "secondary", "tertiary"}
SIGN_TAGS = ("shop", "amenity", "craft", "office", "tourism", "leisure")
SIGN_AMENITY = {"restaurant", "cafe", "bar", "pub", "fast_food", "pharmacy", "bank", "ice_cream", "nightclub",
                "cinema", "theatre", "bakery", "doctors", "dentist", "post_office", "community_centre", "arts_centre", "fuel", "car_wash",
                "kindergarten", "childcare", "library", "veterinary"}


OPEN_TUNNELS = {4592588}  # Langstrassen-Unterfuehrung road tunnel (OSM way): driveable, the terrain is cut down to the road


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


def tidy_roads(g, r=4.0, max_fill=45.0):
    """Clean the carriageway union: no zero-width spikes/slivers, junction corners rounded (radius r), tiny holes closed.

    Closing (buffer(+r).buffer(-r)) would also fill wide gaps (islands, sidewalks between parallel streets), so only
    small compact additions (corner fillets, < max_fill m2) are kept."""
    g = shapely.set_precision(g.buffer(0), 0.01)
    g = g.buffer(0.8, quad_segs=6).buffer(-0.8, quad_segs=6)  # hairline gaps / slits between carriageways (< 1.6 m)
    closed = g.buffer(r, quad_segs=8).buffer(-r, quad_segs=8)
    add = [p for p in shapely.get_parts(closed.difference(g)) if 0 < p.area < max_fill]
    if add:
        g = shapely.union_all([g, *add])
    g = g.buffer(-0.3, quad_segs=4).buffer(0.3, quad_segs=4)  # opening: drops spikes thinner than 0.6 m
    g = shapely.set_precision(g.simplify(0.03), 0.01).buffer(0)
    return _drop_pinholes(g)


def _drop_pinholes(g, min_area=0.5):
    """simplify/set_precision leave ~13 zero-area interior rings in the carriageway; curb_faces() turned each into a ring of floating kerb
    walls (research/ground_audit/audit.md). Interior rings < min_area m2 are removed."""
    parts = []
    for p in shapely.get_parts(g):
        if p.geom_type == "Polygon" and any(shapely.Polygon(r).area < min_area for r in p.interiors):
            p = shapely.Polygon(p.exterior, [r for r in p.interiors if shapely.Polygon(r).area >= min_area])
        parts.append(p)
    return shapely.union_all(parts) if len(parts) > 1 else (parts[0] if parts else g)


def parse(nodes, els):
    """Collect way records and point features inside the area (+margin)."""
    area = box(*AREA).buffer(40)
    checks = poi_checks()
    ways, plazas, cycle, tram, parks, trees, crossings, pois, benches = [], [], [], [], [], [], [], [], []
    extras = {"hydrants": [], "bollards": [], "pingpong": [], "signals": [], "platforms": [], "painted_islands": []}
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
                mk = t.get("crossing:markings", "")
                kind = t.get("crossing", "")
                if mk == "no":
                    kind = "unmarked"
                elif mk in ("zebra", "yes", "surface", "dashes", "lines", "ladder") or t.get("crossing_ref") == "zebra":
                    kind = "zebra" if kind in ("", "unmarked", "traffic_signals", "uncontrolled", "marked") else kind
                crossings.append((p, kind, e["id"]))
            elif t.get("highway") == "traffic_signals":
                extras["signals"].append((p, e["id"]))
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
        if e["id"] in OPEN_TUNNELS:
            tunnel = False  # sunken underpass (terrain_cuts.json + landmark lu_unterfuehrung): drawn as an ordinary road on the cut floor
        hw = t.get("highway")
        if hw in WIDTH and not tunnel and t.get("area") != "yes":
            w = _num(t.get("width"), _num(t.get("lanes"), 0) * 3.2 or WIDTH[hw])
            ways.append({"id": e["id"], "line": line, "w": w, "hw": hw, "oneway": t.get("oneway") == "yes", "name": t.get("name", ""),
                         "maxspeed": t.get("maxspeed", ""), "tags": t,
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
        if t.get("area:highway") == "traffic_island" and pts[0] == pts[-1] and len(pts) >= 4:
            extras["painted_islands"].append(Polygon(pts).buffer(0))  # painted Sperrfläche (streets_islands.hatch)
        if t.get("tram") == "yes" and t.get("public_transport") == "platform" and pts[0] != pts[-1]:
            extras["platforms"].append((line, t))  # tram stop platform edge (streets_islands.py)
        if (t.get("leisure") in ("park", "playground", "garden") or t.get("landuse") in ("grass", "village_green")) \
                and pts[0] == pts[-1] and len(pts) >= 4:
            parks.append(Polygon(pts).buffer(0))
    cyc_geo = shapely.union_all(cycle) if cycle else shapely.Polygon()
    cal, av_road = None, None
    if carriageway.enabled():  # carriageway from the official survey (AV), OSM width only as calibrated fallback (carriageway.py)
        import groundcover
        G = groundcover.load((AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260))
        cap, fb, node_half, cal, cstats, car = carriageway.apply(ways, G)
        av_road = car.g
        discs = carriageway.junction_discs(ways, node_half, nodes)
        keep = shapely.union_all([cap, *discs]) if discs else cap
        av = car.g.intersection(shapely.set_precision(keep.buffer(0), 0.01))
        roads = tidy_roads(shapely.union_all([av, fb, cyc_geo, carriageway.axis_gaps([w for w in ways if w["hw"] != "service"], shapely.union_all([av, fb]))]))
        print("carriageway:", cstats, "calibrated widths:", {"/".join(map(str, k)): round(v, 1) for k, v in cal.items() if len(k) == 1})
    else:
        roads = tidy_roads(shapely.union_all([w["line"].buffer(w["w"] / 2, cap_style="round", join_style="round", quad_segs=10)
                                              for w in ways] + cycle))
    plaza = shapely.union_all(plazas).difference(roads)
    return {"ways": ways, "roads": roads, "plaza": plaza, "parks": shapely.union_all(parks).difference(roads).difference(plaza),
            "carriageway_cal": cal or {}, "av_road": av_road, "tram": tram, "trees": trees, "crossings": crossings, "pois": pois, "benches": benches, **extras}


def mline(w):
    """Centre line of the carriageway: the OSM axis shifted by the measured offset (carriageway.py), cached. Markings and
    kerbside props are placed relative to it, so lanes and bike lines follow the real carriageway edges."""
    if "_mline" not in w:
        ln, off = w["line"], w.get("off", 0.0)
        m = ln.offset_curve(off) if abs(off) > 0.2 else ln
        w["_mline"] = m if (m.geom_type == "LineString" and not m.is_empty and abs(m.length - ln.length) < 0.15 * ln.length + 1) else ln
    return w["_mline"]


def dashes(line, dash, gap, start=0.0):
    out, s, L = [], start, line.length
    while s < L:
        seg = substring(line, s, min(s + dash, L))
        if seg.length > 0.05:
            out.append(seg)
        s += dash + gap
    return out


def _tangent(ln, s):
    a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(min(ln.length, s + 1))
    d = np.array([b.x - a.x, b.y - a.y])
    return d / (np.hypot(*d) + 1e-9)


def junction_gaps(S):
    """Per way: [(s0, s1)] where side streets / driveways open into the carriageway (no centre or lane line there).
    Continuations of the same street (parallel at the touch point) are ignored. Cached in w['gaps']."""
    ways = [w for w in S["ways"]]
    if all("gaps" in w and "gaps_main" in w for w in ways):
        return
    tree = STRtree([w["line"] for w in ways])
    for w in ways:
        ln, gaps = w["line"], []
        for j in tree.query(ln, predicate="intersects"):
            o = ways[j]
            if o is w:
                continue
            for p in shapely.get_parts(ln.intersection(o["line"])):
                if p.geom_type != "Point":
                    continue
                s = ln.project(p)
                dot = abs(np.dot(_tangent(ln, s), _tangent(o["line"], o["line"].project(p))))
                if dot > 0.85:
                    continue  # same street continues
                if dot > 0.5 and o["name"] and o["name"] == w["name"] and o["hw"] == w["hw"] and (s < 0.6 or s > ln.length - 0.6) \
                        and min(p.distance(Point(o["line"].coords[0])), p.distance(Point(o["line"].coords[-1]))) < 0.6:
                    continue  # kinked OSM node between two ways of the same street (markings_lines.py): not a junction
                oh = 1.5 if o["hw"] == "service" else o["w"] / 2
                gaps.append((s - oh - 0.8, s + oh + 0.8, o["hw"] == "service"))
        gaps.sort()
        w["gaps_main"] = [(a, b) for a, b, svc in gaps if not svc]  # driveways (service) do not interrupt the centre line
        w["gaps"] = [(a, b) for a, b, svc in gaps]


def _minus(iv, gaps):
    out = []
    for a, b in iv:
        cur = a
        for g0, g1 in sorted(gaps):
            if g1 <= cur or g0 >= b:
                continue
            if g0 > cur:
                out.append((cur, g0))
            cur = max(cur, g1)
        if cur < b:
            out.append((cur, b))
    return [(a, b) for a, b in out if b - a > 0.6]


def _sub(line, a, b, L):
    """substring of an offset curve for a range given along the original centre line (length L)."""
    k = line.length / max(L, 1e-6)
    return substring(line, max(0, a * k), min(line.length, b * k))


def bike_lane_pieces(w):
    """[(side, solid_intervals, broken_intervals)] along the centre line: solid yellow line, broken before side streets."""
    L, out = w["line"].length, []
    for side in ("left", "right"):
        iv = w["lanes"].get(side, [])
        if not iv:
            continue
        solid = _minus(iv, w["gaps"])
        broken = []
        for g0, g1 in w["gaps"]:  # Swiss practice: line turns broken on the approach to a junction
            broken += [(max(g0 - 9.0, a), min(g0, b)) for a, b in iv if g0 > a and g0 - 9.0 < b]
        broken = [(a, b) for a, b in broken if b - a > 1]
        solid = _minus(solid, broken)
        out.append((side, solid, broken))
    return out


def bus_sides(w):
    """Sides ('left'/'right' of the way line) with a marked bus lane (OSM bus:lanes*, busway*)."""
    t, out = w["tags"], set()
    last = lambda v: v.split("|")[-1] if v else ""
    first = lambda v: v.split("|")[0] if v else ""
    if last(t.get("bus:lanes:forward", t.get("bus:lanes", t.get("lanes:bus", "")))) == "designated" or t.get("busway:right") == "lane":
        out.add("right")
    if last(t.get("bus:lanes:backward", "")) == "designated" or t.get("busway:left") == "lane":
        out.add("left")
    if t.get("bus:lanes") and first(t["bus:lanes"]) == "designated" and "|" in t["bus:lanes"] and t.get("oneway") == "yes":
        out.add("left")
    if w["zone"] in ("beg", "fuss") or w["w"] < 6:
        return set()
    return out


def has_lane(w, side, s):
    return any(a - 1 <= s <= b + 1 for a, b in w["lanes"].get(side, []))


def zebra(x, y, d, half, c_n=None):
    """Yellow Fussgängerstreifen centred at (x, y); d = unit travel direction, half = half road width."""
    n = np.array([-d[1], d[0]])
    out = []
    for k in np.arange(-half + 0.25, half, 1.0):  # 0.5 m stripes, 0.5 m gaps, 3.6 m long
        c = np.array([x, y]) + n * k
        out.append(Polygon([c - d * 1.8 - n * 0.25, c + d * 1.8 - n * 0.25, c + d * 1.8 + n * 0.25, c - d * 1.8 + n * 0.25]))
    return out


def signal_arms(S):
    """Signalised approaches (OSM highway=traffic_signals sits on the arm at the stop line):
    [{p, t, half, way, s, sgn, cont, oneway}]  t = unit travel direction towards the junction. Cached in S."""
    if "_arms" in S:
        return S["_arms"]
    by_node = {}
    for w in S["ways"]:
        for n in w["nodes"]:
            by_node.setdefault(n, []).append(w)
    ends = [(w, w["line"].interpolate(0), 1) for w in S["ways"]] + [(w, w["line"].interpolate(w["line"].length), -1) for w in S["ways"]]
    res = []
    for p, nid in S.get("signals", []):
        for w in by_node.get(nid, [])[:1]:
            ln = w["line"]
            if w["hw"] == "service" or w.get("zone") in ("beg", "fuss") or ln.distance(Point(p)) > 2.5:
                continue
            s = ln.project(Point(p))
            L = ln.length
            if min(s, L - s) > 45:
                continue
            to_start = s < L - s
            sgn = -1 if to_start else 1  # travel direction along the way
            if w["oneway"] and sgn < 0:
                continue
            tv = _tangent(ln, s) * sgn
            q = ln.interpolate(0 if to_start else L)
            cont = False
            for o, e, _ in ends:
                if o is w or e.distance(q) > 3:
                    continue
                oo = o["line"]
                out = _tangent(oo, 0 if oo.interpolate(0).distance(q) < 3 else oo.length)
                if oo.interpolate(0).distance(q) >= 3:
                    out = -out
                if np.dot(out, tv) > 0.9:
                    cont = True
            res.append({"p": p, "t": tv, "half": w["w"] / 2, "way": w, "s": s, "sgn": sgn, "cont": cont,
                        "oneway": w["oneway"]})
    S["_arms"] = res
    return res


def markings(S):
    """Return (white, yellow) marking polygons. Lines exist only where the real street has them (official zones,
    signalised speed and bike-lane inventory of Stadt Zürich via streets_rules, OSM tags for lanes)."""
    import streets_rules
    streets_rules.annotate(S)
    import markings_bike
    markings_bike.prune_lanes(S)  # explicit OSM cycleway=no on one-way carriageways beats the official 'BOTH'
    junction_gaps(S)
    import markings_lines as ML
    white, yellow = [], []
    tram = shapely.union_all([t.buffer(2.0) for t in S["tram"]]) if S["tram"] else None
    if tram is not None:
        shapely.prepare(tram)
    zg = {}  # id(way) -> [(s0, s1)]: zebras / stop lines cut centre, lane and bike lines (markings_lines.py)
    # pedestrian crossings (yellow in Switzerland) at mapped crossing nodes, none inside zone 30 / Begegnungszone
    R = streets_rules.rules()
    import crossings  # crossings2: tags + SWISSIMAGE stripe evidence + snapping (pipeline/crossings.py)
    placed = []
    for nid, c in crossings.decide(S, R).items():
        if not c["draw"]:
            continue
        w, d, x, y = c["way"], c["d"], c["x"], c["y"]
        off = w.get("off", 0.0)  # centre the stripes on the carriageway (left normal = (-d1, d0))
        yellow += zebra(x - d[1] * off, y + d[0] * off, d, w["w"] / 2 - 0.3)
        placed.append((x, y))
        if "line" in w:
            sz = w["line"].project(Point(x, y)); zg.setdefault(id(w), []).append((sz - 3.4, sz + 3.4))
    # signalised approaches: stop line (Haltelinie) at the signal, crossing 1 m beyond it if none is mapped there
    for a in signal_arms(S):
        p, t, w = np.array(a["p"]), a["t"], a["way"]
        r = np.array([t[1], -t[0]])
        p = p - r * w.get("off", 0.0)  # signal sits on the OSM axis, the stop line / crossing on the carriageway centre (carriageway.py)
        zc = p + t * 3.1
        if not any(np.hypot(zc[0] - q[0], zc[1] - q[1]) < 9 for q in placed) and a["half"] >= 2.5:
            yellow += zebra(zc[0], zc[1], t, a["half"] - 0.3)
            placed.append(tuple(zc))
            sz = w["line"].project(Point(zc[0], zc[1])); zg.setdefault(id(w), []).append((sz - 3.4, sz + 3.4))
        bike_side = "right" if a["sgn"] > 0 else "left"
        inner = a["half"] - 0.25 - (1.6 if has_lane(w, bike_side, a["s"]) else 0.0)
        lat0 = -a["half"] + 0.25 if a["oneway"] else 0.25
        if inner > lat0 + 1:
            white.append(LineString([p + r * lat0, p + r * inner]).buffer(0.25, cap_style="flat"))
    # --- longitudinal lines (continuous chains, fitted dashes: pipeline/markings_lines.py)
    def centre_ok(w):
        return (w["hw"] in MAIN and not w["oneway"] and w["w"] >= 7 and w["zone"] is None and w["tempo"] != 20
                and int(_num(w["tags"].get("lanes"), 0)) != 1)

    def lane_fn(w):
        n = int(_num(w["tags"].get("lanes"), 0))
        return (n, (w["w"] - 2.5) / n) if n >= 4 and w["hw"] in MAIN and w["zone"] is None and w["zone"] not in ("beg", "fuss") else None
    white += ML.centre_lines(S, centre_ok, zg, tram)
    white += ML.lane_lines(S, lane_fn, zg, tram)
    # painted bike lanes: broken yellow line (SSV 6.09; markings_bike.py), 1 m / 1 m before junctions
    yellow += markings_bike.lines(S, ML, sys.modules[__name__], zg)
    # bus lanes: yellow line 3.2 m from the kerb, broken at side streets
    for w in S["ways"]:
        for side in bus_sides(w):
            ln, L = ML.way_line(S, w), w["line"].length
            off = ln.offset_curve((1 if side == "left" else -1) * (w["w"] / 2 - 3.2))
            if not off.is_empty and off.geom_type == "LineString":
                yellow += [_sub(off, a, b, L).buffer(0.07, cap_style="flat") for a, b in _minus([(0, L)], w["gaps"] + zg.get(id(w), []))]
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
