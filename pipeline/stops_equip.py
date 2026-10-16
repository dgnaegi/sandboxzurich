"""Real stop equipment (VBZ infrastructure OGD, Stadt Zuerich, CC0) -> web/public/data/stops_equip.json.
Layers (data/raw/stadtzh_all/geo_vbz_infrastruktur_ogd__haltestellen_*): wartehalle (polygon), sitzgelegenheit, dfi_anzeiger,
ticketautomat (polygon), plakatstelle; haltebalken + infosystem only as coverage points.
Attribute `orientierung` is the azimuth (deg, clockwise from north) of the object's long face axis (verified: benches in a shelter
equal the shelter's long axis, mod 180), so the facing side is derived from the nearest tram/bus line in transit.json.
Output (local metres, x east / y north), `s` = +-1: front side = right-hand normal (cos a, -sin a) of azimuth a, pointing to the track.
 sh [x,y,len,depth,a,s]  bn [x,y,a,s,kind(0 bench,1 lean rail,2 seat),inWH]  df [x,y,a,ceil]  tk [x,y,a,s]  pl [x,y,a,s]  cov [x,y]
Usage: .venv/bin/python pipeline/stops_equip.py"""
import json
import math
from collections import Counter

import numpy as np
from pyproj import Transformer
from shapely.geometry import shape
from shapely.strtree import STRtree
from shapely.geometry import LineString

from config import AREA, ROOT

RAW = ROOT / "data" / "raw" / "stadtzh_all"
OUT = ROOT / "web" / "public" / "data" / "stops_equip.json"
_t = Transformer.from_crs(4326, 2056, always_xy=True)
MARGIN = 60.0


def layer(n):
    return json.load(open(next(RAW.glob(f"*haltestellen_{n}.geojson"))))["features"]


def loc(coords):
    a = np.array(coords, float)
    x, y = _t.transform(a[:, 0], a[:, 1])
    return np.column_stack([x - 2681400.0, y - 1248700.0])


def geom_local(f):
    g = f["geometry"]
    if g["type"] == "MultiPoint":
        return ("pt", loc(g["coordinates"])[0])
    if g["type"] == "Point":
        return ("pt", loc([g["coordinates"]])[0])
    if g["type"] == "MultiLineString":
        polys = [loc(l) for l in g["coordinates"] if len(l) >= 3]
    elif g["type"] == "LineString":
        polys = [loc(g["coordinates"])] if len(g["coordinates"]) >= 3 else []
    else:
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        polys = [loc(p[0]) for p in polys if len(p[0]) >= 4]
    if not polys:
        return None
    from shapely.geometry import Polygon
    best = max((Polygon(p) for p in polys), key=lambda q: q.area)
    return ("poly", best)


def rect(poly):
    r = poly.minimum_rotated_rectangle
    if r.geom_type != "Polygon":
        return None
    c = list(r.exterior.coords)
    a, b = math.dist(c[0], c[1]), math.dist(c[1], c[2])
    e = (c[0], c[1]) if a >= b else (c[1], c[2])
    ax = math.degrees(math.atan2(e[1][0] - e[0][0], e[1][1] - e[0][1])) % 180
    return max(a, b), min(a, b), ax, r.centroid


