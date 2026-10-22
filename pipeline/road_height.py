"""Smooth road surface height ("Strassenhoehe").

The raw swissALTI3D grid is noisy along streets (bridge/building remnants, underpass interpolation, cut edges).
`apply(H, ways)` replaces the grid height inside every street corridor (+ a short blend band that becomes the
sidewalk) by a smoothed longitudinal profile along the OSM axis, with a 2 % crown. H is modified in place, so the
carriageway, curbs, sidewalks, hmap (walking / driving height) and every H.at() consumer share the same surface.
"""
import os

import numpy as np
import shapely

STEP = 1.0  # axis sampling (m)
MED = 9  # running median window (samples) - kills spikes from DTM artefacts
AVG = 21  # moving-average window (samples) after the median
JOIN_R = 18.0  # junction height harmonisation radius (m)
CROWN = 0.005  # cross fall (m per m): the carriageway mesh only has edge vertices, so a real 2 % crown would float the walk-height 13 cm above the asphalt
BLEND = 2.5  # m beyond the carriageway edge over which the surface returns to the terrain (minimum)
BLEND_K = 8.0  # road_smooth: blend band grows with the road/terrain offset (m of band per m of offset) so the sidewalk never becomes a steep ramp
BLEND_MAX = 8.0
HW_EXTRA = 5.0  # T23: the corridor is as wide as the drawn carriageway polygon (max this much wider than the OSM width); see _local_halfwidth
MAXSLOPE = 0.15  # longitudinal slope limit of the smoothed profile
MAXDEV = 1.0  # smoothed profile never leaves the real terrain by more than this (real underpasses / cuttings stay)
MAX_FILL = 1.2  # roads2: a cell is never raised by more than this (the blend used to fill rail cuttings/trenches under bridges by up to 7 m -> decks lifted 6 m above the street = "ramps")
MAX_FILL_IN = 3.0  # T23: cells INSIDE the carriageway may be filled more (a street edge next to a hollow / cutting stayed 20-40 cm below the road: the asphalt mesh has vertices on the polygon edge -> 10-20 cm dents)
MAX_SHAVE = 2.0  # roads2: ... nor lowered by more than this (embankment/quay walls next to a street stay)
JOIN_MAXDZ = 1.0  # shared vertices at very different heights are different levels (underpass vs bridge): not harmonised
LIDAR_ROAD = os.environ.get("SBZ_LIDAR_ROAD", "")  # "1": axis heights measured from the LiDAR DTM replace the swissALTI3D sample before smoothing; "2": + smoothed profile clamped to LiDAR +- LIDAR_CLAMP
LIDAR_GUARD = 1.5  # m: LiDAR "ground" further from the grid than this is a deck / embankment seen from above (class 2 on rail bridges), not the road
LIDAR_CLAMP = 0.2
SKIP_BRIDGE = ("yes", "viaduct", "movable", "boardwalk", "cantilever", "aqueduct")


def _runmed(z, k):
    h = k // 2
    p = np.pad(z, h, mode="edge")
    return np.median(np.lib.stride_tricks.sliding_window_view(p, k), axis=1)


def _runavg(z, k):
    h = k // 2
    p = np.pad(z, h, mode="edge")
    c = np.cumsum(np.insert(p, 0, 0.0))
    return (c[k:] - c[:-k]) / k


def _limit_slope(z, ds, m):
    """Forward/backward pass: no step steeper than m (keeps the shape, only shaves overshoots)."""
    z = z.copy()
    lim = m * ds
    for i in range(1, len(z)):
        z[i] = min(max(z[i], z[i - 1] - lim), z[i - 1] + lim)
    for i in range(len(z) - 2, -1, -1):
        z[i] = min(max(z[i], z[i + 1] - lim), z[i + 1] + lim)
    return z


