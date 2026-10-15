"""Bridges and elevated roads/paths from OSM (bridge=yes/viaduct ...) with a real height profile.

bridge_ways(nodes, els, area, H=None) -> list of bridge dicts
tile_rows(bridges, tile_box)          -> {"decks", "piers", ["excl"]} for one tile (meta field "bridges")
exclusion(bridges)                    -> shapely geometry: ground area that must NOT be drawn as street
clip_ways(ways, excl)                 -> streets.parse() way dicts without the part covered by a deck

Profile: the deck must clear every crossed obstacle (rail 7 m for road decks, road 5 m, water 3.5 m ...);
the lowest deck that does so is the slope-limited envelope (road 6 %) of those requirements, capped by the
ground height at both chain ends. Ends are extended along the continuing non-bridge ways (OSM ramps), so the
deck meets the ground there. See research/bridges.md.
"""
import math
from collections import defaultdict

import numpy as np
import shapely
from shapely.geometry import LineString, Point, box
from shapely.strtree import STRtree

ROAD = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link",
        "tertiary", "tertiary_link", "residential", "unclassified", "living_street", "service"}
FOOT = {"footway", "path", "cycleway", "pedestrian", "track"}
WIDTH = {"motorway": 11, "motorway_link": 5.5, "trunk": 10, "trunk_link": 5.5, "primary": 13, "primary_link": 7,
         "secondary": 11, "secondary_link": 7, "tertiary": 9, "tertiary_link": 6, "residential": 7,
         "unclassified": 6, "living_street": 6, "service": 3.5, "footway": 3.0, "path": 2.5, "cycleway": 3.0,
         "pedestrian": 6.0, "track": 3.5, "tram": 3.4, "rail": 4.6}
SLOPE = {"road": 0.06, "foot": 0.08, "tram": 0.07, "rail": 0.15}
# clearance (m) a deck of kind K needs above an obstacle of kind O
CLEAR = {"road": {"rail": 7.0, "tram": 6.0, "road": 5.0, "foot": 3.2, "water": 3.5},
         "foot": {"rail": 6.5, "tram": 5.8, "road": 5.0, "foot": 3.0, "water": 3.0},
         "tram": {"rail": 6.5, "tram": 5.8, "road": 5.2, "foot": 3.2, "water": 3.5},
         "rail": {"rail": 6.5, "tram": 5.8, "road": 5.5, "foot": 3.2, "water": 3.5}}
SLAB = {"road": 1.0, "foot": 0.6, "tram": 0.9, "rail": 1.1}
STEP = 6.0  # densify spacing (m)
EXT_MAX = 260.0  # max ramp extension per chain end (m)


def _kind(t):
    hw = t.get("highway")
    if hw in ROAD:
        return "road"
    if hw in FOOT:
        return "foot"
    r = t.get("railway")
    if r in ("tram", "light_rail"):
        return "tram"
    if r in ("rail", "narrow_gauge", "subway"):
        return "rail"
    return None


def _num(v, d):
    try:
        return float(str(v).split()[0].replace(",", "."))
    except (TypeError, ValueError, IndexError):
        return d


def _layer(t, bridge):
    try:
        return int(float(t.get("layer", 1 if bridge else 0)))
    except ValueError:
        return 1 if bridge else 0


def _is_bridge(t):
    return t.get("bridge") not in (None, "no") and t.get("building") is None and t.get("man_made") != "bridge"


def _width(t, kind):
    key = t.get("highway") or t.get("railway")
    w = _num(t.get("width"), 0) or (_num(t.get("lanes"), 0) * 3.2 if kind == "road" else 0) or WIDTH.get(key, 4.0)
    return max(w, 1.5)


def _resample(pts, core):
    """Densify polyline pts to <= STEP spacing; core[i] flags segment i->i+1 as bridge. Returns arrays."""
    P, C = [pts[0]], [core[0] if core else True]
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        n = max(1, int(math.ceil(np.linalg.norm(b - a) / STEP)))
        for k in range(1, n + 1):
            P.append(tuple(a + (b - a) * k / n))
            C.append(core[i])
    return np.array(P), np.array(C, bool)


