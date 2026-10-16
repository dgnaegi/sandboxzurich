"""Real names where people expect them (Wiedererkennung): institutions, wall-sign fallback, GWR house numbers, junction poles.

Sources: OSM (ODbL) names, BFS GWR entrances (OGD), swissBUILDINGS3D footprints. Names are facts; no logos.
- add_institutions(S, nodes, els)   -> S["inst"]: schools, churches, GZ, libraries ... also mapped as building areas (ways)
- fallback(sg, tb, H, S)            -> sg + wall signs for POIs/institutions without a shopfront segment (flag nf=1: no awning/props)
- gwr_numbers(area, H, rows, S)     -> extra house-number rows for every GWR entrance without an OSM number
- junction_poles(area, H, rows, S)  -> pole street signs at junctions the facade pass left without a sign
"""
import math
from collections import defaultdict

import numpy as np
import shapely
import shapely.ops
from shapely.geometry import LineString, Point, Polygon
from shapely.prepared import prep

import addresses
import sources
from config import ROOT

OX, OY = 2681400.0, 1248700.0
INST_AMENITY = {"school", "kindergarten", "college", "university", "place_of_worship", "community_centre", "library",
                "theatre", "cinema", "arts_centre", "post_office", "pharmacy", "doctors", "dentist", "childcare",
                "social_facility", "bank", "veterinary", "townhall", "police", "fire_station", "clinic", "hospital"}
INST_SHOP = {"supermarket", "department_store", "mall", "kiosk", "convenience"}
BIG_MAX = 40000.0


def _footprint_near(d, p, r):
    pt = Point(p)
    c = d["tree"].query(pt.buffer(r))
    return [d["fps"][i] for i in c]


def add_institutions(S, nodes, els):
    d = addresses._data()
    have = {str(p["osm"]) for p in S["pois"]}
    streets = [w["line"] for w in S["ways"] if w.get("name")]
    st_tree = shapely.STRtree(streets) if streets else None
    out = []

    def toward_street(fp, p):
        if not st_tree:
            return p
        i = st_tree.nearest(fp)
        a, b = shapely.ops.nearest_points(fp.exterior, streets[i])
        return (a.x, a.y)

    for e in els:
        t = e.get("tags", {})
        if not t.get("name"):
            continue
        am, sh = t.get("amenity"), t.get("shop")
        if not (am in INST_AMENITY or sh in INST_SHOP or t.get("office") == "government"):
            continue
        kind = sh or am or "office"
        if str(e["id"]) in have:
            continue
        if e["type"] == "node":
            p = nodes.get(e["id"])
            if p is None:
                continue
            cand = _footprint_near(d, p, 12)
            if not cand:
                continue
            fp = min(cand, key=lambda g: g.distance(Point(p)))
            anchor = p if fp.distance(Point(p)) < 1.0 else toward_street(fp, p)
        elif e["type"] == "way":
            pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if len(pts) < 4:
                continue
            poly = Polygon(pts).buffer(0)
            if poly.is_empty or poly.area > BIG_MAX:
                continue
            inside = [g for g in _footprint_near(d, poly.centroid.coords[0], 120) if poly.contains(g.representative_point())]
            fp = max(inside, key=lambda g: g.area) if inside else poly
            if fp.geom_type != "Polygon":
                continue
            anchor = toward_street(fp, poly.centroid.coords[0])
        else:
            continue
        out.append({"x": round(float(anchor[0]), 2), "y": round(float(anchor[1]), 2), "name": t["name"], "kind": kind,
                    "osm": e["id"], "src": e["type"][0]})
    S["inst"] = out
    kinds = defaultdict(int)
    for o in out:
        kinds[o["kind"]] += 1
    print(f"names: {len(out)} institutions/big shops from OSM nodes+ways: {dict(sorted(kinds.items(), key=lambda kv: -kv[1])[:8])}", flush=True)


def _wall_sign(d, p, name, kind, osm, H, placed, z_off, maxw, r=12.0):
    cand = _footprint_near(d, p, r)
    if not cand:
        return None
    fp = min(cand, key=lambda g: g.distance(Point(p)))
    if fp.distance(Point(p)) > r:
        return None
    wx, wy, tx, ty, L = addresses._wall_at(fp, p)
    if L < 3.0:
        return None
    w = min(maxw, L - 1.0)
    for sh in (0.0, 1.0, -1.0, 2.0, -2.0):
        cx, cy = wx + tx * sh * (w + 0.4), wy + ty * sh * (w + 0.4)
        if all(math.hypot(cx - q[0], cy - q[1]) > w * 0.8 for q in placed):
            break
    else:
        return None
    placed.append((cx, cy))
    z = float(H.at(cx, cy)) + z_off
    return {"x": round(cx + ty * 0.12, 2), "y": round(cy - tx * 0.12, 2), "z": round(z, 2), "tx": round(tx, 4), "ty": round(ty, 4),
            "w": round(w, 2), "name": name, "kind": kind, "osm": osm, "nf": 1}


