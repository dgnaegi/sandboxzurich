"""Marking height audit on built tiles (data/build/tiles_raw): marking vertices (layer 39) vs asphalt (layer 34) vertices.
float: no asphalt vertex within 2 m (xz) has y within 0.25 m of the marking vertex (marking floats above / sinks below every road surface nearby).
usage: .venv/bin/python pipeline/audit_markings_float.py -> research/markings_fix/float.json (clustered places)"""
import sys, glob, json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).parent))
from audit_markings import read_ground, RAW
out = []
for f in sorted(glob.glob(str(RAW / "t_*.glb"))):
    g = read_ground(f)
    if g is None: continue
    pos, col, lay, idx = g; L = lay.astype(int)
    a = pos[L == 34]; m = pos[L == 39]
    if len(a) == 0 or len(m) == 0: continue
    kd = cKDTree(a[:, [0, 2]]); nb = kd.query_ball_point(m[:, [0, 2]], 2.0)
    bad = np.array([len(n) > 0 and np.min(np.abs(a[n, 1] - m[k, 1])) > 0.25 for k, n in enumerate(nb)])
    if bad.sum() < 4: continue
    p = m[bad]; c = np.floor(p[:, [0, 2]] / 20).astype(int)
    for key in set(map(tuple, c)):
        s = (c == key).all(1)
        if s.sum() >= 4:
            q = p[s]; out.append(dict(tile=Path(f).stem, n=int(s.sum()), x=float(q[:, 0].mean()), y=float(-q[:, 2].mean())))
json.dump(out, open("research/markings_fix/float.json", "w"))
out.sort(key=lambda o: -o["n"]); print(len(out), "cells;", [(o["tile"], o["n"], round(o["x"]), round(o["y"])) for o in out[:15]])
