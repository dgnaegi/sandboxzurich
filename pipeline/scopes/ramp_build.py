"""Builder v2: ramp deck rows from the cadastre outline (Scope B) and LiDAR heights (Scope A), on the built tile metadata.

Replaces pipeline/ramp_lidar.py's band tracker as the primary path (research/bridges/scopes_plan.md §4):
  axis     stays on the OSM axis of the live rows (traffic, routes and the road graph follow it); no tracking
  edges    per 2 m station the normal is cast across the cadastre: the narrowest «Brücke» polygon containing the axis, or the
           span between two thin «Brücke» edge polygons (ramp on fill), gives the left / right half widths (`wl` / `wr`); where
           the cadastre has no bridge object, flanking «Mauer» faces within 12 m do (abutment between wing walls). Where another site
           chain lies in the same slice (fork, parallel branch) the slice is split halfway and that side is flagged flush (`ol` /
           `or`, no parapet); a side reaching more than 12 m from the axis is the main deck, not this ramp: width locked to the
           live width + 1.5 m and flagged flush. Without a cadastre object the live width stays.
  heights  LiDAR: 35th percentile of the class-17 deck top in the central strip of the modelled width, tracked along the axis
           so a crossing deck's samples are rejected (rail flyover over the Duttweilerbrücke), else the class-2 ground (fill /
           at grade); smoothed, slope-limited, never below the game terrain; junction and fork ends blend to the connecting
           deck's height, grade ends onto the terrain
  kinds    deck (free underside, `b` = z − thickness) where the cadastre has a bridge polygon or LiDAR sees a deck; solid
           (`b` = terrain) between edge polygons, where walls flank the edge, or where there is no bridge class above the ground;
           at grade below 0.3 m
  ends     an end in the air that meets no other deck is continued along the road graph while the surface stays above the
           terrain (Duttweiler south: the walled abutment); a fork end takes the main chain's height
  piers    cadastre «Pfeiler» polygons under elevated deck sections become pier rows at their real position and width; the
           rule-spaced piers of the live rows under the new footprint are dropped
  props    footway rows inside the new footprint, street furniture and static collision polygons under elevated decks are dropped
  joins    pipeline/scopes/join.py: ramp vertices on another deck are flushed, the other deck's parapet is opened over the
           ramp's mouth (vertices inserted at the mouth boundaries), so the join is one surface and drivable
Usage:  python3 pipeline/scopes/ramp_build.py <site>[,<site>] [--tiles web/public/tiles] [--write] [--report file.md]
With --write the tiles are rewritten from web/public/tiles_orig/<tile>.json (kept once, as the pilot), so a re-run replaces.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import lidar  # noqa: E402
import metrics as M  # noqa: E402
import ramp_lidar as RL  # noqa: E402
import scope_av  # noqa: E402
from ramp_sites import site as site_cfg  # noqa: E402
from rows import Rows, Chain, is_site_row  # noqa: E402
import join as J  # noqa: E402

STEP = 2.0
EXT = 80.0          # m: longest continuation beyond an air end
LANDING_R = 35.0    # m: graph landing nodes this close to a grade end seed approaches
GRADE_RUN = 3       # stations at grade in a row that make a landing
CAD_EXT = 20.0      # m: a grade end follows the cadastre structure (edge polygons, walls) this far at most
GRADE_EXT = 60.0    # m: a grade end follows the cadastre structure (edge polygons, walls) or a terrain hole this far at most
SIDE_MAX = 20.0     # m: a cadastre edge further than this from the axis belongs to the main deck (other decks and siblings already cut the slice)
SIDE_MIN = 1.2
W_STEP = 4.0        # m per station: width rate limit (the cadastre edge caps it; skewed crossings need fast widening)
MAX_SLOPE = 0.12
AT_GRADE = 0.3
BLEND = 10.0        # m: height blend at junction / fork ends
END_FLUSH = 6.0     # m: within this of a fork / junction end both sides are flush (no railing piece at the nose)
EDGE_TOL = 0.3      # m: smoothing may not push a deck edge further than this beyond the measured cadastre edge
COPLANAR = 8.0      # m: a branch this close to the main chain's axis takes its height (one surface where a car changes lanes)
# sibling chains split their shared cadastre slice at the Voronoi boundary (metrics.voronoi_cap): no gore, no overlap
PIER_MIN_EL = 0.8      # m: a cadastre pier under a deck at least this high is modelled (short piers are real too)
PARTNER_TOL = 1.0      # m: a junction partner further than this off the LiDAR surface is reported, not followed
THICK = {"road": 1.0, "tram": 1.0, "foot": 0.5}


def rate_limit(v, r):
    v = v.copy()
    for i in range(1, len(v)):
        v[i] = min(max(v[i], v[i - 1] - r), v[i - 1] + r)
    for i in range(len(v) - 2, -1, -1):
        v[i] = min(max(v[i], v[i + 1] - r), v[i + 1] + r)
    return v


def axis_offsets(p, n, axes, half=M.HALF):
    """Lateral offsets (along the normal through p) where other chain axes cross the normal line."""
    from shapely.geometry import LineString
    L = LineString([p - n * half, p + n * half]); out = []
    for ax in axes:
        q = L.intersection(ax)
        for g in getattr(q, "geoms", [q]):
            if g.is_empty:
                continue
            c = np.asarray(g.coords)[0] if g.geom_type != "Point" else np.array([g.x, g.y])
            out.append(float((c - p) @ n))
    return out


class Build:
    def __init__(self, name, tiles_dir):
        self.cfg = site_cfg(name); self.av = scope_av.load(name)
        self.R = Rows(tiles_dir, "live"); self.chains = self.R.site_chains(self.cfg)
        self.site_keys = {(t, k) for c in self.chains for t, k, _ in c.rows}
        self.decks_av, self.wall_u = self.av.geoms("deck"), self.av.union("wall")
        self.road_av = self.av.union("carriageway")
        self.taken = M.deck_cover(self.R, self.cfg["fetch"], kinds=("road",), exclude=lambda t, k, d: (t, k) in self.site_keys)
        self.lines = []; self.findings = []

    def stations(self, c):
        """Live stations plus continuations beyond air ends; returns dict of arrays and the end kinds."""
        from shapely.geometry import LineString
        st = c.stations(STEP)
        xy, z0, g, wl0, wr0, s = st["xy"], st["z"], st["g"], st["wl"], st["wr"], st["s"]
        ends = dict(c.ends)
        for end in (0, -1):
            if ends[end] not in ("air", "grade"):
                continue
            C = self.R.extend(c, end, EXT if ends[end] == "air" else GRADE_EXT)
            C, t = RL.resample(C, STEP); C, t = C[1:], t[1:]
            if not len(C):
                continue
            if ends[end] == "grade":   # at grade already: follow the cadastre structure (edge polygons, walls) to its end, at most GRADE_EXT
                keep = 0
                for i in range(len(C)):
                    if t[i] > CAD_EXT:
                        break
                    nv = self._nrm(C, i)
                    sv = M.structure(M.deck_slices(C[i], nv, self.decks_av))
                    gl, gr = M.nearest_side(M.intervals(C[i], nv, self.wall_u), wl0[end], wr0[end])
                    if sv or (gl is not None and abs(gl) <= M.WALL_NEAR) or (gr is not None and abs(gr) <= M.WALL_NEAR):
                        keep = i + 1
                    else:
                        break
                if keep == 0:
                    keep = self.hole_run(C, t, float(z0[end]), wl0[end], wr0[end])   # terrain hole beyond the end: follow the LiDAR ground
                    if keep == 0:
                        continue
                    self.lines.append(f"  - grade {'end' if end == -1 else 'start'}: the game terrain beyond lies below the LiDAR ground (terrain hole); "
                                      f"continued {t[keep - 1]:.0f} m along the road graph on the LiDAR ground until it meets the terrain")
                C, t = C[:keep], t[:keep]
                gc = RL.fill_nan(self.R.ground(C[:, 0], C[:, 1]), t)
                if end == -1:
                    xy = np.vstack([xy, C]); z0 = np.concatenate([z0, np.full(keep, np.nan)]); g = np.concatenate([g, gc])
                    wl0 = np.concatenate([wl0, np.full(keep, wl0[-1])]); wr0 = np.concatenate([wr0, np.full(keep, wr0[-1])]); s = np.concatenate([s, s[-1] + t])
                else:
                    xy = np.vstack([C[::-1], xy]); z0 = np.concatenate([np.full(keep, np.nan), z0]); g = np.concatenate([gc[::-1], g])
                    wl0 = np.concatenate([np.full(keep, wl0[0]), wl0]); wr0 = np.concatenate([np.full(keep, wr0[0]), wr0]); s = np.concatenate([s[0] - t[::-1], s])
                self.lines.append(f"  - grade {'end' if end == -1 else 'start'} extended {t[keep - 1]:.0f} m to the end of the cadastre structure")
                continue
            gc = RL.fill_nan(self.R.ground(C[:, 0], C[:, 1]), t)
            zp = float(z0[end]); zc = np.full(len(C), np.nan)
            for i in range(len(C)):
                zc[i], _ = M.lidar_strip(C[i], self._nrm(C, i), wl0[end], wr0[end], zp)
                if np.isfinite(zc[i]):
                    zp = zc[i]
            zc = np.maximum(RL.smooth(RL.fill_nan(zc, t), 5), gc)
            # grade = the surface stays at grade over GRADE_RUN stations (one high terrain sample inside a terrain hole is not a landing)
            low = (zc - gc) < AT_GRADE
            hit = next((i for i in range(len(C)) if low[i:i + GRADE_RUN].all() and (i + GRADE_RUN <= len(C) or i == len(C) - 1)), None)
            if hit is None:
                self.lines.append(f"  - continuation at ({C[0,0]:.0f},{C[0,1]:.0f}): no grade within {EXT:.0f} m, end stays in the air")
                continue
            keep = slice(0, hit + 1)
            fill = lambda v, k: np.full(hit + 1, v[k])
            if end == -1:
                xy = np.vstack([xy, C[keep]]); z0 = np.concatenate([z0, np.full(hit + 1, np.nan)]); g = np.concatenate([g, gc[keep]])
                wl0 = np.concatenate([wl0, fill(wl0, -1)]); wr0 = np.concatenate([wr0, fill(wr0, -1)]); s = np.concatenate([s, s[-1] + t[keep]])
            else:
                xy = np.vstack([C[keep][::-1], xy]); z0 = np.concatenate([np.full(hit + 1, np.nan), z0]); g = np.concatenate([gc[keep][::-1], g])
                wl0 = np.concatenate([fill(wl0, 0), wl0]); wr0 = np.concatenate([fill(wr0, 0), wr0]); s = np.concatenate([s[0] - t[keep][::-1], s])
            ends[end] = "grade"
            self.lines.append(f"  - continuation at {'end' if end == -1 else 'start'}: {t[hit]:.0f} m along the road graph to grade")
        nrm, tan = c.normals(xy)
        return {"xy": xy, "z0": z0, "g": g, "wl0": wl0, "wr0": wr0, "s": s - s[0], "nrm": nrm, "tan": tan}, ends

    def approaches(self, decks):
        """Approach decks over terrain holes: from every grade end of the site's decks, each road-graph edge leaving a node within
        LANDING_R that the new decks do not cover (at-grade roads, and OSM deck edges beyond the deck rows) is followed on the LiDAR
        surface while the game terrain lies more than AT_GRADE below it (Kornhausbrücke: the OSM deck runs on beyond the deck rows
        over a 3 m terrain hole). Solid, at most GRADE_EXT m long."""
        import shapely
        roads = self.R.roads if self.R.roads is not None else RL.Roads()
        self.R.roads = roads
        cover = shapely.union_all([J.footprint(np.array(d["p"], float)[:, :2], np.array(d["wl"], float), np.array(d["wr"], float)) for d in decks]).buffer(0.5)
        out = []
        for d in list(decks):
            for end, kind in d["_ends"].items():
                if kind != "grade":
                    continue
                e = np.array(d["p"][0 if end == 0 else -1], float)
                dn = np.hypot(roads.nodes[:, 0] - e[0], roads.nodes[:, 1] - e[1])
                is_deck = lambda i: bool(roads.edges[i].get("z")) and any(v is not None for v in roads.edges[i]["z"])
                # the graph's landing nodes near this end: the node at the end, or nodes within LANDING_R where a deck edge meets an
                # at-grade edge (the OSM deck often runs on beyond the deck rows, Kornhausbrücke 20 m)
                seeds = [int(n) for n in np.argsort(dn) if dn[n] <= LANDING_R]
                for node in seeds:
                    lead = [] if dn[node] <= 3.0 else [roads.nodes[node].tolist()]
                    for i in roads.adj.get(node, []):
                        edge = roads.edges[i]
                        P = roads.pts(i, node)
                        if len(P) < 2 or self.covered(P, cover):
                            continue                                    # the new decks carry this edge (or it runs under them)
                        v = np.array(P[1], float) - np.array(P[0], float); v = v / (np.linalg.norm(v) or 1.0)
                        cont = roads.continue_from(roads.nodes[node], v, GRADE_EXT)
                        if not cont:
                            continue
                        C, t = RL.resample(np.vstack([e[None, :2]] + ([np.array(lead, float)] if lead else []) + [np.array(cont, float)]), STEP)
                        w = max(1.6, float(edge.get("w") or 6.0) / 2)
                        from shapely.geometry import Point
                        if np.mean([cover.contains(Point(*q)) for q in C]) > 0.4:
                            continue                                    # mostly on the new decks: the bridge's own edge
                        zs, gs, zp = [], [], float(e[2])
                        for k in range(len(C)):                         # LiDAR surface along the path; ground class only (bridge class = a deck)
                            zl, fl = M.lidar_strip(C[k], self._nrm(C, k), w, w, zp)
                            gq = float(self.R.ground(C[k:k + 1, 0], C[k:k + 1, 1])[0])
                            if not np.isfinite(zl) or not np.isfinite(gq) or fl != 2:
                                break
                            if zs:
                                zl = max(min(zl, zp + MAX_SLOPE * STEP), zp - MAX_SLOPE * STEP)
                            zp = zl; zs.append(zl); gs.append(gq)
                        diff = np.array(zs) - np.array(gs) if zs else np.zeros(0)
                        h = next((k for k in range(len(diff)) if diff[k] > AT_GRADE), None)
                        if h is None:
                            continue
                        k0 = max(0, h - 1)
                        k1 = next((k for k in range(h + 1, len(diff)) if (diff[k:k + GRADE_RUN] <= AT_GRADE).all()), None)
                        if k1 is None or k1 - k0 < 2:
                            continue                                    # the hole does not close within GRADE_EXT: terrain pass
                        C, t = C[k0:k1 + 1], t[k0:k1 + 1] - t[k0]; zs, gs = zs[k0:k1 + 1], gs[k0:k1 + 1]
                        n = len(zs); Q = C[:n]; gg = np.array(gs)
                        # width from the cadastre carriageway («Strasse, Weg») around the axis, else 3 m each side
                        wls, wrs = [], []
                        for k in range(n):
                            nv = self._nrm(Q, k); iv = M.containing(M.intervals(Q[k], nv, self.road_av), 0.0, 0.5)
                            wls.append(float(np.clip(iv[1], 1.6, 8.0)) if iv else 3.0); wrs.append(float(np.clip(-iv[0], 1.6, 8.0)) if iv else 3.0)
                        wls = RL.smooth(np.array(wls), 3); wrs = RL.smooth(np.array(wrs), 3)
                        zz = np.maximum(np.array(zs), gg)
                        flush = [1] * n                                  # a street on the embankment: no kerb, parapet or railing
                        out.append({"p": [[round(float(x), 2), round(float(y), 2), round(float(z), 2)] for (x, y), z in zip(Q, zz)],
                                    "g": [round(float(v), 2) for v in gg], "b": [round(float(v), 2) for v in gg], "w": round(float(np.median(wls + wrs)), 1),
                                    "wl": [round(float(v), 2) for v in wls], "wr": [round(float(v), 2) for v in wrs], "ol": flush, "or": list(flush), "kind": "road", "role": "approach",
                                    "name": d["name"], "site": self.cfg["name"], "_kind": np.ones(n, int), "_mode": np.zeros(n, int),
                                    "_flag": np.full(n, 2), "_thick": 1.0, "_ends": {0: "joint", -1: "grade"}, "_s": t[:n], "_tan": self._tans(Q)})
                        poly = __import__("shapely.geometry", fromlist=["LineString"]).LineString(Q)
                        if any(poly.hausdorff_distance(__import__("shapely.geometry", fromlist=["LineString"]).LineString(np.array(a["p"])[:, :2])) < 4.0 for a in out[:-1]):
                            out.pop(); continue                         # the same road as car and bike edge
                        self.lines.append(f"  - approach over a terrain hole from ({e[0]:.0f},{e[1]:.0f}): {t[n - 1]:.0f} m along an at-grade road on the LiDAR ground, "
                                          f"up to {float(np.max(zz - gg)):.1f} m above the game terrain")
        return out

    @staticmethod
    def covered(P, cover, probe=8.0):
        """Is the first `probe` m of polyline P (from its start node) inside the new decks' footprint?"""
        from shapely.geometry import LineString
        ln = LineString(P)
        pts = [ln.interpolate(min(x, ln.length)) for x in (2.0, 4.0, 6.0, probe)]
        return sum(cover.contains(q) for q in pts) >= 3

    @staticmethod
    def _tans(Q):
        T = np.zeros((len(Q), 2))
        for i in range(len(Q)):
            a = Q[max(i - 1, 0)]; b = Q[min(i + 1, len(Q) - 1)]; v = b - a; T[i] = v / (np.linalg.norm(v) or 1.0)
        return T

    def hole_run(self, C, t, z_end, wl, wr):
        """Number of continuation stations (along C) on which the LiDAR ground stays above the game terrain by more than
        AT_GRADE, starting right after a grade end; 0 when the terrain is fine there. Includes the first station at grade."""
        zp = z_end; n = 0
        for i in range(len(C)):
            zl, _ = M.lidar_strip(C[i], self._nrm(C, i), wl, wr, zp)
            gq = float(self.R.ground(C[i:i + 1, 0], C[i:i + 1, 1])[0])
            if not np.isfinite(zl) or not np.isfinite(gq):
                return 0 if n == 0 else n
            n = i + 1; zp = zl
            if zl - gq <= AT_GRADE:
                return 0 if i == 0 else n
        return n

    @staticmethod
    def _nrm(C, i):
        a = C[max(i - 1, 0)]; b = C[min(i + 1, len(C) - 1)]; t = b - a; t = t / (np.hypot(t[0], t[1]) or 1.0)
        return np.array([-t[1], t[0]])

    def widths(self, st, c, other_axes, ends=None):
        from shapely.geometry import LineString
        own_axis = LineString(st["xy"])
        n = len(st["s"]); wl = st["wl0"].copy(); wr = st["wr0"].copy()
        mode = np.zeros(n, int); fl = np.zeros(n, int); fr = np.zeros(n, int); gl = np.full(n, np.nan); gr = np.full(n, np.nan)
        split = np.zeros(n, bool); cap_l = np.full(n, np.inf); cap_r = np.full(n, np.inf)
        for i in range(n):
            p, nv = st["xy"][i], st["nrm"][i]
            sv = M.structure(M.deck_slices(p, nv, self.decks_av))
            if sv:
                lo, hi, mode[i] = sv
                lo, hi, on_other = M.cut_by_taken(p, nv, lo, hi, self.taken)     # other road decks: the slice ends at their edge
                L, Rr = hi, -lo
                cap_l[i] = min(cap_l[i], L + EDGE_TOL); cap_r[i] = min(cap_r[i], Rr + EDGE_TOL)   # the cadastre edge is a hard limit
                if on_other:                                                      # on the main deck itself: a lane, flush both sides
                    L = min(L, st["wl0"][i] + 1.5); Rr = min(Rr, st["wr0"][i] + 1.5); fl[i] = fr[i] = 1
                    cap_l[i] = min(cap_l[i], L); cap_r[i] = min(cap_r[i], Rr)
                if other_axes:                                 # another site chain in the slice: the side ends at the Voronoi boundary
                    cl = M.voronoi_cap(p, nv, own_axis, other_axes, L)
                    if cl is not None:
                        L = min(L, cl); fl[i] = 1; split[i] = True; cap_l[i] = min(cap_l[i], cl)
                    cr = M.voronoi_cap(p, -nv, own_axis, other_axes, Rr)
                    if cr is not None:
                        Rr = min(Rr, cr); fr[i] = 1; split[i] = True; cap_r[i] = min(cap_r[i], cr)
                if L > SIDE_MAX:                               # still reaching far after the sibling split: the main deck, not this ramp's edge
                    L = st["wl0"][i] + 1.5; fl[i] = 1; cap_l[i] = min(cap_l[i], L)
                if Rr > SIDE_MAX:
                    Rr = st["wr0"][i] + 1.5; fr[i] = 1; cap_r[i] = min(cap_r[i], Rr)
                wl[i], wr[i] = L, Rr
            gl[i], gr[i] = [np.nan if v is None else v for v in M.nearest_side(M.intervals(p, nv, self.wall_u), wl[i], wr[i])]
            if not sv:                                                 # no bridge object: flanking walls are the structure's edges
                if np.isfinite(gl[i]) and SIDE_MIN < gl[i] + wl[i] <= SIDE_MAX:
                    wl[i] = gl[i] + wl[i]; gl[i] = 0.0
                if np.isfinite(gr[i]) and SIDE_MIN < gr[i] + wr[i] <= SIDE_MAX:
                    wr[i] = gr[i] + wr[i]; gr[i] = 0.0
        wl = rate_limit(RL.smooth(np.clip(wl, SIDE_MIN, SIDE_MAX), 3), W_STEP); wr = rate_limit(RL.smooth(np.clip(wr, SIDE_MIN, SIDE_MAX), 3), W_STEP)
        wl = np.maximum(np.minimum(wl, cap_l), SIDE_MIN); wr = np.maximum(np.minimum(wr, cap_r), SIDE_MIN)   # a split or a lock is a hard edge, not smoothed
        for end, kind in (ends or {}).items():                 # the nose of a fork and the mouth on a main deck carry no railing
            if kind in ("fork", "junction"):
                j = 0 if end == 0 else n - 1
                near = np.abs(st["s"] - st["s"][j]) <= END_FLUSH
                fl[near] = 1; fr[near] = 1
        self.split = split
        return wl, wr, mode, fl, fr, gl, gr

    def heights(self, st, wl, wr, ends, c):
        n = len(st["s"]); s, g = st["s"], st["g"]
        i0 = int(np.flatnonzero(np.isfinite(st["z0"]))[0])          # first live station: its height is a grade or junction height
        z, flag = M.lidar_track(st["xy"], st["nrm"], wl, wr, i0, float(st["z0"][i0]))
        self.z_raw = z.copy()
        z = RL.fill_nan(z, s); z = RL.smooth(z, 5); z = np.maximum(z, g); z = RL.rate_limit(z, s, MAX_SLOPE); z = np.maximum(z, g)
        for end, kind in ends.items():
            j = 0 if end == 0 else n - 1
            if kind in ("junction", "fork") and np.isfinite(st["z0"][j]):
                target = st["z0"][j] if kind == "junction" else self.fork_z(st["xy"][j], c)
                off = target - z[j]
                if kind == "junction" and abs(off) > PARTNER_TOL:   # the connecting deck is off the LiDAR surface: its error, not ours
                    self.lines.append(f"  - FINDING: junction partner at ({st['xy'][j][0]:.0f},{st['xy'][j][1]:.0f}) lies {off:+.1f} m off the LiDAR deck "
                                      f"surface; ramp kept on LiDAR, the partner deck needs its own fix")
                    self.findings.append((self.cfg["name"], float(st["xy"][j][0]), float(st["xy"][j][1]), round(float(off), 1)))
                    continue
                L = max(BLEND, abs(off) / (MAX_SLOPE * 0.6))           # the blend itself respects the slope limit
                k = np.clip(1 - np.abs(s - s[j]) / L, 0, 1); z = z + off * k
            elif kind == "grade":
                e = z[j] - g[j]
                if 0 < e <= 1.5:
                    k = np.clip(1 - np.abs(s - s[j]) / BLEND, 0, 1); z = np.maximum(z - e * k, g)
        return z, flag

    def coplanar(self, z, st, c, z_raw):
        """Where this chain shares its slice with an already built site chain (fork, parallel branch) it takes that chain's
        height, so the two decks meet without a step where a car changes from one to the other."""
        from shapely.geometry import LineString, Point
        done = [self.built[o] for o in self.chains if o is not c and o in self.built]
        if not done:
            return z
        axes = []
        for d in done:
            Q = np.array(d["p"], float); cum = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q[:, :2], axis=0).T))])
            axes.append((LineString(Q[:, :2]), cum, Q[:, 2]))
        z = z.copy(); z_own = z.copy(); taken_ = np.zeros(len(z), bool)
        for i in range(len(z)):                   # every station near an already built chain's axis (fork nose, overlap, split)
            pt = Point(*st["xy"][i]); best = None
            for ax, cum, zz in axes:
                dist = ax.distance(pt)
                if dist < COPLANAR and (best is None or dist < best[0]):
                    zs = float(np.interp(ax.project(pt), cum, zz))
                    ref = z_raw[i] if np.isfinite(z_raw[i]) else z[i]
                    if abs(zs - ref) < 0.35:                     # one surface only where the LiDAR itself agrees (not two ramps side by side at different grades)
                        best = (dist, zs)
            if best:
                z[i] = best[1]; taken_[i] = True
        # ease the step where a station leaves the sibling's level: carry the offset into the own stations, decaying over BLEND
        s_ = st["s"]
        for i in range(len(z)):
            if not taken_[i]:
                continue
            for d_ in (1, -1):
                j = i + d_
                if 0 <= j < len(z) and not taken_[j]:
                    off = z[i] - z_own[i]
                    k = j
                    while 0 <= k < len(z) and not taken_[k] and abs(s_[k] - s_[i]) < BLEND:
                        z[k] = z_own[k] + off * (1 - abs(s_[k] - s_[i]) / BLEND); k += d_
        return z

    def fork_z(self, p, c):
        """Height of the longest other site chain at the fork point (built first, so its z is final)."""
        for o in self.chains:
            if o is c or o not in self.built:
                continue
            Q = np.array(self.built[o]["p"], float); d = np.hypot(Q[:, 0] - p[0], Q[:, 1] - p[1]); j = int(d.argmin())
            if d[j] < M.HALF:
                return float(Q[j, 2])
        return float(c.P[0, 2] if np.allclose(p, c.P[0, :2]) else c.P[-1, 2])

    def kinds(self, z, g, mode, flag, gl, gr, thick):
        e = z - g
        wall = (np.abs(np.nan_to_num(gl, nan=99)) <= M.WALL_NEAR) | (np.abs(np.nan_to_num(gr, nan=99)) <= M.WALL_NEAR)
        solid = (mode == 2) | ((mode == 0) & (flag != 1)) | wall
        solid = RL.smooth(solid.astype(float), 3) >= 0.5
        kind = np.where(e < AT_GRADE, 0, np.where(solid, 1, 2))
        b = np.where(kind == 0, g - 0.25, np.where(kind == 1, g, z - thick))
        return kind, b

    def build(self, do_join=True):
        self.built = {}
        axes = {c: __import__("shapely.geometry", fromlist=["LineString"]).LineString(c.P[:, :2]) for c in self.chains}
        decks = []
        for c in self.chains:
            thick = float(np.median(c.P[:, 2] - c.B)); thick = thick if 0.2 < thick < 3 else THICK.get(c.kind, 1.0)
            self.lines.append(f"- chain {c}")
            st, ends = self.stations(c)
            wl, wr, mode, fl, fr, gl, gr = self.widths(st, c, [a for o, a in axes.items() if o is not c], ends)
            z, flag = self.heights(st, wl, wr, ends, c)
            z = self.coplanar(z, st, c, self.z_raw)
            kind, b = self.kinds(z, st["g"], mode, flag, gl, gr, thick)
            d = {"p": [[round(float(x), 2), round(float(y), 2), round(float(v), 2)] for (x, y), v in zip(st["xy"], z)],
                 "g": [round(float(v), 2) for v in st["g"]], "b": [round(float(v), 2) for v in b], "w": round(float(np.median(wl + wr)), 1),
                 "wl": [round(float(v), 2) for v in wl], "wr": [round(float(v), 2) for v in wr], "ol": fl.tolist(), "or": fr.tolist(),
                 "kind": c.kind, "name": c.name, "site": self.cfg["name"], "_kind": kind, "_mode": mode, "_flag": flag, "_thick": thick, "_ends": ends, "_s": st["s"], "_tan": st["tan"]}
            self.built[c] = d; decks.append(d)
            w = wl + wr; L = len(kind) * STEP
            self.lines.append(f"  - {L:.0f} m, width {w.min():.1f}/{np.median(w):.1f}/{w.max():.1f} m (min/med/max; live {c.P.shape[0]} vertices, {np.median(c.WL + c.WR):.1f} m); "
                              f"cadastre edges at {int((mode > 0).sum()) * STEP:.0f} m (edge pairs {int((mode == 2).sum()) * STEP:.0f} m); flush left/right {int(fl.sum()) * STEP:.0f}/{int(fr.sum()) * STEP:.0f} m; "
                              f"grade/solid/deck {int((kind == 0).sum()) * STEP:.0f}/{int((kind == 1).sum()) * STEP:.0f}/{int((kind == 2).sum()) * STEP:.0f} m; "
                              f"ends {ends[0]}/{ends[-1]} at {z[0] - st['g'][0]:+.1f}/{z[-1] - st['g'][-1]:+.1f} m above ground; max slope {np.max(np.abs(np.diff(z)) / STEP) * 100:.0f} % at s {st['s'][int(np.argmax(np.abs(np.diff(z))))]:.0f}")
        decks += self.approaches(decks)
        piers, dropped = self.piers(decks)
        self.lines.append(f"- piers: {len(piers)} from the cadastre under elevated deck sections, {dropped} live rule-spaced piers dropped")
        drop = self.footways(decks)
        if drop:
            self.lines.append(f"- footway rows inside the new footprint dropped: {len(drop)}")
        self.decks = decks
        if do_join:
            self.modified, jl = J.join(decks, self.R, self.sel)
            self.lines += jl
        return decks, piers, drop

    def piers(self, decks):
        from shapely.geometry import LineString, Point
        axes = [LineString(np.array(d["p"], float)[:, :2]) for d in decks]
        out = []
        for g in self.av.geoms("pier"):
            if min(ax.distance(g) for ax in axes) > 12:
                continue
            c = g.centroid; best = None
            for d in decks:
                Q = np.array(d["p"], float); dd = np.hypot(Q[:, 0] - c.x, Q[:, 1] - c.y); j = int(dd.argmin())
                if best is None or dd[j] < best[0]:
                    best = (dd[j], d, j)
            _, d, j = best
            Q = np.array(d["p"], float); t = d["_tan"][j]; nv = np.array([-t[1], t[0]])
            lat = float((np.array([c.x, c.y]) - Q[j, :2]) @ nv)
            if not (-d["wr"][j] - 0.5 <= lat <= d["wl"][j] + 0.5) or d["_kind"][j] != 2:
                continue
            gz = float(self.R.ground(np.array([c.x]), np.array([c.y]))[0]); gz = d["g"][j] if not np.isfinite(gz) else gz
            if Q[j, 2] - gz < PIER_MIN_EL:
                continue
            offs = (np.asarray(g.exterior.coords) - Q[j, :2]) @ nv
            out.append([round(c.x, 2), round(c.y, 2), round(gz - 0.3, 2), round(float(Q[j, 2] - d["_thick"]), 2),
                        round(float(np.clip(offs.max() - offs.min(), 0.6, 6.0)), 2), round(math.atan2(t[1], t[0]), 3), d["kind"]])
        kinds = {d["kind"] for d in decks} | {"foot"}   # foot: piers of the footway rows the new footprint replaces
        dropped = [q for q in self.R.piers() if q[6] in kinds and any(RL.lateral_inside(d, q[0], q[1], -3.0) for d in decks)]
        self.dropped_piers = {(round(q[0], 2), round(q[1], 2)) for q in dropped}
        return out, len(dropped)

    def footways(self, decks):
        sel = {(t, k) for t, k, d in self.R.decks() if (t, k) in self.site_keys}
        drop = set()
        for t, k, d in self.R.decks():
            if d["kind"] != "foot" or (t, k) in sel:
                continue
            P = np.array(d["p"], float)
            inside = sum(1 for p in P if any(RL.lateral_inside(dk, p[0], p[1], 0.3, p[2], 1.5) for dk in decks))
            if inside >= 0.7 * len(P):
                drop.add((t, k))
        self.sel = sel
        return drop


