"""Zone 5 round 2: house landmarks from Mapillary/Panoramax/Commons photos (research/zones/zone5_cam_photos.json, protocol research/zones/z5/round2.md).
Colours estimated by eye from the photos, no logos/shop names. swissBUILDINGS3D ids via common.near() + footprint map; only buildings
that match a photo AND the footprint map (Mapillary headings are unreliable). Registers into overrides/landmarks_z5R2.json.
Usage: python z5R2_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z5R2.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=3.8, eg_kind="plain", cornice=("#e4ddcc", 0.3, 0.45), roof=("flat", "#8a8780"), eave_rise=0.0, frame="#f1ede2", lit=0.3)
DISABLED = {"westpark_office"}  # facades #4: duplicate of k5w3_westpark ("Westpark (Galaxus)") - both models z-fought over y 601..739; the older one hides both footprints
SPECS = {  # name: (title, ids, overrides)
    # Letzi towers (cm_Letziturm_2022, cm_Wohnsiedlung_Letzi_2025, Mapillary 703328115763013/1692658461620446): 17-storey point towers behind the yellow-brick hall.
    # White/grey tower: grid of white balconies, nearer to the viewer (photo 17, left tower in photo 3).
    "tower_white": ("Letzitürme weisser Wohnturm", ["ID_183A9F0A"], dict(wall="#dcdad3", seed=91, base_col="#8f8c85", frame="#f6f4ee", win=(1.45, 1.5, 0.9), bayw=2.7, fh=2.95, eg_h=4.4,
                    floor_bands=("#f2f0ea", 0.32, 0.5), cornice=("#f4f2ec", 0.3, 0.4), parapet=0.8)),
    # Red/white tower pair (photo 16): salmon-red vertical sun-screen stripes over white balcony grid.
    "tower_red_a": ("Letzitürme roter Wohnturm A", ["ID_95A21C5D"], dict(wall="#d8a998", seed=92, base_col="#8f8c85", frame="#f6f1ea", win=(1.4, 1.5, 0.9), bayw=2.6, fh=2.95, eg_h=4.4,
                    floor_bands=("#efe9e0", 0.3, 0.5), cornice=("#f2ece2", 0.3, 0.4), parapet=0.8)),
    "tower_red_b": ("Letzitürme roter Wohnturm B", ["ID_EF979786"], dict(wall="#d4a08c", seed=93, base_col="#8f8c85", frame="#f6f1ea", win=(1.4, 1.5, 0.9), bayw=2.6, fh=2.95, eg_h=4.4,
                    floor_bands=("#efe9e0", 0.3, 0.5), cornice=("#f2ece2", 0.3, 0.4), parapet=0.8)),
    # Westpark long office block (Mapillary 555853825895875 from the north, game view agrees): grey metal/stone grid, deep dark windows, ground-floor arcade.
    "westpark_office": ("Westpark grauer Bürobau", ["ID_89288E1A"], dict(wall="#94969a", seed=94, base_col="#6f7174", frame="#b9bcbf", glass="#27323b", sky="#7f929e", win=(2.0, 2.0, 0.75), bayw=4.2, fh=3.7, eg_h=4.4,
                    cornice=("#7e8084", 0.35, 0.4), floor_bands=("#80828a", 0.3, 0.4), parapet=0.6, lit=0.25, wall_stains=0.02)),
    # Badenerstrasse / Luggwegstrasse, south-west row (Panoramax 0e5e3f50 + 5621d338 agree): three Altbauten, 5 storeys, shutters, shops.
    "baden_sw_beige": ("Badenerstrasse SW-Zeile beige", ["ID_27919817"], dict(wall="#d8c6a6", seed=95, base_col="#8a8478", frame="#6c4a3c", win=(1.0, 1.55, 0.9), bayw=2.6, fh=3.0, eg_h=3.8, eg_kind="shop",
                    roof=("hip", "#6b4a40", 4.0), eave_rise=3.6, cornice=("#efe6d0", 0.35, 0.5))),
    "baden_sw_orange": ("Badenerstrasse SW-Zeile orange", ["ID_4C514B14"], dict(wall="#d9a070", seed=96, base_col="#8a8478", frame="#f0e8d8", win=(1.0, 1.55, 0.9), bayw=2.6, fh=3.0, eg_h=3.8, eg_kind="shop",
                    roof=("hip", "#6b4a40", 4.0), eave_rise=3.6, cornice=("#efe6d0", 0.35, 0.5))),
    "baden_sw_blue": ("Badenerstrasse SW-Zeile Eckhaus blaugrau", ["ID_867519A1"], dict(wall="#b4bac8", seed=97, base_col="#8a8a8e", frame="#eeeae0", win=(1.05, 1.6, 0.9), bayw=2.6, fh=3.0, eg_h=3.8, eg_kind="shop",
                    roof=("hip", "#5e4a44", 4.0), eave_rise=3.6, cornice=("#e8e4da", 0.35, 0.5))),
    # Badenerstrasse north side at the Luggweg crossing (Panoramax 0e5e3f50 right): cream new block, balconies, set-back top floor.
    "baden_n_cream": ("Badenerstrasse Neubau cremefarben", ["ID_6F450934", "ID_7C0F796F"], dict(wall="#e3d7bc", seed=98, base_col="#8f8a80", frame="#f4f0e6", win=(1.5, 1.7, 0.85), bayw=2.8, fh=3.1, eg_h=4.2, eg_kind="shop",
                    cornice=("#f2eee2", 0.3, 0.4), floor_bands=("#efe9d8", 0.25, 0.4), parapet=0.8)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        if k in DISABLED: continue
        _k4.block_model("z5R2_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
