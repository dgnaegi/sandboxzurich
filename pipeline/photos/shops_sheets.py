"""Contact sheets: 12 venues per sheet (4x3, 1600 px wide), best photo each, labelled with index/name/address.
Reads research/shops_v3/photos.json, writes research/shops_v3/sheets/sheet_NN.jpg and sheets/index.json (sheet -> ids)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
M = json.load(open(ROOT / "research/shops_v3/photos.json"))
ids = [k for k, v in M.items() if v["photos"]]
W, H, LAB = 400, 300, 34
try: font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
except OSError: font = ImageFont.load_default()
out = ROOT / "research/shops_v3/sheets"; out.mkdir(parents=True, exist_ok=True)
for f in out.glob("sheet_*.jpg"): f.unlink()
index = {}
for s in range(0, len(ids), 12):
    chunk = ids[s:s + 12]; sh = Image.new("RGB", (W * 4, (H + LAB) * 3), "white"); d = ImageDraw.Draw(sh)
    for i, k in enumerate(chunk):
        v = M[k]; cx, cy = (i % 4) * W, (i // 4) * (H + LAB)
        im = Image.open(ROOT / v["photos"][0]["file"]).convert("RGB"); im.thumbnail((W, H)); sh.paste(im, (cx, cy))
        d.text((cx + 3, cy + H + 1), f"{i+1}. {v['name'][:34]}", fill="black", font=font)
        d.text((cx + 3, cy + H + 17), (v["address"] or "")[:44], fill=(90, 90, 90), font=font)
    n = s // 12 + 1; sh.save(out / f"sheet_{n:02d}.jpg", quality=80); index[f"sheet_{n:02d}"] = chunk
json.dump(index, open(out / "index.json", "w"), indent=0)
print(len(ids), "venues,", len(index), "sheets")
