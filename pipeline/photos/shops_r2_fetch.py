"""Round 2 shop photos: Panoramax + Mapillary panoramas (equirectangular -> perspective crop towards the venue).
Reads research/shops_v3/candidates.json. Cache: data/raw/photos/shops_r2/ (_api, _src originals, <id>_<n>.jpg crops).
Writes research/shops_v3/photos_r2.json. Resumable. Usage: shops_r2_fetch.py [--max N]"""
import json, math, sys, time, hashlib, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data/raw/photos/shops_r2"; API = OUT / "_api"; SRC = OUT / "_src"
for d in (API, SRC): d.mkdir(parents=True, exist_ok=True)
CAND = ROOT / "research/shops_v3/candidates.json"; META = ROOT / "research/shops_v3/photos_r2.json"
UA = {"User-Agent": "sandboxzurich-research/1.0 (daniel.gnaegi@outlook.com)"}
lock = threading.Lock()

def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)
def token():
    for l in open(ROOT / ".env"):
        if l.startswith("MAPILLARY_TOKEN="): return l.split("=", 1)[1].strip().strip('"\'')
def hav(la1, lo1, la2, lo2):
    dy = (la2 - la1) * 111320; dx = (lo2 - lo1) * 111320 * math.cos(math.radians(la1))
    return math.hypot(dx, dy), math.degrees(math.atan2(dx, dy)) % 360
def get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=60, **kw)
            if r.status_code == 200: return r
            if r.status_code in (404, 403): return None
        except requests.RequestException: pass
        time.sleep(3 * (i + 1))

def pmx(c):
    cf = API / f"px_{c['id']}.json"
    if cf.exists(): return json.load(open(cf))
    dl, dn = 30 / 111320, 30 / (111320 * math.cos(math.radians(c["lat"])))
    r = get("https://api.panoramax.xyz/api/search", params=dict(bbox=f"{c['lon']-dn:.6f},{c['lat']-dl:.6f},{c['lon']+dn:.6f},{c['lat']+dl:.6f}", limit=100))
    if r is None: return None
    out = []
    for f in r.json().get("features", []):
        p = f["properties"]; io = p.get("pers:interior_orientation") or {}
        fov = io.get("field_of_view") or 0
        pano = fov >= 300 or "360" in (io.get("camera_model") or "") or (f["assets"]["sd"]["href"] and False)
        out.append(dict(src="panoramax", id=f["id"], lon=f["geometry"]["coordinates"][0], lat=f["geometry"]["coordinates"][1],
                        az=p.get("view:azimuth"), pano=pano, date=p.get("datetime", "")[:10], creator=(f.get("providers") or [{}])[0].get("name", ""),
                        license=p.get("license", ""), url=f["assets"]["sd"]["href"], hd=f["assets"].get("hd", {}).get("href"),
                        cam=io.get("camera_model", ""), page=f"https://api.panoramax.xyz/api/collections/{f['collection']}/items/{f['id']}"))
    json.dump(out, open(cf, "w")); return out

def mly(c, tok):
    cf = API / f"ml_{c['id']}.json"
    if cf.exists(): return json.load(open(cf))
    dl, dn = 30 / 111320, 30 / (111320 * math.cos(math.radians(c["lat"])))
    r = get("https://graph.mapillary.com/images", params=dict(access_token=tok, fields="id,captured_at,compass_angle,computed_compass_angle,geometry,thumb_2048_url,is_pano,creator", limit=300,
            bbox=f"{c['lon']-dn:.6f},{c['lat']-dl:.6f},{c['lon']+dn:.6f},{c['lat']+dl:.6f}"))
    if r is None: return None
    out = []
    for im in r.json().get("data", []):
        if not im.get("is_pano") or "thumb_2048_url" not in im: continue
        lo, la = im["geometry"]["coordinates"]
        out.append(dict(src="mapillary", id=im["id"], lon=lo, lat=la, az=im.get("computed_compass_angle", im.get("compass_angle")), pano=True,
                        date=time.strftime("%Y-%m-%d", time.gmtime(im["captured_at"] / 1000)), creator=(im.get("creator") or {}).get("username", ""),
                        license="CC-BY-SA-4.0", url=im["thumb_2048_url"], hd=None, cam="", page=f"https://www.mapillary.com/app/?pKey={im['id']}"))
    json.dump(out, open(cf, "w")); return out

