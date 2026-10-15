"""OSM building/named ways cache (data/build/lm_osm.pkl) + query: osmq.py term1 term2 ... (AND, case-insens.)"""
import sys, pickle
from common import *
CACHE = ROOT / "data" / "build" / "lm_osm.pkl"
if not CACHE.exists():
    import sources
    nodes, els = sources.osm()
    rows = []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way" and "nodes" in e and ("building" in t or "name" in t or "man_made" in t):
            pts = [nodes[n] for n in e["nodes"] if n in nodes]
            if len(pts) > 3: rows.append((t, pts))
    pickle.dump(rows, open(CACHE, "wb"))
rows = pickle.load(open(CACHE, "rb"))
if __name__ == "__main__":
    q = [s.lower() for s in sys.argv[1:]]
    for t, pts in rows:
        blob = " ".join(f"{k}={v}" for k, v in t.items()).lower()
        if all(s in blob for s in q):
            g = Polygon(pts).buffer(0); c = g.centroid
            print("(%.0f,%.0f) a=%.0f" % (c.x, c.y, g.area), {k: v for k, v in t.items() if k in ("name", "addr:street", "addr:housenumber", "building", "building:levels", "height", "start_date", "roof:shape")})
