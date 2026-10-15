"""Round 3 shop photos for venues still not photo_ok. New vs R2:
 - candidates within 40 m (Panoramax bbox +-40 m, Mapillary flat AND 360 with camera_type/make/model/sequence),
 - images already viewed in R1/R2 are excluded,
 - facade normal from OSM building footprints: ray camera->venue is intersected with the building outline, obliquity = angle
   between the ray and the edge normal; 360 crops are centred on the venue/facade hit point, FOV 40-60 by distance,
 - pedestrian/hand cameras (sequence speed < 2.5 m/s, 360 handhelds) preferred over dashcams,
 - Wikimedia Commons geosearch (<=50 m) stored as extra candidates (photos_r3.json -> commons).
Cache: data/raw/photos/shops_r3/ (_api, crops <id>_<n>.jpg; originals shared via shops_r2/_src). Writes research/shops_v3/photos_r3.json.
Usage: shops_r3_fetch.py [--max N]"""
import json, math, sys, time, hashlib, threading, collections
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, requests
sys.path.insert(0, str(Path(__file__).resolve().parent))
import shops_r2_fetch as R2
from shops_r2_fetch import get, hav, token, crop, flat, log, ROOT

OUT = ROOT / "data/raw/photos/shops_r3"; API = OUT / "_api"; API.mkdir(parents=True, exist_ok=True)
D = ROOT / "research/shops_v3"; META = D / "photos_r3.json"
R2.SRC.mkdir(parents=True, exist_ok=True)
lock = threading.Lock()
X0, Y0 = 2681400, 1248700

# ---------- OSM building outlines (local metres relative to the venue's lat/lon) ----------
def load_buildings():
    d = json.load(open(ROOT / "data/raw/osm/part_buildings_r.json"))["elements"]
    nodes = {e["id"]: (e["lat"], e["lon"]) for e in d if e["type"] == "node"}
    polys = []
    for e in d:
        if e["type"] == "way" and (e.get("tags") or {}).get("building") and len(e["nodes"]) > 3 and all(n in nodes for n in e["nodes"]):
            pts = np.array([nodes[n] for n in e["nodes"]]); polys.append(pts)
    lats = np.array([p[:, 0].mean() for p in polys]); lons = np.array([p[:, 1].mean() for p in polys])
    return polys, lats, lons

def to_xy(pts, lat0, lon0):
    return np.stack([(pts[:, 1] - lon0) * 111320 * math.cos(math.radians(lat0)), (pts[:, 0] - lat0) * 111320], 1)

def facade_hit(c, cam_lat, cam_lon, B):
    """Return (hit_bearing_from_cam, hit_dist, obliquity_deg) of ray camera->venue vs nearest building outline; None if no outline near."""
    polys, lats, lons = B
    near = np.where((np.abs(lats - c["lat"]) < 60 / 111320) & (np.abs(lons - c["lon"]) < 60 / (111320 * math.cos(math.radians(c["lat"])))))[0]
    cam = to_xy(np.array([[cam_lat, cam_lon]]), c["lat"], c["lon"])[0]; v = np.zeros(2)
    best = None
    for i in near:
        p = to_xy(polys[i], c["lat"], c["lon"])
        # does the building contain / lie within 8 m of the venue?
        dmin = 1e9
        for a, b in zip(p[:-1], p[1:]):
            ab = b - a; t = max(0, min(1, np.dot(v - a, ab) / (ab @ ab + 1e-9))); dmin = min(dmin, np.linalg.norm(a + t * ab - v))
        if dmin > 8: continue
        d = v - cam; L = np.linalg.norm(d); d = d / L
        for a, b in zip(p[:-1], p[1:]):
            e = b - a; den = d[0] * e[1] - d[1] * e[0]
            if abs(den) < 1e-9: continue
            w = a - cam; t = (w[0] * e[1] - w[1] * e[0]) / den; s = (w[0] * d[1] - w[1] * d[0]) / den
            if 0 <= s <= 1 and t > 0:
                if best is None or t < best[0]:
                    n = np.array([e[1], -e[0]]); n = n / np.linalg.norm(n)
                    obl = math.degrees(math.acos(min(1, abs(np.dot(n, d)))))
                    best = (t, obl, cam + d * t)
    if best is None: return None
    t, obl, hit = best; vec = hit - cam
    return math.degrees(math.atan2(vec[0], vec[1])) % 360, t, obl

