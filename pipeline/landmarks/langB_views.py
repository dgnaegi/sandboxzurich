"""Camera views for free_shot.mjs: street-side view of each langB landmark. Usage: langB_views.py day|night > views.json"""
import json, math, sys
from pathlib import Path
R = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent))
E = {e["addr"]: e for e in json.load(open(R / "research/shops_v3/entrances_langB.json"))}
L = {e["name"]: e for e in json.load(open(R / "pipeline/overrides/landmarks_langB.json"))["landmarks"]}
import langB_all as A
mode = sys.argv[1] if len(sys.argv) > 1 else "day"
order = ["rothaus", "rossi", "lambada", "diamond", "fattony", "klaus", "hungryduck", "blackout", "milano", "gotthard", "l104", "negresco"] if mode == "day" else ["lambada", "diamond", "negresco", "fattony", "rossi", "hungryduck"]
out = []
for k in order:
    title, ids, addr, kw = A.S[k]; l = L[title]; e = E.get(addr) or min(E.values(), key=lambda q: math.hypot(q['x'] - l['x'], q['y'] - l['y']))
    dx, dy = e["x"] - l["x"], e["y"] - l["y"]; n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n; d = 15
    out.append(dict(p=[e["x"] + ux * 9, e["y"] + uy * 9, 2.0], l=[l["x"] + ux * 3, l["y"] + uy * 3, 3.0], fov=60, t="12:30" if mode == "day" else "22:30", w=800, hh=600, wait=3500))
print(json.dumps(out))
