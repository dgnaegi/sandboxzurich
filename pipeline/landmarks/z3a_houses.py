"""Zone 3 (Kreis 4 Mitte), area south-east (Stauffacher, Badenerstrasse/Kalkbreite, Lochergut surroundings, Seebahnstrasse): landmark houses read from
Mapillary/Panoramax/Commons photos (research/zones/zone3_cam_photos.json, protocol research/zones/z3/area_southeast.md). Colours are estimates from the photos;
no logos, no names (signs come from the POI system). swissBUILDINGS3D ids found with common.near() + footprint map; Mapillary headings are unreliable (lesson 15),
so houses were matched by shape/height with free-camera shots. Registers into overrides/landmarks_z3a.json. Usage: python z3a_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z3a.json"
COMMON = dict(cols=2, rows=3, fh=3.1, bayw=2.6, win=(1.2, 1.7, 0.85), eg_h=4.0, eg_kind="shop", cornice=("#e0d8c4", 0.35, 0.45), roof=("flat", "#8a8780"), eave_rise=0.0, frame="#f1ede2", lit=0.35)
SPECS = {  # name: (title, id prefixes, overrides)
    # Stauffacherstrasse west side (Panoramax 33197263 + Mapillary 427038079830413): sandy-beige stone block, arched shop arcade with yellow striped awnings, dark mansard roof
    "stf_west": ("Stauffacherstrasse Arkadenhaeuser", ["ID_C83D6FBC", "ID_2E2325D9", "ID_1495D236"], dict(wall="#d8cbad", seed=301, base_col="#8b8274", eg_kind="arch", eg_h=4.6, bayw=2.8, win=(1.1, 1.85, 0.85), fh=3.9,
                   cornice=("#e9dfc6", 0.45, 0.55), floor_bands=("#e4d8bb", 0.2, 0.3), roof=("hip", "#58575a", 4.5), eave_rise=4.0, awning=("#e3bf47", 3.2, 0.55), eg_col="#4a4540")),
    # (stf_west now hip again: k4w4_kit.hip_roof rebuilt, no spikes on corner footprints)
    # Stauffacher north-east corner: white-grey 1960s ribbon-window office (Mapillary 427038079830413 left edge, Panoramax 33197263 far left)
    "stf_glass": ("Stauffacher Buerohaus Bandfenster", ["ID_296ADA9D"], dict(wall="#d9dad6", seed=302, base_col="#8d8d8a", frame="#e9eae7", glass="#56646f", win=(3.0, 1.3, 0.95), bayw=3.5, fh=3.65, eg_h=4.4, eg_kind="shop",
                   floor_bands=("#eceeea", 0.5, 0.35), cornice=("#eceeea", 0.4, 0.3), parapet=0.7, eg_col="#3c4045")),
    # Badenerstrasse north of the Kalkbreite crossing (Mapillary 443290651463652, 287510466406959, 1164528874022212): light-grey 1960s ribbon-window offices, 6 storeys
    "kal_glass": ("Badenerstrasse Buerohaeuser Bandfenster", ["ID_D8816D9A", "ID_507C9CEE"], dict(wall="#d4d6d4", seed=303, base_col="#8b8c8a", frame="#e6e8e6", glass="#6d8091", win=(3.0, 1.35, 0.9), bayw=3.5, fh=3.4, eg_h=4.2, eg_kind="shop",
                   floor_bands=("#e9ebe9", 0.5, 0.35), cornice=("#e9ebe9", 0.4, 0.3), parapet=0.6, eg_col="#3c4045")),
    # Badenerstrasse/Kalkbreitestrasse crossing, NE side (Mapillary 443290651463652, 1448850089048149, 2020-2024): 1960s concrete block, warm beige plaster, stepped balconies with dark-red shutters, 7 storeys
    "kal_block": ("Badenerstrasse beiger Balkonblock (Kalkbreite)", ["ID_305C979A"], dict(wall="#d3c8b3", seed=305, base_col="#8a8173", eg_kind="plain", eg_h=3.6, win=(1.7, 1.55, 0.95), bayw=3.4, fh=3.5,
                   frame="#94534a", floor_bands=("#b9b09d", 0.45, 0.8), cornice=("#d9d0bc", 0.3, 0.4), parapet=0.5, glass="#2e2a2c")),
    # Lochergut, Badenerstrasse/Sihlfeldstrasse corner (Mapillary 858257206067781, 388177537298792): tall dusty-pink house, dark plinth, small balconies, mansard
    "loch_pink": ("Badenerstrasse rosa Eckhaus (Lochergut)", ["ID_72F2ACBE"], dict(wall="#d6c0b5", seed=304, base_col="#5d5753", eg_h=4.6, eg_kind="shop", eg_col="#3d3a38", win=(1.0, 1.55, 0.95), bayw=2.5, fh=3.0,
                   cornice=("#ddd2c8", 0.35, 0.45), roof=("hip", "#4c4a4d", 4.5), eave_rise=4.0, frame="#efe9e0")),   # hip again since k4w4_kit.hip_roof was rebuilt (offset bands, no spikes); photos show a dark mansard/hip roof
    # Seebahnstrasse west side (Mapillary 816780163741394, 572601749197518, 227007105862174, 6252641528158777): 1920s Genossenschaft rows, 6 floors, plain plaster in warm grey / cream, balconies, shutters, hip roofs, plain ground floors behind hedges and trees
    "see_a": ("Seebahnstrasse Zeile cremefarben", ["ID_04B8041F", "ID_90D17900", "ID_AAF4B3C3"], dict(wall="#e3d6b6", seed=311, base_col="#8e8676", eg_kind="plain", eg_h=3.4, win=(1.25, 1.55, 0.9), bayw=2.8, fh=3.1,
                   cornice=("#efe8d6", 0.3, 0.4), roof=("hip", "#6a5a52", 4.0), eave_rise=3.6, frame="#f3efe4", floor_bands=None)),
    "see_b": ("Seebahnstrasse Zeile graubeige", ["ID_A4ED2362", "ID_3D480FEC", "ID_424FE598"], dict(wall="#cfc6b6", seed=312, base_col="#8a8478", eg_kind="plain", eg_h=3.4, win=(1.25, 1.55, 0.9), bayw=2.8, fh=3.1,
                   cornice=("#e4ddcd", 0.3, 0.4), roof=("hip", "#5f5650", 4.0), eave_rise=3.6, frame="#f1ede2")),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z3a_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
