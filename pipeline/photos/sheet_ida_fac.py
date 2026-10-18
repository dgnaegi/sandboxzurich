"""Facade contact sheets for the Idaplatz quarter: preview/ref_ida_fac_N.jpg (12 houses, 4x3), index research/buildings/ida/sheets.json (N -> [addr])."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
D = ROOT / "research/buildings/ida"
T = json.load(open(D / "targets.json")); P = json.load(open(D / "photos.json"))
items = [(t["addr"], P[t["addr"]]["photos"][0]["file"], t["floors"], t["year"]) for t in T if (P.get(t["addr"]) or {}).get("photos")]
W, H = 400, 300; idx = {}
for s in range(0, len(items), 12):
    sh = Image.new("RGB", (4 * W, 3 * H), (25, 25, 25)); d = ImageDraw.Draw(sh); idx[s // 12] = []
    for k, (a, f, fl, yr) in enumerate(items[s:s + 12]):
        im = Image.open(ROOT / f).convert("RGB"); im.thumbnail((W - 4, H - 4))
        sh.paste(im, ((k % 4) * W + 2, (k // 4) * H + 2))
        d.rectangle([(k % 4) * W, (k // 4) * H, (k % 4) * W + 215, (k // 4) * H + 14], fill=(0, 0, 0))
        d.text(((k % 4) * W + 3, (k // 4) * H + 1), f"{a} ({fl}G {yr})", fill=(255, 220, 0)); idx[s // 12].append(a)
    sh.save(ROOT / f"preview/ref_ida_fac_{s // 12}.jpg", quality=80)
json.dump(idx, open(D / "sheets.json", "w"), ensure_ascii=False)
print(len(items), "houses,", len(idx), "sheets")
