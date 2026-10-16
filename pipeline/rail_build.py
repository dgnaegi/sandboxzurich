"""Oberbau: ballast, sleepers, rails, switches, signals, buffer stops, catenary masts/portals, tunnel portals, parked trains."""
import math
from collections import defaultdict

import numpy as np
from shapely import STRtree
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

from config import TILE

RAIL_TOP = 0.27      # rail head above terrain
WIRE_H = 5.5         # contact wire above rail head
SPAN = 60.0          # mast spacing
BALLAST_TOP = 0.08

C_BALLAST, C_SLOPE = (150, 144, 136), (120, 115, 108)   # multiplied with the ballast texture
C_SLEEP = (168, 164, 158)
C_HEAD, C_WEB = (205, 198, 190), (70, 66, 62)
C_TONGUE, C_FROG, C_BOX = (205, 205, 210), (64, 58, 54), (58, 62, 66)
C_MAST, C_SIGPOLE, C_SIGHEAD = (92, 98, 104), (200, 200, 200), (36, 38, 42)
C_BUFFER, C_PORTAL, C_DARK = (150, 52, 44), (150, 148, 144), (24, 24, 26)
UP = (0, 0, 1)


def tile_of(x, y):
    return int(math.floor(x / TILE)), int(math.floor(y / TILE))


def frames(pts):
    d = np.gradient(pts[:, :2], axis=0)
    t = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
    return t, np.column_stack([-t[:, 1], t[:, 0]])


def decimate(pts, tol=0.06, tol_z=0.03):
    """Douglas-Peucker in 3D (iterative): straight stretches of the 4 m samples collapse into long segments."""
    n = len(pts)
    keep = np.zeros(n, bool)
    keep[[0, n - 1]] = True
    stack = [(0, n - 1)]
    q = pts * np.array([1.0, 1.0, tol / tol_z])
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        seg = q[b] - q[a]
        d = q[a + 1:b] - q[a]
        L2 = max(float(seg @ seg), 1e-9)
        t = np.clip(d @ seg / L2, 0, 1)
        dist = np.linalg.norm(d - t[:, None] * seg, axis=1)
        i = int(dist.argmax())
        if dist[i] > tol or (L2 > 40 * 40):
            m = a + 1 + i if dist[i] > tol else (a + b) // 2
            keep[m] = True
            stack += [(a, m), (m, b)]
    return pts[keep]


def add_track(acc, pts, shoulders=True, jitter=1.0):
    """Track bed on a TrackAcc: ballast quad textured with the sleeper raster (u across, v along), shoulders, rails."""
    pts = decimate(pts)
    t, L = frames(pts)
    z0 = pts[:, 2]
    seg = np.linalg.norm(np.diff(pts[:, :2], axis=0), axis=1)
    v = np.concatenate([[0], np.cumsum(seg)]) / 2.4       # texture period = 2.4 m = 4 sleepers
    def at(u, dz):
        return np.column_stack([pts[:, 0] + L[:, 0] * u, pts[:, 1] + L[:, 1] * u, z0 + dz])
    def strip(u0, d0, u1, d1, color, tex=None):
        A, B = at(u0, d0), at(u1, d1)
        uv = None
        if tex is not None:
            ua, ub = (u0 + 2.75) / 5.5 * 0.8, (u1 + 2.75) / 5.5 * 0.8
            uv = np.stack([np.column_stack([np.full(len(v) - 1, ua), v[:-1]]), np.column_stack([np.full(len(v) - 1, ub), v[:-1]]),
                           np.column_stack([np.full(len(v) - 1, ub), v[1:]]), np.column_stack([np.full(len(v) - 1, ua), v[1:]])], 1)
        acc.quads(np.stack([A[:-1], B[:-1], B[1:], A[1:]], 1), UP, color, None, uv)
    j = lambda c: tuple(int(min(255, x * jitter)) for x in c)
    strip(-1.85, BALLAST_TOP, 1.85, BALLAST_TOP, j(C_BALLAST), True)
    if shoulders:
        strip(-2.75, -0.1, -1.85, BALLAST_TOP, j(C_SLOPE), True)
        strip(1.85, BALLAST_TOP, 2.75, -0.1, j(C_SLOPE), True)
    for s in (-1, 1):
        u = s * 0.7175
        strip(u - 0.04, RAIL_TOP, u + 0.04, RAIL_TOP, C_HEAD)
        strip(u - 0.09, 0.14, u + 0.09, 0.14, C_WEB)


