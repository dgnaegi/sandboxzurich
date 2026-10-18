"""Idaplatz photo | game comparison. Usage: python ida_cmp.py views  -> prints the free_shot.mjs views JSON;  python ida_cmp.py sheet -> preview/ida_cmp.jpg
(game shots from free_shot.mjs: preview/ida_cmp_<i>.jpg)"""
import json, math, sys
from PIL import Image, ImageDraw
ROOT = "/Users/danielgnagi/sandboxzurich/"
# (index in research/v3/ida_index.json, x, y, heading deg); 38 = Commons church photo, position/heading derived
VIEWS = [(37, -107.1, -1107.5, 225), (0, -74.6, -1114.2, 259), (1, -81.0, -1117.0, 289), (13, -79.0, -1116.8, 322), (11, -94.4, -1030.9, 212),
         (20, -144.1, -1064.2, 126), (51, -128.3, -1065.6, 229), (52, -173.0, -1104.4, 52), (81, -179.6, -1118.5, 213), (38, -138.0, -1226.0, 208)]
if __name__ == "__main__":
    if sys.argv[1] == "views":
        out = []
        for i, x, y, h in VIEWS:
            r = math.radians(h); out.append(dict(p=[x, y, 1.6], l=[round(x + 30 * math.sin(r), 1), round(y + 30 * math.cos(r), 1), 2.5], fov=72, w=800, hh=600))
        print(json.dumps(out))
    else:
        idx = json.load(open(ROOT + "research/v3/ida_index.json")); W, H = 400, 300
        sh = Image.new("RGB", (W * 4, H * 5), "#222"); d = ImageDraw.Draw(sh)
        for n, (i, *_r) in enumerate(VIEWS):
            for k, f in enumerate((ROOT + idx[str(i)]["file"], ROOT + f"preview/ida_cmp_{n}.jpg")):
                im = Image.open(f).convert("RGB"); im.thumbnail((W, H)); col = (n % 2) * 2 + k; row = n // 2
                sh.paste(im, (col * W, row * H)); d.text((col * W + 3, row * H + 3), ("Foto #%d" % i) if k == 0 else "Spiel", fill="yellow")
        sh.save(ROOT + "preview/ida_cmp.jpg", quality=80); print("ok")
