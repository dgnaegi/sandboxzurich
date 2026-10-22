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
import json
import os
import math
from collections import defaultdict
from pathlib import Path

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


CHAINS_CACHE = Path(__file__).resolve().parent.parent / "data" / "build" / "deck_chains.json"


def save_chains(out):
    """Deck chains of the real build (terrain smoothed by road_height) for decktrack.DeckTrack: vehicles, trams and the player
    then share exactly the deck heights of the tile meshes (callers without H compute on the raw terrain, up to ~1 m off)."""
    CHAINS_CACHE.write_text(json.dumps([{k: b[k] for k in ("ids", "kind", "w", "p", "name")} for b in out]))


def load_chains():
    return json.loads(CHAINS_CACHE.read_text()) if CHAINS_CACHE.exists() else None


def _load_excl():  # bridges_excl
    ids = set()
    for fn in ("lochergut_excl.json", "bridges_excl.json"):
        p = Path(__file__).resolve().parent / "overrides" / fn
        if p.exists():
            ids |= {int(i) for i in json.loads(p.read_text()).get("bridge_way_ids", [])}
    return ids


_BRIDGES_EXCL = _load_excl()  # bridges_excl


def _roof():
    import terrain_cuts
    h = terrain_cuts.holes()
    return shapely.buffer(h, 1.5) if h is not None else None


_ROOF = _roof()


LIDAR_DECKS = "" if os.environ.get("SBZ_LIDAR_DECKS") == "0" else os.environ.get("SBZ_LIDAR_DECKS", "1")  # default on, "0" off; "1": measured LiDAR deck heights (road/tram/foot) replace the rule-based z; "rail": rails too
LIDAR_MAXOFF = 4.0   # m: measured - rule offsets beyond this are layer confusions (road above / below), not corrections
LIDAR_JOIN = 1.5     # m: chain ends closer than this share one height


def _lidar_decks(prep, bridge_nodes):
    """Phase B (research/lidar): z of each chain = LiDAR deck surface (class 17 top, ground where at grade; lidar_deck.deck_profile).
    Applied as an offset field on the rule-based z so unmeasured stretches keep the rule shape: offset is interpolated between
    measured vertices (held constant beyond the last one, faded out to 0 at the chain end if that end is at grade). z never goes
    below the ground g. Chain ends that meet another chain are then averaged."""
    try:
        import lidar_deck
        if not lidar_deck.lidar.GRID.exists():
            return
    except Exception as e:  # no LiDAR cache (CI / fresh checkout): keep the rule-based decks
        print("bridges: lidar decks skipped:", e)
        return
    n_ok = n_ch = 0
    for ch in prep:
        if ch["kind"] == "rail" and LIDAR_DECKS != "rail":
            continue
        P, z, g, s = ch["P"], ch["z"], ch["g"], ch["s"]
        prof = lidar_deck.deck_profile({"p": np.column_stack([P, z]), "w": ch["wd"]})
        m = prof["z"]
        ok = np.isfinite(m) & (np.abs(m - z) <= LIDAR_MAXOFF)
        if ok.sum() < max(3, 0.3 * len(z)):
            continue
        off = np.interp(s, s[ok], (m - z)[ok])   # constant beyond the first / last measured vertex
        # a rule-deck end that is at grade (z ~ g) stays at grade: fade the offset out over 25 m towards that end. A LiDAR bridge
        # surface (src 1) measured well above the terrain at that end means the rule end is wrong (terrain carved below a deck that
        # really continues): no fade there. Measured vertices are never faded towards the (wrong) rule z: they blend to the ground.
        fade = np.ones(len(z))
        for end in (0, -1):
            if z[end] - g[end] < 0.3 and not (prof["src"][end] == 1 and ok[end] and m[end] - g[end] > 0.8):
                fade = np.minimum(fade, np.clip(np.abs(s - s[end]) / 25.0, 0, 1))
        zn = np.maximum(z + off * fade, g)
        meas = np.where(ok & (fade < 1.0))[0]
        if len(meas):   # at-grade end: measured deck/street surface, lowered towards the ground only by the (<= 0.5 m) gap to it
            f8 = np.clip(fade[meas] * 25.0 / 10.0, 0, 1)   # reaches the full measured height 10 m from the end
            zn[meas] = np.maximum(m[meas] - (1 - f8) * np.clip(m[meas] - g[meas], 0, 0.5), g[meas])
            gap = np.where((fade < 1.0) & ~ok)[0]
            if len(gap) and len(meas) >= 2:
                zn[gap] = np.maximum(np.interp(s[gap], s[meas], zn[meas]), g[gap])
        ch["z"] = zn
        n_ok += 1
        n_ch += int(ok.sum())
    # joints: ends meeting another chain share one height
    ends = [(i, k, ch["P"][k]) for i, ch in enumerate(prep) for k in (0, -1)]
    for a in range(len(ends)):
        for b in range(a + 1, len(ends)):
            (i, k, p), (j, l, q) = ends[a], ends[b]
            if i != j and np.hypot(*(p - q)) < LIDAR_JOIN and (prep[i]["z"] is not prep[j]["z"]):
                zm = 0.5 * (prep[i]["z"][k] + prep[j]["z"][l])
                if abs(prep[i]["z"][k] - prep[j]["z"][l]) < 2.0:
                    for c, kk in ((i, k), (j, l)):
                        zz = prep[c]["z"].copy(); old = zz[kk]; zz[kk] = zm
                        nb = 1 if kk == 0 else len(zz) - 2
                        zz[nb] += 0.5 * (zm - old)
                        prep[c]["z"] = zz
    print(f"bridges: LiDAR decks applied to {n_ok} chains ({n_ch} measured vertices)")


