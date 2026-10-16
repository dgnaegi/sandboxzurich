"""Rivers, canals and basins: water surface, river bed, bank walls, shader data, colliders (research/rivers.md).

prepare(H, G, EX, BR, nodes, els) -> W   once per build (before the tile pool forks). Lowers the bed into the height
                                          grid H (only inside the water polygon, >= 3 m from the bank) and keeps H outside as is.
W.poly            water polygon (AV Bodenbedeckung 'water' + OSM natural=water, bridge gaps closed); subtract it from the ground
W.tile(gm, tb)    adds bed + bank walls to the ground mesh gm, returns the water surface Mesh (or None)
W.meta(tb)        {"water": {...}} per-tile shader data (distance to bank, flow, pier foam) for web/src/world/water.ts
W.colliders(tb)   rings the player must not enter (bank edge, except bridge decks and bathing/stair zones)

Level: the DTM inside the water is the water surface (swissALTI3D), smoothed along the reach and capped to stay >= 0.6 m under
the lowest nearby bank. Flow: principal axis of the water body (structure tensor), direction from the OSM river way or a
global north/west reference (overrides/water.json). Terrain API (terrain.py, road_height.py) is not touched.
"""
import base64
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.strtree import STRtree

from mesh import Mesh, drape
from config import TILE
from styles import LAYER

CFG = Path(__file__).resolve().parent / "overrides" / "water.json"
MIN_AREA = 150.0  # m2; smaller basins are fountains (places_detail)
BED = (78, 84, 74)
WATER_COL = (20, 70, 66)
RES = 4.0  # shader texture resolution (m)
DMAX = 10.0  # distance to bank stored (m)


def _blur(a, s):
    """Separable gaussian (zero padded), sigma in cells."""
    r = max(1, int(3 * s))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2)
    k = (k / k.sum()).astype(np.float32)
    h, w = a.shape
    p = np.pad(a, ((0, 0), (r, r)))
    o = np.zeros_like(a)
    for i, wt in enumerate(k):
        o += wt * p[:, i:i + w]
    p = np.pad(o, ((r, r), (0, 0)))
    o2 = np.zeros_like(a)
    for i, wt in enumerate(k):
        o2 += wt * p[i:i + h]
    return o2


def _nblur(v, w, s):
    """Normalised blur: weighted mean of v (weights w) smoothed with sigma s."""
    num, den = _blur(v * w, s), _blur(w, s)
    return np.where(den > 1e-4, num / np.maximum(den, 1e-4), np.nan)


def _minf(a, r):
    """Minimum filter, radius r cells (square)."""
    h, w = a.shape
    p = np.pad(a, r, constant_values=np.inf)
    o = np.full_like(a, np.inf)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            o = np.minimum(o, p[dy:dy + h, dx:dx + w])
    return o


class _Grid:
    """Duck-typed Heights (drape() only calls .at())."""

    def __init__(self, x0, y0, step, z, off=0.0):
        self.x0, self.y0, self.step, self.z, self.off = x0, y0, step, z, off

    def at(self, x, y):
        z = self.z
        fx = np.clip((np.asarray(x) - self.x0) / self.step, 0, z.shape[1] - 1.001)
        fy = np.clip((np.asarray(y) - self.y0) / self.step, 0, z.shape[0] - 1.001)
        ix, iy = fx.astype(int), fy.astype(int)
        tx, ty = fx - ix, fy - iy
        return (z[iy, ix] * (1 - tx) * (1 - ty) + z[iy, ix + 1] * tx * (1 - ty)
                + z[iy + 1, ix] * (1 - tx) * ty + z[iy + 1, ix + 1] * tx * ty) + self.off


class Water:
    pass


def _osm_water(nodes, els):
    """OSM natural=water polygons (not pond/basin/wastewater) and river/canal lines with their direction."""
    polys, lines = [], []
    for e in els:
        if e["type"] != "way":
            continue
        t = e.get("tags") or {}
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
        if len(pts) < 2:
            continue
        if t.get("waterway") in ("river", "canal") and t.get("tunnel") not in ("yes", "culvert") and t.get("bridge") != "yes":
            lines.append(np.asarray(pts))
        elif t.get("natural") == "water" and t.get("water") not in ("pond", "basin", "wastewater") and pts[0] == pts[-1] and len(pts) >= 4:
            polys.append(Polygon(pts).buffer(0))
    return polys, lines


