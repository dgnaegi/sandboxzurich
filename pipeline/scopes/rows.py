"""Modelled deck rows of a ramp site from the built tile metadata (web/public/tiles/t_*.json), in two variants:
  live   the deployed rows: web/public/tiles_orig/<tile>.json where pipeline/ramp_lidar.py rewrote a tile, else the tile itself
  current  the tiles as they are now (what the last builder wrote: the LiDAR pilot, then builder v2); `pilot` is an alias.
           An `override` directory (e.g. data/build/tiles_pilot) replaces tiles of the same name, so an older builder output can
           be scored after the tiles were rewritten.
A chain is a run of rows joined at shared end vertices (pipeline/ramp_lidar.chains_of); it carries per-vertex left / right half
widths (`wl` / `wr`, falling back to w / 2), heights, game ground and underside, and builds its footprint polygon and 2 m stations.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import ramp_lidar  # noqa: E402

JUNCTION = 2.5   # m: another deck's vertex this close to a chain end = junction
AT_GRADE = 0.3   # m above the game terrain counts as at grade


class Chain:
    def __init__(self, rows, kind, name):
        self.rows, self.kind, self.name = rows, kind, name
        P, G, B, WL, WR = [], [], [], [], []
        for _, _, d in rows:
            wl = d.get("wl") or [d["w"] / 2] * len(d["p"]); wr = d.get("wr") or [d["w"] / 2] * len(d["p"])
            for i, p in enumerate(d["p"]):
                if P and abs(P[-1][0] - p[0]) < 0.05 and abs(P[-1][1] - p[1]) < 0.05:
                    continue
                P.append(p); G.append(d["g"][i]); B.append(d["b"][i]); WL.append(wl[i]); WR.append(wr[i])
        self.P = np.array(P, float); self.G = np.array(G, float); self.B = np.array(B, float)
        self.WL = np.array(WL, float); self.WR = np.array(WR, float)
        seg = np.hypot(np.diff(self.P[:, 0]), np.diff(self.P[:, 1]))
        self.S = np.concatenate([[0.0], np.cumsum(seg)])
        self.length = float(self.S[-1])
        self.ends = {}

    def __repr__(self):
        p = self.P
        return f"{self.kind} ({p[0,0]:.0f},{p[0,1]:.0f})->({p[-1,0]:.0f},{p[-1,1]:.0f}) {self.length:.0f} m [{self.ends.get(0,'?')}/{self.ends.get(-1,'?')}]"

    def normals(self, xy):
        n = len(xy); T = np.zeros((n, 2))
        for i in range(n):
            a = xy[max(i - 1, 0)]; b = xy[min(i + 1, n - 1)]
            t = b - a; T[i] = t / (np.hypot(t[0], t[1]) or 1.0)
        return np.column_stack([-T[:, 1], T[:, 0]]), T

    def footprint(self, which="model"):
        """Union of per-segment quads between the left and right edges (left = +normal)."""
        import shapely
        from shapely.geometry import Polygon
        xy = self.P[:, :2]; N, _ = self.normals(xy)
        quads = []
        for i in range(len(xy) - 1):
            a, b = xy[i], xy[i + 1]
            q = Polygon([a + N[i] * self.WL[i], b + N[i + 1] * self.WL[i + 1], b - N[i + 1] * self.WR[i + 1], a - N[i] * self.WR[i]])
            if not q.is_valid:
                q = q.buffer(0)
            if not q.is_empty:
                quads.append(q)
        return shapely.union_all(quads) if quads else Polygon()

    def stations(self, step=2.0):
        """Resampled arrays along the chain: dict of xy (n,2), z, g, b, wl, wr, s, nrm (n,2), tan (n,2)."""
        A = np.column_stack([self.P, self.G, self.B, self.WL, self.WR])
        n = max(2, int(round(self.length / step)) + 1)
        t = np.linspace(0, self.length, n)
        R = np.column_stack([np.interp(t, self.S, A[:, k]) for k in range(A.shape[1])])
        nrm, tan = self.normals(R[:, :2])
        return {"xy": R[:, :2], "z": R[:, 2], "g": R[:, 3], "b": R[:, 4], "wl": R[:, 5], "wr": R[:, 6], "s": t, "nrm": nrm, "tan": tan}


class Rows:
    def __init__(self, tiles_dir, variant="live", override=None):
        self.variant = variant
        self.tiles = ramp_lidar.Tiles(tiles_dir)          # live metadata (originals) + terrain
        if variant in ("current", "pilot"):
            self.meta = {}
            for name in self.tiles.meta:
                f = f"{tiles_dir}/{name}.json"
                if override and os.path.exists(f"{override}/{name}.json"):
                    f = f"{override}/{name}.json"
                self.meta[name] = json.load(open(f))
        elif variant == "live":
            self.meta = self.tiles.meta
        else:
            raise ValueError(variant)
        self.roads = None

    def ground(self, x, y):
        return self.tiles.ground(x, y)

    def decks(self):
        for name, m in self.meta.items():
            for k, d in enumerate((m.get("bridges") or {}).get("decks", [])):
                yield name, k, d

    def piers(self):
        for name, m in self.meta.items():
            for q in (m.get("bridges") or {}).get("piers", []):
                yield q

    def site_chains(self, cfg):
        rows = [(t, k, d) for t, k, d in self.decks() if is_site_row(cfg, d)]
        if cfg.get("seed"):                       # unnamed rows: the chains passing within r of the seed, among the rows in the fetch box
            sx, sy, sr = cfg["seed"]; fb = cfg["fetch"]
            rows = [(t, k, d) for t, k, d in rows if clip_box(np.array(d["p"], float)[:, :2], fb).any()]
            from shapely.geometry import LineString, Point
            keep = []
            for ch in ramp_lidar.chains_of(rows):
                if any(LineString(np.array(d["p"], float)[:, :2]).distance(Point(sx, sy)) <= sr for _, _, d in ch):
                    keep += ch
            rows = keep
        sel = {(t, k) for t, k, _ in rows}
        others = np.array([p[:2] for t, k, d in self.decks() if (t, k) not in sel and d["kind"] != "rail" for p in d["p"]], float)
        chains = []
        for ch in ramp_lidar.chains_of(rows):
            c = Chain(ch, ch[0][2]["kind"], ch[0][2].get("name", ""))
            g = self.ground(c.P[:, 0], c.P[:, 1])
            for end in (0, -1):
                dj = np.hypot(others[:, 0] - c.P[end, 0], others[:, 1] - c.P[end, 1]).min() if len(others) else 1e9
                el = c.P[end, 2] - (g[end] if not np.isnan(g[end]) else c.G[end])
                c.ends[end] = "junction" if dj < JUNCTION else ("grade" if el < AT_GRADE + 0.1 else "air")
            chains.append(c)
        chains.sort(key=lambda c: -c.length)
        for c in chains:   # an end on another site chain (the fork of the Geroldrampe, a continuation joint) is a joint, not air
            for end in (0, -1):
                if c.ends[end] == "air" and any(o is not c and np.hypot(o.P[:, 0] - c.P[end, 0], o.P[:, 1] - c.P[end, 1]).min() < JUNCTION for o in chains):
                    c.ends[end] = "fork"
        return chains

    def extend(self, chain, end, length):
        """Axis continuation beyond a chain end along the road graph (straight if none), as an (m,2) array starting at the end."""
        if self.roads is None:
            self.roads = ramp_lidar.Roads()
        start = chain.P[end, :2]
        d = start - chain.P[1 if end == 0 else -2, :2]; d = d / (np.linalg.norm(d) or 1.0)
        cont = self.roads.continue_from(start, d, length)
        if not cont:
            cont = [tuple(start + d * 2.0 * k) for k in range(1, int(length / 2.0) + 1)]
        return np.vstack([start[None, :], np.array(cont, float)])

    def site_piers(self, chains, dist=12.0):
        """Tile pier rows [x, y, zb, zt, w, hd, kind] within dist of a site chain axis."""
        from shapely.geometry import LineString, Point
        axes = [LineString(c.P[:, :2]) for c in chains]
        return [q for q in self.piers() if any(ax.distance(Point(q[0], q[1])) < dist for ax in axes)]


def is_site_row(cfg, d):
    """Does deck row d belong to the site? name match (substring or tuple of substrings; "" = any) and kind."""
    if d["kind"] not in cfg["kinds"]:
        return False
    m = cfg["match"]; name = d.get("name") or ""
    return any(x in name for x in m) if isinstance(m, tuple) else (m in name)


def clip_box(xy, box):
    x0, y0, x1, y1 = box
    return (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)


if __name__ == "__main__":
    from ramp_sites import site
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(HERE)), "web", "public", "tiles")
    for name in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["gerold", "duttweiler"]):
        cfg = site(name)
        for v in ("live", "current"):
            R = Rows(d, v)
            ch = R.site_chains(cfg)
            print(f"{name} {v}: {len(ch)} chains, {len(R.site_piers(ch))} tile piers near")
            for c in ch:
                print("  ", c, f"w {np.median(c.WL + c.WR):.1f} m")
