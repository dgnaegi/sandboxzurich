"""Photo research Idaplatz quarter: wraps fetch_v3 with own sites; images -> data/raw/photos/ida/, meta research/v3/photos_ida.json.
Usage: python fetch_ida.py [--only id,id]"""
import fetch_v3 as F

SITES = [  # id, name, local x, y, radius
    ("ida_platz", "Idaplatz (Platzmitte)", -125, -1115, 70),
    ("ida_nord", "Idaplatz Nord / Zurlindenstrasse", -107, -1075, 60),
    ("ida_sued", "Idastrasse Sued", -125, -1165, 60),
    ("ida_berta", "Bertastrasse", -153, -1082, 60),
    ("ida_gertrud", "Gertrudstrasse", -75, -1172, 70),
    ("ida_aemtler", "Aemtlerstrasse / Wiesendangerstrasse", -195, -1175, 70),
    ("ida_zentral", "Zentralstrasse", -42, -1044, 70),
    ("ida_zurlinden_w", "Zurlindenstrasse West", -230, -1100, 70),
    ("ida_zurlinden_o", "Zurlindenstrasse Ost", 0, -1100, 70),
    ("ida_thomas", "Thomasweg / Martastrasse", -210, -1005, 70),
]


def sites():
    return [(i, n, "place", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "ida"
F.META = F.ROOT / "research" / "v3" / "photos_ida.json"
F.SITES_OUT = F.ROOT / "research" / "v3" / "sites_ida.json"
F.N_ML, F.N_COMMONS, F.N_PANO = 14, 8, 4
if __name__ == "__main__":
    F.main()
