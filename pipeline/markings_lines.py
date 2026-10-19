"""Longitudinal road markings as continuous lines (research/lines.md).
Problem of the old per-way code: every OSM way restarted the dash phase, got a 6 m gap at both ends (even where the street continues), dashes were cut
to stubs by junction gaps / tram, the axis was the raw OSM polyline (kinks at nodes) shifted by one constant offset per way.
Here: (1) ways of one street are chained (same name + class, ends within 0.5 m, aligned, exactly two ends at that point) to one smooth polyline whose
lateral offset blends between the ways' measured carriageway offsets; (2) the centre line is placed in the free intervals between junctions / zebras /
tram / chain ends and fitted there (dash 3 m, gap 6 m +-, a dash at both ends, no stubs); (3) bike/bus lines are cut from the same smooth line.
Swiss dimensions: Leitlinie 3 m dash / 6 m gap in town, 0.12 m wide (research/lines.md)."""
from collections import defaultdict
import numpy as np
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import substring

DASH, GAP, HALF_W = 3.0, 6.0, 0.06
JOIN_R, BLEND, SMOOTH = 0.6, 8.0, 3


def _tan_out(line, end):
    """Unit tangent pointing out of the way at its start (end=0) or end (end=1)."""
    L = line.length
    a, b = (line.interpolate(0), line.interpolate(min(2.0, L))) if end == 0 else (line.interpolate(L), line.interpolate(max(0.0, L - 2.0)))
    d = np.array([a.x - b.x, a.y - b.y]) if end == 1 else np.array([a.x - b.x, a.y - b.y])
    return d / (np.hypot(*d) + 1e-9)


def build_chains(S):
    """S['_chains'] = list of chains; each {'ways': [(w, rev)], 's0': [...], 'line': smooth centre polyline (carriageway centre), 'L': axis length};
    w['_ch'] = (chain, s0, rev). Cached in S."""
    if "_chains" in S:
        return S["_chains"]
    ways = [w for w in S["ways"] if w["hw"] != "service" and w["zone"] not in ("beg", "fuss") and w["line"].length > 0.5]
    ends = defaultdict(list)
    for w in ways:
        ln = w["line"]
        for e in (0, 1):
            p = ln.interpolate(0 if e == 0 else ln.length)
            ends[(round(p.x / JOIN_R), round(p.y / JOIN_R))].append((w, e, p))
    # a end point may sit on a rounding boundary: look into the 3x3 neighbourhood
    def near(w, e, p):
        out = []
        kx, ky = round(p.x / JOIN_R), round(p.y / JOIN_R)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for (o, oe, op) in ends.get((kx + dx, ky + dy), []):
                    if (o is not w or oe != e) and op.distance(p) < JOIN_R:
                        out.append((o, oe))
        return out
    link = {}
    for w in ways:
        for e in (0, 1):
            p = w["line"].interpolate(0 if e == 0 else w["line"].length)
            nb = near(w, e, p)
            if len(nb) != 1:
                continue
            o, oe = nb[0]
            if o is w or o["hw"] != w["hw"] or o["name"] != w["name"] or o["oneway"] != w["oneway"]:
                continue
            if float(np.dot(_tan_out(w["line"], e), _tan_out(o["line"], oe))) > -0.6:  # must continue straight-ish (< ~53 deg turn)
                continue
            link[(id(w), e)] = (o, oe)
    for k, (o, oe) in list(link.items()):
        if link.get((id(o), oe), (None,))[0] is None or id(link[(id(o), oe)][0]) != k[0]:
            link.pop(k)
    chains, seen = [], set()
    byid = {id(w): w for w in ways}

    def walk(w, rev):
        seq, cur, r = [], w, rev
        while cur is not None and id(cur) not in seen:
            seen.add(id(cur)); seq.append((cur, r))
            exit_end = 0 if r else 1
            nxt = link.get((id(cur), exit_end))
            if nxt is None:
                break
            cur, r = nxt[0], (nxt[1] == 1)  # entering at its end 1 means we traverse it reversed
        return seq
    for w in ways:  # chain starts: ways with an unlinked start
        if id(w) in seen:
            continue
        if (id(w), 0) not in link:
            _make(chains, walk(w, False))
        elif (id(w), 1) not in link:
            _make(chains, walk(w, True))
    for w in ways:  # rings
        if id(w) not in seen:
            _make(chains, walk(w, False))
    S["_chains"] = chains
    return chains


