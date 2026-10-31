"""LiDAR-informed ramp modelling (pilot on built tile metadata; no full rebuild needed).

Rebuilds the deck rows of named bridge/ramp chains from the LiDAR rasters (pipeline/lidar_grid.py, lidar.py):
  axis    at every 2 m station the surface band that matches the running height (class-17 deck top, else class-2 ground =
          embankment or at-grade road) is found across the OSM axis; the axis stays where OSM (and the road graph, the traffic
          and the ride routes) has it while it lies inside the band, and moves to the band where OSM is off (Geroldrampe: 10 m)
  width   per-vertex left / right half widths = extent of that band on each side of the axis (row keys "wl" / "wr"; the client
          falls back to the symmetric "w" where they are missing)
  props   street furniture, trees and parked cars inside the new footprint under an elevated deck are removed from the tile
  height  low percentile of the band surface (vehicles, railings removed), smoothed, slope-limited, never below the game terrain
  ends    a chain end in the air that is not a junction with another deck is continued along the road graph (roads.json) until
          the measured surface meets the game terrain (tile hmap); two chains ending at the same point share one continuation
  skirt   stations without a class-17 return but above the terrain are embankments / retaining walls: underside "b" = ground
          (solid side faces); bridge stations keep the deck thickness of the original rows
  footways rows of kind foot that lie inside the new footprint are dropped (the measured structure carries them)
Usage:
  python3 pipeline/ramp_lidar.py <tiles_dir> <site>[,<site>] [--write] [--report file.md]
Sites: name substrings of deck rows (SITES). Without --write only the report is printed. With --write the tile JSONs are
rewritten from <tile>.orig.json (kept once), so a re-run replaces the previous result instead of accumulating.
"""
from __future__ import annotations

import base64
import glob
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lidar  # noqa: E402

ROOT = os.path.dirname(HERE)
STEP = 2.0          # station spacing (m)
HALF = 16.0         # lateral search window (m)
TOL = 1.0           # m: surface cells within this of the running height belong to the ramp band
MAX_SLOPE = 0.12
MAX_LAT_STEP = 1.5  # m: lateral centre may move this much per station
MAX_W_STEP = 0.35   # m: width may change this much per station
W_MIN, W_MAX = 3.0, 16.0
AT_GRADE = 0.3      # m above terrain counts as at grade
EXTEND_MAX = 160.0  # m: longest continuation beyond an old chain end
JUNCTION = 2.5      # m: another deck's vertex this close to a chain end = junction (no continuation, axis locked)
LOCK = 12.0         # m: stations this close to a junction keep the prior axis and width
PCT = 35            # low percentile of the band surface = deck top
THICK = {"road": 1.0, "tram": 1.0, "foot": 0.5}

SITES = {
    "gerold": {"match": "Geroldrampe", "kinds": ("road",)},
    "duttweiler": {"match": "Duttweilerbrücke", "kinds": ("road",)},
}


