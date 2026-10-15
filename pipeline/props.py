"""Placed objects for a tile: parked cars, suspended street lamps, signs, walk paths, road mask."""
import base64

import numpy as np
import shapely
from shapely.geometry import Point
from shapely.strtree import STRtree

import shopfronts_v3
from styles import h32

PARK_HW = {"residential", "tertiary", "unclassified"}


def parked_cars(S, tram_lines, tb):
    """Cars along both kerbs of residential/tertiary streets without tram. Returns list of [x, y, heading, colour]."""
    tram_tree = STRtree(tram_lines) if tram_lines else None
    others = STRtree([w["line"] for w in S["ways"]])
    out = []
    for wi, w in enumerate(S["ways"]):
        if w["hw"] not in PARK_HW or w["w"] < 7 or w["line"].length < 30:
            continue
        if tram_tree is not None and len(tram_tree.query(w["line"].buffer(2), predicate="intersects")):
            continue
        for sgn in (1, -1):
            off = w["line"].offset_curve(sgn * (w["w"] / 2 - 1.1))
            if off.is_empty or off.geom_type != "LineString":
                continue
            for s in np.arange(12, off.length - 12, 5.6):
                p = off.interpolate(s)
                if not tb.contains(p):
                    continue
                key = h32(f"{wi}{sgn}{s:.0f}")
                if key % 100 > 62:
                    continue
                # skip junctions: close to another street's centreline
                near = others.query(p.buffer(0.1), predicate="dwithin", distance=4.5)
                if any(S["ways"][j]["line"] is not w["line"] and S["ways"][j]["line"].distance(p) < S["ways"][j]["w"] / 2 + 1
                       for j in near):
                    continue
                if any(Point(c).distance(p) < 8 for c, _, _ in S["crossings"]):
                    continue
                a, b = off.interpolate(s - 1), off.interpolate(s + 1)
                heading = float(np.arctan2(b.x - a.x, b.y - a.y)) + (np.pi if (key >> 8) % 2 else 0)
                out.append([round(p.x, 2), round(p.y, 2), round(heading, 3), key % 12])
    return out


