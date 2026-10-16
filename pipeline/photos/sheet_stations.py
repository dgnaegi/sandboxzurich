"""Contact sheets preview/ref_station_<id>.jpg (10 columns, 160x120 cells, numbered) + research/stations/photos_<id>.json (index -> file/licence)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
d = json.load(open(ROOT / "research/v3/photos_stations.json"))
G = {"hardbruecke": ("st_hb_w", "st_hb_m", "st_hb_e", "st_hb_zug"), "altstetten": ("st_alt_w", "st_alt_m", "st_alt_e", "st_alt_zug"), "wiedikon": ("st_wie_w", "st_wie_m", "st_wie_e", "st_wie_zug")}
for sid, keys in G.items():
    seen, ph = set(), []
    for k in keys:
        for p in d.get(k, {}).get("photos", []):
            if p["file"] in seen: continue
            seen.add(p["file"]); ph.append({**p, "site": k})
    cols, w, h = 10, 160, 120; rows = (len(ph) + cols - 1) // cols
    S = Image.new("RGB", (cols * w, rows * h), (20, 20, 20)); dr = ImageDraw.Draw(S)
    for i, p in enumerate(ph):
        try: im = Image.open(ROOT / p["file"]).convert("RGB")
        except Exception: continue
        im.thumbnail((w, h)); S.paste(im, ((i % cols) * w, (i // cols) * h))
        dr.rectangle([(i % cols) * w, (i // cols) * h, (i % cols) * w + 24, (i // cols) * h + 12], fill=(0, 0, 0)); dr.text(((i % cols) * w + 2, (i // cols) * h), str(i), fill=(255, 220, 0))
    S.save(ROOT / f"preview/ref_station_{sid}.jpg", quality=84)
    json.dump([{"i": i, "file": p["file"], "source": p["source"], "license": p["license"], "author": p.get("author"), "url": p["url"], "heading": p.get("heading"), "year": p.get("year"), "site": p["site"]} for i, p in enumerate(ph)],
              open(ROOT / f"research/stations/photos_{sid}.json", "w"), ensure_ascii=False, indent=0)
    print(sid, len(ph), "photos", S.size)