# ---------------------------------------------------------------- tile metadata, terrain, road graph
class Tiles:
    def __init__(self, d):
        self.dir = d
        self.meta = {}
        self.orig_dir = os.path.join(os.path.dirname(os.path.abspath(d)), "tiles_orig")   # untouched copies of rewritten tiles
        for f in sorted(glob.glob(f"{d}/t_*.json")):
            name = os.path.basename(f)[:-5]
            o = f"{self.orig_dir}/{name}.json"
            self.meta[name] = json.load(open(o if os.path.exists(o) else f))   # always model from the original
        self.world = json.load(open(f"{d}/world.json"))
        self.T = float(self.world["tile"])
        self.h = {}
        for name, m in self.meta.items():
            hm = m.get("hmap")
            if hm and hm.get("zb64"):
                z = np.frombuffer(base64.b64decode(hm["zb64"]), dtype="<i2").astype(float) / 100.0
                self.h[name] = (hm, z.reshape(hm["h"], hm["w"]))

    def name_at(self, x, y):
        return f"t_{math.floor(x / self.T)}_{math.floor(y / self.T)}"

    def ground(self, x, y):
        """Game terrain (tile hmap, bilinear); NaN outside the built tiles."""
        x = np.atleast_1d(np.asarray(x, float)); y = np.atleast_1d(np.asarray(y, float))
        out = np.full(x.shape, np.nan)
        for i in range(len(x)):
            e = self.h.get(self.name_at(x[i], y[i]))
            if not e:
                continue
            hm, z = e
            fx = min(max((x[i] - hm["x0"]) / hm["step"], 0), hm["w"] - 1.001)
            fy = min(max((y[i] - hm["y0"]) / hm["step"], 0), hm["h"] - 1.001)
            ix, iy = int(fx), int(fy); tx, ty = fx - ix, fy - iy
            out[i] = z[iy, ix] * (1 - tx) * (1 - ty) + z[iy, ix + 1] * tx * (1 - ty) + z[iy + 1, ix] * (1 - tx) * ty + z[iy + 1, ix + 1] * tx * ty
        return out

    def rows(self):
        for name, m in self.meta.items():
            for k, d in enumerate((m.get("bridges") or {}).get("decks", [])):
                yield name, k, d


class Roads:
    def __init__(self):
        R = json.load(open(f"{ROOT}/web/public/data/roads.json"))
        self.nodes = np.array(R["nodes"], float)
        self.edges = R["cars"] + R["bikes"]
        self.adj = {}
        for i, e in enumerate(self.edges):
            self.adj.setdefault(e["a"], []).append(i); self.adj.setdefault(e["b"], []).append(i)

    def pts(self, i, from_node):
        p = self.edges[i]["p"]
        P = [(p[k], p[k + 1]) for k in range(0, len(p), 2)]
        return P if self.edges[i]["a"] == from_node else P[::-1]

    def continue_from(self, pt, direction, length):
        """Polyline continuing from the node nearest pt (< 3 m) along the straightest edges for `length` m; [] if none."""
        d = np.hypot(self.nodes[:, 0] - pt[0], self.nodes[:, 1] - pt[1])
        n = int(d.argmin())
        if d[n] > 3.0:
            return []
        out, used, L = [], set(), 0.0
        dirv = np.asarray(direction, float)
        while L < length:
            best = None
            for i in self.adj.get(n, []):
                if i in used:
                    continue
                P = self.pts(i, n)
                if len(P) < 2:
                    continue
                v = np.array(P[1]) - np.array(P[0]); nv = np.linalg.norm(v) or 1.0
                c = float(dirv @ v) / nv
                if best is None or c > best[0]:
                    best = (c, i, P)
            if best is None or best[0] < 0.5:
                break
            _, i, P = best
            used.add(i)
            for q in P[1:]:
                prev = out[-1] if out else tuple(pt)
                if not out and math.hypot(q[0] - pt[0], q[1] - pt[1]) < 6.0:
                    continue   # the road graph's own jog around the junction node would put a kink into the deck; the deck bridges it straight
                L += math.hypot(q[0] - prev[0], q[1] - prev[1]); out.append(q)
            e = self.edges[i]; n = e["b"] if e["a"] == n else e["a"]
            v = np.array(P[-1]) - np.array(P[-2]); dirv = v / (np.linalg.norm(v) or 1.0)
        return out


# ---------------------------------------------------------------- chains from rows
def flip(d):
    e = dict(d)
    e["p"], e["g"], e["b"] = d["p"][::-1], d["g"][::-1], d["b"][::-1]
    e.pop("pa", None); e.pop("pb", None)
    if "pb" in d: e["pa"] = d["pb"]
    if "pa" in d: e["pb"] = d["pa"]
    for k in ("ol", "or", "wv"):
        if k in d: e[k] = d[k][::-1]
    return e


