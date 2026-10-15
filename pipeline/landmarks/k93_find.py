"""Helper: list swissBUILDINGS3D objects near a local point. Usage: k93_find.py x y [radius]"""
import sys, glob, pickle, json
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
ROOT = __file__.rsplit("/pipeline/", 1)[0]


def near(x, y, r=40):
    out = []
    for f in glob.glob(ROOT + "/data/build/bld/*.pkl"):
        for o in pickle.load(open(f, "rb")):
            g = [q for k, q in o["polys"] if k == 0]
            if not g: continue
            allp = np.vstack(g)
            if allp[:, 0].min() > x + r or allp[:, 0].max() < x - r or allp[:, 1].min() > y + r or allp[:, 1].max() < y - r: continue
            out.append(o)
    return out


def footprint(o):
    gs = [Polygon(q[:, :2]).buffer(0) for k, q in o["polys"] if k == 0 and len(q) >= 3]
    return unary_union(gs).buffer(0.05).buffer(-0.05)


if __name__ == "__main__":
    x, y = float(sys.argv[1]), float(sys.argv[2]); r = float(sys.argv[3]) if len(sys.argv) > 3 else 30
    for o in near(x, y, r):
        fp = footprint(o); roof = np.vstack([q for k, q in o["polys"] if k == 2]) if any(k == 2 for k, _ in o["polys"]) else None
        gz = np.vstack([q for k, q in o["polys"] if k == 0])[:, 2].mean()
        print(o["id"][3:11], "h", o["h"], "area", round(fp.area), "cen", np.round(fp.centroid.coords[0], 1).tolist(), "gz", round(float(gz), 1),
              "roof z", None if roof is None else (round(float(roof[:, 2].min()), 1), round(float(roof[:, 2].max()), 1)), "in" if fp.contains(Point(x, y)) else "")
