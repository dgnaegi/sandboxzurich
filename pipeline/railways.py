"""Railway layer for the play area: tracks on ballast, catenary, platforms, station signs, S-Bahn routes.

Reads OSM (sources.osm) and the terrain. Writes
  web/public/models/trains/tiles/r_{ix}_{iy}.glb   one merged mesh per 200 m tile (world material, layer = texture index)
  web/public/data/rail.json                          per tile: wires, sign/clock anchors; plus S-Bahn routes + stations
Run: python3 pipeline/railways.py   (needs data/raw/osm/kreise.json, swissALTI3D cache)
Integration: web/src/world/railways.ts (loads rail.json + tiles near the player).
"""
import json
import math
import subprocess
from collections import defaultdict
from heapq import heappop, heappush

import mapbox_earcut as earcut
import numpy as np
import shapely
from shapely.geometry import LineString, MultiLineString, Point, Polygon
from shapely.ops import unary_union
from shapely import STRtree

import glb
import sources
import terrain
from config import POLYGON, ROOT, TILE, tiles
from styles import LAYER

OUT_DIR = ROOT / "web" / "public" / "models" / "trains" / "tiles"
RAW_DIR = ROOT / "data" / "build" / "rail_raw"
DATA = ROOT / "web" / "public" / "data" / "rail.json"
TERRAIN_AREA = (-2849.0, -2069.0, 1952.0, 1454.0)
Z_SHIFT = -3.06
STEP = 4.0           # track sampling (m)
RAIL_TOP = 0.29      # rail head above terrain
BALLAST = 0.12
WIRE_H = 5.5         # contact wire above rail head
SPAN = 60.0          # mast spacing
PLATFORM_H = 0.55    # platform edge above rail head (SBB standard)
SERVICES = (None, "yard", "siding", "crossover", "spur")
ROUTE_SERVICES = (None, "crossover", "yard")

C_STEEL, C_RUST, C_SLEEP = (112, 108, 104), (98, 84, 74), (128, 124, 120)
C_MAST, C_DECK, C_KERB, C_LINE, C_WALL = (92, 98, 104), (150, 150, 152), (205, 205, 207), (245, 245, 245), (172, 170, 166)
C_ROOF_T, C_ROOF_B = (118, 124, 130), (205, 207, 212)


class Acc:
    """Batched quad accumulator (positions in local metres, z up); arrays() in three.js axes like mesh.Mesh."""

    def __init__(self):
        self.P, self.N, self.C, self.U, self.L = [], [], [], [], []

    def quads(self, P, hint, color, layer=None, uv=None):
        """P: (n,4,3) quads, hint: expected outward direction (3 or (n,3)); flips winding where needed."""
        P = np.asarray(P, np.float64).reshape(-1, 4, 3)
        if len(P) == 0:
            return
        n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        n += np.cross(P[:, 2] - P[:, 0], P[:, 3] - P[:, 0])
        h = np.broadcast_to(np.asarray(hint, np.float64), n.shape)
        flip = (n * h).sum(1) < 0
        P = np.where(flip[:, None, None], P[:, ::-1], P)
        n = np.where(flip[:, None], -n, n)
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        c = np.asarray(color) / 255
        lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
        col = np.append(np.round(lin * 255), 255)
        self.P.append(P.astype(np.float32))
        self.N.append(np.repeat(n[:, None], 4, 1).astype(np.float32))
        self.C.append(np.broadcast_to(col, (len(P), 4, 4)))
        self.U.append((P[:, :, :2] / 2.0).astype(np.float32) if uv is None else np.asarray(uv, np.float32).reshape(-1, 4, 2))
        self.L.append(np.full((len(P), 4), LAYER[layer or "white"], np.float32))

    def box(self, x0, x1, y0, y1, z0, z1, color, rot=0.0, cx=0.0, cy=0.0):
        """Axis box (local coords around origin) rotated by rot about z and moved to (cx, cy); no bottom face."""
        c, s = math.cos(rot), math.sin(rot)
        def p(x, y, z): return (cx + x * c - y * s, cy + x * s + y * c, z)
        a, b, d, e = p(x0, y0, z0), p(x1, y0, z0), p(x1, y1, z0), p(x0, y1, z0)
        a2, b2, d2, e2 = p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)
        ctr = np.array([(a[0] + d[0]) / 2, (a[1] + d[1]) / 2, (z0 + z1) / 2])
        faces = [[a, b, b2, a2], [b, d, d2, b2], [d, e, e2, d2], [e, a, a2, e2], [a2, b2, d2, e2]]
        for f in faces:
            f = np.array(f)
            self.quads(f, f.mean(0) - ctr, color)

    def arrays(self):
        if not self.P:
            return None
        P, N = np.concatenate(self.P).reshape(-1, 3), np.concatenate(self.N).reshape(-1, 3)
        n = len(P) // 4
        base = (np.arange(n) * 4)[:, None]
        idx = np.concatenate([base + [0, 1, 2], base + [0, 2, 3]], 1).reshape(-1, 3)
        sw = lambda a: np.column_stack([a[:, 0], a[:, 2], -a[:, 1]])
        uv = np.concatenate(self.U).reshape(-1, 2)
        uv = uv - np.floor(uv.min(0))
        return {"pos": sw(P), "nrm": sw(N), "col": np.concatenate(self.C).reshape(-1, 4), "idx": idx.astype(np.uint32),
                "uv": uv, "layer": np.concatenate(self.L).reshape(-1)}


