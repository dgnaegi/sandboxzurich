"""Photo research Schlachthof Zuerich (Herdernstrasse) + Letzipark: wraps fetch_v3 with own sites;
images -> data/raw/photos/schlachthof/, meta research/v3/photos_schlachthof.json.  Usage: python fetch_schlachthof.py"""
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius
    ("schl_mitte", "Schlachthofareal Mitte", -655, 93, 90),
    ("schl_herdern", "Herdernstrasse Schlachthof", -690, 50, 70),
    ("schl_nord", "Schlachthof Nord", -640, 140, 70),
    ("lp_mitte", "Letzipark Mitte", -1318, 236, 90),
    ("lp_basler", "Letzipark Baslerstrasse", -1318, 190, 70),
    ("lp_hohl", "Letzipark Hohlstrasse", -1290, 280, 70),
]


def sites():
    return [(i, n, "place", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "schlachthof"
F.META = F.ROOT / "research" / "v3" / "photos_schlachthof.json"
F.SITES_OUT = F.ROOT / "research" / "v3" / "sites_schlachthof.json"
F.N_ML, F.N_COMMONS, F.N_PANO = 10, 10, 4
if __name__ == "__main__":
    F.main()
