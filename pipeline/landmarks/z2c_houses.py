"""Zone 2, area Limmat (Sihlquai / Limmatufer / Konradstrasse): landmark houses read from Mapillary/Panoramax/Commons photos
(research/zones/zone2_cam_photos.json, data/raw/photos/z2/*, protocol research/zones/z2/area_limmat.md). Colours estimated from the photos, no logos.
swissBUILDINGS3D ids from common.near() + footprint maps (photo poses are only +-15 m, headings up to 90 deg off): ids marked 'unsicher' in the protocol.
Registers into overrides/landmarks_z2c.json. Usage: python z2c_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z2c.json"
COMMON = dict(cols=2, rows=3, fh=3.1, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=3.8, eg_kind="shop", cornice=("#e9e2d0", 0.35, 0.45), roof=("flat", "#8a8884"), eave_rise=0.0, frame="#f1ede2", lit=0.3)
SPECS = {  # name: (title, ids, overrides)
    # Sihlquai: long 1930s school wing (Schule/Museum fuer Gestaltung), Mapillary 761147372637310, 941594731022316, 431034635954600: grey-green pebble-dash
    # facade, regular white-framed 3-pane window ribbons, 5-6 identical storeys, low plinth with cellar windows, flat roof
    "gewerbeschule": ("Sihlquai Gewerbeschule Ostfluegel (graugruener Kratzputz)", ["ID_455A74"], dict(wall="#a7ad9d", seed=91, base_col="#838a7c", frame="#f3f3ed", glass="#3a464e", win=(1.55, 1.9, 0.8), bayw=1.95, fh=3.55, eg_h=3.8, eg_kind="plain", cornice=("#9ba194", 0.25, 0.3), parapet=0.5, lit=0.2)),
    # Konradstrasse junction (Mapillary 4055613397840954, 316175953286688, Panoramax 2e4f2ad0): west corner cream-white upper floors on a terracotta-orange ground floor
    "konrad_w": ("Konradstrasse Eckhaus cremeweiss mit terrakottafarbenem EG", ["ID_055C8A"], dict(wall="#ece5d4", seed=92, base_col="#8a8478", eg_col="#cc6440", eg_h=4.0, frame="#f6f2e8", roof=("hip", "#6a5348", 5.0), eave_rise=4.6, awning=("#c8602f", 3.0, 1.0))),
    # north corner opposite (Panoramax 2e4f2ad0, right): pale yellow corner house, dark restaurant ground floor with white awning
    "konrad_n": ("Konradstrasse Eckhaus hellgelb mit Restaurant-EG", ["ID_DC194E"], dict(wall="#e9e0b6", seed=93, base_col="#8a8478", eg_col="#2f2d2b", eg_h=4.0, frame="#f6f2e8", roof=("hip", "#6a5348", 5.0), eave_rise=4.6, awning=("#eeeae0", 3.0, 1.0))),
    # Limmatufer / Sihlquai bridge end (Mapillary 1630790855, 8626332730, 5399634515, Panoramax 958a32): office blocks of the 1950s, grey-white and beige-grey
    # rendering, punched window groups, six storeys, arched courtyard passage in the beige one (ids unsicher)
    "ufer_white": ("Limmatquai Buerohaus grauweiss", ["ID_FE98C9"], dict(wall="#dbd9d1", seed=94, base_col="#8c8a84", frame="#f4f2ea", glass="#3f4b54", win=(1.45, 1.55, 0.9), bayw=2.2, fh=3.5, eg_h=3.8, eg_kind="plain", cornice=("#c9c6bd", 0.25, 0.3), parapet=0.5, lit=0.2)),
    "ufer_beige": ("Limmatquai Buerohaus beigegrau", ["ID_F50E29"], dict(wall="#d1c6ad", seed=95, base_col="#8c8678", frame="#f4f0e4", glass="#3f4b54", win=(1.5, 1.5, 0.9), bayw=2.3, fh=3.5, eg_h=3.8, eg_kind="plain", cornice=("#c4b9a0", 0.25, 0.3), parapet=0.5, lit=0.2)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z2c_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
