"""House-facade contact sheets (upper-facade crops) for Langstrasse Sued addresses lacking visual_notes_v3 entries."""
import json, re
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
meta = json.load(open(ROOT / "research/shops_v3/photos_langB.json"))
shops = json.load(open(ROOT / "research/shops_v3/shops_v3.json"))
notes = json.load(open(ROOT / "research/buildings/visual_notes_v3.json"))
rows = {}
for e in shops:
    m = re.match(r"(Langstrasse|Dienerstrasse|Hohlstrasse|Milit\w+strasse|Zwinglistrasse|Brauerstrasse|Kanonengasse|Neufrankengasse|Kernstrasse|Rolandstrasse) (\d+)", e["address"])
    if not m or m.group(0) in notes or m.group(0) in rows or not meta.get(e["id"]): continue
    if not any(p.get("house") for p in meta[e["id"]]): continue
    rows[m.group(0)] = e
ids = sorted(rows, key=lambda a: -rows[a]["y"])
W, H = 520, 390; PER = 4
sd = ROOT / "research/shops_v3/sheets_langB_house"; sd.mkdir(exist_ok=True)
for f in sd.glob("*.jpg"): f.unlink()
idx = {}
for s in range(0, len(ids), PER):
    grp = ids[s:s + PER]; im = Image.new("RGB", (W * 3, (H + 18) * len(grp)), "white"); d = ImageDraw.Draw(im)
    for r, a in enumerate(grp):
        d.text((4, r * (H + 18) + 3), f"{r+1}. {a} ({rows[a]['name']})", fill="black")
        for c, v in enumerate([p for p in meta[rows[a]["id"]] if p.get("house")][:3]):
            im.paste(Image.open(ROOT / v["house"]).convert("RGB").resize((W, H)), (c * W, r * (H + 18) + 18))
    n = s // PER + 1; im.save(sd / f"sheet_{n:02d}.jpg", quality=80); idx[f"sheet_{n:02d}"] = grp
json.dump(idx, open(sd / "index.json", "w"), ensure_ascii=False)
print(len(ids), "addresses", len(idx), "sheets"); [print(k, v) for k, v in idx.items()]
