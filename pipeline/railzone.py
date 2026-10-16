"""Railway land where nobody walks -> web/public/data/railzone.json (used by pedestrians, pedspots, lawns).

Zone = Amtliche Vermessung "Bahngebiet" (groundcover class rail) + OSM railway=rail/light_rail/narrow_gauge lines
buffered 4 m, minus platforms (OSM railway=platform / public_transport=platform, Perrons stay walkable) and minus
the footprint of road/foot bridges (people on a deck are above the tracks)."""
import json
import sys

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])
import bridges  # noqa: E402
import groundcover  # noqa: E402
import sources  # noqa: E402
from config import AREA, ROOT  # noqa: E402

OUT = ROOT / "web" / "public" / "data" / "railzone.json"


def build():
    nodes, els = sources.osm()
    BIG = (AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)
    G = groundcover.load(BIG)
    rail, plat = [G["rail"].buffer(0)], []
    for e in els:
        if e["type"] != "way":
            continue
        t = e.get("tags", {})
        pts = [nodes[n] for n in e["nodes"] if n in nodes]
        if len(pts) < 2:
            continue
        if t.get("railway") in ("rail", "light_rail", "narrow_gauge"):
            if t.get("tunnel") in ("yes", "building_passage") or t.get("bridge") == "yes":
                continue
            rail.append(LineString(pts).buffer(4.0))
        elif t.get("railway") == "platform" or t.get("public_transport") == "platform" or (
                t.get("highway") == "platform" and t.get("railway") != "tram_stop"):
            plat.append(Polygon(pts).buffer(0.5) if pts[0] == pts[-1] and len(pts) >= 4 else LineString(pts).buffer(2.5))
    zone = shapely.union_all(rail)
    if plat:
        zone = zone.difference(shapely.union_all(plat))
    BR = bridges.bridge_ways(nodes, els, AREA)
    deck = shapely.union_all([LineString(np.array(b["p"])[:, :2]).buffer(b["w"] / 2 + 0.5) for b in BR
                              if b["kind"] in ("road", "foot")] or [Polygon()])
    zone = zone.difference(deck).simplify(0.3)
    polys = [g for g in getattr(zone, "geoms", [zone]) if g.geom_type == "Polygon" and g.area > 4]
    out = [{"b": [round(v, 1) for v in g.bounds],
            "r": [[[round(x, 1), round(y, 1)] for x, y in ring.coords] for ring in [g.exterior, *g.interiors]]} for g in polys]
    json.dump({"zones": out}, open(OUT, "w"), separators=(",", ":"))
    print(f"{len(out)} rail zones, {zone.area / 1e4:.1f} ha -> {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
