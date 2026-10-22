"""Audit of the overhead wires (pipeline/wires.py) on the real inputs, without a tile build (flat ground).

Usage: .venv/bin/python pipeline/audit_wires.py        (prints <= 30 lines; details to research/wires/audit_*.tsv)
Checks: wire ends without mast/wall anchor, span wires crossing a building, tile joins, vertices per tile.
"""
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, box
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import citydata  # noqa: E402
import lidar  # noqa: E402
import sources  # noqa: E402
import streets  # noqa: E402
import wires  # noqa: E402
from config import AREA, TILE, tiles  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUTD = ROOT / "research" / "wires"


def inputs():
    import os
    import pickle
    cf = os.environ.get("WIRES_CACHE")
    if cf and os.path.exists(cf):
        return pickle.load(open(cf, "rb"))
    r = _inputs()
    if cf:
        pickle.dump(r, open(cf, "wb"))
    return r


def _inputs():
    nodes, els = sources.osm()
    S = streets.parse(nodes, els)
    BIG = (AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)
    C = citydata.load(BIG)
    roads = S["roads"]
    lights = [(x, y) for x, y, _ in C.get("lights", []) if not roads.contains(Point(x, y))]
    fps = wires.footprints(sources.buildings(margin=60))
    tr = json.load(open(ROOT / "web/public/data/transit.json"))["lines"]
    routes = [(l["ref"], l["dir"], l["pts"]) for l in tr if l["mode"] == "trolleybus"]
    return S, roads, lights, fps, routes, lidar.masts(BIG)


def main():
    S, roads, lights, fps, routes, masts = inputs()
    T = tiles()
    net = wires.build(S["tram"], routes, masts, lights, fps, roads, lambda x, y: 0.0, T, TILE)
    core = [f.buffer(-0.3) for f, _ in fps]
    ctree = STRtree(core)
    anchors = np.array([a[:2] for a in net.anchors]).reshape(-1, 2)
    akd = shapely.points(anchors) if len(anchors) else []
    atree = STRtree(akd) if len(anchors) else None
    wl = [(w["g"], w["kind"], LineString([p[:2] for p in w["pts"]])) for w in net.wires if w["kind"] != "span"]
    wt = STRtree([w[2] for w in wl])
    area = shapely.union_all([box(ix * TILE, iy * TILE, (ix + 1) * TILE, (iy + 1) * TILE) for ix, iy in T]).boundary
    bad, kinds = [], {"mast": 0, "wall": 0, "junction": 0, "edge": 0}
    for w in net.wires:
        if w["kind"] == "span":
            continue
        for k in (0, -1):
            p = Point(w["pts"][k][:2])
            if atree is not None and any(p.distance(akd[j]) <= 0.35 for j in atree.query(p.buffer(0.4))):
                a = min(net.anchors, key=lambda a: (a[0] - p.x) ** 2 + (a[1] - p.y) ** 2)
                kinds[a[3]] += 1
            elif area.distance(p) < 0.2:
                kinds["edge"] += 1
            elif any(wl[j][0] != w["g"] and wl[j][2].distance(p) <= 1.3 for j in wt.query(p.buffer(1.3))):
                kinds["junction"] += 1
            else:
                bad.append(("end", round(p.x, 1), round(p.y, 1), w["kind"]))
    cross = []
    for w in net.wires:
        if w["kind"] != "span":
            continue
        ln = LineString([p[:2] for p in w["pts"]])
        if len(ctree.query(ln, predicate="intersects")):
            cross.append(("span", round(w["pts"][1][0], 1), round(w["pts"][1][1], 1), "building"))
    # tile joins + vertex budget
    ends, nv = {}, []
    for ix, iy in T:
        tb = box(ix * TILE, iy * TILE, (ix + 1) * TILE, (iy + 1) * TILE)
        ws, ps = wires.tile(net, tb)
        nv.append(sum(len(r) for r in ws))
        x0, y0, x1, y1 = tb.bounds
        for r in ws:
            for p in (r[0], r[-1]):
                if p[0] in (x0, x1) or p[1] in (y0, y1):
                    ends.setdefault((round(p[0], 1), round(p[1], 1)), set()).add((ix, iy))
    tset = set(T)
    join_bad = []
    for (x, y), ts in ends.items():
        if x % TILE == 0 and y % TILE != 0:
            nb = {(int(x // TILE) - 1, int(y // TILE)), (int(x // TILE), int(y // TILE))}
        elif y % TILE == 0 and x % TILE != 0:
            nb = {(int(x // TILE), int(y // TILE) - 1), (int(x // TILE), int(y // TILE))}
        else:
            continue
        if nb <= tset and not nb <= ts:  # both tiles exist but only one has the wire end
            join_bad.append((x, y))
    n_tr = sum(1 for w in net.wires if w["kind"] == "tram")
    n_tb = sum(1 for w in net.wires if w["kind"] == "trolley")
    ms = sum(1 for a in net.anchors if a[3] == "mast")
    print(f"wires: tram {n_tr} polylines, trolley {n_tb} (31/32/33/72 pairs), spans {net.spans}, span fails {net.fail}")
    print(f"masts: lidar/osm candidates {len(masts)}+{len(lights)}, anchors used mast {ms}/wall {len(net.anchors) - ms}, poles drawn {len(net.poles)} (new kerb {net.n_kerb}, LiDAR without game pole {net.n_lidar})")
    print(f"wire ends ok: mast {kinds['mast']}, wall {kinds['wall']}, junction {kinds['junction']}, area edge {kinds['edge']}")
    print(f"UNANCHORED ENDS: {len(bad)}   SPANS THROUGH BUILDINGS: {len(cross)}   TILE JOINS BROKEN: {len(join_bad)}")
    for r in (bad + cross)[:12]:
        print("  ", r)
    print(f"vertices per tile: avg {np.mean(nv):.0f}, max {max(nv)} over {len(nv)} tiles")
    (OUTD / "audit_wires.tsv").write_text("\n".join("\t".join(map(str, r)) for r in bad + cross))
    # old generator for comparison
    import props

    class Flat:
        def at(self, x, y):
            return 0.0

    old = [sum(len(r) for r in props.tram_wires(S["tram"], box(ix * TILE, iy * TILE, (ix + 1) * TILE, (iy + 1) * TILE), Flat())) for ix, iy in T]
    print(f"old tram_wires vertices per tile: avg {np.mean(old):.0f}, max {max(old)}")


if __name__ == "__main__":
    main()
