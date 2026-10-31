"""Per-station measurements of a modelled ramp chain against Scope B (cadastre polygons) and Scope A (LiDAR rasters).

At every 2 m station of a chain the normal is cast across the axis; where it lies inside the cadastre's bridge polygons
(`deck`), carriageway polygons (`carriageway`) or next to walls (`wall`) the left / right extents are recorded. Left = +normal.
Model classes per station: grade (deck < 0.3 m above the game terrain), solid (underside on the ground: embankment / skirt),
deck (elevated with a free underside). LiDAR: 35th percentile of the class-17 deck top in the central strip of the modelled
width, else the class-2 ground there (embankment / at grade), as in pipeline/ramp_lidar.py.
"""
from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import lidar  # noqa: E402
import ramp_lidar  # noqa: E402
from rows import is_site_row  # noqa: E402

HALF = 30.0      # m: half length of the cast normal
EXT = 60.0       # m: axis continuation beyond grade / air chain ends for the landing analysis
MAIN_DECK = 24.0  # m: an AV structure wider than this at a station is the main deck / a junction, not the ramp
WALL_NEAR = 2.5   # m: a wall whose inner face is within this of the modelled edge flanks the modelled structure
WALL_SIDE = 10.0  # m: a wall within this of the axis counts as flanking the (unmodelled) ramp
AT_GRADE = 0.3
SOLID = 0.3       # m: underside within this of the game ground = solid


def intervals(p, n, geom, half=HALF):
    """Offsets along the normal through p where the line (±half) lies inside geom: sorted list of (lo, hi)."""
    from shapely.geometry import LineString
    if geom.is_empty:
        return []
    L = LineString([p - n * half, p + n * half])
    inter = L.intersection(geom)
    out = []
    for q in getattr(inter, "geoms", [inter]):
        if q.is_empty or q.geom_type != "LineString":
            continue
        offs = (np.asarray(q.coords) - p) @ n
        out.append((float(offs.min()), float(offs.max())))
    out.sort()
    merged = []
    for lo, hi in out:
        if merged and lo <= merged[-1][1] + 0.05:
            merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
        else:
            merged.append((lo, hi))
    return merged


def containing(ivs, off=0.0, tol=0.2):
    for lo, hi in ivs:
        if lo - tol <= off <= hi + tol:
            return (lo, hi)
    return None


THIN = 1.5   # m: a bridge polygon narrower than this crossing the normal is an edge structure (parapet / edge beam), not a deck


def voronoi_cap(p, n, own, others, limit, step=0.5):
    """Largest offset t along the normal n from p (up to `limit`) at which the point is still closer to the own axis than to
    any other site axis: the Voronoi boundary between sibling chains (no gore, no overlap). None when no other axis is nearer."""
    from shapely.geometry import Point
    t = step
    while t <= limit:
        q = Point(p[0] + n[0] * t, p[1] + n[1] * t)
        d_own = own.distance(q)
        if any(o.distance(q) < d_own for o in others):
            return max(0.0, t - step)
        t += step
    return None


def deck_slices(p, n, polys, half=HALF):
    """Intervals of the normal through p inside each bridge polygon separately (pieces of one polygon merged, polygons never),
    so that where two structures cross (Duttweilerbrücke over the rail flyover) each keeps its own width."""
    out = []
    for g in polys:
        out += intervals(p, n, g, half)
    return sorted(out)


def structure(ivs, reach=12.0):
    """The AV structure across the axis: the narrowest bridge polygon containing the axis, else the span between a thin bridge
    polygon on each side (ramp on fill between its edge structures, Geroldrampe below x = 176). (lo, hi, mode) or None."""
    cands = [(hi - lo, lo, hi) for lo, hi in ivs if lo - 0.2 <= 0 <= hi + 0.2 and hi - lo >= THIN]
    if cands:
        w, lo, hi = min(cands)
        return lo, hi, 1
    left = [(lo, hi) for lo, hi in ivs if lo > -0.5 and hi - lo < THIN and lo < reach]
    right = [(lo, hi) for lo, hi in ivs if hi < 0.5 and hi - lo < THIN and -hi < reach]
    if left and right:
        return min(right)[0], max(left)[1], 2
    return None


