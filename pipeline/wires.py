"""Overhead contact wires v2 (Fahrleitungen): tram + trolleybus, masts and wall anchors, continuous across tiles.

build(...)  -> Net   once per build, global (all lines of the play area)
tile(net, tb) -> (wires, poles)   cut for one 200 m tile; endpoints exactly on the tile edge, so neighbours join

Rules (research/wires/v2.md):
- one contact wire per track (tram 5.7 m) / two parallel wires 0.6 m apart per trolleybus lane (5.6 m)
- wires end only at a mast (tensioning stub), at a junction (touching another wire), or at the play-area edge
- span wires only between two anchors: masts (LiDAR class 15 / OSM lights / new kerb mast) or a building facade (6.5 m)
- no anchor on one side -> kerb mast outside the carriageway; reuse an existing pole within 1.5 m
Polylines are [[x, y, z], ...] in game metres. Poles are [x, y, z_ground] (drawn 7 m high by web/src/world/props.ts).
"""
from __future__ import annotations

import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point, box
from shapely.strtree import STRtree

H_TRAM, H_TROLLEY = 5.7, 5.6
A_WALL, A_MAST = 6.5, 6.4  # span anchor height above ground
STEP, SPACING, REACH = 10.0, 32.0, 13.0
SIDE_OFF = 0.0  # the game buses drive on the route line itself (transit.ts): wires hang right over it
MIN_WALL_H = 7.5


class Net:
    def __init__(self):
        self.wires = []  # dict(g=group, kind, pts)
        self.poles = []  # [x, y, zg] to draw
        self.anchors = []  # (x, y, z, 'mast'|'wall')
        self.ends = []  # (x, y, kind) kind: end|junction|edge
        self.spans = 0
        self.fail = 0
        self.n_kerb = 0
        self.n_lidar = 0


def footprints(blds):
    """[(polygon, height)] of swissBUILDINGS3D dicts (same rule as build_testarea.footprint)."""
    out = []
    for b in blds:
        rings = [shapely.geometry.Polygon(p[:, :2]).buffer(0) for k, p in b["polys"] if k == 0 and len(p) >= 4]
        rings = [r for r in rings if not r.is_empty]
        if rings:
            out.append((shapely.union_all(rings).simplify(0.3), float(b.get("h") or 0)))
    return out


