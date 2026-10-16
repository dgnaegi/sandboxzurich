"""Train routes on the directed track graph: no reversals inside the graph (turn limit at switches), right-hand running
where OSM says railway:preferred_direction, platform stops aligned to the platform centre."""
import math
from heapq import heappop, heappush

import numpy as np
from shapely import STRtree
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

SVC_COST = {None: 1.0, "crossover": 1.25, "yard": 1.9, "siding": 6.0, "spur": 6.0}
MAX_TURN = math.cos(math.radians(38))


class Graph:
    def __init__(self, net, allow=("crossover", "yard", None), avoid_platforms=False):
        self.net = net
        self.avoid = unary_union([LineString(p["xy"]).buffer(3.2) for p in net.plats]) if avoid_platforms and net.plats else None
        self.E = []                    # (u, v, wi, i0, i1, length, cost)
        self.out = {}                  # node -> [edge ids]
        self.dirs = []                 # (dir at start, dir at end)
        lines = [(wi, LineString(w["pts"][:, :2])) for wi, w in enumerate(net.ways) if w["cls"] != "tunnel" and w["svc"] in allow]
        self._lines = [l for _, l in lines]
        self._lw = [wi for wi, _ in lines]
        self._tree = STRtree(self._lines)
        for wi, w in enumerate(net.ways):
            if w["svc"] not in allow or w["cls"] == "bridge" and False:
                continue
            ni, pts = w["nidx"], w["pts"]
            pd = w["tags"].get("railway:preferred_direction")
            for k in range(len(ni) - 1):
                a, b, i0, i1 = w["nodes"][k], w["nodes"][k + 1], ni[k], ni[k + 1]
                seg = pts[i0:i1 + 1]
                ln = float(np.linalg.norm(np.diff(seg[:, :2], axis=0), axis=1).sum())
                if ln < 0.01:
                    continue
                base = ln * SVC_COST[w["svc"]]
                for fwd in (True, False):
                    s = seg if fwd else seg[::-1]
                    u, v = (a, b) if fwd else (b, a)
                    cost = base * (3.5 if (pd == "forward" and not fwd) or (pd == "backward" and fwd) else 1.0)
                    if pd is None and w["svc"] is None:
                        cost *= self.left_hand_penalty(wi, s)
                    if self.avoid is not None and self.avoid.contains(Point(*s[len(s) // 2, :2])):
                        cost *= 4.0
                    d0 = unit(s[min(2, len(s) - 1), :2] - s[0, :2])
                    d1 = unit(s[-1, :2] - s[max(len(s) - 3, 0), :2])
                    self.out.setdefault(u, []).append(len(self.E))
                    self.E.append((u, v, wi, i0 if fwd else i1, i1 if fwd else i0, ln, cost))
                    self.dirs.append((d0, d1))

    def left_hand_penalty(self, wi, seg):
        """Swiss trains keep right: the opposing track of a double-track pair lies on the left. Penalise the other way round."""
        m = len(seg) // 2
        p = seg[m, :2]
        d = unit(seg[min(m + 1, len(seg) - 1), :2] - seg[max(m - 1, 0), :2])
        n = np.array([-d[1], d[0]])
        left = right = 0
        for j in self._tree.query(Point(*p).buffer(7.0)):
            if self._lw[j] == wi:
                continue
            ln = self._lines[j]
            s_ = ln.project(Point(*p))
            q = np.array(ln.interpolate(s_).coords[0])
            q2 = np.array(ln.interpolate(min(s_ + 3, ln.length)).coords[0]); q1 = np.array(ln.interpolate(max(s_ - 3, 0)).coords[0])
            tq = unit(q2 - q1)
            v = q - p
            lat = float(v @ n)
            if abs(float(tq @ d)) < 0.93 or abs(float(v @ d)) > 2.5:
                continue
            if 3.3 <= lat <= 6.6:
                left += 1
            elif -6.6 <= lat <= -3.3:
                right += 1
        return 1.7 if (right and not left) else 1.0

    def near_nodes(self, p, r):
        nodes = self.net.nodes
        return [n for n in self.out if math.hypot(nodes[n][0] - p[0], nodes[n][1] - p[1]) < r]

    def search(self, srcs, dst_nodes, prev_edge_dir=None):
        """srcs: [(edge or None, node)]; returns {dst_node: (cost, edge_list)}. Edge list ends at dst_node."""
        dst = set(dst_nodes)
        best, prev, h = {}, {}, []
        for node, e0 in srcs:
            for e in self.out.get(node, []):
                if e0 is not None and np.dot(self.dirs[e0][1], self.dirs[e][0]) < MAX_TURN:
                    continue
                c = self.E[e][6]
                if c < best.get(e, 1e18):
                    best[e] = c; prev[e] = None
                    heappush(h, (c, e))
        found = {}
        while h:
            c, e = heappop(h)
            if c > best.get(e, 1e18):
                continue
            v = self.E[e][1]
            if v in dst and v not in found:
                path, x = [], e
                while x is not None:
                    path.append(x); x = prev[x]
                found[v] = (c, path[::-1])
                if len(found) == len(dst):
                    break
            for e2 in self.out.get(v, []):
                if self.E[e2][1] == self.E[e][0]:
                    continue
                if np.dot(self.dirs[e][1], self.dirs[e2][0]) < MAX_TURN:
                    continue
                nc = c + self.E[e2][6]
                if nc < best.get(e2, 1e18):
                    best[e2] = nc; prev[e2] = e
                    heappush(h, (nc, e2))
        return found

    def edge_pts(self, e):
        _, _, wi, i0, i1, _, _ = self.E[e]
        p = self.net.ways[wi]["pts"]
        return p[i0:i1 + 1] if i1 >= i0 else p[i1:i0 + 1][::-1]


def unit(d):
    n = float(np.linalg.norm(d))
    return d / n if n > 1e-9 else np.array([1.0, 0.0])


def chain_route(G, groups, stops_idx=None):
    """groups[0] start node set, groups[-1] end node set, middle groups = alternative stop nodes (a train must pass one).
    Returns (edge list, [index of the arrival edge per stop]) or None; stop choice minimises the whole remaining route."""
    def rec(cur, gi):
        res = G.search(cur, groups[gi])
        if not res:
            return None
        if gi == len(groups) - 1:
            n, (c, path) = min(res.items(), key=lambda kv: kv[1][0])
            return c, path, []
        best = None
        for n, (c, path) in res.items():
            rest = rec([(n, path[-1])], gi + 1)
            if rest and (best is None or c + rest[0] < best[0]):
                best = (c + rest[0], path + rest[1], [len(path) - 1] + [len(path) + i for i in rest[2]])
        return best
    r = rec([(n, None) for n in groups[0]], 1)
    return None if r is None else (r[1], r[2])


def polyline(G, edges):
    pts = []
    for e in edges:
        seg = G.edge_pts(e)
        pts.extend(seg if not pts else seg[1:])
    return np.array(pts)


def project_s(pts, cum, p):
    """Arc length of the point on the polyline nearest to p (xy)."""
    best = (1e18, 0.0)
    a, b = pts[:-1, :2], pts[1:, :2]
    d = b - a
    L2 = np.maximum((d * d).sum(1), 1e-9)
    t = np.clip(((p - a) * d).sum(1) / L2, 0, 1)
    q = a + d * t[:, None]
    dist = np.linalg.norm(q - p, axis=1)
    i = int(dist.argmin())
    return float(cum[i] + t[i] * np.sqrt(L2[i])), float(dist[i])


def platform_centre(net, stop_xy, tracks_pt):
    """Centre of the platform polygon/line nearest to the stopping point."""
    best = None
    for p in net.plats:
        xy = p["xy"]
        ln = LineString(xy)
        d = ln.distance(Point(*tracks_pt))
        if d < 12 and (best is None or d < best[0]):
            best = (d, xy)
    if best is None:
        return None
    xy = best[1]
    if len(xy) >= 4 and (xy[0] == xy[-1]).all():
        return np.asarray(Polygon(xy).centroid.coords[0])
    return np.asarray(LineString(xy).interpolate(0.5, normalized=True).coords[0])


def hb_end(net, ref):
    """OSM node at the buffer-stop end of Zuerich HB track `ref` (railway:track_ref)."""
    for w in net.ways:
        if w["cls"] == "ground" and w["tags"].get("railway:track_ref") == ref and w["svc"] is None:
            for n in (w["nodes"][0], w["nodes"][-1]):
                t = net.nodetags.get(n)
                if t and t.get("railway") == "buffer_stop":
                    return [n]
    return []


def finish(G, net, sp, d, edges, stop_at, names):
    pts = polyline(G, edges)
    cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts[:, :2], axis=0), axis=1))])
    vlen = sp["cars"] * 26.4
    stp = []
    for nm, ei in zip(names, stop_at):
        node = G.E[edges[ei]][1]
        nx, ny = net.nodes[node]
        pc = platform_centre(net, (nx, ny), (nx, ny))
        s = project_s(pts, cum, pc)[0] if pc is not None else float(sum(G.E[e][5] for e in edges[:ei + 1]))
        stp.append({"name": nm, "s": round(s, 1)})
    r = {"name": sp["name"], "dir": d, "len": round(float(cum[-1]), 1), "stops": stp, "v": sp["v"], "cars": sp["cars"],
         "head": sp["head"], "pts": np.round(pts * 10).astype(int).ravel().tolist(), "ways": sorted({G.E[e][2] for e in edges})}
    return r, cum


