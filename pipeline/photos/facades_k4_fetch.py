"""Kreis 4 facade photos: per target address best frontal view (Panoramax pano/flat + Mapillary pano), crop 60deg towards the house.
Reads research/buildings/k4/targets.json; cache data/raw/photos/facades/k4/ (_api, _src, crops <n>.jpg); writes research/buildings/k4/photos.json.
Resumable. Usage: python facades_k4_fetch.py [--max N]"""
import json, math, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import shops_r2_fetch as R

ROOT = R.ROOT
OUT = ROOT / "data/raw/photos/facades/k4"; API = OUT / "_api"; SRC = OUT / "_src"; CR = OUT / "crops"
for d in (API, SRC, CR): d.mkdir(parents=True, exist_ok=True)
R.API, R.SRC = API, SRC
META = ROOT / "research/buildings/k4/photos.json"

def crop_p(f, heading, az, fov=66, W=800, H=600, pitch=14):
    """Equirect -> perspective with upward pitch (houses are tall)."""
    import numpy as np
    from PIL import Image
    im = np.asarray(Image.open(f).convert("RGB")); h, w = im.shape[:2]
    if w > 6000:
        im = np.asarray(Image.fromarray(im).resize((6000, 3000))); h, w = im.shape[:2]
    fl = (W / 2) / math.tan(math.radians(fov / 2))
    xs, ys = np.meshgrid(np.arange(W) - W / 2 + .5, np.arange(H) - H / 2 + .5)
    dx, dy, dz = xs, -ys, np.full_like(xs, fl)
    p = math.radians(pitch); dy2 = dy * math.cos(p) + dz * math.sin(p); dz2 = dz * math.cos(p) - dy * math.sin(p)
    lon = np.arctan2(dx, dz2) + math.radians(heading - az); lat = np.arctan2(dy2, np.hypot(dx, dz2))
    u = ((lon / (2 * math.pi) + .5) % 1) * w; v = np.clip((.5 - lat / math.pi) * h, 0, h - 2)
    u0 = np.floor(u).astype(int) % w; v0 = np.floor(v).astype(int)
    return Image.fromarray(im[v0, u0])

DMAX, DIFF, OBL = (40, 40, 75) if "--relax" in sys.argv else (28, 28, 55)

def pick(t, imgs):
    sdir = t.get("sdir")
    sc = []
    for im in imgs or []:
        if "CC-BY" not in im["license"].upper().replace("_", "-") and "CC0" not in im["license"].upper(): continue
        d, brg = R.hav(im["lat"], im["lon"], t["lat"], t["lon"])
        if d > DMAX or d < 4: continue
        if im["az"] is None: continue
        diff = abs((brg - im["az"] + 180) % 360 - 180)
        if not im["pano"] and diff > DIFF: continue
        obl = 0
        if sdir is not None:   # angle between sight line and facade normal (street axis + 90)
            obl = abs(90 - ((brg - sdir) % 180))
        if obl > OBL: continue
        yr = int(im["date"][:4] or 2000)
        s = abs(d - 14) / 10 + obl / 30 + (0 if im["pano"] else diff / 25 + 0.2) + max(0, 2025 - yr) * 0.1
        sc.append((s, d, brg, diff, im))
    sc.sort(key=lambda x: x[0]); res = []
    for s, d, brg, diff, im in sc:
        if any(abs(r["dist"] - d) < 4 and abs(r["bearing"] - brg) < 15 for r in res): continue
        res.append(dict(im, dist=round(d, 1), bearing=round(brg), angle_diff=round(diff)))
        if len(res) == 2: break
    return res

def work(i, t, tok, meta):
    try:
        c = dict(id=f"{i}", lat=t["lat"], lon=t["lon"])
        imgs = (R.pmx(c) or []) + (R.mly(c, tok) or [])
        sel = pick(t, imgs); res = []
        for n, im in enumerate(sel):
            f = R.source(im)
            if f is None: continue
            out = CR / f"{i}_{n}.jpg"
            if not out.exists() or (RECROP and im["pano"]):
                (crop_p(f, im["bearing"], im["az"]) if im["pano"] else R.flat(f, (im['bearing'] - im['az'] + 180) % 360 - 180, W=800)).save(out, quality=86)
            res.append(dict(file=str(out.relative_to(ROOT)), source=im["src"], pano=im["pano"], id=im["id"], date=im["date"], creator=im["creator"],
                            license=im["license"], dist_m=im["dist"], bearing=im["bearing"], angle_diff=im["angle_diff"]))
        meta[t["addr"]] = dict(i=i, photos=res)
    except Exception as e: R.log("ERR", t["addr"], repr(e)[:100])

RECROP = "--recrop" in sys.argv
if __name__ == "__main__":
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9
    T = json.load(open(ROOT / "research/buildings/k4/targets.json"))
    meta = json.load(open(META)) if META.exists() else {}
    tok = R.token()
    todo = [(i, t) for i, t in enumerate(T) if t["addr"] not in meta or RECROP or ("--relax" in sys.argv and not meta[t["addr"]]["photos"])][:mx]
    R.log(len(todo), "to do"); n = 0
    with ThreadPoolExecutor(6) as ex:
        for _ in ex.map(lambda it: work(it[0], it[1], tok, meta), todo):
            n += 1
            if n % 50 == 0:
                json.dump(dict(list(meta.items())), open(META, "w"), ensure_ascii=False); R.log(n, "done,", sum(1 for m in meta.values() if m["photos"]), "with photos")
    json.dump(dict(list(meta.items())), open(META, "w"), ensure_ascii=False); R.log("finished", len(meta))
