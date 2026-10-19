"""Catalog kiosks (M2): OSM shop=kiosk at street level, freestanding spots only (assign.py adds the rows, kind 2).

A kiosk is placed where the footprint (model bbox +0.3 m) touches neither a building (AV/OSM footprints, data/build/bld)
nor the carriageway (roads.json lines buffered by half width); the OSM position is tried first, then rings up to 3 m
(nearest first). Front (+z) faces the nearest road. Kiosks inside buildings (all 31 in the play area, 2026-10: shops in house footprints), on other levels, or within 3 m of a
kiosk that tile details already draw (details_osm 'kiosk', baked into the tiles) are skipped; those tile kiosks are
replaced by the catalog model (row kind 3, same position/heading). Source: OSM (ODbL), data/raw/osm/kreise.json."""
import json
import math
import sys
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
import sources  # noqa: E402

HALF = (1.42 + 0.3, 1.32 + 0.3, 2.05 + 0.3)   # x half, back (-z), front (+z) incl. margin; index.json M2 bbox


def tile_kiosks():
    """Freestanding kiosks already baked into the tiles by details_osm."""
    out = []
    for f in (ROOT / "web" / "public" / "tiles").glob("t_*.json"):
        d = json.load(open(f))
        for o in (d.get("details") or {}).get("objs", []):
            if o[0] == "kiosk":
                out.append((o[1], o[2], o[4]))
    return out


def rows(area, road_lines):
    """road_lines: [(LineString, half_width)]. Returns (rows, stats)."""
    blds = [Polygon(p[:, :2]) for b in sources.buildings(margin=60) for _, p in b["polys"] if len(p) >= 3]
    blds = [g.buffer(0) for g in blds if g.area > 0.5]
    bt = STRtree(blds)
    rd = [ln.buffer(w) for ln, w in road_lines]
    rt = STRtree(rd)
    rl = [ln for ln, _ in road_lines]
    lt = STRtree(rl)

    def free(poly):
        return not any(blds[i].intersects(poly) for i in bt.query(poly)) and not any(rd[i].intersects(poly) for i in rt.query(poly))

    def front(x, y):
        ln = rl[int(lt.nearest(Point(x, y)))]
        p = ln.interpolate(ln.project(Point(x, y)))
        d = math.hypot(p.x - x, p.y - y) or 1
        return (p.x - x) / d, (p.y - y) / d

    nodes, els = sources.osm()
    known = tile_kiosks()
    # kind 3: replaces a kiosk baked into the tiles (details.ts skips it via catalogKioskNear; the tile collider stays)
    out = [["M2", x, y, h, 1, 0, 3] for x, y, h in known]
    st = {"tile_kiosks": len(known), "osm": 0, "skip_level": 0, "skip_tile": 0, "ok": 0}
    for e in els:
        t = e.get("tags") or {}
        if t.get("shop") != "kiosk":
            continue
        if e["type"] == "node" and e["id"] in nodes:
            x, y = nodes[e["id"]]
        elif e["type"] == "way" and e.get("nodes"):
            xy = [nodes[n] for n in e["nodes"] if n in nodes]
            if len(xy) < 3:
                continue
            x, y = sum(a for a, _ in xy) / len(xy), sum(b for _, b in xy) / len(xy)
        else:
            continue
        if not area.contains(Point(x, y)):
            continue
        st["osm"] += 1
        if t.get("level", "0") not in ("0", "") or t.get("layer", "0") not in ("0", ""):
            st["skip_level"] += 1
            continue
        if any(math.hypot(x - a, y - b) < 3 for a, b, _ in known):
            st["skip_tile"] += 1
            continue
        if any(blds[i].contains(Point(x, y)) for i in bt.query(Point(x, y))):
            st["indoor"] = st.get("indoor", 0) + 1
            if 0: print("  indoor", t.get("name"), round(x), round(y), sorted(round(blds[i].area) for i in bt.query(Point(x, y)) if blds[i].contains(Point(x, y))))
            continue
        fx, fy = front(x, y)
        yaw = math.atan2(fx, -fy)    # three: front (+z) rotated about Y -> (sin yaw, cos yaw) = (fx, -fy)
        cands = [(0.0, 0.0)] + [(r * math.cos(a * math.pi / 8), r * math.sin(a * math.pi / 8)) for r in (1, 2, 3) for a in range(16)]
        hit = None
        for dx, dy in cands:
            # footprint in local metres: x along the street, z toward the road
            fp = box(-HALF[0], -HALF[1], HALF[0], HALF[2])
            fp = affinity.rotate(fp, math.degrees(math.atan2(fy, fx)) - 90, origin=(0, 0))   # local +y -> road direction
            fp = affinity.translate(fp, x + dx, y + dy)
            if free(fp):
                hit = (x + dx, y + dy)
                break
        if not hit:
            st["blocked"] = st.get("blocked", 0) + 1
            continue
        out.append(["M2", round(hit[0], 2), round(hit[1], 2), round(yaw, 3), 1, 0, 2])
        st["ok"] += 1
    return out, st
