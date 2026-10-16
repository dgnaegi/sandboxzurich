"""Photo <-> game comparison sheets preview/station_cmp_<id>.jpg (3 rows: platform view, access, roof; left photo, right game, 1600 px wide).
Run: .venv/bin/python pipeline/landmarks/st_cmp.py [hardbruecke altstetten wiedikon]   (dev server on :5173)"""
import sys, json, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent.parent
E = 1.65
# id -> rows: (photo index in photos_<id>.json, label, p=(x,y,eye z abs), l=(x,y,look z abs), fov)
VIEWS = {
 "altstetten": [(48, "Perron 3/4", (-2065, 801, -11.58 + E), (-2150, 834, -11.7), 65), (46, "Dach/Stuetze", (-2098, 815, -11.58 + 1.4), (-2101, 816.5, -11.58 + 4.3), 70), (7, "Treppe zur Passage", (-2078, 806, -11.58 + E), (-2088, 810.5, -13.8), 65)],
 "hardbruecke": [(2, "Perron 1", (95, 115, -6.0 + E), (30, 140, -6.0 + 1.5), 65), (6, "Aufgang Brueckenebene", (60.4, 128.3, 1.2 + E), (76, 121.5, -5.5), 65), (44, "Perrondach von der Bruecke", (112, 162, 6.5), (60, 128, -5.0), 60)],
 "wiedikon": [(5, "Perron 2/3", (388, -1257.6, -4.9 + E), (458, -1329, -4.9 + 1.7), 65), (32, "Aufnahmegebaeude", (520, -1440, 1.5), (544, -1403, 4.0), 60), (5, "Perrondach", (485, -1355, -4.9 + 1.5), (508, -1378, -4.9 + 3.0), 70)],
}
S = ROOT / "data/build/stcmp"; S.mkdir(parents=True, exist_ok=True)
ids = sys.argv[1:] or list(VIEWS)
for sid in ids:
    ph = json.load(open(ROOT / f"research/stations/photos_{sid}.json"))
    vs = [{"p": [v[2][0], v[2][1], 0], "az": v[2][2], "l": [v[3][0], v[3][1], 0], "lz": v[3][2], "fov": v[4], "w": 800, "hh": 450, "wait": 6000} for v in VIEWS[sid]]
    subprocess.run(["node", str(ROOT / "pipeline/landmarks/free_shot.mjs"), str(S / sid), json.dumps(vs)], check=False, capture_output=True)
    W = Image.new("RGB", (1600, 450 * len(vs)), (20, 20, 20)); d = ImageDraw.Draw(W)
    for i, v in enumerate(VIEWS[sid]):
        im = Image.open(ROOT / ph[v[0]]["file"]).convert("RGB"); im.thumbnail((800, 450)); W.paste(im, (0, i * 450))
        try: W.paste(Image.open(S / f"{sid}_{i}.jpg"), (800, i * 450))
        except Exception as e: print("missing", sid, i, e)
        d.rectangle([0, i * 450, 330, i * 450 + 14], fill=(0, 0, 0)); d.text((3, i * 450 + 1), f"Foto #{v[0]} ({ph[v[0]]['source']}, {ph[v[0]]['license']}) {v[1]}", fill=(255, 220, 0))
        d.rectangle([800, i * 450, 900, i * 450 + 14], fill=(0, 0, 0)); d.text((803, i * 450 + 1), "Spiel", fill=(255, 220, 0))
    W.save(ROOT / f"preview/station_cmp_{sid}.jpg", quality=80); print("wrote", sid)
