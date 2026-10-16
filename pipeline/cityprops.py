"""Place real objects from Stadt Zürich OGD: trees (by genus), street lights, parked cars on real parking
spaces (with bay markings), benches, fountains, bins, bike stands with bikes."""
import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree

from styles import h32
import trees_dims

# tree classes for the renderer: 0 broadleaf, 1 cherry (pink blossom), 2 white blossom (apple, pear, hawthorn),
# 3 plane, 4 lime/linden, 5 maple, 6 chestnut (white candles), 7 birch, 8 conifer, 9 columnar (hornbeam/poplar)
GENUS = {"Prunus": 1, "Malus": 2, "Pyrus": 2, "Crataegus": 2, "Sorbus": 2, "Platanus": 3, "Tilia": 4, "Acer": 5,
         "Aesculus": 6, "Betula": 7, "Pinus": 8, "Picea": 8, "Abies": 8, "Taxus": 8, "Thuja": 8, "Larix": 8,
         "Cedrus": 8, "Metasequoia": 8, "Carpinus": 9, "Populus": 9, "Quercus": 0, "Fraxinus": 0, "Ulmus": 0,
         "Robinia": 0, "Celtis": 0, "Gleditsia": 0, "Liquidambar": 5, "Ginkgo": 9, "Magnolia": 1, "Cercis": 1}


def _road_dir(S, tree, x, y):
    i = tree.nearest(Point(x, y))
    ln = tree.geometries[i]
    s = ln.project(Point(x, y))
    a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(min(ln.length, s + 1))
    return float(np.arctan2(b.x - a.x, b.y - a.y)), ln, s


_EXTRA_DONE = False


def _osm_extras(C, S):
    """Fidelity S9: fill what the OGD inventories miss, once per build.
    - barrier=bollard ways -> a bollard every 1.8 m (S["bollards"]); the OSM nodes were already used
    - amenity=bicycle_parking (nodes + ways) without an OGD Zweiradparkierung entry within 10 m -> C["bikes"] rows
    - amenity=motorcycle_parking without an OGD entry within 10 m -> C["bikes"] rows tagged 'Motorrad'"""
    global _EXTRA_DONE
    if _EXTRA_DONE:
        return
    _EXTRA_DONE = True
    import sources
    from shapely.geometry import LineString
    nodes, els = sources.osm()
    have = STRtree([Point(r[0], r[1]) for r in C.get("bikes", [])]) if C.get("bikes") else None
    covered = lambda p: have is not None and len(have.query(p.buffer(10))) > 0
    nb = nm = nbo = 0
    for e in els:
        t = e.get("tags", {})
        if e["type"] != "way" and e["type"] != "node":
            continue
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes] if e["type"] == "way" else ([nodes[e["id"]]] if e["id"] in nodes else [])
        if not pts:
            continue
        if t.get("barrier") == "bollard" and e["type"] == "way" and len(pts) >= 2:
            ln = LineString(pts)
            for d in np.arange(0.3, ln.length, 1.8):
                q = ln.interpolate(d)
                S["bollards"].append((q.x, q.y))
                nbo += 1
            continue
        am = t.get("amenity")
        if am not in ("bicycle_parking", "motorcycle_parking"):
            continue
        if t.get("bicycle_parking") in ("shed", "building", "underground", "two-tier", "floor") or t.get("covered") == "yes" and e["type"] == "way":
            continue
        c = Polygon(pts).centroid if len(pts) >= 4 and pts[0] == pts[-1] else LineString(pts).centroid if len(pts) > 1 else Point(pts[0])
        if covered(c):
            continue
        try:
            cap = int(t.get("capacity", "0"))
        except ValueError:
            cap = 0
        if am == "motorcycle_parking":
            C["bikes"].append((c.x, c.y, min(cap or 4, 12), "Motorrad")); nm += 1
        else:
            C["bikes"].append((c.x, c.y, min(cap or 4, 16), "Velo")); nb += 1
    print(f"  cityprops: +{nb} OSM bicycle parkings, +{nm} motorcycle parkings, +{nbo} bollards from lines", flush=True)


def street_parking(C, S, reach=4.5):
    """OGD street parking spaces that really lie on the carriageway side of a street (traffic audit, web/tests/traffic_legal.mjs):
    not on squares / living streets, pedestrian zones (OGD), parks or rail land, and at most `reach` m beyond the kerb of the
    nearest vehicle street (service driveways = courtyard entrances do not count). Cached on S."""
    if "_street_parking" in S:
        return S["_street_parking"]
    import streets_rules
    ban = [g for g in (streets_rules.rules().zones.get("fuss"), S.get("plaza"), S.get("parks"), S.get("av_rail")) if g is not None and not g.is_empty]
    ban = shapely.union_all(ban) if ban else None
    if ban is not None:
        shapely.prepare(ban)
    ws = [w for w in S["ways"] if w["hw"] != "service"]
    tree = STRtree([w["line"] for w in ws])
    out = []
    for r in C.get("parking", []):
        p = Point(r[0], r[1])
        if ban is not None and ban.contains(p):
            continue
        i = tree.nearest(p)
        if ws[i]["line"].distance(p) - ws[i]["w"] / 2 > reach:
            continue
        out.append(r)
    print(f"  cityprops: street parking {len(out)} of {len(C.get('parking', []))} spaces on the carriageway", flush=True)
    S["_street_parking"] = out
    return out


