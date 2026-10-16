"""Build a directed road graph (cars + bikes) from OSM for the traffic simulation -> web/public/data/roads.json."""
import json
import math
import sys
from collections import Counter

import numpy as np
import shapely

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])
from config import AREA, ROOT  # noqa: E402
from sources import osm  # noqa: E402
import streets  # noqa: E402
from streets import WIDTH, _num  # noqa: E402

MARGIN = 150.0
SPEED = {"primary": 50, "secondary": 50, "tertiary": 50, "residential": 30, "unclassified": 30, "living_street": 20,
         "primary_link": 50, "secondary_link": 40, "tertiary_link": 40}
WIDTH = {**WIDTH, "living_street": 5}
OUT = ROOT / "web" / "public" / "data" / "roads.json"


# access values that keep ordinary NPC cars off a way ("destination"/"delivery" = Zubringer/Anlieferung only)
NO_CAR = {"no", "private", "permit", "customers", "delivery", "destination", "agricultural", "forestry", "emergency",
          "agricultural;destination", "delivery;private", "unknown"}


def car_allowed(t):
    """OSM access rules for a car: the most specific tag wins (motorcar > motor_vehicle > vehicle > access)."""
    for k in ("motorcar", "motor_vehicle", "vehicle", "access"):
        v = t.get(k)
        if v:
            return v not in NO_CAR
    return True


def offset(pts, d):
    """Offset polyline to the right (x east, y north) by d metres, mitered."""
    p = np.array(pts, float)
    if abs(d) < 1e-6 or len(p) < 2:
        return p
    seg = np.diff(p, axis=0)
    ln = np.linalg.norm(seg, axis=1)
    ln[ln == 0] = 1e-9
    n = np.stack([seg[:, 1], -seg[:, 0]], 1) / ln[:, None]  # right normals
    nn = np.zeros_like(p)
    nn[0], nn[-1] = n[0], n[-1]
    for i in range(1, len(p) - 1):
        m = n[i - 1] + n[i]
        k = np.linalg.norm(m)
        nn[i] = n[i] if k < 1e-6 else m / k * min(1 / max(np.dot(m / k, n[i]), 0.5), 2.0)
    return p + nn * d


def length(p):
    return float(np.linalg.norm(np.diff(np.array(p), axis=0), axis=1).sum())


def scc_edges(es):
    """Edges whose both ends lie in the largest strongly connected component (iterative Kosaraju)."""
    adj, radj = {}, {}
    for e in es:
        adj.setdefault(e["a"], []).append(e["b"])
        radj.setdefault(e["b"], []).append(e["a"])
    seen, order = set(), []
    for r in list(adj) + list(radj):
        if r in seen:
            continue
        seen.add(r)
        st = [(r, iter(adj.get(r, [])))]
        while st:
            n, it = st[-1]
            for m in it:
                if m not in seen:
                    seen.add(m)
                    st.append((m, iter(adj.get(m, []))))
                    break
            else:
                order.append(n)
                st.pop()
    comp, best = {}, []
    for r in reversed(order):
        if r in comp:
            continue
        cur, st = [r], [r]
        comp[r] = r
        while st:
            n = st.pop()
            for m in radj.get(n, []):
                if m not in comp:
                    comp[m] = r
                    cur.append(m)
                    st.append(m)
        if len(cur) > len(best):
            best = cur
    ok = set(best)
    return [e for e in es if e["a"] in ok and e["b"] in ok]


