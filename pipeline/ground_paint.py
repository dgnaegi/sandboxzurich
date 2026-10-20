"""Extra coloured ground paint per tile (red bike crossings, hatched restricted areas, tram stop islands …).
Called at the end of build_testarea._ground_tile. Owned by the streets agent; keep it fast (per tile)."""
import json
import os

import numpy as np
import shapely
from shapely.geometry import Point

import streets
import streets_islands
import streets_ortho
from mesh import drape
from mesh import Mesh  # noqa: F401
from config import ROOT
from styles import LAYER

CURB = 0.12
RED = (178, 64, 52)
GREEN = (62, 150, 78)  # Velostreifen mit Farbbelag (fidelity S1)
_GREEN = None


def _green_sections():
    global _GREEN
    if _GREEN is None:
        d = json.load(open(ROOT / "pipeline" / "overrides" / "velo_green.json"))["sections"]
        _GREEN = [(x["name"], shapely.union_all([Point(*p).buffer(x["r"]) for p in x["pts"]])) for x in d]
    return _GREEN


def green_lanes(S, tb):
    """Strip between the painted lane line (w/2 - 1.5 m) and the gutter, on the sections listed in overrides/velo_green.json."""
    out = []
    near = tb.buffer(30)
    for w in S["ways"]:
        if not any(w["name"] == n for n, _ in _green_sections()) or not w["line"].intersects(near):
            continue
        area = shapely.union_all([a for n, a in _green_sections() if n == w["name"]])
        ln, L = streets.mline(w), w["line"].length
        for side, solid, broken in streets.bike_lane_pieces(w):
            sgn = 1 if side == "left" else -1
            for a, b in solid + broken:
                sub = streets._sub(ln, a, b, L)
                if sub.is_empty or sub.geom_type != "LineString":
                    continue
                outer = sub.buffer(sgn * (w["w"] / 2 - 0.22), single_sided=True, cap_style="flat", join_style="mitre")
                inner = sub.buffer(sgn * (w["w"] / 2 - 1.5), single_sided=True, cap_style="flat", join_style="mitre")
                strip = outer.difference(inner).intersection(area).intersection(tb)
                if not strip.is_empty:
                    out.append(strip)
    return shapely.union_all(out) if out else None


def paint(gm, S, tb, H):
    roads = S["roads"].intersection(tb)
    dbg = None
    if os.environ.get("SBZ_PAINTDBG"):
        k = "%d_%d" % (round(tb.bounds[0] / 200), round(tb.bounds[1] / 200))
        dbg = f"/tmp/paint_{k}.png"
    red = streets_ortho.red_surfaces(tb, roads, dbg)
    import markings_override
    rx = markings_override.red_extra(tb, roads)   # hand-measured add_red (markings_z*.json)
    if rx is not None and not rx.is_empty:
        red = rx if red is None or red.is_empty else shapely.union_all([red, rx])
    if red is not None and not red.is_empty:
        drape(gm, red, H, -CURB + 0.005, RED, cell=10, layer=LAYER["white"])
        print(f"  paint: red surfaces {red.area:.0f} m2", flush=True)

    grn = green_lanes(S, tb)
    if grn is not None and not grn.is_empty:
        drape(gm, grn, H, -CURB + 0.006, GREEN, cell=10, layer=LAYER["white"])
        print(f"  paint: green bike lanes {grn.area:.0f} m2", flush=True)

    hat = streets_islands.hatch(S, tb)
    if hat is not None and not hat.is_empty:
        drape(gm, hat, H, -CURB + 0.009, (238, 238, 232), cell=10, layer=LAYER["white"])
    top, strip, segs = streets_islands.islands(S, tb)
    if top is not None:
        drape(gm, top, H, 0.0, (255, 255, 255), cell=10, layer=LAYER["sidewalk"], uv_scale=5.0)
        drape(gm, strip, H, 0.004, (222, 214, 186), cell=10, layer=LAYER["white"])
        for a, b in segs:
            _kerb(gm, a, b, H)
        print(f"  paint: {len(segs)} island kerb segments", flush=True)


def _kerb(gm, a, b, H):
    za, zb = float(H.at(*a)), float(H.at(*b))
    pts = np.array([[a[0], a[1], za - CURB], [b[0], b[1], zb - CURB], [b[0], b[1], zb], [a[0], a[1], za]], np.float32)
    d = b - a
    L = np.hypot(*d)
    n = np.array([-d[1], d[0], 0]) / L  # road on the left
    gm.add(pts, np.array([[0, 2, 1], [0, 3, 2]], np.uint32), n, (180, 177, 170),
           uv=np.array([[0, 0], [L, 0], [L, 0.1], [0, 0.1]]), layer=LAYER["white"])
