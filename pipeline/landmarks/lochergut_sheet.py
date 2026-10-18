"""Authoring sheet for the Lochergut square: SWISSIMAGE + grid + OGD objects. Usage: python lochergut_sheet.py [cx cy win] -> preview/lochergut_sheet.jpg"""
import json, sys
sys.path.insert(0, "/Users/danielgnagi/sandboxzurich/pipeline")
from PIL import Image, ImageDraw
from config import ROOT
import ortho
cx, cy, win = (float(v) for v in sys.argv[1:4]) if len(sys.argv) > 3 else (80.0, -935.0, 120.0)
f = ortho.fetch("lochergut", 80, -930, 160, 1600)
im = Image.open(f).convert("RGB"); ppm = im.width / 160.0
x0, y0 = (cx - win / 2 - 80) * ppm + 800, (-930 - (cy + win / 2)) * ppm + 800
out = im.crop((int(x0), int(y0), int(x0 + win * ppm), int(y0 + win * ppm))).resize((1000, 1000), Image.LANCZOS)
k = 1000 / win; d = ImageDraw.Draw(out); P = lambda x, y: ((x - (cx - win / 2)) * k, ((cy + win / 2) - y) * k)
for v in range(-int(win / 2 // 10) * 10, int(win / 2) + 1, 10):
    a = P(cx + v, cy)[0]; b = P(cx, cy + v)[1]
    d.line([(a, 0), (a, 1000)], fill=(255, 255, 255), width=1); d.line([(0, b), (1000, b)], fill=(255, 255, 255), width=1)
    d.text((a + 2, 2), str(int(cx + v)), fill=(255, 255, 0)); d.text((2, b + 2), str(int(cy + v)), fill=(255, 255, 0))
C = json.load(open(next((ROOT / "data/build").glob("citydata_v2_-2849*.json"))))
sty = {"trees": ((0, 200, 0), 4), "benches": ((255, 140, 0), 4), "bins": ((255, 0, 255), 3), "fountains": ((0, 160, 255), 5), "lights": ((255, 255, 0), 3), "bikes": ((255, 80, 160), 3)}
for layer, (col, r) in sty.items():
    for row in C.get(layer, []):
        if abs(row[0] - cx) < win / 2 and abs(row[1] - cy) < win / 2:
            px, py = P(row[0], row[1]); d.ellipse((px - r, py - r, px + r, py + r), outline=col, width=2)
out.save(ROOT / "preview/lochergut_sheet.jpg", quality=85); print("ok")