def main():
    nodes, els = osm()
    x0, y0, x1, y1 = AREA
    x0, y0, x1, y1 = x0 - MARGIN, y0 - MARGIN, x1 + MARGIN, y1 + MARGIN
    ways = []
    for e in els:
        if e["type"] != "way":
            continue
        t = e.get("tags", {})
        hw = t.get("highway")
        if not hw or (t.get("tunnel") in ("yes", "building_passage") and e["id"] != 4592588) or t.get("area") == "yes":  # 4592588 = Langstrassen-Unterfuehrung (open, cut floor)
            continue
        if hw not in SPEED and hw != "cycleway":
            continue
        if hw != "cycleway" and (hw == "living_street" or not car_allowed(t)):  # living streets are drawn as squares
            continue
        ns = [n for n in e["nodes"] if n in nodes]
        if len(ns) < 2 or not any(x0 <= nodes[n][0] <= x1 and y0 <= nodes[n][1] <= y1 for n in ns):
            continue
        ways.append((hw, t, ns, e["id"]))
    cnt = Counter(n for _, _, ns, _ in ways for n in set(ns))
    junction = lambda n: cnt[n] >= 2  # noqa: E731

    idx, nlist = {}, []

    def nid(n):
        if n not in idx:
            idx[n] = len(nlist)
            nlist.append(nodes[n])
        return idx[n]

    cars, bikes = [], []
    cur_wid = 0

    def add(lst, a, b, pts, v, w, ow):
        p = np.round(np.array(pts), 1).flatten().tolist()
        lst.append({"a": a, "b": b, "p": p, "v": v, "w": round(w, 1), "ow": int(ow), "wid": cur_wid})

    for hw, t, ns, wid in ways:
        cyc_way = hw == "cycleway"
        cur_wid = wid
        w = _num(t.get("width"), _num(t.get("lanes"), 0) * 3.2 or WIDTH.get(hw, 3)) if not cyc_way else 2.5
        oneway = t.get("oneway") in ("yes", "1", "true") or t.get("junction") == "roundabout"
        rev = t.get("oneway") == "-1"
        if rev:
            ns, oneway = ns[::-1], True
        side = lambda s: (t.get(f"cycleway:{s}") or t.get("cycleway:both") or t.get("cycleway") or "")  # noqa: E731
        lane = side("right") in ("lane", "track", "shared_busway") or (not oneway and side("left") in ("lane", "track"))
        # split at junctions
        cuts = [0] + [i for i in range(1, len(ns) - 1) if junction(ns[i]) or ns.count(ns[i]) > 1] + [len(ns) - 1]
        for c0, c1 in zip(cuts, cuts[1:]):
            seq = ns[c0:c1 + 1]
            pts = [nodes[n] for n in seq]
            a, b = nid(seq[0]), nid(seq[-1])
            if a == b and len(pts) < 4:
                continue
            L = length(pts)
            if L < 1.0:
                continue
            fwd = [list(p) for p in pts]
            bwd = fwd[::-1]
            if cyc_way:
                two = t.get("oneway") not in ("yes", "1")
                add(bikes, a, b, fwd, 15, w, not two)
                if two:
                    add(bikes, b, a, bwd, 15, w, 0)
                continue
            v = SPEED[hw]
            if t.get("maxspeed", "").replace(" ", "").isdigit():
                v = int(t["maxspeed"])
            elif t.get("maxspeed") in ("30", "20"):
                v = int(t["maxspeed"])
            v = min(max(v, 20), 50)
            if oneway:
                add(cars, a, b, fwd, v, w, 1)
            else:
                add(cars, a, b, offset(fwd, w / 4), v, w, 0)
                add(cars, b, a, offset(bwd, w / 4), v, w, 0)
            # bikes: right edge on roads with lane/track or calm streets; skip busy roads without lane
            if hw in ("primary", "secondary", "primary_link", "secondary_link") and not lane:
                continue
            od = max(w / 2 - 0.8, 0.5) if oneway else max(w / 2 - 0.8, 0.5)
            add(bikes, a, b, offset(fwd, od), 15, w, oneway)
            if not oneway:
                add(bikes, b, a, offset(bwd, od), 15, w, 0)

    # construction sites: no lane through trenches, barriers or fences (sites.blocked_zones); lanes that end in a
    # blocked edge become dead ends and are pruned too
    import sites
    from shapely.geometry import LineString
    from shapely.strtree import STRtree
    zones = sites.blocked_zones()
    tree = STRtree(zones) if zones else None

    def blocked(e):
        return tree is not None and len(tree.query(LineString(np.array(e["p"]).reshape(-1, 2)), predicate="intersects")) > 0

    for name, es in (("cars", cars), ("bikes", bikes)):
        had_out = {e["a"] for e in es}
        n0 = len(es)
        es[:] = [e for e in es if not blocked(e)]
        n1 = len(es)
        while True:
            outs = {e["a"] for e in es}
            dead = [e for e in es if e["b"] not in outs and e["b"] in had_out]
            if not dead:
                break
            ids = {id(e) for e in dead}
            es[:] = [e for e in es if id(e) not in ids]
        print(f"construction sites: {name} {n0 - n1} edges blocked + {n1 - len(es)} dead ends pruned")

    # no cars in pedestrian zones (OGD Fussgaengerzone), on squares/pedestrian areas (OSM) or along a tram track that
    # is not a road; then keep only the largest strongly connected part, so no lane leads into a dead end
    import streets_rules
    S = streets.parse(nodes, els)
    banned = [g for g in (streets_rules.rules().zones.get("fuss"), S.get("plaza")) if g is not None and not g.is_empty]
    ban = shapely.union_all(banned).buffer(-0.5)
    shapely.prepare(ban)

    def in_ban(e):
        ln = LineString(np.array(e["p"]).reshape(-1, 2))
        return ln.length > 0 and ln.intersection(ban).length > 0.5 * ln.length

    # streets.parse only draws roads up to 40 m beyond the area: cars never drive where there is no ground
    from shapely.geometry import box
    drawn = box(*AREA).buffer(39)
    n0 = len(cars)
    cars[:] = [e for e in cars if drawn.contains(LineString(np.array(e["p"]).reshape(-1, 2)))]
    print(f"cars beyond the drawn area: {n0 - len(cars)} edges removed")
    n0 = len(cars)
    cars[:] = [e for e in cars if not in_ban(e)]
    print(f"cars in pedestrian zones / squares: {n0 - len(cars)} edges removed")
    keep = scc_edges(cars)
    print(f"cars: {len(cars) - len(keep)} edges outside the largest strongly connected part removed")
    cars[:] = keep

    # report
    def comps(es):
        par = {}
        f = lambda a: par.setdefault(a, a) if par.get(a, a) == a else par.__setitem__(a, f(par[a])) or par[a]  # noqa: E731
        for e in es:
            par[f(e["a"])] = f(e["b"])
        return Counter(f(n) for e in es for n in (e["a"], e["b"]))

    for name, es in (("cars", cars), ("bikes", bikes)):
        c = comps(es)
        outd = Counter(e["a"] for e in es)
        ind = Counter(e["b"] for e in es)
        dead = sum(1 for n in set(outd) | set(ind) if outd[n] == 0 or ind[n] == 0)
        tot = sum(length(np.array(e["p"]).reshape(-1, 2)) for e in es) / 1000
        big = sorted(c.values(), reverse=True)[:3]
        print(f"{name}: {len(es)} edges, {tot:.1f} km, comps {len(c)} (largest node-refs {big}), nodes w/o in/out {dead}")
    print(f"nodes {len(nlist)}")
    # bridge decks: vertices on a deck carry the deck height "z" (null = terrain), so vehicles drive on top of bridges
    import bridges
    from decktrack import DeckTrack
    dt = DeckTrack(bridges.bridge_ways(nodes, els, AREA))
    for name, es in (("cars", cars), ("bikes", bikes)):
        n = 0
        for e in es:
            z = dt.z(np.array(e["p"]).reshape(-1, 2).tolist(), [e["wid"]])
            if any(v is not None for v in z):
                e["z"] = z
                n += 1
            del e["wid"]
        print(f"deck heights: {name} {n} edges on bridges")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"nodes": [[round(x, 1), round(y, 1)] for x, y in nlist], "cars": cars, "bikes": bikes},
              open(OUT, "w"), separators=(",", ":"))
    print("wrote", OUT, OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
