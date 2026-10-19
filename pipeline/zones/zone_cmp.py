"""Photo | game comparison at the zone camera points: per camera point the best local photo from research/zones/zone<N>_photos.json
(daytime, recent, close), then a game view from the photo position and heading (player 4 m ahead so the chase camera sits near the photo point).
Output: preview/zone<N>_cmp_<tag>_<k>.jpg (9 pairs per sheet, photo left, game right) + preview/zone<N>_cmp_<tag>/picks.json.
Needs the dev server (web, port 5173). Usage: python pipeline/zones/zone_cmp.py <N> [tag]   (tag default 'after')"""
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from zones import wgs_to_local  # noqa: E402

N = int(sys.argv[1]); TAG = sys.argv[2] if len(sys.argv) > 2 else "after"
OUT = ROOT / "preview" / f"zone{N}_cmp_{TAG}"; OUT.mkdir(parents=True, exist_ok=True)
W, H = 400, 225


def usable(f):
    """Daylight street view, not a floor/feet shot: bright enough, upper half with structure (facades/sky edges), lower half not dominating."""
    im = Image.open(f).convert("L").resize((96, 64)); px = list(im.getdata())
    top, bot = px[:96 * 32], px[96 * 32:]
    mean = sum(px) / len(px)
    var = lambda a: sum((v - sum(a) / len(a)) ** 2 for v in a) / len(a)
    edges = sum(abs(px[i] - px[i + 1]) for i in range(96 * 32 - 1) if (i + 1) % 96) / (95 * 32)
    return mean > 75 and var(top) > 900 and edges > 6 and var(top) > 0.5 * var(bot)


def pick(photos):
    ok = [p for p in photos if not p.get("night") and p.get("heading") is not None and (ROOT / p["file"]).exists()]
    ok.sort(key=lambda p: abs((p.get("dist_m") or 50) - 20) + 6 * (2026 - (p.get("year") or 2015)))
    return next((p for p in ok if usable(ROOT / p["file"])), None)


def main():
    meta = json.load(open(ROOT / f"research/zones/zone{N}_photos.json"))
    picks, views = [], []
    for sid, s in meta.items():
        p = pick(s.get("photos", []))
        if p is None:
            picks.append(dict(site=sid, name=s["name"], photo=None)); continue
        x, y = wgs_to_local(p["lat"], p["lon"]); yaw = math.radians(p["heading"])
        gx, gy = x + 4 * math.sin(yaw), y + 4 * math.cos(yaw)
        out = str(OUT / f"{sid}.jpg")
        picks.append(dict(site=sid, name=s["name"], photo=p["file"], author=p.get("author"), license=p.get("license"), url=p.get("url"),
                          year=p.get("year"), x=round(gx, 1), y=round(gy, 1), yaw=round(yaw, 2), game=out))
        views.append(dict(x=round(gx, 1), y=round(gy, 1), yaw=round(yaw, 2), out=out))
    json.dump(picks, open(OUT / "picks.json", "w"), ensure_ascii=False, indent=1)
    vf = OUT / "views.json"; json.dump(views, open(vf, "w"))
    r = subprocess.run(["node", "tests/view_shots.mjs", str(vf)], cwd=ROOT / "web", capture_output=True, text=True)
    print(r.stdout.strip()[-200:], r.stderr.strip()[-300:])
    font = ImageFont.load_default(size=14)
    rows = [p for p in picks if p["photo"]]
    for k in range(0, len(rows), 9):
        part = rows[k:k + 9]
        sh = Image.new("RGB", (1600, ((len(part) + 1) // 2) * H), (34, 34, 34)); d = ImageDraw.Draw(sh)
        for i, p in enumerate(part):
            ox, oy = (i % 2) * 800, (i // 2) * H
            for j, f in enumerate((ROOT / p["photo"], Path(p["game"]))):
                if f.exists():
                    im = Image.open(f).convert("RGB"); im.thumbnail((W * 2, H * 2))
                    s_ = max(W / im.width, H / im.height); im = im.resize((int(im.width * s_) + 1, int(im.height * s_) + 1))
                    sh.paste(im.crop((0, 0, W, H)), (ox + j * W, oy))
            d.rectangle([ox, oy, ox + 260, oy + 18], fill=(0, 0, 0)); d.text((ox + 3, oy + 1), f"{p['name']} ({p['year']})", font=font, fill="white")
        f = ROOT / "preview" / f"zone{N}_cmp_{TAG}_{k // 9 + 1}.jpg"; sh.save(f, quality=78); print("sheet", f.relative_to(ROOT))
    print("no photo:", [p["name"] for p in picks if not p["photo"]])


if __name__ == "__main__":
    main()
