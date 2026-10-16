"""Legal-area raster for the traffic audit (web/tests/traffic_legal.mjs) -> web/tests/fixtures/traffic_zones.png + .json.

1 m cells, value per cell: 0 other (kerb/footway/yard), 1 carriageway, 2 square, 3 pedestrian zone (OGD), 4 park,
5 building, 6 rail land, 7 bridge deck. Legal for a car: 1 and 7 (roads win over park/rail/building overlaps, not over
squares/pedestrian zones). Not used by the game, test fixture only.
"""
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from PIL import Image, ImageDraw
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridges  # noqa: E402
import sources  # noqa: E402
import streets  # noqa: E402
import streets_rules  # noqa: E402
from config import AREA, ROOT  # noqa: E402

OUT = ROOT / "web" / "tests" / "fixtures"
CELL = 1.0


def layer(geom, x0, y1, W, H):
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    for g in shapely.get_parts(geom) if geom is not None and not geom.is_empty else []:
        if g.geom_type != "Polygon":
            continue
        f = lambda c: [((x - x0) / CELL, (y1 - y) / CELL) for x, y in c]  # noqa: E731
        d.polygon(f(g.exterior.coords), fill=1)
        for r in g.interiors:
            d.polygon(f(r.coords), fill=0)
    return np.array(im, bool)


def main():
    nodes, els = sources.osm()
    S = streets.parse(nodes, els)
    x0, y0, x1, y1 = AREA[0] - 80, AREA[1] - 80, AREA[2] + 80, AREA[3] + 80
    W, H = int((x1 - x0) / CELL), int((y1 - y0) / CELL)
    bld, rail, tun = [], [], []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way" and t.get("tunnel") in ("yes", "building_passage") and t.get("highway") in streets.WIDTH and len(e["nodes"]) > 1:
            ps = [nodes[n] for n in e["nodes"] if n in nodes]
            if len(ps) > 1:
                tun.append(shapely.LineString(ps).buffer(streets.WIDTH[t["highway"]] / 2))
        if e["type"] != "way" or e["nodes"][0] != e["nodes"][-1] or len(e["nodes"]) < 4:
            continue
        pts = [nodes[n] for n in e["nodes"] if n in nodes]
        if len(pts) < 4:
            continue
        if t.get("building") and t.get("building") not in ("roof", "no") and t.get("layer", "0") in ("0", "1"):
            bld.append(Polygon(pts).buffer(0))
        elif t.get("landuse") == "railway":
            rail.append(Polygon(pts).buffer(0))
    BR = bridges.bridge_ways(nodes, els, AREA)
    decks = shapely.union_all([shapely.LineString(np.array(b["p"])[:, :2]).buffer(b["w"] / 2 + 0.5) for b in BR]) if BR else Polygon()
    R = streets_rules.rules()
    L = lambda g: layer(g, x0, y1, W, H)  # noqa: E731
    g = np.zeros((H, W), np.uint8)
    g[L(S["parks"])] = 4
    g[L(shapely.union_all(rail))] = 6
    g[L(shapely.union_all(bld))] = 5
    g[L(S["roads"])] = 1
    g[L(S["plaza"])] = 2
    g[L(R.zones["fuss"])] = 3
    # a pedestrian-zone polygon may carry a legal road only where the road graph says so: keep it as 3
    g[L(decks)] = 7
    g[L(shapely.union_all(tun))] = 7  # road tunnels / passages (buses run through the Langstrasse underpass)
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(g).save(OUT / "traffic_zones.png", optimize=True)
    json.dump({"x0": x0, "y1": y1, "w": W, "h": H, "cell": CELL}, open(OUT / "traffic_zones.json", "w"))
    print("cells", {int(k): int(v) for k, v in zip(*np.unique(g, return_counts=True))}, (OUT / "traffic_zones.png").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
