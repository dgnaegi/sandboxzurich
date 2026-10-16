"""Sparse facade details on street-facing walls without shops (segs from facade.add_building): cellar light-well gratings
(Lichtschächte, common at the foot of Zürich Altbauten) and rare satellite dishes. No data source: density is a calibration
guess from photos (research/details.md), deterministic by hash. Rows like details_osm objs: [type, x, y, z, heading, a, b, c].
Off by default (no data source, realism rule); SBZ_FACADE_GUESS=1 turns it on."""
import math
import os

from shapely.geometry import Point

from styles import h32


def rows(segs, tb, H, roads):
    out = []
    if os.environ.get("SBZ_FACADE_GUESS") != "1":
        return out
    for s in segs:
        if not s.get("blank") or s["w"] < 4.5 or not tb.contains(Point(s["x"], s["y"])):
            continue
        k = h32("fc" + s["bid"] + str(round(s["x"])) + str(round(s["y"])))
        nx, ny = s["ty"], -s["tx"]  # outward normal
        h = math.atan2(s["ty"], s["tx"])
        if k % 100 < 9:  # grating near the wall foot, shifted along the wall
            off = ((k >> 8) % 100 / 100 - 0.5) * (s["w"] - 2.4)
            x, y = s["x"] + s["tx"] * off + nx * 0.3, s["y"] + s["ty"] * off + ny * 0.3
            if not roads.contains(Point(x, y)):
                out.append(["cellar", round(x, 2), round(y, 2), round(float(H.at(x, y)), 2), round(h, 3), 0, 0, 0])
        if (k >> 12) % 100 < 2:  # satellite dish high on the wall
            off = ((k >> 20) % 100 / 100 - 0.5) * (s["w"] - 1.5)
            x, y = s["x"] + s["tx"] * off + nx * 0.15, s["y"] + s["ty"] * off + ny * 0.15
            out.append(["dish", round(x, 2), round(y, 2), round(float(H.at(x, y)), 2), round(h, 3), 4 + (k >> 4) % 6, 0, 0])
    return out