# ---------- API ----------
def pmx(c):
    cf = API / f"px_{c['id']}.json"
    if cf.exists(): return json.load(open(cf))
    dl, dn = 40 / 111320, 40 / (111320 * math.cos(math.radians(c["lat"])))
    r = get("https://api.panoramax.xyz/api/search", params=dict(bbox=f"{c['lon']-dn:.6f},{c['lat']-dl:.6f},{c['lon']+dn:.6f},{c['lat']+dl:.6f}", limit=200))
    if r is None: return None
    out = []
    for f in r.json().get("features", []):
        p = f["properties"]; io = p.get("pers:interior_orientation") or {}
        fov = io.get("field_of_view") or 0
        pano = fov >= 300 or "360" in (io.get("camera_model") or "")
        out.append(dict(src="panoramax", id=f["id"], lon=f["geometry"]["coordinates"][0], lat=f["geometry"]["coordinates"][1],
                        az=p.get("view:azimuth"), pano=pano, date=p.get("datetime", "")[:10], t=p.get("datetime", ""), seq=f.get("collection"),
                        creator=(f.get("providers") or [{}])[0].get("name", ""), license=p.get("license", ""),
                        url=f["assets"]["sd"]["href"], hd=f["assets"].get("hd", {}).get("href"), cam=io.get("camera_model", ""),
                        page=f"https://api.panoramax.xyz/api/collections/{f['collection']}/items/{f['id']}"))
    json.dump(out, open(cf, "w")); return out

def mly(c, tok):
    cf = API / f"ml_{c['id']}.json"
    if cf.exists(): return json.load(open(cf))
    dl, dn = 40 / 111320, 40 / (111320 * math.cos(math.radians(c["lat"])))
    r = get("https://graph.mapillary.com/images", params=dict(access_token=tok, limit=400,
            fields="id,captured_at,compass_angle,computed_compass_angle,geometry,thumb_2048_url,is_pano,creator,camera_type,make,model,sequence",
            bbox=f"{c['lon']-dn:.6f},{c['lat']-dl:.6f},{c['lon']+dn:.6f},{c['lat']+dl:.6f}"))
    if r is None: return None
    raw = r.json().get("data", []); sp = {}
    seqs = collections.defaultdict(list)
    for im in raw: seqs[im.get("sequence")].append(im)
    for s, L in seqs.items():
        L.sort(key=lambda i: i["captured_at"])
        for a, b in zip(L, L[1:]):
            dt = (b["captured_at"] - a["captured_at"]) / 1000
            if dt > 0:
                d, _ = hav(a["geometry"]["coordinates"][1], a["geometry"]["coordinates"][0], b["geometry"]["coordinates"][1], b["geometry"]["coordinates"][0])
                sp.setdefault(a["id"], d / dt); sp.setdefault(b["id"], d / dt)
    out = []
    for im in raw:
        if "thumb_2048_url" not in im: continue
        lo, la = im["geometry"]["coordinates"]
        out.append(dict(src="mapillary", id=im["id"], lon=lo, lat=la, az=im.get("computed_compass_angle", im.get("compass_angle")), pano=bool(im.get("is_pano")),
                        date=time.strftime("%Y-%m-%d", time.gmtime(im["captured_at"] / 1000)), seq=im.get("sequence"), speed=sp.get(im["id"]),
                        creator=(im.get("creator") or {}).get("username", ""), license="CC-BY-SA-4.0", url=im["thumb_2048_url"], hd=None,
                        cam=f"{im.get('camera_type','')} {im.get('make','')} {im.get('model','')}".strip(), page=f"https://www.mapillary.com/app/?pKey={im['id']}"))
    json.dump(out, open(cf, "w")); return out

