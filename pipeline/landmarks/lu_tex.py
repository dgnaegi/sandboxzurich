"""Procedural textures for the Langstrassen-Unterfuehrung (own designs, no photo material): concrete, painted passage walls,
asphalt with markings, graffiti panels (own tags/pieces), colour swatches + emissive lamp map."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from lm import hexc

CELL = 256


def _noise(w, h, scale, seed, amp):
    r = np.random.default_rng(seed)
    g = r.normal(0, 1, (h // scale + 2, w // scale + 2)).astype(np.float32)
    im = Image.fromarray(g).resize((w, h), Image.BICUBIC)
    return np.asarray(im) * amp


def _base(color, w=CELL, h=CELL, seed=1, blot=14, fine=3):
    a = np.zeros((h, w, 3), np.float32) + np.array(color[:3], np.float32)
    n = _noise(w, h, 48, seed, blot) + _noise(w, h, 6, seed + 7, fine) + _noise(w, h, 2, seed + 11, 2)
    a += n[..., None]
    return a


def _img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def concrete(seed, color=(150, 150, 146), boards=True, ties=True, dirt=0.0):
    a = _base(color, seed=seed)
    r = np.random.default_rng(seed)
    if boards:    # horizontal formwork boards ~0.25 m (85 px/m -> 21 px)
        for y in range(0, CELL, 21):
            a[y:y + 1, :] -= 9
            a[y + 1:y + 21, :] += r.normal(0, 3)
    if ties:      # tie-rod cones
        for y in (42, 168):
            for x in (42, 126, 210):
                yy, xx = np.ogrid[:CELL, :CELL]
                a[(yy - y) ** 2 + (xx - x) ** 2 < 10] -= 28
    if dirt:      # dark streaks from the top + grime near the bottom
        s = _noise(CELL, CELL, 24, seed + 3, 1.0)
        streak = np.clip(_noise(CELL, 4, 1, seed + 5, 1.0), 0, None)
        a -= (dirt * 38 * np.clip(s, -1, 1) ** 2)[..., None]
        grad = np.linspace(0, 1, CELL)[:, None] ** 3
        a *= (1 - dirt * 0.35 * grad)[..., None]
    return _img(a)


def painted(seed, color=(226, 220, 200), dirt=0.5, niche=False):
    a = _base(color, seed=seed, blot=7, fine=2)
    yy = np.linspace(0, 1, CELL)[:, None]
    a *= (1 - dirt * 0.30 * yy ** 2 - 0.0)[..., None]
    a += 6 * (yy < 0.3)[..., None] * 0
    r = np.random.default_rng(seed)
    for _ in range(6):       # scuffs
        x, y = r.integers(0, CELL), r.integers(60, CELL)
        a[y:y + 3, x:x + r.integers(20, 70)] -= 22
    im = _img(a)
    if niche:
        d = ImageDraw.Draw(im); d.rectangle([100, 70, 156, 215], fill=(120, 114, 100, 255)); d.rectangle([103, 73, 153, 212], outline=(150, 144, 130, 255))
    return im


def ceiling(seed, color=(168, 166, 160)):
    a = _base(color, seed=seed, blot=9, fine=2)
    r = np.random.default_rng(seed)
    for _ in range(3):
        x = r.integers(0, CELL); a[:, x:x + 2] -= 18          # shuttering joints
    yy = np.linspace(0, 1, CELL)[:, None]; a -= (14 * (_noise(CELL, CELL, 40, seed + 1, 1.0) > 0.6))[..., None]
    return _img(a)


def ballast(seed):
    a = _base((118, 114, 108), seed=seed, blot=10, fine=14)
    return _img(a)


def tile_white(seed):
    a = _base((236, 234, 226), seed=seed, blot=4, fine=2)
    im = _img(a); d = ImageDraw.Draw(im)
    for k in range(0, CELL, 21):
        d.line([(0, k), (CELL, k)], fill=(150, 150, 142, 255)); d.line([(k, 0), (k, CELL)], fill=(150, 150, 142, 255))
    return im


# ---- graffiti: own pieces (bubble/blockletters, stencil stars, stripes) -------------------------------------------------------
def _font(sz):
    for p in ("/System/Library/Fonts/Supplemental/Arial Black.ttf", "/System/Library/Fonts/Supplemental/Impact.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def graffiti(seed, bg, word, cols):
    """Transparent-ish panel: wall colour bg with a throw-up (outline + fill + highlight) and some tag strokes."""
    r = np.random.default_rng(seed)
    im = Image.new("RGBA", (CELL, CELL), bg); d = ImageDraw.Draw(im)
    f = _font(76 if len(word) <= 3 else 58)
    tw = d.textlength(word, font=f); x0 = (CELL - tw) / 2 + r.integers(-8, 8); y0 = 70 + r.integers(-10, 10)
    for dx, dy in [(5, 5), (4, 4), (3, 3)]:
        d.text((x0 + dx, y0 + dy), word, font=f, fill=hexc("#101010"))
    d.text((x0, y0), word, font=f, fill=hexc(cols[0]), stroke_width=4, stroke_fill=hexc(cols[1]))
    d.text((x0 + 1, y0 - 2), word, font=f, fill=None, stroke_width=0)
    for _ in range(4):   # drips and hot spots
        x = int(x0 + r.integers(5, max(6, int(tw) - 5))); d.line([(x, y0 + 80), (x, y0 + 80 + r.integers(10, 40))], fill=hexc(cols[0]), width=3)
    for k in range(3):   # small tag strokes
        px = r.integers(20, 200); py = r.integers(10, 40) if k else 215
        pts = [(px + i * 14, py + int(8 * math.sin(i * 1.7 + k))) for i in range(6)]
        d.line(pts, fill=hexc(cols[2 + k % 2]), width=4, joint="curve")
    return im.filter(ImageFilter.GaussianBlur(0.6))


def asphalt(w, h, seed, dirt=0.0):
    a = _base((70, 70, 72), w, h, seed, blot=7, fine=5)
    a -= dirt * 8
    return _img(a)


def road_cell(seed, arrow=None):
    """6 m x 11.6 m road cell, 432 x 224 px (u across: o = -5.8..+5.8, v along s). Markings: continuous centre line, dashed lane lines, edge lines."""
    W, H = 432, 224; k = W / 11.6
    im = asphalt(W, H, seed); d = ImageDraw.Draw(im)
    X = lambda o: int((o + 5.8) * k)
    white, yellow = (224, 224, 218, 255), (214, 178, 40, 255)
    d.rectangle([X(0.5), 0, X(0.5) + 5, H], fill=white)                     # centre line (solid)
    d.rectangle([X(-5.5) , 0, X(-5.5) + 5, H], fill=white)                  # edge lines
    d.rectangle([X(5.2), 0, X(5.2) + 5, H], fill=white)
    for o in (-2.6, 3.9):                                                  # dashed lane / advisory bike lane lines
        for y0 in (20, 130):
            d.rectangle([X(o), y0, X(o) + 4, y0 + 56], fill=white if o < 0 else yellow)
    d.rectangle([X(-4.2), 0, X(-4.2) + 3, H], fill=yellow) if False else None
    if arrow == "straight":
        for o in (-1.4, 2.1):
            cx = X(o); d.polygon([(cx - 14, 120), (cx + 14, 120), (cx + 14, 70), (cx + 28, 70), (cx, 20), (cx - 28, 70), (cx - 14, 70)], fill=white)
    return im


def ped_cell(seed):
    """3.6 m x 6 m passage floor, 144 x 224 px; yellow dashed pedestrian/bike separator in the middle (as in the photos)."""
    im = asphalt(144, 224, seed, dirt=0.3); d = ImageDraw.Draw(im)
    for y0 in (6, 118):
        d.rectangle([68, y0, 75, y0 + 70], fill=(205, 172, 38, 255))
    return im


def swatches():
    """4x4 grid of 64 px cells: base colours + emissive map. 0 lamp, 1 dark grey, 2 black, 3 steel, 4 warm white lamp cover,
    5..12 mural wedge colours, 13 red/white sign, 14 yellow, 15 signal green."""
    cols = ["#ffffff", "#4b4e50", "#18191a", "#8c9296", "#f4f0e0", "#e8c21a", "#ee8a1c", "#d8392b", "#b3306e", "#6a3ea1", "#2f63b8", "#1e9fa6", "#3f9a4c", "#c9382c", "#f0d020", "#2f8f4f"]
    im = Image.new("RGBA", (256, 256)); em = Image.new("RGB", (256, 256), (0, 0, 0))
    d = ImageDraw.Draw(im); de = ImageDraw.Draw(em)
    for i, c in enumerate(cols):
        x, y = (i % 4) * 64, (i // 4) * 64
        d.rectangle([x, y, x + 63, y + 63], fill=hexc(c))
        if i in (0, 4):
            de.rectangle([x, y, x + 63, y + 63], fill=(255, 244, 214))
    return im, em


def uv_swatch(i, inset=0.08):
    x, y = (i % 4) * 0.25, 1 - ((i // 4) + 1) * 0.25   # lower-left origin, v up (lm.py flips)
    return x + 0.125, y + 0.125


def conc_tile():
    """Tiling board-formed concrete (3 m repeat), neutral grey; tinted per quad by vertex colour."""
    return concrete(1, (160, 160, 155), dirt=0.25)


def atlas():
    """1024x1024: y 0..447 floor cells (2 rows: road 432x224 | road+arrows 432x224 | passage floor 144x224),
    y 512..1023 wall cells 256x256, id 0..7: 0-1 painted cream, 2 painted with niche, 3 painted dirty, 4-7 graffiti pieces."""
    A = Image.new("RGBA", (1024, 1024), (90, 90, 90, 255))
    for r in range(2):
        A.paste(road_cell(20 + r), (0, r * 224)); A.paste(road_cell(30 + r, "straight"), (432, r * 224)); A.paste(ped_cell(40 + r), (864, r * 224))
    cells = [painted(5), painted(6, (230, 224, 206), 0.3), painted(7, niche=True), painted(8, (214, 206, 186), 0.9),
             graffiti(13, (150, 150, 146, 255), "ZRH", ["#f0c020", "#1c1c1c", "#e04a2c", "#2a74c8"]),
             graffiti(14, (226, 220, 200, 255), "NOA", ["#2fa8a0", "#14202a", "#c0306e", "#f08a1c"]),
             graffiti(15, (138, 138, 134, 255), "SKY", ["#e8e8e0", "#c0306e", "#2a74c8", "#f0c020"]),
             graffiti(16, (214, 206, 186, 255), "BLK", ["#6a3ea1", "#101010", "#e8c21a", "#3f9a4c"])]
    for i, c in enumerate(cells):
        A.paste(c, ((i % 4) * 256, 512 + (i // 4) * 256))
    return A


def uv_floor(kind, row, u0, u1, v0, v1):
    x0, w = {"road": (0, 432), "arrow": (432, 432), "ped": (864, 144)}[kind]
    px = lambda u: (x0 + 1 + u * (w - 2)) / 1024
    py = lambda v: 1 - (row * 224 + 1 + v * 222) / 1024
    return [(px(u0), py(v0)), (px(u1), py(v0)), (px(u1), py(v1)), (px(u0), py(v1))]


def uv_wall(i, u0=0.0, u1=1.0, v0=0.0, v1=1.0):
    """cell i of the wall block; u,v in 0..1 (v up)."""
    c, r = i % 4, i // 4
    px = lambda u: (c * 256 + 2 + u * 252) / 1024
    py = lambda v: 1 - (512 + r * 256 + 2 + (1 - v) * 252) / 1024
    return [(px(u0), py(v0)), (px(u1), py(v0)), (px(u1), py(v1)), (px(u0), py(v1))]
