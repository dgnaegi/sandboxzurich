"""Langstrasse marking override (hook in build_testarea after streets.markings). Replaces the built yellow markings inside the measured
region by the yellow markings measured from SWISSIMAGE (markings_ortho.py -> overrides/markings_langstrasse.json), clipped to the
carriageway; adds hand corrections (add_white / add_yellow / cut polygons, local metres)."""
import json
from pathlib import Path
import shapely
from shapely.geometry import Polygon

F = Path(__file__).resolve().parent / "overrides" / "markings_langstrasse.json"
_C = {}


def _load():
    if "d" not in _C:
        d = json.load(open(F)) if F.exists() else None
        if d:
            P = lambda rs: [Polygon(r).buffer(0) for r in rs]
            d["_region"] = shapely.union_all(P(d["region"])) if d["region"] else None
            d["_yellow"] = shapely.union_all(P(d["yellow"])) if d["yellow"] else None
            for k in ("add_white", "add_yellow", "cut"):
                d["_" + k] = shapely.union_all(P(d[k])) if d.get(k) else None
        _C["d"] = d
    return _C["d"]


def _zones():
    """Per-zone overrides overrides/markings_z<N>.json (add_yellow / add_white / cut polygons, decals [x, y, heading, kind]); additive."""
    if "z" not in _C:
        z = {k: [] for k in ("add_yellow", "add_white", "cut", "decals")}
        for f in sorted(F.parent.glob("markings_z[0-9]*.json")):
            j = json.load(open(f))
            for k in z:
                z[k] += j.get(k, [])
        P = lambda rs: shapely.union_all([Polygon(r).buffer(0) for r in rs]) if rs else None
        _C["z"] = {**{"_" + k: P(z[k]) for k in ("add_yellow", "add_white", "cut")}, "decals": z["decals"]}
    return _C["z"]


def apply(S, white, yellow):
    white, yellow = _apply_langa(S, white, yellow)
    z = _zones()
    if z["_add_yellow"] is not None:
        yellow = shapely.union_all([yellow, z["_add_yellow"].intersection(S["roads"].buffer(0.3))])
    if z["_add_white"] is not None:
        white = shapely.union_all([white, z["_add_white"].intersection(S["roads"].buffer(0.3))])
    if z["_cut"] is not None:
        white, yellow = white.difference(z["_cut"]), yellow.difference(z["_cut"])
    return white, yellow


def _apply_langa(S, white, yellow):
    d = _load()
    if not d or d["_region"] is None:
        return white, yellow
    reg = d["_region"]
    meas = d["_yellow"].intersection(S["roads"].buffer(0.3).intersection(reg))
    parts = [g for g in shapely.get_parts(meas) if g.geom_type == "Polygon" and g.area > 0.12]
    keep = [g for g in parts if g.minimum_rotated_rectangle.length / 2 > 1.0]  # drop specks
    new = shapely.union_all(keep) if keep else None
    y = yellow  # built markings stay (OSM crossing nodes); measured ones are added
    if new is not None:
        y = shapely.union_all([y, new])
    if d["_add_yellow"] is not None:
        y = shapely.union_all([y, d["_add_yellow"]])
    if d["_add_white"] is not None:
        white = shapely.union_all([white, d["_add_white"]])
    if d["_cut"] is not None:
        white, y = white.difference(d["_cut"]), y.difference(d["_cut"])
    return white, y


def decals(rows, tb, H, curb=0.12):
    """Add the measured/observed road decals (bike pictograms, painted 30) inside the tile: rows are [x, y, z, heading, kind]."""
    d = _load() or {}
    from shapely.geometry import Point
    out = list(rows)
    for x, y, h, k in d.get("decals", []) + _zones()["decals"]:
        if tb.contains(Point(x, y)):
            out.append([x, y, round(float(H.at(x, y)) - curb + 0.012, 3), h, k])
    return out
