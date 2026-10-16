"""Photo research wave 6 (public buildings: schools, GZ, Wachen, libraries): wraps fetch_v3 with own site list and meta (research/v3/photos_k4w6.json).
Usage: python fetch_k4w6.py [--only id,id]"""
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius
    ("sh_kern", "Schulhaus Aussersihl Kern (Kernstrasse)", 619, -748, 70),
    ("sh_hohl", "Schulhaus Hohl Aussersihl (Hohlstrasse)", 643, -622, 70),
    ("sh_brauer", "Schulhaus Brauer Aussersihl", 668, -561, 60),
    ("sh_feld", "Schulhaus Feld Aussersihl", 447, -626, 70),
    ("sh_sihlfeld", "Schulhaus Sihlfeld", -161, -356, 80),
    ("sh_limmat", "Schulhaus Limmat Limmatstrasse", 1326, -80, 70),
    ("gz_loogarten", "GZ Loogarten Badenerstrasse Altstetten", -2173, 349, 70),
    ("sh_kappeli", "Schulhaus Kappeli Altstetten", -1719, 284, 80),
    ("sh_pfingstweid", "Schulhaus Pfingstweid", -213, 538, 70),
    ("sh_schuetze", "Schulhaus Schuetze und Quartierzentrum", 511, 538, 80),
    ("wache_aussersihl", "Regionalwache Aussersihl (Stadtpolizei)", 916, -546, 60),
    ("wache_wiedikon", "Regionalwache Wiedikon (Stadtpolizei)", 223, -1517, 60),
    ("pbz_aussersihl", "PBZ Bibliothek Aussersihl (Sihlfeldstrasse)", 608, -1268, 60),
    ("ortsmuseum_wiedikon", "Ortsmuseum Wiedikon", 236, -1761, 60),
    ("wache_industrie", "Regionalwache Industrie", 969, 385, 60),
    ("sh_wengi", "Schulhaus Wengi / Viventa", 506, -947, 60),
]


def sites():
    return [(i, n, "landmark", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.META = F.ROOT / "research" / "v3" / "photos_k4w6.json"
F.SITES_OUT = F.ROOT / "research" / "v3" / "sites_k4w6.json"
if __name__ == "__main__":
    F.main()
