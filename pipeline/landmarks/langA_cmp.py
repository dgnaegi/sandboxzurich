"""Foto | Spiel at 12 facades of Langstrasse Nord -> preview/langA_cmp.jpg. usage: langA_cmp.py [--shots-only|--sheet-only]"""
import json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point
ROOT = Path(__file__).resolve().parents[2]
AX = LineString([(940, -260), (954, -231), (979, -189), (1043, -74), (1081, -6), (1104, 36), (1125, 80)])
# (label, building centre x,y)
T = [("Chicago Bar", 1014, -158), ("Coop to go", 992, -136), ("Hotel 210", 1028, -124), ("Lebara 206", 1019, -143), ("Cinque 215", 1023, -79), ("MeiXin 102", 1038, -53),
     ("Werner", 1078, -34), ("Burgermeister 243", 1093, 43), ("Langstr. 193", 966, -186), ("Langstr. 197", 977, -159), ("Josefstr. 91", 1058, -107), ("Langstr. 231", 1064, -8)]
M = json.load(open(ROOT / "research/langstrasse_A_photos.json"))
shots, pics = [], []
for i, (lab, x, y) in enumerate(T):
    s = AX.project(Point(x, y)); a = AX.interpolate(s); q = AX.interpolate(s + 1)
    left = ((q.x - a.x) * (y - a.y) - (q.y - a.y) * (x - a.x)) > 0
    key = f"ls{int(s // 7 * 7):03d}{'L' if left else 'R'}"
    p = (M.get(key) or {}).get("photos") or []
    if not p:   # neighbour targets
        for d in (-7, 7, -14, 14):
            k2 = f"ls{int((s + d) // 7 * 7):03d}{'L' if left else 'R'}"
            p = (M.get(k2) or {}).get("photos") or []
            if p: break
    pics.append(p[0]["file"] if p else None)
    cx, cy = a.x, a.y
    hdg = math.degrees(math.atan2(x - cx, y - cy)) % 360
    shots.append(dict(id=f"c{i:02d}", x=round(cx - (x - cx) * 0.0, 1), y=round(cy, 1), hdg=round(hdg), t="13:00"))
(ROOT / "preview/_langA").mkdir(exist_ok=True)
json.dump(shots, open(ROOT / "preview/_langA/cmp_shots.json", "w"))
if "--sheet-only" not in sys.argv:
    subprocess.run(["node", "tests/fidelity_shots.mjs", "../preview/_langA/cmp_shots.json", "../preview/_langA/cmp", "70", "1.6"], cwd=ROOT / "web", check=True)
W, H = 480, 360
sheet = Image.new("RGB", (W * 4, H * 6), "black"); d = ImageDraw.Draw(sheet)
for i, (lab, x, y) in enumerate(T):
    c, r = (i % 2) * 2, i // 2
    if pics[i]: sheet.paste(Image.open(ROOT / pics[i]).convert("RGB").resize((W, H)), (c * W, r * H))
    g = ROOT / f"preview/_langA/cmp/game_c{i:02d}.png"
    if g.exists(): sheet.paste(Image.open(g).convert("RGB").resize((W, H)), ((c + 1) * W, r * H))
    d.rectangle((c * W, r * H, c * W + 200, r * H + 13), fill="black"); d.text((c * W + 3, r * H + 1), f"{lab}: Foto | Spiel", fill="yellow")
sheet.save(ROOT / "preview/langA_cmp.jpg", quality=80); print("ok")
