"""Contact sheets of GWR-entrance crops (house + shopfront) for hand-reading facades. Skips addresses already in visual_notes_v3."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
E = {e["id"]: e for e in json.load(open(ROOT / "research/shops_v3/entrances_langB.json"))}
M = json.load(open(ROOT / "research/shops_v3/photos_langB_entr.json"))
N = json.load(open(ROOT / "research/buildings/visual_notes_v3.json"))
ids = [k for k in M if M[k] and E[k]["addr"] not in N]
seen = set(); ids2 = []
for k in sorted(ids, key=lambda k: -E[k]["y"]):
    if E[k]["addr"] in seen: continue
    seen.add(E[k]["addr"]); ids2.append(k)
W, H = 400, 300; PER = 5
sd = ROOT / "research/shops_v3/sheets_langB_entr"; sd.mkdir(exist_ok=True)
for f in sd.glob("*.jpg"): f.unlink()
idx = {}
for s in range(0, len(ids2), PER):
    grp = ids2[s:s + PER]; im = Image.new("RGB", (W * 4, (H + 14) * len(grp)), "white"); d = ImageDraw.Draw(im)
    for r, k in enumerate(grp):
        d.text((3, r * (H + 14) + 2), f"{r+1}. {E[k]['addr']}  ({int(E[k]['x'])},{int(E[k]['y'])})", fill="black")
        tiles = []
        for v in M[k][:3]:
            if v.get("house"): tiles.append(v["house"])
        tiles = tiles[:2] + [v["shop"] for v in M[k][:2]]
        for c, t in enumerate(tiles[:4]):
            im.paste(Image.open(ROOT / t).convert("RGB").resize((W, H)), (c * W, r * (H + 14) + 14))
    n = s // PER + 1; im.save(sd / f"sheet_{n:02d}.jpg", quality=78); idx[f"sheet_{n:02d}"] = [E[k]["addr"] for k in grp]
json.dump(idx, open(sd / "index.json", "w"), ensure_ascii=False)
print(len(ids2), "addresses", len(idx), "sheets"); [print(k, v) for k, v in idx.items()]
