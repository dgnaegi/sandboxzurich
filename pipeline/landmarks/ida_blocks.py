"""Idaplatz: markante Platzhaeuser (Nordostzeile Zurlindenstrasse + Ecke Idaplatz 1), Gruenderzeit, EG Laeden. Farben aus Strassenfotos
(research/buildings/notes_raw_ida_001.tsv, research/idaplatz.md). Registers into overrides/landmarks_ida.json. Usage: python ida_blocks.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRI = ROOT / "pipeline" / "overrides" / "landmarks_ida.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=4.3, eg_kind="shop", cornice=("#e9e2d0", 0.4, 0.5), roof=("hip", "#5d5f61", 5.0), eave_rise=4.6, frame="#f1ede2", lit=0.35)
SPECS = {
    "ida8": (["ID_5D8145D7"], dict(wall="#d4be98", seed=61, base_col="#8c8372")),
    "ida9": (["ID_3AC9BCB9"], dict(wall="#d6d3cc", seed=62, base_col="#8a8a84")),
    "ida10": (["ID_4749448D"], dict(wall="#d8c8a8", seed=63, base_col="#8c8372")),
    "ida1": (["ID_4FED48B9"], dict(wall="#d9b46a", seed=64, base_col="#8a7a60")),
}


def build(only=None):
    _k4.OVR4 = OVRI
    for k, (ids, kw) in SPECS.items():
        if only and k not in only or "FIND" in ids[0]: continue
        _k4.block_model(k, "Idaplatz " + k[3:], ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
