"""Carriageway geometry measured against the official survey (AV, pipeline/groundcover.py) instead of generic OSM widths.

streets.parse() calls apply(ways, G): for every OSM street axis the AV carriageway ("Strasse, Weg", "Parkplatz") is probed
with transects every ~4 m (left/right edge distance from the axis). An edge is TRUSTED when a sidewalk / bike path / green /
rail polygon follows it (AV separates carriageway and Trottoir there). Where the AV carriageway is merged with the sidewalk
(building or private ground follows the edge) the edge is replaced by a calibrated width (median of the trusted transects of
the same street class). Where AV has no carriageway under the axis, the OSM width (calibrated by class) is used.

apply() sets per way: w["w"] (measured width), w["w_osm"], w["off"] (lateral shift of the carriageway centre against the
axis, + = left of the digitising direction) and returns (AV-limited cap, fallback ribbons) from which the road polygon is built.
Switch SBZ_CARRIAGEWAY=osm restores the old pure-OSM buffers. Report: research/carriageway_audit.md
"""
import os
from collections import defaultdict

import numpy as np
import shapely
import shapely.ops
from shapely.geometry import Point, box

DEFAULT = "av"    # SBZ_CARRIAGEWAY=osm restores the old OSM buffers
STEP = 4.0          # m between transects
DS = 0.25           # m sampling along a transect
CELL = 100.0
GAP = 4             # samples (1 m): gaps in the AV carriageway (tram rails, hairlines) are bridged
MARGIN = 0.5        # m kept beyond a trusted AV edge (AV polygon itself is the limit)
MINW = 2.4
OFF_MAX = 5.0


