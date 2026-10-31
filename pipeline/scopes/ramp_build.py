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
GRADE_EXT = 20.0    # m: a grade end follows the cadastre structure (edge polygons, walls) this far at most
SIDE_MAX = 12.0     # m: a cadastre edge further than this from the axis belongs to the main deck
SIDE_MIN = 1.2
W_STEP = 2.0        # m per station: width rate limit (the cadastre edges are exact; this only tames slice toggling)
MAX_SLOPE = 0.12
AT_GRADE = 0.3
BLEND = 10.0        # m: height blend at junction / fork ends
END_FLUSH = 6.0     # m: within this of a fork / junction end both sides are flush (no railing piece at the nose)
COPLANAR = 8.0      # m: a branch this close to the main chain's axis takes its height (one surface where a car changes lanes)
PIER_MIN_EL = 2.2
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
        self.lines = []

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
                    nv = self._nrm(C, i)
                    sv = M.structure(M.deck_slices(C[i], nv, self.decks_av))
                    gl, gr = M.nearest_side(M.intervals(C[i], nv, self.wall_u), wl0[end], wr0[end])
                    if sv or (gl is not None and abs(gl) <= M.WALL_NEAR) or (gr is not None and abs(gr) <= M.WALL_NEAR):
                        keep = i + 1
                    else:
                        break
                if keep == 0:
                    continue
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
            hit = next((i for i in range(len(C)) if zc[i] - gc[i] < AT_GRADE), None)
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

    @staticmethod
    def _nrm(C, i):
        a = C[max(i - 1, 0)]; b = C[min(i + 1, len(C) - 1)]; t = b - a; t = t / (np.hypot(t[0], t[1]) or 1.0)
        return np.array([-t[1], t[0]])

    def widths(self, st, c, other_axes, ends=None):
        n = len(st["s"]); wl = st["wl0"].copy(); wr = st["wr0"].copy()
        mode = np.zeros(n, int); fl = np.zeros(n, int); fr = np.zeros(n, int); gl = np.full(n, np.nan); gr = np.full(n, np.nan)
        split = np.zeros(n, bool); cap_l = np.full(n, np.inf); cap_r = np.full(n, np.inf)
        for i in range(n):
            p, nv = st["xy"][i], st["nrm"][i]
            sv = M.structure(M.deck_slices(p, nv, self.decks_av))
            if sv:
                lo, hi, mode[i] = sv; L, Rr = hi, -lo
                for o in axis_offsets(p, nv, other_axes):     # another site chain in the same slice: split halfway, flush
                    if 0.5 < o < 2 * L:
                        L = min(L, o / 2); fl[i] = 1; split[i] = abs(o) < COPLANAR; cap_l[i] = min(cap_l[i], o / 2)
                    elif -2 * Rr < o < -0.5:
                        Rr = min(Rr, -o / 2); fr[i] = 1; split[i] = abs(o) < COPLANAR; cap_r[i] = min(cap_r[i], -o / 2)
                if L > SIDE_MAX:                               # the main deck, not this ramp's edge
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
        z = RL.fill_nan(z, s); z = RL.smooth(z, 5); z = np.maximum(z, g); z = RL.rate_limit(z, s, MAX_SLOPE); z = np.maximum(z, g)
        for end, kind in ends.items():
            j = 0 if end == 0 else n - 1
            if kind in ("junction", "fork") and np.isfinite(st["z0"][j]):
                target = st["z0"][j] if kind == "junction" else self.fork_z(st["xy"][j], c)
                k = np.clip(1 - np.abs(s - s[j]) / BLEND, 0, 1); z = z + (target - z[j]) * k
            elif kind == "grade":
                e = z[j] - g[j]
                if 0 < e <= 1.5:
                    k = np.clip(1 - np.abs(s - s[j]) / BLEND, 0, 1); z = np.maximum(z - e * k, g)
        return z, flag

    def coplanar(self, z, st, c):
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
        for i in range(len(z)):                   # every station near an already built chain's axis (fork nose, overlap, split)
            pt = Point(*st["xy"][i]); best = None
            for ax, cum, zz in axes:
                dist = ax.distance(pt)
                if dist < COPLANAR and (best is None or dist < best[0]):
                    best = (dist, float(np.interp(ax.project(pt), cum, zz)))
            if best:
                z[i] = best[1]
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

    def build(self):
        self.built = {}
        axes = {c: __import__("shapely.geometry", fromlist=["LineString"]).LineString(c.P[:, :2]) for c in self.chains}
        decks = []
        for c in self.chains:
            thick = float(np.median(c.P[:, 2] - c.B)); thick = thick if 0.2 < thick < 3 else THICK.get(c.kind, 1.0)
            self.lines.append(f"- chain {c}")
            st, ends = self.stations(c)
            wl, wr, mode, fl, fr, gl, gr = self.widths(st, c, [a for o, a in axes.items() if o is not c], ends)
            z, flag = self.heights(st, wl, wr, ends, c)
            z = self.coplanar(z, st, c)
            kind, b = self.kinds(z, st["g"], mode, flag, gl, gr, thick)
            d = {"p": [[round(float(x), 2), round(float(y), 2), round(float(v), 2)] for (x, y), v in zip(st["xy"], z)],
                 "g": [round(float(v), 2) for v in st["g"]], "b": [round(float(v), 2) for v in b], "w": round(float(np.median(wl + wr)), 1),
                 "wl": [round(float(v), 2) for v in wl], "wr": [round(float(v), 2) for v in wr], "ol": fl.tolist(), "or": fr.tolist(),
                 "kind": c.kind, "name": c.name, "_kind": kind, "_mode": mode, "_flag": flag, "_thick": thick, "_ends": ends, "_s": st["s"], "_tan": st["tan"]}
            self.built[c] = d; decks.append(d)
            w = wl + wr; L = len(kind) * STEP
            self.lines.append(f"  - {L:.0f} m, width {w.min():.1f}/{np.median(w):.1f}/{w.max():.1f} m (min/med/max; live {c.P.shape[0]} vertices, {np.median(c.WL + c.WR):.1f} m); "
                              f"cadastre edges at {int((mode > 0).sum()) * STEP:.0f} m (edge pairs {int((mode == 2).sum()) * STEP:.0f} m); flush left/right {int(fl.sum()) * STEP:.0f}/{int(fr.sum()) * STEP:.0f} m; "
                              f"grade/solid/deck {int((kind == 0).sum()) * STEP:.0f}/{int((kind == 1).sum()) * STEP:.0f}/{int((kind == 2).sum()) * STEP:.0f} m; "
                              f"ends {ends[0]}/{ends[-1]} at {z[0] - st['g'][0]:+.1f}/{z[-1] - st['g'][-1]:+.1f} m above ground; max slope {np.max(np.abs(np.diff(z)) / STEP) * 100:.0f} %")
        piers, dropped = self.piers(decks)
        self.lines.append(f"- piers: {len(piers)} from the cadastre under elevated deck sections, {dropped} live rule-spaced piers dropped")
        drop = self.footways(decks)
        if drop:
            self.lines.append(f"- footway rows inside the new footprint dropped: {len(drop)}")
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
        if r[0] > 0:
            row["pa"] = p[r[0] - 1][:2]
        if r[-1] < len(p) - 1:
            row["pb"] = p[r[-1] + 1][:2]
        out.setdefault(t, []).append(row)
    return out


def run(tiles_dir, sites, write=False, report=None):
    lines = ["# Builder v2 (pipeline/scopes/ramp_build.py): rows from cadastre edges and LiDAR heights", ""]
    changed = {}
    for name in sites:
        B = Build(name, tiles_dir)
        lines.append(f"## {name} ('{B.cfg['match']}')")
        decks, piers, drop = B.build()
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
    text = "\n".join(lines)
    print(text)
    if report:
        open(report, "w").write(text + "\n")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    tiles = sys.argv[sys.argv.index("--tiles") + 1] if "--tiles" in sys.argv else os.path.join(ROOT, "web", "public", "tiles")
    rep = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv else None
    run(tiles, (args[0].split(",") if args else ["gerold", "duttweiler"]), write="--write" in sys.argv, report=rep)
