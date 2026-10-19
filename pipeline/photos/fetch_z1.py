"""Photos at the Zone 1 camera points (HB und Langstrasse): wraps fetch_v3 with one site per camera point of pipeline/overrides/zones.json.
Images -> data/raw/photos/z1/, meta -> research/zones/zone1_photos.json, sites -> research/zones/zone1_sites.json.
Usage: python fetch_z1.py [--only id,id] [--force] [--list]   (log: logs/photos_z1_cams.log)"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F  # noqa: E402

ZONE = [z for z in json.load(open(F.ROOT / "pipeline/overrides/zones.json"))["zones"] if z["id"] == 1][0]


def sid(name):
    return "z1_" + re.sub(r"[^a-z0-9]+", "_", name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")).strip("_")


def sites():
    return [(sid(c["name"]), c["name"], "place", *F.local_ll(c["x"], c["y"]), 45) for c in ZONE["cams"]]


F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "z1"
F.META = F.ROOT / "research" / "zones" / "zone1_photos.json"
F.SITES_OUT = F.ROOT / "research" / "zones" / "zone1_sites.json"

if __name__ == "__main__":
    F.main()
