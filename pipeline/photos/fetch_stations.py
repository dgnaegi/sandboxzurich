"""Photo research for SBB stations (Hardbruecke, Altstetten, Wiedikon): several sites along each platform + accesses.
Wraps fetch_v3 -> research/v3/photos_stations.json, images in data/raw/photos/v3/<id>/. Usage: python fetch_stations.py [--only id,id]"""
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius
    ("st_hb_w", "Bahnhof Hardbruecke Perron West", -50, 150, 60),
    ("st_hb_m", "Bahnhof Hardbruecke Perron Mitte / Aufgaenge Hardbruecke", 30, 115, 60),
    ("st_hb_e", "Bahnhof Hardbruecke Perron Ost", 120, 90, 60),
    ("st_hb_zug", "Bahnhof Hardbruecke Zugang Turbinenstrasse / Velostation", 20, 70, 50),
    ("st_alt_w", "Bahnhof Altstetten Perron West", -2180, 825, 60),
    ("st_alt_m", "Bahnhof Altstetten Perron Mitte / Unterfuehrung", -2087, 794, 60),
    ("st_alt_e", "Bahnhof Altstetten Perron Ost", -2000, 760, 60),
    ("st_alt_zug", "Bahnhof Altstetten Bahnhofplatz / Zugang Nord", -2080, 880, 50),
    ("st_wie_w", "Bahnhof Wiedikon Perron Sued", 340, -1190, 60),
    ("st_wie_m", "Bahnhof Wiedikon Perron Mitte", 436, -1285, 55),
    ("st_wie_e", "Bahnhof Wiedikon Perron Nord / Aufnahmegebaeude", 520, -1380, 55),
    ("st_wie_zug", "Bahnhof Wiedikon Zugang Treppen / Vorplatz", 545, -1400, 50),
]


def sites():
    return [(i, n, "landmark", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.META = F.ROOT / "research" / "v3" / "photos_stations.json"
F.SITES_OUT = F.ROOT / "research" / "v3" / "sites_stations.json"
if __name__ == "__main__":
    F.main()
