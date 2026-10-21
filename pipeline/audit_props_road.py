"""Audit: placed street objects (tiles + global data files) standing on the carriageway (traffic_zones raster cell 1 = AV/OSM
carriageway incl. tram bed; squares (2) and pedestrian zones (3) are legit). Usage: python3 pipeline/audit_props_road.py [--out DIR]
Output: counts per source/type + 30 worst places; full list research/props_road/audit.tsv.
Raster = web/tests/fixtures/traffic_zones.png (pipeline/traffic_zones.py, same S['roads'] as the build)."""
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FX = ROOT / "web" / "tests" / "fixtures"
meta = json.load(open(FX / "traffic_zones.json"))
GRID = np.array(Image.open(FX / "traffic_zones.png"))


def cat(x, y):
    i, j = int((x - meta["x0"]) // meta["cell"]), int((meta["y1"] - y) // meta["cell"])
    return int(GRID[j, i]) if 0 <= i < meta["w"] and 0 <= j < meta["h"] else 0


# tile key -> index of x (y follows). Wall/infrastructure objects (lamps, masts, signals, signs, trees = lane_fix) are not furniture.
TILE_XY = {"benches": 0, "bins": 0, "bikes": 0, "racks": 0, "mopeds": 0, "fountains": 0, "terraces": 0, "scooters": 0,
           "pingpong": 0, "playground": 0, "hydrants": 0, "bollards": 0, "lawn": 0, "cranes": 0, "workers": 0, "construction": 0,
           "sites": 1}
SUB_XY = {"details.objs": 1, "yards.props": 1, "places.objs": 1, "places.seats": 0}
# legit on-road objects (see props_road.py): reported as "exempt", not as findings
EXEMPT_SRC = {"sites", "workers", "cranes", "construction", "bollards", "scenes.eggonly", "scenes.umzug"}
EXEMPT_TYPE = {"details.objs": {"gate", "guidepost", "column"}}
TOL = [(0.0, 0.0), (0.6, 0), (-0.6, 0), (0, 0.6), (0, -0.6)]


def on_road(x, y):
    return all(cat(x + dx, y + dy) == 1 for dx, dy in TOL)


def rows():
    for f in sorted(glob.glob(str(ROOT / "web/public/tiles/t_*.json"))):
        d = json.load(open(f))
        tid = Path(f).stem
        for k, i in TILE_XY.items():
            for r in d.get(k) or []:
                yield k, tid, r[i], r[i + 1], str(r[0]) if k == "details.objs" else ""
        for k, i in SUB_XY.items():
            a, b = k.split(".")
            for r in (d.get(a) or {}).get(b) or []:
                yield k, tid, r[i], r[i + 1], str(r[0]) if isinstance(r[0], str) else ""
    D = ROOT / "web/public/data"
    sc = json.load(open(D / "scenes.json"))["scenes"]
    for s in sc:
        pts = s.get("path") or [[s["x"], s["y"]]] if "x" in s or "path" in s else []
        for p in pts:
            yield "scenes." + s.get("type", "?"), "scenes", p[0], p[1], ""
    for o in json.load(open(D / "catalog.json")).get("o", []):
        yield "catalog", "catalog", o[1], o[2], o[0]
    for k, v in json.load(open(D / "ogd_extras.json")).items():
        if isinstance(v, list) and v and isinstance(v[0], dict) and "x" in v[0]:
            for o in v:
                yield "ogd_extras." + k, "ogd", o["x"], o["y"], ""


def overlaps():
    """Objects inside fountain basins / Velotunnel mouth (props_road.keepouts): same rows as the road audit plus lamps, masts, trees."""
    import sys
    sys.path.insert(0, str(ROOT / "pipeline"))
    import props_road
    from shapely.geometry import Point
    discs, tun = props_road.keepouts()
    res = []
    for f in sorted(glob.glob(str(ROOT / "web/public/tiles/t_*.json"))):
        d = json.load(open(f))
        tid = Path(f).stem
        for k in props_road.STAND:
            for r in d.get(k) or []:
                p = Point(r[0], r[1])
                if tun.contains(p):
                    res.append((k, "tunnel", tid, r[0], r[1]))
                elif discs.contains(p):
                    res.append((k, "fountain", tid, r[0], r[1]))
        for par, k, i in (("details", "objs", 1), ("places", "objs", 1), ("yards", "props", 1)):
            for r in (d.get(par) or {}).get(k) or []:
                if any(t in str(r[0]) for t in props_road.KEEP_PLACE) or r[0] in props_road.KEEP_TYPES:
                    continue
                p = Point(r[i], r[i + 1])
                if tun.contains(p):
                    res.append((f"{par}.{k}:{r[0]}", "tunnel", tid, r[i], r[i + 1]))
                elif discs.contains(p):
                    res.append((f"{par}.{k}:{r[0]}", "fountain", tid, r[i], r[i + 1]))
    return res


def main():
    out = ROOT / "research" / "props_road"
    out.mkdir(parents=True, exist_ok=True)
    tot, bad, per, ex = Counter(), Counter(), defaultdict(list), Counter()
    lines = []
    for src, tid, x, y, ty in rows():
        tot[src] += 1
        if src == "catalog" and not ty.startswith("V"):
            src = "catalog.stop"
        if on_road(x, y):
            if src in EXEMPT_SRC or src == "catalog.stop" or ty in EXEMPT_TYPE.get(src, ()):
                ex[src] += 1
                continue
            bad[src] += 1
            per[(round(x / 25) * 25, round(y / 25) * 25)].append(src)
            lines.append(f"{src}\t{ty}\t{tid}\t{x:.1f}\t{y:.1f}")
    (out / "audit.tsv").write_text("source\ttype\ttile\tx\ty\n" + "\n".join(lines) + "\n")
    print(f"on carriageway: {sum(bad.values())} of {sum(tot.values())}; exempt (sites, workers, bollards, gates, stop equipment): {sum(ex.values())}")
    for s in sorted(tot, key=lambda s: -bad[s]):
        if bad[s]:
            print(f"  {s:22s} {bad[s]:6d} / {tot[s]}")
    ov = overlaps()
    (out / "audit_overlaps.tsv").write_text("source\tzone\ttile\tx\ty\n" + "\n".join("\t".join(map(str, r)) for r in ov) + "\n")
    print(f"overlaps (fountain basin / tunnel mouth): {len(ov)}", dict(Counter((r[0].split(':')[0], r[1]) for r in ov)))
    print("worst 25 m cells (x,y,n,top):")
    for (x, y), v in sorted(per.items(), key=lambda kv: -len(kv[1]))[:12]:
        print(f"  {x:.0f},{y:.0f}  n={len(v)}  {Counter(v).most_common(2)}")


if __name__ == "__main__":
    main()
