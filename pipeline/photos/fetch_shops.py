"""Fetch 1-3 frontal street photos per shop/gastro venue from Mapillary (CC BY-SA 4.0).

Candidates: research/pois_kreis{3,4,5,9}_osm.csv (OSM POIs, local metres) inside data/build/playarea.json,
kinds restaurant/cafe/bar/pub/fast_food/bakery/shop=*. Addresses are joined from the curated
pois_kreis*.csv and gastro_match.csv where names match. Priority = distance to anchor streets/places.
Output: data/raw/photos/shops/<osm_id>_<n>.jpg, research/shops_v3/photos.json, candidates in research/shops_v3/candidates.json
Resumable (cache of API answers in data/raw/photos/shops/_api/). Usage: fetch_shops.py [--max N]
"""
import argparse, csv, json, math, os, re, sys, time
from pathlib import Path
import requests
from pyproj import Transformer
from shapely.geometry import Polygon, Point

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data/raw/photos/shops"
API_CACHE = OUT / "_api"
META = ROOT / "research/shops_v3/photos.json"
CAND = ROOT / "research/shops_v3/candidates.json"
ORIGIN = (2681400.0, 1248700.0)
to_wgs = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
KINDS_AMENITY = {"restaurant", "cafe", "bar", "pub", "fast_food", "ice_cream", "biergarten"}
SKIP_SHOP = {"hairdresser", "beauty", "massage", "car_repair", "car", "tattoo", "estate_agent", "travel_agency", "copyshop", "locksmith", "laundry", "dry_cleaning"}
# anchors (WGS lat, lon, weight radius m): higher priority first
ANCHORS = [
    ("Langstrasse", [(47.3772, 8.5262), (47.3788, 8.5290), (47.3800, 8.5312), (47.3760, 8.5238)], 120),
    ("Helvetiaplatz", [(47.3752, 8.5263)], 150),
    ("Baeckeranlage", [(47.3773, 8.5215)], 130),
    ("Josefstrasse", [(47.3874, 8.5152), (47.3860, 8.5200)], 120),
    ("Badenerstrasse", [(47.3733, 8.5167), (47.3745, 8.5200), (47.3765, 8.5148)], 100),
    ("Idaplatz", [(47.3712, 8.5195)], 130),
    ("Hohlstrasse", [(47.3765, 8.5230), (47.3772, 8.5180)], 90),
    ("Kalkbreite", [(47.3735, 8.5222)], 140),
    ("Lochergut", [(47.3737, 8.5240)], 140),
    ("Viadukt", [(47.3860, 8.5260), (47.3872, 8.5232)], 140),
    ("Europaallee", [(47.3778, 8.5340)], 160),
]
UA = {"User-Agent": "sandboxzurich/0.1 (research)"}


def log(m): print(time.strftime("%H:%M:%S"), m, flush=True)


def token():
    for l in open(ROOT / ".env"):
        if l.startswith("MAPILLARY_TOKEN="): return l.split("=", 1)[1].strip().strip('"\'')
    sys.exit("no token")


def hav(la1, lo1, la2, lo2):
    k = 111320.0
    dy = (la2 - la1) * k; dx = (lo2 - lo1) * k * math.cos(math.radians(la1))
    return math.hypot(dx, dy), (math.degrees(math.atan2(dx, dy)) + 360) % 360


def norm(s): return re.sub(r"[^a-z0-9]", "", s.lower())


