"""Lane arrows before signalised stop lines (Swiss practice: one arrow per lane, left / straight / right / combined).
Lane assignment from OSM turn:lanes where mapped, otherwise from the real junction topology (which streets leave the node).
arrows(S, near) -> [(x, y, heading, decal_kind)]   kinds: 4 straight, 7 left, 8 right, 9 straight+left, 10 straight+right."""
import numpy as np
from shapely.geometry import Point

import streets

LANE_W = 3.1
BIKE_W = 1.6
KIND = {frozenset("f"): 4, frozenset("l"): 7, frozenset("r"): 8, frozenset("fl"): 9, frozenset("fr"): 10}
TOKEN = {"left": "l", "slight_left": "l", "sharp_left": "l", "through": "f", "": "f", "none": "f",
         "right": "r", "slight_right": "r", "sharp_right": "r"}


def _tags_lanes(w, sgn):
    t = w["tags"]
    key = "turn:lanes" if w["oneway"] else ("turn:lanes:forward" if sgn > 0 else "turn:lanes:backward")
    v = t.get(key)
    if not v:
        return None
    lanes = []
    for tok in v.split("|"):
        s = {TOKEN.get(p.strip()) for p in tok.split(";") if not p.strip().startswith("merge")}
        s.discard(None)
        lanes.append(s or {"f"})
    return lanes


def _options(S, arm):
    """Directions ('l','f','r') in which traffic can leave the junction after this arm."""
    w, sgn = arm["way"], arm["sgn"]
    ln = w["line"]
    nid = w["nodes"][-1] if sgn > 0 else w["nodes"][0]
    t = arm["t"]
    opts = set()
    for o in S["ways"]:
        if o is w or o["hw"] == "service" or nid not in o["nodes"]:
            continue
        ol = o["line"]
        idxs = [i for i, n in enumerate(o["nodes"]) if n == nid]
        cands = []
        for i in idxs:
            if i < len(o["nodes"]) - 1:
                cands.append(1)
            if i > 0 and not o["oneway"]:
                cands.append(-1)
        # direction of leaving the node along o
        node_pt = Point(ln.coords[-1] if sgn > 0 else ln.coords[0])
        s0 = ol.project(node_pt)
        for d in set(cands):
            if o["oneway"] and d < 0:
                continue
            a = np.array(ol.interpolate(max(0, min(ol.length, s0 + d * 6.0))).coords[0]) - np.array(ol.interpolate(s0).coords[0])
            if np.hypot(*a) < 1:
                continue
            a /= np.hypot(*a)
            ang = np.degrees(np.arctan2(t[0] * a[1] - t[1] * a[0], t[0] * a[0] + t[1] * a[1]))
            if abs(ang) < 35:
                opts.add("f")
            elif 35 <= ang < 150:
                opts.add("l")
            elif -150 < ang <= -35:
                opts.add("r")
    return opts


def _assign(opts, n):
    lanes = [set() for _ in range(n)]
    if "l" in opts:
        lanes[0].add("l")
    if "r" in opts:
        lanes[-1].add("r")
    if "f" in opts:
        for i, s in enumerate(lanes):
            if not s or (n == 1) or (n > 2 and 0 < i < n - 1):
                s.add("f")
        if not any("f" in s for s in lanes):
            lanes[-1 if "r" in opts else 0].add("f")
    return lanes


def arrows(S, near):
    out = []
    for a in streets.signal_arms(S):
        w = a["way"]
        if a["half"] < 2.4 or not near.contains(Point(*a["p"])):
            continue
        s = a["s"]
        opts = _options(S, a)
        if not opts:
            continue
        t = a["t"]
        r = np.array([t[1], -t[0]])
        bike = BIKE_W if streets.has_lane(w, "right" if a["sgn"] > 0 else "left", s) else 0.0
        mapped = _tags_lanes(w, a["sgn"])
        if a["oneway"]:
            lo, hi = -a["half"] + 0.25, a["half"] - 0.25 - bike  # offsets right of centre line, left edge .. right edge
        else:
            lo, hi = 0.35, a["half"] - 0.25 - bike
        n = len(mapped) if mapped else max(1, int((hi - lo) // LANE_W))
        lw = (hi - lo) / n
        lanes = mapped if mapped else _assign(opts, n)
        base = np.array(a["p"]) - t * 9.0
        for i, ls in enumerate(lanes[:4]):
            k = KIND.get(frozenset(ls))
            if k is None:
                k = 9 if ls >= {"f", "l"} else 10 if ls >= {"f", "r"} else 4 if "f" in ls else 7 if "l" in ls else 8
            c = base + r * (lo + lw * (i + 0.5))
            out.append((float(c[0]), float(c[1]), float(np.arctan2(t[0], t[1])), k))
    return out
