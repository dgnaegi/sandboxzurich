"""KVA Josefstrasse plant buildings: height-field boxes from the swissBUILDINGS3D roof faces (chimney spike excluded), industrial
metal-panel facade with fascia bands and a service stair; merged into the chimney GLB by k45_kva.build(). Returns (boxes, hide_pts)."""
import pickle, glob
import numpy as np
from common import *
from shapely.geometry import Point, box as sbox
from shapely.prepared import prep

CH = (433.5, 291.7)


def boxes(cell=3.0, step=3.0):
    roofs = []
    for f in sorted(glob.glob(str(ROOT / "data/build/bld/*.pkl"))):
        for b in pickle.load(open(f, "rb")):
            if b["id"].startswith("ID_C5351824"):
                fp = b
                for k, p in b["polys"]:
                    p = np.asarray(p)
                    if k != 0 and len(p) >= 3 and abs(np.hypot(p[:, 0].mean() - CH[0], p[:, 1].mean() - CH[1])) > 6:
                        try:
                            g = Polygon(p[:, :2]).buffer(0)
                            if g.area > 0.5 and p[:, 2].max() - p[:, 2].min() < 6: roofs.append((g, float(p[:, 2].mean())))
                        except Exception: pass
    g0 = ground(*CH)
    allg = unary_union([g for g, _ in roofs]); x0, y0, x1, y1 = allg.bounds
    xs = np.arange(x0, x1, cell); ys = np.arange(y0, y1, cell)
    H = np.zeros((len(ys), len(xs)))
    for g, z in roofs:
        pg = prep(g); bx = g.bounds
        for j, y in enumerate(ys):
            if y + cell < bx[1] or y > bx[3]: continue
            for i, x in enumerate(xs):
                if x + cell < bx[0] or x > bx[2]: continue
                if pg.contains(Point(x + cell / 2, y + cell / 2)): H[j, i] = max(H[j, i], z - g0 + 3.06)
    H = np.round(H / step) * step
    out = []; used = np.zeros_like(H, bool)
    for j in range(len(ys)):
        for i in range(len(xs)):
            if used[j, i] or H[j, i] < 4: continue
            h = H[j, i]; i2 = i
            while i2 + 1 < len(xs) and not used[j, i2 + 1] and H[j, i2 + 1] == h: i2 += 1
            j2 = j
            while j2 + 1 < len(ys) and all((not used[j2 + 1, q]) and H[j2 + 1, q] == h for q in range(i, i2 + 1)): j2 += 1
            used[j:j2 + 1, i:i2 + 1] = True
            out.append((xs[i], ys[j], xs[i2] + cell, ys[j2] + cell, h))
    hide = [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp["fp"].geoms if hasattr(fp["fp"], "geoms") else [fp["fp"]])] if False else []
    return out
