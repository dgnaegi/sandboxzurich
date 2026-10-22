"""LiDAR point cloud access (Kanton Zuerich 2021/22, OGD CC0), pilot tool.

Tiles: data/raw/lidar/<E>_<N>.laz (500 m tiles, LV95 + LN02, see research/lidar/README.md).
Coordinates are converted to game metres: x = E - 2681400, y = N - 1248700, z = Z - 408 - 3.06
(game frame; the 3.06 m shift is terrain.heights z_shift, see GAME_SHIFT).

Classes (data, not the metadata doc): 1 other, 2 ground, 3/4/5 low/mid/high vegetation, 6 building,
7 noise, 15 wires/masts, 17 bridge deck (doc says 10, data uses 17), 12 strip edge.

Usage:  from lidar import load, grids, profile
        P = load((834, -424, 991, -218))      # dict of arrays x,y,z,i,c,rn,nr
        G = grids(P, 0.5)                     # dict of 2D grids
        S = profile(P, [(894, -364), (931, -278)], half=6)
"""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "lidar"
CACHE = RAW / "crops"
OX, OY = 2681400.0, 1248700.0
GAME_SHIFT = 3.06  # the game world sits 3.06 m below swissALTI3D (terrain.heights z_shift)
Z0 = 408.0 + GAME_SHIFT  # z_game = Z(LN02) - Z0
TILE = 500
GROUND, VEG, BUILDING, BRIDGE, WIRE = 2, (3, 4, 5), 6, 17, 15
NONVEG = (1, 2, 6, 17)  # surfaces one can stand/drive on or that are solid


def tiles_for(bbox):
    x0, y0, x1, y1 = bbox
    e0, e1 = math.floor((x0 + OX) / TILE), math.floor((x1 + OX) / TILE)
    n0, n1 = math.floor((y0 + OY) / TILE), math.floor((y1 + OY) / TILE)
    return [(e * TILE, n * TILE) for e in range(e0, e1 + 1) for n in range(n0, n1 + 1)]


def load(bbox, use_cache=True):
    """Points inside bbox (x0,y0,x1,y1 in game metres), streamed per chunk (low RAM). Cached as npz."""
    import laspy

    key = hashlib.md5(repr(tuple(round(v, 2) for v in bbox)).encode()).hexdigest()[:10]
    cf = CACHE / f"crop_{key}.npz"
    if use_cache and cf.exists():
        return dict(np.load(cf))
    x0, y0, x1, y1 = bbox
    acc = {k: [] for k in "xyzicrn"}
    missing = []
    for e, n in tiles_for(bbox):
        f = RAW / f"{e}_{n}.laz"
        if not f.exists():
            missing.append(f.name)
            continue
        with laspy.open(f) as r:
            for ch in r.chunk_iterator(2_000_000):
                x = np.asarray(ch.x) - OX
                y = np.asarray(ch.y) - OY
                m = (x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)
                if not m.any():
                    continue
                acc["x"].append(x[m].astype(np.float32))
                acc["y"].append(y[m].astype(np.float32))
                acc["z"].append((np.asarray(ch.z)[m] - Z0).astype(np.float32))
                acc["i"].append(np.asarray(ch.intensity)[m].astype(np.uint16))
                acc["c"].append(np.asarray(ch.classification)[m].astype(np.uint8))
                acc["r"].append(np.asarray(ch.return_number)[m].astype(np.uint8))
                acc["n"].append(np.asarray(ch.number_of_returns)[m].astype(np.uint8))
    if missing:
        print("lidar: missing tiles", missing)
    P = {k: (np.concatenate(v) if v else np.zeros(0)) for k, v in acc.items()}
    if use_cache and len(P["x"]):
        CACHE.mkdir(parents=True, exist_ok=True)
        np.savez(cf, **P)
    return P


def sel(P, classes):
    m = np.isin(P["c"], classes)
    return {k: v[m] for k, v in P.items()}


