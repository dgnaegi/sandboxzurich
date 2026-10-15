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
from gen_shopfronts import SHOP_LAYERS  # v2: procedural shopfronts (albedo, night-emissive mask, normal+roughness)
# Index stability: the first 8 shop slots keep their old position (so tiles built earlier stay valid) and carry the
# same kind of shop as before; all further shop layers are appended after the ground layers (no normal map there).
SHOPS = ["shop_cafe_a", "shop_kiosk", "shop_bar_a", "shop_kebab_a", "shop_coiffeur", "shop_velo", "shop_leer", "shop_baeckerei"]
SHOPS_EXTRA = [n for n in SHOP_LAYERS if n not in SHOPS]


def v2(name, tint_mask=True):
    """Facade v2 layer (pipeline/gen_facades.py): albedo, mask (255 = plaster tint), normal (RG) + roughness (B)."""
    r = lambda f, mode, flt: Image.open(FAC / f"{name}_{f}.png").convert(mode).resize((L, L), flt)
    rgb = r("albedo", "RGB", Image.LANCZOS)
    mask = r("mask", "L", Image.BILINEAR) if tint_mask else Image.new("L", (L, L), 0)
    nrm = r("normal", "RGB", Image.LANCZOS)
    rough = r("rough", "L", Image.BILINEAR)
    nb = Image.merge("RGB", (*nrm.split()[:2], rough))
    return rgb, mask, nb


def _calm_grass():
    """Real Zürich lawns: less saturated and a bit darker than the raw grass texture."""
    rgb, m = ground("grass", False)
    hsv = np.asarray(rgb.convert("HSV"), np.float32)
    hsv[..., 1] *= 0.62
    hsv[..., 2] *= 0.86
    return Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB"), m


LAYERS = {}   # order matters: facades | shops | brandmauer (normal maps up to here) | roofs + ground (flat)
for n in FACADES:
    LAYERS[n] = lambda n=n: v2(n)
for n in SHOPS:
    LAYERS[n] = SHOP_LAYERS[n]
LAYERS["brandmauer"] = lambda: v2("brandmauer")
LAYERS.update({"roof_tiles": lambda: (v2("dach_ziegel", False)[0], Image.new("L", (L, L), 255)), "dach_kies": gravel,
               "roof_flat": lambda: ground("kies", False), "asphalt": asphalt,
               "sidewalk": trottoir, "grass": lambda: _calm_grass(),
               "cobble": lambda: ground("stone", mean=160), "tram_bed": tram_bed, "white": plain})
for n in SHOPS_EXTRA:
    LAYERS[n] = SHOP_LAYERS[n]


def _grey_tiles():
    """Neutral clay tiles (mean ~175) for roofs tinted with the colour measured on the orthophoto."""
    from PIL import ImageOps
    g = ImageOps.grayscale(v2("dach_ziegel", False)[0])
    a = np.asarray(g, np.float32)
    a = np.clip((a - a.mean()) * 1.3 + 175, 0, 255).astype(np.uint8)
    return Image.fromarray(a).convert("RGB"), Image.new("L", (L, L), 255)


LAYERS["roof_tiles_grey"] = _grey_tiles  # appended: existing layer indices stay valid

# v3 facades (pipeline/gen_facades3.py): neutral plaster / brick / sandstone, tinted to the exact observed colour.
# Appended last (indices of all earlier layers stay valid); they carry normal maps in an extra range of the normal atlas.
from gen_facades3 import FACADES3  # noqa: E402
for _n in FACADES3:
    LAYERS[_n] = lambda n=_n: v2(n)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = len(LAYERS)
    rows = (n + COLS - 1) // COLS
    rgb = Image.new("RGB", (COLS * L, rows * L))
    mask = Image.new("L", (COLS * L, rows * L))
    n_norm = len(FACADES) + len(SHOPS) + 1  # layers that carry a normal map
    f3 = list(LAYERS).index(FACADES3[0])
    nrows = (n_norm + len(FACADES3) + COLS - 1) // COLS
    nat = Image.new("RGB", (COLS * L, nrows * L), (128, 128, 255))
    for k, (name, fn) in enumerate(LAYERS.items()):
        c, m, *nb = fn()
        if nb:
            j = k if k < n_norm else n_norm + k - f3 if k >= f3 else None  # v3 facades: normal slots after the first n_norm
            if j is not None:
                nat.paste(nb[0], ((j % COLS) * L, (j // COLS) * L))
        rgb.paste(c, ((k % COLS) * L, (k // COLS) * L))
        mask.paste(m, ((k % COLS) * L, (k // COLS) * L))
    rgb.save(OUT / "atlas.webp", quality=82, method=6)
    mask.save(OUT / "atlas_mask.png", optimize=True)
    nat.save(OUT / "atlas_n.webp", quality=90, method=6)  # R,G = normal xy, B = roughness
    json.dump({"size": L, "cols": COLS, "count": n, "layers": list(LAYERS), "facades": len(FACADES),
               "shops_end": len(FACADES) + len(SHOPS), "normals": n_norm, "normals3": len(FACADES3),
               "shops2": [list(LAYERS).index(SHOPS_EXTRA[0]), list(LAYERS).index(SHOPS_EXTRA[0]) + len(SHOPS_EXTRA)],
               "facades3": [f3, f3 + len(FACADES3)]}, open(OUT / "layers.json", "w"))
    print(n, "layers", {f: (OUT / f).stat().st_size // 1024 for f in ("atlas.webp", "atlas_mask.png", "atlas_n.webp")}, "KB")


if __name__ == "__main__":
    main()
