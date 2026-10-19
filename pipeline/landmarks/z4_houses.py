"""Zone 4 (Wiedikon): landmark houses read from Panoramax/Mapillary street views (research/zones/z4/sheets/*.jpg, notes in
research/zones/z4/notes_raw_z4_*.tsv). Colours are estimates from the photos; no shop names or logos. swissBUILDINGS3D ids from z4_find.py.
Registers into overrides/landmarks_z4.json. Usage: python z4_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z4.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=4.2, eg_kind="shop", cornice=("#e9e2d0", 0.4, 0.5), roof=("hip", "#5d5f61", 5.0), eave_rise=4.6, frame="#f1ede2", lit=0.35)
SPECS = {  # name: (title, ids, overrides)
    "berta1": ("Bertastrasse 1 Eckhaus mit Erkern", ["ID_9687191D"], dict(wall="#b8a898", seed=71, base_col="#7d756a", cornice=("#d2c9b8", 0.45, 0.55), awning=("#7a2a24", 3.0, 1.0))),
    "zurl21": ("Zurlindenstrasse 21 stuckverziert", ["ID_416D472A"], dict(wall="#e0d8c0", seed=72, base_col="#8a8478", cornice=("#f4f0e4", 0.5, 0.6), awning=("#a8382c", 3.0, 1.0))),
    "zurl29": ("Zurlindenstrasse 29 Backsteinhaus", ["ID_C40A6B55"], dict(wall="#c06848", seed=73, base_col="#8a8a84", cornice=("#d6cdb8", 0.4, 0.5))),
    "zent78": ("Zentralstrasse 78 ockerfarbenes Eckhaus", ["ID_E21E4F20"], dict(wall="#dcae60", seed=74, base_col="#8a7a60", frame="#f4f0e2")),
    "ida15": ("Idastrasse 15 lachsfarbenes Eckhaus", ["ID_733A1DA3"], dict(wall="#dc9f88", seed=75, base_col="#8c8372")),
    "birm299": ("Birmensdorferstrasse 299", ["ID_CE060823"], dict(wall="#e6eaec", seed=76, base_col="#8a8a84", roof=("hip", "#4a4c50", 5.5), eave_rise=5.0)),
    "birm301": ("Birmensdorferstrasse 301 blaue Laeden", ["ID_99DD1052"], dict(wall="#b4c4da", seed=77, base_col="#8a8a84", frame="#2f5f95", roof=("hip", "#4a4c50", 5.5), eave_rise=5.0)),
    "birm303": ("Birmensdorferstrasse 303 orange Putz", ["ID_0F5B824B"], dict(wall="#d08a68", seed=78, base_col="#8a8a84", frame="#2f5f95", roof=("hip", "#4a4c50", 5.5), eave_rise=5.0)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model(k_name(k), title, ids, **{**COMMON, **kw})


def k_name(k):
    return "z4_" + k


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