class _Ctx:
    def __init__(self, net, cands, fps, roads, zf):
        self.net, self.zf, self.roads = net, zf, roads
        self.c = cands  # Nx4 x, y, height, drawn
        self.kd = cKDTree(cands[:, :2]) if len(cands) else None
        self.used = set()
        self.polys = [f for f, _ in fps]
        self.hts = [h for _, h in fps]
        self.tree = STRtree(self.polys)
        self.core = STRtree([f.buffer(-0.3) if f.buffer(-0.3).area > 1 else f for f in self.polys])
        self.newp = np.zeros((0, 2))
        self.spans = []  # (a, b) xy arrays

    def clear(self, p, a):
        seg = LineString([p, a])
        return len(self.core.query(seg, predicate="intersects")) == 0

    def anchor_z(self, kind, x, y, h=7.0):
        return float(self.zf(x, y)) + (A_WALL if kind == "wall" else min(A_MAST, h - 0.3))

    def options(self, p, d, t, free=False):
        """Anchor options on the side d (unit) from p; t = axis along which the mast window is measured. Best first."""
        out = []
        if self.kd is not None:
            for i in self.kd.query_ball_point(p, REACH + 5):
                v = self.c[i, :2] - p
                al, lat = float(v @ t), float(v @ d)
                if abs(al) <= 5 and 1.2 <= lat <= REACH and self.c[i, 2] >= 6.3:
                    out.append((lat + 0.1 * abs(al), "mast", i, self.c[i, :2]))
        for j, q in enumerate(self.newp):
            v = q - p
            al, lat = float(v @ t), float(v @ d)
            if abs(al) <= 5 and 1.2 <= lat <= REACH:
                out.append((lat + 0.1 * abs(al), "new", j, q))
        out.sort(key=lambda o: o[0])
        res = list(out)
        ray = LineString([p, p + d * REACH])
        hit = None
        for k in self.tree.query(ray, predicate="intersects"):
            if self.polys[k].contains(Point(p)):
                continue
            dist = ray.intersection(self.polys[k]).distance(Point(p))
            if hit is None or dist < hit[0]:
                hit = (dist, k)
        if hit and hit[0] >= 0.8 and self.hts[hit[1]] >= MIN_WALL_H:
            res.append((hit[0], "wall", hit[1], p + d * hit[0]))
        for dist in np.arange(1.0, REACH, 0.5):  # kerb: first point outside the carriageway, +1.2 m
            q = p + d * dist
            if self.roads is None or not self.roads.contains(Point(q)):
                q = p + d * (dist + 1.2)
                if len(self.tree.query(Point(q), predicate="within")) == 0 and dist + 1.2 <= REACH:
                    res.append((dist + 1.2, "kerb", -1, q))
                break
        if free:  # last resort (track end in a plaza/yard): a pole right beside the track end
            for dist in (2.2, 3.2, 4.5):
                q = p + d * dist
                if len(self.tree.query(Point(q), predicate="within")) == 0:
                    res.append((dist, "kerb", -1, q))
        return res

    def pick(self, p, d, t, free=False):
        for _, kind, i, q in self.options(p, d, t, free):
            if self.clear(p, q):
                return kind, i, q
        return None

    def commit(self, a):
        """Register the anchor, return (x, y, z)."""
        kind, i, q = a
        x, y = float(q[0]), float(q[1])
        if kind == "mast":
            self.used.add(i)
            z = self.anchor_z("mast", x, y, self.c[i, 2])
            self.net.anchors.append((x, y, z, "mast"))
        elif kind == "new":
            z = self.anchor_z("mast", x, y)
            self.net.anchors.append((x, y, z, "mast"))
        elif kind == "kerb":
            self.newp = np.vstack([self.newp, [x, y]])
            self.net.n_kerb += 1
            self.net.poles.append([round(x, 2), round(y, 2), round(float(self.zf(x, y)), 2)])
            z = self.anchor_z("mast", x, y)
            self.net.anchors.append((x, y, z, "mast"))
        else:
            z = self.anchor_z("wall", x, y)
            self.net.anchors.append((x, y, z, "wall"))
        return x, y, z


def _unit(v):
    return v / (np.linalg.norm(v) + 1e-9)


def _tangent(L, s):
    a, b = L.interpolate(max(0, s - 0.6)), L.interpolate(min(L.length, s + 0.6))
    return _unit(np.array([b.x - a.x, b.y - a.y]))


def _run(ctx, L, dz, g, kind, ends, pair=False):
    """Contact wire(s) along L plus its stations (spans) and end stubs."""
    net, zf = ctx.net, ctx.zf
    Ls = L.length
    st = []  # station s values
    cur = 0.0
    while cur + 14 < Ls:
        tgt = min(cur + SPACING, Ls - 8)
        s = tgt
        if ctx.kd is not None:  # prefer a real mast: its projection nearest the target spacing
            p0 = L.interpolate(tgt)
            best = None
            for i in ctx.kd.query_ball_point([p0.x, p0.y], 24):
                if ctx.c[i, 2] < 6.3:
                    continue
                pt = Point(ctx.c[i, :2])
                if L.distance(pt) > REACH or L.distance(pt) < 1.2:
                    continue
                sc = L.project(pt)
                if cur + 18 <= sc <= min(cur + 42, Ls - 6) and (best is None or abs(sc - tgt) < abs(best - tgt)):
                    best = sc
            if best is not None:
                s = best
        cur = s
        st.append(s)
    spans = {}
    for s in st:
        p = np.array(L.interpolate(s).coords[0])
        t = _tangent(L, s)
        n = np.array([-t[1], t[0]])
        if any(sp[0].distance(Point(p)) < 1.0 for sp in ctx.spans_ls):
            spans[s] = None  # an existing span (parallel track / opposite lane) already crosses here
            continue
        la, ra = ctx.pick(p, n, t), ctx.pick(p, -n, t)
        if la is None or ra is None:
            net.fail += 1
            spans[s] = None
            continue
        A, B = ctx.commit(la), ctx.commit(ra)
        zc = float(zf(*p)) - 0.12 + dz
        net.wires.append({"g": g, "kind": "span", "pts": [[A[0], A[1], A[2]], [p[0], p[1], zc + 0.3], [B[0], B[1], B[2]]]})
        ctx.spans_ls.append((LineString([A[:2], B[:2]]),))
        net.spans += 1
        spans[s] = zc + 0.3
    ss = sorted(set(list(np.arange(0, Ls, STEP)) + [Ls] + st))
    keep = [s for s in ss if s in st or s in (0.0, Ls) or all(abs(s - q) > 1.5 for q in st)]
    # end stubs
    stub = {}
    for end, s in ((0, 0.0), (1, Ls)):
        if ends[end] != "end":
            continue
        p = np.array(L.interpolate(s).coords[0])
        if len(ctx.tree.query(Point(p).buffer(0.8), predicate="intersects")):  # track ends at a facade: wall rosette
            stub[end] = ctx.commit(("wall", -1, p))
            continue
        t = _tangent(L, s) * (-1 if end == 0 else 1)
        n = np.array([-t[1], t[0]])
        for d in (n, -n, t):
            a = ctx.pick(p, d, n if d is t else t)
            if a is not None:
                stub[end] = ctx.commit(a)
                break
        else:
            for d in (n, -n, t):
                a = ctx.pick(p, d, n if d is t else t, free=True)
                if a is not None:
                    stub[end] = ctx.commit(a)
                    break
            else:
                net.fail += 1
    offs = (-0.3, 0.3) if pair else (0.0,)
    for off in offs:
        pts = []
        for s in keep:
            q = L.interpolate(s)
            t = _tangent(L, s)
            x, y = q.x - t[1] * off, q.y + t[0] * off
            pts.append([x, y, float(zf(x, y)) - 0.12 + dz])
        if 0 in stub:
            pts.insert(0, list(stub[0]))
        if 1 in stub:
            pts.append(list(stub[1]))
        net.wires.append({"g": g, "kind": kind, "pts": [[round(v, 2) for v in p] for p in pts]})