def bridge_ways(nodes, els, area, H=None):
    if H is None:
        from terrain import heights
        H = heights(tuple(area), 2.0, z_shift=-3.06)
    ab = box(*area).buffer(60)
    ways = []  # eligible ways + obstacles
    water_lines, water_polys = [], []
    for e in els:
        if e["type"] != "way" or len(e.get("nodes", [])) < 2:
            continue
        t = e.get("tags", {})
        pts = [nodes[n] for n in e["nodes"] if n in nodes]
        if len(pts) < 2:
            continue
        if t.get("waterway") in ("river", "canal", "stream") and not _is_bridge(t) and t.get("tunnel") not in ("yes", "culvert"):
            ln = LineString(pts)
            if ln.intersects(ab):
                water_lines.append(ln.buffer(3.0 if t["waterway"] == "stream" else 8.0))
            continue
        if t.get("natural") == "water" and pts[0] == pts[-1] and len(pts) >= 4:
            water_polys.append(shapely.Polygon(pts).buffer(0))
            continue
        k = _kind(t)
        if k is None or t.get("area") == "yes" or t.get("highway") == "steps" or t.get("service") in ("driveway",) and False:
            continue
        tunnel = t.get("tunnel") in ("yes", "building_passage", "culvert") or _layer(t, False) < 0
        line = LineString(pts)
        if tunnel or not line.intersects(ab):
            continue
        br = _is_bridge(t)
        ways.append({"id": e["id"], "nodes": [n for n in e["nodes"] if n in nodes], "pts": pts, "line": line, "kind": k,
                     "bridge": br, "layer": _layer(t, br), "w": _width(t, k), "name": t.get("name", ""),
                     "clear": _num(t.get("clearance") or t.get("bridge:clearance") or t.get("height"), 0)})
    seeds = [w for w in ways if w["bridge"]]
    if not seeds:
        return []
    by_node = defaultdict(list)
    for w in ways:
        for n in (w["nodes"][0], w["nodes"][-1]):
            by_node[n].append(w)
    interior = defaultdict(int)
    for w in ways:
        for n in w["nodes"][1:-1]:
            interior[n] += 1
    obst_geoms = water_lines + water_polys
    obst_kind = ["water"] * len(obst_geoms)
    obst_layer = [-1] * len(obst_geoms)
    obst_nodes = [set()] * len(obst_geoms)
    obst_id = [None] * len(obst_geoms)
    for w in ways:
        obst_geoms.append(w["line"].buffer(w["w"] / 2 + 0.3, cap_style="flat"))
        obst_kind.append(w["kind"])
        obst_layer.append(w["layer"])
        obst_nodes.append(set(w["nodes"]))
        obst_id.append(w["id"])
    tree = STRtree(obst_geoms)

    # --- build chains: merge connected bridge ways, extend over non-bridge continuation ways -------------------------
    used, chains = set(), []
    for s in seeds:
        if s["id"] in used:
            continue
        used.add(s["id"])
        seq = [(s, list(s["nodes"]), True)]  # (way, node order, is_bridge)

        def grow(end):  # end = "tail" or "head"
            budget = EXT_MAX
            while True:
                w, nd, _ = seq[-1] if end == "tail" else seq[0]
                n = nd[-1] if end == "tail" else nd[0]
                if interior[n]:
                    return
                cand = [c for c in by_node[n] if c["id"] != w["id"] and c["kind"] == s["kind"]]
                if len(by_node[n]) != 2 or len(cand) != 1 or cand[0]["id"] in used:
                    return
                c = cand[0]
                if not c["bridge"] and budget <= 0:
                    return
                order = list(c["nodes"]) if end == "tail" and c["nodes"][0] == n else \
                    list(reversed(c["nodes"])) if end == "tail" else \
                    list(c["nodes"]) if c["nodes"][-1] == n else list(reversed(c["nodes"]))
                used.add(c["id"]) if c["bridge"] else None
                if not c["bridge"]:
                    budget -= c["line"].length
                (seq.append if end == "tail" else lambda x: seq.insert(0, x))((c, order, c["bridge"]))
                if not c["bridge"] and budget <= 0:
                    return

        grow("tail")
        grow("head")
        chains.append(seq)
    ext_ids = {w["id"] for seq in chains for w, _, b in seq if not b}

    prep, out = [], []
    for seq in chains:
        # polyline from sequence
        pts, core, nid = [], [], []
        for w, order, br in seq:
            p = [nodes[n] for n in order]
            if pts and tuple(pts[-1]) == tuple(p[0]):
                p, order = p[1:], order[1:]
                core_seg = [br] * len(p)
            else:
                core_seg = [br] * max(0, len(p) - 1) + [br]
                if pts:  # gap (should not happen)
                    pts.append(p[0]); core.append(br); nid.append(order[0]); p, order = p[1:], order[1:]; core_seg = [br] * len(p)
            for q, n, c in zip(p, order, core_seg):
                pts.append(q); nid.append(n); core.append(c)
        if len(pts) < 2:
            continue
        # segment core flag: segment i is core if vertex i+1 is core (vertex flags above are per arriving vertex)
        segcore = [core[i + 1] for i in range(len(pts) - 1)]
        core_ways = [w for w, _, b in seq if b]
        kind = core_ways[0]["kind"]
        layer = max(w["layer"] for w in core_ways)
        wd = float(np.mean([w["w"] for w in core_ways]))
        name = next((w["name"] for w in core_ways if w["name"]), "")
        tag_clear = max(w["clear"] for w in core_ways)
        P, C = _resample(pts, segcore)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        L = s[-1]
        g = np.array([float(H.at(x, y)) for x, y in P])
        chain_nodes = set(nid)
        # obstacle requirements along the core
        req = np.full(len(P), -np.inf)
        crossed = False
        for i in range(len(P)):
            if not C[i] and not (i > 0 and C[i - 1]):
                continue
            pt = Point(P[i])
            for j in tree.query(pt.buffer(0.1)):
                if obst_layer[j] >= layer or (obst_nodes[j] & chain_nodes) or obst_id[j] in ext_ids:
                    continue
                if obst_geoms[j].distance(pt) > 1.2 and not obst_geoms[j].contains(pt):
                    continue
                c = tag_clear or CLEAR[kind][obst_kind[j]]
                req[i] = max(req[i], g[i] + c)
                crossed = True
        if not crossed:
            continue
        prep.append(dict(P=P, C=C, s=s, g=g, req=req, kind=kind, layer=layer, wd=wd, name=name, seq=seq,
                         chain_nodes=chain_nodes, nid=nid))

    # joints: chain ends touching another bridge chain are free (not forced to the ground) and share their height
    bridge_nodes = defaultdict(int)
    for ch in prep:
        for n in {ch["nid"][0], ch["nid"][-1]}:
            bridge_nodes[n] += 1
    node_z = {}
    for it in range(4):
        new_z = {}
        for ch in prep:
            req = ch["req"].copy()
            free = []
            for k, n in ((0, ch["nid"][0]), (-1, ch["nid"][-1])):
                if bridge_nodes[n] > 1:
                    free.append(k)
                    if n in node_z:
                        req[k] = max(req[k], node_z[n])
            sl = SLOPE[ch["kind"]]
            for mult in (1.0, 1.5, 2.0):
                z = _envelope(ch["s"], req, ch["g"], sl * mult, free)
                ok = np.all(z[np.isfinite(req)] >= req[np.isfinite(req)] - 0.4)
                if ok:
                    break
            ch["z"] = z
            for k in free:
                n = ch["nid"][k]
                new_z[n] = max(new_z.get(n, -1e9), float(ch["z"][k]))
        node_z = new_z

    out = []
    for ch in prep:
        P, C, s, g, kind, layer, wd, name, seq, chain_nodes, z = (ch[k] for k in (
            "P", "C", "s", "g", "kind", "layer", "wd", "name", "seq", "chain_nodes", "z"))
        # trim flat ends
        el = z - g
        idx = np.where(el > 0.12)[0]
        if not len(idx) or el.max() < 1.2:
            continue
        a, b = max(0, idx[0] - 1), min(len(P) - 1, idx[-1] + 1)
        if s[b] - s[a] < 6:
            continue
        P, z, g, C, s = P[a:b + 1], z[a:b + 1], g[a:b + 1], C[a:b + 1], s[a:b + 1]
        el = z - g
        # obstacle proximity per vertex -> slab (below obstacle) or solid skirt to ground (embankment)
        near = np.zeros(len(P), bool)
        for i in range(len(P)):
            pt = Point(P[i])
            for j in tree.query(pt.buffer(wd / 2 + 1.5)):
                if obst_layer[j] < layer and not (obst_nodes[j] & chain_nodes) and obst_id[j] not in ext_ids \
                        and obst_geoms[j].distance(pt) < wd / 2 + 1.0:
                    near[i] = True
                    break
        slab = SLAB[kind]
        bot = np.where((el < 3.5) & ~near, g - 0.25, z - slab)
        bot = np.minimum(bot, z - 0.4)
        # piers
        piers = []
        gap = 22.0 if kind in ("road", "rail") else 16.0
        pos = gap / 2
        while pos < s[-1] - gap / 3:
            for off in (0, 3, -3, 6, -6, 9, -9):
                sp = pos + off
                if sp < 0 or sp > s[-1]:
                    continue
                x, y = np.interp(sp, s, P[:, 0]), np.interp(sp, s, P[:, 1])
                zd, gz = np.interp(sp, s, z), float(H.at(x, y))
                if zd - gz < 2.2:
                    break
                hit = any(obst_layer[j] < layer and not (obst_nodes[j] & chain_nodes) and obst_id[j] not in ext_ids
                          and obst_geoms[j].intersects(Point(x, y).buffer(wd * 0.35))
                          for j in tree.query(Point(x, y).buffer(wd * 0.35 + 1)))
                if hit:
                    continue
                k = min(int(np.searchsorted(s, sp)), len(P) - 1)
                d = P[k] - P[max(k - 1, 0)]
                hd = math.atan2(d[1], d[0])
                piers.append([round(float(x), 2), round(float(y), 2), round(gz - 0.3, 2), round(float(zd - slab), 2),
                              round(float(wd * 0.55 if kind != "foot" else 0.9), 2), round(hd, 3)])
                break
            pos += gap
        # exclusion footprint: elevated parts minus ground ways beneath
        segs = [LineString(P[i:i + 2]).buffer(wd / 2 + 0.5, cap_style="flat")
                for i in range(len(P) - 1) if min(el[i], el[i + 1]) > 0.3]
        excl = shapely.union_all(segs) if segs else shapely.Polygon()
        out.append({"ids": [w["id"] for w, _, _ in seq], "name": name, "kind": kind, "layer": layer, "w": round(wd, 2),
                    "p": np.column_stack([P, z]).round(2).tolist(), "g": g.round(2).tolist(), "b": bot.round(2).tolist(),
                    "piers": piers, "excl": excl, "max_el": float(el.max()), "max_slope": _maxslope(s, z),
                    "len": float(s[-1])})
    # ground ways beneath must stay drawn: subtract them from the exclusion
    for b in out:
        if b["excl"].is_empty:
            continue
        under = []
        mine = set(b["ids"])
        for j in tree.query(b["excl"]):
            if obst_id[j] is not None and obst_id[j] not in ext_ids and obst_id[j] not in mine and obst_layer[j] < b["layer"]:
                under.append(obst_geoms[j])
        if under:
            b["excl"] = b["excl"].difference(shapely.union_all(under))
    return out


