"""Round 3 contact sheets (12 per sheet, 4x3, 1600 px) for venues with an R3 photo, not photo_ok, not yet annotated in r3.
Label: index, name, address, source/dist/obliquity. Ordering: candidate prio. Optional arg 'alt' uses photo #2 (sheets_r3alt/).
Writes research/shops_v3/sheets_r3/sheet_NN.jpg + index.json."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent.parent; D = ROOT / "research/shops_v3"
ALT = "alt" in sys.argv; N = 1 if ALT else 0
R3 = json.load(open(D / "photos_r3.json")); SV = {e["id"]: e for e in json.load(open(D / "shops_v3.json"))}
ann = set()
if (D / "annotations_r3.jsonl").exists(): ann = {json.loads(l)["id"] for l in open(D / "annotations_r3.jsonl") if l.strip()}
seen = set()
if (D / "sheets_r3_seen.json").exists() and not ALT: seen = set()
CI = {c["id"]: i for i, c in enumerate(json.load(open(D / "candidates.json")))}
ids = sorted([k for k, v in R3.items() if len(v["photos"]) > N and not (SV.get(k) or {}).get("photo_ok") and k not in ann], key=lambda k: CI[k])
W, H, LAB = 400, 300, 34
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
out = D / ("sheets_r3alt" if ALT else "sheets_r3"); out.mkdir(exist_ok=True)
for f in out.glob("sheet_*.jpg"): f.unlink()
index = {}
for s in range(0, len(ids), 12):
    ch = ids[s:s + 12]; sh = Image.new("RGB", (W * 4, (H + LAB) * 3), "white"); d = ImageDraw.Draw(sh)
    for i, k in enumerate(ch):
        v = R3[k]; p = v["photos"][N]
        cx, cy = (i % 4) * W, (i // 4) * (H + LAB)
        im = Image.open(ROOT / p["file"]).convert("RGB"); im.thumbnail((W, H)); sh.paste(im, (cx, cy))
        d.text((cx + 3, cy + H + 1), f"{i+1}. {v['name'][:30]}", fill="black", font=font)
        d.text((cx + 3, cy + H + 17), f"{(v['address'] or '')[:24]} {p['dist_m']:.0f}m o{p['obliq']}", fill=(90, 90, 90), font=font)
    nn = s // 12 + 1; sh.save(out / f"sheet_{nn:02d}.jpg", quality=80); index[f"sheet_{nn:02d}"] = [dict(id=k, file=R3[k]["photos"][N]["file"]) for k in ch]
json.dump(index, open(out / "index.json", "w"), indent=0)
print(len(ids), "venues,", len(index), "sheets")
