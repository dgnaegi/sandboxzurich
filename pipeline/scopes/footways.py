"""Footway decks beside rebuilt road decks (pipeline/scopes/ramp_build.py calls `rebuild` after the joins).

The builder rebuilds road rows; the live footway rows next to them keep the old geometry and can end in the air where the road
deck changed (Kornhausbrücke: a sidewalk on the approach embankment follows the LiDAR ground exactly but stops 2.4 m above a game
terrain 6.7 m too low). For every live foot row within NEAR of a new road deck:
  trim    the stretch inside the new road footprint is dropped (the road deck carries the footway); a vertex is inserted where
          the row leaves the footprint, so the remaining piece starts at the road deck's edge
  heights kept (the live footway heights are LiDAR-fitted); where the vertex has no LiDAR bridge class beneath and stands above
          the game terrain, the underside goes to the terrain (solid embankment, not a floating slab)
  ends    an end in the air (no other deck within JUNCTION) is continued straight on along the LiDAR ground, tracked from the end
          height, until that surface meets the game terrain (at most EXT m), solid underneath
"""
from __future__ import annotations

import numpy as np

import lidar
import metrics as M

NEAR = 15.0       # m: footways this close to a new road deck are rebuilt
MIN_PIECE = 3.0   # m: shorter remaining pieces are dropped
JUNCTION = 2.5
AT_GRADE = 0.3
EXT = 60.0
STEP = 2.0


def _seglen(P):
    return float(np.hypot(*np.diff(P[:, :2], axis=0).T).sum()) if len(P) > 1 else 0.0


def _cut_at_boundary(a, b, fp):
    """Point where segment a->b crosses the footprint boundary (fraction along the segment)."""
    from shapely.geometry import LineString
    x = LineString([a[:2], b[:2]]).intersection(fp.boundary)
    pts = [np.array(g.coords[0]) for g in getattr(x, "geoms", [x]) if not g.is_empty]
    if not pts:
        return 0.5
    L = np.hypot(*(b[:2] - a[:2])) or 1.0
    return float(min(np.hypot(*(q - a[:2])) for q in pts) / L)