def track_dirs(w, k):
    """Unit direction leaving the OSM node k (index into nidx) away from it, both ways along the way: [(dir_xy, wi_dir)]."""
    pts, ni = w["pts"], w["nidx"]
    i = ni[k]
    out = []
    for step in (1, -1):
        j = min(max(i + step * 3, 0), len(pts) - 1)
        if j != i:
            d = pts[j, :2] - pts[i, :2]
            out.append((d / max(np.linalg.norm(d), 1e-9), step))
    return out


def node_index(net):
    """OSM node id -> [(way index, k)] for every way that passes through it."""
    idx = defaultdict(list)
    for wi, w in enumerate(net.ways):
        for k, n in enumerate(w["nodes"]):
            idx[n].append((wi, k))
    return idx


def add_track_detail(net, accs, nidx, taccs):
    """Switch tongues, frogs, point machines, diamonds, signals, buffer stops."""
    ns = nsig = nbuf = 0
    for n, t in net.nodetags.items():
        if n not in nidx:
            continue
        x, y = net.nodes[n]
        occ = nidx[n]
        zs = float(np.mean([net.ways[wi]["pts"][net.ways[wi]["nidx"][k], 2] for wi, k in occ]))
        acc = accs[tile_of(x, y)]
        rt = t.get("railway")
        if rt == "switch" or rt == "railway_crossing":
            dirs = []
            for wi, k in occ:
                w = net.ways[wi]
                if w["cls"] != "ground":
                    continue
                for d, _ in track_dirs(w, k):
                    if not any(np.dot(d, e) > 0.98 for e in dirs):
                        dirs.append(d)
            if len(dirs) < 3 and rt == "switch" and t.get("railway:switch") != "double_slip":
                continue
            if t.get("railway:switch") == "double_slip" or rt == "railway_crossing":
                d = dirs[0] if dirs else np.array([1.0, 0])
                add_diamond(taccs[tile_of(x, y)], x, y, zs, d, dirs)
                ns += 1
                continue
            # stem = branch roughly opposite to the other two; diverging = the one deviating most from the stem axis
            best = None
            for i in range(len(dirs)):
                others = [dirs[j] for j in range(len(dirs)) if j != i]
                score = min(np.dot(dirs[i], o) for o in others)
                if best is None or score < best[0]:
                    best = (score, i)
            si = best[1]
            stem = dirs[si]
            others = sorted([d for j, d in enumerate(dirs) if j != si], key=lambda d: np.dot(d, -stem))
            div = others[0]
            if len(others) < 1:
                continue
            ns += 1
            add_switch(taccs[tile_of(x, y)], accs[tile_of(x, y)], x, y, zs, stem, div)
        elif rt == "signal":
            nsig += add_signal(net, accs, n, t, occ)
        elif rt == "buffer_stop":
            nbuf += add_buffer(net, accs, n, occ)
    return ns, nsig, nbuf


def add_switch(acc, wacc, x, y, z, stem, div):
    """Tongue blades along the diverging branch, frog beyond, point machine beside the stem."""
    zt = z + RAIL_TOP + 0.012
    straight = -stem
    side = np.cross(np.append(straight, 0), np.append(div, 0))[2]
    nrm = np.array([-straight[1], straight[0]])
    sg = 1.0 if side > 0 else -1.0       # side of the straight track on which the branch leaves
    rail_u = sg * 0.7175
    for d0, d1 in ((0.6, 7.5),):
        a = np.array([x, y]) + straight * d0 + nrm * (rail_u - 0.05 * sg)
        b = np.array([x, y]) + straight * d1 + nrm * (rail_u - 0.05 * sg)
        w = nrm * 0.045
        acc.quads([[*(a - w), zt], [*(b - w), zt], [*(b + w), zt], [*(a + w), zt]], UP, C_TONGUE)
    # frog: dark wedge where the branch rail crosses the straight rail
    c = np.array([x, y]) + straight * 13.0 + nrm * rail_u
    w = nrm * 0.16
    acc.quads([[*(c - straight * 1.4 - w), zt + 0.002], [*(c + straight * 1.4 - w * 0.2), zt + 0.002],
               [*(c + straight * 1.4 + w * 0.2), zt + 0.002], [*(c - straight * 1.4 + w), zt + 0.002]], UP, C_FROG)
    m = np.array([x, y]) + straight * 4.0 - nrm * sg * 2.15
    ang = math.atan2(straight[1], straight[0])
    wacc.box(-0.45, 0.45, -0.25, 0.25, z - 0.05, z + 0.55, C_BOX, ang, m[0], m[1])


def add_diamond(acc, x, y, z, d, dirs):
    zt = z + RAIL_TOP + 0.012
    for dd in dirs[:4]:
        n = np.array([-dd[1], dd[0]])
        a, b = np.array([x, y]) + dd * 0.4, np.array([x, y]) + dd * 2.6
        w = n * 0.14
        acc.quads([[*(a - w), zt], [*(b - w * 0.4), zt], [*(b + w * 0.4), zt], [*(a + w), zt]], UP, C_FROG)


