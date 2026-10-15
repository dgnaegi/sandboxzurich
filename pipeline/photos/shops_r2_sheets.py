"""Round 2 contact sheets (12 per sheet, 4x3, 1600 px): venues with an R2 photo, not yet photo_ok (shops_v3.json), then
R1-only venues of sheets 22+ (no R2 photo). Writes research/shops_v3/sheets_r2/sheet_NN.jpg + index.json
(sheet -> [{id, file}])."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent.parent; D = ROOT / "research/shops_v3"
R2 = json.load(open(D / "photos_r2.json")); R1 = {e["id"]: e for e in json.load(open(D / "shops_v3.json"))}
ok = {k for k, e in R1.items() if e["photo_ok"]}
ann2 = set()
if (D / "annotations_r2.jsonl").exists(): ann2 = {json.loads(l)["id"] for l in open(D / "annotations_r2.jsonl") if l.strip()}
items = []
pri = lambda k: (k not in R1, R1.get(k, {}).get("photo_ok") is not None)   # null first (never seen), then false
CI = {c['id']: i for i, c in enumerate(json.load(open(D / 'candidates.json')))}
r2ids = sorted([k for k, v in R2.items() if v["photos"] and k not in ok and k not in ann2], key=lambda k: CI[k])
for k in r2ids: items.append((k, R2[k]["name"], R2[k]["address"], R2[k]["photos"][0]["file"]))
for k, e in R1.items():
    if k in ok or k in R2 and R2[k]["photos"]: continue
    if e["photo_ok"] is None: items.append((k, e["name"], e["address"], e["photos"][0]["file"]))
W, H, LAB = 400, 300, 34
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
out = D / "sheets_r2"; out.mkdir(exist_ok=True)
for f in out.glob("sheet_*.jpg"): f.unlink()
index = {}
for s in range(0, len(items), 12):
    ch = items[s:s + 12]; sh = Image.new("RGB", (W * 4, (H + LAB) * 3), "white"); d = ImageDraw.Draw(sh)
    for i, (k, n, a, f) in enumerate(ch):
        cx, cy = (i % 4) * W, (i // 4) * (H + LAB)
        im = Image.open(ROOT / f).convert("RGB"); im.thumbnail((W, H)); sh.paste(im, (cx, cy))
        d.text((cx + 3, cy + H + 1), f"{i+1}. {n[:34]}", fill="black", font=font); d.text((cx + 3, cy + H + 17), (a or "")[:44], fill=(90, 90, 90), font=font)
    nn = s // 12 + 1; sh.save(out / f"sheet_{nn:02d}.jpg", quality=80); index[f"sheet_{nn:02d}"] = [dict(id=k, file=f) for k, n, a, f in ch]
json.dump(index, open(out / "index.json", "w"), indent=0)
print(len(items), "venues,", len(index), "sheets")