def prepare(H, G, EX, BR, nodes, els):
    cfg = json.load(open(CFG)) if CFG.exists() else {}
    W = Water()
    osm_polys, osm_lines = _osm_water(nodes, els)
    raw = [p for p in getattr(G["water"], "geoms", [G["water"]]) if p.area >= MIN_AREA]
    raw += [p for p in osm_polys if p.area >= 400]
    if not raw:
        W.poly, W.parts = Polygon(), []
        W.empty = True
        return W
    water = shapely.union_all(raw).buffer(0)
    closed = water.buffer(14).buffer(-14)
    under = closed.intersection(EX.buffer(1.0)) if EX is not None and not EX.is_empty else Polygon()
    poly = shapely.set_precision(shapely.union_all([water, under]).buffer(0.05).buffer(-0.05).simplify(0.2), 0.01)
    hb = box(H.x0 + 8, H.y0 + 8, H.x0 + (H.z.shape[1] - 1) * H.step - 8, H.y0 + (H.z.shape[0] - 1) * H.step - 8)
    poly = poly.intersection(hb)
    poly = shapely.union_all([p for p in getattr(poly, "geoms", [poly]) if p.geom_type == "Polygon" and p.area >= MIN_AREA])
    W.empty = poly.is_empty
    W.poly = poly
    if W.empty:
        W.parts = []
        return W
    W.parts = [orient(p, 1.0) for p in getattr(poly, "geoms", [poly])]
    W.tree = STRtree(W.parts)
    ny, nx = H.z.shape
    st = H.step
    ZW = np.full((ny, nx), np.nan, np.float32)
    DP = np.full((ny, nx), np.nan, np.float32)   # bed depth below the surface
    FX = np.zeros((ny, nx), np.float32)
    FY = np.zeros((ny, nx), np.float32)
    FS = np.zeros((ny, nx), np.float32)
    # bathing / stair zones (Flussbad Letten ...): shallow, enterable
    acc = [shapely.Polygon(a["poly"]) for a in cfg.get("access", [])]
    for e in els:  # bathing places mapped in OSM (Flussbad Letten ...): their lot + 30 m of river in front
        t = e.get("tags") or {}
        if e["type"] == "way" and t.get("name") in cfg.get("access_names", []):
            pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(pts) >= 4:
                acc.append(Polygon(pts).buffer(0).buffer(cfg.get("access_buffer", 30.0)))
    W.access = shapely.union_all(acc).buffer(0) if acc else Polygon()
    # flow reference: OSM river/canal tangents (downstream = way direction), else a global direction
    ref = np.array(cfg.get("flow_ref", [-0.25, 0.95]), float)
    ref /= np.hypot(*ref)
    spts, stan = [], []
    for ln in osm_lines:
        d = np.diff(ln, axis=0)
        L = np.hypot(d[:, 0], d[:, 1])
        for i in range(len(d)):
            n = max(1, int(L[i] // 10))
            for k in range(n):
                spts.append(ln[i] + d[i] * (k + 0.5) / n)
                stan.append(d[i] / max(L[i], 1e-6))
    stree = STRtree(shapely.points(np.asarray(spts))) if spts else None
    stan = np.asarray(stan)
    regions = cfg.get("flow", [])
    for part in W.parts:
        x0, y0, x1, y1 = part.bounds
        pad = 70.0
        i0, i1 = max(0, int((x0 - pad - H.x0) / st)), min(nx, int((x1 + pad - H.x0) / st) + 2)
        j0, j1 = max(0, int((y0 - pad - H.y0) / st)), min(ny, int((y1 + pad - H.y0) / st) + 2)
        gx, gy = np.meshgrid(H.x0 + np.arange(i0, i1) * st, H.y0 + np.arange(j0, j1) * st)
        inside = shapely.contains_xy(part, gx, gy)
        core = shapely.contains_xy(part.buffer(-1.5), gx, gy)
        if core.sum() < 6:
            core = inside
        hz = H.z[j0:j1, i0:i1]
        zw0 = _nblur(np.where(core, hz, 0.0).astype(np.float32), core.astype(np.float32), 10)
        ring = shapely.contains_xy(part.buffer(9.0), gx, gy) & ~shapely.contains_xy(part.buffer(1.5), gx, gy)
        bank = _minf(np.where(ring, hz, np.inf).astype(np.float32), 2)
        okb = np.isfinite(bank)
        zb = _nblur(np.where(okb, bank, 0.0).astype(np.float32), okb.astype(np.float32), 8)
        zw = np.where(np.isnan(zb), zw0, np.minimum(zw0, zb - 0.6))
        zw = _nblur(np.nan_to_num(zw).astype(np.float32), (~np.isnan(zw)).astype(np.float32), 5)
        zw = np.where(np.isnan(zw), np.nanmedian(zw0), zw)
        # flow field: principal axis of the water body
        wm = inside.astype(np.float32)
        m = _blur(wm, 12) + 1e-6
        mx, my = _blur(wm * gx, 12) / m, _blur(wm * gy, 12) / m
        cxx = _blur(wm * gx * gx, 12) / m - mx * mx
        cyy = _blur(wm * gy * gy, 12) / m - my * my
        cxy = _blur(wm * gx * gy, 12) / m - mx * my
        th = 0.5 * np.arctan2(2 * cxy, cxx - cyy)
        tr = cxx + cyy + 1e-6
        dl = np.sqrt(((cxx - cyy) / 2) ** 2 + cxy ** 2)
        aniso = np.clip(dl / (tr / 2), 0, 1)
        dx, dy = np.cos(th), np.sin(th)
        rx = np.full_like(dx, ref[0])
        ry = np.full_like(dx, ref[1])
        if stree is not None:  # follow the OSM way direction near it (sparse samples, smoothed)
            sel = np.flatnonzero(inside.ravel())[::5]
            if len(sel):
                q = shapely.points(gx.ravel()[sel], gy.ravel()[sel])
                idx = stree.nearest(q)
                ok = shapely.distance(q, stree.geometries.take(idx)) < 120
                wq, xq, yq = (np.zeros(gx.size, np.float32) for _ in range(3))
                wq[sel[ok]] = 1.0
                xq[sel[ok]], yq[sel[ok]] = stan[idx[ok], 0], stan[idx[ok], 1]
                hx = _nblur(xq.reshape(gx.shape), wq.reshape(gx.shape), 6)
                hy = _nblur(yq.reshape(gx.shape), wq.reshape(gx.shape), 6)
                use = ~np.isnan(hx)
                rx, ry = np.where(use, hx, rx), np.where(use, hy, ry)
        for rg in regions:
            near = np.hypot(gx - rg["c"][0], gy - rg["c"][1]) < rg["r"]
            v = np.asarray(rg["dir"], float); v /= np.hypot(*v)
            rx, ry = np.where(near, v[0], rx), np.where(near, v[1], ry)
        flip = np.where(dx * rx + dy * ry < 0, -1.0, 1.0)
        dx, dy = dx * flip, dy * flip
        sl = (slice(j0, j1), slice(i0, i1))
        inw = inside
        ZW[sl] = np.where(inw, zw, ZW[sl])
        FX[sl] = np.where(inw, dx, FX[sl]); FY[sl] = np.where(inw, dy, FY[sl]); FS[sl] = np.where(inw, aniso, FS[sl])
        depth = np.full(gx.shape, 0.9, np.float32)
        if not W.access.is_empty:
            depth = np.where(shapely.contains_xy(W.access, gx, gy), 0.35, depth)
        DP[sl] = np.where(inw, depth, DP[sl])
        # window values outside the polygon stay valid for bilinear lookups at the edge
        ZW[sl] = np.where(np.isnan(ZW[sl]), zw, ZW[sl])
        DP[sl] = np.where(np.isnan(DP[sl]), depth, DP[sl])
        # bed into the height grid: >= 3 m inside the bank only (ground vertices on the bank keep their DTM height)
        deep = shapely.contains_xy(part.buffer(-3.0), gx, gy)
        H.z[sl] = np.where(deep, np.minimum(hz, zw - depth), hz)
    W.zw = _Grid(H.x0, H.y0, st, ZW)
    W.bed = _Grid(H.x0, H.y0, st, ZW - DP)
    W.H, W.FX, W.FY, W.FS = H, FX, FY, FS
    W.piers = np.array([[q[0], q[1]] for b in BR for q in b["piers"]] or [[1e9, 1e9]])
    W.ex = EX
    W.walls = cfg.get("walls", [])
    ok = np.isfinite(ZW)
    print(f"water: {len(W.parts)} bodies, {poly.area:.0f} m2, level {np.nanmin(ZW[ok]):.1f}..{np.nanmax(ZW[ok]):.1f}, "
          f"{int(H.z.size - (H.z == H.z).sum())} nan")
    return W


def _wall_style(W, x, y):
    for w in W.walls:
        if np.hypot(x - w["c"][0], y - w["c"][1]) < w["r"]:
            return LAYER[w["layer"]], tuple(w["color"]), w.get("uv", 1.0)
    return LAYER["sidewalk"], (170, 170, 164), 3.0  # default: concrete channel wall


def tile(W, gm, tb):
    """Bed + bank walls into gm; returns the water surface Mesh or None."""
    if W.empty:
        return None
    part = [W.parts[i] for i in W.tree.query(tb)]
    part = [p for p in part if p.intersects(tb)]
    if not part:
        return None
    area = shapely.union_all([p.intersection(tb) for p in part])
    if area.is_empty or area.area < 1.0:
        return None
    wm = Mesh()
    drape(wm, area, W.zw, 0.0, WATER_COL, cell=TILE / 10, layer=0, uv_scale=8.0)
    drape(gm, area, W.bed, 0.0, BED, cell=TILE / 10, layer=LAYER["dach_kies"], uv_scale=2.0)
    H = W.H
    for p in part:
        for ring in [p.exterior] + list(p.interiors):
            for seg in getattr(ring.intersection(tb), "geoms", [ring.intersection(tb)]):
                if seg.geom_type != "LineString" or seg.length < 0.3:
                    continue
                n = max(1, int(np.ceil(seg.length / 6.0)))
                pts = np.array([seg.interpolate(seg.length * i / n).coords[0] for i in range(n + 1)])
                top = H.at(pts[:, 0], pts[:, 1])
                zw = W.zw.at(pts[:, 0], pts[:, 1])
                bot = W.bed.at(pts[:, 0], pts[:, 1])
                top = np.maximum(top, zw + 0.05)
                lay, col, us = _wall_style(W, *pts[len(pts) // 2])
                inacc = (not W.access.is_empty) and W.access.distance(Point(*pts[len(pts) // 2])) < 1.0
                for k in range(n):
                    a, b = pts[k], pts[k + 1]
                    d = b - a
                    L = float(np.hypot(*d))
                    if L < 0.05 or max(top[k], top[k + 1]) - min(bot[k], bot[k + 1]) < 0.05:
                        continue
                    nrm = np.array([-d[1], d[0], 0]) / L  # water is on the left (oriented rings)
                    if inacc:  # ramp / steps into the water instead of a wall (1:2)
                        dz = np.array([top[k] - bot[k], top[k + 1] - bot[k + 1]])
                        run = np.minimum(dz * 2.0, 6.0)
                        pb = [(a + nrm[:2] * run[0]), (b + nrm[:2] * run[1])]
                        q = np.array([[pb[0][0], pb[0][1], bot[k]], [pb[1][0], pb[1][1], bot[k + 1]],
                                      [b[0], b[1], top[k + 1]], [a[0], a[1], top[k]]], np.float32)
                        nn = np.cross(q[1] - q[0], q[3] - q[0]); nn /= (np.linalg.norm(nn) + 1e-9)
                        if nn[2] < 0:
                            nn = -nn
                        gm.add(q, np.array([[0, 2, 1], [0, 3, 2]], np.uint32), nn, (190, 186, 176),
                               uv=np.array([[0, 0], [L / 3, 0], [L / 3, run.max() / 3], [0, run.max() / 3]]), layer=LAYER["sidewalk"])
                        continue
                    q = np.array([[a[0], a[1], bot[k]], [b[0], b[1], bot[k + 1]], [b[0], b[1], top[k + 1]], [a[0], a[1], top[k]]], np.float32)
                    hh = float(max(top[k], top[k + 1]) - min(bot[k], bot[k + 1]))
                    gm.add(q, np.array([[0, 2, 1], [0, 3, 2]], np.uint32), nrm, col,
                           uv=np.array([[0, 0], [L / us, 0], [L / us, hh / us], [0, hh / us]]), layer=lay)
    return wm


def meta(W, tb):
    """Per-tile shader texture (RGBA8, 4 m): R distance to bank (0..10 m), G/B flow xy*strength, A pier proximity."""
    if W.empty:
        return {}
    part = [W.parts[i] for i in W.tree.query(tb)]
    part = [p for p in part if p.intersects(tb)]
    if not part:
        return {}
    x0, y0 = tb.bounds[0], tb.bounds[1]
    n = int(TILE / RES) + 1
    gx, gy = np.meshgrid(x0 + np.arange(n) * RES, y0 + np.arange(n) * RES)
    shp = gx.shape
    area = shapely.union_all(part)
    inside = shapely.contains_xy(area, gx.ravel(), gy.ravel())
    if not inside.any():
        return {}
    bd = area.boundary.intersection(tb.buffer(DMAX + 2))
    pts = shapely.points(gx.ravel()[inside], gy.ravel()[inside])
    d = np.zeros(gx.size, np.float32)
    d[inside] = np.clip(shapely.distance(bd, pts), 0, DMAX)
    st = W.H.step
    ix = np.clip(np.round((gx - W.H.x0) / st).astype(int), 0, W.FX.shape[1] - 1)
    iy = np.clip(np.round((gy - W.H.y0) / st).astype(int), 0, W.FX.shape[0] - 1)
    fx, fy, fs = W.FX[iy, ix].ravel(), W.FY[iy, ix].ravel(), W.FS[iy, ix].ravel()
    pa = np.zeros(gx.size, np.float32)
    near = np.hypot(W.piers[:, 0] - (x0 + TILE / 2), W.piers[:, 1] - (y0 + TILE / 2)) < TILE
    if near.any():
        pp = shapely.points(W.piers[near])
        t = STRtree(pp)
        dd = shapely.distance(pts, pp[t.nearest(pts)])
        pa[inside] = np.clip(1 - dd / 7.0, 0, 1)
    rgba = np.zeros((gx.size, 4), np.uint8)
    rgba[:, 0] = np.round(d / DMAX * 255)
    rgba[:, 1] = np.round(128 + 127 * np.clip(fx * fs, -1, 1))
    rgba[:, 2] = np.round(128 + 127 * np.clip(fy * fs, -1, 1))
    rgba[:, 3] = np.round(pa * 255)
    rgba[~inside] = (0, 128, 128, 0)
    return {"water": {"x0": x0, "y0": y0, "n": n, "res": RES, "dmax": DMAX,
                      "level": round(float(np.nanmedian(W.zw.at(gx.ravel()[inside], gy.ravel()[inside]))), 2),
                      "rgba": base64.b64encode(rgba.reshape(shp + (4,)).tobytes()).decode()}}


def colliders(W, tb):
    """Water rings (no bridge decks, no access zones), shrunk 0.2 m so the player stops right at the edge."""
    if W.empty:
        return []
    part = [W.parts[i] for i in W.tree.query(tb)]
    part = [p for p in part if p.intersects(tb)]
    if not part:
        return []
    g = shapely.union_all(part).buffer(-0.2).intersection(tb.buffer(1))
    if W.ex is not None and not W.ex.is_empty:
        g = g.difference(W.ex)
    if not W.access.is_empty:
        g = g.difference(W.access)
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "Polygon" and p.area > 2.0:
            out.append(np.round(np.asarray(p.simplify(0.1).exterior.coords)[:-1], 2).tolist())
    return out