def commons(c):
    cf = API / f"cm_{c['id']}.json"
    if cf.exists(): return json.load(open(cf))
    r = get("https://commons.wikimedia.org/w/api.php", params=dict(action="query", format="json", generator="geosearch", ggscoord=f"{c['lat']}|{c['lon']}",
            ggsradius=50, ggsnamespace=6, ggslimit=10, prop="imageinfo|coordinates", iiprop="url|extmetadata", iiurlwidth=1280))
    out = []
    if r is not None:
        for p in (r.json().get("query") or {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {}); co = (p.get("coordinates") or [{}])[0]
            out.append(dict(title=p["title"], url=ii.get("thumburl"), page=ii.get("descriptionurl"), license=md.get("LicenseShortName", {}).get("value", ""),
                            creator=md.get("Artist", {}).get("value", "")[:80], date=md.get("DateTimeOriginal", {}).get("value", "")[:10],
                            lat=co.get("lat"), lon=co.get("lon")))
    json.dump(out, open(cf, "w")); return out

# ---------- selection ----------
def used_ids():
    u = set()
    for k, v in json.load(open(D / "photos.json")).items():
        for p in v["photos"]: u.add(str(p["mapillary_id"]))
    for k, v in json.load(open(D / "photos_r2.json")).items():
        for p in v["photos"]: u.add(str(p["id"]))
    return u

def pick(c, imgs, B, used):
    sc = []
    for im in imgs or []:
        if str(im["id"]) in used or im["az"] is None: continue
        lic = im["license"].upper().replace("_", "-")
        if "CC-BY" not in lic and "CC0" not in lic: continue
        d, brg = hav(im["lat"], im["lon"], c["lat"], c["lon"])
        if d > 40 or d < 2.5: continue
        diff = abs((brg - im["az"] + 180) % 360 - 180)
        if not im["pano"] and diff > 28: continue
        fh = facade_hit(c, im["lat"], im["lon"], B)
        hb, hd, obl = fh if fh else (brg, d, 45.0)
        if obl > 62: continue
        yr = int(im["date"][:4] or 2000)
        walker = (im.get("speed") is not None and im["speed"] < 2.5) or (im["pano"] and im["src"] == "mapillary" and (im.get("speed") or 9) < 4)
        s = obl / 25 + abs(d - 9) / 12 + (0 if im["pano"] else diff / 20 + 0.3) + max(0, 2025 - yr) * 0.12 - (0.5 if walker else 0)
        sc.append((s, d, hb, diff, obl, im))
    sc.sort(key=lambda t: t[0]); res = []
    for s, d, hb, diff, obl, im in sc:
        if any(abs(r["dist"] - d) < 3 and abs(r["bearing"] - hb) < 12 for r in res): continue
        res.append(dict(im, dist=round(d, 1), bearing=round(hb), angle_diff=round(diff), obliq=round(obl), score=round(s, 2)))
        if len(res) == 2: break
    return res

def source(im):
    f = R2.SRC / (hashlib.md5(im["id"].encode()).hexdigest() + ".jpg")
    if not f.exists():
        r = get(im["hd"] if (im["src"] == "panoramax" and im.get("hd")) else im["url"])
        if r is None: return None
        f.write_bytes(r.content)
    return f

def flat3(f, rel, dist, W=1024):
    """Flat camera: 4:3 window centred on the venue direction; narrower when far (hfov 100 assumed)."""
    im = R2.Image.open(f).convert("RGB"); w, h = im.size
    cx = w / 2 + (w / 2) * math.tan(math.radians(max(-45, min(45, rel)))) / math.tan(math.radians(50))
    cw = w * (0.38 if dist > 20 else 0.5); ch = cw * 0.75
    x0 = min(max(cx - cw / 2, 0), w - cw); y0 = min(max(h * 0.45 - ch / 2, 0), h - ch)
    return im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, int(W * 0.75)), R2.Image.LANCZOS)

def work(c, tok, meta, B, used, ok):
    try:
        imgs = (pmx(c) or []) + (mly(c, tok) or []); cm = commons(c)
        sel = pick(c, imgs, B, used); res = []
        for n, im in enumerate(sel):
            f = source(im)
            if f is None: continue
            out = OUT / f"{c['id']}_{n}.jpg"
            if not out.exists():
                if im["pano"]: crop(f, im["bearing"], im["az"], fov=(45 if im["dist"] > 20 else 60)).save(out, quality=88)
                else: flat3(f, (im["bearing"] - im["az"] + 180) % 360 - 180, im["dist"]).save(out, quality=88)
            res.append(dict(file=str(out.relative_to(ROOT)), source=im["src"], pano=im["pano"], id=im["id"], page=im["page"], date=im["date"], creator=im["creator"],
                            license=im["license"], dist_m=im["dist"], bearing=im["bearing"], angle_diff=im["angle_diff"], obliq=im["obliq"], cam=im.get("cam", ""), speed=im.get("speed")))
        with lock: meta[c["id"]] = dict(name=c["name"], address=c["address"], kind=c["kind"], area=c["area"], photos=res, commons=cm)
    except Exception as e: log("ERR", c["id"], repr(e)[:120])

if __name__ == "__main__":
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9
    sv = json.load(open(D / "shops_v3.json")); ok = {e["id"] for e in sv if e["photo_ok"]}
    cands = [c for c in json.load(open(D / "candidates.json")) if c["id"] not in ok][:mx]
    tok = token(); B = load_buildings(); used = used_ids()
    meta = json.load(open(META)) if META.exists() else {}
    todo = [c for c in cands if c["id"] not in meta]; log(len(todo), "to do")
    done = 0
    with ThreadPoolExecutor(6) as ex:
        for _ in ex.map(lambda c: work(c, tok, meta, B, used, ok), todo):
            done += 1
            if done % 100 == 0: log(done, "done"); json.dump(meta, open(META, "w"), ensure_ascii=False)
    json.dump(meta, open(META, "w"), ensure_ascii=False, indent=0)
    log("FINISHED", len(meta), "with photo:", sum(1 for v in meta.values() if v["photos"]), "with commons:", sum(1 for v in meta.values() if v["commons"]))