INST_Z = {"school": 3.6, "college": 3.6, "university": 3.6, "place_of_worship": 3.4, "community_centre": 3.2, "hospital": 3.6}


def fallback(sg, tb, H, S):
    d = addresses._data()
    covered = {str(s["osm"]) for s in sg}
    placed = [(s["x"], s["y"]) for s in sg]
    names = [(s["x"], s["y"], s["name"].lower()) for s in sg]
    out = list(sg) + [r for r in extra_rows(H) if tb.contains(Point(r["x"], r["y"]))]

    def dup(x, y, n):
        n = n.lower()
        return any(a == n and math.hypot(x - ax, y - ay) < 45 for ax, ay, a in names)

    for p in S.get("pois", []):
        if str(p["osm"]) in covered or not tb.contains(Point(p["x"], p["y"])) or dup(p["x"], p["y"], p["name"]):
            continue
        s = _wall_sign(d, (p["x"], p["y"]), p["name"], p["kind"], p["osm"], H, placed, 2.6, 4.5)
        if s:
            out.append(s)
            names.append((s["x"], s["y"], p["name"].lower()))
    for p in S.get("inst", []):
        if str(p["osm"]) in covered or not tb.contains(Point(p["x"], p["y"])) or dup(p["x"], p["y"], p["name"]):
            continue
        big = p["kind"] in INST_Z
        s = _wall_sign(d, (p["x"], p["y"]), p["name"], p["kind"], p["osm"], H, placed, INST_Z.get(p["kind"], 2.8), 7.0 if big else 4.5, r=3.0)
        if s:
            out.append(s)
            names.append((s["x"], s["y"], p["name"].lower()))
    return out


