"""List swissBUILDINGS3D ids + OSM house numbers along Langstrasse Nord (axis s from the Unterfuehrung portal). usage: langA_find.py [s0 s1]"""
import sys
sys.path.insert(0, '/Users/danielgnagi/sandboxzurich/pipeline')
from common import *
import sources
from shapely.geometry import Point, LineString, Polygon
AX = LineString([(940, -260), (954, -231), (979, -189), (1043, -74), (1081, -6), (1104, 36), (1125, 80)])
nodes, els = sources.osm()
adr = []
for e in els:
    t = e.get('tags') or {}
    if t.get('addr:housenumber') and e['type'] == 'node' and e['id'] in nodes and AX.distance(Point(*nodes[e['id']])) < 40:
        adr.append((t.get('addr:street', ''), t['addr:housenumber'], Point(*nodes[e['id']])))
s0, s1 = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (0, 400)
seen = set()
for x, y in [tuple(AX.interpolate(s).coords[0]) for s in range(int(s0), int(s1), 12)]:
    for b in near(x, y, 30):
        if b["id"] in seen or b["fp"].area < 80: continue
        seen.add(b["id"]); fp = b["fp"]
        s = AX.project(fp.centroid); side = 'odd/L' if ((AX.interpolate(s + 1).x - AX.interpolate(s).x) * (fp.centroid.y - AX.interpolate(s).y) - (AX.interpolate(s + 1).y - AX.interpolate(s).y) * (fp.centroid.x - AX.interpolate(s).x)) > 0 else 'even/R'
        a = sorted({f"{st} {n}" for st, n, p in adr if fp.buffer(2).contains(p)})
        print(round(s), side, str(b["id"])[:12], "c=(%.0f,%.0f) area=%.0f z=%.1f..%.1f" % (fp.centroid.x, fp.centroid.y, fp.area, b["zmin"], b["zmax"]), a)
