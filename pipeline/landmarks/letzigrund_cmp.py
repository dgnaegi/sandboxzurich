"""Photo | game comparison sheet for Letzigrund -> preview/letzi_cmp.jpg (needs the dev server on :5173; one headless browser)."""
import json, subprocess, os
from PIL import Image
ROOT = "/Users/danielgnagi/sandboxzurich"; os.chdir(ROOT)
j = json.load(open("research/letzigrund_photos.json")); cm = j["commons_category"]
photos = [j["letzi"]["photos"][0]["file"], cm[52]["file"], cm[33]["file"], cm[16]["file"], cm[5]["file"], cm[48]["file"]]
G = json.load(open("logs/letzi_gates.json")); CC = (-968.9, -165.9)
def gv(g, t="12:00"):
    P0 = G[g]; o = [P0[0] - CC[0], P0[1] - CC[1]]; n = (o[0] ** 2 + o[1] ** 2) ** .5; P = [P0[0] - o[0] / n * 13, P0[1] - o[1] / n * 13]; L = [CC[0] - (P[0] - CC[0]) * 0.5, CC[1] - (P[1] - CC[1]) * 0.5]
    return dict(p=[P[0], P[1], 1.7], l=L, lz=-2.0, fov=62, t=t)
V = [gv(1), gv(10), gv(2), gv(3), gv(1, "22:30"), gv(10, "22:30")]
for k, v in enumerate(V):
    v.setdefault("t", "12:00"); v["w"], v["hh"] = 640, 360
    subprocess.run(["node", "pipeline/landmarks/free_shot.mjs", f"preview/_lc{k}", json.dumps([v]), v["t"]], check=True)
W, H = 640, 360
im = Image.new("RGB", (2 * W, 6 * H))
for k in range(6):
    a = Image.open(photos[k]).convert("RGB"); a.thumbnail((W, H)); im.paste(a, (0, k * H))
    im.paste(Image.open(f"preview/_lc{k}_0.jpg").convert("RGB").resize((W, H)), (W, k * H))
im.thumbnail((1500, 2400)); im.save("preview/letzi_cmp.jpg", quality=82)
