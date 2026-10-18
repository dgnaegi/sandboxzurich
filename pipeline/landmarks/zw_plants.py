"""Cheap alpha-card vegetation for the Zentralwaescherei landmark: one 512x256 leaf atlas (4x2 cells of 128 px, alpha-tested), crossed quads."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CELLS = {"ivy": 0, "shrub": 1, "grass": 2, "crown": 3, "ivy2": 4, "bush2": 5, "weeds": 6, "crown2": 7}


def leaf(d, x, y, r, col, rng, ang):
    c, s = math.cos(ang), math.sin(ang)
    pts = [(x + (px * c - py * s) * r, y + (px * s + py * c) * r) for px, py in ((-1, 0), (-.4, -.55), (.5, -.5), (1.2, 0), (.5, .5), (-.4, .55))]
    d.polygon(pts, fill=col + (255,)); d.line([(x - r * c, y - r * s), (x + r * 1.1 * c, y + r * 1.1 * s)], fill=tuple(int(v * .7) for v in col) + (255,), width=1)


def tex_plants(seed=5):
    rng = np.random.default_rng(seed); im = Image.new("RGBA", (512, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    gs = [(58, 112, 44), (74, 130, 52), (96, 150, 60), (44, 92, 40), (120, 160, 70)]
    for name, k in CELLS.items():
        x0, y0 = (k % 4) * 128, (k // 4) * 128
        if name.startswith("ivy"):   # hanging strands, wider at top
            for sx in np.linspace(14, 114, 8):
                for j in range(int(rng.integers(9, 16))):
                    y = 4 + j * 8 + rng.uniform(-2, 2); leaf(d, x0 + sx + rng.uniform(-5, 5), y0 + y, rng.uniform(5, 8), gs[int(rng.integers(0, 5))], rng, rng.uniform(0.6, 2.5))
                d.line([(x0 + sx, y0), (x0 + sx, y0 + 100)], fill=(60, 52, 36, 255), width=1)
        elif name in ("shrub", "bush2", "crown", "crown2"):
            n, R = (90, 56) if name.startswith("crown") else (60, 48)
            for _ in range(n):
                a, r = rng.uniform(0, 6.28), math.sqrt(rng.uniform(0, 1)) * R
                x, y = x0 + 64 + math.cos(a) * r, y0 + (60 if name.startswith("crown") else 80) + math.sin(a) * r * (1.0 if name.startswith("crown") else .6)
                leaf(d, x, y, rng.uniform(7, 12), gs[int(rng.integers(0, 5))], rng, rng.uniform(0, 6.28))
        else:   # grass / weeds: blades from the bottom
            for _ in range(46):
                bx = x0 + rng.uniform(10, 118); h = rng.uniform(34, 110) if name == "grass" else rng.uniform(20, 70); lean = rng.uniform(-18, 18)
                col = gs[int(rng.integers(0, 5))] if name == "grass" else (110, 140, 60)
                d.polygon([(bx - 2, y0 + 126), (bx + 2, y0 + 126), (bx + lean, y0 + 126 - h)], fill=col + (255,))
    a = np.array(im); a[:, :, 3] = np.where(a[:, :, 3] > 100, 255, 0); return Image.fromarray(a, "RGBA")


def uvc(name, pad=0.004):
    k = CELLS[name]; cx, cy = k % 4, k // 4
    return (cx * .25 + pad, 1 - (cy + 1) * .5 + pad, (cx + 1) * .25 - pad, 1 - cy * .5 - pad)


def card(m, mp, cx, cy, z0, w, h, rot, cell, col=(255, 255, 255, 255), cross=True):
    u0, v0, u1, v1 = uvc(cell)
    for r in ((rot, rot + math.pi / 2) if cross else (rot,)):
        dx, dy = math.cos(r) * w / 2, math.sin(r) * w / 2
        m.quad(mp, [(cx - dx, cy - dy, z0), (cx + dx, cy + dy, z0), (cx + dx, cy + dy, z0 + h), (cx - dx, cy - dy, z0 + h)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], col=col, n=(0, 0, 1))