def city_props(C, S, tb, H, curb):
    """Return meta dict parts and extra ground markings (white, blue) for tile box tb."""
    _osm_extras(C, S)
    inside = lambda r: tb.contains(Point(r[0], r[1]))
    z = lambda x, y: round(float(H.at(x, y)), 2)
    roads = S["roads"]
    lines = STRtree([w["line"] for w in S["ways"]])
    out = {"trees": [], "lamps": [], "masts": [], "cars": [], "benches": [], "fountains": [], "bins": [], "bikes": [], "mopeds": []}
    for x, y, genus, crown, cat in filter(inside, C.get("trees", [])):
        _, ln, s_ = _road_dir(S, lines, x, y)
        near = ln.interpolate(s_)
        heading = np.arctan2(near.x - x, -(near.y - y))  # three.js Y rotation turning +z towards the carriageway
        guard = cat == "Strassenbaum" and ln.distance(Point(x, y)) < next((w["w"] for w in S["ways"] if w["line"] is ln), 8) / 2 + 3.2
        out["trees"].append(trees_dims.tree_row(C, x, y, z(x, y), genus, crown, cat, heading, guard))
    for x, y, orient in filter(inside, C.get("lights", [])):
        on_road = roads.contains(Point(x, y))
        heading, ln, _ = _road_dir(S, lines, x, y)
        if on_road:  # suspended over the carriageway (typical for Zürich)
            w = next((w["w"] for w in S["ways"] if w["line"] is ln), 8)
            out["lamps"].append([x, y, z(x, y) - curb, round(heading, 3), round(w + 5, 1)])
        else:
            out["masts"].append([x, y, z(x, y), round(np.radians(orient), 3)])
    white, blue = [], []
    for x, y, art in filter(inside, street_parking(C, S)):
        heading, ln, s = _road_dir(S, lines, x, y)
        d = np.array([np.sin(heading), np.cos(heading)])
        n = np.array([d[1], -d[0]])
        c = np.array([x, y])
        bay = Polygon([c - d * 2.5 - n * 1.0, c + d * 2.5 - n * 1.0, c + d * 2.5 + n * 1.0, c - d * 2.5 + n * 1.0])
        (blue if "Blau" in art else white).append(bay.exterior.buffer(0.06))
        key = h32(f"p{x:.1f}{y:.1f}")
        if key % 100 < (90 if "Blau" in art else 72):  # S5: blue-zone bays are nearly full in the photos
            flip = np.pi if (key >> 8) % 2 else 0
            zc = z(x, y) - (curb if roads.contains(Point(x, y)) else 0)
            out["cars"].append([x, y, zc, round(heading + flip, 3), key % 100000])
    for name, layer in (("benches", "benches"), ("fountains", "fountains"), ("bins", "bins")):
        for r in filter(inside, C.get(layer, [])):
            heading, _, _ = _road_dir(S, lines, r[0], r[1])
            out[name].append([r[0], r[1], z(r[0], r[1]), round(heading, 3), *r[2:3]] if name != "fountains" else [r[0], r[1], z(r[0], r[1]), round(heading, 3)])
    out["racks"] = []
    for x, y, n, art in filter(inside, C.get("bikes", [])):
        heading, _, _ = _road_dir(S, lines, x, y)
        k = h32(f"b{x:.1f}{y:.1f}")
        d = np.array([np.sin(heading), np.cos(heading)])
        if art == "Motorrad":  # motorcycle / scooter bays: parked row, nose to the kerb (fidelity S9)
            n = int(min(max(n, 2), 14))
            for i in range(n):
                if h32(f"m{k}{i}") % 100 < 70:
                    px, py = np.array([x, y]) + d * (i - (n - 1) / 2) * 0.85
                    out["mopeds"].append([round(px, 2), round(py, 2), z(px, py), round(heading + (np.pi if k % 2 else 0), 3), h32(f"mc{k}{i}") % 6])
            continue
        n = int(min(max(n, 2), 40))
        filled = int(round(n * (0.6 + (k % 31) / 100)))
        for i in range(n):  # a row of spaces along the street, bikes perpendicular to it
            px, py = np.array([x, y]) + d * (i - (n - 1) / 2) * 0.7
            if i % 2 == 0:
                out["racks"].append([round(px, 2), round(py, 2), z(px, py), round(heading + np.pi / 2, 3)])
            if h32(f"{k}{i}") % n < filled:
                flip = np.pi if h32(f"f{k}{i}") % 2 else 0
                out["bikes"].append([round(px, 2), round(py, 2), z(px, py), round(heading + np.pi / 2 + flip, 3), h32(f"c{k}{i}") % 14])
    return out, shapely.union_all(white), shapely.union_all(blue)


def parking_bays(C, S, extra=0.15):
    """Union of 2.0 x 5.2 m bays at the real parking spaces, oriented along the nearest street."""
    lines = STRtree([w["line"] for w in S["ways"]])
    bays = []
    for x, y, *_ in street_parking(C, S):
        heading, _, _ = _road_dir(S, lines, x, y)
        d = np.array([np.sin(heading), np.cos(heading)])
        n = np.array([d[1], -d[0]])
        c = np.array([x, y])
        bays.append(Polygon([c - d * 2.6 - n * (1 + extra), c + d * 2.6 - n * (1 + extra), c + d * 2.6 + n * (1 + extra),
                             c - d * 2.6 + n * (1 + extra)]))
    return shapely.union_all(bays)


def car_colliders(cars):
    rings = []
    for x, y, _, h, _ in cars:
        d = np.array([np.sin(h), np.cos(h)])
        n = np.array([d[1], -d[0]])
        c = np.array([x, y])
        rings.append([list(np.round(c + d * sl * 2.15 + n * sw * 0.9, 2)) for sl, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    return rings