# ---------------------------------------------------------------- OSM


def load_ways(H):
    """Rail ways with dense (x, y, z) samples. Returns (ways, platforms, roofs, stops)."""
    nodes, els = sources.osm()
    play = Polygon(POLYGON).buffer(260)
    ways, plats, roofs, stops = [], [], [], []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "node" and t.get("railway") in ("stop", "station") and t.get("train") == "yes" and e["id"] in nodes:
            stops.append({"name": t.get("name", ""), "x": nodes[e["id"]][0], "y": nodes[e["id"]][1], "ref": t.get("local_ref"), "kind": t["railway"]})
        if e["type"] != "way" or not all(n in nodes for n in e["nodes"]):
            continue
        xy = np.array([nodes[n] for n in e["nodes"]])
        if len(xy) < 2 or not play.intersects(LineString(xy)):
            continue
        if t.get("railway") == "rail" and t.get("service") in SERVICES:
            ways.append(dense_way(e, t, xy, H))
        elif t.get("railway") == "platform" or (t.get("public_transport") == "platform" and t.get("train") == "yes"):
            plats.append({"xy": xy, "tags": t})
        elif t.get("building") in ("roof", "train_station") and len(xy) >= 4 and (xy[0] == xy[-1]).all():
            roofs.append(xy)
    return ways, plats, roofs, stops


def dense_way(e, t, xy, H):
    seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    pts, nidx = [xy[0]], [0]
    for i in range(len(seg)):
        k = max(1, int(math.ceil(seg[i] / STEP)))
        for j in range(1, k + 1):
            pts.append(xy[i] + (xy[i + 1] - xy[i]) * j / k)
        nidx.append(len(pts) - 1)
    pts = np.array(pts)
    z = np.asarray(H.at(pts[:, 0], pts[:, 1]), np.float64)
    tunnel = t.get("tunnel") in ("yes", "building_passage")
    bridge = t.get("bridge") in ("yes", "viaduct") or t.get("bridge") is not None and t.get("bridge") != "no"
    if tunnel:
        z = z - 7.0
    elif bridge and len(z) > 2:
        z = np.interp(np.arange(len(z)), [0, len(z) - 1], [z[0], z[-1]])
    elif len(z) > 4:
        k = 3
        pad = np.pad(z, k, mode="edge")
        sm = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
        z = sm
        z[0], z[-1] = H.at(*pts[0]), H.at(*pts[-1])
    cls = "tunnel" if tunnel else "bridge" if bridge else "ground"
    return {"id": e["id"], "nodes": e["nodes"], "nidx": nidx, "pts": np.column_stack([pts, z]), "svc": t.get("service"),
            "cls": cls, "elec": t.get("electrified") != "no"}


# ---------------------------------------------------------------- track geometry


def frames(pts):
    """Tangent and left normal per sample (xy)."""
    d = np.gradient(pts[:, :2], axis=0)
    t = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    return t, np.column_stack([-t[:, 1], t[:, 0]])


