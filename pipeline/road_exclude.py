"""roads2: places where cars/bikes/objects must not be: open water without a deck, ground-level rail tracks without a deck.

water_ground(nodes, els, G)  AV water + OSM water (same rule as water.prepare), shapely geometry
track_ground(nodes, els)     ground-level railway=rail/light_rail/narrow_gauge lines buffered by the track gauge + ballast edge
decks(BR)                    footprint of all deck chains (bridges.bridge_ways result or cached chains), buffered by half width
bad_zone(...)                (water | tracks) minus decks, prepared
"""
import json
from pathlib import Path

import numpy as np
import shapely
import shapely.ops
from shapely.geometry import LineString, Polygon

TRACK_BUF = 2.3  # m each side of a track axis (rail bed ~ 3.2 m + 1 m margin; a vehicle centre never lies there)
WATER_MIN = 150.0
OVR = Path(__file__).resolve().parent / "overrides" / "rail_excl.json"


def water_ground(nodes, els, G):
    raw = [p for p in getattr(G["water"], "geoms", [G["water"]]) if p.area >= WATER_MIN]
    for e in els:
        t = e.get("tags") or {}
        if e["type"] == "way" and t.get("natural") == "water" and t.get("water") not in ("pond", "basin", "wastewater"):
            pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(pts) >= 4 and pts[0] == pts[-1]:
                p = Polygon(pts).buffer(0)
                if p.area >= 400:
                    raw.append(p)
    return shapely.union_all(raw).buffer(0) if raw else Polygon()


def track_ground(nodes, els):
    lines = []
    for e in els:
        t = e.get("tags") or {}
        if e["type"] != "way" or t.get("railway") not in ("rail", "light_rail", "narrow_gauge"):
            continue
        if t.get("bridge") not in (None, "no") or t.get("tunnel") not in (None, "no") or t.get("service") or t.get("usage") == "industrial":
            continue  # decks/tunnels carry no ground track (the viaduct is a deck, the road below it is legal); spurs/sidings are embedded in streets (Hardstrasse, Gerstenstrasse)
        if t.get("disused") or t.get("abandoned"):
            continue
        pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
        if len(pts) > 1:
            lines.append(LineString(pts))
    return shapely.union_all([ln.buffer(TRACK_BUF, cap_style="flat") for ln in lines]) if lines else Polygon()


def decks(BR):
    segs = []
    for b in BR:
        p = np.array(b["p"])[:, :2]
        if len(p) > 1 and b.get("kind") != "rail":  # rail decks carry rail, not road traffic
            segs.append(LineString(p).buffer(float(b["w"]) / 2 + 0.6))
    return shapely.union_all(segs) if segs else Polygon()


def bad_zone(nodes, els, G, BR):
    """(open water + ground tracks) minus road/foot/tram decks; manual releases in overrides/rail_excl.json ("allow": [[x0,y0,x1,y1], ...])."""
    z = shapely.union_all([water_ground(nodes, els, G), track_ground(nodes, els)])
    z = z.difference(decks(BR))
    try:
        for b in json.load(open(OVR)).get("allow", []):
            z = z.difference(shapely.box(*b))
    except FileNotFoundError:
        pass
    shapely.prepare(z)
    return z


def edge_in(zone, pts, min_len=2.0):
    ln = LineString(np.asarray(pts).reshape(-1, 2))
    return ln.length > 0 and ln.intersection(zone).length >= min_len


OBJ_KEYS = ("cars", "bikes", "racks", "scooters", "mopeds", "bins", "benches", "workers")
DATA = Path(__file__).resolve().parent.parent / "web" / "public" / "data"


def _extra_decks():
    out = []
    for f in ("station_decks", "hb_decks", "hb3_decks", "velotunnel_decks"):
        try:
            for d in json.load(open(DATA / f"{f}.json")).get("decks", []):
                if len(d["p"]) > 1 and d.get("kind") != "rail" and not d.get("sub"):
                    out.append(LineString(np.array(d["p"])[:, :2]).buffer(d["w"] / 2 + 0.3))
        except Exception:
            pass
    return out