def grids(P, res=0.5, bbox=None):
    """2D grids (row = y, col = x), NaN = no point. Keys: ground (median of cls 2), low, high (all points
    except noise/wires), top (max over NONVEG classes), top_c (class of that top point), bridge (median cls 17),
    count. Returns dict with 'x0','y0','res' and arrays."""
    x, y = P["x"], P["y"]
    x0, y0, x1, y1 = bbox or (x.min(), y.min(), x.max(), y.max())
    W, H = int(math.ceil((x1 - x0) / res)), int(math.ceil((y1 - y0) / res))
    ix = np.clip(((x - x0) / res).astype(int), 0, W - 1)
    iy = np.clip(((y - y0) / res).astype(int), 0, H - 1)
    flat = iy * W + ix
    z, c = P["z"], P["c"]
    out = {"x0": x0, "y0": y0, "res": res, "W": W, "H": H}

    def agg(mask, fn):
        g = np.full(W * H, np.nan, np.float32)
        if not mask.any():
            return g.reshape(H, W)
        f, zz = flat[mask], z[mask]
        o = np.argsort(f, kind="stable")
        f, zz = f[o], zz[o]
        u, st = np.unique(f, return_index=True)
        if fn == "min":
            g[u] = np.minimum.reduceat(zz, st)
        elif fn == "max":
            g[u] = np.maximum.reduceat(zz, st)
        elif fn == "median":
            en = np.append(st[1:], len(f))
            g[u] = [np.median(zz[a:b]) for a, b in zip(st, en)]
        return g.reshape(H, W)

    ok = (c != 7) & (c != 12) & (c != WIRE) & (c != 0)
    out["ground"] = agg(c == GROUND, "median")
    out["low"] = agg(ok, "min")
    out["high"] = agg(ok, "max")
    nv = np.isin(c, NONVEG)
    out["top"] = agg(nv, "max")
    out["bridge"] = agg(c == BRIDGE, "median")
    cnt = np.bincount(flat, minlength=W * H).reshape(H, W).astype(np.float32)
    out["count"] = cnt
    return out


def fill_nn(g, maxd=8):
    """Fill NaN cells of a grid by nearest valid value (limited to maxd cells)."""
    from scipy import ndimage as ndi

    bad = np.isnan(g)
    if not bad.any() or bad.all():
        return g
    d, (iy, ix) = ndi.distance_transform_edt(bad, return_indices=True)
    o = g[iy, ix]
    o[d > maxd] = np.nan
    return o


def sample_grid(G, key, x, y):
    ix = ((np.asarray(x) - G["x0"]) / G["res"]).astype(int)
    iy = ((np.asarray(y) - G["y0"]) / G["res"]).astype(int)
    ok = (ix >= 0) & (ix < G["W"]) & (iy >= 0) & (iy < G["H"])
    out = np.full(np.shape(x), np.nan)
    out[ok] = G[key][iy[ok], ix[ok]]
    return out


def resample_line(line, step=1.0):
    L = np.asarray(line, float)[:, :2]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(L, axis=0).T))]
    s = np.arange(0, d[-1] + 1e-9, step)
    return s, np.interp(s, d, L[:, 0]), np.interp(s, d, L[:, 1]), d


def profile(P, line, step=1.0, half=3.0, along=None):
    """Per station along polyline (game metres): for points within +-half m perpendicular and +-step/2 along:
    top   = 90th percentile of NONVEG heights (topmost solid surface, ignores single outliers/wires)
    topmax= max of NONVEG
    ground= 10th percentile of class 2 (+nan if none)  ; bridge = median of class 17
    veg   = max of vegetation. Returns dict of arrays + s,x,y."""
    s, px, py, _ = resample_line(line, step)
    dx, dy = np.gradient(px), np.gradient(py)
    nrm = np.hypot(dx, dy)
    tx, ty = dx / nrm, dy / nrm
    ax, ay, az, ac = P["x"], P["y"], P["z"], P["c"]
    from scipy.spatial import cKDTree

    T = cKDTree(np.c_[ax, ay])
    R = math.hypot(half, step / 2) + 0.01
    keys = ("top", "topmax", "ground", "bridge", "veg", "n")
    out = {k: np.full(len(s), np.nan) for k in keys}
    for i, nb in enumerate(T.query_ball_point(np.c_[px, py], R)):
        if not nb:
            continue
        nb = np.asarray(nb)
        u = ax[nb] - px[i]
        v = ay[nb] - py[i]
        al = u * tx[i] + v * ty[i]
        pe = -u * ty[i] + v * tx[i]
        m = (np.abs(al) <= step / 2) & (np.abs(pe) <= half)
        if not m.any():
            continue
        nb = nb[m]
        z, c = az[nb], ac[nb]
        out["n"][i] = len(nb)
        nv = np.isin(c, NONVEG)
        if nv.any():
            out["top"][i] = np.percentile(z[nv], 90)
            out["topmax"][i] = z[nv].max()
        g = c == GROUND
        if g.any():
            out["ground"][i] = np.percentile(z[g], 10)
        b = c == BRIDGE
        if b.any():
            out["bridge"][i] = np.median(z[b])
        v_ = np.isin(c, VEG)
        if v_.any():
            out["veg"][i] = z[v_].max()
    out.update(s=s, x=px, y=py)
    return out


