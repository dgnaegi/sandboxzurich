"""Contact sheet ortho | game for the Langstrasse spots. usage: langA_cmp.py out.jpg suffix[,suffix...] names..."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent
out, sufs, names = sys.argv[1], sys.argv[2].split(","), sys.argv[3:]
S = 560; cols = 1 + len(sufs)
sheet = Image.new("RGB", (S * cols, S * len(names)), "black"); d = ImageDraw.Draw(sheet)
for r, n in enumerate(names):
    ims = [("ortho", ROOT / f"data/raw/ortho_langstrasse/{n}.jpg")] + [(s, ROOT / f"preview/_langA/{n}_{s}.png") for s in sufs]
    for c, (lab, f) in enumerate(ims):
        im = Image.open(f).convert("RGB").resize((S, S)); sheet.paste(im, (c * S, r * S)); d.text((c * S + 6, r * S + 4), f"{n} {lab}", fill="yellow")
sheet.save(out, quality=82)
