"""Contact sheets (12 houses, 4x3, 400x300 tiles, labelled) for Kreis 4 -> research/buildings/k4/sheets/NNN.jpg + index.json.
Order: priority streets first, unnoted before noted, only addresses with a photo. Usage: python facades_k4_sheets.py [--noted]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent.parent
K = ROOT / "research/buildings/k4"; NEW = "--new" in sys.argv
SH = K / ("sheets2" if NEW else "sheets"); SH.mkdir(exist_ok=True)
PRIO = ("Langstrasse Brauerstrasse Hohlstrasse Badenerstrasse Stauffacherstrasse Kanzleistrasse Bäckerstrasse Ankerstrasse Militärstrasse Lagerstrasse "
        "Zweierstrasse Kalkbreitestrasse Seebahnstrasse Wiesenstrasse Feldstrasse Dienerstrasse Hardstrasse Gertrudstrasse Zypressenstrasse Anwandstrasse "
        "Agnesstrasse Pflanzschulstrasse Josefstrasse Sihlfeldstrasse Bullingerstrasse Zwinglistrasse Müllerstrasse Hallwylstrasse").split()
def main():
    T = json.load(open(K / "targets.json")); P = json.load(open(K / "photos.json"))
    cand = json.load(open(ROOT / "research/buildings/sheets_v3/candidates.json"))
    order = {s: i for i, s in enumerate(PRIO)}
    items = []
    seen = {a for v in json.load(open(K / "index_pass1.json")).values() for a in v} if NEW else set()
    for t in T:
        ph = (P.get(t["addr"]) or {}).get("photos") or []
        if not ph: continue
        if t["note"] and "--noted" not in sys.argv: continue
        if t["addr"] in seen: continue
        n = "".join(c for c in t["nr"] if c.isdigit())
        items.append((order.get(t["street"], 99), t["street"], int(n or 0), t["nr"], t, ph[0]))
    items.sort(key=lambda x: x[:4])
    font = ImageFont.load_default(size=15) if hasattr(ImageFont, "load_default") else None
    idx = {}
    for s in range(0, len(items), 12):
        sh = Image.new("RGB", (1600, 900), "white"); d = ImageDraw.Draw(sh); names = []
        for j, it in enumerate(items[s:s + 12]):
            t, ph = it[4], it[5]
            im = Image.open(ROOT / ph["file"]).convert("RGB").resize((400, 300))
            x, y = (j % 4) * 400, (j // 4) * 300
            sh.paste(im, (x, y)); d.rectangle([x, y, x + 399, y + 20], fill=(0, 0, 0))
            d.text((x + 4, y + 2), f"{j+1} {t['addr']} ({t['year'] or '?'}, {t['floors'] or '?'}G)", fill=(255, 255, 0), font=font)
            d.line([x + 200, y + 20, x + 200, y + 34], fill=(255, 0, 0), width=2)
            names.append(t["addr"])
        n = s // 12 + 1; sh.save(SH / f"{n:03d}.jpg", quality=80); idx[f"{n:03d}"] = names
    json.dump(idx, open(K / ("index2.json" if NEW else "index.json"), "w"), ensure_ascii=False)
    print(len(items), "houses,", len(idx), "sheets")
if __name__ == "__main__":
    main()
