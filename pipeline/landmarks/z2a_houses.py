"""Zone 2 area a (Escher-Wyss-Platz / Turbinenplatz / Hardbruecke): landmark houses read from Mapillary/Commons photos
(research/zones/zone2_cam_photos.json, data/raw/photos/z2/*, protocol research/zones/z2/area_hardbruecke.md). Colours estimated from the photos, no logos/shop names.
swissBUILDINGS3D ids found with common.near() + footprint map. Registers into overrides/landmarks_z2a.json.
Usage: python z2a_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z2a.json"
COMMON = dict(cols=2, rows=3, fh=3.2, bayw=2.6, win=(1.2, 1.6, 0.9), eg_h=3.8, eg_kind="plain", cornice=("#cfc9bd", 0.3, 0.4), roof=("flat", "#8a8884"), eave_rise=0.0, frame="#f1ede2", lit=0.3)
SPECS = {  # name: (title, ids, overrides)
    # Turbinenplatz west side (Mapillary 2022 x5, Commons 2019 'TECHNOPARK' view): long 6-storey wing, blue-grey panels, light balcony slabs per storey, open glazed ground floor, flat roof (game had blue curtain wall)
    "technopark_wing": ("Technopark Westfluegel (Turbinenplatz)", ["ID_D75595"], dict(wall="#58626c", seed=81, simp=2.0, min_area=80, base_col="#6e7073", frame="#dcdad3", glass="#3a4650", win=(1.9, 1.15, 1.0), bayw=3.0, fh=3.4, eg_h=4.2, eg_kind="shop",
                    cornice=("#c9c7c0", 0.3, 0.45), floor_bands=("#c4c2bc", 0.5, 0.6), roof=("flat", "#7a7a78"), parapet=0.5, lit=0.2)),
    # south side of Turbinenplatz (Commons 2021/2019 + Mapillary 2022 d29 h187): hotel, 6 storeys dark navy cladding, white-framed wide windows, glazed ground floor
    "novotel": ("Hotel am Turbinenplatz (Sued)", ["ID_892840"], dict(wall="#2d3544", seed=82, base_col="#23272e", frame="#e8ebee", glass="#3d4a5c", win=(1.9, 1.35, 0.85), bayw=3.0, fh=3.2, eg_h=4.0, eg_kind="shop",
                    cornice=None, floor_bands=("#3b4558", 0.12, 0.25), roof=("flat", "#4c4e52"), parapet=0.4, lit=0.45)),
    # NW of Escher-Wyss-Platz (Mapillary 2024 h338/h340 from the bridge ramp): long cream 3-storey block, ribbon of small windows, blue awnings at the ground floor, dark flat hip roof
    "ewp_nw_row": ("Escher-Wyss-Platz Nordwest Zeile", ["ID_C6E83B"], dict(wall="#e4dccb", seed=83, base_col="#a9a396", frame="#f3f0e8", win=(1.1, 1.4, 0.95), bayw=2.4, fh=3.0, eg_h=3.4, eg_kind="shop",
                    cornice=("#d9d1bf", 0.25, 0.35), roof=("hip", "#6a625c", 3.0), eave_rise=2.8, awning=("#2f5d9a", 3.1, 0.7))),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z2a_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