def object_zone(W, BR):
    """Open water + railway land (railzone.json: AV Bahngebiet + OSM rails minus platforms/bridges) minus every deck: nothing
    that stands on the ground (bikes, racks, scooters, bins, workers, parked cars) may lie here."""
    parts = []
    if W is not None and not getattr(W, "empty", True):
        parts.append(W.poly)
    try:
        parts += [Polygon(z["r"][0], z["r"][1:]).buffer(0) for z in json.load(open(DATA / "railzone.json"))["zones"]]
    except Exception:
        pass
    z = shapely.union_all(parts) if parts else Polygon()
    z = z.difference(shapely.union_all([decks(BR)] + _extra_decks()))
    try:
        for b in json.load(open(OVR)).get("allow", []):
            z = z.difference(shapely.box(*b))
    except FileNotFoundError:
        pass
    shapely.prepare(z)
    return z


def filter_meta(meta, zone, tb=None):
    """Drop object rows ([x, y, ...]) lying in the zone; returns the number removed."""
    n = 0
    for k in OBJ_KEYS:
        rows = meta.get(k)
        if not rows or not isinstance(rows, list) or not isinstance(rows[0], list) or not isinstance(rows[0][0], (int, float)):
            continue
        xs = np.array([r[0] for r in rows]); ys = np.array([r[1] for r in rows])
        bad = shapely.contains_xy(zone, xs, ys)
        if bad.any():
            meta[k] = [r for r, b in zip(rows, bad) if not b]
            n += int(bad.sum())
    return n


def snap_to_roads(edges, roads, inset=0.8, reach=6.0, max_depth=3):
    """roads2: lane polylines follow the OSM axis (+ calibrated offset); where they leave the AV carriageway (junction corners,
    islands, widened lanes) the vertices are pulled to the nearest point of the carriageway shrunk by `inset`. Segments that still
    leave it get a midpoint (up to max_depth times). Returns (vertices moved, vertices added)."""
    from shapely.strtree import STRtree
    core = roads.buffer(-inset)
    parts = [p for p in getattr(core, "geoms", [core]) if not p.is_empty]
    if not parts:
        return 0, 0
    whole = shapely.union_all(parts)
    shapely.prepare(whole)
    tree = STRtree(parts)
    moved = added = 0

    def fix(pt):
        nonlocal moved
        i = tree.query_nearest(shapely.Point(pt), max_distance=reach)
        if not len(i):
            return pt
        q = shapely.ops.nearest_points(parts[int(i[0])], shapely.Point(pt))[0]
        moved += 1
        return (q.x, q.y)

    for e in edges:
        P = np.asarray(e["p"], float).reshape(-1, 2)
        if len(P) < 2:
            continue
        for _ in range(max_depth):
            ins = shapely.contains_xy(whole, P[:, 0], P[:, 1])
            ok_seg = ins[:-1] & ins[1:]
            segs = shapely.linestrings(np.stack([P[:-1], P[1:]], 1))
            # a segment between two inside points may still cut a corner out of the polygon
            cut = ok_seg & (shapely.length(shapely.intersection(whole, segs)) < shapely.length(segs) - 0.3)
            if ins.all() and not cut.any():
                break
            new = []
            for i in range(len(P)):
                new.append(P[i] if ins[i] else fix(P[i]))
                if i < len(P) - 1 and (cut[i] or not ok_seg[i]) and np.hypot(*(P[i + 1] - P[i])) > 2.5:
                    new.append((P[i] + P[i + 1]) / 2)
                    added += 1
            P = np.asarray(new, float)
        else:
            ins = shapely.contains_xy(whole, P[:, 0], P[:, 1])
            for i in np.where(~ins)[0]:
                P[i] = fix(P[i])
        e["p"] = np.round(P, 1).flatten().tolist()
    return moved, added
