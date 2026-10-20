"""Zone 5 (Altstetten/Letzigrund), area Letzigrund / Herdernstrasse / Haltestelle: landmark houses read from Mapillary dashcam photos
(research/zones/zone5_cam_photos.json, data/raw/photos/z5/*, protocol research/zones/z5/area_letzi.md). Colours are estimates from the photos; no logos.
swissBUILDINGS3D ids found with common.near() around the photo positions. Registers into overrides/landmarks_z5c.json. Usage: python z5c_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z5c.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=3.6, eg_kind="plain", cornice=("#cfc9bd", 0.3, 0.4), roof=("flat", "#8a8884"), eave_rise=0.0, frame="#f1ede2", lit=0.3)
SPECS = {  # name: (title, ids, overrides)
    # Badenerstrasse south of the stadium (Mapillary 727567819204512): 5-storey pink 1950s block, brick plinth, rounded balconies, flat roof; ochre house with hip roof to its west
    "letzi_pink": ("Badenerstrasse rosa Wohnblock (Letzigrund)", ["ID_D0A7406F", "ID_5604C6FA"], dict(wall="#d8aba0", seed=91, base_col="#8c4e40", frame="#f4efe6", win=(1.05, 1.65, 0.9), bayw=2.6, cornice=("#6f6b66", 0.25, 0.35), parapet=0.45)),
    "letzi_ocker": ("Badenerstrasse ockerfarbenes Haus (Letzigrund)", ["ID_FD985A3E"], dict(wall="#e0c58c", seed=92, base_col="#8a7a62", roof=("hip", "#8a4a38", 5.0), eave_rise=4.4, cornice=("#efe6cc", 0.4, 0.5))),
    # Herdernstrasse east side (Mapillary 2025 dashcam, 6+ photos): white-grey plastered 7-storey blocks with blue window frames
    "herdern_block": ("Herdernstrasse weisse Blocks mit blauen Fenstern", ["ID_96DB387A", "ID_9F036ED8", "ID_0C87A1B2"], dict(wall="#dcddd6", seed=93, base_col="#9a9a94", frame="#2f6fae", win=(1.1, 1.5, 0.95), bayw=2.6, fh=3.0, cornice=("#c8c8c2", 0.3, 0.4), parapet=0.5)),
    # Two Y-shaped 38 m towers south of the Letzigrund stop (Mapillary 2023-2025, 4 photos): light grey-beige, small regular windows, flat roof (tiles show brown striped blocks)
    "letzi_tower": ("Hochhaeuser Letzigrund (Y-Form)", ["ID_BEDFC1B3", "ID_43BA45EE"], dict(wall="#c4baa8", seed=94, base_col="#9a968c", frame="#8a8f92", win=(1.5, 1.35, 1.0), bayw=2.9, fh=3.0, eg_h=3.8, cornice=("#a9a69e", 0.3, 0.5), parapet=0.6)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z5c_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
