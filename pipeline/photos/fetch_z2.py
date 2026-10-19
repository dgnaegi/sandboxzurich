"""Photo gaps Zone 2 (Kreis 5 Industrie): wraps fetch_v3 with the sites in zone 2 that have few local photos.
Images -> data/raw/photos/z2/, meta -> research/zones/zone2_photos.json, sites -> research/zones/zone2_sites.json.
Usage: python fetch_z2.py [--only id,id] [--force] [--list]   (log: logs/photos_z2.log)"""
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius (same local frame as zones.json: x = Ost, y = Nord)
    ("z2_escher_wyss", "Escher-Wyss-Platz (Haltestelle + Bruecke)", 448, 696, 70),
    ("z2_hardbruecke_bhf", "Bahnhof Hardbruecke Perron", 28, 111, 60),
    ("z2_turbinenplatz", "Turbinenplatz", -3, 634, 70),
    ("z2_josefwiese", "Josefwiese", 506, 187, 70),
    ("z2_viadukt", "Viadukt (Markthalle)", 704, 399, 70),
    ("z2_limmatplatz", "Limmatplatz (Migros, Tramschlaufe)", 1131, 74, 70),
    ("z2_roentgenplatz", "Roentgenplatz", 759, 126, 70),
    ("z2_konradstrasse", "Limmatstrasse/Konradstrasse", 1286, -229, 60),
    ("z2_fabrikstrasse", "Fabrikstrasse", 710, 86, 60),
    ("z2_limmatufer", "Limmatufer", 1250, 250, 70),
    ("z2_sihlquai", "Sihlquai", 1550, -92, 60),
]


def sites():
    return [(i, n, "place", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "z2"
F.META = F.ROOT / "research" / "zones" / "zone2_photos.json"
F.SITES_OUT = F.ROOT / "research" / "zones" / "zone2_sites.json"

if __name__ == "__main__":
    F.main()
