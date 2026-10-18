"""Review sheet Foto | Spiel at 12 HB spots: hb_review.py out.jpg  (needs vite dev server :5173 with the HB tiles)."""
import json, subprocess, sys, os
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, '.')
from hb_kit import to_world, ROOT
# label, photo idx (research/hb/photos.json), [d,c,h, d,c,h, fov, extra eye height]
V = [
 ("1 Bahnhofplatz-Fassade", 0, [50, -135, 3, 46, -60, 11, 58, 0]),
 ("2 Haupthalle innen", 54, [35, -4, 1.7, 113, -4, 9, 70, .14]),
 ("3 Querhalle", 53, [-30, -45, 1.7, -30, 20, 9, 75, .14]),
 ("4 Perronhalle innen", 80, [-62, -40, 2.7, -160, -40, 5, 62, .3]),
 ("5 Perronhalle aussen/oben", 108, [-40, -120, 38, -170, -30, 5, 60, 0]),
 ("6 Perrondaecher 3-18 (West)", 161, [-330, 5, 22, -80, 5, 8, 65, 0]),
 ("7 Shopville-Treppe S2", 303, [60, -62, 1.7, 60, -95, -3.5, 65, 0]),
 ("8 Untergeschoss Shopville", 305, [10, -92, -3.6, 118, -92, -3.6, 70, 0]),
 ("9 Escher-Brunnen", 396, [48, -105, 2.5, 48, -78, 3, 55, 0]),
 ("10 Sihlquai/Museumstr.", 526, [95, 130, 5, 60, 45, 12, 60, 0]),
 ("11 Landesmuseum-Seite", 486, [-20, 120, 6, -20, 40, 12, 60, 0]),
 ("12 Gleisvorfeld", 81, [-470, 0, 8, -100, 0, 3, 65, 0]),
]
meta = json.load(open(ROOT / "research/hb/photos.json"))["photos"]
out = Path(sys.argv[1]); tmp = os.environ.get("TMP", "/tmp/hbrev")
vs = []
for lab, pi, v in V:
    p = to_world(v[0], v[1]); l = to_world(v[3], v[4])
    vs.append({"p": [round(p[0], 1), round(p[1], 1), v[2] + v[7]], "l": [round(l[0], 1), round(l[1], 1), v[5]], "fov": v[6], "w": 640, "hh": 360, "t": "12:00", "wait": 6000})
if not os.environ.get("SKIP"):
    r = subprocess.run(["node", "hb_review_shot.mjs", tmp, json.dumps(vs)], capture_output=True, text=True); print(r.stdout[-400:], r.stderr[-200:])
W, H = 260, 146
S = Image.new("RGB", (3 * (2 * W) + 2 * 6, 4 * (H + 18)), (20, 20, 20)); dr = ImageDraw.Draw(S)
for i, (lab, pi, v) in enumerate(V):
    x, y = (i % 3) * (2 * W + 6), (i // 3) * (H + 18)
    dr.text((x + 3, y + 3), lab + "  |  Foto  >  Spiel", fill=(255, 255, 255))
    try: a = Image.open(ROOT / meta[pi]["file"]).convert("RGB").resize((W, H)); S.paste(a, (x, y + 18))
    except Exception as e: print("photo", pi, e)
    try: b = Image.open(f"{tmp}_{i}.jpg").convert("RGB").resize((W, H)); S.paste(b, (x + W, y + 18))
    except Exception as e: print("game", i, e)
S.save(out, quality=80); print(out, S.size)
