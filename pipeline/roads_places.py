"""Pick the worst distinct places from logs/roads_audit_pre.json and write logs/roads_places.json (+ ride lines)."""
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sources  # noqa: E402
import streets  # noqa: E402
from config import ROOT  # noqa: E402

top = json.load(open(ROOT / "logs" / "roads_audit_pre.json"))["top"]
nodes, els = sources.osm()
S = streets.parse(nodes, els)
ways = [w for w in S["ways"] if w["hw"] != "service"]
picked = []
for e in top:
    if e["name"].endswith("brücke") or any(np.hypot(e["x"] - p["x"], e["y"] - p["y"]) < 150 for p in picked):
        continue
    pt = Point(e["x"], e["y"])
    w = min(ways, key=lambda w: w["line"].distance(pt))
    from shapely.ops import linemerge
    same = [x["line"] for x in ways if x["name"] == w["name"] and x["line"].distance(pt) < 250]
    m = linemerge(same)
    ml = max(getattr(m, "geoms", [m]), key=lambda g: g.distance(pt) * -1 + g.length * 0.0001)
    w = {**w, "line": ml}
    s = w["line"].project(pt)
    a, b = w["line"].interpolate(max(0, s - 3)), w["line"].interpolate(min(w["line"].length, s + 3))
    d = np.array([b.x - a.x, b.y - a.y]); d /= max(np.hypot(*d), 1e-6)
    seg = [w["line"].interpolate(t) for t in np.arange(max(0, s - 80), min(w["line"].length, s + 80), 4)]
    picked.append({"name": e["name"], "x": e["x"], "y": e["y"], "dx": float(d[0]), "dy": float(d[1]), "pts": [[p.x, p.y] for p in seg]})
    if len(picked) == 8:
        break
json.dump(picked, open(ROOT / "logs" / "roads_places.json", "w"), indent=1)
json.dump([{"name": p["name"], "pts": p["pts"]} for p in picked if len(p["pts"]) > 15][:3], open(ROOT / "logs" / "roads_ride_lines.json", "w"))
for p in picked:
    print(p["name"], round(p["x"]), round(p["y"]), "tile", int(p["x"] // 200), int(p["y"] // 200))
