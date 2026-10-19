"""Wall geometry of swissBUILDINGS3D buildings for zones 1+4 -> data/raw/autofacade/geom.pkl.
Per building: id, footprint (shapely), ground z, eave z, walls = list of (Nx3 float32). Local metres."""
import pickle

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from common import CACHE, ROOT, ZONES

M = 70


def main():
    out, tris, tb, tk = [], [], [], []
    for f in sorted((ROOT / "data" / "build" / "bld").glob("*.pkl")):
        for b in pickle.load(open(f, "rb")):
            ps = b["polys"]
            allp = np.concatenate([p for _, p in ps])
            c = allp.mean(0)
            if not any(x0 - M <= c[0] <= x1 + M and y0 - M <= c[1] <= y1 + M for x0, y0, x1, y1 in ZONES.values()):
                continue
            g = [p for k, p in ps if k == 0]
            w = [p for k, p in ps if k == 1]
            r = [p for k, p in ps if k == 2]
            if not g or not w:
                continue
            try:
                fp = unary_union([Polygon(p[:, :2]).buffer(0) for p in g if len(p) >= 3])
            except Exception:
                continue
            gz = float(np.min(np.concatenate(g)[:, 2]))
            rz = np.concatenate(r)[:, 2] if r else allp[:, 2]
            eave = float(np.percentile(rz, 25))
            out.append(dict(id=b["id"], fp=fp, gz=gz, eave=eave, top=float(allp[:, 2].max()), c=c[:2]))
            for kind, lst in ((1, w), (2, r)):
                for p in lst:
                    p = p[:-1] if np.allclose(p[0], p[-1]) else p
                    for i in range(1, len(p) - 1):
                        tris.append(np.stack([p[0], p[i], p[i + 1]]))
                        tb.append(len(out) - 1)
                        tk.append(kind)
    pickle.dump(dict(b=out, tris=np.array(tris, np.float32), tb=np.array(tb, np.int32), tk=np.array(tk, np.int8)), open(CACHE / "geom.pkl", "wb"))
    print(len(out), "buildings", len(tris), "tris")


if __name__ == "__main__":
    main()
