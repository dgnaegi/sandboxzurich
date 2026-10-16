"""Contact sheets of the Langstrasse Nord facade crops: preview/ref_langA_NN.jpg (12 per sheet, 4x3, labelled s=metres along axis, side, source/date)."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[2]
M = json.load(open(ROOT / "research/langstrasse_A_photos.json"))
items = []
for k, v in sorted(M.items()):
    for n, p in enumerate(v["photos"][:1]):
        items.append((k, p))
W, H = 400, 300
for si in range(0, len(items), 12):
    sh = Image.new("RGB", (W * 4, H * 3), "black"); d = ImageDraw.Draw(sh)
    for j, (k, p) in enumerate(items[si:si + 12]):
        im = Image.open(ROOT / p["file"]).convert("RGB").resize((W, H)); x, y = (j % 4) * W, (j // 4) * H
        sh.paste(im, (x, y)); d.rectangle((x, y, x + 230, y + 13), fill="black")
        d.text((x + 3, y + 1), f"{k} {p['source'][:3]} {p['date'][:4]} d{p['dist_m']:.0f}", fill="yellow")
    sh.save(ROOT / f"preview/ref_langA_{si // 12 + 1:02d}.jpg", quality=80)
print(len(items), "->", (len(items) + 11) // 12, "sheets")
