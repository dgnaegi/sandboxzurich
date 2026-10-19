"""Pedestrian crossings (Fussgängerstreifen): decide per OSM crossing node whether a yellow zebra is drawn. # crossings2
Evidence in this order (research/crossings.md):
  1. OSM tags: crossing=zebra|marked|uncontrolled|traffic_signals, crossing:markings=zebra|yes|..., crossing_ref=zebra  -> "tag"
     (crossing=unmarked / crossing:markings=no are explicit "no" tags).
  2. SWISSIMAGE (0.5 m/px mosaic, data/raw/ortho_wms): yellow stripe pattern across the carriageway around the node -> "ortho".
     Decides unmarked/untagged nodes and overrules a "no" tag only with strong evidence. Cache: data/build/crossings_ortho.json.
  3. Nodes without a street way: snapped to the nearest carriageway within SNAP m.
Zone 30 / Begegnungszone / Fussgängerzone: tags alone do not count (old rule: signalised T30 street, school crossing or traffic_signals);
an ortho-proven stripe pattern always does.
crossings3: scan() adds zebras along all carriageways that the ortho proves but OSM lacks, and moves tag zebras the ortho does not
show (score < 0.15 in sunlight) to a proven stripe pattern within SCAN_MOVE m. audit: pipeline/audit_markings.py.
Public: decide(S) -> {node_id: dict(draw, src, ...)}, ortho_score(x, y, d, half) -> float"""
import json
from pathlib import Path
import numpy as np
import shapely
from PIL import Image
from scipy import ndimage as ndi
from shapely import STRtree
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parent.parent
ORTHO = ROOT / "data/raw/ortho_wms"
CACHE = ROOT / "data/build/crossings_ortho.json"
TILE, PX = 500.0, 1000
SNAP = 6.0
SCAN = 0.76   # crossings3: score for a zebra found by scanning the carriageways (no OSM node), stricter than STRONG: ~100k positions are tested
SCAN_STEP, SCAN_SEP, SCAN_SEP_OWN, SCAN_MOVE = 2.0, 9.0, 4.5, 14.0   # scan_blob experiment (ortho blobs / flank test, research/markings_audit.md): the yellow mask also fires on sunlit warm asphalt -> reverted
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
    scan(S, out, cand, ls, R)  # crossings3: zebras that no OSM node describes (SWISSIMAGE scan along all carriageways)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({str(k): {"draw": v["draw"], "src": v["src"], "tag": v["tag"], "score": v.get("score"), "why": v.get("why")}
                                 for k, v in sorted(out.items(), key=lambda kv: str(kv[0]))}, indent=0))
    return out


def _scan25(S, cand, ls):
    """zebras measured on the 0.25 m SWISSIMAGE (markings_ortho25.py): [(score, x, y, d, way)] or None when that ortho is not cached"""
    try:
        import markings_ortho25 as M25
    except ImportError:
        return None
    if not M25.D.exists() or len(list(M25.D.glob("o_*.jpg"))) < 100:
        return None
    tree = STRtree([w["line"] for w in cand])
    res = []
    for z in M25.detect(S.get("roads")):
        P = Point(z["x"], z["y"])
        w = cand[int(tree.nearest(P))]
        ln = w["line"]
        if ln.distance(P) > 0.35 * w["w"] + 1.2 or 2 * z["half"] < 0.5 * min(w["w"], 12.0) or w["tags"].get("bridge") not in (None, "no") or w["tags"].get("tunnel") not in (None, "no"):
            continue
        s_ = ln.project(P)
        a, b = ln.interpolate(max(s_ - 1, 0)), ln.interpolate(min(s_ + 1, ln.length))
        t = np.array([b.x - a.x, b.y - a.y]); t = t / (np.hypot(*t) + 1e-9)
        d = np.array(z["d"])
        if abs(float(t @ d)) < 0.8:   # stripes run along the travel direction (+-37 deg)
            continue
        res.append((0.9, z["x"], z["y"], d if float(t @ d) > 0 else -d, {"w": 2 * z["half"] + 0.6, "off": 0.0, "tags": w["tags"], "hw": w["hw"]}))
    return res