def way_tangent_at(net, wi, k):
    w = net.ways[wi]
    pts, i = w["pts"], w["nidx"][k]
    a, b = pts[max(i - 1, 0), :2], pts[min(i + 1, len(pts) - 1), :2]
    d = b - a
    return d / max(np.linalg.norm(d), 1e-9), pts[i, 2]


def add_signal(net, accs, n, t, occ):
    wi, k = next(((wi, k) for wi, k in occ if net.ways[wi]["cls"] == "ground"), (None, None))
    if wi is None:
        return 0
    x, y = net.nodes[n]
    d, z = way_tangent_at(net, wi, k)
    fwd = t.get("railway:signal:direction", "forward") != "backward"
    pos = t.get("railway:signal:position", "left")
    L = np.array([-d[1], d[0]])
    off = 3.1 if pos in ("left", "bridge") else -3.1
    p = np.array([x, y]) + L * off
    acc = accs[tile_of(*p)]
    ang = math.atan2(d[1], d[0])
    big = any(k.startswith("railway:signal:combined") or k.startswith("railway:signal:main") for k in t)
    h = 4.6 if big else 3.2
    acc.box(-0.09, 0.09, -0.09, 0.09, z - 0.1, z + h, C_SIGPOLE, ang, p[0], p[1])
    face = -1.0 if fwd else 1.0       # lamp face looks at the approaching train
    hh = 1.25 if big else 0.7
    acc.box(-0.22, 0.22, -0.25, 0.25, z + h - hh, z + h + 0.05, C_SIGHEAD, ang, p[0], p[1])
    red = (hash(n) & 3) != 0 and t.get("railway:signal:combined:function") in ("exit", "entry", "block", "intermediate")
    cols = [(235, 50, 40) if red else (70, 220, 90)]
    if big:
        cols.append((250, 250, 250) if not red else (60, 60, 64))
    for i, c in enumerate(cols):
        zc = z + h - 0.35 - i * 0.5
        q = p + d * face * 0.26
        a, b = q - L * 0.12, q + L * 0.12
        acc.quads([[a[0], a[1], zc - 0.12], [b[0], b[1], zc - 0.12], [b[0], b[1], zc + 0.12], [a[0], a[1], zc + 0.12]],
                  (d[0] * face, d[1] * face, 0), c)
    return 1


def add_buffer(net, accs, n, occ):
    wi, k = occ[0]
    w = net.ways[wi]
    if w["cls"] != "ground" or 0 < k < len(w["nodes"]) - 1 or len(occ) > 1:
        return 0
    x, y = net.nodes[n]
    d, z = way_tangent_at(net, wi, k)
    if k == 0:                     # direction pointing away from the track
        d = -d
    ang = math.atan2(d[1], d[0])
    p = np.array([x, y]) + d * 0.3
    accs[tile_of(*p)].box(-0.3, 0.3, -1.1, 1.1, z + 0.1, z + 1.0, C_BUFFER, ang, p[0], p[1])
    return 1


