"""Compare tile hmaps (walking/driving height) of SBZ_LIDAR_ROAD test builds with the LiDAR DTM.
usage: lidar_road_cmp.py <dirA> <dirB> [<dirC>...]  (dirs with t_*.json copies; first = baseline). Cells that differ between baseline and any
other dir = road corridors; reports MAE/bias/p95 of (hmap - lidar dtm) there, per dir, plus the change size."""
import base64, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lidar


def hm(f):
    h = json.load(open(f))["hmap"]
    z = np.frombuffer(base64.b64decode(h["zb64"]), dtype="<i2").astype(float).reshape(h["h"], h["w"]) / 100
    gy, gx = np.mgrid[0:h["h"], 0:h["w"]]
    return z, h["x0"] + gx * h["step"], h["y0"] + gy * h["step"]


dirs = [Path(d) for d in sys.argv[1:]]
for t in sorted(p.name for p in dirs[0].glob("t_*.json")):
    base, X, Y = hm(dirs[0] / t)
    others = [hm(d / t)[0] for d in dirs[1:]]
    ch = np.zeros(base.shape, bool)
    for o in others:
        ch |= np.abs(o - base) > 0.01
    d = lidar.dtm(X.ravel(), Y.ravel()).reshape(X.shape)
    ok = ch & np.isfinite(d) & np.isnan(lidar.bld(X.ravel(), Y.ravel()).reshape(X.shape))
    print(f"{t}: changed cells {int(ch.sum())}, with lidar {int(ok.sum())}")
    for name, z in [(dirs[0].name, base)] + [(d.name, o) for d, o in zip(dirs[1:], others)]:
        e = (z - d)[ok]
        if len(e):
            print(f"   {name:8s} bias {e.mean():+.3f} MAE {np.abs(e).mean():.3f} p95 {np.percentile(np.abs(e), 95):.3f} max {np.abs(e).max():.2f}")
