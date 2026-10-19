"""Zone 1 contact sheets (16 houses, 4x4, 400x300 tiles, labelled) -> research/zones/z1/sheets/NNN.jpg + index.json (nearest to camera points first)."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent.parent
Z = ROOT / "research/zones/z1"; P3 = "--pass3" in sys.argv; P2 = "--pass2" in sys.argv or P3   # photos2.json (remaining unnoted targets, looser photo selection)
SH = Z / ("sheets3" if P3 else "sheets2" if P2 else "sheets"); SH.mkdir(exist_ok=True)
def main():
    T = json.load(open(Z / "targets.json")); P = json.load(open(Z / ("photos3.json" if P3 else "photos2.json" if P2 else "photos.json")))
    if P2:   # only houses without a usable pass-1 photo
        P1 = json.load(open(Z / "photos.json")); P1.update({a: m for a, m in json.load(open(Z / "photos2.json")).items() if m["photos"]} if P3 else {}); T = [t for t in T if t["addr"] in P and not (P1.get(t["addr"]) or {}).get("photos")]
    items = [(t, P[t["addr"]]["photos"][0]) for t in T if (P.get(t["addr"]) or {}).get("photos")]
    font = ImageFont.load_default(size=16); idx = {}
    for s in range(0, len(items), 16):
        sh = Image.new("RGB", (1600, 1200), "white"); d = ImageDraw.Draw(sh); names = []
        for j, (t, ph) in enumerate(items[s:s + 16]):
            im = Image.open(ROOT / ph["file"]).convert("RGB").resize((400, 300))
            x, y = (j % 4) * 400, (j // 4) * 300
            sh.paste(im, (x, y)); d.rectangle([x, y, x + 399, y + 20], fill=(0, 0, 0))
            d.text((x + 4, y + 2), f"{j+1} {t['addr']} ({t['year'] or '?'}, {t['floors'] or '?'}G)", fill=(255, 255, 0), font=font)
            d.line([x + 200, y + 20, x + 200, y + 34], fill=(255, 0, 0), width=2)
            names.append(t["addr"])
        n = s // 16 + 1; sh.save(SH / f"{n:03d}.jpg", quality=78); idx[f"{n:03d}"] = names
    json.dump(idx, open(Z / ("index3.json" if P3 else "index2.json" if P2 else "index.json"), "w"), ensure_ascii=False)
    print(len(items), "houses,", len(idx), "sheets")
main()
