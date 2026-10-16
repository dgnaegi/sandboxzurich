"""In-game views in the HB frame (d, c, h): hb_game.py out_prefix '[[d,c,h, d,c,h, fov], ...]' -> node hb_game_shot.mjs (test server :5176)."""
import json, subprocess, sys
sys.path.insert(0, '.')
from hb_kit import to_world
out, views = sys.argv[1], json.loads(sys.argv[2])
vs = []
for v in views:
    p = to_world(v[0], v[1]); l = to_world(v[3], v[4])
    vs.append({"p": [round(p[0], 1), round(p[1], 1), v[2]], "l": [round(l[0], 1), round(l[1], 1), v[5]], "fov": v[6] if len(v) > 6 else 60, "w": 900, "hh": 500, "t": __import__("os").environ.get("T", "12:00"), "wait": 7000})
r = subprocess.run(["node", "hb_game_shot.mjs", out, json.dumps(vs)], capture_output=True, text=True)
print(r.stdout[-600:], r.stderr[-300:])
