"""Side-by-side: SWISSIMAGE mosaic crop vs game top-down. python rail_cmp.py tag x y [size=300] -> preview/_rail/cmp_tag.jpg"""
import sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
tag, x, y = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
size = float(sys.argv[4]) if len(sys.argv) > 4 else 300
game = Image.open(ROOT / "preview/_rail" / f"{tag}.png").convert("RGB")
px = game.width
sc = 2.0  # ortho px per metre (1000 px / 500 m)
out = Image.new("RGB", (px, px))
n = int(size * sc)
mos = Image.new("RGB", (n, n))
for ix in range(int((x - size / 2) // 500), int((x + size / 2) // 500) + 1):
    for iy in range(int((y - size / 2) // 500), int((y + size / 2) // 500) + 1):
        f = ROOT / "data/raw/ortho_wms" / f"r_{ix}_{iy}.jpg"
        if not f.exists():
            continue
        t = Image.open(f)
        ox = int((ix * 500 - (x - size / 2)) * sc)
        oy = int(((y + size / 2) - (iy + 1) * 500) * sc)
        mos.paste(t, (ox, oy))
mos = mos.resize((px, px))
c = Image.new("RGB", (px * 2, px)); c.paste(mos, (0, 0)); c.paste(game, (px, 0))
c = c.resize((1600, 800)); c.save(ROOT / "preview/_rail" / f"cmp_{tag}.jpg", quality=82)
