"""Textures for the Schlachthof Zuerich landmark (painted procedurally, free font Barlow only).
Photo basis: Commons CC BY-SA 3.0/4.0 (research/schlachthof.md): yellow brick, red brick arch bands, grey stone, zinc barrel vault."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

FONTS = Path(__file__).resolve().parent.parent.parent / "web" / "public" / "fonts"
YEL = (217, 198, 143); RED = (138, 58, 42); GREY = (170, 166, 156); DGREY = (120, 118, 112)


def font(sz, name="Barlow-Bold"): return ImageFont.truetype(str(FONTS / (name + ".ttf")), sz)


CREAM = (234, 219, 172)


def brick_wall(color=CREAM, size=512, rows=48, cols=16, seed=3, red=True):
    """Pale yellowish clinker with visible light-grey joints, 4 m x 4 m per repeat (48 courses of ~8 cm, 25 cm bricks). red=True adds
    the brick-red bands: a horizontal band and a vertical pilaster strip per repeat (halls, photo 3 of research/schlachthof.md)."""
    rng = np.random.default_rng(seed); joint = (206, 198, 176)
    im = Image.new("RGB", (size, size), joint); d = ImageDraw.Draw(im)
    bh = size / rows; bw = size / cols
    redcol = (176, 78, 52)
    for r in range(rows):
        off = (r % 2) * bw / 2
        for k in range(-1, cols + 1):
            f = 1 + rng.normal(0, 0.035); g = rng.normal(0, 3)
            c = tuple(int(np.clip(v * f + g * (1 if i == 0 else 0.6), 0, 255)) for i, v in enumerate(color))
            d.rectangle([k * bw + off + 1.5, r * bh + 1.5, (k + 1) * bw + off - 1.5, (r + 1) * bh - 1.5], fill=c)
    if red:
        for r in (rows - 3, rows - 2, rows - 1):      # horizontal red band (3 courses)
            for k in range(-1, cols + 1):
                off = (r % 2) * bw / 2; f = 1 + rng.normal(0, 0.05)
                d.rectangle([k * bw + off + 1.5, r * bh + 1.5, (k + 1) * bw + off - 1.5, (r + 1) * bh - 1.5], fill=tuple(int(v * f) for v in redcol))
        for r in range(rows):                          # vertical pilaster strip: 2 bricks wide at u = 0
            off = (r % 2) * bw / 2
            for k in (-1, 0, cols - 1, cols):
                x0 = k * bw + off
                if abs((x0 + bw / 2) % size) < bw * 0.8 or abs((x0 + bw / 2) % size - size) < bw * 0.8:
                    f = 1 + rng.normal(0, 0.05); d.rectangle([x0 + 1.5, r * bh + 1.5, x0 + bw - 1.5, (r + 1) * bh - 1.5], fill=tuple(int(v * f) for v in redcol))
    a = np.asarray(im).astype(float)
    for _ in range(18):                                # soot / water staining streaks
        x = int(rng.integers(0, size)); w = int(rng.integers(8, 34)); a[:, x:x + w] *= 1 + rng.normal(0, 0.02)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def zinc(size=128):
    """Standing-seam zinc: one seam per tile (0.6 m in u), light grey."""
    im = Image.new("RGB", (size, size), (166, 172, 174)); d = ImageDraw.Draw(im)
    for x in range(size): d.line([x, 0, x, size], fill=tuple(int(166 + 6 * math.sin(x / size * math.pi) - 0) if i < 2 else 176 for i in range(3)))
    d.rectangle([0, 0, 3, size], fill=(118, 124, 128)); d.rectangle([4, 0, 5, size], fill=(196, 200, 202))
    for y in range(0, size, 32): d.line([0, y, size, y], fill=(150, 156, 158))
    return im.convert("RGBA")


def tiles(color=(158, 74, 52), size=128, rows=16, cols=10, seed=4):
    rng = np.random.default_rng(seed); im = Image.new("RGB", (size, size), tuple(int(v * .6) for v in color)); d = ImageDraw.Draw(im)
    h, w = size // rows, size // cols
    for r in range(rows):
        for c in range(-1, cols):
            f = 1 + rng.normal(0, 0.1); col = tuple(int(np.clip(v * f, 0, 255)) for v in color); x = c * w + (w // 2 if r % 2 else 0)
            d.rectangle([x + 1, r * h, x + w - 1, r * h + h - 1], fill=col)
    return im.convert("RGBA")


def plaster(color, size=128, seed=3):
    rng = np.random.default_rng(seed); a = np.full((size, size, 3), color, float) + rng.normal(0, 3, (size, size, 1))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


# ---- decal atlas (alpha cut-out) ---------------------------------------------------------------
ATLAS = 1024
RECTS = {"win_arch": (0, 0, 256, 512), "gate": (256, 0, 512, 384), "win_mod": (512, 0, 768, 256), "win_shut": (768, 0, 1024, 512),
         "sign": (0, 512, 1024, 640), "win_arch_ws": (0, 640, 256, 1024), "dock": (256, 640, 512, 896), "door_arch": (512, 640, 768, 1024)}


def uvr(name, flip=False):
    x0, y0, x1, y1 = RECTS[name]; v0, v1 = 1 - y1 / ATLAS, 1 - y0 / ATLAS
    u0, u1 = x0 / ATLAS, x1 / ATLAS
    if flip: u0, u1 = u1, u0
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def _arch_poly(x0, y0, x1, y1, n=14):
    """Pixel polygon: rect from y1 (bottom) up to the spring, semicircular head. y grows downward."""
    r = (x1 - x0) / 2; cx = (x0 + x1) / 2; ys = y0 + r
    pts = [(x0, y1), (x0, ys)] + [(cx - r * math.cos(math.pi * i / n), ys - r * math.sin(math.pi * i / n)) for i in range(0, n + 1)] + [(x1, ys), (x1, y1)]
    return pts


def decals(night=True):
    im = Image.new("RGBA", (ATLAS, ATLAS), (0, 0, 0, 0)); em = Image.new("RGB", (ATLAS, ATLAS), (0, 0, 0))
    d, de = ImageDraw.Draw(im), ImageDraw.Draw(em)
    GL = (86, 108, 116, 255); FR = (74, 92, 84, 255)
    # tall arched window, red brick surround, green-grey mullions
    x0, y0, x1, y1 = RECTS["win_arch"]
    d.polygon(_arch_poly(x0 + 6, y0 + 6, x1 - 6, y1 - 10), fill=RED + (255,))
    d.polygon(_arch_poly(x0 + 30, y0 + 30, x1 - 30, y1 - 30), fill=GL)
    de.polygon(_arch_poly(x0 + 30, y0 + 30, x1 - 30, y1 - 30), fill=(70, 62, 40))
    d.rectangle([x0, y1 - 18, x1, y1 - 8], fill=GREY + (255,))                      # stone sill
    cx = (x0 + x1) / 2; d.line([cx, y0 + 30, cx, y1 - 30], fill=FR, width=4)
    for yy in (y0 + 150, y0 + 260, y0 + 370): d.line([x0 + 30, yy, x1 - 30, yy], fill=FR, width=4)
    # segmental-arch gate / dock opening, red archivolt, dark interior
    x0, y0, x1, y1 = RECTS["gate"]
    d.polygon(_arch_poly(x0 + 6, y0 + 6, x1 - 6, y1), fill=RED + (255,))
    d.polygon(_arch_poly(x0 + 30, y0 + 30, x1 - 30, y1), fill=(48, 50, 52, 255))
    for xx in range(x0 + 40, x1 - 30, 14): d.line([xx, y0 + 140, xx, y1], fill=(66, 70, 72, 255), width=3)
    # modern window
    x0, y0, x1, y1 = RECTS["win_mod"]
    d.rectangle([x0 + 8, y0 + 8, x1 - 8, y1 - 8], fill=(150, 150, 146, 255)); d.rectangle([x0 + 20, y0 + 20, x1 - 20, y1 - 20], fill=GL)
    de.rectangle([x0 + 20, y0 + 20, x1 - 20, y1 - 20], fill=(60, 54, 36)); d.line([(x0 + x1) / 2, y0 + 20, (x0 + x1) / 2, y1 - 20], fill=(150, 150, 146, 255), width=5)
    # shuttered window (Restaurant Schlachthof, green shutters, white frame)
    x0, y0, x1, y1 = RECTS["win_shut"]
    d.rectangle([x0 + 2, y0 + 20, x1 - 2, y1 - 18], fill=(236, 232, 222, 255))
    d.rectangle([x0 + 70, y0 + 40, x1 - 70, y1 - 40], fill=(70, 86, 96, 255)); de.rectangle([x0 + 70, y0 + 40, x1 - 70, y1 - 40], fill=(66, 58, 36))
    d.line([(x0 + x1) / 2, y0 + 40, (x0 + x1) / 2, y1 - 40], fill=(236, 232, 222, 255), width=6)
    d.rectangle([x0 + 2, y0 + 20, x0 + 62, y1 - 18], fill=(52, 112, 82, 255)); d.rectangle([x1 - 62, y0 + 20, x1 - 2, y1 - 18], fill=(52, 112, 82, 255))
    for yy in range(y0 + 34, y1 - 24, 18):
        d.line([x0 + 4, yy, x0 + 60, yy], fill=(36, 84, 60, 255), width=2); d.line([x1 - 60, yy, x1 - 4, yy], fill=(36, 84, 60, 255), width=2)
    # sign board "RESTAURANT SCHLACHTHOF"
    x0, y0, x1, y1 = RECTS["sign"]
    d.rectangle([x0, y0, x1, y1 - 1], fill=(232, 226, 210, 255)); f = font(84)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), "RESTAURANT SCHLACHTHOF", font=f, fill=(40, 40, 38, 255), anchor="mm")
    de.rectangle([x0, y0, x1, y1 - 1], fill=(40, 36, 28))
    # round-arched ground-floor window (restaurant)
    x0, y0, x1, y1 = RECTS["win_arch_ws"]
    d.polygon(_arch_poly(x0 + 8, y0 + 8, x1 - 8, y1 - 8), fill=(236, 232, 222, 255)); d.polygon(_arch_poly(x0 + 34, y0 + 34, x1 - 34, y1 - 34), fill=(70, 86, 96, 255))
    de.polygon(_arch_poly(x0 + 34, y0 + 34, x1 - 34, y1 - 34), fill=(70, 62, 40))
    d.line([(x0 + x1) / 2, y0 + 34, (x0 + x1) / 2, y1 - 34], fill=(236, 232, 222, 255), width=5)
    # roller-shutter dock door in red-brick frame
    x0, y0, x1, y1 = RECTS["dock"]
    d.rectangle([x0 + 4, y0 + 4, x1 - 4, y1], fill=RED + (255,)); d.rectangle([x0 + 26, y0 + 26, x1 - 26, y1], fill=(142, 146, 148, 255))
    for yy in range(y0 + 30, y1, 12): d.line([x0 + 26, yy, x1 - 26, yy], fill=(112, 116, 118, 255), width=2)
    # arched entrance door (restaurant): dark wood, stone surround
    x0, y0, x1, y1 = RECTS["door_arch"]
    d.polygon(_arch_poly(x0 + 6, y0 + 6, x1 - 6, y1), fill=GREY + (255,)); d.polygon(_arch_poly(x0 + 34, y0 + 34, x1 - 34, y1), fill=(84, 60, 44, 255))
    de.polygon(_arch_poly(x0 + 44, y0 + 44, x1 - 44, y0 + 150), fill=(90, 74, 44))
    d.line([(x0 + x1) / 2, y0 + 150, (x0 + x1) / 2, y1], fill=(54, 38, 28, 255), width=5)
    return im, em


# ---- portal ---------------------------------------------------------------------------------------
PW, PZ0, PZ1 = 30.0, -15.0, 13.0     # u in [-15,15] m, z relative to the vault spring line (abs ~10.5 m) in [-15,13] m
R_OUT, R_RED, R_GL = 12.1, 10.4, 8.8  # facade arch: stone ring, red-brick ring, glazing radius (hall width 24.2 m)


def portal(zg, variant=0, size=512):
    """Gable end of the barrel-vault hall. zg: ground level relative to the spring line (negative). Returns (rgba, emissive)."""
    SX = size / PW; SY = size / (PZ1 - PZ0)
    X = lambda u: (u + PW / 2) * SX; Y = lambda z: (PZ1 - z) * SY
    rng = np.random.default_rng(5 + variant)
    base = np.full((size, size, 3), (230, 214, 166), float) + rng.normal(0, 4, (size, size, 1))
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    em = Image.new("RGB", (size, size), (0, 0, 0)); de = ImageDraw.Draw(em)
    for z in np.arange(PZ0, PZ1, 0.3): d.line([0, Y(z), size, Y(z)], fill=(110, 90, 50, 22), width=1)
    d.rectangle([0, Y(zg + 1.5), size, size], fill=DGREY + (255,))                  # plinth
    d.rectangle([0, Y(zg + 1.5), size, Y(zg + 1.5) + 2], fill=(90, 88, 84, 255))
    def arc_band(r0, r1, col):
        pts = [(X(r1 * math.cos(math.pi * i / 40)), Y(r1 * math.sin(math.pi * i / 40))) for i in range(41)]
        pts += [(X(r0 * math.cos(math.pi * (40 - i) / 40)), Y(r0 * math.sin(math.pi * (40 - i) / 40))) for i in range(41)]
        d.polygon(pts, fill=col)
    arc_band(R_RED, R_OUT, GREY + (255,)); arc_band(R_GL, R_RED, RED + (255,))
    for a in np.linspace(0.03, math.pi - 0.03, 60):
        d.line([X(R_GL * math.cos(a)), Y(R_GL * math.sin(a)), X(R_RED * math.cos(a)), Y(R_RED * math.sin(a))], fill=(120, 44, 30, 140), width=1)
    zb = -4.3
    gl = [(X(-R_GL), Y(zb)), (X(R_GL), Y(zb))] + [(X(R_GL * math.cos(math.pi * i / 40)), Y(R_GL * math.sin(math.pi * i / 40))) for i in range(41)]
    d.polygon(gl, fill=(112, 140, 150, 255)); de.polygon(gl, fill=(54, 46, 28))
    lay = Image.new("RGBA", (size, size), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    for i in range(0, 40):
        z = zb + i * (R_GL - zb) / 40
        dl.rectangle([X(-R_GL), Y(z + (R_GL - zb) / 40), X(R_GL), Y(z)], fill=(205, 225, 232, int(90 * i / 40)))
    mk = Image.new("L", (size, size), 0); ImageDraw.Draw(mk).polygon(gl, fill=255); im.paste(lay, (0, 0), Image.composite(lay.split()[3], Image.new("L", (size, size), 0), mk)); d = ImageDraw.Draw(im, "RGBA")
    d.polygon(gl, outline=(70, 90, 84, 255)); FR = (66, 92, 84, 255)
    for k in range(-6, 7):
        u = k * 1.46; d.line([X(u), Y(zb), X(u), Y(math.sqrt(max(0, R_GL ** 2 - u * u)))], fill=FR, width=2)
    for z in np.arange(zb, R_GL, 2.1):
        w = math.sqrt(max(0, R_GL ** 2 - max(z, 0) ** 2)); d.line([X(-w), Y(z), X(w), Y(z)], fill=FR, width=2)
    cz = 6.3; r = 1.9 * SX
    d.ellipse([X(0) - r - 5, Y(cz) - r - 5, X(0) + r + 5, Y(cz) + r + 5], fill=(40, 40, 40, 255)); d.ellipse([X(0) - r, Y(cz) - r, X(0) + r, Y(cz) + r], fill=(244, 240, 226, 255))
    de.ellipse([X(0) - r, Y(cz) - r, X(0) + r, Y(cz) + r], fill=(150, 140, 96))
    d.line([X(0), Y(cz), X(0) + r * 0.2, Y(cz) - r * 0.7], fill=(30, 30, 30, 255), width=3); d.line([X(0), Y(cz), X(0) - r * 0.6, Y(cz) + r * 0.3], fill=(30, 30, 30, 255), width=3)
    pl = (206, 202, 190, 255)
    d.rectangle([X(-3.4), Y(11.9), X(3.4), Y(10.9)], fill=pl); f = font(max(9, int(SX * 0.46)))
    d.text((X(0), Y(11.4)), "STÄDTISCHER SCHLACHTHOF 1909", font=f, fill=(48, 48, 44, 255), anchor="mm")
    d.rectangle([0, Y(zb), size, Y(zb - 0.55)], fill=GREY + (255,)); d.rectangle([0, Y(zb - 0.55), size, Y(zb - 1.0)], fill=RED + (255,))
    def gate(uc, w, h):
        z0 = zg + 1.5; zs = z0 + h - w / 2
        def ap(ww, zb_):
            r_ = ww / 2; return [(X(uc - r_), Y(zb_))] + [(X(uc - r_ * math.cos(math.pi * i / 24)), Y(zs + r_ * math.sin(math.pi * i / 24))) for i in range(25)] + [(X(uc + r_), Y(zb_))]
        d.polygon(ap(w + 1.9, z0 - 0.2), fill=RED + (255,)); d.polygon(ap(w + 0.6, z0 - 0.2), fill=GREY + (255,)); d.polygon(ap(w, z0), fill=(58, 56, 56, 255))
        de.polygon(ap(w - 0.5, z0 + 0.6), fill=(34, 30, 22))
    gate(0, 7.8, 9.6); gate(-9.7, 4.4, 7.4); gate(9.7, 4.4, 7.4)
    for s in (-1, 1):
        uc = s * 13.55
        d.rectangle([X(uc - 1.45), Y(6.4), X(uc + 1.45), Y(6.0)], fill=GREY + (255,))
        for z0_, z1_ in ((zg + 6.0, zg + 9.0), (zg + 13.0, zg + 16.0)):
            d.rectangle([X(uc - 0.5), Y(z1_), X(uc + 0.5), Y(z0_)], fill=(60, 78, 80, 255)); d.rectangle([X(uc - 0.8), Y(z1_) - 4, X(uc + 0.8), Y(z1_)], fill=RED + (255,))
        d.rectangle([X(uc - 1.45), Y(zb), X(uc + 1.45), Y(zb - 0.5)], fill=RED + (255,))
    if variant == 1:
        d.ellipse([X(0) - r - 8, Y(cz) - r - 8, X(0) + r + 8, Y(cz) + r + 8], fill=(92, 118, 128, 255)); de.ellipse([X(0) - r - 8, Y(cz) - r - 8, X(0) + r + 8, Y(cz) + r + 8], fill=(54, 46, 28))
        d.rectangle([X(-3.4), Y(11.9), X(3.4), Y(10.9)], fill=GREY + (255,))
    return im.convert("RGBA"), em