def add_track(acc, pts, lift):
    """Ballast, sleepers and rails for one dense polyline (all segments belong to one tile)."""
    t, L = frames(pts)
    z0 = pts[:, 2] + lift
    def at(u, dz, a=slice(None)):
        return np.column_stack([pts[a, 0] + L[a, 0] * u, pts[a, 1] + L[a, 1] * u, z0[a] + dz])
    up = (0, 0, 1)
    A, B = at(-2.3, 0.04), at(2.3, 0.04)
    acc.quads(np.stack([A[:-1], B[:-1], B[1:], A[1:]], 1), up, (150, 148, 144), "dach_kies")
    # sleepers: every 1.3 m, 0.35 m wide (cheap stand-in for 0.65 m spacing)
    seg = pts[1:, :2] - pts[:-1, :2]
    ln = np.linalg.norm(seg, axis=1)
    cnt = np.maximum(1, np.round(ln / 1.3).astype(int))
    si = np.repeat(np.arange(len(seg)), cnt)
    k = np.concatenate([np.arange(c) for c in cnt])
    f = ((k + 0.5) / cnt[si])[:, None]
    ctr = pts[si, :] + (pts[si + 1, :] - pts[si, :]) * f
    ts, ls = t[si], L[si]
    zz = ctr[:, 2] + lift + 0.075
    def sl(a, b):
        return np.column_stack([ctr[:, 0] + ts[:, 0] * a + ls[:, 0] * b, ctr[:, 1] + ts[:, 1] * a + ls[:, 1] * b, zz])
    acc.quads(np.stack([sl(-0.17, -1.3), sl(0.17, -1.3), sl(0.17, 1.3), sl(-0.17, 1.3)], 1), up, C_SLEEP)
    for s in (-1, 1):  # rails (gauge 1.435), head only; raised so they read from above
        u0 = s * 0.7175
        R_, R2 = at(u0 - 0.05, RAIL_TOP - 0.1), at(u0 + 0.05, RAIL_TOP - 0.1)
        acc.quads(np.stack([R_[:-1], R2[:-1], R2[1:], R_[1:]], 1), up, C_STEEL)


def tile_of(x, y):
    return int(math.floor(x / TILE)), int(math.floor(y / TILE))


def build_tracks(ways, accs, runs):
    """Distribute track geometry over tile accumulators; collect electrified runs per tile (wires are built in the client)."""
    for w in ways:
        if w["cls"] == "tunnel":
            continue
        pts = w["pts"]
        mid = (pts[:-1, :2] + pts[1:, :2]) / 2
        keys = np.floor(mid / TILE).astype(int)
        # runs of equal tile key (overlap one sample so there are no gaps)
        i = 0
        while i < len(keys):
            j = i
            while j + 1 < len(keys) and (keys[j + 1] == keys[i]).all():
                j += 1
            run = pts[i:j + 2]
            if len(run) >= 2:
                key = (int(keys[i][0]), int(keys[i][1]))
                add_track(accs[key], run, 0.0)
                if w["elec"] and w["svc"] in (None, "yard", "crossover", "siding"):
                    runs[key].append(np.round(run * 10).astype(int).ravel().tolist())
            i = j + 1


# ---------------------------------------------------------------- masts


