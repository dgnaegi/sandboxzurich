"""Bump audit: height of the RENDERED road surface (asphalt/marking/sidewalk triangles of data/build/tiles_raw/*.glb) along all street axes.
usage: .venv/bin/python pipeline/audit_bumps.py [--tiles 0_1,0_0]  -> research/bumps.md, data/build/bumps.json
Sampled every 0.5 m. Step: |z(s+.75)-z(s-.75) - 1.5*slope(+-6 m)| > 8 cm; bump: |z - mean(z(s-2.5), z(s+2.5))| > 8 cm (width < 3 m).
Skips bridges/tunnels. Cause = nearest feature (tile edge, crossing, deck end, rail/tram, junction, other)."""
import glob, json, math, sys
from collections import Counter
from pathlib import Path
import numpy as np
import shapely
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_markings as AM  # noqa: E402  (glb reader)

RAW, PX, T = R / "data/build/tiles_raw", 0.5, 200
LAYERS = {34}  # asphalt only: sidewalk (35) / marking (39) triangles sit on curbs and offsets and would fake steps on narrow streets
THR = 0.08
_cache = {}


def tile_z(tx, ty):
    """float32 (n,n) rendered surface height, row 0 = north, PX m/px; NaN without ground triangle"""
    k = (tx, ty)
    if k in _cache:
        return _cache[k]
    f = RAW / f"t_{tx}_{ty}.glb"
    g = AM.read_ground(f) if f.exists() else None
    n = int(T / PX)
    if g is None:
        _cache[k] = None
        return None
    pos, col, lay, idx = g
    Z = np.full((n, n), -np.inf, np.float32)
    X, Yr, Zh = (pos[:, 0] - tx * T) / PX, ((ty + 1) * T + pos[:, 2]) / PX, pos[:, 1]  # col, row (south = larger), height
    for t in idx.reshape(-1, 3):
        if int(lay[t[0]]) not in LAYERS:
            continue
        c, r, z = X[t], Yr[t], Zh[t]
        c0, c1, r0, r1 = int(max(0, math.floor(c.min()))), int(min(n - 1, math.ceil(c.max()))), int(max(0, math.floor(r.min()))), int(min(n - 1, math.ceil(r.max())))
        if c1 < c0 or r1 < r0:
            continue
        gc, gr = np.meshgrid(np.arange(c0, c1 + 1) + .5, np.arange(r0, r1 + 1) + .5)
        d = (r[1] - r[2]) * (c[0] - c[2]) + (c[2] - c[1]) * (r[0] - r[2])
        if abs(d) < 1e-9:
            continue
        a = ((r[1] - r[2]) * (gc - c[2]) + (c[2] - c[1]) * (gr - r[2])) / d
        b = ((r[2] - r[0]) * (gc - c[2]) + (c[0] - c[2]) * (gr - r[2])) / d
        m = (a >= -1e-6) & (b >= -1e-6) & (a + b <= 1 + 1e-6)
        if not m.any():
            continue
        z = a * z[0] + b * z[1] + (1 - a - b) * z[2]
        sub = Z[r0:r1 + 1, c0:c1 + 1]
        sub[m] = np.maximum(sub[m], z[m])
    Z[np.isinf(Z)] = np.nan
    _cache[k] = Z
    return Z


def sample(x, y):
    tx, ty = np.floor(x / T).astype(int), np.floor(y / T).astype(int)
    out = np.full(len(x), np.nan)
    for k in set(zip(tx.tolist(), ty.tolist())):
        Z = tile_z(*k)
        if Z is None:
            continue
        m = (tx == k[0]) & (ty == k[1])
        c, r = (x[m] - k[0] * T) / PX - .5, ((k[1] + 1) * T - y[m]) / PX - .5
        out[m] = Z[np.clip(np.round(r).astype(int), 0, Z.shape[0] - 1), np.clip(np.round(c).astype(int), 0, Z.shape[1] - 1)]
    return out


def detect(z, ds=0.5):
    """-> step, bump, knee arrays: knee = slope change (m/m) between the 3-6 m before and after (ramp ends of underpasses, not a bump)"""
    n = len(z); k = lambda m: int(round(m / ds))
    st = np.zeros(n); bp = np.zeros(n); kn = np.zeros(n)
    a, b, c, d = k(.75), k(6), k(2.5), 0
    for i in range(b, n - b):
        w = z[i - b:i + b + 1]
        if np.isnan(w).any():
            continue
        ref = (z[i + b] - z[i - b]) / (2 * b * ds)
        st[i] = abs(z[i + a] - z[i - a] - 2 * a * ds * ref)
        bp[i] = abs(z[i] - 0.5 * (z[i - c] + z[i + c]))
        kn[i] = abs((z[i + b] - z[i + k(3)]) - (z[i - k(3)] - z[i - b])) / (3 * 1.0)
    return st, bp, kn