FOLLOW_DIST = 4.6   # m: a tram/foot strip this close and parallel to a road chain is on the same structure (ramp)
FOLLOW_DIST_FOOT = 3.0  # m: footways must hug the road (a footway 4 m away may run on the ground below a bridge, e.g. Europabruecke)
FOLLOW_DZ = 1.5     # m: ... and takes its height when the rule/LiDAR height disagrees by more than this
FOLLOW_FADE = 25.0  # m: height offset above ground carried past the last followed vertex fades out over this length


def _follow_parallel(prep):
    """Tram/foot chains that run parallel (<= FOLLOW_DIST, angle < 25 deg) beside a road chain share its structure and height.
    Without this a tram next to the Pfingstweidstrasse ramp (Hardbruecke) took the LiDAR height of the main deck passing above the
    ramp (7 m too high) and dived 28 % down onto the ramp: grey wedge slab, kinked ramp. Past the last followed vertex the offset above
    ground fades out."""
    from shapely.geometry import LineString as LS, Point as Pt
    roads = [(c, LS(c["P"])) for c in prep if c["kind"] == "road"]
    n_fix = 0
    for ch in prep:
        if ch["kind"] not in ("tram", "foot"):
            continue
        P, z, g, s = ch["P"], ch["z"].copy(), ch["g"], ch["s"]
        fol = np.zeros(len(P), bool)
        for i in range(len(P)):
            pt = Pt(P[i])
            d = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
            best = None   # nearest parallel road chain wins (a tram crossing a main deck at a shallow angle belongs to the ramp beside it)
            for c, ln in roads:
                dist = ln.distance(pt)
                if c is ch or dist > (FOLLOW_DIST if ch["kind"] == "tram" else FOLLOW_DIST_FOOT) or (best and dist >= best[0]):
                    continue
                t = ln.project(pt)
                a, b = ln.interpolate(max(t - 2, 0)), ln.interpolate(min(t + 2, ln.length))
                e = np.array([b.x - a.x, b.y - a.y])
                if abs(float(d @ e)) / (np.hypot(*d) * np.hypot(*e) + 1e-9) < 0.906:
                    continue
                best = (dist, float(np.interp(t, c["s"], c["z"])))
            if best and abs(best[1] - z[i]) > FOLLOW_DZ:
                z[i] = best[1]
                fol[i] = True
        if not fol.any():
            continue
        idx = np.where(fol)[0]
        # carry the above-ground offset of the nearest followed vertex over the unfollowed rest, faded out
        for i in range(len(P)):
            if fol[i]:
                continue
            j = idx[np.argmin(np.abs(s[idx] - s[i]))]
            if abs(z[i] - ch["z"][i]) < 1e-9 and np.abs(s[idx] - s[i]).min() < 1e9:
                dist = abs(s[j] - s[i])
                off = z[j] - g[j]
                z[i] = g[i] + off * max(0.0, 1 - dist / FOLLOW_FADE) if abs(ch["z"][i] - z[j]) > FOLLOW_DZ else ch["z"][i]
        ch["z"] = np.maximum(z, g)
        n_fix += 1
    if n_fix:
        print(f"bridges: {n_fix} tram/foot chains follow a parallel road ramp")


