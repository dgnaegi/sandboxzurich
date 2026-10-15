"""Facade photos from Panoramax (CC BY-SA, mostly pedestrian 360 panos) + earlier shop photos (shops_r2) for GWR addresses.
Adds records to research/buildings/sheets_v3/candidates.json (same format as facades_fetch.py, plus 'src').
Usage: python facades_px.py [--max N] [--shops-only]. Resumable (skips addresses that already have an image)."""
import hashlib
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F  # noqa: E402
import shops_r2_fetch as R  # noqa: E402

ROOT = F.ROOT
D = ROOT / "research/buildings/sheets_v3"
RAW = ROOT / "data/raw/photos/facades"
CROPS = RAW / "crops"
API = RAW / "px_api"
CAND = D / "candidates.json"
API.mkdir(parents=True, exist_ok=True)
CROPS.mkdir(parents=True, exist_ok=True)


def px(lat, lon):
    key = f"{round(lat, 4)}_{round(lon, 4)}"
    cf = API / f"{key}.json"
    if cf.exists():
        return json.load(open(cf))
    c = dict(id=key, lat=lat, lon=lon)
    out = R.pmx(c)  # bbox +-30 m, cached under shops_r2/_api by id; re-cache here
    if out is not None:
        json.dump(out, open(cf, "w"))
    return out


def pick(t, imgs):
    lat, lon = F.local_ll(t["x"], t["y"])
    best = None
    for im in imgs or []:
        if "CC" not in (im.get("license") or "").upper() or im.get("az") is None:
            continue
        d, brg = R.hav(im["lat"], im["lon"], lat, lon)
        if d < 5 or d > 28:
            continue
        diff = abs((brg - im["az"] + 180) % 360 - 180)
        if not im["pano"] and diff > 28:
            continue
        yr = int((im.get("date") or "2000")[:4] or 2000)
        if yr < 2019:
            continue
        s = abs(d - 13) / 10 + (0 if im["pano"] else diff / 25 + .3) + max(0, 2025 - yr) * .15
        if best is None or s < best[0]:
            best = (s, d, brg, diff, im)
    return best


def work(t):
    try:
        lat, lon = F.local_ll(t["x"], t["y"])
        b = pick(t, px(lat, lon))
        if not b:
            return t["addr"], None
        _, d, brg, diff, im = b
        f = R.source(im)
        if f is None:
            return t["addr"], None
        if im["pano"]:
            c = R.crop(f, brg, im["az"], fov=75, W=640, H=640)
        else:
            c = R.flat(f, (brg - im["az"] + 180) % 360 - 180, hfov=75, W=640).crop((0, 0, 640, 480)).resize((640, 640))
        slug = t["addr"].replace(" ", "_").replace("/", "-")
        c.save(CROPS / f"{slug}.jpg", "JPEG", quality=85)
        return t["addr"], dict(id=im["id"], by=im["creator"], year=int(im["date"][:4]), d=round(d, 1), diff=round(diff), file=f"crops/{slug}.jpg", src="panoramax")
    except Exception as e:  # noqa: BLE001
        R.log("ERR", t["addr"], repr(e)[:80])
        return t["addr"], None


def shop_photos():
    """addr -> crop from shops_r2 photos (whole house often visible); only for addresses without image."""
    out = {}
    for v in json.load(open(ROOT / "research/shops_v3/photos_r2.json")).values():
        if v["photos"] and v.get("address"):
            a = v["address"].split(",")[0].strip()
            out.setdefault(a, v["photos"][0])
    return out


def main():
    T = json.load(open(D / "targets.json"))
    if "--streets" in sys.argv:   # comma list of street names (exact, as in targets.json)
        keep = set(sys.argv[sys.argv.index("--streets") + 1].split(","))
        T = [t for t in T if t["street"] in keep]
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10 ** 9
    cand = json.load(open(CAND))
    sp = shop_photos()
    n_shop = 0
    for t in T:
        if t["addr"] in sp and not (cand.get(t["addr"]) or {}).get("imgs"):
            p = sp[t["addr"]]
            im = Image.open(ROOT / p["file"]).convert("RGB")
            w, h = im.size
            s = min(w, h)
            c = im.crop((0, 0, s, s)).resize((640, 640))   # shop shot: keep the upper (facade) part, left-aligned square
            slug = t["addr"].replace(" ", "_")
            c.save(CROPS / f"{slug}_shop.jpg", "JPEG", quality=85)
            cand[t["addr"]] = dict(t, imgs=[dict(id=p["id"], by=p["creator"], year=int(p["date"][:4]), d=p["dist_m"], diff=p["angle_diff"],
                                                 file=f"crops/{slug}_shop.jpg", src=p["source"], shop=True)])
            n_shop += 1
    R.log("shop-photo candidates added:", n_shop)
    if "--shops-only" not in sys.argv:
        todo = [t for t in T if not (cand.get(t["addr"]) or {}).get("imgs")][:mx]
        R.log(len(todo), "to query on Panoramax")
        done = ok = 0
        with ThreadPoolExecutor(8) as ex:
            for addr, rec in ex.map(work, todo):
                done += 1
                if rec:
                    t = next(x for x in todo if x["addr"] == addr) if False else None
                    cand[addr] = dict(cand.get(addr) or {k: v for k, v in next(x for x in T if x["addr"] == addr).items()}, imgs=[rec])
                    ok += 1
                if done % 100 == 0:
                    R.log(done, "done,", ok, "with photo")
                    json.dump(cand, open(CAND, "w"), ensure_ascii=False)
        R.log("done", done, ok)
    json.dump(cand, open(CAND, "w"), ensure_ascii=False)


if __name__ == "__main__":
    main()
