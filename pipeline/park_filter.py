"""Apply cityprops.street_parking() to the already built tiles (web/public/tiles/t_*.json) without a full rebuild:
parked cars that stand on squares, pedestrian zones, parks, rail land or far from any carriageway are removed together
with their colliders. A full build (build_testarea.py) does the same through cityprops, this is the fast path.
  .venv/bin/python pipeline/park_filter.py [--dry]
"""
import json
import sys
from pathlib import Path

import shapely

sys.path.insert(0, str(Path(__file__).resolve().parent))
import citydata  # noqa: E402
import cityprops  # noqa: E402
import groundcover  # noqa: E402
import sources  # noqa: E402
import streets  # noqa: E402
from config import AREA, ROOT  # noqa: E402

TILES = ROOT / "web" / "public" / "tiles"


def main(dry):
    nodes, els = sources.osm()
    S = streets.parse(nodes, els)
    BIG = (AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)
    S["av_rail"] = shapely.set_precision(groundcover.load(BIG)["rail"].buffer(0), 0.01)
    C = citydata.load(BIG)
    keep = {(r[0], r[1]) for r in cityprops.street_parking(C, S)}
    n0 = n1 = 0
    for f in sorted(TILES.glob("t_*.json")):
        d = json.load(open(f))
        cars = d.get("cars")
        if not cars:
            continue
        ok = [r for r in cars if (r[0], r[1]) in keep]
        n0 += len(cars)
        n1 += len(ok)
        if len(ok) == len(cars) or dry:
            continue
        gone = [r for r in cars if (r[0], r[1]) not in keep]
        rings = cityprops.car_colliders(gone)
        d["colliders"] = [c for c in d.get("colliders", []) if c not in rings]
        d["cars"] = ok
        json.dump(d, open(f, "w"), separators=(",", ":"))
    print(f"parked cars in tiles: {n0} -> {n1} ({n0 - n1} removed){' (dry)' if dry else ''}")


if __name__ == "__main__":
    main("--dry" in sys.argv)
