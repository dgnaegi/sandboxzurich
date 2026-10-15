"""Generate web/public/data/scenes.json (ambient scenes + easter eggs) from pipeline/overrides/scenes_src.json.

Source format (see research/scenes.md):
  fixed:  scenes copied verbatim (hand placed).
  groups: {id, type, pick, n, entries[], street, off, min_sep, params}
    pick = {tags:{k:v|"*"}, name_re, no_name, no_tags:[k..], unique_name}  -> OSM objects inside the play area
         | {way:{highway:[..], min_len, skip_footway:[..]}}                  -> walking paths (type walker/stilts)
         | {name:"exact OSM name"} per entry (entry.name) or {at:[x,y]}
    entries cycle through title/text (+ any scene params like sign, kind, color).
Candidates are picked by farthest-point sampling so scenes spread over the whole area; positions inside buildings
are rejected (or moved to the street side with off=true) using the OSM building footprints.
Run: python3 pipeline/scenes_build.py
"""
import json
import math
import re
import sys

from shapely.geometry import LineString, Point, Polygon
from shapely.strtree import STRtree

from config import POLYGON, ROOT
from sources import osm

SRC = ROOT / "pipeline" / "overrides" / "scenes_src.json"
OUT = ROOT / "web" / "public" / "data" / "scenes.json"
ROADS = {"residential", "tertiary", "primary", "secondary", "unclassified", "living_street", "trunk", "tertiary_link", "secondary_link", "primary_link"}


def inside_poly(p, poly=POLYGON):
    x, y = p
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[i - 1]
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            c = not c
    return c


class World:
    def __init__(self):
        nodes, els = osm()
        self.items, self.ways = [], []
        bpolys, roads = [], []
        for e in els:
            t = e.get("tags")
            if e["type"] == "way" and e.get("nodes"):
                pts = [nodes[n] for n in e["nodes"] if n in nodes]
                if len(pts) < 2:
                    continue
                if t and "building" in t and len(pts) >= 4 and pts[0] == pts[-1]:
                    bpolys.append(Polygon(pts).buffer(0))
                if t and t.get("highway") in ROADS and "tunnel" not in t:
                    roads.append(LineString(pts))
                if t and t.get("highway") in ("footway", "path", "pedestrian", "track"):
                    self.ways.append((pts, t))
                c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
                if t:
                    self.items.append((c, t))
            elif e["type"] == "node" and t:
                self.items.append((nodes[e["id"]], t))
        self.items = [(p, t) for p, t in self.items if inside_poly(p)]
        self.btree, self.bpolys = STRtree(bpolys), bpolys
        self.rtree, self.roads = STRtree(roads), roads
        print(f"items {len(self.items)}, buildings {len(bpolys)}, roads {len(roads)}, paths {len(self.ways)}")

    def in_building(self, x, y):
        pt = Point(x, y)
        return any(self.bpolys[i].contains(pt) for i in self.btree.query(pt))

    def street(self, x, y):
        """(distance, ux, uy, tx, ty): nearest road point direction and tangent."""
        pt = Point(x, y)
        i = self.rtree.nearest(pt)
        ln = self.roads[i]
        d = ln.project(pt)
        q = ln.interpolate(d)
        dist = pt.distance(q)
        a, b = ln.interpolate(max(0, d - 2)), ln.interpolate(min(ln.length, d + 2))
        tx, ty = b.x - a.x, b.y - a.y
        tn = math.hypot(tx, ty) or 1
        if dist < 1e-6:
            return 0, 0, 1, tx / tn, ty / tn
        return dist, (q.x - x) / dist, (q.y - y) / dist, tx / tn, ty / tn


def match(t, pick):
    for k, v in pick.get("tags", {}).items():
        if k not in t or (v != "*" and t[k] not in (v if isinstance(v, list) else [v])):
            return False
    if pick.get("no_name") and "name" in t:
        return False
    if pick.get("has_name") and "name" not in t:
        return False
    if "name_re" in pick and not re.search(pick["name_re"], t.get("name", ""), re.I):
        return False
    return not any(k in t for k in pick.get("no_tags", []))


def yaw(dx, dy):
    return round(math.atan2(dx, dy), 2)


def place(w, p, grp, rng_i):
    """Resolve a raw point into (x, y, dir) or None. grp.auto: try moving out of a building to the street side, else keep the point."""
    if grp.get("auto"):
        for g2 in ({**grp, "auto": False, "off": True}, {**grp, "auto": False, "off": False, "nocheck": True}):
            r = place(w, p, g2, rng_i)
            if r:
                return r
        return None
    x, y = p
    mode, off = grp.get("street"), grp.get("off", False)
    d, ux, uy, tx, ty = w.street(x, y)
    if off:
        if d < 3.5:
            return None
        t = 0.0
        while t < d - 2.0 and w.in_building(x + ux * t, y + uy * t):
            t += 0.5
        t = min(t + grp.get("extra", 1.5), d - 1.5)
        x, y = x + ux * t, y + uy * t
        if w.in_building(x, y) or d - t < 1.5:
            return None
    elif w.in_building(x, y) and not grp.get("nocheck"):
        return None
    if not inside_poly((x, y)):
        return None
    if mode == "face":
        dr = yaw(ux, uy)
    elif mode == "away":
        dr = yaw(-ux, -uy)
    elif mode == "along":
        dr = yaw(tx, ty)
    else:
        dr = round(((rng_i * 2654435761) % 628) / 100 - 3.14, 2)
    return round(x, 1), round(y, 1), dr