def add_masts(ways, accs, H):
    lines = []
    for w in ways:
        if w["cls"] == "tunnel" or not w["elec"] or w["svc"] not in (None, "yard", "crossover"):
            continue
        lines.append(LineString(w["pts"][:, :2]))
    allr = unary_union(lines)
    samp = np.concatenate([w["pts"] for w in ways if w["cls"] != "tunnel"])
    tree = STRtree([Point(p[0], p[1]) for p in samp[::2]])
    sampz = samp[::2]
    placed = []
    n_m = 0
    idx = 0
    for ln in sorted(lines, key=lambda l: -l.length):
        for d in np.arange(10.0, ln.length - 5.0, SPAN):
            p0, p1 = ln.interpolate(d), ln.interpolate(min(ln.length, d + 2))
            tx, ty = p1.x - p0.x, p1.y - p0.y
            nl = math.hypot(tx, ty)
            if nl < 1e-6:
                continue
            tx, ty = tx / nl, ty / nl
            lx, ly = -ty, tx
            if any(math.hypot(p0.x - q[0], p0.y - q[1]) < 38 for q in placed):
                continue
            ray = LineString([(p0.x - lx * 28, p0.y - ly * 28), (p0.x + lx * 28, p0.y + ly * 28)])
            cr = ray.intersection(allr)
            us = sorted({round(((g.x - p0.x) * lx + (g.y - p0.y) * ly), 1) for g in getattr(cr, "geoms", [cr]) if g.geom_type == "Point"} | {0.0})
            cl = [0.0]  # cluster containing the track at u = 0: gaps <= 9 m
            for u in [u for u in us if u > 0]:
                if u - cl[-1] <= 9:
                    cl.append(u)
                else:
                    break
            neg = [0.0]
            for u in sorted([u for u in us if u < 0], reverse=True):
                if neg[-1] - u <= 9:
                    neg.append(u)
                else:
                    break
            umin, umax = min(neg), max(cl)
            nt = len({round(u / 3) for u in us if umin - .1 <= u <= umax + .1})
            ctr = (umin + umax) / 2
            cx, cy = p0.x + lx * ctr, p0.y + ly * ctr
            placed.append((cx, cy))
            zt = float(sampz[tree.nearest(Point(cx, cy))][2])
            idx += 1
            sides = [(-1, umin - 2.9), (1, umax + 2.9)]
            if nt <= 1:
                sides = [sides[idx % 2]]
            for sgn, u in sides:
                mx, my = p0.x + lx * u, p0.y + ly * u
                g = float(H.at(mx, my))
                base = min(g, zt) - 0.3 if abs(g - zt) < 6 else zt - 0.5
                top = zt + RAIL_TOP + WIRE_H + 2.6
                ang = math.atan2(ty, tx)
                acc = accs[tile_of(mx, my)]
                acc.box(-0.16, 0.16, -0.16, 0.16, base, top, C_MAST, ang, mx, my)
                n_m += 1
                if nt <= 2:  # cantilever arm over the track(s)
                    span_to = (umax if sgn < 0 else umin) if nt > 1 else 0.0
                    ln_arm = abs(u - span_to) + 0.4
                    ax, ay = mx - lx * sgn * ln_arm / 2, my - ly * sgn * ln_arm / 2
                    acc.box(-0.07, 0.07, -ln_arm / 2, ln_arm / 2, top - 0.5, top - 0.25, C_MAST, ang, ax, ay)
            if nt >= 3:  # portal: cross beam over all tracks
                w_ = umax - umin + 5.8
                acc.box(-0.18, 0.18, -w_ / 2, w_ / 2, zt + RAIL_TOP + WIRE_H + 1.6, zt + RAIL_TOP + WIRE_H + 2.5, C_MAST,
                        math.atan2(ty, tx), cx, cy)
    return n_m


# ---------------------------------------------------------------- platforms