def intensity_raster(P, res=0.10, classes=(2, 1, 17), bbox=None):
    """Mean intensity (0..65535) of road-level points per cell, NaN where empty. Uses given classes."""
    m = np.isin(P["c"], classes)
    x, y, i = P["x"][m], P["y"][m], P["i"][m].astype(np.float64)
    x0, y0, x1, y1 = bbox or (x.min(), y.min(), x.max(), y.max())
    W, H = int(math.ceil((x1 - x0) / res)), int(math.ceil((y1 - y0) / res))
    ix = np.clip(((x - x0) / res).astype(int), 0, W - 1)
    iy = np.clip(((y - y0) / res).astype(int), 0, H - 1)
    f = iy * W + ix
    s = np.bincount(f, i, W * H)
    n = np.bincount(f, None, W * H)
    with np.errstate(invalid="ignore", divide="ignore"):
        g = np.where(n > 0, s / n, np.nan).reshape(H, W)
    return {"img": g.astype(np.float32), "x0": x0, "y0": y0, "res": res, "W": W, "H": H}


# ---- cached 0.5 m rasters (pipeline/lidar_grid.py) ---------------------------------------------------------------
# API:  dtm(x, y) / bridge(x, y) / top(x, y) / bld(x, y) / veg(x, y) / chm(x, y)  -> float array (game metres), NaN = no data
#       masts(bbox=None) -> Nx5 [x, y, z_top, z_base, n_pts] of detected poles (game metres)
#       dtm_filled(x, y, maxd=6) nearest-valid fill (cells with no ground class: under buildings/bridges stay NaN beyond maxd)
# x, y are scalars or arrays in game metres; 500 m source tiles are cached (LRU, ~8 MB each).
GRID = ROOT / "data" / "build" / "lidar"
_GCACHE: dict = {}
_ND = -32768


def _gtile(e, n):
    k = (e, n)
    if k not in _GCACHE:
        f = GRID / f"g_{e}_{n}.npz"
        if f.exists():
            z = np.load(f)
            _GCACHE[k] = {q: z[q] for q in ("dtm", "bridge", "top", "bld", "veg")}
        else:
            _GCACHE[k] = None
        while len(_GCACHE) > 12:
            _GCACHE.pop(next(iter(_GCACHE)))
    return _GCACHE[k]


def _gsample(key, x, y):
    x = np.atleast_1d(np.asarray(x, float)); y = np.atleast_1d(np.asarray(y, float))
    X, Y = x + OX, y + OY
    e = np.floor(X / TILE).astype(int) * TILE
    n = np.floor(Y / TILE).astype(int) * TILE
    out = np.full(x.shape, np.nan)
    for te, tn in set(zip(e.tolist(), n.tolist())):
        m = (e == te) & (n == tn)
        t = _gtile(te, tn)
        if t is None:
            continue
        ix = np.clip(((X[m] - te) / 0.5).astype(int), 0, 999)
        iy = np.clip(((Y[m] - tn) / 0.5).astype(int), 0, 999)
        v = t[key][iy, ix].astype(float)
        v[v == _ND] = np.nan
        out[m] = v / 100.0
    return out


def dtm(x, y): return _gsample("dtm", x, y)
def bridge(x, y): return _gsample("bridge", x, y)
def top(x, y): return _gsample("top", x, y)
def bld(x, y): return _gsample("bld", x, y)
def veg(x, y): return _gsample("veg", x, y)


def chm(x, y):
    """Canopy height above ground (m): veg top minus dtm (dtm filled within 4 m); NaN where no vegetation return."""
    v = veg(x, y)
    g = dtm_filled(x, y, 4.0)
    return v - g


def dtm_filled(x, y, maxd=6.0):
    """DTM with holes filled from the nearest ground cell within maxd metres (8 ring samples, coarse)."""
    g = dtm(x, y)
    if not np.isnan(g).any():
        return g
    x = np.atleast_1d(np.asarray(x, float)); y = np.atleast_1d(np.asarray(y, float))
    bad = np.isnan(g)
    best = np.full(g.shape, np.nan)
    for r in np.arange(0.5, maxd + 0.01, 0.5):
        todo = bad & np.isnan(best)
        if not todo.any():
            break
        acc = np.full((8, int(todo.sum())), np.nan)
        for k in range(8):
            a = k * math.pi / 4
            acc[k] = dtm(x[todo] + r * math.cos(a), y[todo] + r * math.sin(a))
        with np.errstate(all="ignore"):
            v = np.nanmean(acc, axis=0)
        best[np.where(todo)[0]] = v
    g[bad] = best[bad]
    return g


_MASTS = None


def masts(bbox=None):
    global _MASTS
    if _MASTS is None:
        rows = []
        for f in sorted(GRID.glob("g_*.npz")):
            m = np.load(f)["mast"]
            if len(m):
                rows.append(m)
        _MASTS = np.concatenate(rows) if rows else np.zeros((0, 5), np.float32)
    if bbox is None:
        return _MASTS
    x0, y0, x1, y1 = bbox
    m = _MASTS
    return m[(m[:, 0] >= x0) & (m[:, 0] <= x1) & (m[:, 1] >= y0) & (m[:, 1] <= y1)]
