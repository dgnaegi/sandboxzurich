import sys
from common import *
lat, lon, r = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
x, y = ll(lat, lon); print("local", round(x), round(y))
min_h = float(sys.argv[4]) if len(sys.argv) > 4 else 0
for b in sorted(near(x, y, r), key=lambda b: -b["fp"].area):
    if b["fp"].area < 150: continue
    bb = b["fp"].bounds
    print(b["id"][:12] if isinstance(b["id"], str) else b["id"], "c=(%.0f,%.0f)" % tuple(b["c"]), "area=%.0f" % b["fp"].area, "z=%.1f..%.1f" % (b["zmin"], b["zmax"]), "bb=(%.0f,%.0f,%.0f,%.0f)" % bb)
