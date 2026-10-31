"""Join new ramp rows with the decks they meet at an angle.

pipeline/bridges._open_sides flags a vertex side (`ol` / `or`) only where another deck runs side by side (near-parallel, gap
<= 1.5 m, same height); a ramp meeting a deck at an angle is never joined, so the main deck's parapet and railing collider run
across the ramp's mouth (Geroldrampe at the Hardbrücke). This applies the same idea in both directions:
  ramp rows   a vertex side whose edge point lies inside another road / tram deck at the same height is flushed
  other rows  where a new ramp footprint covers a deck's edge, vertices are inserted at the mouth boundaries and the vertices
              inside the mouth are flagged on that side (the client opens a segment only when both vertices are flagged)
"""
from __future__ import annotations

import numpy as np

GAP = 1.0    # m: a footprint this close to the other deck's edge counts as touching (the client fills 0.75 m)
DZ = 0.6     # m: height difference up to which two decks are one surface
NEAR = 60.0  # m: other rows considered around a new deck


def normals(P, pa=None, pb=None):
    """Left normals per vertex; at the ends the neighbouring vertices of the adjacent row (`pa`, `pb`) make the normals continuous
    across a tile boundary, as the client's offsets() does."""
    n = len(P); N = np.zeros((n, 2))
    for i in range(n):
        a = P[i - 1] if i > 0 else (np.asarray(pa[:2], float) if pa is not None else P[0])
        b = P[i + 1] if i < n - 1 else (np.asarray(pb[:2], float) if pb is not None else P[n - 1])
        t = b - a; t = t / (np.hypot(t[0], t[1]) or 1.0)
        N[i] = (-t[1], t[0])
    return N


def footprint(P, wl, wr, pa=None, pb=None):
    import shapely
    from shapely.geometry import Polygon
    N = normals(P, pa, pb); quads = []
    for i in range(len(P) - 1):
        q = Polygon([P[i] + N[i] * wl[i], P[i + 1] + N[i + 1] * wl[i + 1], P[i + 1] - N[i + 1] * wr[i + 1], P[i] - N[i] * wr[i]])
        q = q if q.is_valid else q.buffer(0)
        if not q.is_empty:
            quads.append(q)
    return shapely.union_all(quads) if quads else Polygon()


class Other:
    def __init__(self, tile, k, row):
        from shapely.geometry import LineString
        self.tile, self.k, self.row = tile, k, row
        self.P = np.array(row["p"], float); self.axis = LineString(self.P[:, :2])
        self.cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(self.P[:, :2], axis=0).T))])
        hw = row["w"] / 2
        self.wl = np.array(row.get("wl") or [hw] * len(self.P), float); self.wr = np.array(row.get("wr") or [hw] * len(self.P), float)
        self.fp = footprint(self.P[:, :2], self.wl, self.wr)

    def z_at(self, x, y):
        s = self.axis.project(__import__("shapely.geometry", fromlist=["Point"]).Point(x, y))
        return float(np.interp(s, self.cum, self.P[:, 2]))


def join(decks, rows, site_keys, extra=(), base=None):
    """decks: new deck dicts (p, wl, wr, ol, or, kind); rows: rows.Rows (live metadata); site_keys: (tile, k) of the live rows
    that are rebuilt (this site's, or every site's in a multi-site run). `extra`: new deck dicts of other sites, joined like live
    decks and modified in place; `base`: {(tile, k): row} already modified by an earlier join (openings accumulate).
    Flags the new decks in place; returns {(tile, k): modified row} for the other live decks and a list of report lines."""
    import shapely
    from shapely.geometry import LineString, Point
    lines = []
    new = [(d, np.array(d["p"], float), np.array(d["wl"], float), np.array(d["wr"], float)) for d in decks]
    fps = [footprint(P[:, :2], wl, wr) for _, P, wl, wr in new]
    allfp = shapely.union_all(fps)
    others = []
    for t, k, r in rows.decks():
        if (t, k) in site_keys or r["kind"] not in ("road", "tram"):
            continue
        r = (base or {}).get((t, k), r)
        Q = np.array(r["p"], float)
        if allfp.distance(LineString(Q[:, :2])) > NEAR:
            continue
        others.append(Other(t, k, r))
    for d in extra:                                   # other sites' new decks (multi-site run)
        if d["kind"] in ("road", "tram") and allfp.distance(LineString(np.array(d["p"], float)[:, :2])) <= NEAR:
            o = Other("", -1, d); o.deck = d; others.append(o)
    # 1. ramp vertices on another deck: flush
    n_flush = 0
    for d, P, wl, wr in new:
        N = normals(P[:, :2])
        for i in range(len(P)):
            for side, key, hw in ((1, "ol", wl[i]), (-1, "or", wr[i])):
                if d[key][i]:
                    continue
                e = P[i, :2] + N[i] * hw * side
                for o in others:
                    if o.fp.buffer(GAP).contains(Point(e)) and abs(o.z_at(*e) - P[i, 2]) < DZ:
                        q = o.axis.interpolate(o.axis.project(Point(e)))               # the other deck must lie beside, not inside
                        if abs(float((np.array([q.x, q.y]) - P[i, :2]) @ N[i])) < hw - 0.3:
                            continue
                        d[key][i] = 1; n_flush += 1
                        break
    # 1b. the site's own chains against each other: a side whose edge lies in a sibling's footprint (fork nose, overlap) is flush
    n_self = 0
    for d, P, wl, wr in new:
        N = normals(P[:, :2])
        sib = [(fp2, P2) for (d2, P2, _, _), fp2 in zip(new, fps) if d2 is not d]
        for i in range(len(P)):
            for side, key, hw in ((1, "ol", wl[i]), (-1, "or", wr[i])):
                if d[key][i]:
                    continue
                e = P[i, :2] + N[i] * hw * side
                for fp2, P2 in sib:
                    if fp2.buffer(GAP).contains(Point(e)):
                        j = int(np.hypot(P2[:, 0] - e[0], P2[:, 1] - e[1]).argmin())
                        if abs(P2[j, 2] - P[i, 2]) < DZ:
                            d[key][i] = 1; n_self += 1
                            break
    # 2. other decks: open the mouth where a new ramp footprint covers their edge
    modified = {}
    for o in others:
        if open_mouths(o, allfp, new, lines, f"{o.row.get('name') or o.row['kind']} ({o.tile or 'new'} row {o.k})"):
            if getattr(o, "deck", None) is not None:
                for key in ("p", "g", "b", "wl", "wr", "ol", "or"):
                    o.deck[key] = o.row[key]
            else:
                modified[(o.tile, o.k)] = o.row
    # 2b. the site's own chains: a sibling's footprint over a chain's edge (a branch leaving the main chain) opens that stretch
    n_mouth = 0
    for idx, (d, P, wl, wr) in enumerate(new):
        sib = [fp for j, fp in enumerate(fps) if j != idx]
        if not sib:
            continue
        o = Other("", idx, d)
        if open_mouths(o, shapely.union_all(sib), [t for j, t in enumerate(new) if j != idx], lines, f"{d.get('name') or d['kind']} chain {idx}"):
            for key in ("p", "g", "b", "wl", "wr", "ol", "or"):
                d[key] = o.row[key]
            n_mouth += 1
    lines.insert(0, f"- join: {n_flush} ramp vertex sides flushed on other decks, {n_self} on sibling chains, {len(modified)} other rows and {n_mouth} site chains opened at a mouth")
    return modified, lines