def _lidar_axis(xy, hw):
    """Median LiDAR ground (class 2) across the carriageway (+-0.6 half width, 5 offsets) at each axis point; NaN where unmeasured
    (under decks / buildings / tunnels). Vehicles are not in class 2, so parked cars leave holes, not bumps."""
    import lidar
    d = np.gradient(xy, axis=0)
    nr = np.stack([-d[:, 1], d[:, 0]], 1)
    nr /= np.maximum(np.hypot(*nr.T), 1e-9)[:, None]
    offs = np.linspace(-0.6 * hw, 0.6 * hw, 5)
    Z = np.stack([lidar.dtm(*(xy + o * nr).T) for o in offs])
    ok = np.isfinite(Z).sum(0) >= 2
    out = np.full(len(xy), np.nan)
    out[ok] = np.nanmedian(Z[:, ok], axis=0)
    return out


def profiles(H, ways):
    """[(way, s (m), xy (n,2), z_smooth)] with junction heights harmonised between ways."""
    out = []
    for w in ways:
        t = w.get("tags", {})
        if t.get("bridge") in SKIP_BRIDGE or t.get("tunnel") in ("yes", "building_passage"):
            continue
        ln = w["line"]
        if ln.length < 2.0:
            continue
        n = max(2, int(round(ln.length / STEP)) + 1)
        s = np.linspace(0, ln.length, n)
        xy = np.array([(p.x, p.y) for p in shapely.line_interpolate_point(ln, s)])
        raw = H.at(xy[:, 0], xy[:, 1]).astype(np.float64)
        use, lid = raw, None
        if LIDAR_ROAD:
            lid = _lidar_axis(xy, w["w"] / 2)
            ok = np.isfinite(lid) & (np.abs(lid - raw) <= LIDAR_GUARD)
            lid = np.where(ok, lid, np.nan)
            use = np.where(ok, lid, raw)
        zs = _runavg(_runmed(use, MED), AVG)
        out.append({"w": w, "s": s, "xy": xy, "raw": raw, "z": zs, "lid": lid})
    # junctions: shared line vertices (rounded to 5 cm)
    nodes = {}
    for i, p in enumerate(out):
        for c in p["w"]["line"].coords:
            k = (round(c[0], 1), round(c[1], 1))
            si = float(p["w"]["line"].project(shapely.Point(c)))
            nodes.setdefault(k, []).append((i, si))
    for k, lst in nodes.items():
        if len({i for i, _ in lst}) < 2:
            continue
        zi = [np.interp(si, out[i]["s"], out[i]["z"]) for i, si in lst]
        if max(zi) - min(zi) > JOIN_MAXDZ:
            continue
        zj = float(np.mean(zi))
        for i, si in lst:
            p = out[i]
            d = zj - np.interp(si, p["s"], p["z"])
            p["z"] = p["z"] + d * np.clip(1 - np.abs(p["s"] - si) / JOIN_R, 0, 1)
    for p in out:
        p["z"] = np.clip(_limit_slope(p["z"], STEP, MAXSLOPE), p["raw"] - MAXDEV, p["raw"] + MAXDEV)
        if LIDAR_ROAD == "2" and p["lid"] is not None and np.isfinite(p["lid"]).any():
            ls = np.where(np.isfinite(p["lid"]), _runmed(np.nan_to_num(p["lid"], nan=0.0), 5), np.nan)
            ls = np.where(np.isfinite(p["lid"]), ls, p["z"])
            p["z"] = np.clip(p["z"], ls - LIDAR_CLAMP, ls + LIDAR_CLAMP)
    return out