def _make(chains, seq):
    if not seq:
        return
    pts, s0, s = [], [], 0.0
    for w, rev in seq:
        c = list(w["line"].coords)
        c = c[::-1] if rev else c
        s0.append(s); s += w["line"].length
        pts += c if not pts else c[1:]
    ax = LineString(pts)
    L = ax.length
    n = max(3, int(np.ceil(L / 1.0)) + 1)
    ss = np.linspace(0, L, n)
    P = np.array([(p.x, p.y) for p in shapely.line_interpolate_point(ax, ss)])
    # moving-average smoothing, ends fixed (window shrinks towards the ends)
    Q = P.copy()
    for i in range(1, n - 1):
        k = min(SMOOTH, i, n - 1 - i)
        Q[i] = P[i - k:i + k + 1].mean(axis=0)
    T = np.gradient(Q, axis=0); T /= np.hypot(T[:, 0], T[:, 1])[:, None] + 1e-9
    N = np.stack([-T[:, 1], T[:, 0]], axis=1)
    # lateral offset: each way's measured carriageway offset (left of way direction), mirrored when traversed reversed; linear blend at joins
    off = np.zeros(n)
    for (w, rev), a in zip(seq, s0):
        o = -w.get("off", 0.0) if rev else w.get("off", 0.0)
        off[(ss >= a) & (ss <= a + w["line"].length + 1e-6)] = o
    for i in range(1, len(seq)):
        j = s0[i]; ob, oa = (-seq[i - 1][0].get("off", 0.0) if seq[i - 1][1] else seq[i - 1][0].get("off", 0.0)), (-seq[i][0].get("off", 0.0) if seq[i][1] else seq[i][0].get("off", 0.0))
        h = min(BLEND, seq[i - 1][0]["line"].length / 2, seq[i][0]["line"].length / 2)
        m = (ss > j - h) & (ss < j + h)
        off[m] = ob + (oa - ob) * (ss[m] - (j - h)) / (2 * h)
    C = Q + N * off[:, None]
    line = LineString(C)
    ch = {"ways": seq, "s0": s0, "L": L, "line": line, "k": line.length / max(L, 1e-6)}
    for (w, rev), a in zip(seq, s0):
        w["_ch"] = (ch, a, rev)
    chains.append(ch)


def way_line(S, w):
    """Smooth carriageway centre line of one way in way direction (replaces streets.mline for markings); falls back to mline."""
    import streets
    build_chains(S)
    c = w.get("_ch")
    if c is None:
        return streets.mline(w)
    ch, a, rev = c
    L = w["line"].length
    sub = substring(ch["line"], a * ch["k"], (a + L) * ch["k"])
    if sub.geom_type != "LineString" or sub.is_empty:
        return streets.mline(w)
    if rev:
        sub = LineString(list(sub.coords)[::-1])
    return sub


def fit_dashes(a, b, dash=DASH, gap=GAP):
    """Dash intervals filling [a, b]: dash at both ends, equal gaps (4.5..8 m for 3/6), no stubs. [] if shorter than one dash."""
    L = b - a
    if L < dash - 0.05:
        return []
    n = max(1, int(round((L + gap) / (dash + gap))))
    while n > 1 and (L - n * dash) / (n - 1) < 0.75 * gap:
        n -= 1
    if n == 1:
        return [(a + (L - dash) / 2, a + (L + dash) / 2)] if L < 2 * dash + 0.75 * gap else [(a, a + dash), (b - dash, b)]
    g = (L - n * dash) / (n - 1)
    return [(a + i * (dash + g), a + i * (dash + g) + dash) for i in range(n)]


