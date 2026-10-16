"""Apply pipeline/overrides/terrain_cuts.json to a Heights grid (in place)."""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString

F = Path(__file__).resolve().parent / "overrides" / "terrain_cuts.json"


def _profile(H, X, Y, c):
    """Sunken straight corridor with a longitudinal profile (underpass floor): axis a->b, profile [[s, z], ...] (s in m from a),
    half-width "half", terrain blended over "blend" m outside the rectangle. mode "min" (default) only lowers, "set" sets both ways."""
    a, b = np.asarray(c["axis"][0], float), np.asarray(c["axis"][1], float)
    L = float(np.linalg.norm(b - a)); d = (b - a) / L; nrm = np.array([d[1], -d[0]])
    pr = np.asarray(c["profile"], float); half, bl = float(c["half"]), float(c.get("blend", 1.0))
    s0, s1 = pr[0, 0], pr[-1, 0]
    x0, x1 = min(a[0], b[0]) - half - bl - 3, max(a[0], b[0]) + half + bl + 3
    y0, y1 = min(a[1], b[1]) - half - bl - 3, max(a[1], b[1]) + half + bl + 3
    m = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
    dx, dy = X[m] - a[0], Y[m] - a[1]
    s, o = dx * d[0] + dy * d[1], dx * nrm[0] + dy * nrm[1]
    ds = np.maximum(np.maximum(s0 - s, s - s1), 0); do = np.maximum(np.abs(o) - half, 0)
    dist = np.hypot(ds, do)
    z = np.interp(s, pr[:, 0], pr[:, 1])
    t = np.clip(dist / bl, 0, 1)
    tz = z * (1 - t) + H.z[m] * t
    new = np.minimum(H.z[m], tz) if c.get("mode", "min") == "min" else tz
    H.z[m] = np.where(dist <= bl, new, H.z[m])
    print(f"terrain_cuts: {c['name'][:40]} -> profile {pr[0, 1]:.2f}..{pr[-1, 1]:.2f}")


def apply(H, lock_only=False):
    """lock_only=True re-applies only the entries marked "lock": true (call it again after road_height.apply so smoothing cannot lift them)."""
    if not F.exists():
        return
    ny, nx = H.z.shape
    X, Y = np.meshgrid(H.x0 + np.arange(nx) * H.step, H.y0 + np.arange(ny) * H.step)
    for c in json.load(open(F))["cuts"]:
        if lock_only and not c.get("lock"):
            continue
        if "profile" in c:
            _profile(H, X, Y, c)
            continue
        if "poly" in c:  # flat platform: terrain inside the polygon is set to z (both ways), blended over "blend" m outside (e.g. Zuerich HB hall floor)
            pg = shapely.Polygon(c["poly"]); bl = c.get("blend", 3.0); z = float(c["z"])
            x0, y0, x1, y1 = pg.buffer(bl).bounds
            m = (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
            d = shapely.distance(pg, shapely.points(X[m], Y[m]))
            t = np.clip(d / bl, 0, 1)
            H.z[m] = np.where(d <= bl, z * (1 - t) + H.z[m] * t, H.z[m])
            print(f"terrain_cuts: {c['name'][:40]} -> flat z {z:.2f}")
            continue
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
