"""Zone 2 (Kreis 5 Industrie): landmark houses read from Mapillary/Panoramax street views (research/zones/z2/sheets*/*.jpg, notes in
research/zones/z2/notes_raw_z2_*.tsv). Colours are estimates from the photos; no shop names or logos. swissBUILDINGS3D ids via z4_find.py.
Registers into overrides/landmarks_z2.json. Usage: python z2_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z2.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=4.2, eg_kind="shop", cornice=("#e9e2d0", 0.4, 0.5), roof=("hip", "#6a5a52", 5.0), eave_rise=4.6, frame="#f1ede2", lit=0.35)
SPECS = {  # name: (title, ids, overrides)
    "hard316": ("Hardstrasse 316 ockergelbes Eckhaus", ["ID_52F098DA"], dict(wall="#e0b048", seed=81, base_col="#8a7a60", cornice=("#c8503a", 0.35, 0.5), awning=("#a82a24", 3.0, 1.0))),
    "traug8": ("Traugottstrasse 8 ockergelb mit Backsteinbaendern", ["ID_F5C5A3DE"], dict(wall="#e0b048", seed=82, base_col="#8a7a60", cornice=("#c8503a", 0.35, 0.5), awning=("#a82a24", 3.0, 1.0), eave_rise=4.0)),
    "gaso26": ("Gasometerstrasse 26 cremefarbenes Eckhaus", ["ID_60B87639"], dict(wall="#e8dcc0", seed=83, base_col="#8a8478", cornice=("#f4f0e4", 0.45, 0.55), awning=("#5a2a30", 3.0, 1.0))),
    "acker52": ("Ackerstrasse 52 gelbes Eckhaus mit Markisen", ["ID_A7BCFF6E"], dict(wall="#e8d090", seed=84, base_col="#8a8070", awning=("#c8703a", 3.0, 1.0))),
    "josef130": ("Josefstrasse 130 Sandsteinfassade", ["ID_113D61EE"], dict(wall="#d8ccb8", seed=85, base_col="#8a8478", cornice=("#e4dccb", 0.5, 0.6), awning=("#8a2a24", 3.0, 1.0), roof=("hip", "#5d5f61", 5.0))),
    "fabrik17": ("Fabrikstrasse 17 Backstein und Rustika", ["ID_FAD56DB4"], dict(wall="#b85a40", seed=86, base_col="#8a8a84", cornice=("#d6cdb8", 0.4, 0.5), roof=("hip", "#5d5f61", 5.0))),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z2_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
