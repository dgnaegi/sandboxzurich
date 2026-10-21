"""Street furniture must not stand on the carriageway where cars drive (user 2026-10-21: tables etc. on the road).

zone(S, BR)     carriageway (S['roads'], incl. tram bed) minus squares, pedestrian zones / Begegnungszonen (OGD) and bridge decks
set_zone(g)     build-time global (build_testarea sets it once before the tile pool forks); snap(x, y) uses it
snap(x, y)      (x, y) unchanged when off the zone, the nearest kerb point + gap when within max_shift, else None (drop)
fix_meta(meta)  safety net over all tile object lists (benches, bins, bikes, racks, ... details/places/yards rows)
Exempt (real on-road objects): signals/signs/lamps/masts, bollards, gates, construction sites (sites/cranes/workers/construction),
VBZ stop equipment (catalog H*/M*) and scenes with a fixed event site.
Cache for standalone scripts (catalog/scenes): data/cache/props_road_zone.wkb, written by `python3 pipeline/props_road.py`."""
import sys
from pathlib import Path

import numpy as np
import shapely
import shapely.ops
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "props_road_zone.wkb"
sys.path.insert(0, str(Path(__file__).resolve().parent))

_Z = {"g": None, "edge": None}
GAP = 0.5
MAX_SHIFT = 4.0

# tile list keys -> index of x ; (parent, key) -> index of x. z stays: H.at is the pavement level (roads are sunk by CURB)
LIST_KEYS = {"benches": 0, "bins": 0, "fountains": 0, "hydrants": 0, "pingpong": 0, "scooters": 0, "mopeds": 0, "bikes": 0,
             "racks": 0, "playground": 0}
SUB_KEYS = {("details", "objs"): 1, ("places", "objs"): 1, ("places", "seats"): 0, ("yards", "props"): 1}
KEEP_TYPES = {"gate", "guidepost", "column"}   # barrier=gate across a road, hiking signs, columns: real on-road objects


def zone(S, BR=None):
    import road_exclude
    import streets_rules
    ex = [g for g in (S.get("plaza"), streets_rules.rules().zones.get("fuss"), streets_rules.rules().zones.get("beg")) if g is not None and not g.is_empty]
    g = S["roads"]
    if ex:
        g = g.difference(shapely.union_all(ex))
    if BR:
        g = g.difference(shapely.union_all([road_exclude.decks(BR)] + road_exclude._extra_decks()))
    return g


def set_zone(g):
    if g is None:
        _Z["g"] = _Z["edge"] = None
        return
    shapely.prepare(g)
    _Z["g"], _Z["edge"] = g, g.boundary


def load_cached():
    if _Z["g"] is None and CACHE.exists():
        set_zone(shapely.from_wkb(CACHE.read_bytes()))
    return _Z["g"]


def on_road(x, y):
    g = _Z["g"]
    return g is not None and g.contains(Point(x, y))


def snap(x, y, max_shift=MAX_SHIFT, gap=GAP):
    g = _Z["g"]
    if g is None:
        return x, y
    p = Point(x, y)
    if not g.contains(p):
        return x, y
    from shapely.ops import nearest_points
    q = nearest_points(_Z["edge"], p)[0]
    d = q.distance(p)
    if d > max_shift:
        return None
    ux, uy = (q.x - x) / max(d, 1e-6), (q.y - y) / max(d, 1e-6)
    n = Point(q.x + ux * gap, q.y + uy * gap)
    if g.contains(n):
        return None
    return round(n.x, 2), round(n.y, 2)


def fix_meta(meta):
    """Snap / drop rows of the object lists lying on the zone. Returns {key: (moved, dropped)}."""
    stat = {}
    todo = [(None, k, i) for k, i in LIST_KEYS.items()] + [(a, b, i) for (a, b), i in SUB_KEYS.items()]
    for par, k, i in todo:
        rows = (meta.get(par) or {}).get(k) if par else meta.get(k)
        if not rows or not isinstance(rows, list):
            continue
        out, mv, dr = [], 0, 0
        for r in rows:
            if par and isinstance(r[0], str) and r[0] in KEEP_TYPES:
                out.append(r); continue
            if not on_road(r[i], r[i + 1]):
                out.append(r); continue
            q = snap(r[i], r[i + 1])
            if q is None:
                dr += 1; continue
            r = list(r); r[i], r[i + 1] = q
            out.append(r); mv += 1
        if mv or dr:
            stat[f"{par + '.' if par else ''}{k}"] = (mv, dr)
            if par:
                meta[par][k] = out
            else:
                meta[k] = out
    return stat


# ---- object-object overlaps: nothing stands inside a fountain basin or the Velotunnel mouth, nor furniture inside a building ----
BASIN_R = {"tellerbrunnen": None, "dfount": 0.9, "rfount": 1.6, "basin": 2.2, "hundebrunnen": 0.8, "bucket": 0.7}   # None = param a + margin
CATALOG_R = 1.9          # catalog fountains (V*), kind 0
FOUNT_TYPES = ("brunnen", "fount", "basin", "bucket")
KEEP_PLACE = ("brunnen", "fount", "basin", "bucket", "bowl", "sculpt", "pyramid", "monument", "granitepyr", "kerb", "generic", "pavilion",
              "kiosk", "stall", "shelter", "container", "flag", "namesign", "taxisign", "clockpost", "cabinet", "grill", "sandbox", "pingpong")
