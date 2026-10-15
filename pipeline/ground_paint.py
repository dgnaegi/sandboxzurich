"""Extra coloured ground paint per tile (red bike crossings, hatched restricted areas, tram stop islands …).
Called at the end of build_testarea._ground_tile. Owned by the streets agent; keep it fast (per tile)."""
import os

import numpy as np

import streets_islands
import streets_ortho
from mesh import drape
from mesh import Mesh  # noqa: F401
from styles import LAYER

CURB = 0.12
RED = (178, 64, 52)


def paint(gm, S, tb, H):
    roads = S["roads"].intersection(tb)
    dbg = None
    if os.environ.get("SBZ_PAINTDBG"):
        k = "%d_%d" % (round(tb.bounds[0] / 200), round(tb.bounds[1] / 200))
        dbg = f"/tmp/paint_{k}.png"
    red = streets_ortho.red_surfaces(tb, roads, dbg)
    if red is not None and not red.is_empty:
        drape(gm, red, H, -CURB + 0.005, RED, cell=10, layer=LAYER["white"])
        print(f"  paint: red surfaces {red.area:.0f} m2", flush=True)

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
