"""Langstrasse Sued photo round: frontal crops (shopfront + whole house) for hospitality/shops from Panoramax + Mapillary panoramas.
Reuses the API cache of shops_r2_fetch (data/raw/photos/shops_r2/_api). Output: data/raw/photos/langstrasse_b/<id>_<n>_{s,h}.jpg + research/shops_v3/photos_langB.json
(CC BY-SA 4.0 sources; only viewed for reading facade facts, never used as texture)."""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
import shops_r2_fetch as R

ROOT = R.ROOT; OUT = ROOT / "data/raw/photos/langstrasse_b"; OUT.mkdir(parents=True, exist_ok=True)
A = (913, -321); B = (705, -990)

def lat(e):
    ax, ay = B[0] - A[0], B[1] - A[1]; L = math.hypot(ax, ay)
    return ((e['x'] - A[0]) * ay - (e['y'] - A[1]) * ax) / L, ((e['x'] - A[0]) * ax + (e['y'] - A[1]) * ay) / L

def section():
    d = json.load(open(ROOT / "research/shops_v3/shops_v3.json"))
    return [e for e in d if (abs(lat(e)[0]) < 75 and 0 < lat(e)[1] < 720) or (e['area'] == 'Badenerstrasse' and e['x'] > 100)]

def crop(f, heading, az, fov, pitch, W=900, H=675):
    im = np.asarray(Image.open(f).convert("RGB")); h, w = im.shape[:2]
    if w > 6000:
        im = np.asarray(Image.fromarray(im).resize((6000, 3000))); h, w = im.shape[:2]
    fl = (W / 2) / math.tan(math.radians(fov / 2))
    xs, ys = np.meshgrid(np.arange(W) - W / 2 + .5, np.arange(H) - H / 2 + .5)
    p = math.radians(pitch)
    x3, y3, z3 = xs, -ys, np.full_like(xs, fl)
    y2 = y3 * math.cos(p) + z3 * math.sin(p); z2 = -y3 * math.sin(p) + z3 * math.cos(p)
    lon = np.arctan2(x3, z2) + math.radians(heading - az); la = np.arctan2(y2, np.hypot(x3, z2))
    u = ((lon / (2 * math.pi) + .5) % 1) * w; v = np.clip((.5 - la / math.pi) * h, 0, h - 2)
    u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int); fu = (u - u0)[..., None]; fv = (v - v0)[..., None]
    u0 %= w; u1 = (u0 + 1) % w
    o = im[v0, u0] * (1 - fu) * (1 - fv) + im[v0, u1] * fu * (1 - fv) + im[v0 + 1, u0] * (1 - fu) * fv + im[v0 + 1, u1] * fu * fv
    return Image.fromarray(o.astype(np.uint8))

def pick3(c, imgs):
    sc = []
    for im in imgs or []:
        if "CC-BY" not in im["license"].upper().replace("_", "-") and "CC0" not in im["license"].upper(): continue
        d, brg = R.hav(im["lat"], im["lon"], c["lat"], c["lon"])
        if d > 30 or d < 3 or im["az"] is None: continue
        diff = abs((brg - im["az"] + 180) % 360 - 180)
        if not im["pano"] and diff > 30: continue
        yr = int(im["date"][:4] or 2000)
        sc.append((abs(d - 11) / 10 + (0 if im["pano"] else diff / 25 + .3) + max(0, 2025 - yr) * .12, d, brg, diff, im))
    sc.sort(key=lambda t: t[0]); res = []
    for s, d, brg, diff, im in sc:
        if any(abs(r["dist"] - d) < 4 and abs(r["bearing"] - brg) < 15 for r in res): continue
        res.append(dict(im, dist=round(d, 1), bearing=round(brg), angle_diff=round(diff)))
        if len(res) == 3: break
    return res

def work(c, tok):
    imgs = (R.pmx(c) or []) + (R.mly(c, tok) or [])
    res = []
    for n, im in enumerate(pick3(c, imgs)):
        f = R.source(im)
        if f is None: continue
        s = OUT / f"{c['id']}_{n}_s.jpg"; h = OUT / f"{c['id']}_{n}_h.jpg"
        if im["pano"]:
            crop(f, im["bearing"], im["az"], 55, 3).save(s, quality=86)
            crop(f, im["bearing"], im["az"], 85, 22).save(h, quality=84)
        else:
            R.flat(f, (im['bearing'] - im['az'] + 180) % 360 - 180).save(s, quality=86); h = None
        res.append(dict(shop=str(s.relative_to(ROOT)), house=str(h.relative_to(ROOT)) if h else None, source=im["src"], pano=im["pano"], page=im["page"], date=im["date"],
                        creator=im["creator"], license=im["license"], dist_m=im["dist"]))
    return res

if __name__ == "__main__":
    from concurrent.futures import ThreadPoolExecutor
    cand = {c["id"]: c for c in json.load(open(ROOT / "research/shops_v3/candidates.json"))}
    S = [e for e in section() if e["id"] in cand]; tok = R.token()
    with ThreadPoolExecutor(5) as ex: out = list(ex.map(lambda e: (e["id"], work(cand[e["id"]], tok)), S))
    meta = dict(out)
    json.dump(meta, open(ROOT / "research/shops_v3/photos_langB.json", "w"), ensure_ascii=False, indent=0)
    print(len(S), "venues", sum(len(v) for v in meta.values()), "views", sum(1 for v in meta.values() if v))
