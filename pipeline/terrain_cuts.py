"""Apply pipeline/overrides/terrain_cuts.json to a Heights grid (in place)."""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString

F = Path(__file__).resolve().parent / "overrides" / "terrain_cuts.json"


def apply(H):
    if not F.exists():
        return
    ny, nx = H.z.shape
    X, Y = np.meshgrid(H.x0 + np.arange(nx) * H.step, H.y0 + np.arange(ny) * H.step)
    for c in json.load(open(F))["cuts"]:
        ln = LineString(c["line"])
        if c["z"] == "min":
            s = np.linspace(0, ln.length, max(2, int(ln.length / 2)))
            pts = [ln.interpolate(v) for v in s[: len(s) * 2 // 3]]  # open cutting part, before the covered end
            z = float(min(H.at(p.x, p.y) for p in pts))
        else:
            z = float(c["z"])
        w, bl = c["width"] / 2, c.get("blend", 3.0)
        x0, y0, x1, y1 = ln.buffer(w + bl).bounds
        m = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
        d = shapely.distance(ln, shapely.points(X[m], Y[m]))
        t = np.clip((d - w) / bl, 0, 1)  # 0 inside the corridor, 1 outside the blend band
        H.z[m] = np.where(d <= w + bl, np.minimum(H.z[m], z * (1 - t) + H.z[m] * t), H.z[m])
        print(f"terrain_cuts: {c['name'][:40]} -> z {z:.2f}")