def carve_underpasses(H, ways, report=True, blend=2.0):
    """underpass_infer.spans(): the DTM plateau of an untagged underpass is cut down to the line between the portal levels (flat floor,
    corridor = carriageway + 1 m, `blend` m of wall) BEFORE the profile smoothing, so the smoothed street follows the floor. Only ever lowers."""
    import underpass_infer
    sp = underpass_infer.spans(H, ways)
    ny, nx = H.z.shape
    for c in sp:
        ln = c["line"]
        hw = 4.0
        for w in ways:   # corridor width: widest street that runs along this span
            if w["hw"] != "service" and w["line"].distance(ln.interpolate(ln.length / 2)) < 3.0:
                hw = max(hw, w["w"] / 2)
        hw += 1.0
        x0, y0, x1, y1 = ln.buffer(hw + blend + 1).bounds
        gx0, gx1 = max(int((x0 - H.x0) / H.step), 0), min(int((x1 - H.x0) / H.step) + 2, nx)
        gy0, gy1 = max(int((y0 - H.y0) / H.step), 0), min(int((y1 - H.y0) / H.step) + 2, ny)
        X, Y = np.meshgrid(H.x0 + np.arange(gx0, gx1) * H.step, H.y0 + np.arange(gy0, gy1) * H.step)
        pts = shapely.points(X.ravel(), Y.ravel())
        d = shapely.distance(ln, pts)
        sp_ = shapely.line_locate_point(ln, pts)
        z = c["z0"] + (c["z1"] - c["z0"]) * np.clip(sp_ / max(ln.length, 1e-6), 0, 1)
        t = np.clip((d - hw) / blend, 0, 1)
        tz = z * (1 - t) + H.z[gy0:gy1, gx0:gx1].ravel() * t
        cur = H.z[gy0:gy1, gx0:gx1].ravel()
        H.z[gy0:gy1, gx0:gx1] = np.where(d <= hw + blend, np.minimum(cur, tz), cur).reshape(X.shape).astype(H.z.dtype)
    if report and sp:
        print(f"road_height: {len(sp)} underpass spans carved ({sum(c['len'] for c in sp):.0f} m)")


def _local_halfwidth(H, xy, roads):
    """Half-width of the drawn carriageway polygon at the axis points xy (distance to the polygon edge, raster EDT on the height grid).
    The asphalt mesh has vertices on the polygon edge; where the corridor (OSM width) was narrower, those edge vertices took the height of a
    neighbouring hollow / embankment and tilted the road surface (10-30 cm bumps, Hohlstrasse, Foerrlibuckstrasse, research/bumps.md)."""
    from scipy import ndimage as ndi
    ny, nx = H.z.shape
    x0, x1 = xy[:, 0].min() - 30, xy[:, 0].max() + 30
    y0, y1 = xy[:, 1].min() - 30, xy[:, 1].max() + 30
    gx0, gx1 = max(int((x0 - H.x0) / H.step), 0), min(int((x1 - H.x0) / H.step) + 1, nx)
    gy0, gy1 = max(int((y0 - H.y0) / H.step), 0), min(int((y1 - H.y0) / H.step) + 1, ny)
    X, Y = np.meshgrid(H.x0 + np.arange(gx0, gx1) * H.step, H.y0 + np.arange(gy0, gy1) * H.step)
    shapely.prepare(roads)
    inside = np.zeros(X.shape, bool)
    for r0 in range(0, X.shape[0], 256):
        inside[r0:r0 + 256] = shapely.contains_xy(roads, X[r0:r0 + 256], Y[r0:r0 + 256])
    edt = ndi.distance_transform_edt(inside) * H.step
    ci = np.clip(np.round((xy[:, 0] - H.x0) / H.step).astype(int) - gx0, 0, X.shape[1] - 1)
    ri = np.clip(np.round((xy[:, 1] - H.y0) / H.step).astype(int) - gy0, 0, X.shape[0] - 1)
    return edt[ri, ci]