def build_candidates():
    poly = Polygon(json.load(open(ROOT / "data/build/playarea.json"))["polygon"])
    addr = {}
    for f in ROOT.glob("research/pois_kreis?.csv"):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            if r.get("address"): addr[norm(r.get("new_name") or r["name"])] = r["address"]; addr.setdefault(norm(r["name"]), r["address"])
    for r in csv.DictReader(open(ROOT / "research/gastro_match.csv", encoding="utf-8")):
        if r.get("address"):
            for k in (r.get("osm_name"), r["name"]):
                if k: addr.setdefault(norm(k), r["address"])
    out, seen = [], set()
    for f in sorted(ROOT.glob("research/pois_kreis?_osm.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            try: x, y = float(r["x"]), float(r["y"])
            except (ValueError, KeyError, TypeError): continue
            if r["osm_id"] in seen or not r["name"].strip(): continue
            kind = r["kind"]; k, _, v = kind.partition("=")
            if not ((k == "amenity" and v in KINDS_AMENITY) or (k == "shop" and v not in SKIP_SHOP)): continue
            if not poly.contains(Point(x, y)): continue
            seen.add(r["osm_id"])
            lon, lat = to_wgs.transform(ORIGIN[0] + x, ORIGIN[1] + y)
            best, area = 1e9, ""
            for name, pts, rad in ANCHORS:
                d = min(hav(lat, lon, a, b)[0] for a, b in pts) - rad
                if d < best: best, area = d, name
            out.append(dict(id=r["osm_id"], name=r["name"], kind=kind, address=addr.get(norm(r["name"]), r.get("address", "")),
                            x=x, y=y, lat=lat, lon=lon, area=area if best < 60 else "", prio=best))
    out.sort(key=lambda c: (c["prio"] > 60, c["kind"].startswith("shop="), c["prio"]))
    return out


def query(c, tok):
    cf = API_CACHE / f"{c['id']}.json"
    if cf.exists(): return json.load(open(cf))
    dlat, dlon = 40 / 111320, 40 / (111320 * math.cos(math.radians(c["lat"])))
    p = dict(access_token=tok, fields="id,captured_at,compass_angle,geometry,thumb_1024_url,is_pano,creator", limit=300,
             bbox=f"{c['lon']-dlon:.6f},{c['lat']-dlat:.6f},{c['lon']+dlon:.6f},{c['lat']+dlat:.6f}")
    for i in range(4):
        try:
            r = requests.get("https://graph.mapillary.com/images", params=p, headers=UA, timeout=40)
            if r.status_code == 200:
                d = r.json().get("data", []); json.dump(d, open(cf, "w")); return d
            log(f"  HTTP {r.status_code} {r.text[:80]}")
        except requests.RequestException as e: log(f"  err {e}")
        time.sleep(5 * (i + 1))
    return None


def pick(c, imgs):
    sc = []
    for im in imgs:
        if im.get("is_pano") or "thumb_1024_url" not in im: continue
        lo, la = im["geometry"]["coordinates"]
        d, brg = hav(la, lo, c["lat"], c["lon"])
        diff = abs((brg - im["compass_angle"] + 180) % 360 - 180)
        if d > 26 or d < 4 or diff > 25: continue
        yr = int(time.strftime("%Y", time.gmtime(im["captured_at"] / 1000)))
        s = abs(d - 12) / 12 + diff / 25 + max(0, 2024 - yr) * 0.25
        sc.append((s, d, diff, yr, im))
    sc.sort(key=lambda t: t[0]); res = []
    for s, d, diff, yr, im in sc:
        if any(abs(r["dist"] - d) < 4 and abs(r["angle_diff"] - diff) < 8 for r in res): continue
        res.append(dict(mapillary_id=im["id"], dist=round(d, 1), angle_diff=round(diff), year=yr, creator=(im.get("creator") or {}).get("username", ""), url=im["thumb_1024_url"], score=round(s, 2)))
        if len(res) == 3: break
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--max", type=int, default=900); a = ap.parse_args()
    API_CACHE.mkdir(parents=True, exist_ok=True); tok = token()
    cands = build_candidates()[: a.max]
    json.dump(cands, open(CAND, "w"), ensure_ascii=False, indent=0)
    log(f"{len(cands)} candidates")
    meta = json.load(open(META)) if META.exists() else {}
    from concurrent.futures import ThreadPoolExecutor

    def work(c):
        imgs = query(c, tok)
        if imgs is None: return c, None
        files = []
        for n, p in enumerate(pick(c, imgs)):
            fn = OUT / f"{c['id']}_{n}.jpg"
            if not fn.exists():
                try:
                    r = requests.get(p["url"], headers=UA, timeout=40); r.raise_for_status(); fn.write_bytes(r.content)
                except requests.RequestException as e: log(f"  dl err {e}"); continue
            q = {k: v for k, v in p.items() if k != "url"}
            q.update(file=str(fn.relative_to(ROOT)), license="CC-BY-SA-4.0", source="mapillary",
                     page=f"https://www.mapillary.com/app/?pKey={p['mapillary_id']}")
            files.append(q)
        return c, files

    todo = [c for c in cands if c["id"] not in meta]
    with ThreadPoolExecutor(6) as ex:
        for i, (c, files) in enumerate(ex.map(work, todo)):
            if files is None: continue
            meta[c["id"]] = dict(name=c["name"], address=c["address"], photos=files)
            if i % 25 == 0:
                json.dump(meta, open(META, "w"), ensure_ascii=False, indent=1); log(f"{i}/{len(todo)} with photos: {sum(1 for m in meta.values() if m['photos'])}")
    json.dump(meta, open(META, "w"), ensure_ascii=False, indent=1)
    log(f"done: {sum(1 for m in meta.values() if m['photos'])}/{len(meta)} with photos")


if __name__ == "__main__": main()
