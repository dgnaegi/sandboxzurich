"""Pedestrian crossings (Fussgängerstreifen): decide per OSM crossing node whether a yellow zebra is drawn. # crossings2
Evidence in this order (research/crossings.md):
  1. OSM tags: crossing=zebra|marked|uncontrolled|traffic_signals, crossing:markings=zebra|yes|..., crossing_ref=zebra  -> "tag"
     (crossing=unmarked / crossing:markings=no are explicit "no" tags).
  2. SWISSIMAGE (0.5 m/px mosaic, data/raw/ortho_wms): yellow stripe pattern across the carriageway around the node -> "ortho".
     Decides unmarked/untagged nodes and overrules a "no" tag only with strong evidence. Cache: data/build/crossings_ortho.json.
  3. Nodes without a street way: snapped to the nearest carriageway within SNAP m.
Zone 30 / Begegnungszone / Fussgängerzone: tags alone do not count (old rule: signalised T30 street, school crossing or traffic_signals);
an ortho-proven stripe pattern always does.
Public: decide(S) -> {node_id: dict(draw, src, ...)}, ortho_score(x, y, d, half) -> float"""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from shapely import STRtree
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parent.parent
ORTHO = ROOT / "data/raw/ortho_wms"
CACHE = ROOT / "data/build/crossings_ortho.json"
TILE, PX = 500.0, 1000
SNAP = 6.0
STRONG = 0.7  # ortho-only decision: 0.5-0.7 on 442 OSM-unmarked nodes was vegetation/brick in 6 of 8 checked cases, 0.7+ real stripes
_tiles = {}


def _tile(ix, iy):
    k = (ix, iy)
    if k not in _tiles:
        f = ORTHO / f"r_{ix}_{iy}.jpg"
        _tiles[k] = None
        if f.exists():
            a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
            R, G, B = a[..., 0], a[..., 1], a[..., 2]
            yb = (R + G) / 2 - B
            lum = (R + G + B) / 3
            ybs = ndi.gaussian_filter(yb, 0.6)
            loc = ndi.median_filter(ybs[::2, ::2], size=9)
            loc = np.kron(loc, np.ones((2, 2), np.float32))[: yb.shape[0], : yb.shape[1]]
            sunny = (yb > 14) & (R > 85) & (np.abs(R - G) < 24) & (G > R - 24)
            shade = (lum < 95) & (lum > 22) & (ybs > np.maximum(5.0, 0.10 * lum)) & (ybs - loc > 3.5) & (np.abs(R - G) < 0.25 * lum + 6)
            _tiles[k] = (sunny.astype(np.float32) + shade.astype(np.float32) * 0.5)  # 1 = sunlit yellow, 0.5 = shaded yellow
    return _tiles[k]


def _sample(pts):
    """yellow-mask value (0..1) at local metres pts (N,2); NaN where no ortho."""
    out = np.full(len(pts), np.nan, np.float32)
    ix, iy = np.floor(pts[:, 0] / TILE).astype(int), np.floor(pts[:, 1] / TILE).astype(int)
    for k in set(zip(ix.tolist(), iy.tolist())):
        t = _tile(*k)
        if t is None:
            continue
        m = (ix == k[0]) & (iy == k[1])
        c = (pts[m, 0] - k[0] * TILE) * 2.0 - 0.5
        r = ((k[1] + 1) * TILE - pts[m, 1]) * 2.0 - 0.5
        out[m] = ndi.map_coordinates(t, [r, c], order=1, mode="nearest")
    return out