def car_collider(x, y, heading):
    d = np.array([np.sin(heading), np.cos(heading)])
    n = np.array([d[1], -d[0]])
    c = np.array([x, y])
    return [list(np.round(c + d * sl * 2.15 + n * sw * 0.9, 2)) for sl, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def lamps(S, tb):
    """Zürich-style lamps hanging on a cable over the street centre, every ~32 m. [x, y, heading, span]."""
    out = []
    for w in S["ways"]:
        if w["w"] < 6.5 or w["hw"] == "service":
            continue
        ln = w["line"]
        for s in np.arange(10, ln.length - 5, 32):
            p = ln.interpolate(s)
            if not tb.contains(p):
                continue
            a, b = ln.interpolate(s - 1), ln.interpolate(s + 1)
            out.append([round(p.x, 2), round(p.y, 2), round(float(np.arctan2(b.x - a.x, b.y - a.y)), 3), round(w["w"] + 6, 1)])
    return out


def signs(S, segs, tb):
    """Attach each named POI to the nearest shop facade segment (one sign per segment)."""
    if not segs:
        return []
    pts = shapely.points([(s["x"], s["y"]) for s in segs])
    tree = STRtree(pts)
    used, out = set(), []
    for poi in S["pois"]:
        p = Point(poi["x"], poi["y"])
        if not tb.contains(p):
            continue
        cand = sorted(tree.query(p.buffer(25)), key=lambda i: pts[i].distance(p))
        i = next((i for i in cand if i not in used), None)
        if i is None:
            continue
        used.add(i)
        s = segs[i]
        out.append({"x": round(s["x"], 2), "y": round(s["y"], 2), "z": round(s["z"], 2), "tx": round(s["tx"], 4),
                    "ty": round(s["ty"], 4), "w": round(min(s["w"] - 0.6, 9), 2), "name": poi["name"],
                    "kind": poi["kind"], "osm": poi["osm"]})
        d = pavement_depth(S, out[-1])
        if d is not None:
            out[-1]["pd"] = d
        v = shopfronts_v3.notes_for(poi)
        if v:
            out[-1]["v"] = v
    return out


def pavement_depth(S, sg):
    """Metres of paved pavement in front of the facade strip: grows until a carriageway or a lawn/park is hit (None if > 9)."""
    free = S.get("_sf_blocked")
    if free is None:
        free = S["_sf_blocked"] = shapely.union_all([g for g in (S["roads"], S.get("parks")) if g is not None])
        shapely.prepare(free)
    nx, ny, hw = sg["ty"], -sg["tx"], min(sg["w"] / 2, 2.5)
    for d in np.arange(0.5, 9.01, 0.5):
        strip = shapely.geometry.Polygon([(sg["x"] + sg["tx"] * u + nx * v, sg["y"] + sg["ty"] * u + ny * v)
                                          for u, v in ((-hw, 0.35), (hw, 0.35), (hw, d), (-hw, d))])
        if free.intersects(strip):
            return round(float(d) - 0.5, 1)
    return None


def walk_paths(roads, plaza, tb):
    """Sidewalk centrelines ~1.7 m outside the kerb, clipped to the tile."""
    ring = roads.buffer(1.7).boundary.intersection(tb).difference(plaza)
    out = []
    for g in getattr(ring, "geoms", [ring]):
        if g.geom_type == "LineString" and g.length > 15:
            out.append(np.round(np.asarray(g.simplify(0.5).coords), 1).tolist())
    return out


def road_mask(roads, tb, res=1.0):
    """1 bit per res x res cell: 1 = lowered carriageway. Base64, row-major from (x0, y0)."""
    x0, y0, x1, y1 = tb.bounds
    xs = np.arange(x0 + res / 2, x1, res)
    ys = np.arange(y0 + res / 2, y1, res)
    gx, gy = np.meshgrid(xs, ys)
    inside = shapely.contains_xy(roads, gx.ravel(), gy.ravel())
    return base64.b64encode(np.packbits(inside.astype(np.uint8)).tobytes()).decode(), len(xs)


def tram_wires(tram_lines, tb, H, height=5.7):
    """Overhead contact wire above every track plus span wires every 30 m. Polylines [[x, y, z], ...]."""
    out = []
    for ln in tram_lines:
        part = ln.intersection(tb)
        for g in getattr(part, "geoms", [part]):
            if g.geom_type != "LineString" or g.length < 1:
                continue
            pts = [g.interpolate(s) for s in np.append(np.arange(0, g.length, 8), g.length)]
            out.append([[round(p.x, 2), round(p.y, 2), round(float(H.at(p.x, p.y)) - 0.12 + height, 2)] for p in pts])
            for s in np.arange(15, g.length, 30):
                p, q = g.interpolate(s), g.interpolate(min(g.length, s + 1))
                d = np.array([q.x - p.x, q.y - p.y])
                d /= np.linalg.norm(d) + 1e-9
                n = np.array([-d[1], d[0]])
                zc = float(H.at(p.x, p.y)) - 0.12 + height + 0.25
                a, b = np.array([p.x, p.y]) - n * 7, np.array([p.x, p.y]) + n * 7
                out.append([[round(a[0], 2), round(a[1], 2), round(zc + 0.4, 2)], [round(p.x, 2), round(p.y, 2), round(zc, 2)],
                            [round(b[0], 2), round(b[1], 2), round(zc + 0.4, 2)]])
    return out


def posters(blank_segs, tb, spacing=45.0):
    """Alternative Linke posters (3 x F4 in a row) on street-facing blank walls, `spacing` metres apart."""
    out = []
    for s in sorted(blank_segs, key=lambda s: h32(s["bid"] + str(round(s["x"])))):
        if not tb.contains(Point(s["x"], s["y"])):
            continue
        if any(np.hypot(s["x"] - o[0], s["y"] - o[1]) < spacing for o in out):
            continue
        out.append([round(s["x"], 2), round(s["y"], 2), round(s["z"], 2), round(s["tx"], 4), round(s["ty"], 4),
                    h32(s["bid"]) % 4, 3 if s["w"] > 3.4 else 1])
    return out


_WILD = None


def _wild_pieces():
    """Poster-wall pieces from wildposters.json: [(sheet, [x, y] of the top event's venue or None)]."""
    global _WILD
    if _WILD is None:
        import json
        from config import ROOT
        try:
            _WILD = [(i, p.get("xy")) for i, p in enumerate(json.load(open(ROOT / "web/public/tex/wildposters.json"))["pieces"])]
        except Exception:
            _WILD = [(i, None) for i in range(16)]
    return _WILD


def wild_posters(blank_segs, used, tb, spacing=22.0, main_dist=None):
    """Pasted poster walls (1.5 x 1.5 m pieces of real past culture events) on blank ground-floor walls (Brandmauern),
    denser on main streets; each wall prefers pieces whose venues are nearby. Rows: [x, y, z, tx, ty, sheet, rot]."""
    out, centres = [], []
    for s in sorted(blank_segs, key=lambda s: h32("w" + s["bid"] + str(round(s["y"])))):
        if not tb.contains(Point(s["x"], s["y"])) or s["w"] < 2.0:
            continue
        if any(np.hypot(s["x"] - u[0], s["y"] - u[1]) < 6 for u in used):
            continue
        sp = spacing * (0.6 if main_dist and main_dist(s["x"], s["y"]) < 25 else 1.0)
        if any(np.hypot(s["x"] - c[0], s["y"] - c[1]) < sp for c in centres):
            continue
        centres.append((s["x"], s["y"]))
        k = h32("c" + s["bid"])
        offs = [0.0] if s["w"] < 3.6 else [-0.8, 0.8]
        ranked = sorted(_wild_pieces(), key=lambda p: (np.hypot(p[1][0] - s["x"], p[1][1] - s["y"]) if p[1] else 1200.0)
                        + (h32(f"{k}{p[0]}") % 900))
        for i, off in enumerate(offs):
            kk = h32(f"{k}{i}")
            out.append([round(s["x"] + s["tx"] * off, 2), round(s["y"] + s["ty"] * off, 2), round(s["z"] - 0.75 + ((kk >> 4) % 5 - 2) * 0.03, 2),
                        round(s["tx"], 4), round(s["ty"], 4), ranked[i * 3 % len(ranked)][0], round(((kk >> 8) % 9 - 4) * 0.01, 3)])
    return out


def wall_bikes(segs, tb, H):
    """Bikes leaning against facades (shops and plain walls), as in every Zürich street. Rows like city bikes:
    [x, y, z, heading, colour]."""
    out = []
    for s in segs:
        if not tb.contains(Point(s["x"], s["y"])):
            continue
        k = h32("bk" + s["bid"] + str(round(s["x"])))
        if k % 100 > (30 if not s.get("blank") else 15):
            continue
        n = 1 + (k >> 7) % 3
        ox, oy = s["ty"], -s["tx"]  # outward normal
        for i in range(n):
            off = ((k >> (i * 4)) % 9 - 4) * 0.45
            x = s["x"] + s["tx"] * off + ox * 0.45
            y = s["y"] + s["ty"] * off + oy * 0.45
            heading = float(np.arctan2(s["tx"], s["ty"])) + (np.pi if (k >> (i + 3)) % 2 else 0)
            out.append([round(x, 2), round(y, 2), round(float(H.at(x, y)), 2), round(heading, 3), (k >> (i * 5)) % 14])
    return out


def lawn_spots(parks, tb, H, per_m2=1 / 140.0, cap=28):
    """Places where people lie, sit or chat on the grass: [x, y, z, heading, kind] (0 lie, 1 picnic, 2 chat)."""
    area = parks.intersection(tb)
    out = []
    for g in getattr(area, "geoms", [area]):
        if g.is_empty or g.geom_type != "Polygon" or g.area < 80:
            continue
        n = min(cap - len(out), int(g.area * per_m2) + 1)
        x0, y0, x1, y1 = g.bounds
        k = h32(f"lawn{x0:.0f}{y0:.0f}")
        tries = 0
        while n > 0 and tries < 200:
            tries += 1
            k = (k * 1103515245 + 12345) & 0x7FFFFFFF
            x = x0 + (k % 10000) / 10000 * (x1 - x0)
            k = (k * 1103515245 + 12345) & 0x7FFFFFFF
            y = y0 + (k % 10000) / 10000 * (y1 - y0)
            if not g.buffer(-1.5).contains(Point(x, y)):
                continue
            out.append([round(x, 2), round(y, 2), round(float(H.at(x, y)), 2), round((k % 628) / 100, 2), k % 3])
            n -= 1
    return out


def decals(S, tb, H, curb=0.12):
    """Road decals: [x, y, z, heading, kind]; kind 0 bike pictogram, 1 manhole, 2 gully, 3 'ZONE 30', 4 straight arrow,
    5 'BUS', 6 painted '30'. Zone entries / speed regimes come from the official data (streets_rules), not OSM maxspeed."""
    import streets
    import streets_rules as SR
    from shapely.geometry import box
    SR.annotate(S)
    streets.junction_gaps(S)
    out = []
    z = lambda x, y: round(float(H.at(x, y)) - curb + 0.012, 3)
    add = lambda p, h, k: out.append([round(p.x, 2), round(p.y, 2), z(p.x, p.y), round(float(h), 3), k]) if tb.contains(p) else None
    def heading(ln, s):
        a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(min(ln.length, s + 1))
        return np.arctan2(b.x - a.x, b.y - a.y)
    near = box(*tb.bounds).buffer(30)
    R = SR.rules()
    for wi, w in enumerate(S["ways"]):
        ln = w["line"]
        if ln.length < 8 or not ln.intersects(near):
            continue
        L, gaps, zone = ln.length, w["gaps"], w["zone"]
        free = lambda s: not any(g0 - 1 <= s <= g1 + 1 for g0, g1 in gaps)
        # bike pictograms on the painted lanes: after each junction, then every ~40 m, riding direction
        if zone not in ("beg", "fuss"):
            for side, solid, broken in streets.bike_lane_pieces(w):
                sgn = 1 if side == "left" else -1
                off = ln.offset_curve(sgn * (w["w"] / 2 - 0.85))
                if off.is_empty or off.geom_type != "LineString":
                    continue
                for a, b in w["lanes"][side]:
                    for s in list(np.arange(a + 7, b - 5, 40)):
                        if free(s):
                            add(off.interpolate(s * off.length / L), heading(off, s * off.length / L) + (np.pi if sgn > 0 else 0), 0)
            for side in streets.bus_sides(w):
                sgn = 1 if side == "left" else -1
                off = ln.offset_curve(sgn * (w["w"] / 2 - 1.7))
                if off.is_empty or off.geom_type != "LineString":
                    continue
                for s in np.arange(14, L - 8, 70):
                    if free(s):
                        add(off.interpolate(s * off.length / L), heading(off, s * off.length / L) + (np.pi if sgn > 0 else 0), 5)
        # manholes along the carriageway, gullies at the kerb
        if w["hw"] != "service" and zone not in ("fuss",):
            k = h32(f"mh{wi}")
            for s in np.arange(12 + k % 20, L - 6, 38 + k % 17):
                p = ln.offset_curve(((k >> 3) % 5 - 2) * 0.6).interpolate(s) if w["w"] > 6 else ln.interpolate(s)
                add(p, heading(ln, s), 1)
            for sgn in (1, -1):
                kerb = ln.offset_curve(sgn * (w["w"] / 2 - 0.35))
                if kerb.is_empty or kerb.geom_type != "LineString":
                    continue
                for s in np.arange(8, kerb.length - 4, 22):
                    add(kerb.interpolate(s), heading(kerb, s), 2)
        # 'ZONE 30' painted where traffic enters an official T30 zone; '30' roundel on signalised 30 stretches
        if w["hw"] in ("service", "primary_link", "secondary_link", "tertiary_link") or L < 20:
            continue
        evs = w.get("events")
        if evs is None:
            evs = w["events"] = way_events(w)
        for s, prev, new in evs:
            for sgn, enter in ((1, new), (-1, prev)):  # travelling +s enters `new`, travelling -s enters `prev`
                other = prev if sgn > 0 else new
                if enter == "z30" and other != "z30":
                    ss = min(max(s + sgn * 8, 5), L - 5)
                    add(ln.interpolate(ss), heading(ln, ss) + (0 if sgn > 0 else np.pi), 3)
                elif enter == "t30" and other not in ("z30", "t30") and w["hw"] in ("primary", "secondary", "tertiary"):
                    ss = min(max(s + sgn * 10, 5), L - 5)
                    add(ln.interpolate(ss), heading(ln, ss) + (0 if sgn > 0 else np.pi), 6)
    # lane arrows (left / straight / right / combined) before the stop line of signalised approaches
    import streets_arrows
    for x, y, h, k in streets_arrows.arrows(S, near):
        add(Point(x, y), h, k)
    return out


def way_events(w):
    """Zone / speed regime changes along a way (extended 12 m beyond both ends): [(s, prev, new)] with s on the way."""
    import streets_rules as SR
    ln = w["line"]
    c = np.asarray(ln.coords)
    if len(c) < 2:
        return []
    d0, d1 = c[0] - c[1], c[-1] - c[-2]
    d0, d1 = d0 / (np.hypot(*d0) + 1e-9), d1 / (np.hypot(*d1) + 1e-9)
    ext = np.vstack([c[0] + d0 * 12, c, c[-1] + d1 * 12])
    return [(s - 12.0, prev, new) for s, prev, new in SR.events(ext)]


def outdoor_ids():
    """OSM ids with outdoor seating (research/pois_testarea_details.csv, «ja …»)."""
    import csv
    from config import ROOT
    f = ROOT / "research" / "pois_testarea_details.csv"
    if not f.exists():
        return set()
    return {r["osm_id"].lstrip("n") for r in csv.DictReader(open(f)) if r.get("outdoor_seating", "").startswith("ja")}


def terraces(signs, roads, outdoor, H, colliders_inside):
    """Café/bar tables on the sidewalk in front of venues with outdoor seating: [x, y, z, heading, parasol]."""
    out, groups = [], []
    for sg in signs:
        ox, oy = sg["ty"], -sg["tx"]  # outward normal of the facade
        kind = sg.get("kind", "")
        if str(sg.get("osm")) in outdoor:
            n = 2 + h32(sg["name"]) % 3
            for i in range(n):
                off = (i - (n - 1) / 2) * 1.9
                x, y = sg["x"] + sg["tx"] * off + ox * 1.7, sg["y"] + sg["ty"] * off + oy * 1.7
                if roads.contains(Point(x, y)) or colliders_inside(x, y):
                    continue
                out.append([round(x, 2), round(y, 2), round(float(H.at(x, y)), 2), round(float(np.arctan2(sg["tx"], sg["ty"])), 3),
                            1 if h32(sg["name"]) % 2 else 0])
        if kind in ("bar", "pub", "nightclub"):  # people chatting/smoking outside bars
            x, y = sg["x"] + ox * 1.6, sg["y"] + oy * 1.6
            if not roads.contains(Point(x, y)):
                groups.append([round(x, 2), round(y, 2), round(float(H.at(x, y)), 2), (h32(sg["name"]) % 628) / 100, 2])
    return out, groups


def graffiti(blank_segs, used, tb, main_dist):
    """Fictional tags on blank ground-floor walls (more on main streets): [x, y, z, tx, ty, idx, scale]."""
    out = []
    for sg in blank_segs:
        if not tb.contains(Point(sg["x"], sg["y"])):
            continue
        k = h32("g" + sg["bid"] + str(round(sg["x"])))
        chance = 40 if main_dist(sg["x"], sg["y"]) < 25 else 20
        if k % 100 >= chance or any(np.hypot(sg["x"] - u[0], sg["y"] - u[1]) < 2.5 for u in used):
            continue
        for j in range(1 + (k >> 8) % 2):
            off = ((k >> (10 + j * 3)) % 7 - 3) * 0.5
            out.append([round(sg["x"] + sg["tx"] * off, 2), round(sg["y"] + sg["ty"] * off, 2),
                        round(sg["z"] - 0.9 + ((k >> 14) % 5) * 0.2, 2), round(sg["tx"], 4), round(sg["ty"], 4),
                        (k >> (4 + j)) % 16, round(0.9 + ((k >> 18) % 5) * 0.15, 2)])
    return out


def construction(blds, segs, tb, main_dist, n_extra=6):
    """Facade scaffolding: every building marked «Im Bau» (max 6 per tile) plus facades on main streets (>= 70 m apart).
    Real sites (OGD/OSM) are added by sites.scaffold_rows(). Rows [x, y, z, tx, ty, width, height]."""
    out = []
    cand = [s for s in segs if tb.contains(Point(s["x"], s["y"]))]
    building_ids = {b["id"] for b in blds if b.get("type") == "Im Bau"}
    seen = set()
    for s in sorted(cand, key=lambda s: -s["w"]):
        if s["bid"] in building_ids and s["bid"] not in seen:
            seen.add(s["bid"])
            out.append(s)
    out = out[:6]
    main = sorted([s for s in cand if main_dist(s["x"], s["y"]) < 20 and s["w"] > 8], key=lambda s: h32("bau" + s["bid"]))
    for s in main:
        if len(out) >= 6 + n_extra:
            break
        if h32("site" + s["bid"]) % 4 == 0 and all(np.hypot(s["x"] - o["x"], s["y"] - o["y"]) > 70 for o in out):
            out.append(s)
    return [[round(s["x"], 2), round(s["y"], 2), round(s["z"] - (3.45 if not s.get("blank") else 1.75), 2), round(s["tx"], 4),
             round(s["ty"], 4), round(min(s["w"], 16), 1), 14.0] for s in out]


def scooters(paths, tb, every=70.0):
    """Shared e-scooters left on the sidewalk (no brand): [x, y, heading, colour]."""
    out = []
    for path in paths:
        a = np.asarray(path)
        seg = np.hypot(*np.diff(a, axis=0).T)
        acc = 0.0
        for i, L in enumerate(seg):
            acc += L
            if acc > every and tb.contains(Point(*a[i])):
                acc = 0.0
                k = h32(f"sc{a[i][0]:.0f}{a[i][1]:.0f}")
                if k % 3 == 0:
                    continue
                out.append([round(float(a[i][0]), 2), round(float(a[i][1]), 2), round((k % 628) / 100, 2), k % 3])
    return out
