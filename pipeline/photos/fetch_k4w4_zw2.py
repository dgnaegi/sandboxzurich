"""Second pass for the Zentralwaescherei: Mapillary/Panoramax frames within ~70 m of the street front (kiosk at local ~(255,318)) and the
south/east yard (water tower ~ (333,297)), any viewing direction that sees one of the targets. Adds to photos_k4w4_zw.json."""
import json, math, re
import fetch_v3 as F
from fetch_v3 import get, log, metres, bearing, adiff, download, local_ll, ROOT, OUT_DIR, token, ML, PANO
import fetch_k4w4_zw as Z

TARGETS = [(255, 318), (293, 360), (333, 297), (300, 340), (320, 395)]
D = OUT_DIR / "zentralwaescherei"
meta = json.load(open(Z.META)); photos = meta["zentralwaescherei"]["photos"]
have = {p["url"] for p in photos}
tx = [(local_ll(*t)) for t in TARGETS]
c0 = local_ll(290, 340); rad = 190
dlat, dlon = rad / 110574, rad / (111320 * math.cos(math.radians(c0[0])))
r = get("ml", ML, {"access_token": token(), "bbox": f"{c0[1]-dlon:.6f},{c0[0]-dlat:.6f},{c0[1]+dlon:.6f},{c0[0]+dlat:.6f}",
                   "fields": "id,thumb_1024_url,compass_angle,computed_geometry,captured_at,creator,is_pano", "limit": 4000}, pause=0.3)
cands = []
for im in r.json().get("data", []):
    if im.get("is_pano") or not im.get("thumb_1024_url") or not im.get("computed_geometry"): continue
    ilon, ilat = im["computed_geometry"]["coordinates"]
    best = None
    for (tlat, tlon), t in zip(tx, TARGETS):
        dx, dy = metres(tlat, tlon, ilat, ilon); d = math.hypot(dx, dy)
        if d < 10 or d > 75: continue
        df = adiff(im.get("compass_angle", 0), bearing(dx, dy))
        if df < 38 and (best is None or d < best[0]): best = (d, df, t)
    if best: cands.append((best[0] + best[1], im, best))
cands.sort(key=lambda c: c[0]); log(f"candidates {len(cands)}")
chosen = []
for s, im, b in cands:
    ilon, ilat = im["computed_geometry"]["coordinates"]
    if all(math.hypot(*metres(ilat, ilon, *(x["computed_geometry"]["coordinates"][::-1]))) > 7 or adiff(im["compass_angle"], x["compass_angle"]) > 25 for x in chosen):
        chosen.append(im)
    if len(chosen) >= 30: break
n = 0
for im in chosen:
    f = D / f"ml_{im['id']}.jpg"
    if str(f.relative_to(ROOT)) in {p['file'] for p in photos}: continue
    if download(im["thumb_1024_url"], f, "ml"):
        ilon, ilat = im["computed_geometry"]["coordinates"]
        photos.append(dict(file=str(f.relative_to(ROOT)), source="mapillary", license="CC BY-SA 4.0", author=(im.get("creator") or {}).get("username", "unknown"),
                           url=f"https://www.mapillary.com/app/?pKey={im['id']}", lat=ilat, lon=ilon, heading=im.get("compass_angle"), year=0, night=False, dist_m=0)); n += 1
Z.META.write_text(json.dumps(meta, ensure_ascii=False, indent=1)); log(f"added {n}, total {len(photos)}")
