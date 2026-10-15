"""Photo research wave 3 / Kreis 5: wraps fetch_v3 with own site list and own meta file (research/v3/photos_k5w3.json),
so parallel agents do not collide on photos.json. Usage: python fetch_k5w3.py [--only id,id]"""
import sys
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius
    ("freitag_turm", "Freitag Flagship Store / Container-Turm (Geroldstrasse 17-21)", 207, 177, 70),
    ("frau_gerolds_garten", "Frau Gerolds Garten (Geroldstrasse 23)", 180, 150, 60),
    ("loewenbraeu", "Loewenbraeu-Areal (Limmatstrasse 264)", 727, 518, 140),
    ("westpark", "Westpark / Galaxus (Pfingstweidstrasse 60)", -137, 730, 110),
    ("mobimo_tower", "Mobimo Tower (Turbinenstrasse 18)", -179, 447, 90),
    ("puls5", "Puls 5 (Giessereistrasse)", 86, 736, 110),
    ("zentralwaescherei", "Zentralwaescherei (Neue Hard 12)", 293, 360, 90),
    ("technopark", "Technopark (Technoparkstrasse 1)", -28, 758, 100),
    ("hochhaus_pfingstweid", "Hochhaus Pfingstweidstrasse (80 m, 2013)", -493, 725, 90),
    ("migros_limmatplatz", "Migros/Klubschule Limmatplatz", 1130, 120, 100),
]


def sites():
    return [(i, n, "landmark", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.META = F.ROOT / "research" / "v3" / "photos_k5w3.json"
F.SITES_OUT = F.ROOT / "research" / "v3" / "sites_k5w3.json"
if __name__ == "__main__":
    F.main()