def platform_polys(plats, ways):
    """Platform polygons near passenger tracks (not tram-only stops)."""
    lines = [LineString(w["pts"][:, :2]) for w in ways if w["cls"] != "tunnel" and w["svc"] in (None, "crossover", "yard")]
    tracks = unary_union(lines)
    out = []
    for p in plats:
        xy = p["xy"]
        if tracks.distance(Point(*xy[len(xy) // 2])) > 14 and tracks.distance(Point(*xy[0])) > 14:
            continue
        if (xy[0] == xy[-1]).all() and len(xy) >= 4:
            poly = Polygon(xy).buffer(0)
        else:
            ls = LineString(xy)
            sgn = 1
            o = ls.offset_curve(3.2)
            if not o.is_empty and tracks.distance(o) < tracks.distance(ls.offset_curve(-3.2)):
                sgn = -1
            o = ls.offset_curve(3.2 * sgn)
            if o.is_empty or o.geom_type != "LineString":
                continue
            poly = Polygon(list(ls.coords) + list(o.coords)[::-1]).buffer(0)
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda g: g.area)
        if poly.is_empty or poly.area < 8 or poly.area > 6000:
            continue
        out.append(poly)
    return out, tracks, lines


def add_platforms(polys, tracks, ways, roofs, accs, H, signs, stops):
    samp = np.concatenate([w["pts"] for w in ways if w["cls"] != "tunnel" and w["svc"] in (None, "crossover", "yard")])
    tree = STRtree([Point(p[0], p[1]) for p in samp])
    def rail_z(x, y):
        return float(samp[tree.nearest(Point(x, y))][2]) + RAIL_TOP

    n_roof = 0
    for poly in polys:
        poly = shapely.segmentize(poly, 20.0)
        if not poly.exterior.is_ccw:
            poly = Polygon(list(poly.exterior.coords)[::-1])
        ring = np.asarray(poly.exterior.coords)[:-1]
        zt = np.array([rail_z(x, y) + PLATFORM_H for x, y in ring])
        tri = earcut.triangulate_float64(ring, np.array([len(ring)], np.uint32)).reshape(-1, 3)
        # deck top (triangles as degenerate quads), keyed to the tile of the centroid
        c = poly.centroid
        acc = accs[tile_of(c.x, c.y)]
        if len(tri):
            tq = np.stack([ring[tri[:, 0]], ring[tri[:, 1]], ring[tri[:, 2]], ring[tri[:, 2]]], 1)
            zq = zt[tri]
            P = np.concatenate([tq, np.concatenate([zq, zq[:, 2:3]], 1)[..., None]], 2)
            acc.quads(P, (0, 0, 1), C_DECK)
        for i in range(len(ring)):
            a, b = ring[i], ring[(i + 1) % len(ring)]
            za, zb = zt[i], zt[(i + 1) % len(ring)]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            d = math.hypot(*(b - a))
            if d < 0.2:
                continue
            tx, ty = (b - a) / d
            out = np.array([ty, -tx, 0.0])  # outward for CCW ring
            trackside = tracks.distance(Point(mx, my)) < 4.5
            bot_a = (rail_z(*a) - RAIL_TOP + 0.1) if trackside else float(H.at(*a)) - 0.3
            bot_b = (rail_z(*b) - RAIL_TOP + 0.1) if trackside else float(H.at(*b)) - 0.3
            bot_a, bot_b = min(bot_a, za - 0.3), min(bot_b, zb - 0.3)
            acc.quads([[a[0], a[1], bot_a], [b[0], b[1], bot_b], [b[0], b[1], zb], [a[0], a[1], za]], out, C_WALL)
            if trackside:  # kerb band and white safety line, inset from the edge
                inn = -out[:2]
                def pp(p, z, u): return [p[0] + inn[0] * u, p[1] + inn[1] * u, z + 0.012]
                acc.quads([pp(a, za, 0.0), pp(b, zb, 0.0), pp(b, zb, 0.45), pp(a, za, 0.45)], (0, 0, 1), C_KERB)
                acc.quads([pp(a, za, 0.85), pp(b, zb, 0.85), pp(b, zb, 0.97), pp(a, za, 0.97)], (0, 0, 1), C_LINE)
        # roofs over this platform
        rect = poly.minimum_rotated_rectangle
        rc = np.asarray(rect.exterior.coords)[:4]
        e0, e1 = rc[1] - rc[0], rc[2] - rc[1]
        ax = (e0 if np.linalg.norm(e0) >= np.linalg.norm(e1) else e1)
        plen = np.linalg.norm(ax)
        ax = ax / max(plen, 1e-6)
        mid = np.array([poly.centroid.x, poly.centroid.y])
        zp = float(np.mean(zt))
        for roof in roofs:
            rp = Polygon(roof).buffer(0)
            if rp.is_empty or not rp.intersects(poly):
                continue
            inter = rp.intersection(poly)
            if inter.area < 15:
                continue
            n_roof += 1
            rz = zp + 3.6
            rr = np.asarray(rp.exterior.coords)[:-1]
            if not rp.exterior.is_ccw:
                rr = rr[::-1]
            t = earcut.triangulate_float64(rr, np.array([len(rr)], np.uint32)).reshape(-1, 3)
            if len(t):
                tq = np.stack([rr[t[:, 0]], rr[t[:, 1]], rr[t[:, 2]], rr[t[:, 2]]], 1)
                for zz, col, hint in ((rz + 0.3, C_ROOF_T, 1), (rz, C_ROOF_B, -1)):
                    P = np.concatenate([tq, np.full(tq.shape[:2] + (1,), zz)], 2)
                    accs[tile_of(*mid)].quads(P, (0, 0, hint), col)
            for i in range(len(rr)):
                a, b = rr[i], rr[(i + 1) % len(rr)]
                d = np.linalg.norm(b - a)
                if d < 0.2:
                    continue
                out = np.array([(b - a)[1], -(b - a)[0], 0.0])
                accs[tile_of(*mid)].quads([[a[0], a[1], rz], [b[0], b[1], rz], [b[0], b[1], rz + 0.3], [a[0], a[1], rz + 0.3]], out, C_ROOF_T)
            ci = inter.centroid
            sub = np.arange(-plen / 2 + 3, plen / 2 - 2, 12.0)
            for sd in sub:
                p = mid + ax * sd
                if inter.buffer(0.5).contains(Point(*p)):
                    accs[tile_of(*p)].box(-0.18, 0.18, -0.18, 0.18, zp, rz, C_MAST, 0.0, p[0], p[1])
        # name signs + clock posts along the platform centre line
        near = [s for s in stops if math.hypot(s["x"] - mid[0], s["y"] - mid[1]) < 120]
        if near and plen > 25:
            nm = min(near, key=lambda s: math.hypot(s["x"] - mid[0], s["y"] - mid[1]))["name"]
            yaw = math.atan2(ax[1], ax[0])
            for frac, kind in ((-0.3, 0), (0.0, 1), (0.3, 0)):
                p = mid + ax * plen * frac
                if not poly.buffer(-0.3).contains(Point(*p)):
                    continue
                zd = rail_z(*p) + PLATFORM_H
                h = 2.5 if kind == 0 else 3.0
                accs[tile_of(*p)].box(-0.05, 0.05, -0.05, 0.05, zd, zd + h, C_MAST, 0.0, p[0], p[1])
                signs[tile_of(*p)].append([round(p[0], 2), round(p[1], 2), round(zd + h, 2), round(yaw, 3), nm, kind])
    return n_roof


# ---------------------------------------------------------------- routes (S-Bahn)


def build_graph(ways):
    adj = defaultdict(list)
    xy = {}
    for wi, w in enumerate(ways):
        if w["svc"] not in ROUTE_SERVICES:
            continue
        ni, pts = w["nidx"], w["pts"]
        for k in range(len(ni) - 1):
            a, b = w["nodes"][k], w["nodes"][k + 1]
            xy[a], xy[b] = pts[ni[k], :2], pts[ni[k + 1], :2]
            seg = pts[ni[k]:ni[k + 1] + 1]
            ln = float(np.linalg.norm(np.diff(seg[:, :2], axis=0), axis=1).sum()) * (1.0 if w["svc"] is None else 1.4)
            adj[a].append((b, ln, wi, ni[k], ni[k + 1]))
            adj[b].append((a, ln, wi, ni[k + 1], ni[k]))
    return adj, xy


def dijkstra(adj, srcs, dsts, used=None):
    best = {s: 0.0 for s in srcs}
    prev = {}
    h = [(0.0, s) for s in srcs]
    dsts = set(dsts)
    while h:
        d, u = heappop(h)
        if d > best.get(u, 1e18):
            continue
        if u in dsts:
            path = []
            while u in prev:
                pu, e = prev[u]
                path.append(e)
                u = pu
            return d, path[::-1], u
        for v, ln, wi, i0, i1 in adj[u]:
            pen = 1.3 if used and (min(u, v), max(u, v)) in used else 1.0
            nd = d + ln * pen
            if nd < best.get(v, 1e18):
                best[v] = nd
                prev[v] = (u, (u, v, wi, i0, i1))
                heappush(h, (nd, v))
    return None


def nearest_nodes(xy, p, r):
    return [n for n, q in xy.items() if math.hypot(q[0] - p[0], q[1] - p[1]) < r]


def route(adj, xy, ways, groups, used):
    """Chain shortest paths through node groups (start, stops..., end). Returns (pts, stop_s, edges)."""
    cur = groups[0]
    pts, stop_s, edges = [], [], []
    for gi, g in enumerate(groups[1:]):
        if gi < len(groups) - 2:  # stop: pick the platform track with the cheapest way in AND out
            best = None
            for n in g:
                a = dijkstra(adj, cur, [n], used)
                b = dijkstra(adj, [n], groups[gi + 2], used)
                if a and b and (best is None or a[0] + b[0] < best[0]):
                    best = (a[0] + b[0], n)
            if best is None:
                return None
            g = [best[1]]
        r = dijkstra(adj, cur, g, used)
        if r is None:
            return None
        _, path, node = r
        for u, v, wi, i0, i1 in path:
            seg = ways[wi]["pts"][i0:i1 + 1] if i1 >= i0 else ways[wi]["pts"][i1:i0 + 1][::-1]
            pts.extend(seg if not pts else seg[1:] if np.allclose(pts[-1], seg[0], atol=1.0) else seg)
            edges.append((min(u, v), max(u, v)))
        end = path[-1][1] if path else node
        stop_s.append(len(pts) - 1)
        cur = [end]
    return np.array(pts), stop_s, edges


def build_routes(ways, stops):
    adj, xy = build_graph(ways)
    near = lambda p, r=30: nearest_nodes(xy, p, r)
    grp = lambda name: [near((s["x"], s["y"]), 12) for s in stops if s["name"] == name and s["kind"] == "stop"]
    flat = lambda gs: [n for g in gs for n in g]
    alt, hard, wied = flat(grp("Zürich Altstetten")), flat(grp("Zürich Hardbrücke")), flat(grp("Zürich Wiedikon"))
    west = sorted(near((-2560, 830), 250), key=lambda n: math.hypot(xy[n][0] + 2560, xy[n][1] - 830))[:6]
    east = near((1690, -640), 60)
    south = sorted(near((430, -1295), 900), key=lambda n: xy[n][1])[:6]
    specs = [("S-Bahn Altstetten", [west, alt, hard, east], ["Zürich Altstetten", "Zürich Hardbrücke"]),
             ("S-Bahn Wiedikon", [south, wied, east], ["Zürich Wiedikon"])]
    out, used = [], set()
    for name, groups, stop_names in specs:
        for d, gs in ((0, groups), (1, groups[::-1])):
            r = route(adj, xy, ways, gs, used)
            if r is None:
                print("no route", name, d)
                continue
            pts, idx, edges = r
            used.update(edges)
            names = stop_names if d == 0 else stop_names[::-1]
            cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts[:, :2], axis=0), axis=1))])
            stp = [{"name": nm, "s": round(float(cum[i]), 1)} for nm, i in zip(names, idx[:-1])]
            out.append({"name": name, "dir": d, "len": round(float(cum[-1]), 1), "stops": stp,
                        "pts": np.round(pts * 10).astype(int).ravel().tolist()})
            print(name, d, "len", round(cum[-1]), "stops", stp)
    return out


