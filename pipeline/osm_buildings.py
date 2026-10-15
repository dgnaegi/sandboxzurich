"""Bring swissBUILDINGS3D (2019) up to date with OSM: new buildings are extruded from OSM footprints,
2019 buildings that no longer exist in OSM are dropped.

New: OSM building with < 25 % of its area covered by swissBUILDINGS3D. Height: OSM height, else
building:levels / GWR floors x 3.0 m (+0.6 m parapet), else 10 m (residential) / 6 m. Flat roof.
Gone: swissBUILDINGS3D building (> 40 m2) with < 15 % of its footprint covered by any OSM building.
Output buildings use the swissBUILDINGS3D dict format, so facade.add_building treats them the same.
"""
import shapely
from shapely.geometry import LineString, Polygon
from shapely.strtree import STRtree
import numpy as np

from gwr import gwr_for_building

SKIP = {"roof", "carport", "shelter", "canopy", "bridge", "construction", "ruins", "hut", "kiosk", "transformer_tower"}


def _osm_footprints(nodes, els):
    out = []
    for e in els:
        t = e.get("tags") or {}
        b = t.get("building")
        if e["type"] != "way" or not b or b in SKIP or t.get("location") == "underground":
            continue
        ids = e.get("nodes", [])
        if len(ids) < 4 or ids[0] != ids[-1]:
            continue
        pts = [nodes[n] for n in ids if n in nodes]
        if len(pts) < 4:
            continue
        g = Polygon(pts).buffer(0)
        if g.geom_type == "Polygon" and g.area > 12:
            out.append((e["id"], g, t))
    # multipolygon relations (large complexes, e.g. Westpark Pfingstweidstrasse 60): without them such
    # buildings count as "demolished since 2019"
    ways = {e["id"]: e.get("nodes", []) for e in els if e["type"] == "way"}
    for e in els:
        t = e.get("tags") or {}
        b = t.get("building")
        if e["type"] != "relation" or t.get("type") != "multipolygon" or not b or b in SKIP:
            continue
        rings = {"outer": [], "inner": []}
        for m in e.get("members", []):
            ids = ways.get(m.get("ref")) if m.get("type") == "way" else None
            pts = [nodes[n] for n in ids or [] if n in nodes]
            if len(pts) >= 2 and m.get("role") in rings:
                rings[m["role"]].append(LineString(pts))
        outer = shapely.union_all(list(shapely.polygonize(rings["outer"]).geoms)) if rings["outer"] else None
        if outer is None or outer.is_empty:
            continue
        if rings["inner"]:
            outer = outer.difference(shapely.union_all(list(shapely.polygonize(rings["inner"]).geoms)))
        for k, g in enumerate(shapely.get_parts(outer.buffer(0))):
            if g.geom_type == "Polygon" and g.area > 12:
                out.append((-(e["id"] * 10 + k), g, t))  # negative ids: no clash with way ids
    return out


def _height(g, t):
    try:
        if t.get("height"):
            return float(str(t["height"]).split()[0])
    except ValueError:
        pass
    lv = t.get("building:levels")
    if not lv:
        gw = gwr_for_building(np.asarray(g.exterior.coords)[:, :2])
        lv = (gw or {}).get("floors")
    try:
        if lv:
            return max(3.0, float(lv) * 3.0 + 0.6)
    except ValueError:
        pass
    return 10.0 if t.get("building") in ("residential", "apartments", "house", "yes") and g.area > 80 else 6.0


def _make(oid, g, t, H):
    ring = np.asarray(g.exterior.coords)[:-1]
    if Polygon(ring).exterior.is_ccw is False:
        ring = ring[::-1]
    z0 = float(min(H.at(x, y) for x, y in ring))
    z1 = z0 + _height(g, t)
    polys = [(0, np.column_stack([ring, np.full(len(ring), z0)]).astype(np.float32)),
             (2, np.column_stack([ring, np.full(len(ring), z1)]).astype(np.float32))]
    for a, b in zip(ring, np.roll(ring, -1, axis=0)):
        polys.append((1, np.array([[a[0], a[1], z0], [b[0], b[1], z0], [b[0], b[1], z1], [a[0], a[1], z1]], np.float32)))
    c = np.concatenate([p for _, p in polys]).mean(0)
    return {"id": f"osm_{oid}", "h": z1 - z0, "type": "osm", "polys": polys, "center": c, "_osm_tags": t}


def update(blds, nodes, els, H, footprint, play):
    """play: polygon where OSM is complete. New = OSM building with best IoU < 0.4 against 2019 data and
    (GWR year >= 2019 or < 25 % covered); 2019 buildings under new ones (> 20 %) or without any OSM
    building (< 15 % covered) are dropped (only inside play)."""
    osm = _osm_footprints(nodes, els)
    if not osm:
        return blds
    fps = [footprint(b) for b in blds]
    fps = [f.buffer(0) if f is not None and not f.is_valid else f for f in fps]
    idx = [i for i, f in enumerate(fps) if f is not None]
    valid = [fps[i] for i in idx]
    stree = STRtree(valid)
    x0, y0, x1, y1 = shapely.MultiPolygon([f for f in valid if f.geom_type == "Polygon"]).bounds
    new, new_g = [], []
    for oid, g, t in osm:
        c = g.centroid
        if not (x0 <= c.x <= x1 and y0 <= c.y <= y1):
            continue
        hit = stree.query(g)
        iou = max((g.intersection(valid[i]).area / g.union(valid[i]).area for i in hit), default=0.0)
        if iou >= 0.4:
            continue
        cov = sum(g.intersection(valid[i]).area for i in hit) / g.area if len(hit) else 0.0
        year = (gwr_for_building(np.asarray(g.exterior.coords)[:, :2]) or {}).get("year")
        try:
            recent = int(year) >= 2019
        except (TypeError, ValueError):
            recent = False
        if recent or cov < 0.25:
            new.append(_make(oid, g, t, H))
            new_g.append(g)
    ntree = STRtree(new_g) if new_g else None
    otree = STRtree([g for _, g, _ in osm])
    keep, gone = [], 0
    for b, fp in zip(blds, fps):
        if fp is None or fp.area < 40 or not play.contains(fp.centroid):
            keep.append(b)
            continue
        under = sum(fp.intersection(new_g[i]).area for i in ntree.query(fp)) / fp.area if ntree else 0.0
        cov = sum(fp.intersection(osm[i][1]).area for i in otree.query(fp)) / fp.area
        if under > 0.2 or cov < 0.15:
            gone += 1
        else:
            keep.append(b)
    print(f"osm_buildings: {gone} replaced/demolished since 2019, {len(new)} new from OSM")
    return keep + new
