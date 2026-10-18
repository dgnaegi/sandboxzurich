"""Contact sheet of the qgh reference photos. Usage: qgh_sheet.py out.jpg start count cols [thumb_w]"""
import json, sys
from PIL import Image, ImageDraw
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
meta = json.load(open(ROOT / "research" / "quartiergarten_hard_photos.json"))
out, s, n, cols = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]); tw = int(sys.argv[5]) if len(sys.argv) > 5 else 400; th = tw * 3 // 4
sel = list(enumerate(meta))[s:s + n]; rows = (len(sel) + cols - 1) // cols
sh = Image.new("RGB", (cols * tw, rows * th), "white"); d = ImageDraw.Draw(sh)
for k, (i, m) in enumerate(sel):
    im = Image.open(ROOT / m["file"]).convert("RGB"); im.thumbnail((tw, th)); x, y = (k % cols) * tw, (k // cols) * th
    sh.paste(im, (x, y)); d.rectangle([x, y, x + 34, y + 16], fill="black"); d.text((x + 3, y + 2), str(i), fill="yellow")
sh.save(ROOT / out, quality=80)
