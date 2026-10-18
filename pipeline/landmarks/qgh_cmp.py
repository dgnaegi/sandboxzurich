"""Photo | game comparison -> preview/qgh_cmp.jpg. Usage: qgh_cmp.py idx:photo_idx ...  (game shot qgh_g_<idx>.jpg vs photo index in research/quartiergarten_hard_photos.json)"""
import json, sys
from PIL import Image, ImageDraw
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; meta = json.load(open(ROOT / "research" / "quartiergarten_hard_photos.json"))
pairs = [tuple(map(int, a.split(":"))) for a in sys.argv[1:]]; W, H = 640, 480
sh = Image.new("RGB", (2 * W, len(pairs) * H), "white"); d = ImageDraw.Draw(sh)
for r, (g, p) in enumerate(pairs):
    a = Image.open(ROOT / meta[p]["file"]).convert("RGB"); a.thumbnail((W, H)); b = Image.open(ROOT / "preview" / f"qgh_g_{g}.jpg").convert("RGB"); b.thumbnail((W, H))
    sh.paste(a, (0, r * H)); sh.paste(b, (W, r * H)); d.text((4, r * H + 3), f"Foto #{p} ({meta[p]['source']})", fill="yellow"); d.text((W + 4, r * H + 3), "Spiel", fill="yellow")
sh.save(ROOT / "preview" / "qgh_cmp.jpg", quality=82)
