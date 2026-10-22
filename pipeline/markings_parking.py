"""Street parking (OGD Stadt Zuerich, CC0) as a side test for the painted bike lanes: a Velostreifen on a street with kerbside parking lies between the
parked cars and the traffic lane (kerb + 2.0 m bay + 1.5 m lane), not 1.5 m from the kerb (ortho check research/markings_plaus/lines.md).
API: has_parking(way_line, half_w, side, a, b) -> bool (>= 1 parking space per 12 m of the piece within [half_w - 1.2, half_w + 3.0] m of the carriageway centre
on that side; side 'left' = left of the way direction)."""
import json
from pathlib import Path
import numpy as np
import shapely
from shapely import STRtree

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/stadtzh/geo_oeffentlich_zugaengliche_strassenparkplaetze_ogd__view_pp_ogd.geojson"
CACHE = ROOT / "data/build/parking_local.npy"
_P = {}


def points():
    if "p" not in _P:
        if CACHE.exists():
            a = np.load(CACHE)
        else:
            import sources
            c = np.array([f["geometry"]["coordinates"][:2] for f in json.load(open(RAW))["features"] if f.get("geometry")], dtype=np.float64)
            x, y = sources.geo.to_local(c[:, 0], c[:, 1]) if np.abs(c[:, 0]).max() < 1000 else (c[:, 0] - sources.geo.ORIGIN_E, c[:, 1] - sources.geo.ORIGIN_N)
            a = np.c_[x, y]; np.save(CACHE, a)
        _P["p"] = a; _P["t"] = STRtree(shapely.points(a))
    return _P["p"], _P["t"]


def side_counts(line, a, b, half_w, side, lo=-1.2, hi=3.0):
    """parking spaces beside the way piece [a, b] (m along the way) on `side`, lateral distance from the centre in [half_w + lo, half_w + hi]"""
    a_, t = points()
    seg = shapely.line_interpolate_point(line, np.linspace(a, b, max(2, int((b - a) / 2))))
    box = shapely.union_all(shapely.buffer(seg, half_w + hi + 1.0)) if len(seg) else None
    idx = t.query(box) if box is not None else []
    n = 0
    for i in idx:
        p = shapely.points(a_[i])
        s = line.project(p)
        if not (a - 1 <= s <= b + 1):
            continue
        q = line.interpolate(s)
        q2 = line.interpolate(min(s + 1.0, line.length)); q1 = line.interpolate(max(s - 1.0, 0.0))
        d = np.array([q2.x - q1.x, q2.y - q1.y]); d /= (np.hypot(*d) + 1e-9)
        lat = (a_[i][0] - q.x) * (-d[1]) + (a_[i][1] - q.y) * d[0]       # + = left of the way direction
        if (lat > 0) == (side == "left") and half_w + lo <= abs(lat) <= half_w + hi:
            n += 1
    return n


def has_parking(line, half_w, side, a, b):
    return side_counts(line, a, b, half_w, side) >= max(1, (b - a) / 12.0)
