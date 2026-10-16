import sys
sys.path.insert(0, "pipeline")
import sources
nodes, els = sources.osm()
ways = [e for e in els if e["type"] == "way" and "nodes" in e and "highway" in e.get("tags", {})]
def ns(name):
    s = {}
    for w in ways:
        if w["tags"].get("name", "") == name:
            for n in w["nodes"]: s[n] = nodes.get(n)
    return s
pairs = ["Langstrasse|Dienerstrasse","Langstrasse|Militärstrasse","Brauerstrasse|Hohlstrasse","Bertastrasse|Zurlindenstrasse","Limmatstrasse|Röntgenstrasse","Birmensdorferstrasse|Zweierstrasse","Zurlindenstrasse|Zweierstrasse","Hohlstrasse|Sihlfeldstrasse","Hardstrasse|Hardbrücke","Stauffacherstrasse|Badenerstrasse","Stauffacherstrasse|Kanzleistrasse","Langstrasse|Zollstrasse","Hohlstrasse|Kanzleistrasse","Hohlstrasse|Langstrasse","Goldbrunnenstrasse|Birmensdorferstrasse"]
for p in pairs:
    a, b = p.split("|"); A, B = ns(a), ns(b)
    c = [A[n] for n in set(A) & set(B)]
    print(p, [[round(v, 1) for v in q] for q in c[:3]] or "none")
names = ["Brupbacher","Ernst-Nobs","Goldbrunnen","Schmiedeplatz","Löwenbrunnen","Bahnhof Wiedikon","Hardbrücke","Bahnhof Altstetten","Stauffacher","Sihlfeld","Kanzleiareal","Kanzlei"]
for e in els:
    t = e.get("tags", {}); nm = t.get("name", "")
    if not nm or not any(k.lower() in nm.lower() for k in names): continue
    if e["type"] == "node" and e["id"] in nodes: print("node", nm, [round(v, 1) for v in nodes[e["id"]]], t.get("railway") or t.get("amenity") or t.get("public_transport") or t.get("tourism") or "")
    elif e["type"] == "way" and e.get("nodes") and e["nodes"][0] in nodes and "highway" not in t:
        xs = [nodes[n] for n in e["nodes"] if n in nodes]; print("way", nm, [round(sum(a)/len(a), 1) for a in zip(*xs)], t.get("leisure") or t.get("railway") or t.get("building") or t.get("public_transport") or "")
