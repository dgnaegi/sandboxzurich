"""Alpha-card vegetation atlas for the Quartiergarten Hard (512x512, 4x4 cells of 128 px, alpha-tested): trees/shrubs/grass from zw_plants plus
vegetable rows, flowers, bean/sunflower stalks, tomato cages, wire mesh and reed grass."""
import math
import numpy as np
from PIL import Image, ImageDraw
from zw_plants import leaf

CELLS = {n: i for i, n in enumerate(["crown", "shrub", "grass", "weeds", "ivy", "crown2", "bush2", "veg", "flow1", "flow2", "beans", "tall", "tomato", "mesh", "reed", "cab"])}
GS = [(58, 112, 44), (74, 130, 52), (96, 150, 60), (44, 92, 40), (120, 160, 70)]


def tex_atlas(seed=7):
    rng = np.random.default_rng(seed); im = Image.new("RGBA", (512, 512), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for name, k in CELLS.items():
        x0, y0 = (k % 4) * 128, (k // 4) * 128
        L = lambda x, y, r, col, a=None: leaf(d, x0 + x, y0 + y, r, col, rng, rng.uniform(0, 6.28) if a is None else a)
        if name in ("crown", "crown2", "shrub", "bush2"):
            big = name.startswith("crown"); n, R = (95, 56) if big else (60, 48)
            for _ in range(n):
                a, r = rng.uniform(0, 6.28), math.sqrt(rng.uniform(0, 1)) * R
                L(64 + math.cos(a) * r, (58 if big else 82) + math.sin(a) * r * (1 if big else .6), rng.uniform(7, 12), GS[int(rng.integers(0, 5))])
            if big: d.line([(x0 + 64, y0 + 128), (x0 + 64, y0 + 100)], fill=(70, 56, 40, 255), width=4)
        elif name == "ivy":
            for sx in np.linspace(12, 116, 8):
                for j in range(int(rng.integers(9, 15))):
                    L(sx + rng.uniform(-5, 5), 4 + j * 8, rng.uniform(5, 8), GS[int(rng.integers(0, 5))], rng.uniform(.6, 2.5))
        elif name in ("grass", "weeds", "reed"):
            for _ in range(46):
                bx = x0 + rng.uniform(10, 118); h = {"grass": rng.uniform(34, 110), "weeds": rng.uniform(20, 70), "reed": rng.uniform(70, 124)}[name]
                col = GS[int(rng.integers(0, 5))] if name != "reed" else (150, 140, 80)
                d.polygon([(bx - 2, y0 + 126), (bx + 2, y0 + 126), (bx + rng.uniform(-18, 18), y0 + 126 - h)], fill=col + (255,))
                if name == "reed" and rng.random() < .5: d.ellipse([bx - 3, y0 + 126 - h - 8, bx + 3, y0 + 126 - h + 6], fill=(178, 160, 100, 255))
        elif name in ("veg", "cab"):   # leafy rows: rosettes of big leaves at the bottom
            for cx in ([24, 64, 104] if name == "veg" else [32, 96]):
                for _ in range(14 if name == "veg" else 22):
                    a = rng.uniform(0, 6.28); r = rng.uniform(2, 20 if name == "veg" else 26)
                    L(cx + math.cos(a) * r, 100 + math.sin(a) * r * .55 - (6 if name == "cab" else 0), rng.uniform(7, 12), (92, 140, 70) if name == "veg" else (110, 150, 110))
        elif name in ("flow1", "flow2"):
            cols = [(230, 80, 120), (250, 200, 50), (240, 240, 240), (200, 80, 200)] if name == "flow1" else [(250, 160, 30), (250, 230, 60), (230, 60, 60)]
            for _ in range(46): bx = rng.uniform(10, 118); h = rng.uniform(30, 100); d.line([(x0 + bx, y0 + 126), (x0 + bx + rng.uniform(-8, 8), y0 + 126 - h)], fill=(70, 120, 50, 255), width=2)
            for _ in range(34):
                bx, by = rng.uniform(10, 118), rng.uniform(20, 100); c = cols[int(rng.integers(0, len(cols)))]; r = rng.uniform(4, 8)
                d.ellipse([x0 + bx - r, y0 + by - r, x0 + bx + r, y0 + by + r], fill=c + (255,)); d.ellipse([x0 + bx - 2, y0 + by - 2, x0 + bx + 2, y0 + by + 2], fill=(90, 60, 20, 255))
        elif name == "beans":   # poles with climbing bean leaves
            for px_ in (22, 64, 106):
                d.line([(x0 + px_, y0 + 128), (x0 + px_ + 4, y0 + 2)], fill=(140, 110, 70, 255), width=3)
                for j in range(12): L(px_ + rng.uniform(-8, 10), 118 - j * 9, rng.uniform(6, 9), GS[int(rng.integers(0, 5))])
        elif name == "tall":   # sunflower / corn
            for px_ in (30, 70, 108):
                d.line([(x0 + px_, y0 + 128), (x0 + px_, y0 + 34)], fill=(80, 130, 50, 255), width=4)
                for j in range(4): L(px_ + (14 if j % 2 else -14), 112 - j * 18, 11, (70, 130, 50), 0 if j % 2 else 3.14)
                d.ellipse([x0 + px_ - 13, y0 + 20, x0 + px_ + 13, y0 + 46], fill=(245, 200, 30, 255)); d.ellipse([x0 + px_ - 7, y0 + 27, x0 + px_ + 7, y0 + 40], fill=(90, 56, 20, 255))
        elif name == "tomato":
            for px_ in (30, 64, 98):
                for q in (-9, 9): d.line([(x0 + px_ + q, y0 + 128), (x0 + px_ + q, y0 + 20)], fill=(150, 150, 150, 255), width=2)
                for j in range(5): d.line([(x0 + px_ - 9, y0 + 112 - j * 20), (x0 + px_ + 9, y0 + 112 - j * 20)], fill=(150, 150, 150, 255), width=1)
                for j in range(26): L(px_ + rng.uniform(-14, 14), 20 + rng.uniform(0, 100), rng.uniform(5, 8), GS[int(rng.integers(0, 5))])
                for j in range(5): ex, ey = x0 + px_ + rng.uniform(-10, 10), y0 + 60 + rng.uniform(0, 50); d.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], fill=(210, 50, 40, 255))
        elif name == "mesh":
            c = Image.new("RGBA", (128, 128), (0, 0, 0, 0)); dc = ImageDraw.Draw(c)
            for t in range(-128, 256, 14):
                dc.line([(t, 0), (t + 128, 128)], fill=(120, 126, 120, 255), width=1); dc.line([(t + 128, 0), (t, 128)], fill=(120, 126, 120, 255), width=1)
            dc.line([(0, 1), (127, 1)], fill=(90, 96, 90, 255), width=3); dc.line([(0, 126), (127, 126)], fill=(90, 96, 90, 255), width=3)
            im.paste(c, (x0, y0))
    a = np.array(im); a[:, :, 3] = np.where(a[:, :, 3] > 100, 255, 0); return Image.fromarray(a, "RGBA")


def uvc(name, pad=0.004):
    k = CELLS[name]; cx, cy = k % 4, k // 4
    return (cx * .25 + pad, 1 - (cy + 1) * .25 + pad, (cx + 1) * .25 - pad, 1 - cy * .25 - pad)


def card(m, mp, cx, cy, z0, w, h, rot, cell, col=(255, 255, 255, 255), cross=True):
    u0, v0, u1, v1 = uvc(cell)
    for r in ((rot, rot + math.pi / 2) if cross else (rot,)):
        dx, dy = math.cos(r) * w / 2, math.sin(r) * w / 2
        m.quad(mp, [(cx - dx, cy - dy, z0), (cx + dx, cy + dy, z0), (cx + dx, cy + dy, z0 + h), (cx - dx, cy - dy, z0 + h)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], col=col, n=(0, 0, 1))
