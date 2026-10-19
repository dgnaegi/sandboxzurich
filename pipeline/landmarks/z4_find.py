"""Zone 4: swissBUILDINGS3D ids for facade-note addresses (footprint containing/nearest to the GWR entrance point).
usage: z4_find.py "Bertastrasse 1" "Zurlindenstrasse 21" ...   (xy from research/zones/zone4_facades.json, GWR points from data/build/gwr_kreise.json)"""
import sys, json
from common import *
from shapely.geometry import Point
G = {f"{r['street']} {r['nr']}": r for r in json.load(open(ROOT / "data/build/gwr_kreise.json"))}
for a in sys.argv[1:]:
    r = G[a]; p = Point(r["x"], r["y"])
    c = sorted(near(r["x"], r["y"], 40), key=lambda b: b["fp"].distance(p))[:2]
    for b in c:
        print(a, str(b["id"])[:12], "d=%.1f area=%.0f z=%.1f..%.1f" % (b["fp"].distance(p), b["fp"].area, b["zmin"], b["zmax"]), "c=(%.0f,%.0f)" % (b["fp"].centroid.x, b["fp"].centroid.y))