def open_mouths(o, cover, decks_z, lines, label):
    """Open the sides of row `o` where `cover` (a union of deck footprints) lies over its edge: vertices are inserted at the
    boundaries of each covered stretch and the vertices inside are flagged on that side, if the covering deck is at the same
    height (`decks_z`: (deck, P, wl, wr) tuples whose nearest vertex gives the height). Returns True when the row changed."""
    from shapely.geometry import LineString, Point
    changed = False
    for side, key in ((1, "ol"), (-1, "or")):
        N = normals(o.P[:, :2]); hw = o.wl if side > 0 else o.wr
        edge = LineString(o.P[:, :2] + N * (hw * side)[:, None])
        cov = edge.intersection(cover.buffer(GAP))
        pieces = [g for g in getattr(cov, "geoms", [cov]) if not g.is_empty and g.geom_type == "LineString" and g.length > 1.0]
        for g in pieces:
            c = np.asarray(g.coords)
            sa, sb = sorted((o.axis.project(Point(c[0])), o.axis.project(Point(c[-1]))))
            mid = c[len(c) // 2]
            zo = float(np.interp(o.axis.project(Point(mid)), o.cum, o.P[:, 2]))
            dz = min(abs(zo - P[int(np.hypot(P[:, 0] - mid[0], P[:, 1] - mid[1]).argmin()), 2]) for _, P, _, _ in decks_z)
            if dz >= DZ:
                continue
            o.row = insert_vertices(o.row, o.cum, (sa, sb))
            o.P = np.array(o.row["p"], float); o.cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(o.P[:, :2], axis=0).T))])
            hw2 = o.row["w"] / 2
            o.wl = np.array(o.row.get("wl") or [hw2] * len(o.P), float); o.wr = np.array(o.row.get("wr") or [hw2] * len(o.P), float)
            o.row.setdefault("ol", [0] * len(o.P)); o.row.setdefault("or", [0] * len(o.P))
            flags = o.row[key]
            for i in range(len(o.P)):
                if sa - 0.05 <= o.cum[i] <= sb + 0.05:
                    flags[i] = 1
            changed = True
            lines.append(f"  - opened {label} {'left' if side > 0 else 'right'} side over {sb - sa:.1f} m at s {sa:.0f}–{sb:.0f}")
    return changed


def insert_vertices(row, cum, ss, tol=0.5):
    """Insert vertices at chainages ss (metres along the row) unless one exists within tol; interpolates p, g, b, wl, wr; copies flags."""
    row = dict(row)
    P = np.array(row["p"], float)
    for s in ss:
        cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P[:, :2], axis=0).T))])
        if np.min(np.abs(cum - s)) < tol or s <= 0 or s >= cum[-1]:
            continue
        j = int(np.searchsorted(cum, s)); t = (s - cum[j - 1]) / ((cum[j] - cum[j - 1]) or 1.0)
        lerp = lambda a, b: a + (b - a) * t
        P = np.insert(P, j, lerp(P[j - 1], P[j]), axis=0)
        row["p"] = [[round(float(v), 2) for v in q] for q in P]
        for key in ("g", "b", "wl", "wr"):
            if key in row:
                row[key] = row[key][:j] + [round(float(lerp(row[key][j - 1], row[key][j])), 2)] + row[key][j:]
        for key in ("ol", "or"):
            if key in row:
                row[key] = row[key][:j] + [row[key][j - 1] if row[key][j - 1] == row[key][j] else 0] + row[key][j:]
    return row
