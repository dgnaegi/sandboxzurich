"""Photo <-> model comparison sheets: preview/hb_cmp_<name>.jpg (photo left, isolated model right). Needs the dev server (view.mjs)."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, '.')
from hb_kit import to_world, ORG, ROOT
SETS = {  # name: (photo file name, model name, [d, c, h, d, c, h, fov], label)
    "halle": ("cm_Z_rich_Hauptbahnhof_16233218675_jpg.jpg", "Zürich Hauptbahnhof + Innenraum", [35, -4, 1.7, 113, -4, 9, 70], "Haupthalle: Blick nach Osten"),
    "fassade": ("cm_Curych_2017_36_jpg.jpg", "Zürich Hauptbahnhof", [64, -114, 3.2, 46, -60, 11, 58], "Fassade Bahnhofplatz"),
    "perron": ("cm_3_IR_2441_Zue_Chi_Zuerich_HB_101216_jpg.jpg", "Zürich Hauptbahnhof + Perrons", [-62, -40, 2.7, -160, -40, 5, 62], "Perron 4/5 Richtung Westen"),
    "querhalle": ("cm_Hauptbahnhof_Z_rich_Haupthalle_2018_09_05_14_22_48_jpg.jpg", "Zürich Hauptbahnhof + Innenraum", [-30, -45, 1.7, -30, 20, 9, 75], "Querhalle"),
}
GAME = bool(__import__('os').environ.get('GAME'))
GH = {'perron': 0.3, 'halle': 0.14, 'querhalle': 0.14}   # extra eye height above ground in the game (raised deck / floor)
meta = json.load(open(ROOT / "research/hb/photos.json"))["photos"]
(ROOT / "preview").mkdir(exist_ok=True)
for name, (fn, mdl, v, label) in SETS.items():
    if len(sys.argv) > 1 and name not in sys.argv[1].split(","): continue
    p = to_world(v[0], v[1]); l = to_world(v[3], v[4])
    tmp = f"/tmp/hbcmp_{name}"
    if GAME:   # real game (test server :5176 with the HB tiles), see hb_game_shot.mjs
        views = [{"p": [round(p[0], 1), round(p[1], 1), v[2] + GH.get(name, 0)], "l": [round(l[0], 1), round(l[1], 1), v[5]], "fov": v[6], "w": 900, "hh": 500, "t": "12:00", "wait": 7000}]
        subprocess.run(["node", "hb_game_shot.mjs", tmp, json.dumps(views)], check=True, capture_output=True)
    else:
        views = [{"m": mdl, "p": [round(p[0] - ORG[0], 2), round(p[1] - ORG[1], 2), v[2]], "l": [round(l[0] - ORG[0], 2), round(l[1] - ORG[1], 2), v[5]], "fov": v[6], "n": 0}]
        subprocess.run(["node", "view.mjs", tmp, json.dumps(views)], check=True, capture_output=True)
    src = next(x for x in meta if x["file"].endswith(fn))
    a = Image.open(ROOT / src["file"]).convert("RGB"); b = Image.open(tmp + "_0.jpg").convert("RGB")
    H = 450; a = a.resize((int(a.width * H / a.height), H)); b = b.resize((int(b.width * H / b.height), H))
    s = Image.new("RGB", (a.width + b.width + 10, H + 26), (20, 20, 20)); s.paste(a, (0, 26)); s.paste(b, (a.width + 10, 26))
    d = ImageDraw.Draw(s); d.text((6, 6), f"{label} | Foto: {src['author'][:40]} ({src['license']}, Commons) | rechts: {'Spiel (HB-Kacheln)' if GAME else 'Modell (isoliert)'}", fill=(255, 255, 255))
    out = ROOT / "preview" / f"hb_cmp_{name}.jpg"; s.save(out, quality=82); print(out.name, s.size)