def _envelope(s, req, g, sl, free=()):
    """Lowest slope-limited profile above the requirements, forced down to the ground at both ends."""
    n = len(s)
    z = np.where(np.isfinite(req), req, -1e9)
    for i in range(1, n):
        z[i] = max(z[i], z[i - 1] - sl * (s[i] - s[i - 1]))
    for i in range(n - 2, -1, -1):
        z[i] = max(z[i], z[i + 1] - sl * (s[i + 1] - s[i]))
    cap = np.full(n, 1e9)
    if 0 not in free:
        cap = np.minimum(cap, g[0] + sl * (s - s[0]))
    if -1 not in free:
        cap = np.minimum(cap, g[-1] + sl * (s[-1] - s))
    z = np.minimum(z, cap)
    f = g.astype(float).copy()  # floor: highest slope-limited profile below the terrain (no steep following of banks)
    for i in range(1, n):
        f[i] = min(f[i], f[i - 1] + sl * (s[i] - s[i - 1]))
    for i in range(n - 2, -1, -1):
        f[i] = min(f[i], f[i + 1] + sl * (s[i + 1] - s[i]))
    return np.maximum(np.where(z < -1e8, g, z), f)


def _maxslope(s, z):
    d = np.diff(s)
    return float(np.max(np.abs(np.diff(z)) / np.maximum(d, 0.01))) if len(d) else 0.0


