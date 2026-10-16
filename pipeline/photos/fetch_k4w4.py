"""Photo research wave 4 (buildings along Langstrasse/Badenerstrasse/Limmatplatz/Stauffacher...): wraps fetch_v3 with own site list and meta
(research/v3/photos_k4w4.json). Usage: python fetch_k4w4.py [--only id,id]"""
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius
    ("limmathaus", "Limmathaus (Limmatstrasse 118, Limmatplatz)", 1223, 29, 70),
    ("johanneskirche", "Johanneskirche Limmatplatz", 1269, -16, 60),
    ("zett_haus", "Zett-Haus (Badenerstrasse/Seebahnstrasse)", 1071, -1118, 80),
    ("stauffacher_turm", "Hochhaus Stauffacher (Badenerstrasse/Stauffacherstrasse)", 950, -1114, 70),
    ("apollo_stauffacher", "Apollo-Haus Stauffacherstrasse", 874, -1095, 60),
    ("baeckeranlage_pavillon", "Quartierzentrum Baeckeranlage Pavillon", 600, -694, 60),
    ("crowne_plaza", "Crowne Plaza Zuerich (Badenerstrasse 420)", -767, -428, 90),
    ("alto_tower", "Alto Tower / Badenerstrasse 600 area", -1198, 29, 90),
    ("swissmill", "Swissmill Tower (Sihlquai/Limmat)", 770, 640, 120),
    ("st_joseph", "Pfarrkirche St. Joseph", 838, 309, 70),
    ("kw_letten", "Wasserkraftwerk Letten", 1215, 351, 80),
    ("james_hochhaus", "James Hochhaus Badenerstrasse", -1584, -300, 90),
    ("docks_langstrasse", "The Docks / Langstrasse", 992, -218, 70),
    ("idaplatz_block", "Grossblock Idaplatz/Hohlstrasse", 287, -1078, 100),
    ("albisriederplatz_ost", "Albisriederplatz Bauten", -526, -695, 70),
    ("langstrasse_sued", "Langstrasse Eckbauten Sued", 713, -658, 70),
    ("langstrasse_nord", "Langstrasse Eckbauten Nord", 808, -477, 70),
    ("roentgen_zeile", "Roentgenstrasse Zeile", 762, 52, 70),
    ("wiedikon_platz", "Bahnhof Wiedikon Platz Bauten", 470, -1415, 70),
]


def sites():
    return [(i, n, "landmark", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.META = F.ROOT / "research" / "v3" / "photos_k4w4.json"
F.SITES_OUT = F.ROOT / "research" / "v3" / "sites_k4w4.json"
if __name__ == "__main__":
    F.main()
