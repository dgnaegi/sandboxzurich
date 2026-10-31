"""One surface per structure (pipeline/scopes/ramp_build.py, pass 4 before gaps.close).

Each chain gets its heights from its own LiDAR strip tracker, so where several new rows lie on one structure (Hardbrücke south
end: two carriageway chains, the footways and a ramp mouth over each other) they disagree by 0.3-0.5 m: the body stands on a
lower row inside the drawn one (sinking) and the parapets between them stay closed (railings in the carriageway). Here every
vertex of a new row that lies on a LiDAR bridge surface takes the height of that surface at its own position (median of the
bridge-class cells within RADIUS m), so rows on the same structure meet at the same height wherever they overlap; gaps.close
then finds them at one level and makes the joints flush. A vertex whose row runs more than MATCH m off that surface belongs to
another level (a ramp passing underneath) and keeps its height. Changes are smoothed along the row (running median of 3) and
faded out over FADE vertices where the row leaves the structure, so no step appears at the edge of the bridge surface.

foot_on_road: a wide road row is flat across, a footway beside it follows the surface at its own axis; where the footway
overlaps the road's edge it is drawn above the road (up to 0.4 m at Hardplatz) while the client stands the body on the road
(road decks win over footways): the body sinks into the drawn footway. There the footway takes the road's height (faded).

to_edge: a road row whose cadastre width stops short of the structure (Hardbrücke south end: 3.6 m short, a railing where the
real carriageway goes on) is widened on each closed side as far as the LiDAR bridge surface continues at its height (within
EDGE_DZ, at most EDGE_MAX m); runs shorter than 2 vertices are left, widened runs smoothed (median of 3).
"""
from __future__ import annotations

import numpy as np

import lidar

RADIUS = 2.0      # m, LiDAR cells per vertex
MIN_SHARE = 0.3   # share of bridge-class cells in the disk for a vertex to be on the structure
MATCH = 1.5       # m, a row farther off the surface is on another level
FADE = 5          # vertices (2 m each)
EDGE_DZ = 0.4     # m, the bridge surface still belongs to this row's level
EDGE_MAX = 5.0    # m, widest extension to the structure's edge
EDGE_MIN = 1.0    # m, shorter extensions are left (outline noise)

_OFF = np.array([(dx, dy) for dx in np.arange(-RADIUS, RADIUS + 1e-9, 0.5) for dy in np.arange(-RADIUS, RADIUS + 1e-9, 0.5)
                 if dx * dx + dy * dy <= RADIUS * RADIUS])


def surface_at(P):
    """LiDAR bridge surface (median within RADIUS) at each (x, y) of P, NaN where the vertex is not on a bridge surface."""
    X = (P[:, None, 0] + _OFF[None, :, 0]).ravel()
    Y = (P[:, None, 1] + _OFF[None, :, 1]).ravel()
    B = lidar.bridge(X, Y).reshape(len(P), len(_OFF))
    ok = np.isfinite(B)
    med = np.array([np.median(b[o]) if o.mean() >= MIN_SHARE else np.nan for b, o in zip(B, ok)])
    return med


def shared(ours):
    """Move the vertices of `ours` (new rows, changed in place) onto the shared LiDAR bridge surface. Returns report lines."""
    moved, rows, dmax = 0, 0, 0.0
    for d in ours:
        if d.get("kind") == "rail" or len(d["p"]) < 3:
            continue
        P = np.array(d["p"], float)
        n = len(P)
        H = surface_at(P[:, :2])
        on = np.isfinite(H) & (np.abs(H - P[:, 2]) <= MATCH)
        if not on.any():
            continue
        delta = np.where(on, np.nan_to_num(H) - P[:, 2], 0.0)
        sm = delta.copy()                                   # running median of 3 inside the structure (single noisy cells)
        for i in range(1, n - 1):
            if on[i]:
                sm[i] = float(np.median(delta[i - 1:i + 2]))
        # fade out beyond the structure: linear over FADE vertices from the last vertex on it
        dist = np.full(n, np.inf)
        idx = np.flatnonzero(on)
        for i in range(n):
            dist[i] = np.min(np.abs(idx - i))
        w = np.clip(1 - dist / (FADE + 1), 0, 1)
        nearest = np.array([sm[idx[np.argmin(np.abs(idx - i))]] for i in range(n)])
        final = np.where(on, sm, nearest * w)
        ch = np.abs(final) > 0.01
        if not ch.any():
            continue
        for i in np.flatnonzero(ch):
            d["p"][i][2] = round(float(d["p"][i][2] + final[i]), 2)
            d["b"][i] = round(float(d["b"][i] + final[i]), 2)
        moved += int(ch.sum()); rows += 1; dmax = max(dmax, float(np.abs(final).max()))
    return [f"- shared bridge surface: {moved} vertices of {rows} rows moved onto the LiDAR bridge surface (largest change {dmax:.2f} m)"]