def exclusion(bridges):
    return shapely.union_all([b["excl"] for b in bridges]) if bridges else shapely.Polygon()


def clip_ways(ways, excl):
    """streets.parse() way dicts: cut away the parts under a deck (markings, curbs then follow automatically)."""
    if excl.is_empty:
        return ways
    out = []
    for w in ways:
        if not w["line"].intersects(excl):
            out.append(w)
            continue
        rest = w["line"].difference(excl)
        for part in getattr(rest, "geoms", [rest]):
            if part.geom_type == "LineString" and part.length > 1.0:
                out.append({**w, "line": part})
    return out


def tile_rows(bridges, tile_box, with_excl=False):
    tb = box(*tile_box) if not hasattr(tile_box, "bounds") else tile_box
    x0, y0, x1, y1 = tb.bounds
    decks, piers, excl = [], [], []
    for b in bridges:
        p = b["p"]
        runs, cur = [], []
        for i in range(len(p) - 1):
            mx, my = (p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2
            if x0 <= mx < x1 and y0 <= my < y1:
                if not cur:
                    cur = [i]
                cur.append(i + 1)
            elif cur:
                runs.append(cur); cur = []
        if cur:
            runs.append(cur)
        for r in runs:
            decks.append({"p": [p[i] for i in r], "g": [b["g"][i] for i in r], "b": [b["b"][i] for i in r],
                          "w": b["w"], "kind": b["kind"], "name": b["name"]})
        piers += [q + [b["kind"]] for q in b["piers"] if x0 <= q[0] < x1 and y0 <= q[1] < y1]
        if with_excl and not b["excl"].is_empty:
            part = b["excl"].intersection(tb)
            for g in getattr(part, "geoms", [part]):
                if g.geom_type == "Polygon" and not g.is_empty:
                    excl.append([[round(x, 2), round(y, 2)] for x, y in g.exterior.coords])
    r = {"decks": decks, "piers": piers}
    if with_excl:
        r["excl"] = excl
    return r


if __name__ == "__main__":
    import sys
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    import sources
    from config import AREA
    nodes, els = sources.osm()
    BR = bridge_ways(nodes, els, AREA)
    print(f"{len(BR)} bridges, {sum(len(b['piers']) for b in BR)} piers, "
          f"max deck elevation {max(b['max_el'] for b in BR):.1f} m, max slope {max(b['max_slope'] for b in BR) * 100:.1f} %")
    for b in sorted(BR, key=lambda b: -b["max_el"])[:40]:
        print(f"  {b['kind']:5} {b['name'][:28]:28} len {b['len']:6.0f} w {b['w']:4.1f} lay {b['layer']} "
              f"el {b['max_el']:4.1f} slope {b['max_slope'] * 100:4.1f}% piers {len(b['piers'])}")