class Mask:
    """Point-in-polygon test for a big multipolygon: clipped per 100 m cell, prepared."""

    def __init__(self, geom):
        self.g, self.cells = geom, {}

    def _cell(self, i, j):
        c = self.cells.get((i, j))
        if c is None:
            b = box(i * CELL - 30, j * CELL - 30, (i + 1) * CELL + 30, (j + 1) * CELL + 30)
            c = shapely.clip_by_rect(self.g, *b.bounds) if not self.g.is_empty else self.g
            shapely.prepare(c)
            self.cells[(i, j)] = c
        return c

    def contains(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        out = np.zeros(x.shape, bool)
        ci, cj = np.floor(x / CELL).astype(int), np.floor(y / CELL).astype(int)
        key = ci * 100003 + cj
        for k in np.unique(key):
            m = key == k
            i, j = ci[m][0], cj[m][0]
            out[m] = shapely.contains_xy(self._cell(i, j), x[m], y[m])
        return out


def _normal(ln, s):
    a, b = ln.interpolate(max(0, s - 1.0)), ln.interpolate(min(ln.length, s + 1.0))
    d = np.array([b.x - a.x, b.y - a.y])
    d /= np.hypot(*d) + 1e-9
    return np.array([-d[1], d[0]])  # left normal


def transects(ln):
    L = ln.length
    n = max(2, int(np.ceil(L / STEP)) + 1)
    return np.linspace(0, L, n)


def probe(ln, half, car, tr, others=None, wid=None):
    """Edge distances of the AV carriageway around the axis. Returns dict of arrays over the transects of the line:
    s, P (xy on axis), N (left normal), lo, hi (signed distance of right/left AV edge, NaN = no carriageway), trl, trr."""
    S = transects(ln)
    P = np.array([[ln.interpolate(s).x, ln.interpolate(s).y] for s in S])
    N = np.array([_normal(ln, s) for s in S])
    D = max(half + 7.0, 10.0)
    d = np.arange(-D, D + 1e-6, DS)
    X = P[:, 0:1] + N[:, 0:1] * d[None, :]
    Y = P[:, 1:2] + N[:, 1:2] * d[None, :]
    M = car.contains(X, Y)
    k0 = len(d) // 2
    lo = np.full(len(S), np.nan)
    hi = np.full(len(S), np.nan)
    for i in range(len(S)):
        row = M[i]
        if not row.any():
            continue
        # anchor: axis sample, else nearest carriageway sample within 2.5 m
        near = np.nonzero(row[k0 - 10:k0 + 11])[0]
        if not len(near):
            continue
        a = k0 - 10 + near[np.argmin(np.abs(near - 10))]
        b = a
        miss = 0
        j = a
        while j > 0:
            j -= 1
            if row[j]:
                b = j
                miss = 0
            else:
                miss += 1
                if miss > GAP:
                    break
        left_i = b  # lowest index in run = right side (d negative)
        b = a
        miss = 0
        j = a
        while j < len(d) - 1:
            j += 1
            if row[j]:
                b = j
                miss = 0
            else:
                miss += 1
                if miss > GAP:
                    break
        lo[i], hi[i] = d[left_i] - DS / 2, d[b] + DS / 2
    # parallel neighbour carriageways (dual carriageways / one-way pairs mapped as two ways in one AV area): split halfway
    cutl = np.zeros(len(S), bool)
    cutr = np.zeros(len(S), bool)
    if others is not None:
        tree, olines, oids = others
        segs = shapely.linestrings(np.stack([P - N * D, P + N * D], axis=1))
        qi, oi = tree.query(segs, predicate="intersects")
        for i, j in zip(qi, oi):
            if oids[j] == wid or np.isnan(lo[i]):
                continue
            for pt in shapely.get_parts(segs[i].intersection(olines[j])):
                if pt.geom_type != "Point":
                    continue
                dk = (pt.x - P[i, 0]) * N[i, 0] + (pt.y - P[i, 1]) * N[i, 1]
                if abs(dk) < 1.0:
                    continue
                t = _normal(olines[j], olines[j].project(pt))
                if abs(t @ N[i]) < 0.8:  # not parallel to this transect's normal => crossing street, ignore
                    continue
                if dk > 0 and dk / 2 < hi[i]:
                    hi[i], cutl[i] = dk / 2, True
                elif dk < 0 and dk / 2 > lo[i]:
                    lo[i], cutr[i] = dk / 2, True
    # trusted: what follows beyond each edge?
    def beyond(sign, e):
        ok = np.zeros(len(S), bool)
        for off in (0.5, 1.0):
            dd = e + sign * off
            v = ~np.isnan(dd)
            if v.any():
                q = P[v] + N[v] * dd[v, None]
                ok[v] |= tr.contains(q[:, 0], q[:, 1])
        return ok
    return {"s": S, "P": P, "N": N, "lo": lo, "hi": hi, "trl": beyond(+1, hi) | cutl, "trr": beyond(-1, lo) | cutr}


def _med(a, k=5):
    """running median over k transects, NaN-aware"""
    out = a.copy()
    h = k // 2
    for i in range(len(a)):
        w = a[max(0, i - h):i + h + 1]
        w = w[~np.isnan(w)]
        out[i] = np.median(w) if len(w) and not np.isnan(a[i]) else np.nan  # a gap stays a gap (fallback ribbon there)
    return out


def _vote(a, k=5):
    out = a.copy()
    h = k // 2
    for i in range(len(a)):
        w = a[max(0, i - h):i + h + 1]
        out[i] = w.mean() >= 0.5
    return out


def class_key(w):
    t = w["tags"]
    try:
        lanes = int(float(str(t.get("lanes", "0")).split(";")[0]))
    except ValueError:
        lanes = 0
    return (w["hw"], bool(w["oneway"]), min(lanes, 4))


def measure(ways, car, tr):
    from shapely import STRtree
    """probe() every way (service streets excepted) and compute the calibration table."""
    pr = {}
    olines = [w["line"] for w in ways if w["hw"] != "service" and w["line"].length > 5]
    oids = [w["id"] for w in ways if w["hw"] != "service" and w["line"].length > 5]
    others = (STRtree(olines), olines, oids)
    for w in ways:
        if w["hw"] == "service" or w["line"].length < 1 or w["tags"].get("bridge") not in (None, "no"):
            continue  # decks: the AV under a bridge is another street / water, keep the OSM width
        p = probe(w["line"], w["w"] / 2, car, tr, others, w["id"])
        p["lo"], p["hi"] = _med(p["lo"]), _med(p["hi"])
        p["trl"], p["trr"] = _vote(p["trl"].astype(float)).astype(bool), _vote(p["trr"].astype(float)).astype(bool)
        pr[w["id"]] = p
    samples = defaultdict(list)
    for w in ways:
        p = pr.get(w["id"])
        if p is None:
            continue
        ok = ~np.isnan(p["lo"]) & p["trl"] & p["trr"]
        if ok.any():
            wd = (p["hi"] - p["lo"])[ok]
            samples[class_key(w)] += wd.tolist()
            samples[(w["hw"],)] += wd.tolist()
    cal = {k: float(np.median(v)) for k, v in samples.items() if len(v) >= 15}
    return pr, cal


def cal_width(w, cal):
    c = cal.get(class_key(w)) or cal.get((w["hw"],))
    if c is None:
        return w["w"]
    return float(min(max(c, MINW), w["w"] * 1.25))


def edges(w, p, cal):
    """Final (lo, hi) per transect plus a 'fallback' flag (no AV carriageway there)."""
    cw = cal_width(w, cal)
    lo, hi, trl, trr = p["lo"].copy(), p["hi"].copy(), p["trl"], p["trr"]
    fb = np.isnan(lo) | (hi - lo < 1.5)
    for i in range(len(lo)):
        if fb[i]:
            continue
        if trl[i] and trr[i]:
            continue
        if trr[i] and not trl[i]:
            hi[i] = min(hi[i], lo[i] + cw)
        elif trl[i] and not trr[i]:
            lo[i] = max(lo[i], hi[i] - cw)
        else:
            mid = (lo[i] + hi[i]) / 2
            lo[i], hi[i] = max(lo[i], mid - cw / 2), min(hi[i], mid + cw / 2)
    return lo, hi, fb, cw


def _ribbon(P, N, a, b, ok):
    quads = []
    for i in range(len(P) - 1):
        if not (ok[i] and ok[i + 1]):
            continue
        pts = [P[i] + N[i] * a[i], P[i] + N[i] * b[i], P[i + 1] + N[i + 1] * b[i + 1], P[i + 1] + N[i + 1] * a[i + 1]]
        q = shapely.Polygon(pts)
        if not q.is_valid:
            q = q.buffer(0)
        if not q.is_empty:
            quads.append(q)
    return quads


def apply(ways, G):
    """Update w["w"], w["off"] of all ways from the AV; returns (cap_av, fallback) shapely geometries and stats."""
    # tram tracks inside streets are "Bahngebiet" strips in the AV, splitting the carriageway: narrow rail strips (< ~9 m) near
    # an axis belong to the road surface (the old OSM buffers covered them as well)
    near = shapely.union_all([w["line"].buffer(14) for w in ways])
    rail = G["rail"].buffer(0).intersection(near)
    strips = rail.difference(rail.buffer(-4.5).buffer(4.7))
    road = shapely.union_all([G["carriageway"].buffer(0), strips.buffer(0.15)])
    car = Mask(shapely.set_precision(road.buffer(0), 0.01))
    tr = Mask(shapely.union_all([G["sidewalk"], G["plaza"], G["green"], G["rail"]]))
    pr, cal = measure(ways, car, tr)
    caps, fbs, node_half = [], [], defaultdict(float)
    stats = {"ways": 0, "av": 0, "fb": 0}
    for w in ways:
        w["w_osm"] = w["w"]
        w["off"] = 0.0
        p = pr.get(w["id"])
        if p is None:
            fbs.append(w["line"].buffer(w["w"] / 2, cap_style="round", join_style="round", quad_segs=10))
            continue
        lo, hi, fb, cw = edges(w, p, cal)
        stats["ways"] += 1
        good = ~fb
        wd = hi - lo
        if good.sum() >= max(2, 0.5 * len(fb)):
            stats["av"] += 1
            w["w"] = float(max(np.median(wd[good]), MINW))
            w["off"] = float(np.clip(np.median(((hi + lo) / 2)[good]), -OFF_MAX, OFF_MAX))
        else:
            stats["fb"] += 1
            w["w"] = cw if w["hw"] != "service" else w["w"]
        both = p["trl"] & p["trr"]
        w["audit"] = {"av_w": float(np.nanmedian(p["hi"] - p["lo"])) if (~np.isnan(p["lo"])).any() else float("nan"),
                      "trust": float(both[~np.isnan(p["lo"])].mean()) if (~np.isnan(p["lo"])).any() else 0.0,
                      "fb": float(fb.mean()), "cal": cw, "av_c": float(np.nanmedian((p["hi"] + p["lo"]) / 2)) if (~np.isnan(p["lo"])).any() else 0.0}
        P, N = p["P"], p["N"]
        # AV-limited cap: an unchanged AV edge keeps a margin (the AV polygon itself clips), a cut edge is exact
        cl = lo - np.where(np.abs(lo - p["lo"]) < 1e-6, MARGIN, 0.0)
        ch = hi + np.where(np.abs(hi - p["hi"]) < 1e-6, MARGIN, 0.0)
        caps += _ribbon(P, N, cl, ch, good)
        # no AV under the axis: calibrated OSM ribbon around the axis (+ shifted centre if neighbours measured one)
        fw = cw if w["hw"] != "service" else w["w"]
        if fb.any():
            runs = _ribbon(P, N, np.full(len(P), -fw / 2), np.full(len(P), fw / 2), fb | np.roll(fb, 1) | np.roll(fb, -1))
            fbs += runs
        for n in (w["nodes"][0], w["nodes"][-1]):
            node_half[n] = max(node_half[n], w["w"] / 2)
    return shapely.union_all(caps) if caps else shapely.Polygon(), shapely.union_all(fbs) if fbs else shapely.Polygon(), node_half, cal, stats, car


def axis_gaps(ways, road):
    """Every OSM car way keeps a drivable surface: axis stretches (> 1.5 m) that the AV-based road does not cover (sidewalk crossings,
    AV mapping differences) get a ribbon of the measured width."""
    m = Mask(road)
    out = []
    for w in ways:
        ln = w["line"]
        n = int(ln.length) + 1
        pts = np.array([[q.x, q.y] for q in (ln.interpolate(min(s, ln.length)) for s in np.linspace(0, ln.length, n + 1))])
        ok = m.contains(pts[:, 0], pts[:, 1])
        i = 0
        while i < len(ok):
            if ok[i]:
                i += 1
                continue
            j = i
            while j < len(ok) and not ok[j]:
                j += 1
            if j - i >= 2:
                a, b = max(0.0, (i - 1) * ln.length / n), min(ln.length, j * ln.length / n)
                out.append(shapely.ops.substring(ln, a, b).buffer(w["w"] / 2, cap_style="flat"))
            i = j
    return shapely.union_all(out) if out else shapely.Polygon()


def junction_discs(ways, node_half, nodes_xy):
    """small discs at nodes where >= 2 ways meet, so the AV junction area (corners) is kept."""
    cnt = defaultdict(int)
    for w in ways:
        for n in (w["nodes"][0], w["nodes"][-1]):
            cnt[n] += 1
    return [Point(nodes_xy[n]).buffer(node_half[n] + 1.5, quad_segs=8) for n, c in cnt.items() if c >= 2 and n in nodes_xy]


def enabled():
    return os.environ.get("SBZ_CARRIAGEWAY", DEFAULT) != "osm"