def main():
    lines = [LineString(l["pts"]) for l in json.load(open(ROOT / "web/public/data/transit.json"))["lines"] if len(l["pts"]) > 1]
    tree = STRtree(lines)
    x0, y0, x1, y1 = AREA
    from shapely.geometry import Point as _P, Polygon as _Pg
    from config import POLYGON
    play = _Pg(POLYGON).buffer(30)   # only inside the playable polygon (+30 m): no floating objects over unloaded terrain
    inside = lambda x, y: play.contains(_P(x, y))

    def side(x, y, az):
        from shapely.geometry import Point
        p = Point(x, y)
        idx = tree.query(p.buffer(30))
        if not len(idx):
            return 1
        ln = min((lines[i] for i in idx), key=lambda l: l.distance(p))
        q = ln.interpolate(ln.project(p))
        a = math.radians(az)
        d = (q.x - x) * math.cos(a) - (q.y - y) * math.sin(a)
        return 1 if d >= 0 else -1

    out = {"src": "Stadt Zuerich / VBZ Infrastruktur OGD, CC0", "sh": [], "bn": [], "df": [], "tk": [], "pl": [], "cov": []}
    shelters = []
    for f in layer("wartehalle"):
        g = geom_local(f)
        r = g and g[0] == "poly" and rect(g[1])
        if not r or not inside(r[3].x, r[3].y) or r[0] < 2.5:
            continue
        L, W, az, c = r
        shelters.append((g[1], az))
        out["sh"].append([round(c.x, 2), round(c.y, 2), round(L, 1), round(min(max(W, 1.4), 2.2), 1), round(az), side(c.x, c.y, az)])
    # the layer holds overlapping footprints for one shelter (roof + wall): merge centres < 2 m apart, keep the deeper one
    merged = []
    for e in sorted(out["sh"], key=lambda r: -r[3]):
        if not any(math.hypot(e[0] - m[0], e[1] - m[1]) < 2.0 for m in merged):
            merged.append(e)
    out["sh"] = merged
    shelters = [s for s in shelters if any(math.hypot(s[0].centroid.x - m[0], s[0].centroid.y - m[1]) < 2.5 for m in merged)]
    stree = STRtree([s[0] for s in shelters])

    def in_wh(x, y):
        from shapely.geometry import Point
        p = Point(x, y)
        return any(shelters[i][0].buffer(0.8).contains(p) for i in stree.query(p.buffer(1)))

    def pt_az(f, g):
        o = f["properties"].get("orientierung")
        try:
            return float(o) % 180
        except (TypeError, ValueError):
            r = g[0] == "poly" and rect(g[1])
            return r[2] if r else 0.0

    for f in layer("sitzgelegenheit"):
        g = geom_local(f)
        if not g or g[0] != "pt" or not inside(*g[1]):
            continue
        t = str(f["properties"].get("typ") or "")
        kind = 1 if "Stehhilfe" in t else 2 if t == "Sitz" else 0
        x, y = g[1]
        az = pt_az(f, g)
        out["bn"].append([round(x, 2), round(y, 2), round(az), side(x, y, az), kind, int(in_wh(x, y))])
    for f in layer("dfi_anzeiger"):
        g = geom_local(f)
        if g and g[0] == "pt" and inside(*g[1]):
            out["df"].append([round(g[1][0], 2), round(g[1][1], 2), round(pt_az(f, g)), int("Decke" in str(f["properties"].get("typ")))])
    for key, n in (("tk", "ticketautomat"), ("pl", "plakatstelle")):
        for f in layer(n):
            g = geom_local(f)
            if not g:
                continue
            if g[0] == "poly":
                r = rect(g[1])
                if not r:
                    continue
                x, y, az = r[3].x, r[3].y, r[2]
            else:
                x, y = g[1]; az = pt_az(f, g)
            if inside(x, y):
                out[key].append([round(x, 2), round(y, 2), round(az), side(x, y, az)])
    seen = set()
    for n in ("haltebalken", "infosystem"):
        for f in layer(n):
            g = geom_local(f)
            if g and g[0] == "pt" and inside(*g[1]):
                k = (round(g[1][0] / 8), round(g[1][1] / 8))
                if k not in seen:
                    seen.add(k); out["cov"].append([round(g[1][0]), round(g[1][1])])
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print({k: len(v) for k, v in out.items() if isinstance(v, list)}, f"{OUT.stat().st_size // 1024} KB",
          "bench kinds", Counter(b[4] for b in out["bn"]), "in WH", sum(b[5] for b in out["bn"]))


if __name__ == "__main__":
    main()