_K = {"discs": None, "tunnel": None}
MOUTH = 32.0             # m of the Velotunnel ramp counted as the portal cut
DATA = ROOT / "web" / "public" / "data"


def keepouts():
    """(fountain discs geometry, tunnel-mouth polygon): from places_detail overrides (basin objects), catalog fountains, velotunnel
    decks and pipeline/overrides/props_keepout.json ({"discs": [[x, y, r, name]], "polys": [[[x, y]..]]})."""
    import json
    if _K["discs"] is not None:
        return _K["discs"], _K["tunnel"]
    discs, polys = [], []
    try:
        import places_detail
        for pl in places_detail.load():
            for o in places_detail._objects(pl):
                t = o["t"]
                if t in BASIN_R:
                    r = (float(o.get("a", 6)) + 0.7) if BASIN_R[t] is None else BASIN_R[t]
                    discs.append(Point(pl["center"][0] + o["p"][0], pl["center"][1] + o["p"][1]).buffer(r, 32))
    except Exception as e:   # noqa: BLE001
        print("props_road: places_detail keepouts skipped:", e)
    try:
        for o in json.load(open(DATA / "catalog.json"))["o"]:
            if o[6] == 0:
                discs.append(Point(o[1], o[2]).buffer(CATALOG_R, 16))
    except Exception:   # noqa: BLE001
        pass
    try:
        ov = json.load(open(Path(__file__).resolve().parent / "overrides" / "props_keepout.json"))
        discs += [Point(d[0], d[1]).buffer(d[2], 32) for d in ov.get("discs", [])]
        polys += [shapely.Polygon(p_) for p_ in ov.get("polys", [])]
    except FileNotFoundError:
        pass
    try:   # Velotunnel mouth: first MOUTH m of every ramp deck, objects there stand on the cycle path or in the cut
        from shapely.geometry import LineString
        for d in json.load(open(DATA / "velotunnel_decks.json"))["decks"]:
            ln = LineString([(q[0], q[1]) for q in d["p"]])
            for a, b in ((0, MOUTH), (max(ln.length - MOUTH, 0), ln.length)):
                seg = shapely.ops.substring(ln, a, b)
                polys.append(seg.buffer(d["w"] / 2 + 1.2, cap_style="flat"))
    except Exception:   # noqa: BLE001
        pass
    _K["discs"] = shapely.union_all(discs) if discs else Point(0, 0).buffer(0)
    _K["tunnel"] = shapely.union_all(polys) if polys else Point(0, 0).buffer(0)
    shapely.prepare(_K["discs"]); shapely.prepare(_K["tunnel"])
    return _K["discs"], _K["tunnel"]


def _push(g, x, y, max_shift=9.0, gap=0.5):
    from shapely.ops import nearest_points
    p = Point(x, y)
    q = nearest_points(g.boundary, p)[0]
    d = q.distance(p)
    if d > max_shift:
        return None
    ux, uy = (q.x - x) / max(d, 1e-6), (q.y - y) / max(d, 1e-6)
    n = Point(q.x + ux * gap, q.y + uy * gap)
    return None if g.contains(n) else (round(n.x, 2), round(n.y, 2))


GROUND = ("benches", "bins", "racks", "mopeds", "scooters")   # not bikes: wall-leaning bikes sit on the facade line
STAND = GROUND + ("bikes", "hydrants", "pingpong", "lamps", "masts", "trees")


def fix_overlaps(meta, inside_building=None):
    """Furniture/lamps/trees inside a fountain basin -> pushed out of it; inside the Velotunnel mouth -> dropped; ground furniture
    inside a building footprint -> dropped. Fountain-like and fixed place objects are never touched. Returns stats."""
    discs, tun = keepouts()
    stat = {}

    def one(k, rows, i, typed):
        out, mv, dr = [], 0, 0
        for r in rows:
            x, y = r[i], r[i + 1]
            if typed and (not isinstance(r[0], str) or any(t in r[0] for t in KEEP_PLACE) or r[0] in KEEP_TYPES):
                out.append(r); continue
            if tun.contains(Point(x, y)) or (inside_building and k in GROUND and inside_building(x, y)):
                dr += 1; continue
            if discs.contains(Point(x, y)):
                q = _push(discs, x, y)
                if q is None or tun.contains(Point(*q)) or (inside_building and k in GROUND and inside_building(*q)):
                    dr += 1; continue
                r = list(r); r[i], r[i + 1] = q; mv += 1
            out.append(r)
        if mv or dr:
            stat[k] = (mv, dr)
        return out

    for k in STAND:
        if meta.get(k):
            meta[k] = one(k, meta[k], 0, False)
    for par, k, i in (("details", "objs", 1), ("places", "objs", 1), ("yards", "props", 1)):
        if (meta.get(par) or {}).get(k):
            meta[par][k] = one(f"{par}.{k}", meta[par][k], i, True)
    return stat


def main():
    import bridges
    import sources
    import streets
    from config import AREA
    nodes, els = sources.osm()
    S = streets.parse(nodes, els)
    BR = bridges.bridge_ways(nodes, els, AREA)
    g = zone(S, BR)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(shapely.to_wkb(g))
    print("zone cached", CACHE, round(g.area), "m2")


if __name__ == "__main__":
    main()
