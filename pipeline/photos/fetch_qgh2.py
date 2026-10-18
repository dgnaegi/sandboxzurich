"""More Mapillary views of the Quartiergarten Hard: every image (incl. 360 crops) that looks at one of several garden target points. Reference only."""
import json, math, io
import numpy as np
from PIL import Image
import requests
import fetch_v3 as F

OUT = F.ROOT / "data" / "raw" / "photos" / "qgh"
TARGETS = [(-640, -120), (-600, -150), (-690, -190), (-640, -60), (-690, -100), (-610, -200), (-660, -150)]  # local m inside the garden
tok = F.token(); lat0, lon0 = F.local_ll(-640, -130)
rad = 160; dlat, dlon = rad / 110574, rad / (111320 * math.cos(math.radians(lat0)))
r = F.get("ml", F.ML, {"access_token": tok, "bbox": f"{lon0-dlon:.6f},{lat0-dlat:.6f},{lon0+dlon:.6f},{lat0+dlat:.6f}",
                       "fields": "id,thumb_2048_url,thumb_1024_url,compass_angle,computed_geometry,captured_at,creator,is_pano,computed_compass_angle", "limit": 2000}, pause=0.3)
data = r.json().get("data", [])
print(len(data), "images", sum(1 for i in data if i.get("is_pano")), "panos")
tg = [F.local_ll(*t) for t in TARGETS]
cands = []
for im in data:
    if not im.get("computed_geometry"): continue
    ilon, ilat = im["computed_geometry"]["coordinates"]
    best = None
    for (tl, tn) in tg:
        dx, dy = F.metres(tl, tn, ilat, ilon); d = math.hypot(dx, dy)
        if d < 8 or d > 150: continue
        b = F.bearing(dx, dy)
        diff = 0 if im.get("is_pano") else F.adiff(im.get("compass_angle", 0), b)
        if diff <= 50 and (best is None or d < best[0]): best = (d, b, diff)
    if best:
        cands.append((best[0] + best[2] * 0.3, im, best))
cands.sort(key=lambda c: c[0]); chosen = []
for s, im, (d, b, diff) in cands:
    ilon, ilat = im["computed_geometry"]["coordinates"]
    if all(math.hypot(*F.metres(ilat, ilon, x[0], x[1])) > 7 or abs(((b - x[2]) + 180) % 360 - 180) > 30 for x in chosen):
        chosen.append((ilat, ilon, b, im, d))
    if len(chosen) >= 40: break
meta = json.load(open(F.ROOT / "research" / "quartiergarten_hard_photos.json")); have = {m["url"] for m in meta}
def persp(img, yaw_deg, fov=80, size=1024):
    W, H = img.size; a = np.asarray(img); f = (size / 2) / math.tan(math.radians(fov / 2))
    xs, ys = np.meshgrid(np.arange(size) - size / 2, np.arange(size * 2 // 3) - size / 3)
    lon = np.arctan2(xs, f) + math.radians(yaw_deg); lat = np.arctan2(-ys, np.hypot(xs, f))
    u = ((lon / (2 * math.pi) + .5) % 1) * (W - 1); v = (.5 - lat / math.pi) * (H - 1)
    return Image.fromarray(a[v.astype(int), u.astype(int)])
n = 0
for ilat, ilon, b, im, d in chosen:
    url = f"https://www.mapillary.com/app/?pKey={im['id']}"
    if url in have: continue
    link = im.get("thumb_2048_url") or im.get("thumb_1024_url")
    try: raw = requests.get(link, timeout=40).content; img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e: print("fail", e); continue
    if im.get("is_pano"):
        yaw = b - (im.get("computed_compass_angle") or im.get("compass_angle") or 0); img = persp(img, yaw)
    else: img.thumbnail((1024, 1024))
    f = OUT / f"ml2_{im['id']}.jpg"; img.save(f, quality=85)
    from datetime import datetime, timezone
    meta.append(dict(file=str(f.relative_to(F.ROOT)), source="mapillary" + ("-360crop" if im.get("is_pano") else ""), license="CC BY-SA 4.0", author=(im.get("creator") or {}).get("username", "unknown"), url=url, lat=ilat, lon=ilon, heading=im.get("compass_angle"), year=datetime.fromtimestamp(im["captured_at"] / 1000, timezone.utc).year, dist_m=round(d)))
    n += 1
json.dump(meta, open(F.ROOT / "research" / "quartiergarten_hard_photos.json", "w"), ensure_ascii=False, indent=1); print("added", n)
