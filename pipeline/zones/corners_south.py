"""Zone 4 south corner check: pick photos, render game views at photo position (needs dev server :5173), make Foto|Spiel sheets preview/z4s_corner_<k>.jpg.
Usage: python pipeline/zones/corners_south.py pick | shoot | sheets"""
import json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "preview" / "z4s_corner_shots"; OUT.mkdir(parents=True, exist_ok=True)
CF = ROOT / "research/zones/z4/corners_south_picks.json"
W, H = 400, 225


def usable(f):
    im = Image.open(f).convert("L").resize((96, 64)); px = list(im.getdata())
    top, bot = px[:96 * 32], px[96 * 32:]
    mean = sum(px) / len(px)
    var = lambda a: sum((v - sum(a) / len(a)) ** 2 for v in a) / len(a)
    edges = sum(abs(px[i] - px[i + 1]) for i in range(96 * 32 - 1) if (i + 1) % 96) / (95 * 32)
    return mean > 75 and var(top) > 900 and edges > 6 and var(top) > 0.5 * var(bot)


def pick():
    c = json.load(open(ROOT / "research/zones/z4/corners_south_cands.json"))
    c = [p for p in c if not (p["near"] == "Birmensdorferstr" and (p["x"] < -700 or p["y"] < -2250 or p["y"] > -900))]
    c.sort(key=lambda p: -(p.get("year") or 2000))
    cells, out = {}, []
    for p in c:
        k = (round(p["x"] / 45), round(p["y"] / 45), int(((p["h"] + 45) % 360) // 90))
        if k in cells: continue
        try:
            if not usable(ROOT / p["file"]): continue
        except Exception: continue
        if sum(1 for q in out if q['near'] == p['near']) >= 7: continue
        cells[k] = 1; out.append(p)
    out.sort(key=lambda p: (p["near"], p["x"], p["y"]))
    for i, p in enumerate(out):
        yaw = math.radians(p["h"])
        p.update(id=i, gx=round(p["x"] + 4 * math.sin(yaw), 1), gy=round(p["y"] + 4 * math.cos(yaw), 1), yaw=round(yaw, 2), game=str(OUT / f"c{i:03d}.jpg"))
    json.dump(out, open(CF, "w"), indent=0, ensure_ascii=False)
    from collections import Counter
    print(len(out), Counter(p["near"] for p in out))


def shoot(lo=0, hi=999):
    ps = json.load(open(CF))[lo:hi]
    vf = OUT / "views.json"
    json.dump([dict(x=p["gx"], y=p["gy"], yaw=p["yaw"], out=p["game"]) for p in ps], open(vf, "w"))
    r = subprocess.run(["node", "tests/view_shots.mjs", str(vf)], cwd=ROOT / "web", capture_output=True, text=True)
    print(r.stdout.strip()[-200:], r.stderr.strip()[-300:])


def sheets(ids=None, per=8, tag="a"):
    ps = json.load(open(CF))
    if ids is not None: ps = [p for p in ps if p["id"] in ids]
    font = ImageFont.load_default(size=14)
    for k in range(0, len(ps), per):
        part = ps[k:k + per]
        sh = Image.new("RGB", (1600, ((len(part) + 1) // 2) * H), (34, 34, 34)); d = ImageDraw.Draw(sh)
        for i, p in enumerate(part):
            ox, oy = (i % 2) * 800, (i // 2) * H
            for j, f in enumerate((ROOT / p["file"], Path(p["game"]))):
                if f.exists():
                    im = Image.open(f).convert("RGB"); im.thumbnail((W * 2, H * 2))
                    s_ = max(W / im.width, H / im.height); im = im.resize((int(im.width * s_) + 1, int(im.height * s_) + 1))
                    sh.paste(im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H)), (ox + j * W, oy))
            d.rectangle([ox, oy, ox + 330, oy + 18], fill=(0, 0, 0)); d.text((ox + 3, oy + 1), f"#{p['id']} {p['near'][:14]} ({p['x']:.0f},{p['y']:.0f}) h{p['h']:.0f}", font=font, fill="white")
        f = ROOT / "preview" / f"z4s_corner_{tag}{k // per + 1}.jpg"; sh.save(f, quality=76); print(f.name)


def inview(lo, hi):
    """Houses (research/zones/z4/targets.json) in the photo's view cone with current note summary: for hand comparison."""
    G = json.load(open(ROOT / "data/build/gwr_kreise.json"))
    T = [dict(addr=f"{g['street']} {g['nr']}", x=g["x"], y=g["y"], floors=g["floors"]) for g in G if -700 < g["x"] < 700 and -2300 < g["y"] < -850]
    N = json.load(open(ROOT / "research/buildings/visual_notes_v3.json"))
    ps = json.load(open(CF))
    for p in ps[lo:hi]:
        yaw = math.radians(p["h"]); rows = []
        for t in T:
            dx, dy = t["x"] - p["x"], t["y"] - p["y"]; d = math.hypot(dx, dy)
            if not 5 < d < 65: continue
            a = (math.degrees(math.atan2(dx, dy)) - p["h"] + 540) % 360 - 180
            if abs(a) > 42: continue
            n = N.get(t["addr"], {})
            rows.append((d, f"{t['addr']} {int(a):+d}° {int(d)}m {n.get('hex','-')} g{n.get('geschosse','-')}/{t.get('floors')} {n.get('dach','')[:3]} {n.get('stil','')[:4]}"))
        rows.sort()
        print(f"#{p['id']} {p['streets']}: " + " | ".join(r[1] for r in rows[:7]))


if __name__ == "__main__":
    a = sys.argv[1]
    if a == "pick": pick()
    elif a == "shoot": shoot(*(int(v) for v in sys.argv[2:4]))
    elif a == "view": inview(int(sys.argv[2]), int(sys.argv[3]))
    elif a == "sheets": sheets(tag=sys.argv[2] if len(sys.argv) > 2 else "a")
