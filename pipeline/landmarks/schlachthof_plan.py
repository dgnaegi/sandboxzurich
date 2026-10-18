"""Plan: SWISSIMAGE crop + building footprints with indices. Usage: schlachthof_plan.py cx cy half out.jpg"""
import sys, requests
from common import *
from PIL import Image, ImageDraw
cx, cy, h = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]); out = sys.argv[4]
e, n = 2681400 + cx, 1248700 + cy
r = requests.get("https://wms.geo.admin.ch/", params=dict(SERVICE="WMS", VERSION="1.1.1", REQUEST="GetMap", LAYERS="ch.swisstopo.images-swissimage", STYLES="", SRS="EPSG:2056", BBOX=f"{e-h},{n-h},{e+h},{n+h}", WIDTH=1600, HEIGHT=1600, FORMAT="image/jpeg"))
open(out.replace(".jpg", "_raw.jpg"), "wb").write(r.content)
im = Image.open(out.replace(".jpg", "_raw.jpg")).convert("RGB"); S = im.width / (2 * h); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - cx + h) * S, (cy + h - y) * S)
bs = [b for b in all_buildings() if b["fp"].distance(Point(cx, cy)) < h * 1.1]
for i, b in enumerate(bs):
    for g in (b["fp"].geoms if hasattr(b["fp"], "geoms") else [b["fp"]]):
        d.line([P(*q) for q in g.exterior.coords], fill=(255, 255, 0), width=2)
    px, py = P(*b["c"]); d.text((px - 10, py - 5), b["id"][3:9], fill=(255, 40, 40))
for k in range(-int(h // 50), int(h // 50) + 1):
    gx = round(cx / 50) * 50 + k * 50; gy = round(cy / 50) * 50 + k * 50
    d.line([P(gx, cy - h), P(gx, cy + h)], fill=(0, 255, 255), width=1); d.text(P(gx, cy + h - 8), str(gx), fill=(0, 255, 255))
    d.line([P(cx - h, gy), P(cx + h, gy)], fill=(0, 255, 255), width=1); d.text(P(cx - h + 3, gy), str(gy), fill=(0, 255, 255))
im.resize((1200, 1200)).save(out, quality=85)
