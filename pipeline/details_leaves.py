"""Autumn leaf litter under deciduous trees (game season = October, see research/fidelity.md S8).
Input: tree rows [x, y, z, cls, crown, height, base, flags, heading] (trees_dims.tree_row). Output: groups
[x, y, z, rot_deg, colour_index] (3 leaves each, drawn flat by web/src/world/details.ts), denser near the trunk,
lying on the road surface (z - curb) when the spot is on the carriageway, never inside buildings."""
import math

import numpy as np
from shapely.geometry import Point

from styles import h32

CONIFER, COLUMNAR, PINE = 8, 9, 14
# colour index per class: 0 brown/ochre, 1 yellow, 2 orange-red
COL = {2: 1, 4: 1, 5: 2, 6: 0, 7: 1, 9: 1, 11: 1, 12: 0, 13: 0, 10: 1}


def rows(trees, H, roads, inside_any, curb, per_tree=9, cap=500):
    out = []
    for t in trees:
        x, y, z, cls, crown = t[0], t[1], t[2], int(t[3]), t[4]
        if cls in (CONIFER, PINE):
            continue
        rnd = np.random.default_rng(h32(f"lf{x:.1f}{y:.1f}"))
        n = per_tree + int(min(crown, 12) * 0.5)
        r = max(1.2, min(crown, 14) * 0.55)
        for _ in range(n):
            d = abs(rnd.normal(0, r * 0.55))
            a = rnd.uniform(0, 2 * math.pi)
            px, py = x + d * math.cos(a), y + d * math.sin(a)
            if inside_any(px, py):
                continue
            pz = float(H.at(px, py)) - (curb if roads.contains(Point(px, py)) else 0) + 0.02
            out.append([round(px, 1), round(py, 1), round(pz, 2), int(rnd.uniform(0, 180)),
                        COL.get(cls, 0) if rnd.random() < 0.7 else int(rnd.integers(0, 3))])
            if len(out) >= cap:
                return out
    return out
