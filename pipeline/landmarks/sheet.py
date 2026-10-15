"""Contact sheet: sheet.py out.jpg cols img1 img2 ... (each cell 533 px wide, 4:3)."""
import sys
from PIL import Image
out, cols, *f = sys.argv[1:]; cols = int(cols); w, h = 1600 // cols, 1200 // cols
rows = (len(f) + cols - 1) // cols
s = Image.new("RGB", (w * cols, h * rows))
for i, p in enumerate(f):
    im = Image.open(p).convert("RGB"); im.thumbnail((w, h)); s.paste(im, ((i % cols) * w, (i // cols) * h))
s.save(out, quality=85)
