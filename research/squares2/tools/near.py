"""near.py x y r -> OSM ways/nodes with tags within r m"""
import sys
sys.path.insert(0, "pipeline")
import sources
x, y, r = map(float, sys.argv[1:4])
nodes, els = sources.osm()
for e in els:
    t = e.get("tags")
    if not t: continue
    if e["type"] == "node" and e["id"] in nodes:
        p = nodes[e["id"]]
        if abs(p[0]-x) < r and abs(p[1]-y) < r: print("N", e["id"], [round(v-c, 1) for v, c in zip(p, (x, y))], {k: v for k, v in t.items() if k not in ("source",)})
    elif e["type"] == "way" and e.get("nodes"):
        xs = [nodes[n] for n in e["nodes"] if n in nodes]
        if not xs: continue
        cx = sum(a[0] for a in xs)/len(xs); cy = sum(a[1] for a in xs)/len(xs)
        if abs(cx-x) < r and abs(cy-y) < r: print("W", e["id"], [round(cx-x, 1), round(cy-y, 1)], len(xs), {k: v for k, v in t.items() if k not in ("source", "addr:country", "addr:city", "addr:postcode")})
