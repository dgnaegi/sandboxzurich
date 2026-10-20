"""Zone 5, Bahnhof Altstetten: landmark houses read from Mapillary/Panoramax street views at the camera points
(research/zones/zone5_cam_photos.json, notes research/zones/z5/area_station.md). Colours are estimates from the photos; no logos.
Registers into overrides/landmarks_z5a.json. Usage: python z5a_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z5a.json"
SPECS = {  # name: (title, ids, kwargs)
    # Migros/Activ-Fitness-Bau Altstetterstrasse: hellgrauer Betonbau, Fensterbaender, gerundete SO-Ecke, Erdgeschoss verglast
    "migros": ("Altstetterstrasse Bandfassaden-Bau (Aktiv Fitness)", ["ID_A35B08F6"],
               dict(wall="#cdc9bd", frame="#8d908e", glass="#4d6665", sky="#9bb4b8", cols=1, rows=2, fh=3.45, bayw=3.1, win=(2.75, 1.55, 0.85), eg_h=4.8, eg_kind="shop",
                    eg_col="#3a3f42", base_col="#7c7b76", cornice=("#e4e1d6", 0.35, 0.45), floor_bands=("#e2dfd3", 0.55, 0.45), roof=("flat", "#7b7a76"), parapet=0.8, seed=151, lit=0.3)),
    # ABZ-Wohnbau (1985) an der Altstetterstrasse: rotbrauner Backstein, vorgesetzte Stahlgalerien
    "abz": ("Altstetterstrasse ABZ-Backsteinbau", ["ID_2B880E23"],
            dict(wall="#8f4d3d", frame="#2f3335", glass="#35424c", sky="#8aa0ae", cols=3, rows=2, fh=3.0, bayw=3.2, win=(1.5, 1.3, 0.9), eg_h=3.2, eg_kind="plain",
                 base_col="#6f6a63", cornice=("#4a4846", 0.3, 0.4), floor_bands=("#3d4144", 0.3, 0.6), roof=("flat", "#5f605e"), parapet=0.5, seed=152, lit=0.3, wall_stains=0.02)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z5a_" + k, title, ids, **kw)


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