def drop_colliders(meta, decks):
    """Static collision polygons (tile key `colliders`: posts, kiosks, pillars) under an elevated new deck are removed like the
    props: the car collision is two-dimensional, a post under the deck would stop a car on the deck (Geroldrampe fork nose)."""
    rows = meta.get("colliders")
    if not isinstance(rows, list) or not rows:
        return 0
    keep, n = [], 0
    for poly in rows:
        try:
            cx = sum(q[0] for q in poly) / len(poly); cy = sum(q[1] for q in poly) / len(poly)
        except Exception:  # noqa: BLE001
            keep.append(poly); continue
        if any(RL.lateral_inside(dk, cx, cy, -1.0) and RL.deck_el(dk, cx, cy) >= 2.2 for dk in decks):
            n += 1; continue
        keep.append(poly)
    meta["colliders"] = keep
    return n


def cut_rows(deck, tiles):
    """Per-tile rows (segment midpoint decides the tile), keeping wl/wr/ol/or per vertex."""
    p = deck["p"]; runs, cur, cur_t = [], [], None
    for i in range(len(p) - 1):
        t = tiles.name_at((p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2)
        if cur and t == cur_t:
            cur.append(i + 1)
        else:
            if cur:
                runs.append((cur_t, cur))
            cur, cur_t = [i, i + 1], t
    if cur:
        runs.append((cur_t, cur))
    out = {}
    for t, r in runs:
        row = {k: [deck[k][i] for i in r] for k in ("p", "g", "b", "wl", "wr", "ol", "or")}
        row.update({"w": deck["w"], "kind": deck["kind"], "name": deck["name"]})
        for key in ("site", "role"):
            if deck.get(key):
                row[key] = deck[key]
        if r[0] > 0:
            row["pa"] = p[r[0] - 1][:2]
        if r[-1] < len(p) - 1:
            row["pb"] = p[r[-1] + 1][:2]
        out.setdefault(t, []).append(row)
    return out


def run(tiles_dir, sites, write=False, report=None):
    lines = ["# Builder v2 (pipeline/scopes/ramp_build.py): rows from cadastre edges and LiDAR heights", ""]
    changed = {}
    built = []
    for name in sites:                                   # pass 1: every site's decks
        B = Build(name, tiles_dir)
        res = B.build(do_join=len(sites) == 1)
        built.append((name, B, res))
    if len(sites) > 1:                                   # pass 2: joins see the other sites' new decks; openings accumulate
        all_keys = set().union(*(B.sel for _, B, _ in built))
        mods = {}
        for name, B, res in built:
            extra = [d for n2, B2, _ in built if B2 is not B for d in B2.decks]
            B.modified, jl = J.join(B.decks, B.R, all_keys, extra=extra, base=mods)
            mods.update(B.modified); B.lines += jl
        for _, B, _ in built:
            B.modified = {k: v for k, v in mods.items() if k in B.modified}
    # pass 3: footway rows beside the new decks (trim, continue air ends along the LiDAR ground, solid on embankments)
    import footways as FW
    R0 = built[0][1].R
    skip = set().union(*(B.sel | res[2] for _, B, res in built))
    foot_new, fl = FW.rebuild([d for _, B, _ in built for d in B.decks], R0, skip, lambda x, y: float(R0.ground(np.array([x]), np.array([y]))[0]))
    for _, B, res in built:
        B.foot = {}
    for (t, k), rs in foot_new.items():
        built[0][1].foot[(t, k)] = rs
    for name, B, (decks, piers, drop) in built:
        lines.append(f"## {name} ('{B.cfg['match']}')")
        lines += B.lines + [""]
        if not write:
            continue
        T = B.R.tiles
        for t, k in B.sel | drop:
            changed.setdefault(t, {"drop": set(), "add": [], "decks": [], "piers": []})["drop"].add(k)
        for d in decks:
            for t, rs in cut_rows(d, T).items():
                ch = changed.setdefault(t, {"drop": set(), "add": [], "decks": [], "piers": []})
                ch["add"] += rs; ch["decks"].append(d)
        for q in piers:
            changed.setdefault(T.name_at(q[0], q[1]), {"drop": set(), "add": [], "decks": [], "piers": []})["piers"].append(q)
        for (t, k), row in B.modified.items():
            changed.setdefault(t, {"drop": set(), "add": [], "decks": [], "piers": []}).setdefault("mod", {})[k] = row
        for (t, k), rs in B.foot.items():
            changed.setdefault(t, {"drop": set(), "add": [], "decks": [], "piers": []})["drop"].add(k)
            for d in rs:
                for t2, rows2 in cut_rows(d, T).items():
                    changed.setdefault(t2, {"drop": set(), "add": [], "decks": [], "piers": []})["add"] += rows2
        for t, ch in changed.items():
            ch.setdefault("dropped_piers", set()).update(B.dropped_piers)
    if write:
        T = RL.Tiles(tiles_dir)
        os.makedirs(T.orig_dir, exist_ok=True)
        import glob, shutil
        for orig in glob.glob(f"{T.orig_dir}/t_*.json"):      # tiles an earlier run rewrote but this run does not touch: restore
            t = os.path.basename(orig)[:-5]
            if t not in changed:
                shutil.copyfile(orig, f"{tiles_dir}/{t}.json"); lines.append(f"- restored {t} from the original (not touched by this run)")
        for t, ch in changed.items():
            f = f"{tiles_dir}/{t}.json"; orig = f"{T.orig_dir}/{t}.json"
            if not os.path.exists(orig):
                os.rename(f, orig)
            m = json.load(open(orig))
            br = m.setdefault("bridges", {"decks": [], "piers": []})
            mod = ch.get("mod", {})
            br["decks"] = [mod.get(k, d) for k, d in enumerate(br.get("decks", [])) if k not in ch["drop"]] + ch["add"]
            dp = ch.get("dropped_piers", set())
            br["piers"] = [q for q in br.get("piers", []) if (round(q[0], 2), round(q[1], 2)) not in dp] + ch["piers"]
            np_ = RL.drop_props(m, ch["decks"])
            nc = drop_colliders(m, ch["decks"])
            json.dump(m, open(f, "w"), separators=(",", ":"))
            lines.append(f"- wrote {t}: dropped {len(ch['drop'])} rows, added {len(ch['add'])}, opened {len(mod)}, piers +{len(ch['piers'])}, props removed under the new decks {np_}, static colliders {nc}")
    lines += [""] + fl
    text = "\n".join(lines)
    print(text)
    if report:
        open(report, "w").write(text + "\n")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tiles = sys.argv[sys.argv.index("--tiles") + 1] if "--tiles" in sys.argv else os.path.join(ROOT, "web", "public", "tiles")
    rep = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv else None
    run(tiles, (args[0].split(",") if args else ["gerold", "duttweiler"]), write="--write" in sys.argv, report=rep)