def nearest_side(ivs, wl, wr):
    """Nearest wall interval left of the left edge and right of the right edge: gaps (wall face - modelled edge), None if none."""
    left = [lo for lo, hi in ivs if hi > -0.5]    # anything on the left half plane
    right = [hi for lo, hi in ivs if lo < 0.5]
    gl = min((lo - wl for lo in left), default=None)
    gr = min((-hi - wr for hi in right), default=None)
    return gl, gr


TOL = 1.0   # m: class-17 samples further than this (+ slope allowance) from the running height belong to another deck


def lidar_strip(p, n, wl, wr, z_prev=None):
    """(z, flag) from the LiDAR central strip: flag 1 bridge class, 2 ground, 0 nothing. With `z_prev` (running height along
    the axis) bridge-class samples of a crossing deck (Duttweilerbrücke under the rail flyover, 6 m higher) are rejected;
    a bridge station whose samples are all rejected returns (NaN, 1) and is interpolated by the caller."""
    hw = max(0.5, 0.3 * min(wl, wr))
    offs = np.arange(-hw, hw + 1e-9, 0.5)
    X = p[0] + n[0] * offs; Y = p[1] + n[1] * offs
    b = lidar.bridge(X, Y)
    has_bridge = np.isfinite(b).sum() >= max(2, 0.5 * len(offs))
    if has_bridge and z_prev is not None and np.isfinite(z_prev):
        b = np.where(np.abs(b - z_prev) <= TOL + 0.3, b, np.nan)
        if np.isfinite(b).sum() < 2:
            return np.nan, 1
    if has_bridge:
        return ramp_lidar.robust_low(b), 1
    g = lidar.dtm(X, Y)
    if np.isfinite(g).sum() >= 2:
        return ramp_lidar.robust_low(g), 2
    return np.nan, 0


def lidar_track(xy, nrm, wl, wr, i0, z0):
    """Running-height LiDAR surface along stations: forward from i0 and backward from i0, seeded with z0 (a chain start at
    grade or at a junction, the same for every row set). Returns (z, flag) arrays, NaN where occluded by another deck."""
    n = len(xy); z = np.full(n, np.nan); flag = np.zeros(n, int)
    for rng in (range(i0, n), range(i0 - 1, -1, -1)):
        zp = z0
        for i in rng:
            z[i], flag[i] = lidar_strip(xy[i], nrm[i], wl[i], wr[i], zp)
            if np.isfinite(z[i]):
                zp = z[i]
    return z, flag


def other_axes(rows, cfg):
    """Axes of the road / tram deck rows that are not the site's own (junction partners such as the Hardbrücke)."""
    from shapely.geometry import LineString
    out = []
    for t, k, d in rows.decks():
        if d["kind"] in ("road", "tram") and not is_site_row(cfg, d):
            out.append(LineString(np.array(d["p"], float)[:, :2]))
    return out


def cut_by_taken(p, n, lo, hi, taken):
    """Cut the slice [lo, hi] at the near edges of other road decks crossing the normal; (lo, hi, on_other)."""
    on = False
    for tl, th in intervals(p, n, taken):
        if tl < -0.3 and th > 0.3:
            on = True
        elif th <= 0.3 and th > lo:
            lo = th
        elif tl >= -0.3 and tl < hi:
            hi = tl
    return lo, hi, on