def _mask_intervals(line, geom, step=0.5, pad=1.0):
    """Intervals along line (s) where it is within geom."""
    n = max(2, int(line.length / step) + 1)
    s = np.linspace(0, line.length, n)
    p = shapely.line_interpolate_point(line, s)
    hit = shapely.intersects(geom, p)
    out, i = [], 0
    while i < n:
        if hit[i]:
            j = i
            while j + 1 < n and hit[j + 1]:
                j += 1
            out.append((s[i] - pad, s[j] + pad)); i = j + 1
        else:
            i += 1
    return out


def centre_lines(S, eligible, extra_gaps, tram):
    """White dashed centre lines as polygons.
    eligible(w) -> bool for the centre line; extra_gaps: {id(w): [(s0, s1)]} in way coordinates (zebras)."""
    import streets
    out = []
    for ch in build_chains(S):
        ws = [(w, rev, a) for (w, rev), a in zip(ch["ways"], ch["s0"])]
        # eligible ways of the chain -> runs of consecutive eligible ways
        runs, cur = [], None
        for w, rev, a in ws:
            if eligible(w):
                if cur is None:
                    cur = [a, a + w["line"].length]; runs.append(cur)
                else:
                    cur[1] = a + w["line"].length
            else:
                cur = None
        if not runs:
            continue
        gaps = []
        for w, rev, a in ws:
            L = w["line"].length
            for g0, g1 in w["gaps_main"]:
                gaps.append((a + (L - g1 if rev else g0), a + (L - g0 if rev else g1)))
            for g0, g1 in extra_gaps.get(id(w), []):
                gaps.append((a + (L - g1 if rev else g0), a + (L - g0 if rev else g1)))
        line = ch["line"]; k = ch["k"]
        gaps.sort()
        for ra, rb in runs:
            # chain ends keep the 3 m clearance of the old code (they are junctions / dead ends)
            iv = [(ra + (3.0 if ra <= 0.01 else 0.0), rb - (3.0 if rb >= ch["L"] - 0.01 else 0.0))]
            if tram is not None:
                seg = substring(line, ra * k, rb * k)
                tg = [(ra + a / k, ra + b / k) for a, b in _mask_intervals(seg, tram, pad=0.8)]
                gaps_all = sorted(gaps + tg)
            else:
                gaps_all = gaps
            for a, b in streets._minus(iv, gaps_all):
                for d0, d1 in fit_dashes(a, b):
                    sg = substring(line, d0 * k, d1 * k)
                    if sg.geom_type == "LineString" and sg.length > 0.5:
                        out.append(sg.buffer(HALF_W, cap_style="flat"))
    return out


def lane_lines(S, lane_fn, extra_gaps, tram):
    """Broken lines between the lanes of one direction on multi-lane ways. lane_fn(w) -> (lanes, lane_width) or None."""
    import streets
    out = []
    build_chains(S)
    for w in S["ways"]:
        lf = lane_fn(w) if w["hw"] != "service" else None
        if not lf or "_ch" not in w:
            continue
        lanes, lw = lf
        ch, a, rev = w["_ch"]
        L = w["line"].length
        ml = way_line(S, w)
        # way ends that continue into another way of the chain get no clearance
        start_free = (a <= 0.01) if not rev else (a + L >= ch["L"] - 0.01)
        end_free = (a + L >= ch["L"] - 0.01) if not rev else (a <= 0.01)
        gaps = list(w["gaps_main"]) + list(extra_gaps.get(id(w), [])) + ([(-3, 3)] if start_free else []) + ([(L - 3, L + 3)] if end_free else [])
        if tram is not None:
            gaps += [(x - 0.0, y) for x, y in _mask_intervals(ml, tram, pad=0.8)]
        gaps.sort()
        iv = streets._minus([(0, L)], gaps)
        for kk in range(1, lanes // 2):
            for sgn in (1, -1):
                off = ml.offset_curve(sgn * kk * lw)
                if off.is_empty or off.geom_type != "LineString":
                    continue
                kf = off.length / max(L, 1e-6)
                for a2, b2 in iv:
                    for d0, d1 in fit_dashes(a2, b2):
                        sg = substring(off, d0 * kf, d1 * kf)
                        if sg.geom_type == "LineString" and sg.length > 0.5:
                            out.append(sg.buffer(HALF_W, cap_style="flat"))
    return out