def ortho_score(x, y, d, half, shade=False, want_shift=False):
    """Best fraction of yellow pixels in a 4.5 m x (2*half) window shifted around the node (stripes lie across the carriageway)."""
    d = np.asarray(d, float)
    n = np.array([-d[1], d[0]])
    half = float(np.clip(half, 2.0, 7.0))
    u = np.arange(-2.25, 2.26, 0.25)
    v = np.arange(-half, half + 0.01, 0.25)
    U, V = np.meshgrid(u, v)
    best, bs = 0.0, (0.0, 0.0)
    shifts = [(a, b) for a in (-4, -3, -2, -1, 0, 1, 2, 3, 4) for b in (-1.5, 0, 1.5)]
    P = np.stack([x + U.ravel() * d[0] + V.ravel() * n[0], y + U.ravel() * d[1] + V.ravel() * n[1]], 1)
    yb = _sample(P)
    if np.isnan(yb).all():
        return (-1.0, (0.0, 0.0)) if want_shift else -1.0
    yel = (yb > (0.2 if shade else 0.8)).reshape(U.shape)
    for a, b in shifts:
        ia = int(round(a / 0.25)); ib = int(round(b / 0.25))
        w = np.roll(np.roll(yel, ia, axis=1), ib, axis=0)
        f = float(w.mean())
        cols = w.mean(axis=1)  # per across-position: stripes cross the whole 4.5 m
        sc = f * min(1.0, float((cols > 0.3).mean()) * 1.6)
        if sc > best:
            best, bs = sc, (-a, -b)
    return (best, bs) if want_shift else best


def _langstrasse_region():
    f = ROOT / "pipeline/overrides/markings_langstrasse.json"
    if not f.exists():
        return None
    import shapely
    from shapely.geometry import Polygon
    d = json.load(open(f))
    return shapely.union_all([Polygon(r).buffer(0) for r in d.get("region", [])]) if d.get("region") else None


def decide(S, R=None):
    """-> {node_id: {draw, src, x, y, d, way, score}}; every crossing node of S["crossings"] gets an entry. Writes CACHE."""
    import streets_rules
    R = R or streets_rules.rules()
    cand = [w for w in S["ways"] if w["hw"] != "service" and w["w"] >= 4]
    tree = STRtree([w["line"] for w in cand])
    by_node = {}
    for w in cand:
        for n in w["nodes"]:
            by_node.setdefault(n, []).append(w)
    ls = _langstrasse_region()
    out = {}
    for (x, y), kind, nid in S["crossings"]:
        tag = kind not in ("no", "unmarked", "")
        P = Point(x, y)
        w = next(iter(by_node.get(nid, [])), None)
        if w is None:  # crossing node without a street way: snap to the nearest carriageway (tag 10 m, ortho-only 6 m)
            i = tree.nearest(P)
            if i is not None and cand[i]["line"].distance(P) <= (10.0 if tag else SNAP):
                w = cand[i]
        rec = {"draw": False, "src": "no", "tag": kind}
        out[nid] = rec
        if w is None:
            rec["why"] = "no way"
            continue
        ln = w["line"]
        s = ln.project(P)
        q = ln.interpolate(s)
        a, b = ln.interpolate(max(s - 1, 0)), ln.interpolate(min(s + 1, ln.length))
        d = np.array([b.x - a.x, b.y - a.y]); d = d / (np.hypot(*d) + 1e-9)
        sc, (du, dv) = ortho_score(q.x, q.y, d, w["w"] / 2, want_shift=True)
        rec.update(score=round(float(sc), 2), x=q.x, y=q.y, d=d, way=w)
        zone = R.zone_point(x, y)
        proven = sc >= STRONG
        if tag:
            ok = zone not in ("beg", "fuss") and not (zone == "z30" and w["tempo"] != 30 and not R.near_school(x, y, 40) and kind != "traffic_signals")
            if ok:
                rec.update(draw=True, src="tag")
                continue
        if proven and not (ls is not None and ls.contains(P)):  # inside the measured Langstrasse region markings_override owns the stripes
            rec.update(draw=True, src="ortho", x=q.x + du * d[0] - dv * d[1], y=q.y + du * d[1] + dv * d[0])
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({str(k): {"draw": v["draw"], "src": v["src"], "tag": v["tag"], "score": v.get("score"), "why": v.get("why")}
                                 for k, v in sorted(out.items())}, indent=0))
    return out