def build_routes(net, stops):
    G = Graph(net)
    Gic = Graph(net, avoid_platforms=True)
    near = lambda p, r=30: G.near_nodes(p, r)
    sel = lambda name, r=14: sorted({n for s in stops if s["name"] == name and s["kind"] == "stop" for n in near((s["x"], s["y"]), r)})
    alt, hard, wied = sel("Zürich Altstetten"), sel("Zürich Hardbrücke"), sel("Zürich Wiedikon")
    west = sorted(near((-2560, 830), 250), key=lambda n: math.hypot(net.nodes[n][0] + 2560, net.nodes[n][1] - 830))[:8]
    tun = [n for w in net.ways if w["cls"] == "tunnel" and w["tags"].get("ref") == "748" for n in w["nodes"]
           if net.nodes[n][0] > 1450 and n in G.out]       # Durchmesserlinie (Weinbergtunnel) towards HB Loewenstrasse
    south = sorted(near((430, -1295), 900), key=lambda n: net.nodes[n][1])[:8]
    specs = [
        dict(name="S-Bahn Altstetten", groups=[west, alt, hard, hb_end(net, "15")], stops=["Zürich Altstetten", "Zürich Hardbrücke"], v=22, cars=5, head=240, term=True),
        dict(name="S-Bahn Wiedikon", groups=[south, wied, hb_end(net, "9")], stops=["Zürich Wiedikon"], v=20, cars=5, head=270, term=True),
        dict(name="IC Gl. 16", groups=[west, hb_end(net, "16")], stops=[], v=33, cars=6, head=900, term=True),
        dict(name="IC Gl. 17", groups=[west, hb_end(net, "17")], stops=[], v=33, cars=6, head=1020, term=True),
        dict(name="IR Gl. 18", groups=[west, hb_end(net, "18")], stops=[], v=30, cars=6, head=1200, term=True),
    ]
    out = []
    for sp in specs:
        if not all(sp["groups"]):
            print("missing group", sp["name"])
            continue
        term = sp.get("term")
        g = Gic if term else G
        for d in (0, 1):
            gs = sp["groups"] if d == 0 else sp["groups"][::-1]
            names = sp["stops"] if d == 0 else sp["stops"][::-1]
            r = chain_route(g, gs)
            if r is None:
                print("no route", sp["name"], d)
                continue
            edges, stop_at = r
            rt, cum = finish(g, net, sp, d, edges, stop_at, names)
            if term:
                vlen = sp["cars"] * 26.4
                if d == 0:
                    rt.update(te=1, stops=rt["stops"] + [{"name": "Zürich HB", "s": round(float(cum[-1]) - 6 - vlen / 2, 1)}])
                else:
                    rt.update(ts=1, stops=[{"name": "Zürich HB", "s": round(6 + vlen / 2, 1)}] + rt["stops"])
            out.append(rt)
            tags = {}
            for wi in rt["ways"]:
                t = net.ways[wi]["tags"]
                k = (t.get("service"), t.get("usage"), t.get("tunnel") or t.get("bridge"))
                tags[k] = tags.get(k, 0) + 1
            print(sp["name"], d, "len", round(cum[-1]), "stops", rt["stops"], "ways", tags)
    return out