def rebuild(new_decks, rows, skip_keys, ground):
    """new_decks: rebuilt road deck dicts (all sites); rows: rows.Rows (live); skip_keys: (tile, k) already dropped;
    ground(x, y): game terrain. Returns ({(tile, k): [deck dicts]}, report lines)."""
    import shapely
    from shapely.geometry import LineString, Point
    from join import footprint
    roads = [d for d in new_decks if d["kind"] in ("road", "tram")]
    if not roads:
        return {}, []
    fp = shapely.union_all([footprint(np.array(d["p"], float)[:, :2], np.array(d["wl"], float), np.array(d["wr"], float)) for d in roads])
    near = fp.buffer(NEAR)
    allpts = np.array([q[:2] for t, k, d in rows.decks() if d["kind"] != "rail" for q in d["p"]] +
                      [q[:2] for d in new_decks for q in d["p"]], float)
    out, lines, n_ext, n_trim = {}, [], 0, 0
    for t, k, d in rows.decks():
        if d["kind"] != "foot" or (t, k) in skip_keys or len(d["p"]) < 2:
            continue
        P = np.array(d["p"], float); G = np.array(d["g"], float); B = np.array(d["b"], float)
        if not near.intersects(LineString(P[:, :2])):
            continue
        inside = np.array([fp.contains(Point(x, y)) for x, y in P[:, :2]])
        # pieces of consecutive outside vertices, each extended to the footprint edge where it touches an inside vertex
        pieces, i = [], 0
        while i < len(P):
            if inside[i]:
                i += 1; continue
            j = i
            while j + 1 < len(P) and not inside[j + 1]:
                j += 1
            idx = list(range(i, j + 1)); pts, gs, bs = [P[q] for q in idx], [G[q] for q in idx], [B[q] for q in idx]
            joint = [False, False]
            if i > 0:
                f = _cut_at_boundary(P[i], P[i - 1], fp); pts.insert(0, P[i] + (P[i - 1] - P[i]) * f)
                gs.insert(0, G[i] + (G[i - 1] - G[i]) * f); bs.insert(0, B[i] + (B[i - 1] - B[i]) * f); joint[0] = True
            if j < len(P) - 1:
                f = _cut_at_boundary(P[j], P[j + 1], fp); pts.append(P[j] + (P[j + 1] - P[j]) * f)
                gs.append(G[j] + (G[j + 1] - G[j]) * f); bs.append(B[j] + (B[j + 1] - B[j]) * f); joint[1] = True
            pieces.append((np.array(pts), np.array(gs), np.array(bs), joint))
            i = j + 1
        changed = inside.any()
        new_rows = []
        for Q, g, b, joint in pieces:
            if _seglen(Q) < MIN_PIECE:
                continue
            # air ends: continue along the LiDAR ground until it meets the game terrain
            for end in (0, -1):
                if joint[0 if end == 0 else 1]:
                    continue
                e = Q[end]
                if e[2] - ground(e[0], e[1]) <= AT_GRADE:
                    continue
                dd = np.hypot(allpts[:, 0] - e[0], allpts[:, 1] - e[1])
                if (dd < JUNCTION).sum() > 2:        # other decks meet this end (its own two neighbouring vertices aside)
                    continue
                prev = Q[1] if end == 0 else Q[-2]
                v = e[:2] - prev[:2]; v = v / (np.hypot(*v) or 1.0); nv = np.array([-v[1], v[0]])
                ext, zp = [], float(e[2])
                for s in np.arange(STEP, EXT + 1e-9, STEP):
                    q = e[:2] + v * s
                    zl, fl = M.lidar_strip(q, nv, d["w"] / 2, d["w"] / 2, zp)
                    gq = float(ground(q[0], q[1]))
                    if not np.isfinite(zl):
                        break
                    zl = max(min(zl, zp + 0.12 * STEP), zp - 0.12 * STEP)   # footway slope limit
                    ext.append((q[0], q[1], zl, gq)); zp = zl
                    if zl - gq < AT_GRADE:
                        break
                if not ext or ext[-1][2] - ext[-1][3] >= AT_GRADE:
                    lines.append(f"  - footway end at ({e[0]:.0f},{e[1]:.0f}) {e[2] - ground(e[0], e[1]):+.1f} m: no grade along the LiDAR ground within {EXT:.0f} m, left as is")
                    continue
                E = np.array([[x, y, z] for x, y, z, _ in ext]); Eg = np.array([gq for *_, gq in ext])
                if end == 0:
                    Q = np.vstack([E[::-1], Q]); g = np.concatenate([Eg[::-1], g]); b = np.concatenate([Eg[::-1], b])
                else:
                    Q = np.vstack([Q, E]); g = np.concatenate([g, Eg]); b = np.concatenate([b, Eg])
                n_ext += 1; changed = True
                lines.append(f"  - footway end at ({e[0]:.0f},{e[1]:.0f}) {e[2] - ground(e[0], e[1]):+.1f} m above the game terrain continued {_seglen(E) + STEP:.0f} m along the LiDAR ground to grade")
            # solid where there is no bridge class beneath (embankment), terrain from the game
            gg = np.array([float(ground(x, y)) for x, y in Q[:, :2]]); gg = np.where(np.isfinite(gg), gg, g)
            br = lidar.bridge(Q[:, 0], Q[:, 1])
            solid = ~np.isfinite(br) & (Q[:, 2] - gg > AT_GRADE)
            if solid.any():
                changed = True
            b = np.where(solid, gg, np.minimum(b, Q[:, 2] - 0.2))
            n = len(Q)
            new_rows.append({"p": [[round(float(x), 2), round(float(y), 2), round(float(z), 2)] for x, y, z in Q],
                             "g": [round(float(v), 2) for v in gg], "b": [round(float(v), 2) for v in b], "w": d["w"],
                             "wl": [d["w"] / 2] * n, "wr": [d["w"] / 2] * n, "ol": [0] * n, "or": [0] * n,
                             "kind": "foot", "name": d.get("name", ""), "site": "footway"})
        if changed:
            out[(t, k)] = new_rows
            n_trim += int(inside.any())
    lines.insert(0, f"- footways beside new decks: {len(out)} rows rebuilt ({n_trim} trimmed at a new deck, {n_ext} air ends continued to grade)")
    return out, lines
