"""Textures for Frau Gerolds Garten (photos: data/raw/photos/fgg, research/fgg.md): gravel, weathered timber, sign atlas, shop glass. Barlow font only."""
import numpy as np
from PIL import Image, ImageDraw
from k5w3_kit import font, rgb, noisy, mixc

SIGNS = {"gate": (0, 0, 1024, 200), "bar": (0, 200, 340, 290), "kueche": (340, 200, 680, 290), "grill": (680, 200, 1020, 290), "markt": (0, 300, 1024, 420),
         "chalk": (0, 430, 512, 640), "cocktail": (512, 430, 1024, 640)}


def uvr(name, W=1024, H=640):
    x0, y0, x1, y1 = SIGNS[name]
    return [(x0 / W, 1 - y1 / H), (x1 / W, 1 - y1 / H), (x1 / W, 1 - y0 / H), (x0 / W, 1 - y0 / H)]


def gravel(size=128, seed=2):
    rng = np.random.default_rng(seed); a = np.full((size, size, 3), (196, 188, 170), float)
    a += rng.normal(0, 22, (size, size, 1))
    for _ in range(520):
        x, y = rng.integers(0, size, 2); r = int(rng.integers(1, 3)); a[max(0, y - r):y + r, max(0, x - r):x + r] *= rng.uniform(0.6, 1.2)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def wood(size=128, seed=5, col="#8a6a48"):
    """Weathered planks (horizontal boards 8 per tile, dark gaps)."""
    rng = np.random.default_rng(seed); C = rgb(col); im = Image.new("RGB", (size, size), C); d = ImageDraw.Draw(im); bh = size / 8
    for r in range(8):
        f = rng.uniform(0.82, 1.12); c = tuple(int(np.clip(v * f, 0, 255)) for v in C); d.rectangle([0, r * bh + 1, size, (r + 1) * bh - 1], fill=c)
        for _ in range(5):
            x = int(rng.integers(0, size)); d.line([x, r * bh + 2, x + int(rng.integers(8, 40)), r * bh + 2], fill=mixc(c, (0, 0, 0), 0.25))
    return noisy(im, 4, seed)


def signs():
    W, H = 1024, 640
    im = Image.new("RGBA", (W, H), (30, 30, 30, 255)); em = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im); de = ImageDraw.Draw(em)
    x0, y0, x1, y1 = SIGNS["gate"]; d.rectangle([x0, y0, x1, y1], fill=(46, 74, 52, 255)); d.rectangle([x0 + 8, y0 + 8, x1 - 8, y1 - 8], outline=(232, 226, 200, 255), width=5)
    f = font("Barlow-Bold", 118); d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 2), "FRAU GEROLDS GARTEN", font=f, fill=(244, 238, 214, 255), anchor="mm")
    de.text(((x0 + x1) / 2, (y0 + y1) / 2 + 2), "FRAU GEROLDS GARTEN", font=f, fill=(70, 66, 50), anchor="mm")
    for k, (txt, bg) in {"bar": ("BAR  >", (186, 60, 44)), "kueche": ("KÜCHE  >", (216, 160, 40)), "grill": ("GRILL  >", (52, 112, 130))}.items():
        x0, y0, x1, y1 = SIGNS[k]; d.rectangle([x0 + 4, y0 + 6, x1 - 4, y1 - 6], fill=bg + (255,)); d.text(((x0 + x1) / 2, (y0 + y1) / 2), txt, font=font("Barlow-Bold", 58), fill=(250, 246, 236, 255), anchor="mm")
    x0, y0, x1, y1 = SIGNS["markt"]; d.rectangle([x0, y0, x1, y1], fill=(34, 36, 38, 255)); d.text(((x0 + x1) / 2, (y0 + y1) / 2), "GEROLDS MARKT", font=font("Barlow-Bold", 84), fill=(236, 232, 220, 255), anchor="mm")
    de.text(((x0 + x1) / 2, (y0 + y1) / 2), "GEROLDS MARKT", font=font("Barlow-Bold", 84), fill=(90, 86, 76), anchor="mm")
    for k, (l1, l2) in {"chalk": ("Heute", "Flammkuchen"), "cocktail": ("Spritz", "Gerold")}.items():
        x0, y0, x1, y1 = SIGNS[k]; d.rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], fill=(30, 36, 34, 255), outline=(150, 112, 70, 255), width=10)
        d.text(((x0 + x1) / 2, y0 + 70), l1, font=font("Barlow-Bold", 62), fill=(240, 240, 230, 255), anchor="mm"); d.text(((x0 + x1) / 2, y0 + 140), l2, font=font("Barlow-Bold", 56), fill=(236, 200, 120, 255), anchor="mm")
    return im, em


