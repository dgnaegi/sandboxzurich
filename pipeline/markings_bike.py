"""Painted bike lanes (Radstreifen): yellow lines + which sides really have one (research/markings_plaus/lines.md).
Findings (SWISSIMAGE 0.25 m, zones 1-3, ~105 measurable pieces; SSV Art. 74a Abs. 5 + Markierung 6.09: 'Radstreifen werden durch eine unterbrochene oder
ununterbrochene gelbe Linie abgegrenzt', unterbrochen = normal, ununterbrochen = Ausnahme):
 - the line along the strip is BROKEN in the ortho: stripe duty 0.2-0.5 on 96 % of the pieces (4 % > 0.8), period ~6 m (autocorrelation, 10 of 31 periodic pieces at 6.0-6.5 m,
   visual check Lagerstrasse / Hohlstrasse / Kasernenstrasse / Zollbruecke: ~2.5 m stripe, ~3.5 m gap). The game drew a continuous line everywhere.
 - official 'BOTH' on one carriageway of a split road (Badenerstrasse, Museumstrasse) drew a lane on the inner side too; OSM says cycleway:<side>=no there.
Constants: BIKE_DASH / BIKE_GAP (m), width 0.12 m (+-0.06, as before)."""
import shapely
from shapely.geometry import LineString

BIKE_DASH, BIKE_GAP, HALF_W = 2.5, 3.5, 0.06


def prune_lanes(S):
    """Drop an official bike-lane side on ONE-WAY ways when OSM maps that side explicitly as 'no' (the official Velonetz marks 'BOTH' on each carriageway of
    a split road). Idempotent; changes w['lanes'] (bike pictograms follow: props.decals reads it later)."""
    n = 0
    for w in S["ways"]:
        if not w.get("oneway") or "lanes" not in w or w.get("_lanes_pruned"):
            continue
        w["_lanes_pruned"] = True
        for side in ("left", "right"):
            if w["lanes"].get(side) and str(w["cyc"][side]).strip().lower() in ("no", "none"):
                w["lanes"][side] = []; n += 1
    return n


def lines(S, ML, streets, zg):
    """Yellow bike-lane line polygons: broken 2.5 m / 3.5 m along the strip, 1 m / 1 m on the approach to a junction (as before); cut at zebras / stop lines (zg)."""
    out = []
    for w in S["ways"]:
        if w["hw"] == "service" or w["zone"] in ("beg", "fuss"):
            continue
        ln, L = ML.way_line(S, w), w["line"].length
        for side, solid, broken in streets.bike_lane_pieces(w):
            sgn = 1 if side == "left" else -1
            off = ln.offset_curve(sgn * (w["w"] / 2 - 1.5))
            if off.is_empty or off.geom_type != "LineString":
                continue
            for a, b in streets._minus(solid, zg.get(id(w), [])):
                out += [streets._sub(off, d0, d1, L).buffer(HALF_W, cap_style="flat") for d0, d1 in ML.fit_dashes(a, b, BIKE_DASH, BIKE_GAP)]
            for a, b in broken:
                out += [streets._sub(off, d0, d1, L).buffer(HALF_W, cap_style="flat") for d0, d1 in ML.fit_dashes(a, b, 1.0, 1.0)]
    return out
