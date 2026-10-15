"""Wave 3 / Kreis 4 photo research: reuses fetch_v3 + contact_sheet_v3 with its own metadata file (research/v3/photos_k4w3.json)
so parallel agents do not overwrite research/v3/photos.json. Usage: python k4w3_fetch.py [fetch|sheet] [id,id]"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F
import contact_sheet_v3 as C
ROOT = F.ROOT
META = ROOT / "research" / "v3" / "photos_k4w3.json"
F.META = META; C.META = META
F.SITES_OUT = ROOT / "research" / "v3" / "sites_k4w3.json"
LOC = [  # id, name, kind, x, y (local m) or None, lat, lon, radius
    ("kaserne", "Alte Kaserne Zuerich", 47.37548, 8.53299, 110),
    ("zeughaeuser", "Zeughaeuser Kasernenareal", None, None, 90, (1050, -740)),
    ("amtshaus_helvetia", "Amtshaus Helvetiaplatz", 47.3763, 8.52714, 80),
    ("peter_paul", "Kirche St. Peter und Paul", None, None, 80, (857, -1318)),
    ("sihlpost", "Sihlpost", None, None, 100, (1421, -738)),
    ("apollo_stauffacher", "Kino Apollo Stauffacherstrasse", None, None, 70, (875, -1104)),
    ("zett_haus", "Zett-Haus", None, None, 80, (1074, -1122)),
    ("bezirksgebaeude", "Bezirksgebaeude Badenerstrasse 90", 47.37431, 8.52598, 80),
    ("schulhaus_hohl", "Schulhaus Hohl", 47.37827, 8.52486, 80),
    ("schulhaus_feld", "Schulhaus Feldstrasse", 47.37863, 8.5223, 80),
    ("hotel_25hours", "25hours Hotel Langstrasse", 47.38044, 8.5287, 80),
    ("zollhaus", "Zollhaus Zollstrasse 121", 47.38156, 8.52965, 80),
    ("unia_stauffacher", "Unia-Haus Stauffacher", None, None, 70, (910, -1292)),
    ("kollerhof", "Kollerhof", None, None, 70, (751, -770)),
]


def sites():
    S = []
    for r in LOC:
        sid, name, la, lo, rad = r[:5]
        if la is None: la, lo = F.local_ll(*r[5])
        S.append((sid, name, "landmark", la, lo, rad))
    return S


F.sites = sites
if __name__ == "__main__":
    mode = sys.argv[1]; ids = sys.argv[2] if len(sys.argv) > 2 else None
    if mode == "fetch":
        sys.argv = ["x"] + (["--only", ids] if ids else [])
        F.main()
    else:
        sys.argv = ["x"] + ([ids] if ids else [])
        C.main()
