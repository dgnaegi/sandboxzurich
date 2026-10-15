"""Place real objects from Stadt Zürich OGD: trees (by genus), street lights, parked cars on real parking
spaces (with bay markings), benches, fountains, bins, bike stands with bikes."""
import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree

from styles import h32

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


def city_props(C, S, tb, H, curb):
    """Return meta dict parts and extra ground markings (white, blue) for tile box tb."""
    inside = lambda r: tb.contains(Point(r[0], r[1]))
    z = lambda x, y: round(float(H.at(x, y)), 2)
    roads = S["roads"]
    lines = STRtree([w["line"] for w in S["ways"]])
    out = {"trees": [], "lamps": [], "masts": [], "cars": [], "benches": [], "fountains": [], "bins": [], "bikes": []}
    for x, y, genus, crown, cat in filter(inside, C.get("trees", [])):
        cls = GENUS.get(genus, 0)
        cr = min(max(crown, 2.0), 22.0)
        out["trees"].append([x, y, z(x, y), cls, round(cr, 1), round(min(cr * 1.25 + 3, 30), 1)])
    for x, y, orient in filter(inside, C.get("lights", [])):
        on_road = roads.contains(Point(x, y))
        heading, ln, _ = _road_dir(S, lines, x, y)
        if on_road:  # suspended over the carriageway (typical for Zürich)
            w = next((w["w"] for w in S["ways"] if w["line"] is ln), 8)
            out["lamps"].append([x, y, z(x, y) - curb, round(heading, 3), round(w + 5, 1)])
        else:
            out["masts"].append([x, y, z(x, y), round(np.radians(orient), 3)])
    white, blue = [], []
    for x, y, art in filter(inside, C.get("parking", [])):
        heading, ln, s = _road_dir(S, lines, x, y)
        d = np.array([np.sin(heading), np.cos(heading)])
        n = np.array([d[1], -d[0]])
        c = np.array([x, y])
        bay = Polygon([c - d * 2.5 - n * 1.0, c + d * 2.5 - n * 1.0, c + d * 2.5 + n * 1.0, c - d * 2.5 + n * 1.0])
        (blue if "Blau" in art else white).append(bay.exterior.buffer(0.06))
        key = h32(f"p{x:.1f}{y:.1f}")
        if key % 100 < 72:
            flip = np.pi if (key >> 8) % 2 else 0
            zc = z(x, y) - (curb if roads.contains(Point(x, y)) else 0)
            out["cars"].append([x, y, zc, round(heading + flip, 3), key % 100000])
    for name, layer in (("benches", "benches"), ("fountains", "fountains"), ("bins", "bins")):
        for r in filter(inside, C.get(layer, [])):
            heading, _, _ = _road_dir(S, lines, r[0], r[1])
            out[name].append([r[0], r[1], z(r[0], r[1]), round(heading, 3)])
    out["racks"] = []
    for x, y, n, art in filter(inside, C.get("bikes", [])):
        if "Motor" in art:
            continue
        heading, _, _ = _road_dir(S, lines, x, y)
        k = h32(f"b{x:.1f}{y:.1f}")
        d = np.array([np.sin(heading), np.cos(heading)])
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
    for x, y, *_ in C.get("parking", []):
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
