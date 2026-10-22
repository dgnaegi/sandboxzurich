"""Zone 1 landmark round (HB und Langstrasse camera points): landmark houses read from Mapillary/Panoramax photos
(research/zones/zone1_cam_photos.json, data/raw/photos/z1/*, protocol research/zones/z1/area_landmarks.md). Colours estimated from the photos, no logos.
swissBUILDINGS3D ids from common.near()/footprint map. Registers into overrides/landmarks_z1L.json.
Usage: python z1L_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z1L.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=3.6, eg_kind="plain", cornice=("#cfc9bd", 0.3, 0.4), roof=("flat", "#8a8884"), eave_rise=0.0, frame="#f1ede2", lit=0.3)
SPECS = {  # name: (title, ids, overrides)
    # Bahnhofplatz west side, north block (Mapillary 2024 h160 + 2019): grey-green stone-panel 1960s block, paired vertical windows with dark green frames, glazed ground floor with red awning band; game had a granite Gruenderzeit block
    "bahnhofplatz_teal": ("Bahnhofplatz graugruener Geschaeftsbau", ["ID_CBA646B8"], dict(wall="#82948f", seed=91, base_col="#5f6b68", frame="#33423e", glass="#2a363a", win=(1.0, 1.75, 0.95), bayw=2.4, fh=3.5, eg_h=4.6, eg_kind="shop", cornice=("#6f7f7a", 0.25, 0.3), parapet=0.5, awning=("#c4302e", 3.7, 0.5), roof=("flat", "#76797a"))),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z1L_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
