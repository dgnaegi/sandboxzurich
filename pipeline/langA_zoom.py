"""Zoom comparison: ortho (SWISSIMAGE 60 m box) | game topdown of the same box. usage: langA_zoom.py suffix name x y [name x y ...] -> preview/_langA/z_<name>_<suffix>.jpg (requires topdown PNG preview/_langA/z_<name>_<suffix>.png)"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import langA_ortho as O
ROOT = O.ROOT
suf = sys.argv[1]; a = sys.argv[2:]
for i in range(0, len(a), 3):
    n, x, y = a[i], float(a[i + 1]), float(a[i + 2])
    f = O.D / f"z_{n}.jpg"
    if not f.exists():
        O.get(f"z_{n}", x, y, 30)
    g = ROOT / f"preview/_langA/z_{n}_{suf}.png"
    A = Image.open(f).convert("RGB").resize((800, 800)); B = Image.open(g).convert("RGB").resize((800, 800))
    s = Image.new("RGB", (1600, 800)); s.paste(A, (0, 0)); s.paste(B, (800, 0))
    ImageDraw.Draw(s).text((6, 4), f"{n} ortho | {suf}", fill="yellow"); s.save(ROOT / f"preview/_langA/z_{n}_{suf}.jpg", quality=85)
