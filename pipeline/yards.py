"""Courtyards, front gardens and private vegetation (research/yards.md). Hooks in build_testarea.py (marked YARDS):

    yards.prepare(els, nodes, pg_rows)                     once, after details_osm.prepare (forked workers share it)
    yards.add_private_trees(C, fps, area)                  once, after the OSM private trees: nDSM trees missing in the register
    yards.tile_meta(tb, H, S, C, P, bld_polys)             -> {"yards": {...}} rows for web/src/world/yards.ts

Data: swissSURFACE3D - swissALTI3D nDSM (data/build/ndsm, 1 m), SWISSIMAGE (data/raw/ortho_wms, ExG greenness),
Stadt Zuerich Gruenflaechen (Strauchbepflanzung / Formhecke), AV Bodenbedeckung (via S), OSM hedges/fences (dedupe).
Rows (all local metres, z = ground):
    bushes  [x, y, z, radius, height, colour]          hedges [x, y, z, heading, length, width, height, colour]
    walls   [type, x, y, z, heading, length]           type 0 low wall, 1 metal fence, 2 low hedge
    props   [type, x, y, z, heading, a]                bikeshed, drying, sandbox, table, bench
    gravel  [x, y, z, heading, length]                 strip along building walls
"""
import json
import math
from pathlib import Path

import numpy as np
import shapely
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from config import ROOT
from styles import h32

E0, N0 = 2681400.0, 1248700.0
NDSM = ROOT / "data/build/ndsm"
ORTHO = ROOT / "data/raw/ortho_wms"
GRUEN = ROOT / "data/raw/stadtzh_all/geo_gruenflaechen__gruenflaechen.geojson"
_nd, _or = {}, {}
_D = {"shrub": None, "hedgeosm": None, "pg": []}


def _ndsm(e, n):
    if (e, n) not in _nd:
        f = NDSM / f"{e}-{n}.npy"
        _nd[(e, n)] = np.load(f).astype(np.float32) if f.exists() else None
    return _nd[(e, n)]


def _ortho(ix, iy):
    if (ix, iy) not in _or:
        f = ORTHO / f"r_{ix}_{iy}.jpg"
        _or[(ix, iy)] = np.asarray(Image.open(f).convert("RGB")).astype(np.int16) if f.exists() else None
    return _or[(ix, iy)]


def sample(xs, ys):
    """nDSM height (m, NaN where unknown) and ExG greenness at local points (arrays)."""
    E, N = xs + E0, ys + N0
    h = np.full(xs.shape, np.nan, np.float32)
    g = np.zeros(xs.shape, np.float32)
    te, tn = (E // 1000).astype(int), (N // 1000).astype(int)
    for a, b in set(zip(te.ravel().tolist(), tn.ravel().tolist())):
        t = _ndsm(a, b)
        if t is None:
            continue
        m = (te == a) & (tn == b)
        c = np.clip((E[m] - a * 1000).astype(int), 0, 999)
        r = np.clip(((b + 1) * 1000 - N[m]).astype(int), 0, 999)
        h[m] = t[r, c]
    ix, iy = np.floor(xs / 500).astype(int), np.floor(ys / 500).astype(int)
    for a, b in set(zip(ix.ravel().tolist(), iy.ravel().tolist())):
        t = _ortho(a, b)
        if t is None:
            continue
        m = (ix == a) & (iy == b)
        px = xs[m] - a * 500
        py = (b + 1) * 500 - ys[m]
        acc = np.zeros(px.shape, np.float32)
        for dx in (-.25, .25):  # 1 m cell = 2x2 ortho pixels
            for dy in (-.25, .25):
                c = np.clip(((px + dx) * 2).astype(int), 0, 999)
                r = np.clip(((py + dy) * 2).astype(int), 0, 999)
                p = t[r, c]
                acc += 2 * p[:, 1] - p[:, 0] - p[:, 2]
        g[m] = acc / 4
    return h, g


def _grid(x0, y0, nx, ny):
    xs = x0 + np.arange(nx) + .5
    ys = y0 + np.arange(ny) + .5
    X, Y = np.meshgrid(xs, ys)
    return X, Y


def _mask(geom, X, Y):
    if geom is None or geom.is_empty:
        return np.zeros(X.shape, bool)
    shapely.prepare(geom)
    return shapely.contains_xy(geom, X.ravel(), Y.ravel()).reshape(X.shape)


def prepare(els=None, nodes=None, pg_rows=()):
    """Stadt-Zuerich shrub / hedge care areas (local polygons) and OSM hedge/fence lines for de-duplication."""
    from pyproj import Transformer
    t = Transformer.from_crs(4326, 2056, always_xy=True)
    sh, hd = [], []
    if GRUEN.exists():
        for f in json.load(open(GRUEN))["features"]:
            pe = f["properties"].get("pflegeeinheit") or ""
            kind = "hedge" if "hecke" in pe.lower() else "shrub" if "strauch" in pe.lower() else None
            if not kind or not f["geometry"]:
                continue
            g = shapely.geometry.shape(f["geometry"])
            x, y = t.transform(*g.centroid.coords[0])
            if not (-3300 < x - E0 < 2500 and -2200 < y - N0 < 1600):
                continue
            g = shapely.transform(g, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])) - [E0, N0])
            (hd if kind == "hedge" else sh).append(g.buffer(0))
    _D["shrub"] = unary_union(sh) if sh else None
    _D["hedgepoly"] = unary_union(hd) if hd else None
    try:
        import details_osm
        ls = [LineString(xy) for k, xy, _ in details_osm._D["lines"]] if details_osm._D else []
        _D["hedgeosm"] = unary_union(ls).buffer(1.3) if ls else None
    except Exception:
        _D["hedgeosm"] = None
    _D["pg"] = [(r[0], r[1]) for r in pg_rows]
    al = []
    for e in els or []:
        if e["type"] == "way" and (e.get("tags") or {}).get("landuse") == "allotments":
            xy = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(xy) >= 4:
                g = Polygon(xy).buffer(0)
                if not g.is_empty and g.area > 300:
                    al.append(g)
    _D["allot"] = al
    print(f"yards: {len(sh)} shrub + {len(hd)} hedge care areas", flush=True)


