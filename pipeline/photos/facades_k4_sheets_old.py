"""Contact sheets from the earlier frontal Mapillary crops (candidates.json) for Kreis 4 targets without a note. -> research/buildings/k4/sheets_old/NNN.jpg + index_old.json"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent.parent
K = ROOT / "research/buildings/k4"; SH = K / "sheets_old"; SH.mkdir(exist_ok=True)
import sys; sys.path.insert(0, str(Path(__file__).parent))
from facades_k4_sheets import PRIO
def main():
    T = json.load(open(K / "targets.json")); cand = json.load(open(ROOT / "research/buildings/sheets_v3/candidates.json"))
    order = {s: i for i, s in enumerate(PRIO)}; items = []
    for t in T:
        c = cand.get(t["addr"])
        if t["note"] or not c or not c.get("imgs"): continue
        f = ROOT / "data/raw/photos/facades" / c["imgs"][0]["file"]
        if not f.exists(): continue
        n = "".join(ch for ch in t["nr"] if ch.isdigit()); items.append((order.get(t["street"], 99), t["street"], int(n or 0), t["nr"], t, f, c["imgs"][0]))
    items.sort(key=lambda x: x[:4]); font = ImageFont.load_default(size=15); idx = {}
    for s in range(0, len(items), 12):
        sh = Image.new("RGB", (1600, 900), "white"); d = ImageDraw.Draw(sh); names = []
        for j, it in enumerate(items[s:s + 12]):
            t = it[4]; im = Image.open(it[5]).convert("RGB").resize((400, 300))
            x, y = (j % 4) * 400, (j // 4) * 300; sh.paste(im, (x, y)); d.rectangle([x, y, x + 399, y + 20], fill=(0, 0, 0))
            d.text((x + 4, y + 2), f"{j+1} {t['addr']} ({t['year'] or '?'}, {t['floors'] or '?'}G)", fill=(255, 255, 0), font=font); names.append(t["addr"])
        n = s // 12 + 1; sh.save(SH / f"{n:03d}.jpg", quality=80); idx[f"{n:03d}"] = [(a, items[s + i][6]) for i, a in enumerate(names)]
    json.dump(idx, open(K / "index_old.json", "w"), ensure_ascii=False); print(len(items), "houses", len(idx), "sheets")
main()
