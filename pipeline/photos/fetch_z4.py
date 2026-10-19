"""Photo gaps Zone 4 (Wiedikon): wraps fetch_v3 with the sites not covered by fetch_ida.py.
Images -> data/raw/photos/z4/, meta -> research/zones/zone4_photos.json, sites -> research/zones/zone4_sites.json.
Usage: python fetch_z4.py [--only id,id] [--force] [--list]   (log: logs/photos_z4.log)"""
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius (same local frame as zones.json: x = Ost, y = Nord)
    ("z4_schmiede", "Schmiede Wiedikon (Kreuzung + Tram)", 139, -1562, 60),
    ("z4_bahnhof_vp", "Bahnhof Wiedikon Vorplatz", 563, -1400, 70),
    ("z4_bahnhof_perron", "Bahnhof Wiedikon Perron", 423, -1301, 60),
    ("z4_goldbrunnen", "Goldbrunnenplatz + Haltestelle", -191, -1516, 70),
    ("z4_kalkbreite", "Kalkbreite", 340, -1170, 70),
    ("z4_friedhof", "Friedhof Sihlfeld Haupteingang", -405, -939, 70),
    ("z4_ortsmuseum", "Ortsmuseum Wiedikon", 236, -1761, 60),
]


def sites():
    return [(i, n, "place", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "z4"
F.META = F.ROOT / "research" / "zones" / "zone4_photos.json"
F.SITES_OUT = F.ROOT / "research" / "zones" / "zone4_sites.json"

if __name__ == "__main__":
    F.main()
