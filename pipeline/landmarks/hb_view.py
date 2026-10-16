"""Isolated-model views in the HB frame. usage: hb_view.py out_prefix 'Model name' '[ [d,c,h, d,c,h, fov], ...]' [night]
Positions are in model frame (d,c,h above terrain); converted to world offsets for view.mjs. Needs the dev server on :5173."""
import json, subprocess, sys, math
sys.path.insert(0, '.')
from hb_kit import to_world, ORG
out, name, views = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
night = float(sys.argv[4]) if len(sys.argv) > 4 else 0
vs = []
for v in views:
    p = to_world(v[0], v[1]); l = to_world(v[3], v[4])
    vs.append({"m": name, "p": [round(p[0] - ORG[0], 2), round(p[1] - ORG[1], 2), v[2]], "l": [round(l[0] - ORG[0], 2), round(l[1] - ORG[1], 2), v[5]], "fov": v[6] if len(v) > 6 else 55, "n": night})
r = subprocess.run(["node", "view.mjs", out, json.dumps(vs)], capture_output=True, text=True)
print(r.stdout[-400:], r.stderr[-300:])