def add_portals(net, accs, nidx):
    """Concrete portal frames where a tunnel chain meets ground track."""
    n = 0
    for wi, w in enumerate(net.ways):
        if w["cls"] != "tunnel":
            continue
        for k in (0, len(w["nodes"]) - 1):
            node = w["nodes"][k]
            if any(net.ways[o]["cls"] != "tunnel" for o, _ in nidx[node]):
                x, y = net.nodes[node]
                pts, i = w["pts"], w["nidx"][k]
                j = min(max(i + (4 if k == 0 else -4), 0), len(pts) - 1)
                d = pts[j, :2] - pts[i, :2]
                d = d / max(np.linalg.norm(d), 1e-9)
                z = float(pts[i, 2])
                ang = math.atan2(d[1], d[0])
                L = np.array([-d[1], d[0]])
                acc = accs[tile_of(x, y)]
                acc.box(-0.5, 0.5, -3.4, -2.3, z - 0.2, z + 6.2, C_PORTAL, ang, x + d[0] * 0.2, y + d[1] * 0.2)
                acc.box(-0.5, 0.5, 2.3, 3.4, z - 0.2, z + 6.2, C_PORTAL, ang, x + d[0] * 0.2, y + d[1] * 0.2)
                acc.box(-0.5, 0.5, -3.4, 3.4, z + 5.4, z + 6.4, C_PORTAL, ang, x + d[0] * 0.2, y + d[1] * 0.2)
                c = np.array([x, y]) + d * 0.75
                a, b = c - L * 2.3, c + L * 2.3
                acc.quads([[a[0], a[1], z], [b[0], b[1], z], [b[0], b[1], z + 5.4], [a[0], a[1], z + 5.4]], (d[0], d[1], 0), C_DARK)
                n += 1
    return n


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
    n_m = idx = 0
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
            ray = LineString([(p0.x - lx * 40, p0.y - ly * 40), (p0.x + lx * 40, p0.y + ly * 40)])
            cr = ray.intersection(allr)
            us = sorted({round(((g.x - p0.x) * lx + (g.y - p0.y) * ly), 1) for g in getattr(cr, "geoms", [cr]) if g.geom_type == "Point"} | {0.0})
            cl = [0.0]
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
            ang = math.atan2(ty, tx)
            top = zt + RAIL_TOP + WIRE_H + 2.2
            sides = [(-1, umin - 2.9), (1, umax + 2.9)]
            if nt <= 1:
                sides = [sides[idx % 2]]
            for sgn, u in sides:
                mx, my = p0.x + lx * u, p0.y + ly * u
                g = float(H.at(mx, my))
                base = min(g, zt) - 0.3 if abs(g - zt) < 6 else zt - 0.5
                post = 0.16 if nt < 3 else 0.2
                accs[tile_of(mx, my)].box(-post, post, -post, post, base, top + (0.6 if nt >= 3 else 0.4), C_MAST, ang, mx, my)
                n_m += 1
                if nt <= 2:
                    span_to = (umax if sgn < 0 else umin) if nt > 1 else 0.0
                    ln_arm = abs(u - span_to) + 0.4
                    ax, ay = mx - lx * sgn * ln_arm / 2, my - ly * sgn * ln_arm / 2
                    accs[tile_of(mx, my)].box(-0.07, 0.07, -ln_arm / 2, ln_arm / 2, top - 0.5, top - 0.25, C_MAST, ang, ax, ay)
            if nt >= 3:   # Quertragwerk: two chords + diagonals' verticals over all tracks
                w_ = umax - umin + 5.8
                acc = accs[tile_of(cx, cy)]
                zb = zt + RAIL_TOP + WIRE_H + 1.3
                for z0, z1 in ((zb, zb + 0.14), (zb + 1.1, zb + 1.24)):
                    acc.box(-0.09, 0.09, -w_ / 2, w_ / 2, z0, z1, C_MAST, ang, cx, cy)
                for v in np.arange(-w_ / 2 + 0.3, w_ / 2, 4.0):
                    acc.box(-0.05, 0.05, -0.05, 0.05, zb, zb + 1.2, C_MAST, ang, cx + lx * v, cy + ly * v)
    return n_m


def parked_trains(net, used_ways, cars=4, car_l=26.4):
    """Parked rakes on long siding/yard tracks no route uses -> {tile: [[x,y,z,yaw,pitch,kind,tint]]}."""
    out = defaultdict(list)
    for wi, w in enumerate(net.ways):
        if wi in used_ways or w["cls"] != "ground" or w["svc"] not in ("siding", "yard") or not w["elec"]:
            continue
        pts = w["pts"]
        ln = np.linalg.norm(np.diff(pts[:, :2], axis=0), axis=1)
        cum = np.concatenate([[0], np.cumsum(ln)])
        L = cum[-1]
        h = (w["id"] * 2654435761) >> 7
        if L < cars * car_l + 20 or h % 100 >= 55:
            continue
        # straight part only: skip when the way bends a lot
        rake = cars if L > cars * car_l + 30 else max(2, int((L - 12) // car_l))
        n = min(rake, cars + (h >> 8) % 2)
        s0 = (L - n * car_l) / 2 + ((h >> 4) % 7 - 3)
        flip = (h >> 11) & 1
        tint = (h >> 13) % 4
        for i in range(n):
            sc = s0 + (i + 0.5) * car_l
            def at(s):
                s = min(max(s, 0), L)
                j = min(np.searchsorted(cum, s, side="right") - 1, len(pts) - 2)
                f = (s - cum[j]) / max(ln[j], 1e-6)
                return pts[j] + (pts[j + 1] - pts[j]) * f
            a, b, c = at(sc), at(sc + 9), at(sc - 9)
            dx, dy, dz = b[0] - c[0], b[1] - c[1], b[2] - c[2]
            hd = math.hypot(dx, dy) or 1
            tail = (i == n - 1)
            yaw = math.atan2(-dx, dy) + (math.pi if tail else 0)
            pitch = math.atan2(dz, hd) * (-1 if tail else 1)
            kind = 0 if i == 0 or tail else 1
            out[tile_of(a[0], a[1])].append([round(a[0], 2), round(a[1], 2), round(a[2], 2), round(yaw, 3), round(pitch, 3), kind, tint])
    return out