def _classify(parts, edge):
    """Per merged part: ('end'|'junction'|'edge') for start and end."""
    tree = STRtree(parts)
    res = []
    for i, L in enumerate(parts):
        r = []
        for e in (L.coords[0], L.coords[-1]):
            pt = Point(e)
            near = [j for j in tree.query(pt.buffer(1.0)) if j != i and parts[j].distance(pt) <= 1.0]
            if near:
                r.append("junction")
            elif edge.distance(pt) < 0.2:
                r.append("edge")
            else:
                r.append("end")
        res.append(r)
    return res


def _merge(lines, area):
    cl = []
    for ln in lines:
        part = ln.intersection(area)
        cl += [g for g in shapely.get_parts(part) if g.geom_type == "LineString"]
    if not cl:
        return []
    m = shapely.line_merge(shapely.union_all(cl))
    return [g for g in shapely.get_parts(m) if g.geom_type == "LineString" and g.length >= 2.0]


def _lane(pts, off):
    """Offset a route polyline by off metres to the right of travel (resampled to 6 m)."""
    L = LineString(pts)
    ss = np.append(np.arange(0, L.length, 6.0), L.length)
    out = []
    for s in ss:
        q = L.interpolate(s)
        t = _tangent(L, s)
        out.append((q.x + t[1] * off, q.y - t[0] * off))
    return LineString(out)