def deck_cover(rows, box, margin=60.0, kinds=("road", "tram", "foot"), exclude=None):
    """Union of the footprints of the deck rows of `kinds` near the box (minus the site's own rows when `exclude` is given):
    what the cadastre structure is covered by, or what other decks occupy of a shared structure."""
    import shapely
    from join import footprint
    polys = []
    x0, y0, x1, y1 = box[0] - margin, box[1] - margin, box[2] + margin, box[3] + margin
    for t, k, d in rows.decks():
        if d["kind"] not in kinds or (exclude and exclude(t, k, d)):
            continue
        P = np.array(d["p"], float)
        if not ((P[:, 0] >= x0) & (P[:, 0] <= x1) & (P[:, 1] >= y0) & (P[:, 1] <= y1)).any():
            continue
        hw = d["w"] / 2
        polys.append(footprint(P[:, :2], np.array(d.get("wl") or [hw] * len(P), float), np.array(d.get("wr") or [hw] * len(P), float), d.get("pa"), d.get("pb")))
    return shapely.union_all(polys) if polys else shapely.Polygon()


def measure(chain, av, rows, step=2.0, box=None, ext=(), others=(), cover=None, taken=None, site_axes=()):
    """Station table for one chain: dict of equal-length arrays (NaN / -1 where not measured). `ext` = chain ends (0 / -1) that
    get an axis continuation of EXT m beyond the end (model columns NaN there) for the landing analysis."""
    st = chain.stations(step)
    xy, z, g, b, wl, wr, s, nrm = st["xy"], st["z"], st["g"], st["b"], st["wl"], st["wr"], st["s"], st["nrm"]
    ol, orr = st["ol"].astype(bool), st["or"].astype(bool)
    is_model = np.ones(len(s), bool)
    for end in ext:
        C = rows.extend(chain, end, EXT)
        C, t = ramp_lidar.resample(C, step)
        C = C[1:]; t = t[1:]
        m = len(C); nan = np.full(m, np.nan)
        if end == -1:
            N, _ = chain.normals(np.vstack([xy[-2:], C])); N = N[2:]
            xy = np.vstack([xy, C]); nrm = np.vstack([nrm, N]); s = np.concatenate([s, s[-1] + t])
            z = np.concatenate([z, nan]); g = np.concatenate([g, rows.ground(C[:, 0], C[:, 1])]); b = np.concatenate([b, nan])
            wl = np.concatenate([wl, np.full(m, wl[-1])]); wr = np.concatenate([wr, np.full(m, wr[-1])])
            ol = np.concatenate([ol, np.zeros(m, bool)]); orr = np.concatenate([orr, np.zeros(m, bool)])
            is_model = np.concatenate([is_model, np.zeros(m, bool)])
        else:
            N, _ = chain.normals(np.vstack([C[::-1], xy[:2]])); N = N[:m]
            xy = np.vstack([C[::-1], xy]); nrm = np.vstack([N, nrm]); s = np.concatenate([s[0] - t[::-1], s])
            z = np.concatenate([nan, z]); g = np.concatenate([rows.ground(C[::-1, 0], C[::-1, 1]), g]); b = np.concatenate([nan, b])
            wl = np.concatenate([np.full(m, wl[0]), wl]); wr = np.concatenate([np.full(m, wr[0]), wr])
            ol = np.concatenate([np.zeros(m, bool), ol]); orr = np.concatenate([np.zeros(m, bool), orr])
            is_model = np.concatenate([np.zeros(m, bool), is_model])
    n = len(s)
    decks, road_u, wall_u = av.geoms("deck"), av.union("carriageway"), av.union("wall")
    cols = {k: np.full(n, np.nan) for k in ("av_lo", "av_hi", "road_lo", "road_hi", "wall_gl", "wall_gr", "lz", "lg")}
    cols["lflag"] = np.zeros(n, int); cols["av_mode"] = np.zeros(n, int)   # 0 none, 1 inside a bridge polygon, 2 between edge structures
    for i in range(n):
        p = xy[i]; nv = nrm[i]
        c = structure(deck_slices(p, nv, decks))
        if c:
            cols["av_lo"][i], cols["av_hi"][i], cols["av_mode"][i] = c
        c = containing(intervals(p, nv, road_u))
        if c:
            cols["road_lo"][i], cols["road_hi"][i] = c
        gl, gr = nearest_side(intervals(p, nv, wall_u), wl[i], wr[i])
        cols["wall_gl"][i] = np.nan if gl is None else gl
        cols["wall_gr"][i] = np.nan if gr is None else gr
        cols["lg"][i] = float(lidar.dtm(np.array([p[0]]), np.array([p[1]]))[0])
    i0 = int(np.flatnonzero(is_model)[0])
    cols["lz"], cols["lflag"] = lidar_track(xy, nrm, wl, wr, i0, float(z[i0]))
    shared = np.zeros(n, bool)
    if len(others):
        from shapely.geometry import LineString
        for i in range(n):
            if np.isfinite(cols["av_lo"][i]):
                seg = LineString([xy[i] + nrm[i] * cols["av_lo"][i], xy[i] + nrm[i] * cols["av_hi"][i]])
                shared[i] = any(seg.intersects(a) for a in others)
    cols["shared"] = shared
    # the part of the slice available to this ramp: the piece around the axis not occupied by other road deck rows (the
    # Hardbrücke's carriageway beside a merge lane); footway rows do not count, the ramp rows carry the footways
    cols["av_lo_raw"], cols["av_hi_raw"] = cols["av_lo"].copy(), cols["av_hi"].copy()
    on_other = np.zeros(n, bool)             # the station itself lies inside another road deck (junction on the main deck)
    if taken is not None and not taken.is_empty:
        for i in range(n):
            lo, hi = cols["av_lo"][i], cols["av_hi"][i]
            if not np.isfinite(lo):
                continue
            for tl, th in intervals(xy[i], nrm[i], taken):
                if tl < -0.3 and th > 0.3:
                    on_other[i] = True
                elif th <= 0.3 and th > lo:
                    lo = th
                elif tl >= -0.3 and tl < hi:
                    hi = tl
            cols["av_lo"][i], cols["av_hi"][i] = lo, hi
    cols["on_other"] = on_other
    if len(site_axes):                       # other chains of the same site in the slice (fork, split carriageways): Voronoi boundary
        from shapely.geometry import LineString
        own = LineString(xy[is_model])
        for i in range(n):
            lo, hi = cols["av_lo"][i], cols["av_hi"][i]
            if not np.isfinite(lo):
                continue
            c = voronoi_cap(xy[i], nrm[i], own, site_axes, hi)
            if c is not None:
                hi = min(hi, c)
            c = voronoi_cap(xy[i], -nrm[i], own, site_axes, -lo)
            if c is not None:
                lo = max(lo, -c)
            cols["av_lo"][i], cols["av_hi"][i] = lo, hi
    unc = np.full(n, np.nan)                 # metres of the chain's share of the AV slice covered by no deck row at all
    uncov_iv = [[] for _ in range(n)]
    if cover is not None and not cover.is_empty:
        mi = np.flatnonzero(is_model); i_first, i_last = int(mi[0]), int(mi[-1])
        tan = np.column_stack([nrm[:, 1], -nrm[:, 0]])
        for i in range(n):
            lo, hi = cols["av_lo"][i], cols["av_hi"][i]      # the chain's own share of the slice (other road rows and siblings removed)
            if np.isfinite(lo):
                q = xy[i] + (tan[i] * 0.2 if i == i_first else -tan[i] * 0.2 if i == i_last else 0)   # end stations: sample just inside the row
                pieces = [(max(l, lo), min(h, hi)) for l, h in intervals(q, nrm[i], cover)]
                pieces = sorted((l, h) for l, h in pieces if h > l)
                cov = sum(h - l for l, h in pieces)
                unc[i] = max(0.0, (hi - lo) - cov)
                gaps = []; cur = lo                                 # the uncovered sub-intervals, for the overlay
                for l, h in pieces:
                    if l > cur + 0.2:
                        gaps.append((cur, l))
                    cur = max(cur, h)
                if hi > cur + 0.2:
                    gaps.append((cur, hi))
                uncov_iv[i] = gaps
    cols["uncov"] = unc; cols["uncov_iv"] = uncov_iv
    e = z - g
    kind = np.where(~is_model, -1, np.where(e < AT_GRADE, 0, np.where(b - g < SOLID, 1, 2)))   # -1 none, 0 grade, 1 solid, 2 deck
    inbox = np.ones(n, bool) if box is None else (xy[:, 0] >= box[0]) & (xy[:, 0] <= box[2]) & (xy[:, 1] >= box[1]) & (xy[:, 1] <= box[3])
    out = {"xy": xy, "nrm": nrm, "s": s, "z": z, "g": g, "b": b, "wl": wl, "wr": wr, "is_model": is_model, "kind": kind, "inbox": inbox}
    out.update(cols)
    out["av_w"] = out["av_hi"] - out["av_lo"]
    out["av_off"] = 0.5 * (out["av_hi"] + out["av_lo"])        # + : the AV structure's centre lies left of the modelled axis
    out["road_w"] = out["road_hi"] - out["road_lo"]
    out["ramp"] = np.isfinite(out["av_w"]) & (out["av_w"] <= MAIN_DECK) & (out["av_w"] >= 2.0) & ~out["on_other"]   # the slice available to this ramp; not on another deck
    out["excess_l"] = np.where(ol, np.nan, wl - out["av_hi"])   # + : modelled left edge beyond the AV edge; a flush side has no edge
    out["excess_r"] = np.where(orr, np.nan, wr + out["av_lo"])
    out["ol"], out["or"] = ol, orr
    out["wall_l"] = np.abs(out["wall_gl"]) <= WALL_NEAR
    out["wall_r"] = np.abs(out["wall_gr"]) <= WALL_NEAR
    out["wall_flank"] = (np.nan_to_num(out["wall_gl"] + wl, nan=99) <= WALL_SIDE) | (np.nan_to_num(out["wall_gr"] + wr, nan=99) <= WALL_SIDE)
    out["res"] = z - out["lz"]                                  # model height - LiDAR surface
    out["terr"] = g - out["lg"]                                 # game terrain - LiDAR ground
    return out


