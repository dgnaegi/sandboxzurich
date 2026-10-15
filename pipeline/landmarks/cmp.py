"""Side-by-side Foto | Spiel. Usage: cmp.py out.jpg ref1.jpg game1.jpg [ref2 game2 ...]  (rows of pairs, each 800 px wide)."""
import sys
from PIL import Image
out, *f = sys.argv[1:]
rows = []
for i in range(0, len(f), 2):
    ref = f[i]
    if "@" in ref:   # crop a cell (col,row) of a 4-column 400x300 reference sheet
        ref, cr = ref.split("@"); c, r_ = map(int, cr.split(","))
        a = Image.open(ref).convert("RGB").crop((c * 400, r_ * 300, c * 400 + 400, r_ * 300 + 300))
    else: a = Image.open(ref).convert("RGB")
    b = Image.open(f[i + 1]).convert("RGB")
    h = 450
    a = a.resize((int(a.width * h / a.height), h)); b = b.resize((int(b.width * h / b.height), h))
    r = Image.new("RGB", (a.width + b.width, h)); r.paste(a, (0, 0)); r.paste(b, (a.width, 0)); rows.append(r)
W = max(r.width for r in rows); H = sum(r.height for r in rows)
s = Image.new("RGB", (W, H)); y = 0
for r in rows: s.paste(r, (0, y)); y += r.height
if W > 1600: s = s.resize((1600, int(H * 1600 / W)))
s.save(out, quality=85)