def heading(d, at_end):
    p = d["p"]
    a, b = (p[-2], p[-1]) if at_end else (p[1], p[0])   # direction pointing out of the row
    v = np.array(b[:2], float) - np.array(a[:2], float)
    return v / (np.linalg.norm(v) or 1.0)


def chains_of(rows):
    """Join rows at shared end vertices when the direction continues (turn < 60 deg); else they end there (fork = two ends)."""
    key = lambda p: (round(p[0], 1), round(p[1], 1))
    ends = {}
    for r in rows:
        for k in (0, -1):
            ends.setdefault(key(r[2]["p"][k]), []).append(r)
    used, out = set(), []
    for r0 in rows:
        if id(r0) in used:
            continue
        chain = [r0]; used.add(id(r0))
        for forward in (True, False):
            while True:
                cur = chain[-1] if forward else chain[0]
                p = cur[2]["p"][-1] if forward else cur[2]["p"][0]
                here = ends.get(key(p), [])
                nb = [r for r in here if id(r) not in used]
                if len(here) != 2 or len(nb) != 1:
                    break
                nxt = nb[0]
                d = nxt[2] if key(nxt[2]["p"][0]) == key(p) else flip(nxt[2])   # oriented away from p
                cp = cur[2]["p"]
                t_chain = np.array(cp[-1][:2], float) - np.array(cp[-2][:2], float) if forward else np.array(cp[0][:2], float) - np.array(cp[1][:2], float)
                t_next = np.array(d["p"][1][:2], float) - np.array(d["p"][0][:2], float)
                t_chain /= (np.linalg.norm(t_chain) or 1.0); t_next /= (np.linalg.norm(t_next) or 1.0)
                if float(t_chain @ t_next) < math.cos(math.radians(60)):   # sharp turn = fork, not a continuation
                    break
                used.add(id(nb[0]))
                if forward:
                    chain.append((nxt[0], nxt[1], d))
                else:
                    chain.insert(0, (nxt[0], nxt[1], flip(d)))
        out.append(chain)
    return out


def merged(chain):
    P, G, B = [], [], []
    for _, _, d in chain:
        for i, p in enumerate(d["p"]):
            if P and abs(P[-1][0] - p[0]) < 0.05 and abs(P[-1][1] - p[1]) < 0.05:
                continue
            P.append(p); G.append(d["g"][i]); B.append(d["b"][i])
    return np.array(P, float), np.array(G, float), np.array(B, float)


def resample(P, step):
    seg = np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1]))
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(round(s[-1] / step)) + 1)
    t = np.linspace(0, s[-1], n)
    return np.column_stack([np.interp(t, s, P[:, k]) for k in range(P.shape[1])]), t


# ---------------------------------------------------------------- the tracker
def surface(x, y):
    """Measured surface: class-17 deck top where present, else class-2 ground; flags 1 = bridge, 2 = ground, 0 = none."""
    b = lidar.bridge(x, y); g = lidar.dtm(x, y)
    S = np.where(np.isnan(b), g, b)
    F = np.where(np.isnan(b), np.where(np.isnan(g), 0, 2), 1)
    return S, F


def robust_low(v):
    v = v[~np.isnan(v)]
    if len(v) < 3:
        return np.nan
    m = np.median(v)
    k = v[np.abs(v - m) <= 0.45]
    return float(np.percentile(k if len(k) >= 3 else v, PCT))