def pct(v, q):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    return float(np.percentile(v, q)) if len(v) else np.nan


def piers(chains, tables, av, rows, corridor=12.0):
    """Cadastre piers near the modelled axes vs the modelled structure, and the tile pier rows vs the cadastre piers."""
    from shapely.geometry import LineString, Point
    axes = [LineString(c.P[:, :2]) for c in chains]
    out = {"av_total": 0, "under_deck": 0, "under_solid": 0, "under_grade": 0, "outside": 0, "av_matched": 0, "tile_total": 0, "tile_matched": 0}
    avp = [g for g in av.geoms("pier") if min(ax.distance(g) for ax in axes) <= corridor]
    tile = rows.site_piers(chains, corridor)
    out["av_total"] = len(avp); out["tile_total"] = len(tile)
    for g in avp:
        c = g.centroid
        best = None
        for ch, T in zip(chains, tables):
            M = T["is_model"]
            d = np.hypot(T["xy"][M, 0] - c.x, T["xy"][M, 1] - c.y); j = int(d.argmin())
            if best is None or d[j] < best[0]:
                best = (d[j], T, np.flatnonzero(M)[j])
        _, T, j = best
        lat = float((np.array([c.x, c.y]) - T["xy"][j]) @ T["nrm"][j])
        inside = -T["wr"][j] - 0.5 <= lat <= T["wl"][j] + 0.5
        if not inside:
            out["outside"] += 1
        else:
            out[("under_grade", "under_solid", "under_deck")[T["kind"][j]]] += 1
        if any(g.distance(Point(q[0], q[1])) <= 2.0 for q in tile):
            out["av_matched"] += 1
    for q in tile:
        if any(g.distance(Point(q[0], q[1])) <= 2.0 for g in avp):
            out["tile_matched"] += 1
    return out