# ----------------------------------------------------------------------------------------------- private trees
def _tree_zones():
    import glob, json, os
    from shapely.geometry import Polygon
    out = []
    for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "overrides", "tree_excl_*.json")):
        out += [Polygon(r) for r in json.load(open(f)).get("rings", [])]
    return out


def add_private_trees(C, fps, area, step=400):
    """Append nDSM canopy maxima that the tree register / OSM lack to C['trees'] as (x, y, '', crown, 'ndsm')."""
    ex = np.array([(t[0], t[1], t[3] or 6) for t in C.get("trees", [])], float).reshape(-1, 3)
    bld = unary_union([f for f in fps]).buffer(1.2)
    shapely.prepare(bld)
    x0, y0, x1, y1 = [int(v) for v in area]
    new = []
    for cx in range(x0 // step * step, x1, step):
        for cy in range(y0 // step * step, y1, step):
            X, Y = _grid(cx - 10, cy - 10, step + 20, step + 20)
            h, g = sample(X, Y)
            can = (h > 3.5) & (g > 0) & ~_mask(bld, X, Y)
            can = ndimage.binary_opening(can, iterations=1)
            if not can.any():
                continue
            hs = ndimage.gaussian_filter(np.nan_to_num(h), 1.2)
            pk = (hs == ndimage.maximum_filter(hs, size=7)) & can
            lab, n = ndimage.label(can)
            areas = ndimage.sum(can, lab, index=np.arange(1, n + 1))
            npk = np.bincount(lab[pk], minlength=n + 1)
            for r, c in zip(*np.nonzero(pk)):
                l = lab[r, c]
                cd = float(np.clip(2 * math.sqrt(areas[l - 1] / max(npk[l], 1) / math.pi) * 1.1, 4, 14))
                x, y = X[r, c], Y[r, c]
                if not (cx <= x < cx + step and cy <= y < cy + step):
                    continue
                new.append((x, y, cd))
    pts = np.array(new, float).reshape(-1, 3)
    kept = 0
    if len(ex):
        tr = cKDTree(ex[:, :2])
        d, j = tr.query(pts[:, :2]) if len(pts) else (np.zeros(0), np.zeros(0, int))
        ok = d > np.maximum(2.5, 0.45 * ex[j, 2]) if len(pts) else np.zeros(0, bool)
        pts = pts[ok]
    zones = _tree_zones()
    if zones:   # landmark sites whose old canopy/roof reading must not become trees (e.g. Stadion Letzigrund roof ring)
        C["trees"] = [t for t in C["trees"] if not any(z.contains(Point(t[0], t[1])) for z in zones)]
        pts = np.array([q for q in pts if not any(z.contains(Point(q[0], q[1])) for z in zones)], float).reshape(-1, 3)
    for x, y, cd in pts:
        C["trees"].append((float(x), float(y), "", float(cd), "ndsm"))
        kept += 1
    print(f"yards: {kept} private nDSM trees added (of {len(new)} canopy maxima)", flush=True)
    drop_unsupported_trees(C)
    return kept


def drop_unsupported_trees(C, radius=3, min_h=2.5):
    """LiDAR check (audit_lidar d): private trees (OSM natural=tree, nDSM maxima) without any canopy > 2.5 m within 3 m are
    roofs / platforms / vehicles / felled trees from the older DSM. Register trees (Baumkataster) stay: young plantings after the
    2021/22 flight have no crown yet. A tree class not in veg (3-5) still counts when a non-building return stands > min_h above ground."""
    try:
        import lidar
    except Exception:
        return 0
    if not (lidar.GRID.exists() and any(lidar.GRID.glob("g_*.npz"))):
        return 0
    idx = [i for i, t in enumerate(C.get("trees", [])) if t[4] in ("osm", "ndsm")]
    if not idx:
        return 0
    off = np.array([(dx, dy) for dx in range(-radius, radius + 1) for dy in range(-radius, radius + 1) if dx * dx + dy * dy <= radius * radius], float)
    drop = set()
    for a in range(0, len(idx), 500):
        part = idx[a:a + 500]
        P = np.array([C["trees"][i][:2] for i in part], float)
        X = (P[:, None, 0] + off[None, :, 0]).ravel(); Y = (P[:, None, 1] + off[None, :, 1]).ravel()
        if np.isnan(lidar.dtm(X, Y)).all():   # no LiDAR here (outside the loaded tiles): keep
            continue
        g = lidar.dtm_filled(X, Y, 4.0)
        v = lidar.veg(X, Y) - g
        t = lidar.top(X, Y) - g
        nb = (np.isnan(lidar.bld(X, Y)) & np.isnan(lidar.bridge(X, Y))).reshape(len(part), -1).all(axis=1)   # nothing built within the disc
        sup = ((v > min_h) & (v < 80)).reshape(len(part), -1).any(axis=1) | (nb & (((t > min_h) & (t < 80)).reshape(len(part), -1).sum(axis=1) >= 4))
        nodata = np.isnan(g).reshape(len(part), -1).all(axis=1)
        drop |= {part[k] for k in range(len(part)) if not sup[k] and not nodata[k]}
    if drop:
        C["trees"] = [t for i, t in enumerate(C["trees"]) if i not in drop]
    print(f"yards: {len(drop)} private trees dropped (no LiDAR canopy within {radius} m)", flush=True)
    return len(drop)


# ----------------------------------------------------------------------------------------------- tile rows
def _rnd(*a):
    return (h32("y" + ",".join(str(v) for v in a)) % 10000) / 10000.0


def _pca(pts):
    c = pts.mean(0)
    u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
    return c, vt[0], s


def _shrubs(tb, H, S, C, bld, z, out):
    x0, y0, x1, y1 = [int(v) for v in tb.bounds]
    X, Y = _grid(x0, y0, x1 - x0, y1 - y0)
    h, g = sample(X, Y)
    green = (g > 2) & (h >= 0.8) & (h < 3.2)
    care = _mask(_D["shrub"], X, Y) if _D["shrub"] is not None else np.zeros(X.shape, bool)
    hed = _mask(_D.get("hedgepoly"), X, Y)
    h = np.where(np.isfinite(h), h, 0)
    h = np.where((care | hed) & (h < 0.8), np.where(hed, 1.2, 0.9), h)
    cand = green | care | hed
    cand &= ~_mask(bld, X, Y) & ~_mask(S["roads"].union(S["plaza"]), X, Y) & ~_mask(S["parks"].buffer(-2.0), X, Y)
    if _D["hedgeosm"] is not None:
        cand &= ~_mask(_D["hedgeosm"], X, Y)
    trees = [(t[0], t[1], max(t[3] or 6, 3) * .5) for t in C.get("trees", []) if tb.buffer(10).contains(Point(t[0], t[1]))]
    if trees:  # inside tree crowns: the canopy is the tree, not a shrub
        T = np.array(trees)
        d, j = cKDTree(T[:, :2]).query(np.c_[X.ravel(), Y.ravel()])
        cand &= ~(d < T[j, 2] * .8).reshape(X.shape)
    cand = ndimage.binary_opening(cand, iterations=1)
    lab, n = ndimage.label(cand)
    bushes, hedges = [], []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        m = lab[sl] == i
        a = int(m.sum())
        if a < 4:
            continue
        rr, cc = np.nonzero(m)
        px, py = X[sl][rr, cc], Y[sl][rr, cc]
        hh = float(np.percentile(h[sl][rr, cc], 85))
        col = h32(f"c{px[0]:.0f}{py[0]:.0f}") % 8
        pts = np.c_[px, py]
        c, ax, s = _pca(pts)
        proj = (pts - c) @ ax
        length = float(proj.max() - proj.min() + 1)
        width = a / max(length, 1)
        if length >= 5 and width <= 3.0 and length / width >= 2.5:  # hedge: boxes along the principal axis
            heading = math.atan2(ax[1], ax[0])
            k = max(1, int(round(length / 6)))
            seg = length / k
            for q in range(k):
                t = proj.min() + .5 + seg * (q + .5)
                p = c + ax * t
                hedges.append([round(p[0], 2), round(p[1], 2), z(p[0], p[1]), round(heading, 3), round(seg + .1, 2),
                               round(float(np.clip(width * .9, .5, 2.6)), 2), round(float(np.clip(hh * .9, .6, 3.0)), 2), col])
        else:  # shrub beds: blobs of bushes on a jittered 1.8 m grid
            cells = {}
            for x, y in pts:
                cells.setdefault((int(x // 1.8), int(y // 1.8)), []).append((x, y))
            for (gx, gy), v in cells.items():
                if len(v) < 2:
                    continue
                v = np.array(v).mean(0)
                r = float(np.clip(.7 + .22 * hh + .3 * _rnd(gx, gy), .7, 1.7))
                bushes.append([round(v[0], 2), round(v[1], 2), z(v[0], v[1]), round(r, 2), round(float(np.clip(hh * (.75 + .3 * _rnd(gy, gx)), .6, 2.6)), 2),
                               (col + gx) % 8])
    out["bushes"] = bushes[:900]
    out["hedges"] = hedges[:300]


def _courtyards(tb, S, bld):
    walk = tb.difference(S["roads"]).difference(S["plaza"]).difference(S["parks"])
    side = walk.intersection(S["roads"].buffer(6.0).union(S["plaza"].buffer(3.0)))
    if S.get("av_green") is not None:
        side = side.difference(S["av_green"].intersection(tb))
    yard = walk.difference(side).difference(bld)
    return side, yard


def _front_walls(tb, H, S, side, yard, bld, z, out):
    """Mäuerchen / Zaun / low hedge where a front garden meets the pavement (not where OSM already has a barrier)."""
    walls = []
    near = bld.buffer(14)
    if side.boundary is None:  # GeometryCollection after the differences: keep only the polygonal parts
        side = unary_union([g for g in getattr(side, "geoms", []) if g.geom_type in ("Polygon", "MultiPolygon")]) or Polygon()
    edge = side.boundary.intersection(yard.buffer(.4)).intersection(near).intersection(tb)
    if _D["hedgeosm"] is not None:
        edge = edge.difference(_D["hedgeosm"])
    for ln in getattr(edge, "geoms", [edge]):
        if ln.geom_type != "LineString" or ln.length < 4:
            continue
        # skip pieces where a building touches the pavement (no garden) or the strip is open public lawn
        L = ln.length
        k = max(1, int(L // 8))
        for q in range(k):
            a, b = L * q / k, L * (q + 1) / k
            r = _rnd(round(ln.coords[0][0]), round(ln.coords[0][1]), q)
            if r < .38 or b - a < 3:
                continue
            a += .8 if q == 0 else 0
            b -= .8 if q == k - 1 else 0
            p0, p1 = ln.interpolate(a), ln.interpolate(b)
            mx, my = (p0.x + p1.x) / 2, (p0.y + p1.y) / 2
            if bld.distance(Point(mx, my)) > 12:
                continue
            ty = 0 if r < .6 else 1 if r < .8 else 2
            walls.append([ty, round(mx, 2), round(my, 2), z(mx, my), round(math.atan2(p1.y - p0.y, p1.x - p0.x), 3), round(p0.distance(p1) - .1, 2)])
    out["walls"] = walls[:500]


def _props(tb, H, S, C, P, yard, bld, bpolys, z, out):
    props, gravel = [], []
    green = S["av_green"].intersection(tb) if S.get("av_green") is not None else Polygon()
    court = yard.difference(S["roads"].buffer(7))
    pg = [Point(p) for p in _D["pg"] if tb.buffer(40).contains(Point(p))]
    bikes = [(r[0], r[1]) for r in (P.get("bikes") or []) if len(r) > 1]
    placed = []

    def free(x, y, r):
        return all(math.hypot(x - a, y - b) > r for a, b in placed)

    for poly in getattr(court, "geoms", [court]):
        if poly.is_empty or poly.area < 120:
            continue
        inner = poly.buffer(-1.8)
        if inner.is_empty:
            continue
        gp = inner.intersection(green)
        pp = inner.difference(green)
        x0, y0, x1, y1 = inner.bounds
        pts = [(x, y) for x in np.arange(x0, x1, 2.5) for y in np.arange(y0, y1, 2.5)]
        pts = [p for p in pts if inner.contains(Point(p))]
        for x, y in pts:
            r = _rnd(round(x), round(y))
            p = Point(x, y)
            onlawn = gp.contains(p)
            dwall = bld.distance(p)
            if onlawn and poly.area > 220 and r < .012 and free(x, y, 14):
                props.append(["drying", round(x, 2), round(y, 2), z(x, y), round(r * 628, 3), 0]); placed.append((x, y))
            elif onlawn and poly.area > 380 and .5 < r < .515 and free(x, y, 25) and all(q.distance(p) > 35 for q in pg):
                props.append(["sandbox", round(x, 2), round(y, 2), z(x, y), round(r * 12, 3), 0]); placed.append((x, y))
            elif not onlawn and 1.8 < dwall < 3.8 and r < .02 and free(x, y, 16) and all(math.hypot(x - a, y - b) > 8 for a, b in bikes):
                # heading along the nearest wall
                near = min(bpolys, key=lambda f: f.distance(p)) if bpolys else None
                hd = 0.0
                if near is not None:
                    d = near.exterior.project(p)
                    q0, q1 = near.exterior.interpolate(d), near.exterior.interpolate(d + 1)
                    hd = math.atan2(q1.y - q0.y, q1.x - q0.x)
                props.append(["bikeshed", round(x, 2), round(y, 2), z(x, y), round(hd, 3), int(r * 1000) % 3]); placed.append((x, y))
            elif (not onlawn) and dwall < 6 and .6 < r < .612 and free(x, y, 10):
                props.append(["table", round(x, 2), round(y, 2), z(x, y), round(r * 100, 3), int(r * 1e4) % 2]); placed.append((x, y))
        # gravel strip along walls on paved ground
    for f in bpolys:
        if not f.intersects(tb):
            continue
        ring = f.exterior
        L = ring.length
        for q in range(int(L // 6)):
            m = ring.interpolate(6 * q + 3)
            if not tb.contains(m) or _rnd(round(m.x), round(m.y)) > .3:
                continue
            q0, q1 = ring.interpolate(6 * q + .5), ring.interpolate(6 * q + 5.5)
            hd = math.atan2(q1.y - q0.y, q1.x - q0.x)
            ox, oy = -math.sin(hd) * (.55 if not f.exterior.is_ccw else -.55), math.cos(hd) * (.55 if not f.exterior.is_ccw else -.55)
            gx, gy = m.x + ox, m.y + oy
            if yard.contains(Point(gx, gy)) and not green.contains(Point(gx, gy)):
                gravel.append([round(gx, 2), round(gy, 2), z(gx, gy), round(hd, 3), 5.0])
    out["props"] = props[:400]
    out["gravel"] = gravel[:300]


def _allotments(tb, z, out):
    """Familiengarten (OSM landuse=allotments): a timber shed per ~180 m2 plus low vegetable-bed rows."""
    for g in _D.get("allot", []):
        if not g.intersects(tb):
            continue
        inner = g.buffer(-1.5)
        if inner.is_empty:
            continue
        x0, y0, x1, y1 = inner.bounds
        hd0 = 0.0
        for x in np.arange(x0, x1, 12.0):
            for y in np.arange(y0, y1, 15.0):
                r = _rnd(round(x), round(y), "al")
                px, py = x + 12 * r * .5, y + 15 * (1 - r) * .5
                if not (inner.contains(Point(px, py)) and tb.contains(Point(px, py))):
                    continue
                out.setdefault("props", []).append(["shed", round(px, 2), round(py, 2), z(px, py), hd0, int(r * 1000) % 3])
                for k in range(3):  # beds beside the shed
                    bx, by = px + 3.2 + k * 1.9, py
                    if inner.contains(Point(bx, by)) and tb.contains(Point(bx, by)):
                        out.setdefault("hedges", []).append([round(bx, 2), round(by, 2), z(bx, by), 1.571, 6.0, 1.2, .45, 7 if k % 2 else 0])


_EXCL = None


def _apply_excl(out):
    """overrides/yards_excl_*.json {"rings": [[[x,y],...]]}: drop generic yard bushes/hedges/props whose anchor lies inside a ring (hand-built landmark areas, e.g. Quartiergarten Hard)."""
    global _EXCL
    if _EXCL is None:
        import glob, json, os
        from shapely.geometry import Polygon
        _EXCL = []
        for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "overrides", "yards_excl_*.json")):
            _EXCL += [Polygon(r) for r in json.load(open(f)).get("rings", [])]
        for g in _EXCL: shapely.prepare(g)
    if not _EXCL:
        return
    for key in ("bushes", "hedges", "props"):
        rows = out.get(key)
        if not rows:
            continue
        i = 1 if key == "props" else 0
        out[key] = [r for r in rows if not any(g.contains(Point(r[i], r[i + 1])) for g in _EXCL)]


def tile_meta(tb, H, S, C, P, bld_polys):
    if _D["shrub"] is None and _D["hedgeosm"] is None and not _D.get("ready"):
        pass
    z = lambda x, y: round(float(H.at(x, y)), 2)
    bpolys = [f for f in bld_polys if f.geom_type == "Polygon"]
    bld = unary_union(bld_polys).buffer(.5) if bld_polys else Polygon()
    shapely.prepare(bld)
    out = {}
    try:
        _shrubs(tb, H, S, C, bld, z, out)
        side, yard = _courtyards(tb, S, bld)
        _front_walls(tb, H, S, side, yard, bld, z, out)
        _props(tb, H, S, C, P, yard, bld, bpolys, z, out)
        _allotments(tb, z, out)
    except Exception as e:  # never break a tile build over vegetation
        import traceback
        traceback.print_exc()
        print("yards: tile failed", e, flush=True)
    _apply_excl(out)
    return {"yards": out}


# ----------------------------------------------------------------------------------------------- trees vs. bridge decks
def drop_deck_trees(C, BR, H, margin_nd=2.0):
    """No tree on or through an elevated deck (Hardbruecke, Duttweilerbruecke, rail viaducts, footbridges ...). The nDSM reads decks,
    vehicles and catenary as canopy, so nDSM maxima near a deck are dropped; register/OSM trees stay only where the crown clears the
    deck underside (tree top < underside - 0.2 m). Returns the number removed. pipeline/audit_trees_deck.py"""
    import trees_dims
    segs, info = [], []
    for b in BR or []:
        p = b["p"]
        for i in range(len(p) - 1):
            if min(p[i][2] - b["g"][i], p[i + 1][2] - b["g"][i + 1]) < 0.3:
                continue
            segs.append(LineString([q[:2] for q in p[i:i + 2]]).buffer(b["w"] / 2 + 0.3, cap_style="flat"))
            info.append(min(b["b"][i], b["b"][i + 1]))
    if not segs:
        return 0
    from shapely.strtree import STRtree
    st = STRtree(segs)
    keep, n = [], 0
    for t in C.get("trees", []):
        x, y = t[0], t[1]
        pt = Point(x, y)
        near = [j for j in st.query(pt.buffer(4.0)) if segs[j].distance(pt) <= 4.0]
        if not near:
            keep.append(t)
            continue
        z = float(H.at(x, y))
        row = trees_dims.tree_row(C, x, y, z, t[2], t[3], t[4], 0.0, False)   # same crown / height as the tile row (audit_trees_deck.py)
        rad = max(row[4] * .25, margin_nd if t[4] == "ndsm" else 0)
        hit = [j for j in near if segs[j].distance(pt) <= rad]
        if not hit:
            keep.append(t)
            continue
        under = min(info[j] for j in hit)
        if t[4] == "ndsm" or z > under - 0.5 or z + row[5] > under - 0.2:
            n += 1
        else:
            keep.append(t)
    C["trees"] = keep
    print(f"yards: {n} trees removed on/through bridge decks", flush=True)
    return n
