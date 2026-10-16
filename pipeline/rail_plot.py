"""Debug plot of the rail net + routes (PIL): python rail_plot.py out.png x0 y0 x1 y1 [width_px]"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "."); import terrain, rail_net
out, x0, y0, x1, y1 = sys.argv[1], *map(float, sys.argv[2:6])
W = int(sys.argv[6]) if len(sys.argv) > 6 else 1600
sc = W / (x1 - x0); Hh = int((y1 - y0) * sc)
H = terrain.heights((-2849.0, -2069.0, 1952.0, 1454.0), 2.0, z_shift=-3.06)
net = rail_net.load(H)
im = Image.new("RGB", (W, Hh), "white"); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - x0) * sc, (y1 - y) * sc)
col = {None: "black", "crossover": "magenta", "yard": "blue", "siding": "green", "spur": "olive"}
for w in net.ways:
    p = w["pts"]; d.line([P(a, b) for a, b in p[:, :2]], fill=col[w["svc"]] if w["cls"] != "tunnel" else "gray", width=1 if w["cls"] == "ground" else 3)
R = json.load(open("../web/public/data/rail.json"))["routes"]
pal = ["#e6194b", "#3cb44b", "#f58231", "#911eb4", "#46f0f0", "#f032e6"]
for i, r in enumerate(R):
    a = np.array(r["pts"]).reshape(-1, 3) / 10
    d.line([P(x, y) for x, y in a[:, :2]], fill=pal[i % 6], width=4)
    cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(a[:, :2], axis=0), axis=1))])
    for s in r["stops"]:
        j = min(np.searchsorted(cum, s["s"]), len(a) - 1); x, y = P(*a[j, :2]); d.ellipse([x - 7, y - 7, x + 7, y + 7], outline="red", width=3)
for n, t in net.nodetags.items():
    x, y = P(*net.nodes[n]); c = {"switch": "cyan", "signal": "red", "buffer_stop": "brown", "railway_crossing": "green"}[t["railway"]]
    d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=c)
for p in net.plats:
    d.line([P(a, b) for a, b in p["xy"]], fill="orange", width=3)
im.save(out)
