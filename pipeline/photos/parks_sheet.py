"""Contact sheet per park: preview/ref_parks_<id>.jpg (4x4 = 16 photos, 1600 px). Numbers = index in photos.json.
Usage: python parks_sheet.py id[,id]  (photos from research/parks/photos.json, or research/v3/photos.json for photos_from)"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
spec = {p["id"]: p for p in json.load(open(ROOT / "research/parks/parks.json"))["parks"]}
mine = json.load(open(ROOT / "research/parks/photos.json"))
v3 = json.load(open(ROOT / "research/v3/photos.json"))
for pid in sys.argv[1].split(","):
    src = spec[pid].get("photos_from")
    ph = (v3[src.split(":")[1] if ":" in src else pid] if src else mine[pid])["photos"]
    # prefer commons/pano, then spread
    order = sorted(range(len(ph)), key=lambda i: (ph[i]["source"] == "mapillary", i))[:16]
    s = Image.new("RGB", (1600, 1200)); d = ImageDraw.Draw(s)
    for k, i in enumerate(order):
        try:
            im = Image.open(ROOT / ph[i]["file"]).convert("RGB"); im.thumbnail((400, 300))
            s.paste(im, ((k % 4) * 400, (k // 4) * 300)); d.text(((k % 4) * 400 + 4, (k // 4) * 300 + 4), f"#{i}", fill=(255, 255, 0))
        except Exception as e:
            pass
    s.save(ROOT / f"preview/ref_parks_{pid}.jpg", quality=80); print(pid, len(ph))
