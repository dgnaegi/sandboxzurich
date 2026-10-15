import sys
from common import *
x, y, r = map(float, sys.argv[1:4])
for t, g in osm_named(x, y, r):
    if "name" in t or "height" in t or "building:levels" in t:
        c = g.centroid
        print("(%.0f,%.0f)" % (c.x, c.y), "a=%.0f" % g.area, {k: v for k, v in t.items() if k in ("name","building","height","building:levels","start_date","architect","roof:shape")})
