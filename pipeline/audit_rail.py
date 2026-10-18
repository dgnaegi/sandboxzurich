"""Read-only audit: objects/edges on railway land (railzone.json) that are not on a bridge deck or platform.
Usage: .venv/bin/python pipeline/audit_rail.py  -> research/audit_rail.md"""
import glob
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.strtree import STRtree

R = Path(__file__).resolve().parent.parent
D = R / "web/public/data"
zones = [Polygon(z["r"][0], z["r"][1:]) for z in json.load(open(D / "railzone.json"))["zones"]]
tree = STRtree(zones)


def inzone(x, y):
    return len(tree.query(shapely.Point(x, y), predicate="within")) > 0


# decks (walkable/drivable) from all tiles: a point on a deck is fine
decks = []
for f in glob.glob(str(R / "web/public/tiles/t_*.json")):
    try:
        m = json.load(open(f))
    except Exception:
        continue
    for d in (m.get("bridges") or {}).get("decks", []):
        if d["kind"] != "rail" and not d.get("sub"):
            decks.append((d["p"], d["w"]))
for f in ("station_decks", "hb_decks", "hb3_decks"):
    try:
        for d in json.load(open(D / f"{f}.json")).get("decks", []):
            decks.append((d["p"], d["w"]))
    except Exception:
        pass
dg = shapely.union_all([shapely.LineString(np.array(p)[:, :2]).buffer(w / 2 + 0.3) for p, w in decks if len(p) > 1] or [Polygon()])
dgp = shapely.prepared.prep(dg) if hasattr(shapely, "prepared") else dg


def ondeck(x, y):
    return dg.contains(shapely.Point(x, y))


def bad(x, y):
    return inzone(x, y) and not ondeck(x, y)


sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridges  # noqa: E402  roads2
import groundcover  # noqa: E402
import road_exclude  # noqa: E402
import sources  # noqa: E402
from config import AREA  # noqa: E402
_n, _e = sources.osm()
BZ = road_exclude.bad_zone(_n, _e, groundcover.load((AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)), bridges.bridge_ways(_n, _e, AREA))


def bad_edge(x, y):  # roads2: lanes count only on open water / ground-level tracks (AV 'Bahngebiet' also covers roads under viaducts)
    return shapely.contains_xy(BZ, x, y)


res = {}
def edges(name, rows, key="p", stride=3, bad=bad):
    n, hits = 0, []
    for i, e in enumerate(rows):
        p = e[key] if isinstance(e, dict) else e
        pts = list(zip(p[0::2], p[1::2])) if (p and not isinstance(p[0], list)) else [tuple(q[:2]) for q in p]
        cnt, first = 0, None
        for (a, b), (c, d) in zip(pts, pts[1:]):
            L = math.hypot(c - a, d - b)
            for k in range(max(1, int(L / stride))):
                t = k / max(1, int(L / stride))
                x, y = a + (c - a) * t, b + (d - b) * t
                if bad(x, y):
                    cnt += 1
                    first = first or (round(x), round(y))
        n += 1
        if cnt:
            hits.append((cnt * stride, i, first))
    hits.sort(reverse=True)
    res[name] = (n, hits)


roads = json.load(open(D / "roads.json"))
edges("Auto-Kanten (roads.cars)", roads["cars"], bad=bad_edge)
edges("Velo-Kanten (roads.bikes)", roads["bikes"], bad=bad_edge)
tr = json.load(open(D / "transit.json"))["lines"]
edges("Bus/Tram-Linien (transit.lines)", tr, "pts", 4)


def pts(name, rows):
    hits = [(0, i, (round(r[0]), round(r[1]))) for i, r in enumerate(rows) if bad(r[0], r[1])]
    res[name] = (len(rows), hits)


se = json.load(open(D / "stops_equip.json"))
for k, v in se.items():
    if isinstance(v, list) and v and isinstance(v[0], list) and isinstance(v[0][0], (int, float)):
        pts(f"Haltestellen-Ausstattung stops_equip.{k}", v)
for f in sorted(glob.glob(str(R / "research/stations/spots_*.json"))):
    s = json.load(open(f))
    for k, v in s.items():
        if isinstance(v, list) and v and isinstance(v[0], list) and isinstance(v[0][0], (int, float)):
            pts(f"Ped-Spots {Path(f).stem}.{k}", v)
TK = ["cars", "bikes", "racks", "scooters", "mopeds", "benches", "bins", "workers"]
agg = {k: [0, []] for k in TK}
for f in glob.glob(str(R / "web/public/tiles/t_*.json")):
    try:
        m = json.load(open(f))
    except Exception:
        continue
    for k in TK:
        for r in m.get(k) or []:
            if isinstance(r, list) and len(r) > 1 and isinstance(r[0], (int, float)):
                agg[k][0] += 1
                if bad(r[0], r[1]):
                    agg[k][1].append((0, Path(f).stem, (round(r[0]), round(r[1]))))
for k, (n, h) in agg.items():
    res[f"Kachel-Objekte {k}"] = (n, h)

out = ["# Audit Bahnfläche (generiert von pipeline/audit_rail.py)", "",
       f"Zonen: {len(zones)}, Decks (nicht Gleis, nicht sub): {len(decks)}. Treffer = innerhalb railzone und nicht auf Deck.", "",
       "| Kategorie | geprüft | Treffer |", "|---|---|---|"]
for k, (n, h) in res.items():
    out.append(f"| {k} | {n} | {len(h)} |")
out.append("")
for k, (n, h) in res.items():
    if h:
        out += [f"## {k}"] + [f"- {a}m idx/tile {b} bei {c}" for a, b, c in h[:8]] + [""]
Path(R / "research/audit_rail.md").write_text("\n".join(out))
print("\n".join(out[:34]))