def bridge_ways(nodes, els, area, H=None, H_raw=None):
    H_given = H is not None
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
        if e["id"] in _BRIDGES_EXCL:  # bridges_excl
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
        if H_raw is not None:  # roads2: a trench (rail cutting) the smoothing partly filled is still the real ground below the deck: clearance counts from it
            gr = np.array([float(H_raw.at(x, y)) for x, y in P])
            g = np.where(g - gr > 1.0, gr, g)
        if _ROOF is not None:  # covered underpass (terrain_cuts "hole"): the lowered floor is not the ground under a deck above it, the roof is: interpolate from outside
            inside = shapely.contains_xy(_ROOF, P[:, 0], P[:, 1])
            if inside.any() and not inside.all():
                g = np.where(inside, np.interp(s, s[~inside], g[~inside]), g)
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
                z = _envelope(ch["s"], _fair(ch["s"], z, req), ch["g"], sl * mult, free)  # no roller-coaster between obstacles
                ok = np.all(z[np.isfinite(req)] >= req[np.isfinite(req)] - 0.4)
                if ok:
                    break
            ch["z"] = z
            for k in free:
                n = ch["nid"][k]
                new_z[n] = max(new_z.get(n, -1e9), float(ch["z"][k]))
        node_z = new_z

    if LIDAR_DECKS:
        _lidar_decks(prep, bridge_nodes)
    _follow_parallel(prep)

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
    _snap_foot(out)
    _open_sides(out)
    out = _trim_tram(out)
    for b in out:   # open sides again on the trimmed set: a road deck must not stay open towards a dropped tram strip (car fell into the Sihl at Gessnerbrücke)
        b.pop("ol", None); b.pop("or", None)
    _open_sides(out)
    _zebras(out, nodes, els)
    if H_given and H_raw is not None:  # roads2: only the real build (it passes the unsmoothed grid) writes the chain cache; audits do not
        save_chains(out)
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


def _zebras(out, nodes, els):
    """Mapped pedestrian crossings (OSM highway=crossing nodes) on a road deck -> b["zb"] = [x, y, z, dirX, dirY] (drawn yellow by web/src/world/bridges.ts).
    Only on the elevated part (>= 1 m above terrain); ground rails/markings are cut under the deck by the exclusion."""
    cr = [(nodes[e["id"]], e) for e in els if e["type"] == "node" and e.get("tags", {}).get("highway") == "crossing"
          and e["tags"].get("crossing") != "no" and e["id"] in nodes]
    for b in out:
        b["zb"] = []
        if b["kind"] != "road" or not cr:
            continue
        P = np.array(b["p"])
        ln = LineString(P[:, :2])
        for (x, y), _ in cr:
            pt = shapely.geometry.Point(x, y)
            if ln.distance(pt) > 2.5:
                continue
            s = ln.project(pt)
            q = ln.interpolate(s); q2 = ln.interpolate(min(s + 0.5, ln.length)); q0 = ln.interpolate(max(s - 0.5, 0))
            d = np.array([q2.x - q0.x, q2.y - q0.y]); n = np.hypot(*d)
            if n < 1e-6:
                continue
            cum = np.r_[0, np.cumsum(np.hypot(*np.diff(P[:, :2], axis=0).T))]
            z = float(np.interp(s, cum, P[:, 2])); g = float(np.interp(s, cum, b["g"]))
            if z - g >= 1.0:
                b["zb"].append([round(q.x, 2), round(q.y, 2), round(z, 2), round(d[0] / n, 3), round(d[1] / n, 3)])