def apply(H, ways, report=True, roads=None):
    """Blend all street profiles into H (in place). Overlapping streets (dual carriageways, side roads, junctions)
    are averaged with distance weights instead of "nearest wins", so no patchwork steps appear between profiles."""
    carve_underpasses(H, ways, report)   # T22: streets that run under an embankment keep their floor instead of climbing over it
    P = profiles(H, ways)
    if not P:
        return
    X = np.concatenate([p["xy"][:, 0] for p in P])
    Y = np.concatenate([p["xy"][:, 1] for p in P])
    Z = np.concatenate([p["z"] for p in P])
    HW = np.concatenate([np.full(len(p["s"]), p["w"]["w"] / 2) for p in P])
    if roads is not None and not roads.is_empty:   # T23: corridor = drawn carriageway polygon (not narrower than the mesh edge vertices)
        loc = _local_halfwidth(H, np.concatenate([p["xy"] for p in P]), roads)
        HW = np.maximum(HW, np.minimum(loc, HW + HW_EXTRA))
    RAW = np.concatenate([p["raw"] for p in P])
    dev = np.abs(Z - RAW)  # road_smooth: offset to the terrain on the axis and 2.5 m beside the edge (hillside roads)
    off = 0
    for p in P:
        p["hwv"] = HW[off: off + len(p["s"])]
        off += len(p["s"])
        d = np.gradient(p["xy"], axis=0)
        nr = np.stack([-d[:, 1], d[:, 0]], 1)
        nr /= np.maximum(np.hypot(*nr.T), 1e-9)[:, None]
        hwp = (p["hwv"] + BLEND)[:, None]
        p["dev"] = np.maximum.reduce([np.abs(p["z"] - H.at(*(p["xy"] + sg * nr * hwp).T)) for sg in (1, -1)])
    dev = np.maximum(dev, np.concatenate([p["dev"] for p in P]))
    BL = np.clip(BLEND_K * dev, BLEND, BLEND_MAX)  # per-sample blend width
    ny, nx = H.z.shape
    st = H.step
    R = int(np.ceil((HW.max() + BL.max()) / st)) + 1
    best = np.full((ny, nx), np.inf)  # smallest normalised distance e / blend to a carriageway edge (negative inside)
    sw = np.zeros(ny * nx)
    sz = np.zeros(ny * nx)
    cx = np.round((X - H.x0) / st).astype(int)
    cy = np.round((Y - H.y0) / st).astype(int)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            gx, gy = cx + dx, cy + dy
            d = np.hypot(H.x0 + gx * st - X, H.y0 + gy * st - Y)
            e = (d - HW) / BL
            ok = (gx >= 0) & (gx < nx) & (gy >= 0) & (gy < ny) & (e < 1.0)
            idx = np.where(ok)[0]
            if not len(idx):
                continue
            gxi, gyi, ei = gx[idx], gy[idx], e[idx]
            flat = gyi * nx + gxi
            wgt = (1 - d[idx] / (HW[idx] + BL[idx])) ** 2
            np.add.at(sw, flat, wgt)
            np.add.at(sz, flat, wgt * (Z[idx] - CROWN * np.minimum(d[idx], HW[idx])))
            order = np.argsort(-ei)  # smallest e written last -> wins duplicates
            sel = ei[order] < best[gyi[order], gxi[order]]
            best[gyi[order][sel], gxi[order][sel]] = ei[order][sel]
    m = np.isfinite(best)
    t = np.clip(best[m], 0, 1)
    cov = 1 - t * t * (3 - 2 * t)  # 1 in the carriageway, 0 at the end of the blend band
    tz = sz[m.ravel()] / sw[m.ravel()]
    old = H.z[m].copy()
    new = old * (1 - cov) + tz * cov
    new = old + np.clip(new - old, -MAX_SHAVE, np.where(cov > 0.9, MAX_FILL_IN, MAX_FILL))  # roads2 (+ T23: inside the carriageway the fill cap is MAX_FILL_IN)
    H.z[m] = new.astype(H.z.dtype)
    if report:
        dz = np.abs(H.z[m] - old)
        print(f"road_height: {len(P)} ways, {int(m.sum())} cells, mean change {dz.mean():.2f} m, p99 {np.percentile(dz, 99):.2f} m")


def ground_exclusion(EX, BR, ways):
    """Bridge exclusion minus the carriageways of ground streets that pass under a deck (they keep their asphalt)."""
    chain = {i for b in BR for i in b["ids"]}
    under = [w["line"].buffer(w["w"] / 2 + 0.2, cap_style="flat") for w in ways
             if w["id"] not in chain and w["tags"].get("bridge") in (None, "no")]
    return EX.difference(shapely.union_all(under)) if under and not EX.is_empty else EX


def clip_ways(ways, EX, EXR, BR):
    """Chain ways of a bridge (deck + ramps) are cut by the full exclusion, all other ways only by EXR."""
    import bridges
    chain = {i for b in BR for i in b["ids"]}
    mine = bridges.clip_ways([w for w in ways if w["id"] in chain], EX)
    rest = bridges.clip_ways([w for w in ways if w["id"] not in chain], EXR)
    return rest + mine
