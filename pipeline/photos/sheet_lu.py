"""Contact sheets for the Langstrasse underpass + Ole Ole Bar photo sets (research/v3/photos.json ids langstr_unterf*, oleole).
Writes preview/ref_v3_langstr_unterf.jpg (+ _b) and preview/ref_v3_oleole.jpg (numbered 'id:index', 5 columns)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
meta = json.load(open(ROOT / "research/v3/photos.json"))
COLS, W, HH = 5, 320, 240


def sheet(items, dest):
    rows = (len(items) + COLS - 1) // COLS
    s = Image.new("RGB", (COLS * W, rows * HH), (25, 25, 25)); d = ImageDraw.Draw(s)
    for k, (sid, i, p) in enumerate(items):
        x, y = (k % COLS) * W, (k // COLS) * HH
        try:
            im = Image.open(ROOT / p["file"]).convert("RGB"); im.thumbnail((W - 4, HH - 4)); s.paste(im, (x + 2, y + 2))
        except OSError:
            pass
        d.rectangle([x + 2, y + 2, x + 120, y + 18], fill=(0, 0, 0))
        d.text((x + 6, y + 4), f"{sid[-5:]}:{i} {p['source'][0].upper()}{' N' if p.get('night') else ''}", fill=(255, 220, 0))
    s.save(dest, "JPEG", quality=76)


def main():
    lu = [(sid, i, p) for sid in ("langstr_unterf", "langstr_unterf_sued", "langstr_unterf_nord") for i, p in enumerate(meta[sid]["photos"])]
    seen, uniq = set(), []
    for t in lu:
        if t[2]["file"] not in seen:
            seen.add(t[2]["file"]); uniq.append(t)
    lu = uniq
    print("underpass photos", len(lu))
    for n in range(0, len(lu), 25):
        sheet(lu[n:n + 25], ROOT / "preview" / ("ref_v3_langstr_unterf%s.jpg" % ("" if n == 0 else "_%d" % (n // 25 + 1))))
    ol = [("oleole", i, p) for i, p in enumerate(meta["oleole"]["photos"])]
    print("oleole photos", len(ol))
    sheet(ol[:25], ROOT / "preview/ref_v3_oleole.jpg")


main()
