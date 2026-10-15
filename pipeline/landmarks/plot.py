import sys
from PIL import Image, ImageDraw
from common import *
x, y, r = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]); out = sys.argv[4]
S = 900 / (2 * r)
im = Image.new("RGB", (900, 900), "white"); d = ImageDraw.Draw(im)
def P(px, py): return ((px - x + r) * S, (y + r - py) * S)
for b in near(x, y, r * 1.5):
    for g in (b["fp"].geoms if hasattr(b["fp"], "geoms") else [b["fp"]]):
        pts = [P(*q) for q in g.exterior.coords]
        zz = min(1, max(0, (b["zmax"] + 10) / 80))
        d.polygon(pts, fill=(int(255 - 160 * zz), int(230 - 120 * zz), 200), outline="black")
    cx, cy = P(*b["c"]); d.text((cx - 12, cy - 5), "%.0f" % (b["zmax"] - b["zmin"]), fill="black")
im.save(out)
