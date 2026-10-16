"""usage: fetch.py [--only id,..]. Sites from research/squares2/sites.json: [{id,name,x,y,rad}] (local metres). Reuses pipeline/photos/fetch_v3.py."""
import json, sys
from pathlib import Path
sys.path.insert(0, "pipeline/photos")
import fetch_v3 as F
R = F.ROOT
F.OUT_DIR = R / "data/raw/photos/squares2"
F.META = R / "research/squares2/photos.json"
F.SITES_OUT = R / "research/squares2/sites_ll.json"
def sites():
    out = []
    for s in json.load(open(R / "research/squares2/sites.json")):
        lat, lon = F.local_ll(s["x"], s["y"])
        out.append((s["id"], s["name"], "place", lat, lon, s.get("rad", 70)))
    return out
F.sites = sites
F.main()