def write_tiles(accs, runs, signs, routes):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    keep = {(ix, iy) for ix, iy in tiles()}
    names = sorted({s[4] for v in signs.values() for s in v})
    meta, tris = {}, 0
    for key in sorted(set(accs) | set(runs)):
        if key not in keep:
            continue
        nm = f"r_{key[0]}_{key[1]}"
        arr = accs[key].arrays() if key in accs else None
        if arr is not None:
            raw = RAW_DIR / f"{nm}.glb"
            glb.write(raw, {"rail": arr})
            subprocess.run(["npx", "--no-install", "gltfpack", "-i", str(raw), "-o", str(OUT_DIR / f"{nm}.glb"), "-cc", "-kv", "-km", "-vtf", "-vp", "15"],
                           cwd=ROOT / "web", check=True, capture_output=True)
            tris += len(arr["idx"])
        m = {}
        if runs.get(key):
            m["wr"] = runs[key]
        if signs.get(key):
            m["sg"] = [[*s[:4], names.index(s[4]), s[5]] for s in signs[key]]
        if arr is not None:
            m["glb"] = 1
        meta[f"{key[0]}_{key[1]}"] = m
    DATA.write_text(json.dumps({"tile": TILE, "stations": names, "tiles": meta, "routes": routes}, separators=(",", ":")))
    print("tiles", len(meta), "tris", tris, "rail.json KB", DATA.stat().st_size // 1024)


def main():
    H = terrain.heights(TERRAIN_AREA, 2.0, z_shift=Z_SHIFT)
    ways, plats, roofs, stops = load_ways(H)
    accs, runs, signs = defaultdict(Acc), defaultdict(list), defaultdict(list)
    build_tracks(ways, accs, runs)
    nm = add_masts(ways, accs, H)
    polys, tracks, _ = platform_polys(plats, ways)
    nr = add_platforms(polys, tracks, ways, roofs, accs, H, signs, stops)
    print("ways", len(ways), "masts", nm, "platforms", len(polys), "roofs", nr, "signs", sum(len(v) for v in signs.values()))
    routes = build_routes(ways, stops)
    write_tiles(accs, runs, signs, routes)


if __name__ == "__main__":
    main()