def gwr_numbers(area, H, rows, S):
    import csv
    d = addresses._data()
    x0, y0, x1, y1 = area
    lines = defaultdict(list)
    for name, _, pts in addresses._streets(area):
        lines[name].append(LineString(pts))
    cell = defaultdict(list)
    for r in rows:
        cell[int(r[0] // 20), int(r[1] // 20)].append(r)
    added, seen, new = 0, set(), []

    def near_same(x, y, text):
        cx, cy = int(x // 20), int(y // 20)
        return any(r[5].lower() == text and math.hypot(r[0] - x, r[1] - y) < 14 for a in (-1, 0, 1) for b in (-1, 0, 1) for r in cell.get((cx + a, cy + b), []))

    for r in csv.DictReader(open(ROOT / "data/raw/gwr/eingang_entree_entrata.csv"), delimiter="\t"):
        if not r["DKODE"] or not r["DEINR"]:
            continue
        x, y = float(r["DKODE"]) - OX, float(r["DKODN"]) - OY
        if not (x0 <= x < x1 and y0 <= y < y1):
            continue
        text = r["DEINR"].replace(" ", "")
        if near_same(x, y, text.lower()) or (r["EGID"], r["EDID"]) in seen:
            continue
        seen.add((r["EGID"], r["EDID"]))
        pt = Point(x, y)
        cand = _footprint_near(d, (x, y), 10)
        if not cand:
            continue
        poly = min(cand, key=lambda g: g.distance(pt))
        if poly.distance(pt) > 10:
            continue
        target = (x, y)
        if poly.contains(pt) and lines.get(r["STRNAME"]):
            ln = min(lines[r["STRNAME"]], key=lambda l: l.distance(pt))
            target = ln.interpolate(ln.project(pt)).coords[0]
        wx, wy, tx, ty, L = addresses._wall_at(poly, target)
        if L < 1.0:
            continue
        if any(math.hypot(wx + ty * 0.05 - q[0], wy - tx * 0.05 - q[1]) < 0.6 for q in new[-40:]) :
            continue
        z = float(H.at(wx, wy)) + addresses.NUM_Z
        row = [round(wx + ty * addresses.OFF, 2), round(wy - tx * addresses.OFF, 2), round(z, 2), round(tx, 3), round(ty, 3), text]
        new.append(row)
        cell[int(row[0] // 20), int(row[1] // 20)].append(row)
        added += 1
    print(f"names: {added} house numbers added from GWR entrances", flush=True)
    return new


def junction_poles(area, H, rows, S):
    d = addresses._data()
    x0, y0, x1, y1 = area
    by = defaultdict(list)
    for e in d["els"]:
        t = e.get("tags", {})
        if e["type"] != "way" or "highway" not in t or t["highway"] in addresses.NON_ROAD or not t.get("name"):
            continue
        if t.get("tunnel") in ("yes", "building_passage") or t.get("bridge") == "yes":
            continue
        ids = [n for n in e["nodes"] if n in d["nodes"]]
        for i, n in enumerate(ids):
            j = i + 1 if i + 1 < len(ids) else i - 1
            if j < 0:
                continue
            p, q = np.array(d["nodes"][n]), np.array(d["nodes"][ids[j]])
            v = q - p
            if np.hypot(*v) > 0.1:
                by[n].append((t["name"], p, v / np.hypot(*v), float(t.get("width", 0) or 0) or 6.0))
    roads = prep(S["roads"].buffer(0.9))
    cell = defaultdict(list)
    for r in rows:
        cell[int(r[0] // 40), int(r[1] // 40)].append(r)
    out, placed = [], []
    for n, items in by.items():
        names = {i[0] for i in items}
        p = items[0][1]
        if len(names) < 2 or not (x0 <= p[0] < x1 and y0 <= p[1] < y1):
            continue
        half = max(i[3] for i in items) / 2
        cx, cy = int(p[0] // 40), int(p[1] // 40)
        near = [r for a in (-1, 0, 1) for b in (-1, 0, 1) for r in cell.get((cx + a, cy + b), [])]
        for name in sorted(names):
            if any(r[4] == name and math.hypot(r[0] - p[0], r[1] - p[1]) < 32 for r in near):
                continue
            dirv = next(i[2] for i in items if i[0] == name)
            best = None
            for rad in (half + 1.3, half + 3.0, half + 5.5):
                for k in range(12):
                    a = k * math.pi / 6
                    c = (p[0] + math.cos(a) * rad, p[1] + math.sin(a) * rad)
                    pt = Point(c)
                    if roads.contains(pt) or d["tree"].query(pt.buffer(0.8)).size:
                        continue
                    if any(math.hypot(c[0] - q[0], c[1] - q[1]) < 3.5 for q in placed):
                        continue
                    sc = rad + abs(math.sin(a - math.atan2(dirv[1], dirv[0]))) * 0.0
                    if best is None or sc < best[0]:
                        best = (sc, c)
                if best:
                    break
            if not best:
                continue
            c = best[1]
            placed.append(c)
            h = math.atan2(dirv[1], dirv[0])
            row = [round(c[0], 2), round(c[1], 2), round(float(H.at(*c)) + 2.6, 2), round(h, 3), name, "", 1]
            out.append(row)
            near.append(row)
    print(f"names: {len(out)} pole street signs added at open junctions", flush=True)
    return out


_extra = []


def _roof_z(fp):
    """Highest swissBUILDINGS3D z of buildings whose centre lies inside the footprint (local metres)."""
    z = 0.0
    for b in sources.buildings(margin=0, area=fp.bounds):
        if fp.contains(Point(b["center"][:2])):
            z = max(z, max(float(p[:, 2].max()) for _, p in b["polys"]))
    return z


def extra_rows(H):
    """Hand-picked big name boards (free lettering, no logo): Digitec Galaxus head office, Westpark, Pfingstweidstrasse 60b.
    Board on the roof edge of the south wall (Pfingstweidstrasse) and the east wall (Hardturm side), lit at night."""
    if _extra:
        return _extra
    d = addresses._data()
    cand = [g for g in _footprint_near(d, (-177, 670), 80) if g.area > 4000 and g.centroid.distance(Point(-177, 670)) < 45]
    if not cand:
        return _extra
    fp = max(cand, key=lambda g: g.area)
    roof = _roof_z(fp)
    co = np.asarray(fp.exterior.coords)
    for want in ((0, -1), (1, 0)):   # outward normal south, east
        best = None
        for a, b in zip(co[:-1], co[1:]):
            e = b - a
            L = float(np.hypot(*e))
            if L < 12:
                continue
            tx, ty = e / L
            if fp.contains(Point((a + b) / 2 + np.array([ty, -tx]) * 0.3)):
                tx, ty = -tx, -ty
            if ty * want[0] - tx * want[1] > 0.7 and (best is None or L > best[0]):
                best = (L, a, b, tx, ty)
        if not best:
            continue
        L, a, b, tx, ty = best
        m = (a + b) / 2
        gz = float(H.at(m[0], m[1]))
        z = max(gz + 9.0, (roof - 3.0) if roof > gz + 12 else gz + 9.0)
        _extra.append({"x": round(float(m[0] + ty * 0.2), 2), "y": round(float(m[1] - tx * 0.2), 2), "z": round(z, 2),
                       "tx": round(tx, 4), "ty": round(ty, 4), "w": round(min(L - 6, 22.0), 2), "name": "Digitec Galaxus",
                       "kind": "galaxus", "osm": 308058574, "nf": 1, "big": 1})
    print(f"names: Digitec Galaxus boards {len(_extra)}, roof z {roof:.1f}", flush=True)
    return _extra
