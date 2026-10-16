"""Stadt Zuerich OGD extras -> web/public/data/ogd_extras.json (CC0, see docs/DATA_SOURCES.md).
 - blaue_tafeln_p: historical info plaques; snapped to the nearest real facade (swissBUILDINGS3D footprint), outward normal.
 - velopumpstationen_p: public bike pumps.
Usage: .venv/bin/python pipeline/ogd_extras.py   -> {tafeln:[{x,y,nx,ny,t,a,txt,y0}], pumps:[{x,y}]}"""
import json

import numpy as np
from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import nearest_points, unary_union
from shapely.geometry import Polygon
from shapely.strtree import STRtree

import sources
from config import AREA, ROOT

RAW = ROOT / "data" / "raw" / "stadtzh_all"
OUT = ROOT / "web" / "public" / "data" / "ogd_extras.json"
_lv = Transformer.from_crs(2056, 4326, always_xy=True)
O = (2681400.0, 1248700.0)
MARGIN = 60.0


def load(name):
    return json.load(open(next(RAW.glob(f"*{name}*.geojson"))))["features"]


def footprints():
    polys = []
    for b in sources.buildings(margin=80):
        parts = []
        for _, p in b["polys"]:
            if len(p) >= 3:
                g = Polygon(p[:, :2])
                if g.is_valid and g.area > 0.5:
                    parts.append(g)
        if parts:
            u = unary_union(parts).buffer(0.2).buffer(-0.2)
            polys.append(u)
    return polys


def main():
    x0, y0, x1, y1 = AREA
    from shapely.geometry import Point as _P, Polygon as _Pg
    from config import POLYGON
    play = _Pg(POLYGON).buffer(30)   # only inside the playable polygon (+30 m): no floating objects over unloaded terrain
    inside = lambda x, y: play.contains(_P(x, y))
    blds = footprints()
    tree = STRtree(blds)
    tafeln, skipped = [], 0
    for f in load("blaue_tafeln"):
        p = f["properties"]
        if str(p.get("montiert", "")).lower() != "ja" or not p.get("text_tafel"):
            continue
        x, y = float(p["point_x"]) - O[0], float(p["point_y"]) - O[1]
        if not inside(x, y):
            continue
        pt = Point(x, y)
        cand = tree.query(pt.buffer(25))
        best = None
        for i in cand:
            d = blds[i].distance(pt)
            if best is None or d < best[0]:
                best = (d, i)
        if best is None:
            skipped += 1
            continue
        g = blds[best[1]]
        if g.geom_type == "MultiPolygon":
            g = min(g.geoms, key=lambda q: q.distance(pt))
        ring = g.exterior
        q = ring.interpolate(ring.project(pt))
        # outward normal: sample a point 0.6 m off the wall both ways, the one outside the footprint wins
        s = ring.project(q)
        a = ring.interpolate(max(0, s - 0.5)); b = ring.interpolate(min(ring.length, s + 0.5))
        tx, ty = b.x - a.x, b.y - a.y
        L = np.hypot(tx, ty) or 1.0
        nx, ny = ty / L, -tx / L
        if g.contains(Point(q.x + nx * 0.6, q.y + ny * 0.6)):
            nx, ny = -nx, -ny
        tafeln.append({"x": round(q.x, 2), "y": round(q.y, 2), "nx": round(nx, 3), "ny": round(ny, 3),
                       "t": (p.get("titel_tafel") or "").strip(), "a": (p.get("adressen_tafel") or "").strip(),
                       "yr": (p.get("ds_tafel") or "").strip(), "txt": " ".join(p["text_tafel"].split()), "off": round(best[0], 1)})
    pumps = []
    for f in load("velopumpstationen"):
        lon, lat = f["geometry"]["coordinates"]
        x, y = Transformer.from_crs(4326, 2056, always_xy=True).transform(lon, lat)
        x -= O[0]; y -= O[1]
        if inside(x, y):
            pumps.append({"x": round(x, 2), "y": round(y, 2), "n": f["properties"].get("bezeichnung") or ""})
    OUT.write_text(json.dumps({"src": "Stadt Zuerich OGD (CC0): blaue_tafeln_p, velopumpstationen_p", "tafeln": tafeln, "pumps": pumps},
                              ensure_ascii=False, separators=(",", ":")))
    offs = sorted(t["off"] for t in tafeln)
    print(f"tafeln {len(tafeln)} (skipped no building {skipped}); snap dist median {offs[len(offs)//2]} m, max {offs[-1]} m; pumps {len(pumps)}; {OUT.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
