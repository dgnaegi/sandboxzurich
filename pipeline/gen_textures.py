"""Build the texture array for the game: 512x512 layers packed in an 8-column grid.

Outputs web/public/tex/atlas.webp (RGB) + atlas_mask.png (L, 255 = tint with vertex colour) + layers.json.
Facades/shops/roofs come from gen_facades.py (v2, + atlas_n.webp with normal xy + roughness);
ground from the reel (kies, grass, stone); asphalt, sidewalk and tram bed are generated here.
"""
import json
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from config import REEL, ROOT

TEX = REEL.parent / "assets" / "tex"
OUT = ROOT / "web" / "public" / "tex"
L = 512
COLS = 8
rng = np.random.default_rng(7)
random.seed(7)


def noise(h, w, scale, amp):
    small = rng.normal(0, 1, (max(2, h // scale), max(2, w // scale)))
    small = (small - small.min()) / (np.ptp(small) + 1e-6)
    n = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    return (n - 0.5) * amp


def from_reel(name):
    im = Image.open(TEX / f"{name}.png")
    rgb = im.convert("RGB").resize((L, L), Image.LANCZOS)
    mask = im.getchannel("A").resize((L, L), Image.BILINEAR) if im.mode == "RGBA" else Image.new("L", (L, L), 0)
    return rgb, mask


def plaster(h, w, base=225):
    g = np.clip(base + noise(h, w, 32, 22) + noise(h, w, 4, 10), 0, 255)
    return np.stack([g, g * 0.985, g * 0.955], -1).astype(np.uint8)


SHOP_COLORS = [(200, 40, 40), (30, 30, 30), (40, 110, 70), (220, 170, 30), (110, 20, 40), (20, 70, 140),
               (230, 230, 225), (90, 60, 40)]


def shopfront(i):
    """12 m x 4 m ground floor stretched to 512x512: sign band (blank), shop window, door."""
    W, H = 1024, 341
    im = Image.fromarray(plaster(H, W, 215))
    d = ImageDraw.Draw(im)
    bg = SHOP_COLORS[i]
    x_door = [700, 60, 860, 420, 120, 760, 300, 860][i]
    d.rectangle([20, 40, 1004, 104], fill=bg)  # sign band, name is drawn at runtime
    for x0, x1 in ((40, x_door - 30), (x_door + 150, 990)):
        if x1 - x0 < 80:
            continue
        d.rectangle([x0, 124, x1, 322], fill=(40, 46, 52), outline=(35, 35, 35), width=8)
        for k in range(70):
            c = 70 + k
            d.line([x0 + 6, 130 + k, x1 - 6, 130 + k], fill=(c, c + 14, c + 24))
        if i % 2:
            for xx in range(x0 + 30, x1 - 30, 70):  # shelves / goods silhouettes
                d.rectangle([xx, 250, xx + 40, 316], fill=random.choice([(180, 60, 50), (220, 200, 90), (70, 120, 160), (230, 230, 230)]))
    d.rectangle([x_door, 124, x_door + 120, 336], fill=(60, 44, 36))
    d.rectangle([x_door + 12, 136, x_door + 108, 250], fill=(70, 90, 105))
    if i in (0, 4, 6, 2):  # striped awning
        for k in range(20, 1000, 40):
            d.polygon([(k, 104), (k + 40, 104), (k + 44, 126), (k + 4, 126)], fill=bg if (k // 40) % 2 else (240, 240, 235))
    rgb = im.filter(ImageFilter.GaussianBlur(0.6)).resize((L, L), Image.LANCZOS)
    return rgb, Image.new("L", (L, L), 0)


def roof_tiles():
    a = np.zeros((L, L, 3), np.float32)
    y, x = np.mgrid[0:L, 0:L]
    row = (y // 32)
    xs = (x + (row % 2) * 24) % 48
    shade = 0.75 + 0.25 * np.sin((y % 32) / 32 * np.pi) - 0.25 * (xs < 3)
    base = np.array([150, 78, 58], np.float32)
    var = noise(L, L, 48, 0.25)[..., None] + rng.normal(0, 0.04, (L // 32 + 1, L // 48 + 2))[row, (x + (row % 2) * 24) // 48][..., None]
    a = base * (shade[..., None] + var)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), Image.new("L", (L, L), 0)


def asphalt():
    g = 118 + noise(L, L, 64, 18) + noise(L, L, 8, 10) + rng.normal(0, 9, (L, L))
    rgb = np.stack([g, g * 1.0, g * 1.04], -1)
    for _ in range(14):  # patches and cracks
        x, y, r = rng.integers(0, L, 3)
        rr = 20 + r % 60
        yy, xx = np.ogrid[:L, :L]
        rgb[((xx - x) ** 2 + (yy - y) ** 2) < rr * rr] *= 0.96
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    return im, Image.new("L", (L, L), 255)


def trottoir():
    """Zürich sidewalks are mostly light, fine-grained asphalt."""
    g = 150 + noise(L, L, 64, 14) + noise(L, L, 6, 8) + rng.normal(0, 7, (L, L))
    rgb = np.stack([g, g * 0.99, g * 0.97], -1)
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    return im, Image.new("L", (L, L), 255)


def gravel():
    """Fine, even roof gravel with faint bitumen seams (flat roofs)."""
    g = 150 + noise(L, L, 64, 8) + rng.normal(0, 13, (L, L))
    rgb = np.stack([g, g * 0.985, g * 0.95], -1)
    rgb[::128, :] *= 0.8
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.5))
    return im, Image.new("L", (L, L), 255)  # tintable per building


def tram_bed():
    g = 120 + noise(L, L, 6, 50) + rng.normal(0, 14, (L, L))
    rgb = np.stack([g, g * 0.96, g * 0.9], -1)
    for y in range(0, L, 64):  # sleepers
        rgb[y:y + 22] = rgb[y:y + 22] * 0.6 + np.array([70, 62, 55]) * 0.4
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)), Image.new("L", (L, L), 0)


def plain(v=255):
    return Image.new("RGB", (L, L), (v, v, v)), Image.new("L", (L, L), 255)


def ground(name, tint=True, mean=None):
    rgb, _ = from_reel(name)
    if mean:  # normalise brightness so ground layers read well after tone mapping
        a = np.asarray(rgb, np.float32)
        rgb = Image.fromarray(np.clip(a * (mean / a.mean()), 0, 255).astype(np.uint8))
    return rgb, Image.new("L", (L, L), 255 if tint else 0)


FAC = ROOT / "data" / "build" / "facades"  # sources from gen_facades.py (not shipped)
FACADES = ["gruender_a", "gruender_b", "gruender_c", "jugend_a", "jugend_b", "genoss_a", "genoss_b", "genoss_c",
           "block50_a", "block50_b", "block60_a", "waschbeton_a", "waschbeton_b", "neubau_a", "neubau_b", "neubau_c",
           "gewerbe_a", "gewerbe_b", "gewerbe_c", "buero_a", "buero_b", "buero_c"]
SHOPS = ["shop_cafe", "shop_kiosk", "shop_bar", "shop_kebab", "shop_coiffeur", "shop_velo", "shop_leer", "shop_baeckerei"]


def v2(name, tint_mask=True):
    """Facade v2 layer (pipeline/gen_facades.py): albedo, mask (255 = plaster tint), normal (RG) + roughness (B)."""
    r = lambda f, mode, flt: Image.open(FAC / f"{name}_{f}.png").convert(mode).resize((L, L), flt)
    rgb = r("albedo", "RGB", Image.LANCZOS)
    mask = r("mask", "L", Image.BILINEAR) if tint_mask else Image.new("L", (L, L), 0)
    nrm = r("normal", "RGB", Image.LANCZOS)
    rough = r("rough", "L", Image.BILINEAR)
    nb = Image.merge("RGB", (*nrm.split()[:2], rough))
    return rgb, mask, nb


LAYERS = {}   # order matters: facades | shops | brandmauer (normal maps up to here) | roofs + ground (flat)
for n in FACADES:
    LAYERS[n] = lambda n=n: v2(n)
for n in SHOPS:
    LAYERS[n] = lambda n=n: v2(n, False)
LAYERS["brandmauer"] = lambda: v2("brandmauer")
LAYERS.update({"roof_tiles": lambda: (v2("dach_ziegel", False)[0], Image.new("L", (L, L), 255)), "dach_kies": gravel,
               "roof_flat": lambda: ground("kies", False), "asphalt": asphalt,
               "sidewalk": trottoir, "grass": lambda: ground("grass", False),
               "cobble": lambda: ground("stone", mean=160), "tram_bed": tram_bed, "white": plain})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = len(LAYERS)
    rows = (n + COLS - 1) // COLS
    rgb = Image.new("RGB", (COLS * L, rows * L))
    mask = Image.new("L", (COLS * L, rows * L))
    n_norm = len(FACADES) + len(SHOPS) + 1  # layers that carry a normal map
    nrows = (n_norm + COLS - 1) // COLS
    nat = Image.new("RGB", (COLS * L, nrows * L), (128, 128, 255))
    for k, (name, fn) in enumerate(LAYERS.items()):
        c, m, *nb = fn()
        if nb:
            nat.paste(nb[0], ((k % COLS) * L, (k // COLS) * L))
        rgb.paste(c, ((k % COLS) * L, (k // COLS) * L))
        mask.paste(m, ((k % COLS) * L, (k // COLS) * L))
    rgb.save(OUT / "atlas.webp", quality=82, method=6)
    mask.save(OUT / "atlas_mask.png", optimize=True)
    nat.save(OUT / "atlas_n.webp", quality=90, method=6)  # R,G = normal xy, B = roughness
    json.dump({"size": L, "cols": COLS, "count": n, "layers": list(LAYERS), "facades": len(FACADES),
               "shops_end": len(FACADES) + len(SHOPS), "normals": n_norm}, open(OUT / "layers.json", "w"))
    print(n, "layers", {f: (OUT / f).stat().st_size // 1024 for f in ("atlas.webp", "atlas_mask.png", "atlas_n.webp")}, "KB")


if __name__ == "__main__":
    main()