def build(tram_lines, routes, masts, lights, fps, roads, zf, tiles, tile=200.0):
    """tram_lines: [LineString]; routes: [(ref, dir, pts)] trolleybus; masts: LiDAR Nx5 [x,y,ztop,zbase,n];
    lights: off-road OSM light posts Nx2; fps: [(Polygon, h)]; roads: carriageway polygon; zf(x,y) ground height."""
    net = Net()
    area = shapely.union_all([box(ix * tile, iy * tile, (ix + 1) * tile, (iy + 1) * tile) for ix, iy in tiles])
    edge = area.boundary
    lights = np.asarray(lights, float).reshape(-1, 2)
    rows = [[x, y, 7.0, 1.0] for x, y in lights]
    if len(masts):
        mm = np.asarray(masts, float)
        kd = cKDTree(lights) if len(lights) else None
        for x, y, zt, zb, _ in mm:
            if zt - zb < 6.3 or not area.buffer(15).contains(Point(x, y)):
                continue
            if kd is not None and kd.query([x, y])[0] < 1.5:
                continue
            rows.append([x, y, zt - zb, 0.0])
    cands = np.array(rows, float).reshape(-1, 4)
    ctx = _Ctx(net, cands, fps, roads, zf)
    ctx.spans_ls = []
    g = 0
    tall = shapely.union_all([f for f, h in fps if h >= MIN_WALL_H])
    parts = _merge([ln.difference(tall) if ln.intersects(tall) else ln for ln in tram_lines], area)  # tracks under buildings: wire ends at the facade
    for L, ends in zip(parts, _classify(parts, edge)):
        net.ends += [(L.coords[0][0], L.coords[0][1], ends[0]), (L.coords[-1][0], L.coords[-1][1], ends[1])]
        _run(ctx, L, H_TRAM, g, "tram", ends)
        g += 1
    accepted = None  # trolleybus: drop route stretches already wired by another route in the same lane
    lanes = []
    for ref, d, pts in routes:
        lane = _lane(pts, SIDE_OFF).intersection(area)
        for q in shapely.get_parts(lane):
            if q.geom_type != "LineString":
                continue
            if accepted is not None:
                q = q.difference(accepted)
            lanes += [x for x in shapely.get_parts(q) if x.geom_type == "LineString" and x.length > 3]
            accepted = shapely.union_all([accepted, q.buffer(2.5)]) if accepted is not None else q.buffer(2.5)
    parts = [x for x in shapely.get_parts(shapely.line_merge(shapely.union_all(lanes))) if x.geom_type == "LineString" and x.length >= 3] if lanes else []
    for L, ends in zip(parts, _classify(parts, edge)):
        net.ends += [(L.coords[0][0], L.coords[0][1], ends[0]), (L.coords[-1][0], L.coords[-1][1], ends[1])]
        _run(ctx, L, H_TROLLEY, g, "trolley", ends, pair=True)
        g += 1
    for i in ctx.used:  # LiDAR masts without a drawn game pole that carry a span
        if ctx.c[i, 3] < 0.5:
            net.poles.append([round(float(ctx.c[i, 0]), 2), round(float(ctx.c[i, 1]), 2), round(float(zf(ctx.c[i, 0], ctx.c[i, 1])), 2)])
    net.n_lidar = sum(1 for i in ctx.used if ctx.c[i, 3] < 0.5)
    net.poles = [list(r) for r in {tuple(r) for r in net.poles}]
    return net


def _clip(a, b, x0, y0, x1, y1):
    """Liang-Barsky: clipped (p, q) of segment a-b (3D) in the box, edge coordinates exact; None if outside."""
    t0, t1 = 0.0, 1.0
    for p, q in ((-(b[0] - a[0]), a[0] - x0), (b[0] - a[0], x1 - a[0]), (-(b[1] - a[1]), a[1] - y0), (b[1] - a[1], y1 - a[1])):
        if abs(p) < 1e-12:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return None
    f = lambda t: [min(max(a[0] + t * (b[0] - a[0]), x0), x1), min(max(a[1] + t * (b[1] - a[1]), y0), y1), a[2] + t * (b[2] - a[2])]
    return f(t0) if t0 > 0 else list(a), f(t1) if t1 < 1 else list(b)


def tile(net, tb):
    """(wires, poles) of one tile. Wires cut at the tile edge (endpoints exactly on it)."""
    x0, y0, x1, y1 = tb.bounds
    out = []
    for w in net.wires:
        P = w["pts"]
        xs = [p[0] for p in P]
        ys = [p[1] for p in P]
        if max(xs) < x0 or min(xs) > x1 or max(ys) < y0 or min(ys) > y1:
            continue
        run = []
        for a, b in zip(P[:-1], P[1:]):
            c = _clip(a, b, x0, y0, x1, y1)
            if c is None:
                if len(run) > 1:
                    out.append(run)
                run = []
                continue
            p, q = c
            if run and abs(run[-1][0] - p[0]) < 1e-6 and abs(run[-1][1] - p[1]) < 1e-6:
                run.append(q)
            else:
                if len(run) > 1:
                    out.append(run)
                run = [p, q]
        if len(run) > 1:
            out.append(run)
    out = [[[round(v, 2) for v in p] for p in r] for r in out]
    poles = [r for r in net.poles if x0 <= r[0] < x1 and y0 <= r[1] < y1]
    return out, poles
