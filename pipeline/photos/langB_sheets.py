"""Contact sheets for Langstrasse Sued: one row per venue (3 shopfront crops). Usage: langB_sheets.py [all]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
meta = json.load(open(ROOT / "research/shops_v3/photos_langB.json"))
shops = {e["id"]: e for e in json.load(open(ROOT / "research/shops_v3/shops_v3.json"))}
ann = ROOT / "research/shops_v3/annotations_langB.jsonl"
done = {json.loads(l)["id"] for l in open(ann)} if ann.exists() else set()
ids = [k for k, v in meta.items() if v and k not in done and (sys.argv[1:] == ["all"] or not shops[k].get("photo_ok"))]
ids.sort(key=lambda k: shops[k]["y"], reverse=True)
W, H = 520, 390; PER = 4
out = ROOT / "preview"; out.mkdir(exist_ok=True)
sd = ROOT / "research/shops_v3/sheets_langB"; sd.mkdir(exist_ok=True)
for f in sd.glob("*.jpg"): f.unlink()
idx = {}
for s in range(0, len(ids), PER):
    grp = ids[s:s + PER]; im = Image.new("RGB", (W * 3, (H + 18) * len(grp)), "white"); d = ImageDraw.Draw(im)
    for r, k in enumerate(grp):
        e = shops[k]; d.text((4, r * (H + 18) + 3), f"{r+1}. {e['name']} | {e['kind'][8:]} | {e['address'][:40]} | ({int(e['x'])},{int(e['y'])})", fill="black")
        for c, v in enumerate(meta[k][:3]):
            t = Image.open(ROOT / v["shop"]).convert("RGB").resize((W, H)); im.paste(t, (c * W, r * (H + 18) + 18))
    n = s // PER + 1; im.save(sd / f"sheet_{n:02d}.jpg", quality=80); idx[f"sheet_{n:02d}"] = grp
json.dump(idx, open(sd / "index.json", "w"))
print(len(ids), "venues", len(idx), "sheets")
