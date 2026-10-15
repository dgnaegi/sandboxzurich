"""Real cycling infrastructure in the test area (OSM: highway=cycleway, cycleway*=lane|track, bicycle_road=yes,
cyclestreet=yes) as polylines for gameplay (faster on bike lanes). Output: web/public/data/veloinfra.json"""
import json

from shapely.geometry import LineString, box

import sources
from config import AREA, ROOT


def main():
    nodes, els = sources.osm()
    area = box(*AREA).buffer(100)
    out = []
    for e in els:
        if e["type"] != "way":
            continue
        t = e.get("tags", {})
        cyc = [t.get(k, "") for k in ("cycleway", "cycleway:left", "cycleway:right", "cycleway:both")]
        infra = (t.get("highway") == "cycleway" or any(c in ("lane", "track", "opposite_lane", "opposite_track") for c in cyc)
                 or t.get("bicycle_road") == "yes" or t.get("cyclestreet") == "yes"
                 or (t.get("highway") in ("path", "footway") and t.get("bicycle") == "designated"))
        if not infra:
            continue
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
        if len(pts) < 2 or not LineString(pts).intersects(area):
            continue
        kind = "weg" if t.get("highway") in ("cycleway", "path", "footway") else "strasse" if t.get("bicycle_road") == "yes" or t.get("cyclestreet") == "yes" else "streifen"
        out.append({"k": kind, "p": [[round(x, 1), round(y, 1)] for x, y in pts]})
    json.dump({"lines": out}, open(ROOT / "web" / "public" / "data" / "veloinfra.json", "w"), separators=(",", ":"))
    total = sum(LineString(l["p"]).length for l in out)
    print(len(out), "segments,", round(total), "m", {k: sum(1 for l in out if l["k"] == k) for k in ("weg", "streifen", "strasse")})


if __name__ == "__main__":
    main()