def shopglass(size=256):
    """Shop front bay, 2.4 m wide x 3 m tall: charcoal frame, dark glass with warm lit interior, hanging plants at the top."""
    im = Image.new("RGBA", (size, size), (44, 46, 48, 255)); em = Image.new("RGB", (size, size), (0, 0, 0)); d = ImageDraw.Draw(im); de = ImageDraw.Draw(em)
    d.rectangle([14, 20, size - 14, size - 8], fill=(84, 100, 108, 255)); de.rectangle([14, 20, size - 14, size - 8], fill=(140, 112, 70))
    d.line([size // 2, 20, size // 2, size - 8], fill=(44, 46, 48, 255), width=6); d.line([14, 82, size - 14, 82], fill=(44, 46, 48, 255), width=5)
    rng = np.random.default_rng(3)
    for _ in range(26):
        x = int(rng.integers(18, size - 18)); y = int(rng.integers(24, 78)); d.ellipse([x - 7, y - 5, x + 7, y + 9], fill=(60, 140, 66, 255))
    return im, em


CCOLS = ["#2a6f78", "#8a3a24", "#7a2a24", "#a87a28", "#2f5a80", "#5c6062", "#3f6a48", "#9a4a1e"]


def containers():
    """4x2 container long sides (cells 256x112) + 64 px strip (unused): strong corrugation, rust, plus hatch+awning / doors / glass / graffiti stripes."""
    CW_, CH_ = 256, 112; H = 2 * CH_ + 64
    im = Image.new("RGB", (1024, H), (20, 20, 20)); em = Image.new("RGB", (1024, H), (0, 0, 0)); d = ImageDraw.Draw(im); de = ImageDraw.Draw(em); rng = np.random.default_rng(11)
    for k, col in enumerate(CCOLS):
        x0, y0 = (k % 4) * CW_, (k // 4) * CH_; C = rgb(col)
        d.rectangle([x0, y0, x0 + CW_, y0 + CH_], fill=C)
        for xx in range(x0 + 4, x0 + CW_ - 4, 6):
            d.line([xx, y0 + 8, xx, y0 + CH_ - 8], fill=mixc(C, (0, 0, 0), 0.38), width=2); d.line([xx + 3, y0 + 8, xx + 3, y0 + CH_ - 8], fill=mixc(C, (255, 255, 255), 0.16))
        for _ in range(14):                                                            # rust streaks / patches
            xx = int(rng.integers(x0 + 8, x0 + CW_ - 8)); yy = int(rng.integers(y0 + 8, y0 + 60)); d.rectangle([xx, yy, xx + int(rng.integers(3, 14)), yy + int(rng.integers(14, 50))], fill=mixc(C, (130, 66, 30), 0.5))
        d.rectangle([x0, y0, x0 + CW_, y0 + 9], fill=mixc(C, (0, 0, 0), 0.5)); d.rectangle([x0, y0 + CH_ - 10, x0 + CW_, y0 + CH_], fill=mixc(C, (0, 0, 0), 0.5))
        d.rectangle([x0, y0, x0 + 8, y0 + CH_], fill=mixc(C, (0, 0, 0), 0.45)); d.rectangle([x0 + CW_ - 9, y0, x0 + CW_, y0 + CH_], fill=mixc(C, (0, 0, 0), 0.45))
        f = k % 4
        if f == 0:      # serving hatch with striped awning + counter
            d.rectangle([x0 + 60, y0 + 26, x0 + 190, y0 + 70], fill=(30, 34, 36)); de.rectangle([x0 + 64, y0 + 30, x0 + 186, y0 + 66], fill=(150, 112, 60))
            for i in range(10): d.polygon([(x0 + 52 + i * 15, y0 + 14), (x0 + 67 + i * 15, y0 + 14), (x0 + 70 + i * 15, y0 + 30), (x0 + 49 + i * 15, y0 + 30)], fill=(214, 60, 48) if i % 2 else (238, 232, 218))
            d.rectangle([x0 + 56, y0 + 72, x0 + 194, y0 + 80], fill=(120, 90, 60))
        elif f == 1:    # double door with locking bars
            d.rectangle([x0 + 70, y0 + 14, x0 + 186, y0 + CH_ - 12], fill=mixc(C, (0, 0, 0), 0.35))
            for xx in (x0 + 90, x0 + 108, x0 + 148, x0 + 166): d.line([xx, y0 + 16, xx, y0 + CH_ - 14], fill=(160, 160, 156), width=3)
            d.line([x0 + 128, y0 + 14, x0 + 128, y0 + CH_ - 12], fill=(20, 20, 20), width=3)
        elif f == 2:    # two windows with frames + stripe
            for ox_ in (40, 150):
                d.rectangle([x0 + ox_, y0 + 24, x0 + ox_ + 66, y0 + 70], fill=(224, 220, 208)); d.rectangle([x0 + ox_ + 5, y0 + 29, x0 + ox_ + 61, y0 + 65], fill=(48, 62, 70)); de.rectangle([x0 + ox_ + 5, y0 + 29, x0 + ox_ + 61, y0 + 65], fill=(140, 110, 60))
            d.rectangle([x0 + 10, y0 + 84, x0 + CW_ - 10, y0 + 94], fill=(236, 200, 60))
        else:           # large glass sliding front
            d.rectangle([x0 + 40, y0 + 20, x0 + 216, y0 + CH_ - 14], fill=(210, 210, 204)); d.rectangle([x0 + 46, y0 + 26, x0 + 210, y0 + CH_ - 20], fill=(54, 70, 78)); de.rectangle([x0 + 46, y0 + 26, x0 + 210, y0 + CH_ - 20], fill=(150, 118, 70))
            d.line([x0 + 128, y0 + 26, x0 + 128, y0 + CH_ - 20], fill=(210, 210, 204), width=4)
    return noisy(im, 3, 4).convert("RGBA"), em
