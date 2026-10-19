"""Tram track ground geometry: rails, flangeways, bed and the road surface they sit in (used by build_testarea._ground_base).
Zurich street-running track = grooved rails flush in the asphalt (head <= ~2 cm above the carriageway). Own trassee (not road, not plaza):
a low ballast bed level with its surroundings, no kerb. Rationale / measurements: research/tram_tracks.md.
SBZ_TRAM_OLD=1 reproduces the pre-fix geometry (for audit_tramtracks.py before/after)."""
import os
import shapely
from mesh import drape
from styles import LAYER

OLD = bool(os.environ.get("SBZ_TRAM_OLD"))
CURB = 0.12
HEAD_ROAD, HEAD_OFF, BED_OFF = 0.012, 0.025, 0.012  # rail head above the surface it sits in / above the bed / bed above its surroundings
BASE = {"road": -CURB, "plaza": 0.0, "park": 0.01, "rail": -0.08, "walk": 0.0}


def _poly(g):
    """Polygonal parts only (overlays of snapped inputs can return GeometryCollections / lines)."""
    parts = [x for x in shapely.get_parts(g) if x.geom_type in ("Polygon", "MultiPolygon") and not x.is_empty]
    return shapely.union_all(parts) if parts else shapely.Polygon()


def _op(a, b, op):
    """Robust overlay: retry with 1 cm snapped inputs when GEOS fails (same trick as build_testarea.ground_tile)."""
    if a.is_empty or b is None:
        return a
    try:
        return _poly(getattr(a, op)(b))
    except shapely.errors.GEOSException:
        a2, b2 = shapely.set_precision(a.buffer(0), 0.01), shapely.set_precision(b.buffer(0), 0.01)
        return _poly(getattr(a2, op)(b2))


def geometry(tram):
    rails = shapely.union_all([ln.offset_curve(o).buffer(0.035) for ln in tram for o in (-0.5, 0.5)])
    grooves = shapely.union_all([ln.offset_curve(o).buffer(0.022) for ln in tram for o in (-0.44, 0.44)])
    bed = shapely.union_all([ln.buffer(1.4, cap_style="flat") for ln in tram])
    return tuple(shapely.set_precision(g, 0.005) for g in (rails, grooves, bed))


def merge_into_roads(roads, plaza, tram):
    """Street-running track belongs to the carriageway: the strip between carriageway and track (AV 'Bahngebiet' sliver, gap between two
    road polygons) would otherwise leave kerb faces on both sides of the rails (the 'little walls'). Track crossing a plaza edge is merged as well, otherwise a kerb runs along the rails."""
    if OLD or not tram:
        return roads
    zone = shapely.union_all([ln.buffer(3.2) for ln in tram])
    bed = shapely.union_all([ln.buffer(1.45, cap_style="flat") for ln in tram])
    loc = shapely.union_all([roads.intersection(zone), bed.intersection(roads.buffer(3.0))]).buffer(1.0, quad_segs=4).buffer(-1.0, quad_segs=4)
    loc = loc.intersection(zone)  # plaza cobbles under the track become carriageway too (build removes them from S['plaza'])
    return shapely.set_precision(shapely.union_all([roads, loc]).buffer(0), 0.01)


def base_name(p, S):
    if S["roads"].contains(p):
        return "road"
    if S["plaza"].contains(p):
        return "plaza"
    if S["parks"].contains(p):
        return "park"
    if S.get("av_rail") is not None and S["av_rail"].contains(p):
        return "rail"
    return "walk"


def head_z(h, inroad, p, S):
    if OLD:
        return h - CURB + 0.012 if inroad else h + 0.07
    b = base_name(p, S)
    return h + BASE[b] + (HEAD_ROAD if b == "road" else (HEAD_OFF + BED_OFF if b in ("walk", "rail") else HEAD_OFF))


def bed_z(h, p, S):
    return h + 0.015 if OLD else h + BASE[base_name(p, S)] + BED_OFF


def paint(gm, S, tb, H, rails, grooves, bed):
    roads = S["roads"]
    off = _op(_op(bed, tb, 'intersection'), roads, 'difference')
    if OLD:
        drape(gm, off, H, 0.015, (190, 185, 175), layer=LAYER["roof_flat"], uv_scale=2)
        drape(gm, grooves.intersection(roads).intersection(tb), H, -CURB + 0.011, (28, 28, 30), cell=10, layer=LAYER["white"])
        drape(gm, rails.intersection(roads).intersection(tb), H, -CURB + 0.012, (175, 175, 178), cell=10, layer=LAYER["white"])
        drape(gm, rails.difference(roads).intersection(tb), H, 0.07, (120, 118, 116), cell=10, layer=LAYER["white"])
        return
    plaza, parks = S["plaza"], S["parks"]
    ball = _op(_op(off, plaza, 'difference'), parks, 'difference')  # ballast only on own trassee (not plaza cobbles, not lawn)
    rl = S.get("av_rail")
    for g, lift in ((_op(ball, rl, 'difference'), BED_OFF), (_op(ball, rl, 'intersection') if rl is not None else None, BASE["rail"] + BED_OFF)):
        if g is not None and not g.is_empty:
            drape(gm, g, H, lift, (190, 185, 175), cell=4, layer=LAYER["roof_flat"], uv_scale=2)
    for g, lift, col in ((grooves, -CURB + 0.011, (28, 28, 30)), (rails, -CURB + HEAD_ROAD, (175, 175, 178))):
        drape(gm, _op(_op(g, tb, 'intersection'), roads, 'intersection'), H, lift, col, cell=4, layer=LAYER["white"])
    r_off = _op(_op(rails, tb, 'intersection'), roads, 'difference')
    r_rest = r_off
    for zone, base in ((plaza, 0.0), (parks, 0.01)):  # rails on cobbles / lawn: flush, 2.5 cm
        drape(gm, _op(r_off, zone, 'intersection'), H, base + HEAD_OFF, (120, 118, 116), cell=4, layer=LAYER["white"])
        r_rest = _op(r_rest, zone, 'difference')
    if rl is not None:
        drape(gm, _op(r_rest, rl, 'intersection'), H, BASE["rail"] + BED_OFF + HEAD_OFF, (120, 118, 116), cell=4, layer=LAYER["white"])
        r_rest = _op(r_rest, rl, 'difference')
    drape(gm, r_rest, H, BED_OFF + HEAD_OFF, (120, 118, 116), cell=4, layer=LAYER["white"])
