"""Photo research wave 5 (new sites): wraps fetch_v3 with own site list and meta (research/v3/photos_k4w5.json). Usage: python fetch_k4w5.py [--only id,id]"""
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius
    ("europaallee_lager", "Europaallee Lagerstrasse Bloecke", 1357, -571, 90),
    ("europaallee_ost", "Europaallee Gleisbogen / Lagerstrasse Sued", 1450, -650, 80),
    ("altstetten_platz", "Bahnhof Altstetten Platz Raender", -2135, 794, 90),
    ("goldbrunnen", "Goldbrunnenplatz Birmensdorferstrasse", 279, -1787, 80),
]


def sites():
    return [(i, n, "landmark", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.META = F.ROOT / "research" / "v3" / "photos_k4w5.json"
F.SITES_OUT = F.ROOT / "research" / "v3" / "sites_k4w5.json"
if __name__ == "__main__":
    F.main()
