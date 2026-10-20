"""Zone 3, area Mitte (Bullingerplatz / Bullingerhof / Sihlfeldstrasse / Ernastrasse): landmark houses read from Mapillary/Panoramax photos
(research/zones/zone3_cam_photos.json, data/raw/photos/z3/*, protocol research/zones/z3/area_middle.md). Colours estimated from the photos, no logos.
swissBUILDINGS3D ids found with common.near() + footprint map (positions of the photos are only +-15 m). Registers into overrides/landmarks_z3b.json.
Usage: python z3b_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z3b.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=3.6, eg_kind="plain", cornice=("#cfc9bd", 0.3, 0.4), roof=("flat", "#8a8884"), eave_rise=0.0, frame="#f1ede2", lit=0.3)
SPECS = {  # name: (title, ids, overrides)
    # south end of Bullingerplatz (Mapillary 698579288902806, 1199284434377587): red-brick corner house, white plaster centre bay with gable, dark granite plinth, dark hip roof
    "brick_corner": ("Zypressenstrasse Eckhaus Backstein (Bullingerplatz)", ["ID_06F4F40D"], dict(wall="#a64d3c", seed=71, base_col="#4a4a4c", frame="#f3eee4", win=(1.1, 1.7, 0.85), bayw=2.6, roof=("hip", "#48403d", 6.0), eave_rise=5.6, cornice=("#ebe5d6", 0.35, 0.5), fh=3.1, eg_h=3.8)),
    # two small Heimatstil houses SE of the fountain (Mapillary 1444815882778112, 1186383535673317): ochre plaster, terracotta hip roof, three storeys
    "ochre_row": ("Bullingerplatz ockerfarbene Hausreihe", ["ID_145E5C84", "ID_A8C614F6"], dict(wall="#dcc995", seed=72, base_col="#9d8a68", frame="#f4f0e4", win=(1.05, 1.5, 0.9), bayw=2.6, roof=("hip", "#8f4a36", 4.6), eave_rise=4.3, cornice=("#efe5c8", 0.3, 0.4), fh=3.0, eg_h=3.3)),
    # round pavilion west of Bullingerplatz (Mapillary 1155629122273388): white rough plaster, big windows, flat roof
    "pavilion": ("Rundpavillon westlich Bullingerplatz", ["ID_090BB9FA"], dict(wall="#ebe7dc", seed=73, base_col="#b8b4aa", frame="#d8d6cf", win=(1.7, 1.8, 0.8), bayw=3.0, rows=2, eg_h=4.2, roof=("flat", "#8a8884"), cornice=None, parapet=0.35)),
    # low white volume with window band west of the round pavilion (same photo, right side)
    "pavilion_low": ("Flachbau westlich Bullingerplatz", ["ID_1D4E9A12"], dict(wall="#ebe7dc", seed=76, base_col="#b8b4aa", frame="#d8d6cf", win=(1.2, 1.1, 1.1), bayw=2.0, rows=1, fh=3.2, eg_h=0, roof=("flat", "#8a8884"), cornice=None, parapet=0.3)),
    # long three-storey main building of the Bullingerhof estate, far centre of Mapillary 1155629122273388: cream plaster, dark grey hip roof (colour only, weak evidence for the id)
    "bhof_main": ("Bullingerhof Hauptbau", ["ID_CC508A03"], dict(wall="#e4dcc4", seed=77, base_col="#a8a08c", frame="#f0ece2", win=(1.1, 1.5, 0.9), bayw=2.6, roof=("hip", "#4a4846", 4.0), eave_rise=3.8, cornice=("#d8d0b8", 0.3, 0.4), fh=3.0, eg_h=3.2)),
    # Sihlfeldstrasse north side (Mapillary 1121383229223286, 1121408482694988): pink-beige 5-storey block, ribbon windows, glazed ground floor, flat roof
    "sihlfeld_pink": ("Sihlfeldstrasse rosa Wohnblock", ["ID_07C92BCE"], dict(wall="#d9c3b6", seed=74, base_col="#8c8077", frame="#e9e5dc", win=(2.0, 1.25, 1.0), bayw=2.8, eg_kind="shop", eg_h=4.0, fh=3.1, cornice=("#c8bdb2", 0.3, 0.35), parapet=0.5)),
    # Ernastrasse east corner (Panoramax 73c4d772): cream-beige corner house with two balcony bays
    "erna_corner": ("Ernastrasse beiges Eckhaus", ["ID_DED0B869"], dict(wall="#e6d2ae", seed=75, base_col="#9c9078", frame="#f4f0e6", win=(1.1, 1.75, 0.85), bayw=2.6, roof=("hip", "#7d6a5e", 5.0), eave_rise=4.6, cornice=("#f0e8d4", 0.35, 0.5), fh=3.1)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z3b_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
