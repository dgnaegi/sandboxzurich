"""Close the open strips beside new rows (pipeline/scopes/ramp_build.py, pass 4 after the joins and the footways).

The top-down check (topcheck.py) found holes between side-by-side decks that the joins leave: a rebuilt road deck takes its
width from the cadastre carriageway while the live footway beside it keeps its old axis (Geroldrampe: a 1.7 m strip at the
same height), and a ramp running beside the main deck at another height stops short of it (2.9 m from the Hardbrücke, 1 m
lower). For every vertex side of a new row that is not flush yet, a probe walks outward from the edge up to GAP_MAX m; where it
enters another walkable deck first:
  same height (|dz| <= DZ)  the side is widened until the client's gap fill (0.75 m on flush sides) reaches the other deck
                            and flagged flush (no parapet, no railing collider) when the strip is at most FLUSH_MAX m or one
                            of the two is a footway; a wider strip between two carriageways is closed with the parapets kept
  this row lower            the side is widened to reach OVER m under the other deck's edge; the parapet stays (level change)
  this row higher           left alone: the lower deck is widened from its own side if it is a new row
Runs shorter than MIN_RUN vertices are not widened (deck ends, ramp mouths); widened runs are smoothed (running median of 3).
"""
from __future__ import annotations

import numpy as np

from join import normals

GAP_MAX = 3.5     # m
STEP = 0.25       # m, probe step
DZ = 0.25         # m, same surface: below the step the top-down check flags (join.DZ = 0.6 leaves visible steps)
OVER = 0.3        # m reach under a higher deck
GAP_FILL = 0.75   # m, the client's fill on flush sides (web/src/world/bridges.ts)
FLUSH_MAX = 1.5   # m, widest strip made flush between two carriageways (pipeline/bridges joins side-by-side decks up to this)
MIN_RUN = 2       # vertices


class Deck:
    """Footprint and height test for one row (live rows may lack per-vertex widths)."""

    def __init__(self, d):
        self.d = d
        self.P = np.array(d["p"], float)
        n = len(self.P)
        self.wl = np.array(d.get("wl") or [d["w"] / 2] * n, float)
        self.wr = np.array(d.get("wr") or [d["w"] / 2] * n, float)
        r = float(max(self.wl.max(), self.wr.max())) + 1.0
        self.box = (self.P[:, 0].min() - r, self.P[:, 1].min() - r, self.P[:, 0].max() + r, self.P[:, 1].max() + r)

    def near(self, box):
        return not (self.box[2] < box[0] or self.box[0] > box[2] or self.box[3] < box[1] or self.box[1] > box[3])

    def z_at(self, x, y):
        """Deck height at (x, y) if the point lies inside the footprint, else None."""
        P = self.P
        if len(P) < 2:
            return None
        a, b = P[:-1, :2], P[1:, :2]
        ab = b - a
        L2 = np.maximum((ab ** 2).sum(1), 1e-9)
        t = np.clip(((x - a[:, 0]) * ab[:, 0] + (y - a[:, 1]) * ab[:, 1]) / L2, 0, 1)
        fx, fy = a[:, 0] + ab[:, 0] * t - x, a[:, 1] + ab[:, 1] * t - y
        lat = (ab[:, 0] * -fy - ab[:, 1] * -fx) / np.sqrt(L2)          # > 0: point left of the axis
        hw = np.where(lat > 0, self.wl[:-1] + (self.wl[1:] - self.wl[:-1]) * t, self.wr[:-1] + (self.wr[1:] - self.wr[:-1]) * t)
        ok = np.hypot(fx, fy) <= hw
        if not ok.any():
            return None
        k = int(np.argmin(np.where(ok, np.hypot(fx, fy), np.inf)))
        return float(P[k, 2] + (P[k + 1, 2] - P[k, 2]) * t[k])


def _runs(mask):
    out, i = [], 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j + 1 < len(mask) and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def close(ours, others):
    """Widen the sides of `ours` (new rows, changed in place) toward `others` (every walkable row in the final tile set,
    `ours` included). Returns report lines."""
    idx = [Deck(d) for d in others if d.get("kind") != "rail"]
    stats = {"flush": 0, "under": 0, "m": 0.0}
    for d in ours:
        if d.get("kind") == "rail" or len(d["p"]) < 2:
            continue
        me = Deck(d)
        n = len(me.P)
        for key in ("wl", "wr", "ol", "or"):
            if not d.get(key):
                d[key] = [d["w"] / 2] * n if key in ("wl", "wr") else [0] * n
        N = normals(me.P[:, :2], d.get("pa"), d.get("pb"))
        box = (me.box[0] - GAP_MAX, me.box[1] - GAP_MAX, me.box[2] + GAP_MAX, me.box[3] + GAP_MAX)
        cand = [o for o in idx if o.d is not d and o.near(box)]
        for side, wk, fk in ((1, "wl", "ol"), (-1, "wr", "or")):
            ext, flush = np.zeros(n), np.zeros(n, bool)
            for i in range(n):
                if d[fk][i]:
                    continue
                e = me.P[i, :2] + side * N[i] * d[wk][i]
                for g in np.arange(STEP, GAP_MAX + 1e-9, STEP):
                    q = e + side * N[i] * g
                    hit = next(((z, o) for z, o in ((o.z_at(q[0], q[1]), o) for o in cand) if z is not None), None)
                    if hit is None:
                        continue
                    dz = me.P[i, 2] - hit[0]
                    if abs(dz) <= DZ and (g <= FLUSH_MAX or "foot" in (d.get("kind"), hit[1].d.get("kind"))):
                        ext[i], flush[i] = max(0.0, g - GAP_FILL) + 0.05, True
                    elif abs(dz) <= DZ:                 # wider strip between two carriageways: closed, parapets stay (median)
                        ext[i] = g
                    elif dz < 0:
                        ext[i] = g + OVER
                    break
            for i0, i1 in _runs(ext > 0):
                if i1 - i0 + 1 < MIN_RUN:
                    ext[i0:i1 + 1] = 0; flush[i0:i1 + 1] = False
            sm = ext.copy()
            for i in range(1, n - 1):
                if ext[i] > 0:
                    sm[i] = float(np.median(ext[i - 1:i + 2])) or ext[i]
            for i in range(n):
                if sm[i] > 0:
                    d[wk][i] = round(float(d[wk][i] + sm[i]), 2)
                    if flush[i]:
                        d[fk][i] = 1
            stats["flush"] += int(flush.sum()); stats["under"] += int(((sm > 0) & ~flush).sum()); stats["m"] += float(sm.sum())
    return [f"- side gaps closed: {stats['flush']} vertex sides widened flush to a deck at the same height, {stats['under']} "
            f"closed with the parapet kept (under a higher deck, or up to a parallel carriageway; {stats['m']:.0f} m of width added in total)"]