def uncovered_polys(T):
    """Polygons of the uncovered stretches (ramp stations, consecutive) for the overlay."""
    import shapely
    from shapely.geometry import Polygon
    out = []
    idx = np.flatnonzero(T["is_model"] & T["ramp"])
    for i, j in zip(idx[:-1], idx[1:]):
        if j != i + 1:
            continue
        for a0, a1 in T["uncov_iv"][i]:
            for b0, b1 in T["uncov_iv"][j]:
                if min(a1, b1) - max(a0, b0) > -1.0:
                    q = Polygon([T["xy"][i] + T["nrm"][i] * a0, T["xy"][i] + T["nrm"][i] * a1, T["xy"][j] + T["nrm"][j] * b1, T["xy"][j] + T["nrm"][j] * b0])
                    q = q if q.is_valid else q.buffer(0)
                    if not q.is_empty:
                        out.append(q)
    return shapely.union_all(out) if out else Polygon()


def av_outline(T):
    """Polygon of the AV structure cross-sections along the modelled axis (ramp stations, incl. edge-structure spans)."""
    import shapely
    from shapely.geometry import Polygon
    quads = []
    idx = np.flatnonzero(T["is_model"] & T["ramp"])
    for i, j in zip(idx[:-1], idx[1:]):
        if j != i + 1:
            continue
        a, b = T["xy"][i], T["xy"][j]; na, nb = T["nrm"][i], T["nrm"][j]
        q = Polygon([a + na * T["av_hi"][i], b + nb * T["av_hi"][j], b + nb * T["av_lo"][j], a + na * T["av_lo"][i]])
        q = q if q.is_valid else q.buffer(0)
        if not q.is_empty:
            quads.append(q)
    return shapely.union_all(quads) if quads else Polygon()


