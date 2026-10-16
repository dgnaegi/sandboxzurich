"""Smooth road surface height ("Strassenhoehe").

The raw swissALTI3D grid is noisy along streets (bridge/building remnants, underpass interpolation, cut edges).
`apply(H, ways)` replaces the grid height inside every street corridor (+ a short blend band that becomes the
sidewalk) by a smoothed longitudinal profile along the OSM axis, with a 2 % crown. H is modified in place, so the
carriageway, curbs, sidewalks, hmap (walking / driving height) and every H.at() consumer share the same surface.
"""
import numpy as np
import shapely

STEP = 1.0  # axis sampling (m)
MED = 9  # running median window (samples) - kills spikes from DTM artefacts
AVG = 21  # moving-average window (samples) after the median
JOIN_R = 18.0  # junction height harmonisation radius (m)
CROWN = 0.005  # cross fall (m per m): the carriageway mesh only has edge vertices, so a real 2 % crown would float the walk-height 13 cm above the asphalt
BLEND = 2.5  # m beyond the carriageway edge over which the surface returns to the terrain
MAXSLOPE = 0.15  # longitudinal slope limit of the smoothed profile
MAXDEV = 1.0  # smoothed profile never leaves the real terrain by more than this (real underpasses / cuttings stay)
JOIN_MAXDZ = 1.0  # shared vertices at very different heights are different levels (underpass vs bridge): not harmonised
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
        zs = _runavg(_runmed(raw, MED), AVG)
        out.append({"w": w, "s": s, "xy": xy, "raw": raw, "z": zs})
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
    return out


def apply(H, ways, report=True):
    """Blend all street profiles into H (in place). Overlapping streets (dual carriageways, side roads, junctions)
    are averaged with distance weights instead of "nearest wins", so no patchwork steps appear between profiles."""
    P = profiles(H, ways)
    if not P:
        return
    X = np.concatenate([p["xy"][:, 0] for p in P])
    Y = np.concatenate([p["xy"][:, 1] for p in P])
    Z = np.concatenate([p["z"] for p in P])
    HW = np.concatenate([np.full(len(p["s"]), p["w"]["w"] / 2) for p in P])
    ny, nx = H.z.shape
    st = H.step
    R = int(np.ceil((HW.max() + BLEND) / st)) + 1
    best = np.full((ny, nx), np.inf)  # smallest distance to a carriageway edge (negative inside)
    sw = np.zeros(ny * nx)
    sz = np.zeros(ny * nx)
    cx = np.round((X - H.x0) / st).astype(int)
    cy = np.round((Y - H.y0) / st).astype(int)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            gx, gy = cx + dx, cy + dy
            d = np.hypot(H.x0 + gx * st - X, H.y0 + gy * st - Y)
            e = d - HW
            ok = (gx >= 0) & (gx < nx) & (gy >= 0) & (gy < ny) & (e < BLEND)
            idx = np.where(ok)[0]
            if not len(idx):
                continue
            gxi, gyi, ei = gx[idx], gy[idx], e[idx]
            flat = gyi * nx + gxi
            wgt = (1 - d[idx] / (HW[idx] + BLEND)) ** 2
            np.add.at(sw, flat, wgt)
            np.add.at(sz, flat, wgt * (Z[idx] - CROWN * np.minimum(d[idx], HW[idx])))
            order = np.argsort(-ei)  # smallest e written last -> wins duplicates
            sel = ei[order] < best[gyi[order], gxi[order]]
            best[gyi[order][sel], gxi[order][sel]] = ei[order][sel]
    m = np.isfinite(best)
    t = np.clip(best[m] / BLEND, 0, 1)
    cov = 1 - t * t * (3 - 2 * t)  # 1 in the carriageway, 0 at the end of the blend band
    tz = sz[m.ravel()] / sw[m.ravel()]
    old = H.z[m].copy()
    H.z[m] = (old * (1 - cov) + tz * cov).astype(H.z.dtype)
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