FAIR_FILL = 35.0   # m: dips shorter than 2x this between higher parts of the deck are filled (a driveable, flat-topped deck)
FAIR_SMOOTH = 12.0  # m: vertical-curve rounding of the filled profile


def _fair(s, z, req):
    """Fill dips (dilation) and round the kinks (moving average) of the lowest feasible profile z; never below z or req."""
    from numpy.lib.stride_tricks import sliding_window_view as win
    grid = np.arange(s[0], s[-1] + 1e-6, 3.0)
    if len(grid) < 4:
        return z
    zg = np.interp(grid, s, z)
    k = int(FAIR_FILL / 3)
    dil = win(np.pad(zg, k, mode="edge"), 2 * k + 1).max(axis=1)
    k2 = int(FAIR_SMOOTH / 3)
    sm = win(np.pad(dil, k2, mode="edge"), 2 * k2 + 1).mean(axis=1)
    out = np.maximum(np.interp(s, grid, sm), z)
    return np.where(np.isfinite(req), np.maximum(out, req), out)


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


def _snap_foot(out):
    """Footways running alongside a road deck take the road deck's height (walking sideways off the carriageway must not step).
    Snap fully within the common width + 2.5 m, fade out over 5 m more; crossings at another level (|dz| >= 1.5 m) stay."""
    roads = [b for b in out if b["kind"] in ("road", "tram")]
    if not roads:
        return
    lines, cums = [], []
    for b in roads:
        P = np.array(b["p"])
        lines.append(LineString(P[:, :2]))
        cums.append((np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P[:, :2], axis=0).T))]), P[:, 2]))
    tree = STRtree(lines)
    for f in out:
        if f["kind"] != "foot":
            continue
        for i, (x, y, z) in enumerate(f["p"]):
            pt, best = Point(x, y), None
            for j in tree.query(pt.buffer(14)):
                d = lines[j].distance(pt)
                lim = roads[j]["w"] / 2 + f["w"] / 2 + 2.5
                if d < lim + 5 and (best is None or d < best[0]):
                    sj = lines[j].project(pt)
                    best = (d, lim, float(np.interp(sj, cums[j][0], cums[j][1])))
            if best and abs(best[2] - z) < 1.5:
                w = 1.0 if best[0] <= best[1] else 1 - (best[0] - best[1]) / 5
                nz = z + (best[2] - z) * w
                f["b"][i] = round(f["b"][i] + nz - z, 2)
                f["p"][i][2] = round(nz, 2)


def _side_by_side(a, A, i, nrm, d, cand, lines, Ps, la, max_dz, max_gap, only=None):
    """Other road/tram decks lying side by side with vertex i of deck a (near-parallel, gap <= max_gap, |dz| < max_dz):
    list of (side, zOther, roadKind); side = +1 left of travel, -1 right, 0 = on top of each other."""
    res = []
    pt = Point(*A[i, :2])
    for k, bb in enumerate(cand):
        if bb is a or (only and bb["kind"] != only):
            continue
        lk = lines[k]
        if lk.distance(pt) >= a["w"] / 2 + bb["w"] / 2 + max_gap + 0.3:
            continue
        B = Ps[k]
        sj = lk.project(pt)
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(B[:, :2], axis=0).T))])
        if sj <= 0.01 or sj >= cum[-1] - 0.01:
            continue   # beyond the other deck's ends
        zb = float(np.interp(sj, cum, B[:, 2]))
        if abs(zb - A[i, 2]) >= max_dz:
            continue
        q = lk.interpolate(sj)
        v = np.array([q.x - A[i, 0], q.y - A[i, 1]])
        dist = float(np.hypot(*v))
        if dist - a["w"] / 2 - bb["w"] / 2 > max_gap:
            continue
        m = min(int(np.searchsorted(cum, sj)), len(B) - 1)
        t = B[m] - B[max(m - 1, 0)]
        tl = float(np.hypot(*t[:2])) or 1.0
        if abs(float(np.dot(t[:2] / tl, d))) < 0.9:   # a deck crossing at an angle is not side by side
            continue
        res.append((0 if dist < 0.3 else (1 if float(np.dot(v, nrm)) > 0 else -1), zb))
    return res


