"""Photos at the camera points of one zone: wraps fetch_v3 with one site per camera point of pipeline/overrides/zones.json.
Images -> data/raw/photos/z<N>/, meta -> research/zones/zone<N>_cam_photos.json (read by pipeline/zones/zone_cmp.py), sites -> zone<N>_cam_sites.json.
Usage: python fetch_zone_cams.py <N> [--only id,id] [--force] [--list]   (log: logs/photos_z<N>_cams.log)"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F  # noqa: E402

N = int(sys.argv.pop(1))
ZONE = [z for z in json.load(open(F.ROOT / "pipeline/overrides/zones.json"))["zones"] if z["id"] == N][0]


def sid(name):
    return f"z{N}_" + re.sub(r"[^a-z0-9]+", "_", name.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")).strip("_")


def sites():
    return [(sid(c["name"]), c["name"], "place", *F.local_ll(c["x"], c["y"]), 45) for c in ZONE["cams"]]


F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / f"z{N}"
F.META = F.ROOT / "research" / "zones" / f"zone{N}_cam_photos.json"
F.SITES_OUT = F.ROOT / "research" / "zones" / f"zone{N}_cam_sites.json"

if __name__ == "__main__":
    F.main()
