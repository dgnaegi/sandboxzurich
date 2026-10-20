"""Zone 5 (Altstetten), area Lindenplatz / Altstetterstrasse / Hohlstrasse / Baslerstrasse: landmark houses from Commons + Mapillary/Panoramax photos
(research/zones/zone5_cam_photos.json, protocol research/zones/z5/area_linden.md). Colours estimated from the photos. Shop names only where
readable in a photo (Coop, Spirgarten). swissBUILDINGS3D ids found via the footprint map (research/zones/z5/ + common.near).
Registers into overrides/landmarks_z5b.json. Usage: python z5b_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z5b.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=4.2, eg_kind="shop", cornice=("#e9e2d0", 0.4, 0.5), roof=("hip", "#5d5f61", 5.0), eave_rise=4.6, frame="#f1ede2", lit=0.35)
SPECS = {  # name: (title, ids, overrides)
    # Hotel/Restaurant Spirgarten + Coop (Badenerstrasse 681): salmon-orange 1950s block, strip windows, glazed ground floor (Commons Welti_Spirgarten, Mapillary 498123644871495)
    "spirgarten": ("Badenerstrasse 681 Spirgarten/Coop", ["ID_85DB372F"], dict(wall="#d4856a", seed=81, base_col="#8f8a82", frame="#f4f1ea", win=(2.0, 1.3, 0.95), bayw=2.9, fh=3.3, eg_h=4.4,
                   roof=("hip", "#7c746e", 3.0), eave_rise=2.6, cornice=("#f1ece0", 0.6, 0.6))),   # SWISSIMAGE: low dark hip roof; hip works again (hip_roof rebuilt, T-S1 fixed)
    # Altstetterstrasse 150/152: tan plastered 5-storey row with shops (Mapillary 1157056783007138 / 687999557132870)
    "altst150": ("Altstetterstrasse 150 beiges Ladenhaus", ["ID_03A21443"], dict(wall="#e7d8b0", seed=82, base_col="#8a8478", roof=("hip", "#4b4440", 4.5))),
    "altst152": ("Altstetterstrasse 152 beiges Ladenhaus", ["ID_7E84243E"], dict(wall="#ebdcb4", seed=83, base_col="#8a8478", roof=("hip", "#4b4440", 4.5))),
    # Badenerstrasse 672 round corner house, yellow-ochre with red hip roof (far end of the Altstetterstrasse view)
    "baden672": ("Badenerstrasse 672 Eckhaus rotes Dach", ["ID_44D57742"], dict(wall="#e3c88f", seed=84, base_col="#8a8478", roof=("hip", "#a4452f", 5.0), eave_rise=5.4, cornice=("#f1e9d4", 0.45, 0.5))),
    # Altstetterstrasse east side: light-grey modern slab houses with white balcony bands
    "altst149": ("Altstetterstrasse 149 graues Wohnhaus", ["ID_4FFE24FC"], dict(wall="#d4d3cd", seed=85, base_col="#8a8a86", roof=("flat", "#8a8780"), eave_rise=0.0, win=(1.5, 1.45, 0.85), bayw=2.7, fh=3.0, cornice=("#f2f1ec", 0.35, 0.4))),
    "altst147": ("Altstetterstrasse 147 graues Wohnhaus", ["ID_65AB9E2D"], dict(wall="#d9d8d2", seed=86, base_col="#8a8a86", roof=("flat", "#8a8780"), eave_rise=0.0, win=(1.5, 1.45, 0.85), bayw=2.7, fh=3.0, cornice=("#f2f1ec", 0.35, 0.4))),
    # Hohlstrasse (Altstetten) near Letzipark: red-brick former factory with tall arched steel windows (Mapillary 514605241324304 / 795050989783909, sign "Komplex")
    "hohl_brick": ("Hohlstrasse Backsteinfabrik", ["ID_72D5F120"], dict(wall="#9a4d3a", seed=87, base_col="#7d6a5c", frame="#e9e4d8", glass="#2b343c", arch=True, win=(1.5, 3.4, 0.9), bayw=3.6, fh=5.4, eg_h=5.0, eg_kind="arch",
                   roof=("flat", "#6d6a66"), eave_rise=0.0, cornice=("#cbb9a2", 0.4, 0.4), parapet=0.5)),
    # Hohlstrasse 459/465 (Letzipark side): long cream slab, ribbon windows, open parking arcade at ground floor (Mapillary 1971266673697893)
    "hohl_letzi": ("Hohlstrasse 459 Buerohaus Letzipark", ["ID_D5030418"], dict(wall="#e8dfc8", seed=88, base_col="#8f8a80", frame="#f6f3ea", win=(2.1, 1.25, 0.95), bayw=2.8, fh=3.5, eg_h=4.6, eg_kind="shop",
                   roof=("flat", "#8a8780"), eave_rise=0.0, cornice=("#f4f0e4", 0.5, 0.4), parapet=0.5, eg_col="#4a4743")),
    # Flurstrasse 2 / Hohlstrasse junction: cream 9-storey slab, white balcony slabs form a grid (Mapillary 974017061161906 + 436475452826573 agree)
    "flur_block": ("Flurstrasse 2 weisses Balkonhaus", ["ID_42C70DE5"], dict(wall="#e2ddd0", seed=89, base_col="#8f8c85", frame="#f4f2ec", win=(1.35, 1.7, 0.85), bayw=2.4, fh=3.1, eg_h=4.0,
                   roof=("flat", "#8a8780"), eave_rise=0.0, cornice=("#f4f2ec", 0.3, 0.4), floor_bands=("#f3f1ea", 0.28, 0.55), parapet=0.9)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z5b_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