def track(axis, z0, lock):
    """Follow the band along a prior axis (Nx2). lock[i] = keep the prior axis / width at station i.
    Returns centre (x, y), z (NaN = nothing measured), left / right half widths (NaN = unbounded / locked), flag (1 bridge, 2 ground, 0 none).
    The axis stays on the prior (OSM carriageway axis, which the road graph and the traffic follow) as long as it lies inside the
    measured band with a margin; it only moves when the band is elsewhere (Geroldrampe: OSM 10 m off) and then by <= MAX_LAT_STEP per station."""
    axis = np.asarray(axis, float)[:, :2]
    n = len(axis)
    xy = np.zeros((n, 2)); Z = np.full(n, np.nan); WL = np.full(n, np.nan); WR = np.full(n, np.nan); Fl = np.zeros(n, int)
    Cs = np.zeros(n); NRM = np.zeros((n, 2))
    c_prev, z_prev = 0.0, z0
    offs = np.arange(-HALF, HALF + 1e-9, 0.5)
    for i in range(n):
        a = axis[max(i - 1, 0)]; b = axis[min(i + 1, n - 1)]
        t = b - a; t = t / (np.hypot(t[0], t[1]) or 1.0); nrm = np.array([-t[1], t[0]])
        NRM[i] = nrm
        S, F = surface(axis[i, 0] + nrm[0] * offs, axis[i, 1] + nrm[1] * offs)
        cand = np.abs(S - z_prev) <= TOL + MAX_SLOPE * STEP
        runs, k = [], 0
        while k < len(cand):
            if cand[k]:
                j = k
                while j + 1 < len(cand) and (cand[j + 1] or (j + 2 < len(cand) and cand[j + 2])):
                    j += 1
                runs.append((k, j)); k = j + 1
            else:
                k += 1
        c_pred = 0.0 if lock[i] else 0.7 * c_prev
        best = None
        for (k0, k1) in runs:
            lo, hi = offs[k0], offs[k1]
            bounded = k0 > 0 and k1 < len(cand) - 1
            dist = 0.0 if lo - 0.5 <= c_pred <= hi + 0.5 else min(abs(lo - c_pred), abs(hi - c_pred))
            score = dist + (0 if bounded else 6.0)
            if best is None or score < best[0]:
                best = (score, k0, k1, 0.5 * (lo + hi), bounded)
        if best is None or best[0] > 8.0:
            Cs[i] = 0.0 if lock[i] else c_prev
            xy[i] = axis[i] + nrm * Cs[i]
            continue
        _, k0, k1, cen, bounded = best
        lo, hi = offs[k0] - 0.25, offs[k1] + 0.25
        width = hi - lo
        wl = wr = np.nan
        if bounded and width <= W_MAX and not lock[i]:
            m = max(1.0, 0.35 * width)   # the axis may sit anywhere in the central part of the band: keep the prior axis if it does
            c = float(np.clip(0.0, lo + m, hi - m)) if lo + m <= hi - m else cen
            c = float(np.clip(c, c_prev - MAX_LAT_STEP, c_prev + MAX_LAT_STEP))
            wl, wr = hi - c, c - lo   # left = +offset side (left normal), right = -offset side
        else:
            c = float(np.clip(0.0, c_prev - MAX_LAT_STEP, c_prev + MAX_LAT_STEP))
        sel = slice(k0, k1 + 1)
        # deck top from the central strip of the band (carriageway): raised footways, parapets and noise walls at the edges
        # are also class 17 and would lift the median by 0.5 to 1.5 m
        kc = int(round((k0 + k1) / 2)); hk = max(3, int(0.3 * width / 0.5))
        z = robust_low(S[max(k0, kc - hk):min(k1, kc + hk) + 1])
        is_bridge = (F[sel] == 1).mean() > 0.5
        if not is_bridge:
            wl = wr = np.nan   # ground-class band (embankment, at grade): its lateral extent is the whole level surface, not the ramp; keep the bridge / prior width
        Cs[i] = c; xy[i] = axis[i] + nrm * c; Z[i] = z; WL[i] = wl; WR[i] = wr; Fl[i] = 1 if is_bridge else 2
        c_prev = c
        if not np.isnan(z):
            z_prev = z
    # the band centre jitters by up to a cell per station: smooth the lateral offsets so the axis has no kinks (a kinked axis
    # leaves gaps in the per-segment railing collider for off-axis points and looks wrong), widths follow the smoothed axis
    Cm = smooth(Cs, 5); Cm = np.convolve(np.pad(Cm, 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")
    WL = WL + (Cs - Cm); WR = WR - (Cs - Cm)   # same band edges, measured from the smoothed axis
    xy = axis + NRM * Cm[:, None]
    return xy, Z, WL, WR, Fl


def smooth(v, k):
    v = np.asarray(v, float); out = v.copy(); h = k // 2
    for i in range(len(v)):
        win = v[max(0, i - h):i + h + 1]; win = win[~np.isnan(win)]
        out[i] = np.median(win) if len(win) else np.nan
    return out


def fill_nan(v, s):
    v = np.asarray(v, float); ok = ~np.isnan(v)
    return v if ok.sum() == 0 else np.where(ok, v, np.interp(s, s[ok], v[ok]))


def rate_limit(v, s, r):
    v = v.copy()
    for i in range(1, len(v)):
        v[i] = min(max(v[i], v[i - 1] - r * (s[i] - s[i - 1])), v[i - 1] + r * (s[i] - s[i - 1]))
    for i in range(len(v) - 2, -1, -1):
        v[i] = min(max(v[i], v[i + 1] - r * (s[i + 1] - s[i])), v[i + 1] + r * (s[i + 1] - s[i]))
    return v


def finish(xy, z, wl, wr, f, g, s, w_prior, kind, thick, grade_ends):
    """Heights, widths and underside of a tracked polyline -> deck dict."""
    z = fill_nan(z, s); z = smooth(z, 5); z = np.maximum(z, g); z = rate_limit(z, s, MAX_SLOPE); z = np.maximum(z, g)
    side = []
    for v in (wl, wr):
        v = smooth(v, 9); v = np.where(np.isnan(v), w_prior / 2, np.clip(v, W_MIN / 2, W_MAX / 2)); side.append(rate_limit(v, s, MAX_W_STEP / 2))
    wl, wr = side
    w = wl + wr
    for end in grade_ends:   # ends meant to be at grade: blend the last 10 m onto the terrain
        e = z[end] - g[end]
        if 0 < e <= 1.5:
            k = np.clip(1 - np.abs(s - s[end]) / 10.0, 0, 1)
            z = np.maximum(z - e * k, g)
    solid = (f != 1) | (z - g < 0.6)
    solid = smooth(solid.astype(float), 5) >= 0.5
    b = np.where(solid, g, z - thick)
    return {"p": [[round(float(x), 2), round(float(y), 2), round(float(v), 2)] for (x, y), v in zip(xy, z)],
            "g": [round(float(v), 2) for v in g], "b": [round(float(v), 2) for v in b], "w": round(float(np.median(w)), 1),
            "wl": [round(float(v), 2) for v in wl], "wr": [round(float(v), 2) for v in wr], "kind": kind, "_f": f.tolist(), "_s": s.tolist()}


def stats(deck):
    p = np.array(deck["p"], float); g = np.array(deck["g"], float); seg = np.hypot(np.diff(p[:, 0]), np.diff(p[:, 1]))
    wv = [a + b for a, b in zip(deck["wl"], deck["wr"])] if "wl" in deck else [deck["w"]] * len(p)
    return {"len": float(seg.sum()), "w": (float(min(wv)), float(np.median(wv)), float(max(wv))), "end_el": (float(p[0, 2] - g[0]), float(p[-1, 2] - g[-1])),
            "max_slope": float(np.max(np.abs(np.diff(p[:, 2])) / np.maximum(seg, 0.1))) if len(p) > 1 else 0.0, "n": len(p)}


def fmt(name, old, new, extra=""):
    return (f"- {name}: length {old['len']:.0f} -> {new['len']:.0f} m; width {old['w'][1]:.1f} -> {new['w'][0]:.1f}/{new['w'][1]:.1f}/{new['w'][2]:.1f} m (min/med/max); "
            f"ends above ground {old['end_el'][0]:+.1f}/{old['end_el'][1]:+.1f} -> {new['end_el'][0]:+.1f}/{new['end_el'][1]:+.1f} m; "
            f"max slope {old['max_slope']*100:.0f} -> {new['max_slope']*100:.0f} %{extra}")


# ---------------------------------------------------------------- a site
def model_site(tiles, roads, cfg, lines):
    rows = [(t, k, d) for t, k, d in tiles.rows() if cfg["match"] in (d.get("name") or "") and d["kind"] in cfg["kinds"]]
    sel = {(t, k) for t, k, _ in rows}
    others = np.array([p[:2] for t, k, d in tiles.rows() if (t, k) not in sel and d["kind"] != "rail" for p in d["p"]], float)
    chains = chains_of(rows)
    lines.append(f"rows {len(rows)}, chains {len(chains)}")
    decks, requests = [], {}
    for ci, chain in enumerate(chains):
        kind = chain[0][2]["kind"]; name = chain[0][2].get("name", "")
        P, G, B = merged(chain)
        thick = float(np.median(P[:, 2] - B)); thick = thick if 0.2 < thick < 3 else THICK.get(kind, 1.0)
        axis, s = resample(P, STEP)
        g = tiles.ground(axis[:, 0], axis[:, 1]); g = fill_nan(g, s)
        g = np.where(np.isnan(g), np.interp(s, np.concatenate([[0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))]), G), g)
        kinds_end = {}
        for end in (0, -1):
            dj = np.hypot(others[:, 0] - axis[end, 0], others[:, 1] - axis[end, 1]).min() if len(others) else 1e9
            kinds_end[end] = "junction" if dj < JUNCTION else ("grade" if axis[end, 2] - g[end] < AT_GRADE + 0.1 else "air")
        lock = np.zeros(len(axis), bool)
        for end, k in kinds_end.items():
            if k == "junction":
                lock |= np.abs(s - s[end]) < LOCK
        xy, z, wl, wr, f = track(axis, float(P[0, 2]), lock)
        w_prior = chain[0][2]["w"]
        lat = float(np.max(np.hypot(xy[:, 0] - axis[:, 0], xy[:, 1] - axis[:, 1])))
        deck = finish(xy, z, wl, wr, f, g, s, w_prior, kind, thick, [e for e, k in kinds_end.items() if k == "grade"])
        deck["name"] = name; deck["_chain"] = ci; deck["_ends"] = kinds_end; deck["_thick"] = thick
        decks.append(deck)
        for end, k in kinds_end.items():
            if k == "air":
                pt = tuple(round(v, 0) for v in axis[end, :2])
                d_out = (axis[end, :2] - axis[end - 1 if end == -1 else 1, :2]); d_out = d_out / (np.linalg.norm(d_out) or 1.0)
                requests.setdefault(pt, []).append((ci, end, d_out, w_prior))
        old = stats({"p": P.tolist(), "g": G.tolist(), "w": w_prior}); new = stats(deck)
        meas = int((~np.isnan(z)).sum())
        lines.append(fmt(f"chain {kind} ({P[0,0]:.0f},{P[0,1]:.0f})->({P[-1,0]:.0f},{P[-1,1]:.0f}) [{kinds_end[0]}/{kinds_end[-1]}]", old, new,
                         f"; stations {len(axis)} measured {meas} (bridge {(f == 1).sum()}, ground {(f == 2).sum()}); axis moved up to {lat:.1f} m"))
    # continuations (one per end point, shared by the chains that end there)
    for pt, reqs in requests.items():
        ci, end, d_out, w_prior = reqs[0]
        for r in reqs[1:]:
            d_out = d_out + r[2]; w_prior = max(w_prior, r[3])
        d_out = d_out / (np.linalg.norm(d_out) or 1.0)
        start = np.array(decks[ci]["p"][end], float)
        cont = roads.continue_from(start[:2], d_out, EXTEND_MAX)
        if not cont:
            cont = [tuple(start[:2] + d_out * STEP * k) for k in range(1, int(EXTEND_MAX / STEP) + 1)]
        C = np.array(cont, float)
        C, s = resample(np.vstack([start[None, :2], C]), STEP)
        g = fill_nan(tiles.ground(C[:, 0], C[:, 1]), s)
        xy, z, wl, wr, f = track(C, float(start[2]), np.zeros(len(C), bool))
        zf = fill_nan(z, s); zf = np.maximum(smooth(zf, 5), g)
        hit = next((i for i in range(1, len(zf)) if zf[i] - g[i] < AT_GRADE), None)
        if hit is None:
            lines.append(f"- continuation at ({pt[0]:.0f},{pt[1]:.0f}): no grade found within {s[-1]:.0f} m, skipped")
            continue
        keep = slice(0, hit + 1)
        deck = finish(xy[keep], z[keep], wl[keep], wr[keep], f[keep], g[keep], s[keep], w_prior, decks[ci]["kind"], decks[ci]["_thick"], [-1])
        deck["name"] = decks[ci]["name"]; deck["_chain"] = -1; deck["_ends"] = {0: "joint", -1: "grade"}
        # the chains that end here take the continuation's start height
        for r in reqs:
            dk = decks[r[0]]; dk["p"][r[1]][2] = deck["p"][0][2]
            if dk["b"][r[1]] > dk["p"][r[1]][2] - 0.1: dk["b"][r[1]] = dk["g"][r[1]]
        decks.append(deck)
        new = stats(deck)
        lines.append(f"- continuation from ({pt[0]:.0f},{pt[1]:.0f}) for {len(reqs)} chain(s): {new['len']:.0f} m along the road graph, ends {new['end_el'][1]:+.1f} m above ground, "
                     f"width {new['w'][0]:.1f}/{new['w'][1]:.1f}/{new['w'][2]:.1f}, max slope {new['max_slope']*100:.0f} %, bridge {(f[keep] == 1).sum()} / ground {(f[keep] == 2).sum()} stations")
    # footways inside the new footprint are redundant
    drop_foot = set()
    for t, k, d in tiles.rows():
        if d["kind"] != "foot" or (t, k) in sel:
            continue
        P = np.array(d["p"], float)
        inside = sum(1 for p in P if any(lateral_inside(dk, p[0], p[1], 0.3, p[2], 1.5) for dk in decks))
        if inside >= 0.7 * len(P):
            drop_foot.add((t, k))
    if drop_foot:
        lines.append(f"- footway rows inside the new footprint dropped: {len(drop_foot)}")
    return decks, sel | drop_foot


def lateral_inside(deck, x, y, margin, z=None, dz=None):
    """Is (x, y) inside the footprint of deck (left / right half widths minus margin)? Optionally also within dz of the deck height."""
    Q = np.array(deck["p"], float)
    dd = np.hypot(Q[:, 0] - x, Q[:, 1] - y); j = int(dd.argmin())
    if dd[j] > max(deck["wl"][j], deck["wr"][j]) + 1.0:
        return False
    a = Q[max(j - 1, 0), :2]; b = Q[min(j + 1, len(Q) - 1), :2]
    t = b - a; t = t / (np.hypot(t[0], t[1]) or 1.0); nrm = np.array([-t[1], t[0]])
    lat = float((np.array([x, y]) - Q[j, :2]) @ nrm)
    lim = (deck["wl"][j] if lat > 0 else deck["wr"][j]) - margin
    if abs(lat) > lim:
        return False
    return z is None or abs(Q[j, 2] - z) < dz


PROP_KEYS = ("lamps", "bins", "benches", "trafficsigns", "hydrants", "bollards", "bikes", "racks", "mopeds", "signals", "trees", "masts",
             "scooters", "cars", "construction", "sites", "workers")


def drop_props(meta, decks):
    """Street furniture, trees and parked cars standing inside the new footprint where the deck is above the ground are removed
    (same idea as bridges.drop_deck_props for the rebuilt chains). Returns the number removed."""
    n = 0
    for key in PROP_KEYS:
        rows = meta.get(key)
        if not isinstance(rows, list) or not rows:
            continue
        keep = []
        for r in rows:
            if isinstance(r, list) and len(r) >= 2 and isinstance(r[0], (int, float)) and isinstance(r[1], (int, float)) and \
                    any(lateral_inside(dk, r[0], r[1], -0.5) and deck_el(dk, r[0], r[1]) >= 0.3 for dk in decks):
                n += 1; continue
            keep.append(r)
        meta[key] = keep
    return n


def deck_el(deck, x, y):
    Q = np.array(deck["p"], float); j = int(np.hypot(Q[:, 0] - x, Q[:, 1] - y).argmin())
    return Q[j, 2] - deck["g"][j]


def cut_rows(deck, tiles):
    """Split one chain into per-tile rows (same rule as bridges.tile_rows: the segment midpoint decides the tile)."""
    p = deck["p"]; out = {}
    runs, cur, cur_t = [], [], None
    for i in range(len(p) - 1):
        t = tiles.name_at((p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2)
        if cur and t == cur_t:
            cur.append(i + 1)
        else:
            if cur: runs.append((cur_t, cur))
            cur, cur_t = [i, i + 1], t
    if cur: runs.append((cur_t, cur))
    for t, r in runs:
        row = {"p": [p[i] for i in r], "g": [deck["g"][i] for i in r], "b": [deck["b"][i] for i in r], "w": deck["w"],
               "wl": [deck["wl"][i] for i in r], "wr": [deck["wr"][i] for i in r], "kind": deck["kind"], "name": deck["name"]}
        if r[0] > 0: row["pa"] = p[r[0] - 1][:2]
        if r[-1] < len(p) - 1: row["pb"] = p[r[-1] + 1][:2]
        out.setdefault(t, []).append(row)
    return out


def run(tiles_dir, sites, write=False, report=None):
    tiles = Tiles(tiles_dir); roads = Roads()
    lines = ["# LiDAR ramp pilot (pipeline/ramp_lidar.py)", ""]
    changed = {}
    for site in sites:
        lines.append(f"## {site} ('{SITES[site]['match']}')")
        decks, drop = model_site(tiles, roads, SITES[site], lines)
        if write:
            for t, k in drop:
                changed.setdefault(t, {"drop": set(), "add": [], "decks": []})["drop"].add(k)
            for d in decks:
                for t, rs in cut_rows(d, tiles).items():
                    ch = changed.setdefault(t, {"drop": set(), "add": [], "decks": []})
                    ch["add"] += rs; ch["decks"].append(d)
        lines.append("")
    if write:
        os.makedirs(tiles.orig_dir, exist_ok=True)
        for t, ch in changed.items():
            f = f"{tiles_dir}/{t}.json"; orig = f"{tiles.orig_dir}/{t}.json"
            if not os.path.exists(orig):
                os.rename(f, orig)
            m = json.load(open(orig))
            br = m.setdefault("bridges", {"decks": [], "piers": []})
            br["decks"] = [d for k, d in enumerate(br.get("decks", [])) if k not in ch["drop"]] + ch["add"]
            np_ = drop_props(m, ch["decks"])
            json.dump(m, open(f, "w"), separators=(",", ":"))
            lines.append(f"- wrote {t}: dropped {len(ch['drop'])} rows, added {len(ch['add'])}, props removed under the new decks {np_}")
    text = "\n".join(lines)
    print(text)
    if report:
        open(report, "w").write(text + "\n")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rep = sys.argv[sys.argv.index("--report") + 1] if "--report" in sys.argv else None
    run(args[0], args[1].split(","), write="--write" in sys.argv, report=rep)
