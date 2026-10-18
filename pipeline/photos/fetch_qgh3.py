"""Panoramax views toward the Quartiergarten Hard (CC BY-SA, per image). Reference only."""
import json, math, io, requests
import numpy as np
from PIL import Image
import fetch_v3 as F

OUT = F.ROOT / "data" / "raw" / "photos" / "qgh"; MP = F.ROOT / "research" / "quartiergarten_hard_photos.json"
TARGETS = [(-640, -120), (-600, -150), (-690, -190), (-640, -60), (-690, -100), (-610, -200), (-660, -150)]
tg = [F.local_ll(*t) for t in TARGETS]
H = {"User-Agent": "sandboxzurich/0.1"}
feats, url = [], "https://api.panoramax.xyz/api/search"
params = dict(bbox="8.5055,47.3805,8.5110,47.3840", limit=500)
r = requests.get(url, params=params, headers=H, timeout=60).json(); feats = r["features"]; print(len(feats), "features")
cands = []
for f in feats:
    lon, lat = f["geometry"]["coordinates"][:2]; p = f["properties"]
    az = p.get("view:azimuth", 0) or 0; pano = (p.get("pers:fov") or 0) >= 180 or p.get("type") == "equirectangular"
    best = None
    for tl, tn in tg:
        dx, dy = F.metres(tl, tn, lat, lon); d = math.hypot(dx, dy)
        if d < 8 or d > 90: continue
        b = F.bearing(dx, dy); diff = 0 if pano else F.adiff(az, b)
        if diff <= 60 and (best is None or d < best[0]): best = (d, b, diff)
    if best: cands.append((best[0] + best[2] * .4, f, best, pano))
cands.sort(key=lambda c: c[0]); chosen = []
for s, f, (d, b, diff), pano in cands:
    lon, lat = f["geometry"]["coordinates"][:2]
    if all(math.hypot(*F.metres(lat, lon, x[0], x[1])) > 8 or abs(((b - x[2]) + 180) % 360 - 180) > 30 for x in chosen):
        chosen.append((lat, lon, b, f, d, pano))
    if len(chosen) >= 30: break
print(len(cands), "cands", len(chosen), "chosen", sum(1 for c in chosen if c[5]), "pano")
meta = json.load(open(MP)); n = 0
for lat, lon, b, f, d, pano in chosen:
    p = f["properties"]; a = f["assets"].get("sd") or f["assets"].get("hd")
    try: img = Image.open(io.BytesIO(requests.get(a["href"], headers=H, timeout=40).content)).convert("RGB")
    except Exception as e: print("fail", e); continue
    if pano:
        W, Hh = img.size; yaw = b - (p.get("view:azimuth") or 0); size = 1024; fov = 80; ar = np.asarray(img); ff = (size / 2) / math.tan(math.radians(fov / 2))
        xs, ys = np.meshgrid(np.arange(size) - size / 2, np.arange(size * 2 // 3) - size / 3)
        lo = np.arctan2(xs, ff) + math.radians(yaw); la = np.arctan2(-ys, np.hypot(xs, ff))
        img = Image.fromarray(ar[((.5 - la / math.pi) * (Hh - 1)).astype(int), (((lo / (2 * math.pi)) % 1) * (W - 1)).astype(int)])
    else: img.thumbnail((1024, 1024))
    fn = OUT / f"px_{f['id'][:12]}.jpg"; img.save(fn, quality=85)
    meta.append(dict(file=str(fn.relative_to(F.ROOT)), source="panoramax" + ("-360crop" if pano else ""), license=p.get("license", "CC-BY-SA-4.0"), author=(p.get("providers") or [{}])[0].get("name", "unknown") if p.get("providers") else "unknown", url="https://api.panoramax.xyz/#focus=pic&pic=" + f["id"], lat=lat, lon=lon, heading=p.get("view:azimuth"), year=int(p["datetime"][:4]), dist_m=round(d)))
    n += 1
json.dump(meta, open(MP, "w"), ensure_ascii=False, indent=1); print("added", n)