def _open_sides(out, max_dz=0.5, max_gap=1.5, snap_dz=1.5):
    """Decks lying side by side form ONE deck (tram inside / next to a road deck, split carriageways).
    1. A tram deck within a road deck's width (or <= max_gap beside it) takes the road deck's height (|dz| < snap_dz; every chain
       is height-fitted on its own, so the tram strip would otherwise sit up to 1 m beside the carriageway).
    2. Per vertex, b["ol"][i] / b["or"][i] = 1 when another road/tram deck at the same height (|dz| < max_dz) touches that
       side (left / right of travel, gap <= max_gap). web/src/world/bridges.ts draws no curb / parapet / railing there."""
    cand = [b for b in out if b["kind"] in ("road", "tram")]
    if len(cand) < 2:
        return
    Ps = [np.array(b["p"]) for b in cand]
    lines = [LineString(P[:, :2]) for P in Ps]
    for snap in (True, False):
        for a, A, la in zip(cand, Ps, lines):
            if snap and a["kind"] != "tram":
                continue
            n = len(A)
            ol, orr = [0] * n, [0] * n
            for i in range(n):
                j0, j1 = max(i - 1, 0), min(i + 1, n - 1)
                d = (A[j1, :2] - A[j0, :2]); L = float(np.hypot(*d)) or 1.0; d = d / L
                nrm = np.array([-d[1], d[0]])
                if snap:
                    hits = _side_by_side(a, A, i, nrm, d, cand, lines, Ps, la, snap_dz, max_gap, only="road")
                    if hits:
                        z0 = A[i, 2]; A[i, 2] = hits[0][1]
                        a["b"][i] = round(a["b"][i] + A[i, 2] - z0, 2)
                        a["p"][i][2] = round(float(A[i, 2]), 2)
                    continue
                for side, _ in _side_by_side(a, A, i, nrm, d, cand, lines, Ps, la, max_dz, max_gap):
                    if side >= 0:
                        ol[i] = 1
                    if side <= 0:
                        orr[i] = 1
            if not snap and (any(ol) or any(orr)):
                a["ol"], a["or"] = ol, orr


