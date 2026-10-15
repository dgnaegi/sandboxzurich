"""Compose preview/plaza3_<id>.jpg (key photo | game) and plaza3_all.jpg (<=1600 px). Run from repo root with .venv/bin/python."""
import json, sys
from pathlib import Path
from PIL import Image
R = Path(__file__).resolve().parents[2]
ph = json.load(open(R / "research/v3/photos.json"))
sites = {s["id"]: s for s in json.load(open(R / "research/v3/places_v3.json"))["sites"]}
ids = [p.stem[len("plaza3_game_"):] for p in sorted((R / "preview").glob("plaza3_game_*.png"))]
tiles = []
for i in ids:
    g = Image.open(R / f"preview/plaza3_game_{i}.png").convert("RGB").resize((800, 450))
    k = (sites.get(i, {}).get("key_photos") or [0])[0]
    try:
        r = Image.open(R / ph[i]["photos"][k]["file"]).convert("RGB")
        w, h = r.size; s = max(800 / w, 450 / h); r = r.resize((int(w * s), int(h * s))); l = (r.width - 800) // 2; t = (r.height - 450) // 2
        r = r.crop((l, t, l + 800, t + 450))
    except Exception:
        r = Image.new("RGB", (800, 450), (30, 30, 30))
    pair = Image.new("RGB", (1600, 450)); pair.paste(r, (0, 0)); pair.paste(g, (800, 0)); pair.save(R / f"preview/plaza3_{i}.jpg", quality=82)
    tiles.append(g.resize((400, 225)))
W = 4; H = (len(tiles) + W - 1) // W
sheet = Image.new("RGB", (400 * W, 225 * H))
for n, t in enumerate(tiles): sheet.paste(t, ((n % W) * 400, (n // W) * 225))
sheet.save(R / "preview/plaza3_all.jpg", quality=82); print(len(tiles), "places")
