"""Render the arcade-style map of Kreise 3/4/5/9 from OSM + Kreis borders, and resolve jump points.

Outputs web/public/map/map.json (jump points, Kreise; the drawing itself is pipeline/mapdata.py) (scale, origin, kreise, places). Usage: .venv/bin/python pipeline/build_map.py
"""
import json

import numpy as np
import shapely
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from shapely.geometry import LineString, Point, Polygon

import sources
from config import AREA, POLYGON, ROOT

OUT = ROOT / "web" / "public" / "map"
MPP = 2.0  # metres per pixel
FONT = ROOT / "web" / "public" / "fonts"
COL = {"bg": (34, 40, 44), "land": (52, 60, 64), "bld": (74, 82, 86), "park": (58, 92, 56), "water": (46, 92, 132),
       "rail": (92, 96, 100), "road": (130, 138, 142), "main": (214, 196, 120), "border": (236, 236, 236)}
KREIS_LABEL = {"Kreis 3": "KREIS 3 · WIEDIKON", "Kreis 4": "KREIS 4 · AUSSERSIHL", "Industriequartier": "KREIS 5 · INDUSTRIEQUARTIER",
               "Kreis 9": "KREIS 9 · ALTSTETTEN"}
ROADW = {"motorway": 16, "trunk": 14, "primary": 12, "secondary": 10, "tertiary": 9, "residential": 6, "living_street": 5,
         "unclassified": 5, "pedestrian": 5, "service": 3}
MAIN = {"motorway", "trunk", "primary", "secondary"}


def kreis_anchor(k):
    """Map label point of a Kreis: pole of inaccessibility of its part inside the play area (whole Kreis if that part is tiny)."""
    from shapely.ops import polylabel
    g = k.intersection(Polygon(POLYGON))
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda q: q.area)
    if g.is_empty or g.area < 150_000:
        g = k
    c = polylabel(g, tolerance=5)
    return [round(c.x, 1), round(c.y, 1)]


def kreise():
    d = json.load(open(ROOT / "research" / "kreise_poly_simplified.json"))
    out = {}
    for name, ll in d.items():
        lat, lon = np.array(ll)[:, 0], np.array(ll)[:, 1]
        x, y = sources.geo.to_local(lon, lat)
        out[name] = Polygon(np.column_stack([x, y])).buffer(0)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    K = kreise()
    allk = shapely.union_all(list(K.values()))
    x0, y0, x1, y1 = allk.buffer(250).bounds
    W, H = int((x1 - x0) / MPP), int((y1 - y0) / MPP)
    px = lambda c: [((x - x0) / MPP, (y1 - y) / MPP) for x, y in c]
    img = Image.new("RGB", (W, H), COL["bg"])
    d = ImageDraw.Draw(img)
    for p in K.values():
        d.polygon(px(p.exterior.coords), fill=COL["land"])
    nodes, els = sources.osm()
    named = {}
    layers = {k: [] for k in ("park", "water", "bld", "rail", "road", "main")}
    for e in els:
        t = e.get("tags", {})
        if t.get("name") and e["type"] == "node" and e["id"] in nodes:
            named.setdefault(t["name"], []).append(Point(nodes[e["id"]]))
        if e["type"] != "way":
            continue
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
        if len(pts) < 2:
            continue
        closed = pts[0] == pts[-1] and len(pts) >= 4
        if t.get("name") and closed:
            named.setdefault(t["name"], []).append(Polygon(pts).buffer(0))
        elif t.get("name") and "highway" in t:
            named.setdefault("~" + t["name"], []).append(LineString(pts))
        if closed and (t.get("leisure") in ("park", "garden", "playground", "pitch") or t.get("landuse") in ("grass", "cemetery", "allotments")):
            layers["park"].append(pts)
        elif closed and (t.get("natural") == "water" or t.get("waterway") == "riverbank"):
            layers["water"].append(pts)
        elif closed and "building" in t:
            layers["bld"].append(pts)
        elif t.get("waterway") == "river":
            layers["water"].append(("line", pts, 22))
        elif t.get("railway") == "rail":
            layers["rail"].append(pts)
        elif t.get("highway") in ROADW and t.get("tunnel") != "yes":
            layers["main" if t["highway"] in MAIN else "road"].append((pts, ROADW[t["highway"]]))
    for k in ("park", "water", "bld"):
        for item in layers[k]:
            if isinstance(item, tuple):
                d.line(px(item[1]), fill=COL[k], width=int(item[2] / MPP), joint="curve")
            else:
                d.polygon(px(item), fill=COL[k])
    for pts in layers["rail"]:
        d.line(px(pts), fill=COL["rail"], width=2)
    for k in ("road", "main"):
        for pts, w in layers[k]:
            d.line(px(pts), fill=COL[k], width=max(1, int(w / MPP)), joint="curve")
    # outside the four Kreise: darker
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(px(allk.exterior.coords) if allk.geom_type == "Polygon" else [], fill=255)
    img = Image.composite(img, Image.blend(img, Image.new("RGB", (W, H), COL["bg"]), 0.7), mask)
    d = ImageDraw.Draw(img)
    for p in K.values():
        c = px(p.exterior.coords)
        for a, b in zip(c[:-1], c[1:]):  # dashed border
            n = max(1, int(np.hypot(b[0] - a[0], b[1] - a[1]) / 8))
            for i in range(0, n, 2):
                d.line([(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n),
                        (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)], fill=COL["border"], width=2)
    f = ImageFont.truetype(str(FONT / "Anton-Regular.ttf"), 46)
    for name, p in K.items():
        c = p.representative_point()
        lx, ly = px([(c.x, c.y)])[0]
        text = KREIS_LABEL[name]
        tw = d.textlength(text, font=f)
        d.text((lx - tw / 2 + 3, ly + 3), text, font=f, fill=(0, 0, 0))
        d.text((lx - tw / 2, ly), text, font=f, fill=(255, 255, 255))
    img = img.filter(ImageFilter.SMOOTH)
    # raster base map retired: the game now draws vector data from pipeline/mapdata.py

    places = []
    for p in json.load(open(ROOT / "pipeline" / "overrides" / "places.json"))["places"]:
        g, src = None, "ll"
        if "cross" in p:
            a, b = (shapely.union_all(named.get("~" + s, [])) for s in p["cross"])
            if not a.is_empty and not b.is_empty and a.intersects(b):
                g, src = a.intersection(b).centroid, "osm-cross"
        if g is None and p.get("osm") in named:
            g, src = shapely.union_all(named[p["osm"]]).centroid, "osm"
        if g is None:
            lat, lon = p["ll"]
            g = Point(sources.geo.to_local(lon, lat))
        built = Polygon(POLYGON).contains(g)
        places.append({"name": p["name"], "sub": p["sub"], "x": round(g.x, 1), "y": round(g.y, 1), "yaw": p["yaw"],
                       "built": built, "src": src})
    meta = {"mpp": MPP, "x0": x0, "y1": y1, "w": W, "h": H, "built": list(AREA), "polygon": POLYGON, "places": places,
            "kreise": {KREIS_LABEL[n]: np.round(np.asarray(p.exterior.coords), 1).tolist() for n, p in K.items()},
            "kreis_at": {KREIS_LABEL[n]: kreis_anchor(p) for n, p in K.items()}}
    json.dump(meta, open(OUT / "map.json", "w"), separators=(",", ":"))
    print(f"map meta {W}x{H};",
          ", ".join(f"{p['name']}({p['src']}{',built' if p['built'] else ''})" for p in places))


if __name__ == "__main__":
    main()