def areas(chains, tables, av, box, corridor=25.0):
    """Footprint agreement inside the view box. `corridor`: IoU / precision / recall of the modelled footprint vs all AV bridge
    polygons within `corridor` of the modelled axes (main deck included). `outline`: IoU vs the AV ramp cross-sections along
    the modelled axes (what the ramp rows should trace)."""
    import shapely
    from shapely.geometry import LineString, box as sbox
    B = sbox(*box)
    model = shapely.union_all([c.footprint() for c in chains]).intersection(B)
    cor = shapely.union_all([LineString(c.P[:, :2]).buffer(corridor) for c in chains])
    ref = av.union("deck").intersection(cor).intersection(B)
    inter = model.intersection(ref).area
    out = {"model_area": model.area, "av_area": ref.area, "iou": inter / (model.union(ref).area or 1), "precision": inter / (model.area or 1), "recall": inter / (ref.area or 1)}
    outline = shapely.union_all([av_outline(T) for T in tables]).intersection(B)
    i2 = model.intersection(outline).area
    # station-wise IoU: per ramp station the modelled cross-section [-wr, wl] against the available slice [lo, hi]; summed overlaps
    # over summed unions, so a cadastre structure shorter than the modelled rows (walled approaches) does not drag the value down
    inter = union = 0.0
    for T in tables:
        for i in np.flatnonzero(T["is_model"] & T["inbox"] & T["ramp"]):
            a0, a1 = -T["wr"][i], T["wl"][i]; b0, b1 = T["av_lo"][i], T["av_hi"][i]
            inter += max(0.0, min(a1, b1) - max(a0, b0)); union += max(a1, b1) - min(a0, b0)
    out.update({"outline_area": outline.area, "outline_iou": inter / (union or 1), "outline_recall": i2 / (outline.area or 1), "outline_area_iou": i2 / (model.union(outline).area or 1)})
    return out
