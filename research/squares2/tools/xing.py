"""Find local coords of street crossings / named places. usage: xing.py "A" "B"  |  xing.py place "Name" """
import sys, json
sys.path.insert(0, "pipeline")
import sources
nodes, els = sources.osm()
ways = [e for e in els if e["type"] == "way" and "nodes" in e]
def ns(name):
    s = {}
    for w in ways:
        if w.get("tags", {}).get("name", "") == name and "highway" in w["tags"]:
            for n in w["nodes"]:
                s[n] = nodes.get(n)
    return s
if sys.argv[1] == "place":
    for e in els:
        t = e.get("tags", {})
        if sys.argv[2].lower() in t.get("name", "").lower() and t.get("name"):
            if e["type"] == "node" and e["id"] in nodes: print("node", e["id"], t.get("name"), [round(v, 1) for v in nodes[e["id"]]], t.get("amenity") or t.get("place") or t.get("highway") or t.get("leisure"))
            elif e["type"] == "way" and e.get("nodes") and e["nodes"][0] in nodes:
                xs = [nodes[n] for n in e["nodes"] if n in nodes]; print("way", e["id"], t.get("name"), [round(sum(a)/len(a), 1) for a in zip(*xs)], t.get("leisure") or t.get("highway") or t.get("place") or t.get("landuse"))
else:
    a, b = ns(sys.argv[1]), ns(sys.argv[2])
    for n in set(a) & set(b): print(sys.argv[1], sys.argv[2], [round(v, 1) for v in a[n]])
    if not set(a) & set(b): print("no shared node; a:", len(a), "b:", len(b))
