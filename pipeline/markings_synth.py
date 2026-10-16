"""Langstrasse Nord: continuous yellow kerb-side lines (measured from SWISSIMAGE + photos: ~0.3 m wide, 2.95 m left/right of the OSM axis),
interrupted at side-street junctions (OSM junction nodes). Adds them to overrides/markings_langstrasse.json as "add_yellow".
usage: .venv/bin/python pipeline/markings_synth.py"""
import json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import LineString, Point
import sources

ROOT = Path(__file__).resolve().parent.parent
OVR = ROOT / "pipeline/overrides/markings_langstrasse.json"
AXIS_N = [(1104, 36), (1081, -6), (1043, -74), (979, -189), (954, -231)]  # Limmatplatz -> north portal of the Unterfuehrung
OFF, HALF_W, GAP_BEFORE, GAP_AFTER = 2.95, 0.15, 6.0, 5.0


def junctions(ln):
    d = json.load(open(ROOT / "data/raw/osm/part_highway_r.json")); els = d["elements"] if isinstance(d, dict) else d
    nodes = {e["id"]: Point(*sources.geo.to_local(e["lon"], e["lat"])) for e in els if e["type"] == "node"}
    out = []
    for e in els:
        t = e.get("tags") or {}
        if e["type"] != "way" or t.get("name") == "Langstrasse" or t.get("highway") in (None, "footway", "path", "steps", "service", "cycleway", "pedestrian"):
            continue
        for n in e["nodes"]:
            if n in nodes and ln.distance(nodes[n]) < 2.0:
                out.append(ln.project(nodes[n]))
    s = sorted(out); return [x for i, x in enumerate(s) if i == 0 or x - s[i - 1] > 6]


def main():
    ln = LineString(AXIS_N); L = ln.length; J = junctions(ln)
    print("axis", round(L), "m junctions at s =", [round(j) for j in J])
    iv = [(0.0, L)]
    for j in J:
        out = []
        for a, b in iv:
            if j + GAP_AFTER < a or j - GAP_BEFORE > b: out.append((a, b)); continue
            if a < j - GAP_BEFORE: out.append((a, j - GAP_BEFORE))
            if b > j + GAP_AFTER: out.append((j + GAP_AFTER, b))
        iv = out
    # keep clear of Limmatplatz (first 22 m) and the portal (last 6 m)
    iv = [(max(a, 22.0), min(b, L - 6.0)) for a, b in iv if min(b, L - 6.0) - max(a, 22.0) > 3]
    polys = []
    for sg in (1, -1):
        off = ln.offset_curve(sg * OFF)
        for a, b in iv:
            # project the axis interval to the offset curve (same arc parameter within a few cm on gentle bends)
            sub = shapely.ops.substring(off, a * off.length / L, b * off.length / L)
            if sub.geom_type == "LineString" and sub.length > 2:
                polys.append(sub.buffer(HALF_W, cap_style="flat"))
    # decals: bike pictograms in the kerb lanes after each junction (riding direction), painted "30" in the driving lanes (photos ls224/ls238)
    dec = []
    def at(s0):
        p, q = ln.interpolate(s0), ln.interpolate(min(L, s0 + 1.5)); tx, ty = q.x - p.x, q.y - p.y; n = np.hypot(tx, ty); return p, tx / n, ty / n
    def put(s0, lat, flip, kind):   # lat > 0 = left of axis direction
        p, tx, ty = at(s0); h = float(np.arctan2(tx, ty)) + (np.pi if flip else 0)
        dec.append([round(p.x - ty * lat, 2), round(p.y + tx * lat, 2), round(h, 3), kind])
    for j in J:
        if j > 20 and j < L - 10:
            put(min(L - 8, j + GAP_AFTER + 5), -3.6, False, 0)      # right lane travels along the axis direction (away from the junction)
            put(max(24, j - GAP_BEFORE - 5), 3.6, True, 0)          # left lane travels against it
    for s0 in (60, 170, 255):
        put(s0, -1.45, False, 6); put(s0 + 6, 1.45, True, 6)
    d = json.load(open(OVR)); d["decals"] = dec
    d["add_yellow"] = [[[round(x, 2), round(y, 2)] for x, y in g.exterior.coords] for g in polys]
    json.dump(d, open(OVR, "w")); print(len(polys), "line pieces,", round(sum(g.area for g in polys)), "m2")


if __name__ == "__main__":
    import shapely.ops  # noqa
    main()
