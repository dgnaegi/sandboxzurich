"""Build a directed road graph (cars + bikes) from OSM for the traffic simulation -> web/public/data/roads.json."""
import json
import math
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])
from config import AREA, ROOT  # noqa: E402
from sources import osm  # noqa: E402
from streets import WIDTH, _num  # noqa: E402

MARGIN = 150.0
SPEED = {"primary": 50, "secondary": 50, "tertiary": 50, "residential": 30, "unclassified": 30, "living_street": 20,
         "primary_link": 50, "secondary_link": 40, "tertiary_link": 40}
WIDTH = {**WIDTH, "living_street": 5}
OUT = ROOT / "web" / "public" / "data" / "roads.json"


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
        if not hw or t.get("tunnel") in ("yes", "building_passage") or t.get("area") == "yes":
            continue
        if hw not in SPEED and hw != "cycleway":
            continue
        if t.get("access") in ("private", "no") or t.get("motor_vehicle") == "no" and hw != "cycleway":
            if hw != "cycleway":
                continue
        ns = [n for n in e["nodes"] if n in nodes]
        if len(ns) < 2 or not any(x0 <= nodes[n][0] <= x1 and y0 <= nodes[n][1] <= y1 for n in ns):
            continue
        ways.append((hw, t, ns))
    cnt = Counter(n for _, _, ns in ways for n in set(ns))
    junction = lambda n: cnt[n] >= 2  # noqa: E731

    idx, nlist = {}, []

    def nid(n):
        if n not in idx:
            idx[n] = len(nlist)
            nlist.append(nodes[n])
        return idx[n]

    cars, bikes = [], []

    def add(lst, a, b, pts, v, w, ow):
        p = np.round(np.array(pts), 1).flatten().tolist()
        lst.append({"a": a, "b": b, "p": p, "v": v, "w": round(w, 1), "ow": int(ow)})

    for hw, t, ns in ways:
        cyc_way = hw == "cycleway"
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"nodes": [[round(x, 1), round(y, 1)] for x, y in nlist], "cars": cars, "bikes": bikes},
              open(OUT, "w"), separators=(",", ":"))
    print("wrote", OUT, OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