def load_ways():
    import sources, streets
    nodes, els = sources.osm()
    S = streets.parse(nodes, els)
    skip_hw = {"footway", "path", "steps", "track", "cycleway", "corridor", "pedestrian"}
    ways = [w for w in S["ways"] if w["hw"] not in skip_hw and w["tags"].get("bridge") not in ("yes", "viaduct", "movable", "boardwalk", "cantilever", "aqueduct")
            and w["tags"].get("tunnel") not in ("yes", "building_passage") and w["tags"].get("layer") in (None, "0")]
    return ways, S


def causes_index(S):
    from shapely.strtree import STRtree
    P = {}
    cr = []
    for c in S.get("crossings", []) or []:   # streets.parse: (point, kind, osm id)
        p = c[0]
        cr.append(p if hasattr(p, "geom_type") else shapely.Point(float(p[0]), float(p[1])))
    P["crossing"] = (STRtree(cr), cr) if cr else None
    tr = [t for t in S.get("tram", [])]
    P["tram"] = (STRtree(tr), tr) if tr else None
    return P


def near(P, k, pt, r):
    if not P.get(k):
        return False
    t, g = P[k]
    return any(g[j].distance(pt) <= r for j in t.query(pt.buffer(r)))


def main():
    only = None
    if "--tiles" in sys.argv:
        only = set(sys.argv[sys.argv.index("--tiles") + 1].split(","))
    ways, S = load_ways()
    P = causes_index(S)
    from config import POLYGON
    play = shapely.Polygon(POLYGON).buffer(-8)
    ev, tot = [], 0.0
    from shapely.geometry import LineString
    for w in ways:
        ln = w["line"].intersection(play)
        if ln.geom_type != "LineString" or ln.length < 8:
            continue
        s = np.arange(0, ln.length, 0.5)
        pts = shapely.line_interpolate_point(ln, s)
        x, y = shapely.get_x(pts), shapely.get_y(pts)
        if only is not None and not any(f"{math.floor(a / T)}_{math.floor(b / T)}" in only for a, b in zip(x[::20], y[::20])):
            continue
        z = sample(x, y)
        if np.isnan(z).all():
            continue
        tot += ln.length
        st, bp, kn = detect(z)
        flag = (st > THR) | (bp > THR)
        i = 0
        while i < len(z):
            if flag[i]:
                j = i
                while j + 1 < len(z) and flag[j + 1:j + 7].any():
                    j += 1
                kk = i + int(np.argmax(np.maximum(st[i:j + 1], bp[i:j + 1])))
                mag = float(max(st[kk], bp[kk]))
                kind = "ramp knee" if kn[kk] > 0.10 else "bump"
                pt = shapely.Point(x[kk], y[kk])
                te = min(abs(x[kk] % T), T - abs(x[kk] % T), abs(y[kk] % T), T - abs(y[kk] % T))
                cause = ("crossing" if near(P, "crossing", pt, 4.0) else "tram/rail" if near(P, "tram", pt, 3.0)
                         else "tile edge" if te < 1.5 else "other")
                ev.append(dict(x=round(float(x[kk]), 1), y=round(float(y[kk]), 1), cm=round(mag * 100), len=round((j - i) * .5, 1),
                               cause=cause, kind=kind, prof=[None if np.isnan(v) else round(float(v), 2) for v in z[max(0, i - 24):j + 25:2]], svc=w["hw"] == "service", street=w["tags"].get("name", "") or w["hw"], tile=f"{math.floor(x[kk] / T)}_{math.floor(y[kk] / T)}"))
                i = j + 7
            else:
                i += 1
    ev.sort(key=lambda e: -e["cm"])
    (R / "data/build/bumps.json").write_text(json.dumps(dict(km=tot / 1000, events=ev)))
    cnt = Counter(e["cause"] for e in ev if not e["svc"] and e["kind"] == "bump")
    print(f"{tot / 1000:.1f} km axes; events > {THR * 100:.0f} cm: {len(ev)} (service ways {sum(e['svc'] for e in ev)}, ramp knees {sum(e['kind'] != 'bump' for e in ev)}); "
          f"street bumps {sum(cnt.values())} {dict(cnt)}; > 15 cm: {sum(e['cm'] > 15 for e in ev if not e['svc'] and e['kind'] == 'bump')}")
    for e in [e for e in ev if not e['svc'] and e['kind'] == 'bump'][:14]:
        print(e)


if __name__ == "__main__":
    main()
