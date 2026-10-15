"""Numbered contact sheets per v3 site: preview/ref_v3_<id>.jpg (16 picks, 4x4, 1600 px wide) and
preview/ref_v3_<id>_b.jpg (the remaining photos, if >= 6). Numbers = index in research/v3/photos.json[id].photos.

Pick order for sheet a: up to 6 Commons, 2 Panoramax, 1 night shot, then Mapillary spread by bearing.
Usage: python contact_sheet_v3.py [id,id]
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent
META = ROOT / "research" / "v3" / "photos.json"
COLS, W, HH = 4, 400, 300


def sheet(items, dest):
    rows = (len(items) + COLS - 1) // COLS
    s = Image.new("RGB", (COLS * W, rows * HH), (25, 25, 25))
    d = ImageDraw.Draw(s)
    for k, (i, p) in enumerate(items):
        x, y = (k % COLS) * W, (k // COLS) * HH
        try:
            im = Image.open(ROOT / p["file"]).convert("RGB")
            im.thumbnail((W - 4, HH - 4))
            s.paste(im, (x + 2, y + 2))
        except OSError:
            pass
        d.rectangle([x + 2, y + 2, x + 70, y + 20], fill=(0, 0, 0))
        tag = {"mapillary": "M", "commons": "C", "panoramax": "P"}[p["source"]]
        d.text((x + 6, y + 5), f"#{i} {tag}{' N' if p.get('night') else ''}", fill=(255, 220, 0))
    s.save(dest, "JPEG", quality=78)


def main():
    meta = json.load(open(META))
    ids = sys.argv[1].split(",") if len(sys.argv) > 1 else list(meta)
    for sid in ids:
        ph = list(enumerate(meta[sid]["photos"]))
        if not ph:
            continue
        la, lo = meta[sid]["lat"], meta[sid]["lon"]
        cm = [x for x in ph if x[1]["source"] == "commons"]
        pick = [x for x in cm if x[1].get("via")][:4] + [x for x in cm if not x[1].get("via")][:3] + [x for x in ph if x[1]["source"] == "panoramax"][:2]
        pick += [x for x in ph if x[1].get("night") and x not in pick][:1]
        ml = [x for x in ph if x[1]["source"] == "mapillary" and x not in pick]
        ml.sort(key=lambda x: math.atan2(x[1]["lon"] - lo, x[1]["lat"] - la))
        need = 16 - len(pick)
        if len(ml) > need:
            ml = [ml[int(j * len(ml) / need)] for j in range(need)]
        pick += ml
        pick = pick[:16]
        sheet(pick, ROOT / "preview" / f"ref_v3_{sid}.jpg")
        rest = [x for x in ph if x not in pick]
        if len(rest) >= 6:
            sheet(rest[:16], ROOT / "preview" / f"ref_v3_{sid}_b.jpg")
        print(sid, len(ph), len(pick), len(rest))


if __name__ == "__main__":
    main()
