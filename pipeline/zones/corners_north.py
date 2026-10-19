"""Zone 4 North corner check: corner list (junctions + camera points), best photo per corner, game view from the photo pose, contact sheets.
Usage: python pipeline/zones/corners_north.py pick   -> research/zones/z4/_corners_n.json
       python pipeline/zones/corners_north.py shots  -> game views (dev server :5173) + preview/z4n_corner_<k>.jpg (8 pairs per sheet)"""
import json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "pipeline")); sys.path.insert(0, str(ROOT / "pipeline" / "zones"))
from zones import wgs_to_local  # noqa
OUT = ROOT / "research/zones/z4/_corners_n.json"
CORNERS = [  # name, x, y (extra viewpoints at the north-quarter beyond OSM junction detection)
    ("Idaplatz Mitte", -112.3, -1113.7), ("Idaplatz Nord/Zurlindenstr", -130.5, -1095.9), ("Idastrasse Sued", -124.6, -1124.3),
    ("Bertastr/Zurlindenstr", -136.4, -1067.5), ("Zentralstr (Cam)", 7.7, -1101.7), ("Zurlindenstr West", -49.6, -1149.9),
    ("Zurlindenstr Ost", 30, -1190), ("Thomasweg/Martastr", -118.5, -953.7), ("Idaplatz/Idastr", -126.9, -1125.2),
    ("Badener/Martastr", -106.2, -875.6), ("Badener/Berta/Sihlfeld", 0, -939.4), ("Gertrud/Zentralstr", 3, -1107.4),
    ("Eschwies/Zurlindenstr", 20, -1216.2), ("Gertrud/Sihlfeld/Weststr", 41.9, -1072.2), ("Sihlfeld/Zentralstr", 57.6, -1160.1),
    ("Hasler/Zentralstr", 77.4, -1184.9), ("Idaplatz West", -150, -1110), ("Idaplatz Ost", -95, -1105),
    ("Bertastr Nord", -125, -1010), ("Zurlindenstr Mitte", -90, -1135), ("Zentralstr Nord", 8, -1040),
    ("Idastr Nord (Sued Berta)", -135, -1040), ("Thomasweg Sued", -118, -990), ("Martastr West", -170, -920),
]
def usable(f):
    im = Image.open(f).convert("L").resize((96, 64)); px = list(im.getdata()); top, bot = px[:96*32], px[96*32:]
    mean = sum(px)/len(px); var = lambda a: sum((v-sum(a)/len(a))**2 for v in a)/len(a)
    edges = sum(abs(px[i]-px[i+1]) for i in range(96*32-1) if (i+1) % 96)/(95*32)
    return mean > 75 and var(top) > 900 and edges > 6 and var(top) > .5*var(bot)
def pick():
    P = json.load(open(ROOT/"research/zones/z4/_photos_n.json")); res = []
    for n, cx, cy in CORNERS:
        best = None
        for p in P:
            dx, dy = cx-p["x"], cy-p["y"]; d = math.hypot(dx, dy)
            if d < 6 or d > 45: continue
            ang = math.degrees(math.atan2(dx, dy)) % 360; da = abs((p["h"]-ang+180) % 360-180)
            if da > 45: continue
            sc = d*0.5 + da*0.4 + 4*(2026-(p["yr"] or 2015))
            if best is None or sc < best[0]:
                if usable(ROOT/p["f"]): best = (sc, p, d, da)
        res.append(dict(name=n, x=cx, y=cy, photo=best and best[1]["f"], px=best and round(best[1]["x"], 1), py=best and round(best[1]["y"], 1), h=best and best[1]["h"], d=best and round(best[2])))
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(sum(1 for r in res if r["photo"]), "of", len(res), "corners with photo")
def shots():
    res = json.load(open(OUT)); views = []
    for i, r in enumerate(res):
        if not r["photo"]: continue
        yaw = math.radians(r["h"]); r["out"] = str(ROOT/f"preview/z4n_game_{i:02d}.jpg"); r["id"] = i
        views.append(dict(x=round(r["px"]+4*math.sin(yaw), 1), y=round(r["py"]+4*math.cos(yaw), 1), yaw=round(yaw, 2), out=r["out"]))
    vf = ROOT/"research/zones/z4/_views_n.json"; json.dump(views, open(vf, "w"))
    r_ = subprocess.run(["node", "tests/view_shots.mjs", str(vf)], cwd=ROOT/"web", capture_output=True, text=True); print(r_.stdout[-100:], r_.stderr[-200:])
    rows = [r for r in res if r["photo"]]; font = ImageFont.load_default(size=14); W, H = 400, 225
    for k in range(0, len(rows), 8):
        part = rows[k:k+8]; sh = Image.new("RGB", (1600, 2*H*0+((len(part)+1)//2)*H), (34, 34, 34)); d = ImageDraw.Draw(sh)
        for i, r in enumerate(part):
            ox, oy = (i % 2)*800, (i//2)*H
            try: sh.paste(Image.open(ROOT/r["photo"]).convert("RGB").resize((W, H)), (ox, oy)); sh.paste(Image.open(r["out"]).convert("RGB").resize((W, H)), (ox+W, oy))
            except Exception as e: print(e)
            d.rectangle([ox, oy, ox+330, oy+18], fill=(0, 0, 0)); d.text((ox+3, oy+1), f"#{r['id']} {r['name']} ({Path(r['photo']).stem[-8:]})", fill=(255, 255, 0), font=font)
        sh.save(ROOT/f"preview/z4n_corner_{k//8+1}.jpg", quality=80)
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
def labels():
    """Photo-only sheets (3x3) with address labels of buildings (research/buildings/ida/targets.json, OSM floors) projected by bearing (assumed 95 deg field of view)."""
    T = json.load(open(ROOT/"research/buildings/ida/targets.json")); res = [r for r in json.load(open(OUT)) if r["photo"]]
    font = ImageFont.load_default(size=13); W, H = 533, 300
    for k in range(0, len(res), 9):
        sh = Image.new("RGB", (1600, 900), (34, 34, 34)); d = ImageDraw.Draw(sh)
        for i, r in enumerate(res[k:k+9]):
            ox, oy = (i % 3)*W, (i//3)*H
            sh.paste(Image.open(ROOT/r["photo"]).convert("RGB").resize((W, H)), (ox, oy)); d.rectangle([ox, oy, ox+W, oy+16], fill=(0, 0, 0)); d.text((ox+3, oy), f"#{r['id']} {r['name']}", fill=(255, 255, 0), font=font)
            vis = []
            for t in T:
                dx, dy = t["x"]-r["px"], t["y"]-r["py"]; dist = math.hypot(dx, dy)
                if not 8 < dist < 75: continue
                da = (math.degrees(math.atan2(dx, dy))-r["h"]+180) % 360-180
                if abs(da) < 46: vis.append((dist, da, t))
            vis.sort(key=lambda v: v[0])
            for j, (dist, da, t) in enumerate(vis[:9]):
                xx = ox+W/2+math.tan(math.radians(da))/math.tan(math.radians(47.5))*W/2; yy = oy+30+(j % 6)*20
                d.text((xx-20, yy), f"{t['addr'].replace('strasse','str')} {t.get('floors') or ''}G {int(dist)}m", fill=(0, 255, 255), font=font, stroke_width=1, stroke_fill=(0, 0, 0))
        sh.save(ROOT/f"preview/z4n_labels_{k//9+1}.jpg", quality=82)
{"pick": pick, "shots": shots, "labels": labels}[sys.argv[1]]()
