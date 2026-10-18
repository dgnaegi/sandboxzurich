"""Roof height map of swissBUILDINGS3D around a point. Usage: schlachthof_hmap.py cx cy half out.png [ids...]"""
import pickle, glob, sys
import numpy as np
from PIL import Image, ImageDraw
from common import *
cx, cy, h = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]); out = sys.argv[4]
S = 1200 / (2 * h); im = Image.new("RGB", (1200, 1200), (20, 20, 20)); d = ImageDraw.Draw(im)
P = lambda x, y: ((x - cx + h) * S, (cy + h - y) * S)
g0 = ground(cx, cy); items = []
for f in sorted(glob.glob(str(ROOT / "data/build/bld/*.pkl"))):
    for b in pickle.load(open(f, "rb")):
        for k, p in b["polys"]:
            if abs(p[:, 0].mean() - cx) < h * 1.2 and abs(p[:, 1].mean() - cy) < h * 1.2: items.append((k, p, b["id"]))
items.sort(key=lambda t: t[1][:, 2].mean())
for k, p, i in items:
    z = p[:, 2].mean() - g0
    c = int(min(255, max(0, z * 9))); d.polygon([P(*q[:2]) for q in p], fill=(c, 255 - c // 2 if z < 20 else 120, 255 - c))
for k in range(-int(h // 25), int(h // 25) + 1):
    gx = round(cx / 25) * 25 + k * 25; gy = round(cy / 25) * 25 + k * 25
    d.line([P(gx, cy - h), P(gx, cy + h)], fill=(90, 90, 90)); d.text(P(gx, cy + h - 8), str(gx), fill=(255, 255, 0))
    d.line([P(cx - h, gy), P(cx + h, gy)], fill=(90, 90, 90)); d.text(P(cx - h + 3, gy), str(gy), fill=(255, 255, 0))
im.save(out); print(g0)
