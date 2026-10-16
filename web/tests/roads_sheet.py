"""python roads_sheet.py N : per place i a before/after sheet (ground+oblique) -> preview/roads_fix_<i>.jpg (<=1600 px)"""
import sys
from PIL import Image, ImageDraw
P = "/Users/danielgnagi/sandboxzurich/preview/"
import json
names = [p["name"] for p in json.load(open("/Users/danielgnagi/sandboxzurich/logs/roads_places.json"))]
for i in range(int(sys.argv[1])):
    S = Image.new("RGB", (1600, 900), (30, 30, 30))
    for c, tag in enumerate(("before", "after")):
        for r, m in enumerate("go"):
            im = Image.open(f"{P}_roads_{tag}_{i}_{m}.png").convert("RGB").resize((800, 450))
            ImageDraw.Draw(im).text((8, 8), f"{tag} {names[i]} ({m})", fill=(255, 255, 0))
            S.paste(im, (c * 800, r * 450))
    S.save(f"{P}roads_fix_{i}.jpg", quality=80)
