"""Zone 3 round 2 (Kreis 4 Mitte): colour/height/roof/window-grid landmarks for the weakest camera points
(Brauerstrasse West, Erismannhof, Zypressenstrasse). Photos: research/zones/zone3_cam_photos.json, data/raw/photos/z3/*, protocol research/zones/z3/round2.md.
swissBUILDINGS3D ids via common.near() + footprint map; colours estimated from the photos, no logos.
Registers into overrides/landmarks_z3R2.json. Usage: python z3R2_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z3R2.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=3.6, eg_kind="plain", cornice=("#cfc9bd", 0.3, 0.4), roof=("flat", "#8a8884"), eave_rise=0.0, frame="#f1ede2", lit=0.3)
BRAU = dict(wall="#e3d9c2", seed=81, base_col="#8d8678", frame="#dcd8cc", win=(1.6, 1.35, 0.85), bayw=2.8, fh=3.1, eg_kind="shop", eg_h=4.2, cornice=("#d2c8b0", 0.3, 0.4),
            floor_bands=("#d9cfb8", 0.85, 0.2), roof=("flat", "#7d7b78"), parapet=0.55, curtains=[(232, 228, 216), (190, 186, 176), (150, 150, 146)])
ERIS = dict(wall="#e4c688", base_col="#a8997a", frame="#7f95a3", surround="#ecdfb4", win=(1.0, 1.5, 0.9), bayw=2.5, fh=3.1, eg_h=3.3, eg_kind="plain", cornice=("#ead9a8", 0.3, 0.35),
            floor_bands=("#d2b97a", 0.06, 0.25), roof=("hip", "#8c4a3a", 6.0), eave_rise=6.0, wall_stains=0.02, lit=0.3)
SPECS = {  # name: (title, ids, overrides)
    # Brauerstrasse bend, north arc incl. round corner (Mapillary 1146949566206965 / 2532352523600586 / 364198516329610): cream plaster, continuous balcony slabs, glazed EG, flat roof
    "brau_n": ("Brauerstrasse Bogen Nord (Balkonblock)", ["ID_2D0EE768", "ID_02E63929", "ID_FCCA3186", "ID_0CAB36AA", "ID_4E17324F", "ID_B7092D2D"], dict(BRAU, seed=81)),
    # south arc (same photos, 1394859187776249 on the right): same cream plaster, balcony bands
    "brau_s": ("Brauerstrasse Bogen Sued (Balkonblock)", ["ID_8A4DC12B", "ID_CFB8EB2D", "ID_5B218972"], dict(BRAU, seed=82, wall="#e6dcc6")),
    # SW row Brauerstrasse (Mapillary 364198516329610 right, 886729676872277): near-white cream block with balconies
    "brau_row": ("Brauerstrasse Zeile Sued (Balkonblock)", ["ID_F64C47E7", "ID_D8B9722B", "ID_DD9D80A9", "ID_917BF92B"], dict(BRAU, seed=83, wall="#ece5d4", floor_bands=("#e0d8c4", 0.8, 0.2))),
    # Erismannhof (ABZ Genossenschaft 1920s): ochre-yellow plaster, grey-blue shutters (frame colour), dark red hip roofs (Mapillary 1328722922382564 .. 800156825722845)
    "eris_w": ("Erismannhof West/Sued", ["ID_E00341F6", "ID_459BC898", "ID_4928F4C9", "ID_E519C7CB", "ID_9213CCA0", "ID_6E3465BC"], dict(ERIS, seed=84)),
    "eris_e": ("Erismannhof Ost", ["ID_B100545B", "ID_2327183A", "ID_1DFDAA59", "ID_D930E6B4", "ID_04A411BD", "ID_FFE80347"], dict(ERIS, seed=85)),
    "eris_n": ("Erismannhof Nord", ["ID_4714C360", "ID_8DC0297D", "ID_48D49CB0", "ID_ADD4C771"], dict(ERIS, seed=86)),
    # Zypressenstrasse NW row (Mapillary 783653180485285, 2425725217612512): beige plaster, grey-green shutters/bay frames, low roof
    "zyp_nw": ("Zypressenstrasse Zeile Nordwest", ["ID_FC00114C", "ID_58A9E0BF", "ID_37B723BB"], dict(wall="#dcd0b4", seed=87, base_col="#9a9080", frame="#8c9a94", surround="#e8e0cc", win=(1.2, 1.6, 0.9), bayw=2.6, fh=3.1,
        eg_h=3.5, cornice=("#e4dcc6", 0.3, 0.4), roof=("hip", "#6a5f58", 3.2), eave_rise=3.0)),
    # yellow house west of the red brick corner (Mapillary 698579288902806): yellow plaster, dark balconies, hip roof
    "zyp_yellow": ("Zypressenstrasse gelbes Haus", ["ID_D9D49985"], dict(wall="#e4d38f", seed=88, base_col="#9a9070", frame="#f3eedc", win=(1.1, 1.7, 0.85), bayw=2.6, fh=3.1, eg_h=3.5, cornice=("#efe5c0", 0.3, 0.4), roof=("hip", "#5a504a", 4.6), eave_rise=4.2)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z3R2_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