def way_path(w, grp):
    pk = grp["pick"]["way"]
    out = []
    for pts, t in w.ways:
        if t.get("highway") not in pk.get("highway", ["footway", "path"]):
            continue
        if t.get("footway") in pk.get("skip_footway", ["sidewalk", "crossing", "traffic_island"]) or t.get("indoor") or t.get("tunnel") or t.get("bridge") or t.get("layer"):
            continue
        ln = LineString(pts)
        if ln.length < pk.get("min_len", 60) or not all(inside_poly(p) for p in pts[:: max(1, len(pts) // 6)]):
            continue
        L = min(ln.length, pk.get("len", 45))
        s0 = (ln.length - L) / 2
        path = [[round(ln.interpolate(s0 + L * k / 6).x, 1), round(ln.interpolate(s0 + L * k / 6).y, 1)] for k in range(7)]
        out.append(path)
    return out


def site_signs(taken):
    """Info boards at real construction sites (Stadt Zürich OGD, pipeline/sites.py): scenes without an egg."""
    import sites
    out, seen = [], set()
    for st in sites.load():
        if st["id"] in seen or not st["name"]:
            continue
        poly = st["poly"]
        if st["kind"] == "road":
            c = poly.exterior.coords[0] if poly.geom_type == "Polygon" else poly.representative_point().coords[0]
            to = st.get("to", "")
            lines = ["BAUSTELLE", st["name"].split(",")[0][:22], f"bis {to[5:7]}.{to[:4]}" if len(to) >= 7 else "Tiefbauamt"]
            x, y, d = c[0], c[1], 0.0
        else:
            parts = [q.strip() for q in st["name"].split(",")]
            lines = ["HOCHBAU", parts[0][:22], (parts[1] if len(parts) > 1 else "")[:22]]
            cen = poly.centroid
            q = poly.buffer(3.2).exterior.interpolate(0.15, normalized=True)
            x, y, d = q.x, q.y, math.atan2(q.x - cen.x, q.y - cen.y)
        if not inside_poly((x, y)):
            continue
        seen.add(st["id"])
        out.append({"type": "sign", "x": round(x, 1), "y": round(y, 1), "dir": round(d, 2), "sign": lines})
    print("site signs:", len(out))
    return out


def main():
    w = World()
    src = json.load(open(SRC))
    scenes, taken, ids = [], [], set()
    for s in src.get("fixed", []):
        scenes.append(s)
        x = s.get("x", s.get("path", [[0, 0]])[0][0]); y = s.get("y", s.get("path", [[0, 0]])[0][1])
        taken.append((x, y))
        ids.add(s["egg"]["id"])
    for grp in src["groups"]:
        entries = grp["entries"]
        n = grp.get("n", len(entries))
        gid, typ = grp["id"], grp["type"]
        pick = grp.get("pick", {})
        gmin = grp.get("min_sep", 60)
        cands = []  # (x, y, dir, path|None)
        named = [e for e in entries if "name" in e or "at" in e]
        if "way" in pick:
            for path in way_path(w, grp):
                cands.append((path[3][0], path[3][1], 0, path, {}))
        elif not named:
            seen = set()
            for i, (p, t) in enumerate(w.items):
                if not match(t, pick):
                    continue
                if pick.get("unique_name"):
                    if t.get("name") in seen:
                        continue
                    seen.add(t.get("name"))
                r = place(w, p, grp, i)
                if r:
                    cands.append((*r, None, t))
        chosen = []
        if named:
            for e in entries[:n]:
                if "at" in e:
                    p = e["at"]
                else:
                    ms = [pp for pp, t in w.items if t.get("name") == e["name"]]
                    if not ms:
                        print("  !! not found:", e["name"])
                        continue
                    p = ms[0]
                p = (p[0] + e.get("dx", 0), p[1] + e.get("dy", 0))
                r = place(w, p, {**grp, **e.get("place", {})}, len(chosen))
                if r:
                    chosen.append((*r, None, {"name": e.get("name", "")}, e))
                else:
                    print("  !! unplaceable:", e.get("name", e.get("at")))
        else:
            pool = list(cands)
            while len(chosen) < n and pool:
                allp = taken + [(c[0], c[1]) for c in chosen]
                best, bd = None, -1
                for c in pool:
                    d = min((math.hypot(c[0] - a, c[1] - b) for a, b in allp), default=1e9)
                    dg = min((math.hypot(c[0] - k[0], c[1] - k[1]) for k in chosen), default=1e9)
                    if d >= 30 and dg >= gmin and d > bd:
                        best, bd = c, d
                if best is None:
                    break
                pool.remove(best)
                chosen.append((*best, entries[len(chosen) % len(entries)]))  # (x, y, dir, path, tags, entry)
        for i, c in enumerate(chosen):
            x, y, dr, path, tags, e = c
            fmt = lambda v: v.replace("{name}", tags.get("name", "")) if isinstance(v, str) else [fmt(a) for a in v] if isinstance(v, list) else v  # noqa: E731
            e = {k: fmt(v) for k, v in e.items()}
            egg = {"id": f"{gid}{i + 1}", "title": e["title"], "text": e["text"]}
            assert egg["id"] not in ids, egg["id"]
            ids.add(egg["id"])
            sc = {"type": typ, **{k: v for k, v in grp.get("params", {}).items()},
                  **{k: v for k, v in e.items() if k not in ("title", "text", "name", "at", "place")}}
            if path:
                sc["path"] = path
            else:
                sc.update(x=x, y=y, dir=e.get("dir", dr))
            sc["egg"] = egg
            scenes.append(sc)
            taken.append((x, y))
        print(f"{gid:14s} {typ:12s} {len(chosen)}/{n}")
    scenes += site_signs(taken)
    json.dump({"_doc": "Generated by pipeline/scenes_build.py from pipeline/overrides/scenes_src.json. Do not edit.", "scenes": scenes},
              open(OUT, "w"), ensure_ascii=False, indent=0)
    print("scenes:", len(scenes), "->", OUT.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
