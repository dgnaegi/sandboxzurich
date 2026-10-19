"""Zone 4 (Wiedikon): yellow road markings missing in the built markings, measured from SWISSIMAGE 0.25 m/px (cache data/raw/ortho_025,
see markings_ortho25.py) with the Langstrasse detector (markings_ortho.yellow_mask/comps/good/slim). Only polygons on the OSM carriageway,
inside Zone 4 and play area, and not already covered by the built yellow are kept -> pipeline/overrides/markings_z4.json
(keys add_yellow / add_white / cut / decals, applied by markings_override). Hand-added decals survive a re-run.
usage: .venv/bin/python pipeline/markings_z4_measure.py"""
import json, os, sys
from pathlib import Path
import numpy as np
from PIL import Image
import shapely
from shapely.geometry import box, Polygon
sys.path.insert(0, os.path.dirname(__file__))
import sources, streets, markings_ortho as MO
from config import POLYGON

ROOT = Path(__file__).resolve().parent.parent
D, TILE, PX = ROOT / "data/raw/ortho_025", 250.0, 0.25
OUT = ROOT / "pipeline/overrides/markings_z4.json"
Z = next(z for z in json.load(open(ROOT / "pipeline/overrides/zones.json"))["zones"] if z["id"] == 4)
area = Polygon(Z["polys"][0]).intersection(Polygon(POLYGON))

nodes, els = sources.osm()
S = streets.parse(nodes, els)
roads = S["roads"].buffer(0.3)
white, yellow = streets.markings(S)
built = yellow.buffer(0.35)
found = []
for f in sorted(D.glob("o_*_*.jpg")):
    ix, iy = map(int, f.stem.split("_")[1:])
    bx = box(ix * TILE, iy * TILE, (ix + 1) * TILE, (iy + 1) * TILE)
    if not bx.intersects(area):
        continue
    a = np.asarray(Image.open(f).convert("RGB")).astype(float)
    inner = bx.buffer(-1.0).intersection(area).intersection(roads)
    if inner.is_empty:
        continue
    for g in MO.comps(MO.yellow_mask(a), ix * TILE, (iy + 1) * TILE, PX):
        g = g.intersection(inner)
        for p in shapely.get_parts(g):
            if p.geom_type == "Polygon" and MO.good(p):
                found.append(MO.slim(p))
new = [p for p in found if p.area > 0.2 and p.intersection(built).area < 0.4 * p.area]
print("detected %d, already built %d, new %d (%.0f m2)" % (len(found), len(found) - len(new), len(new), sum(p.area for p in new)))
ring = lambda g: [[round(x, 2), round(y, 2)] for x, y in g.exterior.coords]
old = json.load(open(OUT)) if OUT.exists() else {}
d = {"doc": "Zone 4 Wiedikon: gemessen aus SWISSIMAGE 0.25 m (markings_z4_measure.py). add_yellow = neue Polygone; add_white/cut/decals [x,y,heading,kind] von Hand.",
     "add_yellow": [ring(p) for p in new if p.geom_type == "Polygon"], "add_white": old.get("add_white", []), "cut": old.get("cut", []), "decals": old.get("decals", [])}
OUT.write_text(json.dumps(d))
for p in sorted(new, key=lambda p: -p.area)[:12]:
    c = p.centroid; print("  %.1f m2 at (%d,%d)" % (p.area, c.x, c.y))
