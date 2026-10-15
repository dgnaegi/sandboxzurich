"""Top-down check: orthophoto | game for places. .venv/bin/python web/tests/plaza_top.py out.jpg win id [id ...]  (dev server on :5173)"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image
R = Path(__file__).resolve().parents[2]
out, win, ids = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
cen = json.load(open(R / "data/raw/ortho_places/centers.json"))
S = 560
sheet = Image.new("RGB", (2 * S, S * len(ids)))
for n, i in enumerate(ids):
    x, y = cen[i]
    tmp = f"/tmp/pt_{i}.png"
    subprocess.run(["node", "tests/topdown.mjs", tmp, str(x), str(y), str(win), str(S)], cwd=R / "web", check=True)
    ox, oy = x, y
    im = Image.open(R / f"data/raw/ortho_places/ortho_{i}.jpg").convert("RGB")
    pp = im.width / 140.0
    c = im.width / 2
    half = win / 2 * pp
    sheet.paste(im.crop((int(c - half), int(c - half), int(c + half), int(c + half))).resize((S, S)), (0, n * S))
    sheet.paste(Image.open(tmp).convert("RGB").resize((S, S)), (S, n * S))
sheet.save(out, quality=82)
