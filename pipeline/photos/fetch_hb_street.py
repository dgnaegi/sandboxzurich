"""Street-level HB photos from Mapillary + Panoramax (no Wikimedia calls) -> data/raw/photos/hb/, metadata research/hb/photos_street.json.
finalize_hb.py merges this file into photos.json."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F
import fetch_hb as H
ROOT = F.ROOT
OUT = ROOT / "data/raw/photos/hb"; META = ROOT / "research/hb/photos_street.json"
meta = json.load(open(META)) if META.exists() else {"photos": []}
have = {Path(p["file"]).name for p in meta["photos"]}
tok = F.token()
for (x, y, r) in ((1790, -650, 230), (1700, -640, 120), (1850, -700, 150), (1650, -700, 160), (1760, -740, 100), (1880, -600, 120)):
    la, lo = F.local_ll(x, y)
    for c in F.mapillary("hb", la, lo, r, tok):
        f = OUT / f"ml_{c['id']}.jpg"
        if f.name in have: continue
        if H.dl(c["url"], f, "ml"):
            meta["photos"].append(dict(file=str(f.relative_to(ROOT)), source="mapillary", license="CC BY-SA 4.0", author=c["author"], page=f"https://www.mapillary.com/app/?pKey={c['id']}",
                                       lat=c["lat"], lon=c["lon"], heading=c["heading"], year=c["year"], group="mapillary")); have.add(f.name)
    for c in F.panoramax(la, lo, r):
        f = OUT / f"px_{c['id'][:12]}.jpg"
        if f.name in have: continue
        if H.dl(c["url"], f, "pano"):
            meta["photos"].append(dict(file=str(f.relative_to(ROOT)), source="panoramax", license=c["license"], author=c["author"], page="https://api.panoramax.xyz/#focus=pic&pic=" + c["id"],
                                       lat=c["lat"], lon=c["lon"], heading=c["heading"], group="panoramax")); have.add(f.name)
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=1)); print(len(meta["photos"]), flush=True)
