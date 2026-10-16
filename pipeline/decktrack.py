"""Deck heights for vehicle paths (cars, bikes, buses, trams): which vertices of a polyline run ON a bridge deck.

A path only follows the decks of bridges built from its own OSM ways (bridge["ids"] vs the ways the path is made of),
so a road passing underneath never jumps up. Result per vertex: deck z (surface height, m) or None = terrain."""
import numpy as np
from shapely import STRtree
from shapely.geometry import LineString, Point

REACH = 0.8


class DeckTrack:
    def __init__(self, bridges):
        self.segs, self.meta = [], []
        for b in bridges:
            p = np.array(b["p"])
            ids = set(b["ids"])
            for i in range(len(p) - 1):
                self.segs.append(LineString(p[i:i + 2, :2]))
                self.meta.append((p[i], p[i + 1], b["w"] / 2 + REACH, ids))
        self.tree = STRtree(self.segs)

    def z(self, pts, way_ids):
        """pts [(x, y)], way_ids = OSM way ids the path consists of -> [deck z or None] per vertex."""
        way_ids = set(way_ids)
        out = []
        for x, y in pts:
            best = None
            for j in self.tree.query(Point(x, y).buffer(12)):
                a, b, hw, ids = self.meta[j]
                if not ids & way_ids:
                    continue
                d = b[:2] - a[:2]
                L2 = float(d @ d) or 1e-9
                t = min(1.0, max(0.0, float(((x, y) - a[:2]) @ d) / L2))
                q = a[:2] + d * t
                dd = (q[0] - x) ** 2 + (q[1] - y) ** 2
                if dd <= hw * hw and (best is None or dd < best[0]):
                    best = (dd, float(a[2] + (b[2] - a[2]) * t))
            out.append(None if best is None else round(best[1], 2))
        return out
