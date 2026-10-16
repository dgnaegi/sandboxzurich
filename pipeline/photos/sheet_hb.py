"""Contact sheets for HB photos: preview/ref_hb_<group>_<n>.jpg (4 x 5 cells of 400x300, numbered by index in research/hb/photos.json).
Usage: sheet_hb.py [group,group]   (default: all groups)"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
meta = json.load(open(ROOT / "research/hb/photos.json"))["photos"]
COLS, ROWS, W, H = 4, 5, 400, 300
groups = {}
for i, p in enumerate(meta): groups.setdefault(p.get("group", "x"), []).append((i, p))
sel = sys.argv[1].split(",") if len(sys.argv) > 1 else list(groups)
(ROOT / "preview").mkdir(exist_ok=True)
for g in sel:
    items = groups.get(g, [])
    for s in range(0, len(items), COLS * ROWS):
        ch = items[s:s + COLS * ROWS]
        sh = Image.new("RGB", (COLS * W, ((len(ch) + COLS - 1) // COLS) * H), (25, 25, 25)); d = ImageDraw.Draw(sh)
        for k, (i, p) in enumerate(ch):
            x, y = (k % COLS) * W, (k // COLS) * H
            try:
                im = Image.open(ROOT / p["file"]).convert("RGB"); im.thumbnail((W - 4, H - 4)); sh.paste(im, (x + 2, y + 2))
            except OSError: pass
            d.rectangle([x + 2, y + 2, x + 52, y + 18], fill=(0, 0, 0)); d.text((x + 6, y + 4), f"#{i}", fill=(255, 220, 0))
        out = ROOT / "preview" / f"ref_hb_{g}_{s // (COLS * ROWS)}.jpg"; sh.save(out, quality=72); print(out.name, len(ch))