def _trim_tram(out, el_min=2.5, near=0.5):
    """Trams run on the normal street (User 2026-10-21): a tram deck part stays only next to a road deck at the same height
    (after _open_sides it took the road deck's height) or where it is really elevated (a ramp group whose peak is >= el_min above
    the ground: water/rail/road below). Ramps alongside at-grade streets are dropped, the tram then follows the terrain
    (decktrack/transit fall back to the ground height there). Chains are split at the dropped parts."""
    roads = [b for b in out if b["kind"] == "road"]
    rl = [LineString(np.array(b["p"])[:, :2]) for b in roads]
    rP = [np.array(b["p"]) for b in roads]
    rc = [np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P[:, :2], axis=0).T))]) for P in rP]
    tree = STRtree(rl) if rl else None
    res = []
    for b in out:
        if b["kind"] != "tram":
            res.append(b)
            continue
        P = np.array(b["p"]); g = np.array(b["g"]); n = len(P); el = P[:, 2] - g
        road = np.zeros(n, bool)
        if tree is not None:
            for i in range(n):
                pt = Point(P[i, :2])
                for j in tree.query(pt.buffer(14)):
                    if rl[j].distance(pt) <= roads[j]["w"] / 2 + b["w"] / 2 + 1.5:
                        sj = rl[j].project(pt)
                        if abs(float(np.interp(sj, rc[j], rP[j][:, 2])) - P[i, 2]) < near:
                            road[i] = True
                            break
        keep = road.copy()
        i = 0
        while i < n:  # ramp groups: contiguous elevated vertices not beside a road deck
            if el[i] > 0.15 and not road[i]:
                j = i
                while j + 1 < n and el[j + 1] > 0.15 and not road[j + 1]:
                    j += 1
                if el[i:j + 1].max() >= el_min:
                    keep[i:j + 1] = True
                i = j + 1
            else:
                i += 1
        if keep.all():
            res.append(b)
            continue
        i = 0
        while i < n:
            if not keep[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and keep[j + 1]:
                j += 1
            if j - i >= 1:
                sl = slice(i, j + 1)
                nb = dict(b)
                nb["p"] = b["p"][sl]; nb["g"] = b["g"][sl]; nb["b"] = b["b"][sl]
                if "ol" in b:
                    nb["ol"] = b["ol"][sl]; nb["or"] = b["or"][sl]
                Q = P[sl]
                sq = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q[:, :2], axis=0).T))])
                nb["len"] = float(sq[-1]); nb["max_el"] = float(el[sl].max()); nb["max_slope"] = _maxslope(sq, Q[:, 2])
                nb["piers"] = [q for q in b["piers"] if np.min(np.hypot(Q[:, 0] - q[0], Q[:, 1] - q[1])) < 8.0]
                segs = [LineString(Q[k:k + 2, :2]).buffer(b["w"] / 2 + 0.5, cap_style="flat")
                        for k in range(len(Q) - 1) if min(el[i + k], el[i + k + 1]) > 0.3]
                nb["excl"] = shapely.union_all(segs) if segs else shapely.Polygon()
                res.append(nb)
            i = j + 1
    return res


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
            row = {"p": [p[i] for i in r], "g": [b["g"][i] for i in r], "b": [b["b"][i] for i in r],
                   "w": b["w"], "kind": b["kind"], "name": b["name"]}
            zb = [z for z in b.get("zb", []) if x0 <= z[0] < x1 and y0 <= z[1] < y1]
            if zb and any(abs(z[0] - p[i][0]) < 40 and abs(z[1] - p[i][1]) < 40 for z in zb for i in r):
                row["zb"] = zb
            if "ol" in b:
                row["ol"] = [b["ol"][i] for i in r]
                row["or"] = [b["or"][i] for i in r]
            if r[0] > 0:   # context vertices of a row cut at the tile border: same offset normals on both sides
                row["pa"] = p[r[0] - 1][:2]
            if r[-1] < len(p) - 1:
                row["pb"] = p[r[-1] + 1][:2]
            decks.append(row)
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


DECK_PROP_KEYS = {"lamps": 14.0, "bins": 1.2, "benches": 1.0, "trafficsigns": 3.0, "hydrants": 1.0, "bollards": 1.0, "bikes": 1.2,
                  "racks": 1.2, "mopeds": 1.2, "signals": 4.0}


def drop_deck_props(meta, BR):
    """Street furniture standing on the ground UNDER a deck (z at ground, not at deck height) must not stick through / sit inside it:
    lamps in the Kalkbreite rail cutting pierced the road deck. A row inside a deck footprint (+0.2 m) is dropped when its base is below
    the deck and its top reaches the underside (lamps: row[4] is the height), or when the deck is solid to the ground (skirt). Rows on
    the deck (z ~ deck top) stay. Returns the number dropped; audit: pipeline/audit_decks.py (buried / pierce)."""
    from shapely.strtree import STRtree
    segs, info = [], []
    for b in BR or []:
        if b["kind"] == "rail":
            continue
        p = b["p"]
        for i in range(len(p) - 1):
            if min(p[i][2] - b["g"][i], p[i + 1][2] - b["g"][i + 1]) < 0.3:
                continue
            segs.append(LineString([q[:2] for q in p[i:i + 2]]).buffer(b["w"] / 2 + 0.2, cap_style="flat"))
            info.append((min(b["b"][i], b["b"][i + 1]), (p[i][2] + p[i + 1][2]) / 2))
    if not segs:
        return 0
    st = STRtree(segs)
    n = 0
    for k, h0 in DECK_PROP_KEYS.items():
        rows = meta.get(k)
        if not rows:
            continue
        keep = []
        for r in rows:
            pt = Point(r[0], r[1])
            drop = False
            for j in st.query(pt):
                if not segs[j].contains(pt):
                    continue
                under, top = info[j]
                z = r[2]
                if z > top - 0.6:      # stands on the deck
                    continue
                h = float(r[4]) if k == "lamps" and len(r) > 4 else h0
                if z + h > under - 0.1:
                    drop = True
                    break
            if drop:
                n += 1
            else:
                keep.append(r)
        meta[k] = keep
    return n