def scan(S, out, cand, ls, R):
    """crossings3. Adds out['scan_<n>'] entries {draw, src='scan', x, y, d, way, score}. Mutates tag entries moved to a proven pattern.
    Every carriageway is walked in SCAN_STEP m; where the ortho shows a stripe pattern across the road (score >= SCAN) a zebra is added."""
    found = []
    found25 = _scan25(S, cand, ls)
    for w in ([] if found25 is not None else cand):   # fallback (no 0.25 m ortho cached): walk the carriageways on the 0.5 m mosaic
        t = w["tags"]
        if t.get("bridge") not in (None, "no") or t.get("tunnel") not in (None, "no") or w["line"].length < 14:
            continue
        ln = w["line"]
        ss = np.arange(5.0, ln.length - 5.0, SCAN_STEP)
        pts = np.array([(p.x, p.y) for p in shapely.line_interpolate_point(ln, ss)])
        P = [ln.interpolate(min(a + 1, ln.length)) for a in ss]
        Q = [ln.interpolate(max(a - 1, 0)) for a in ss]
        D = np.array([(a.x - b.x, a.y - b.y) for a, b in zip(P, Q)]); D = D / (np.hypot(D[:, 0], D[:, 1])[:, None] + 1e-9)
        half = float(np.clip(w["w"] / 2, 2.0, 7.0))
        offs = np.linspace(-half, half, 7)   # prefilter: any yellow near the axis (one vectorised look-up per way)
        pre = np.stack([pts[:, 0, None] + (-D[:, 1, None]) * offs[None], pts[:, 1, None] + D[:, 0, None] * offs[None]], -1).reshape(-1, 2)
        yb = _sample(pre).reshape(len(ss), len(offs))
        ok = np.nan_to_num(yb, nan=0.0).max(axis=1) >= 0.5
        for i in np.nonzero(ok)[0]:
            sc, (du, dv) = ortho_score(pts[i, 0], pts[i, 1], D[i], w["w"] / 2, want_shift=True)
            if sc >= SCAN:
                x, y = pts[i, 0] + du * D[i, 0] - dv * D[i, 1], pts[i, 1] + du * D[i, 1] + dv * D[i, 0]
                if ls is not None and ls.contains(Point(x, y)):
                    continue
                found.append((sc, x, y, D[i], w))
    found = (found25 or []) + found
    found.sort(key=lambda f: -f[0])
    conf = [(r["x"], r["y"]) for r in out.values() if r["draw"] and r.get("score", 1.0) >= 0.15]
    unconf = {k: r for k, r in out.items() if r["draw"] and r.get("score", 1.0) < 0.15 and r["score"] >= 0 and r["src"] == "tag"}
    taken, n, moved = [], 0, 0
    for sc, x, y, d, w in found:
        if any(np.hypot(x - a, y - b) < SCAN_SEP for a, b in conf) or any(np.hypot(x - a, y - b) < SCAN_SEP_OWN for a, b in taken):
            continue
        for k, r in unconf.items():  # an unconfirmed tag zebra close to a proven pattern was placed on the wrong spot: move it
            if r["draw"] and np.hypot(x - r["x"], y - r["y"]) < SCAN_MOVE:
                r.update(draw=False, src="moved")
                moved += 1
        out[f"scan_{n}"] = {"draw": True, "src": "scan", "tag": "", "score": round(float(sc), 2), "x": x, "y": y, "d": d, "way": w}
        taken.append((x, y)); n += 1
    feet = []   # the AV carriageway polygon is narrower than the real street at wide junctions / tram stops: a zebra there was clipped away -> asphalt under it
    for k, r in out.items():
        if r["src"] == "scan":
            d, c, h = np.asarray(r["d"]), np.array([r["x"], r["y"]]), r["way"]["w"] / 2 + 0.2
            nn = np.array([-d[1], d[0]])
            feet.append(shapely.Polygon([c - d * 2.2 - nn * h, c + d * 2.2 - nn * h, c + d * 2.2 + nn * h, c - d * 2.2 + nn * h]))
    if feet and S.get("roads") is not None:
        S["roads"] = shapely.union_all([S["roads"], *feet])
    print(f"crossings: {n} zebras from the SWISSIMAGE scan, {moved} tag zebras without ortho evidence moved", flush=True)
