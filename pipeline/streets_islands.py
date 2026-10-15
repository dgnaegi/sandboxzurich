"""Tram stop islands: raised platform (OSM public_transport=platform, tram=yes) between lane and track, with kerb and a
light tactile edge strip. islands(S, tb) -> (top polygon, edge strip polygon, kerb segments [(a, b)] road on the left)."""
import numpy as np
import shapely
from shapely.geometry import Point
from shapely.geometry.polygon import orient
from shapely.strtree import STRtree

WIDTH = 2.5      # island width away from the track side edge (m)
EDGE = 0.35      # tactile / safety strip along the track-side edge (m)


def islands(S, tb):
    trams = S["tram"]
    if not S.get("platforms") or not trams:
        return None, None, []
    tree = STRtree(trams)
    area = tb.buffer(4)
    tops, strips = [], []
    for ln, t in S["platforms"]:
        if ln.length < 6 or not ln.intersects(area):
            continue
        m = ln.interpolate(0.5, normalized=True)
        i = tree.nearest(m)
        tr = trams[i]
        if m.distance(tr) > 4.5:
            continue
        # which side of the platform line is the track on? the island lies on the other side
        s = ln.project(m)
        a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(min(ln.length, s + 1))
        n = tr.interpolate(tr.project(m))
        cross = (b.x - a.x) * (n.y - m.y) - (b.y - a.y) * (n.x - m.x)
        sgn = -1 if cross > 0 else 1  # buffer(+d, single_sided) grows to the left
        for width, out in ((WIDTH, tops), (EDGE, strips)):
            g = ln.buffer(sgn * width, single_sided=True, cap_style="flat", join_style="mitre")
            if not g.is_empty:
                out.append(g)
    if not tops:
        return None, None, []
    top = shapely.union_all(tops).intersection(S["roads"]).intersection(tb)
    strip = shapely.union_all(strips).intersection(S["roads"]).intersection(tb)
    if top.is_empty:
        return None, None, []
    segs = []
    road_edge = S["roads"].boundary
    for poly in shapely.get_parts(top):
        if poly.geom_type != "Polygon" or poly.area < 2:
            continue
        poly = orient(poly, -1.0)  # clockwise: interior on the right, road on the left
        c = np.asarray(poly.exterior.coords)
        for a, b in zip(c[:-1], c[1:]):
            if np.hypot(*(b - a)) < 0.05:
                continue
            mid = Point((a + b) / 2)
            if mid.distance(road_edge) < 0.3 or not tb.contains(mid):
                continue  # on the carriageway boundary: the normal kerb exists already
            segs.append((a, b))
    return top, strip, segs


def hatch(S, tb):
    """Sperrflächen (painted islands, OSM area:highway=traffic_island on the carriageway): white outline + diagonal stripes.
    Returns a polygon (stripes + outline) clipped to the road, or None."""
    polys = [p for p in S.get("painted_islands", []) if p.intersects(tb) and p.intersects(S["roads"]) and p.area > 3]
    out = []
    for p in polys:
        p = p.intersection(S["roads"])
        for q in shapely.get_parts(p):
            if q.geom_type != "Polygon" or q.area < 3:
                continue
            inner = q.buffer(-0.12)
            out.append(q.difference(inner) if not inner.is_empty else q)
            x0, y0, x1, y1 = q.bounds
            d = np.hypot(x1 - x0, y1 - y0)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            for k in np.arange(-d / 2, d / 2, 0.9):  # 45 degree stripes, 0.3 m wide every 0.9 m
                st = shapely.geometry.LineString([(cx + k - d, cy - d), (cx + k + d, cy + d)]).buffer(0.15, cap_style="flat")
                g = st.intersection(inner)
                if not g.is_empty:
                    out.append(g)
    return shapely.union_all(out).intersection(tb) if out else None
