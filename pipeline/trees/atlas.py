"""Procedural leaf atlas (grey-scale luminance + alpha; hue comes from vertex colours).
Layout: 4 x 2 tiles of 128 px -> 512 x 256. Tile index = row*4 + col.
 0 broadleaf cluster, 1 small round leaves (linden/cherry), 2 maple, 3 birch (small, pointed),
 4 blossom, 5 conifer spray, 6 chestnut palmate, 7 chestnut candle.
Run: python3 pipeline/trees/atlas.py
"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

T = 128
SS = 4  # supersampling
OUT = Path(__file__).resolve().parents[2] / "web/public/models/trees/leaves.webp"


def leaf_poly(cx, cy, length, width, ang, pointed=0.5, n=14):
    pts = []
    for side in (1, -1):
        for i in range(n + 1):
            t = i / n if side == 1 else 1 - i / n
            # width profile: widest at ~40%, pointed tip
            w = math.sin(math.pi * t ** (0.8 + pointed * 0.4)) * width * 0.5 * side
            x, y = t * length, w
            pts.append((cx + x * math.cos(ang) - y * math.sin(ang),
                        cy + x * math.sin(ang) + y * math.cos(ang)))
    return pts


def grey(v):
    v = max(0, min(255, int(v)))
    return (v, v, v, 255)


def draw_leaf(d, cx, cy, length, width, ang, rng, pointed=0.5, base=0.8):
    v = 255 * min(1, base * rng.uniform(0.62, 1.0))
    d.polygon(leaf_poly(cx, cy, length, width, ang, pointed), fill=grey(v))
    ex, ey = cx + length * 0.92 * math.cos(ang), cy + length * 0.92 * math.sin(ang)
    d.line([(cx, cy), (ex, ey)], fill=grey(min(255, v * 1.18)), width=max(1, int(SS * 0.7)))


def tile_img():
    return Image.new("RGBA", (T * SS, T * SS), (170, 170, 170, 0))


def cluster(rng, n, length, width, spread, pointed=0.5, center=(0.5, 0.5), base=0.85):
    im = tile_img(); d = ImageDraw.Draw(im)
    S = T * SS
    order = []
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, spread) * S
        order.append((r, a))
    for r, a in sorted(order, reverse=True):
        cx = S * center[0] + r * math.cos(a) * 0.9
        cy = S * center[1] + r * math.sin(a) * 0.9
        ang = a + rng.uniform(-0.7, 0.7)
        # leaves start at their base, pointing outward
        draw_leaf(d, cx, cy, length * S * rng.uniform(0.85, 1.15), width * S, ang, rng, pointed,
                  base * (0.7 + 0.3 * (r / (spread * S + 1e-6))))
    return im


def maple(rng):
    im = tile_img(); d = ImageDraw.Draw(im); S = T * SS
    for k in range(4):
        cx = S * (0.3 + 0.4 * rng.random()); cy = S * (0.3 + 0.4 * rng.random())
        R = S * rng.uniform(0.2, 0.27); rot = rng.uniform(0, 6.28)
        pts = []
        for i in range(10 * 5):
            a = rot + i / 50 * 2 * math.pi
            lobe = abs(math.cos(a - rot) ** 2 * 0 + math.cos(2.5 * (a - rot)))
            r = R * (0.45 + 0.55 * lobe ** 0.6)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        v = 255 * rng.uniform(0.6, 0.95)
        d.polygon(pts, fill=grey(v))
        for j in range(5):
            a = rot + j * 2 * math.pi / 5
            d.line([(cx, cy), (cx + R * 0.8 * math.cos(a), cy + R * 0.8 * math.sin(a))], fill=grey(min(255, v * 1.2)), width=SS)
    return im


def blossom(rng):
    im = tile_img(); d = ImageDraw.Draw(im); S = T * SS
    for i in range(34):
        cx = S * rng.uniform(0.12, 0.88); cy = S * rng.uniform(0.12, 0.88)
        if (cx - S / 2) ** 2 + (cy - S / 2) ** 2 > (S * 0.42) ** 2:
            continue
        r = S * rng.uniform(0.05, 0.075); v = 255 * rng.uniform(0.82, 1.0)
        ph = rng.uniform(0, 6.28)
        for p in range(5):
            a = ph + p * 2 * math.pi / 5
            px, py = cx + r * 0.7 * math.cos(a), cy + r * 0.7 * math.sin(a)
            d.ellipse([px - r * .6, py - r * .6, px + r * .6, py + r * .6], fill=grey(v))
        d.ellipse([cx - r * .25, cy - r * .25, cx + r * .25, cy + r * .25], fill=grey(v * 0.55))
    # a few green-ish leaves behind give depth (luminance only)
    for i in range(8):
        draw_leaf(d, S * rng.uniform(.3, .7), S * rng.uniform(.3, .7), S * .12, S * .06, rng.uniform(0, 6.28), rng, .5, .55)
    return im


def conifer(rng):
    im = tile_img(); d = ImageDraw.Draw(im); S = T * SS
    # branchlet pointing right from left-centre with needle-clumps
    d.line([(S * .04, S * .5), (S * .96, S * .5)], fill=grey(110), width=SS * 2)
    for i in range(46):
        t = rng.uniform(0.05, 0.95); x = S * t
        sp = (1 - t) * 0.40 + 0.04
        for side in (-1, 1):
            L = S * sp * rng.uniform(0.6, 1.0)
            ang = side * rng.uniform(0.9, 1.35) + rng.uniform(-.2, .2)
            ex, ey = x + L * math.cos(ang) * 0.55, S * .5 + L * math.sin(ang)
            v = 255 * rng.uniform(0.55, 0.95)
            d.line([(x, S * .5), (ex, ey)], fill=grey(v), width=int(SS * 1.8))
            d.ellipse([ex - SS * 2, ey - SS * 2, ex + SS * 2, ey + SS * 2], fill=grey(v))
    return im


def candle(rng):
    im = tile_img(); d = ImageDraw.Draw(im); S = T * SS
    d.line([(S * .5, S * .98), (S * .5, S * .5)], fill=grey(120), width=SS * 2)
    for i in range(130):
        y = S * rng.uniform(0.04, 0.9)
        w = (0.06 + 0.2 * (y / S)) * S * (1 - 0.15 * rng.random())
        x = S * .5 + rng.uniform(-1, 1) * w * 0.85
        r = S * rng.uniform(.025, .045); v = 255 * rng.uniform(.85, 1)
        d.ellipse([x - r, y - r, x + r, y + r], fill=grey(v))
        if rng.random() < .15:
            d.ellipse([x - r * .4, y - r * .4, x + r * .4, y + r * .4], fill=grey(v * .6))
    return im


def build():
    rng = random.Random(7)
    tiles = [
        cluster(rng, 22, 0.26, 0.15, 0.30, 0.5),
        cluster(rng, 30, 0.17, 0.14, 0.34, 0.25, base=0.9),
        maple(rng),
        cluster(rng, 36, 0.16, 0.085, 0.36, 0.8, base=0.9),
        blossom(rng),
        conifer(rng),
        cluster(rng, 7, 0.40, 0.17, 0.05, 0.5, center=(0.5, 0.5), base=0.85),
        candle(rng),
    ]
    atlas = Image.new("RGBA", (T * 4, T * 2), (0, 0, 0, 0))
    for i, im in enumerate(tiles):
        r, g, b, a = im.split()
        # blur RGB beyond alpha edge to avoid dark fringes, then downsample
        small = im.resize((T, T), Image.LANCZOS)
        atlas.paste(small, ((i % 4) * T, (i // 4) * T))
    return atlas


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    a = build()
    a.save(OUT, "WEBP", quality=80, method=6, exact=True)
    print(OUT, OUT.stat().st_size, "bytes")