def pick(c, imgs):
    sc = []
    for im in imgs or []:
        if "CC-BY" not in im["license"].upper().replace("_", "-") and "CC0" not in im["license"].upper(): continue
        d, brg = hav(im["lat"], im["lon"], c["lat"], c["lon"])
        if d > 25 or d < 2.5: continue
        if im["az"] is None: continue
        diff = abs((brg - im["az"] + 180) % 360 - 180)
        if not im["pano"] and diff > 30: continue
        yr = int(im["date"][:4] or 2000)
        s = abs(d - 10) / 10 + (0 if im["pano"] else diff / 25) + max(0, 2025 - yr) * 0.15 + (0 if im["pano"] else 0.3)
        sc.append((s, d, brg, diff, im))
    sc.sort(key=lambda t: t[0]); res = []
    for s, d, brg, diff, im in sc:
        if any(abs(r["dist"] - d) < 3 and abs(r["bearing"] - brg) < 12 for r in res): continue
        res.append(dict(im, dist=round(d, 1), bearing=round(brg), angle_diff=round(diff))); 
        if len(res) == 2: break
    return res

def source(im):
    f = SRC / (hashlib.md5(im["id"].encode()).hexdigest() + ".jpg")
    if not f.exists():
        r = get(im["hd"] if (im["pano"] and im["src"] == "panoramax" and im.get("hd")) else im["url"])
        if r is None: return None
        f.write_bytes(r.content)
    return f

def crop(f, heading, az, fov=60, W=1024, H=768):
    im = np.asarray(Image.open(f).convert("RGB")); h, w = im.shape[:2]
    if w > 6000:
        im = np.asarray(Image.fromarray(im).resize((6000, 3000))); h, w = im.shape[:2]
    fl = (W / 2) / math.tan(math.radians(fov / 2))
    xs, ys = np.meshgrid(np.arange(W) - W / 2 + .5, np.arange(H) - H / 2 + .5)
    dx, dy, dz = xs, -ys, np.full_like(xs, fl)   # camera frame: z forward
    lon = np.arctan2(dx, dz) + math.radians((heading - az))
    lat = np.arctan2(dy, np.hypot(dx, dz))
    u = ((lon / (2 * math.pi) + .5) % 1) * w; v = (.5 - lat / math.pi) * h
    u0 = np.floor(u).astype(int); v0 = np.clip(np.floor(v).astype(int), 0, h - 2); fu = (u - u0)[..., None]; fv = (v - v0)[..., None]
    u0 %= w; u1 = (u0 + 1) % w
    out = (im[v0, u0] * (1 - fu) * (1 - fv) + im[v0, u1] * fu * (1 - fv) + im[v0 + 1, u0] * (1 - fu) * fv + im[v0 + 1, u1] * fu * fv)
    return Image.fromarray(out.astype(np.uint8))

def flat(f, W=1024):
    im = Image.open(f).convert("RGB"); im.thumbnail((W, W)); return im

def work(c, tok, meta):
    try:
        imgs = (pmx(c) or []) + (mly(c, tok) or [])
        sel = pick(c, imgs); res = []
        for n, im in enumerate(sel):
            f = source(im)
            if f is None: continue
            out = OUT / f"{c['id']}_{n}.jpg"
            if not out.exists():
                (crop(f, im["bearing"], im["az"]) if im["pano"] else flat(f)).save(out, quality=88)
            res.append(dict(file=str(out.relative_to(ROOT)), source=im["src"], pano=im["pano"], id=im["id"], page=im["page"], date=im["date"],
                            creator=im["creator"], license=im["license"], dist_m=im["dist"], bearing=im["bearing"], angle_diff=im["angle_diff"]))
        with lock: meta[c["id"]] = dict(name=c["name"], address=c["address"], kind=c["kind"], area=c["area"], x=c["x"], y=c["y"], photos=res)
    except Exception as e: log("ERR", c["id"], repr(e)[:100])

if __name__ == "__main__":
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9
    cands = json.load(open(CAND))[:mx]; tok = token()
    meta = json.load(open(META)) if META.exists() else {}
    todo = [c for c in cands if c["id"] not in meta]
    log(len(todo), "to do")
    done = 0
    with ThreadPoolExecutor(6) as ex:
        for _ in ex.map(lambda c: work(c, tok, meta), todo):
            done += 1
            if done % 50 == 0:
                log(done, "done,", sum(1 for v in meta.values() if v["photos"]), "with photos"); json.dump(meta, open(META, "w"), ensure_ascii=False)
    json.dump(meta, open(META, "w"), ensure_ascii=False, indent=0)
    log("FINISHED", len(meta), sum(1 for v in meta.values() if v["photos"]))
