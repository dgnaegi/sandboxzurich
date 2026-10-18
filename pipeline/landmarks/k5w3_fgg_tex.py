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
    rng = np.random.default_rng(seed); a = np.full((size, size, 3), (150, 140, 122), float)
    a += rng.normal(0, 14, (size, size, 1))
    for _ in range(260):
        x, y = rng.integers(0, size, 2); r = int(rng.integers(1, 3)); a[max(0, y - r):y + r, max(0, x - r):x + r] *= rng.uniform(0.7, 1.15)
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
