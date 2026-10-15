"""Print footprint outline info for swissBUILDINGS3D ids near a point: k4w3_fp.py x y r [minarea]"""
import sys, math
from common import *
from lm import rect_of
x, y, r = map(float, sys.argv[1:4]); ma = float(sys.argv[4]) if len(sys.argv) > 4 else 100
for b in sorted(near(x, y, r), key=lambda b: -b["fp"].area):
    if b["fp"].area < ma: continue
    P = outline(b["fp"], 0.5); (cx, cy), ux, uy, L, W = rect_of(P)
    print(b["id"], "c=(%.0f,%.0f)" % (P.centroid.x, P.centroid.y), "area=%.0f" % P.area, "z=%.1f..%.1f" % (b["zmin"], b["zmax"]),
          "rect L=%.1f W=%.1f ang=%.0f" % (L, W, math.degrees(math.atan2(uy, ux))), "nv=%d" % (len(P.exterior.coords) - 1))