def foot_on_road(ours, others):
    """Footway rows of `ours` follow the road / tram row they overlap (heights changed in place). Returns report lines."""
    from gaps import Deck
    from join import normals
    roads = [Deck(o) for o in others if o.get("kind") in ("road", "tram")]
    moved = 0
    for d in ours:
        if d.get("kind") != "foot" or len(d["p"]) < 2:
            continue
        P = np.array(d["p"], float)
        n = len(P)
        N = normals(P[:, :2], d.get("pa"), d.get("pb"))
        wl = np.array(d.get("wl") or [d["w"] / 2] * n, float); wr = np.array(d.get("wr") or [d["w"] / 2] * n, float)
        box = (P[:, 0].min() - 15, P[:, 1].min() - 15, P[:, 0].max() + 15, P[:, 1].max() + 15)
        cand = [r for r in roads if r.near(box)]
        target = np.full(n, np.nan)
        for i in range(n):
            for o in (0.0, wl[i] * 0.8, -wr[i] * 0.8):              # axis, near the left and the right edge
                q = P[i, :2] + N[i] * o
                zs = [z for z in (r.z_at(q[0], q[1]) for r in cand) if z is not None and abs(z - P[i, 2]) <= MATCH]
                if zs:
                    target[i] = min(zs, key=lambda z: abs(z - P[i, 2]))
                    break
        hit = np.isfinite(target)
        if not hit.any():
            continue
        delta = np.where(hit, target - P[:, 2], 0.0)
        idx = np.flatnonzero(hit)
        dist = np.array([np.min(np.abs(idx - i)) for i in range(n)])
        nearest = np.array([delta[idx[np.argmin(np.abs(idx - i))]] for i in range(n)])
        final = np.where(hit, delta, nearest * np.clip(1 - dist / (FADE + 1), 0, 1))
        for i in np.flatnonzero(np.abs(final) > 0.01):
            d["p"][i][2] = round(float(d["p"][i][2] + final[i]), 2)
            d["b"][i] = round(float(d["b"][i] + final[i]), 2)
            moved += 1
    return [f"- footways on road rows: {moved} footway vertices moved to the height of the road row they overlap"]


def to_edge(ours):
    """Widen the closed sides of new road rows to the edge of the LiDAR bridge surface at their height. Returns report lines."""
    from join import normals
    from gaps import _runs
    added, sides = 0.0, 0
    for d in ours:
        if d.get("kind") not in ("road", "tram") or len(d["p"]) < 3:
            continue
        P = np.array(d["p"], float)
        n = len(P)
        N = normals(P[:, :2], d.get("pa"), d.get("pb"))
        for sgn, wk, fk in ((1, "wl", "ol"), (-1, "wr", "or")):
            ext = np.zeros(n)
            steps = np.arange(0.5, EDGE_MAX + 1e-9, 0.5)
            for i in range(n):
                if d[fk][i]:
                    continue
                e = P[i, :2] + sgn * N[i] * d[wk][i]
                Q = e[None, :] + sgn * N[i][None, :] * steps[:, None]
                H = lidar.bridge(Q[:, 0], Q[:, 1])
                good = np.isfinite(H) & (np.abs(H - P[i, 2]) <= EDGE_DZ)
                k = int(np.argmin(good)) if not good.all() else len(good)   # first step off the surface
                ext[i] = steps[k - 1] if k > 0 else 0.0
            ext[ext < EDGE_MIN] = 0.0
            for i0, i1 in _runs(ext > 0):
                if i1 - i0 + 1 < 2:
                    ext[i0:i1 + 1] = 0
            sm = ext.copy()
            for i in range(1, n - 1):
                if ext[i] > 0:
                    sm[i] = float(np.median(ext[i - 1:i + 2])) or ext[i]
            for i in np.flatnonzero(sm > 0):
                d[wk][i] = round(float(d[wk][i] + sm[i]), 2)
            added += float(sm.sum()); sides += int((sm > 0).sum())
    return [f"- road rows widened to the bridge surface edge: {sides} vertex sides, {added:.0f} m of width in total"]

