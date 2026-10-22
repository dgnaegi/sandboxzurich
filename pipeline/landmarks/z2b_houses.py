"""Zone 2 area Josef (Josefwiese / Roentgenplatz / Heinrichstrasse): landmark houses read from Mapillary/Panoramax/Commons photos
(research/zones/zone2_cam_photos.json, data/raw/photos/z2/*, protocol research/zones/z2/area_josef.md). Colours estimated from the photos, no logos.
swissBUILDINGS3D ids found with common.near() + footprint map (photo positions only +-15 m). Registers into overrides/landmarks_z2b.json.
Usage: python z2b_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z2b.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=3.6, eg_kind="plain", cornice=("#cfc9bd", 0.3, 0.4), roof=("flat", "#8a8884"), eave_rise=0.0, frame="#f1ede2", lit=0.3)
SPECS = {  # name: (title, ids, overrides)
    # Josefwiese south edge (Commons Max Vogt 2024 x3 + Mapillary 1055319798323957): 10-storey slab, pale blue-grey panel cladding, vertical stair strip, balcony ribbons, flat roof
    "josef_slab": ("Josefwiese blaugrauer Plattenbau", ["ID_2FD78AE0"], dict(wall="#b7c0cb", seed=81, base_col="#7d848c", frame="#dde2e8", win=(0.9, 1.0, 1.1), bayw=3.0, eg_h=0, fh=3.2, cornice=("#a2abb5", 0.25, 0.3), floor_bands=("#9ba5b0", 0.22, 0.35), parapet=0.5, roof=("flat", "#7a7d80"))),
    # Josefwiese pavilion at the viaduct foot (Commons Josefswiese.jpg, Josefswiese2.jpg): single storey, whitewashed walls, dark brown hip roof
    "josef_pavilion": ("Josefwiese Pavillon", ["ID_9EE8989A"], dict(wall="#eae4d6", seed=82, base_col="#8c867a", frame="#5a4a40", win=(1.3, 1.5, 0.9), bayw=3.0, rows=1, eg_h=0, fh=3.0, cornice=None, roof=("hip", "#5b4a42", 2.6), eave_rise=4.6)),
    # Roentgenplatz west side (Mapillary 0, 1, 5, 6, 10; Panoramax 2024): orange-ochre Heimatstil blocks with brown balconies, red-brown hip roof; game had lavender
    "roent_west": ("Roentgenplatz Westseite ocker", ["ID_3236D5D0", "ID_03CFE3C7", "ID_FAD7E0C1"], dict(wall="#e0b77a", seed=83, base_col="#a88c62", frame="#f4ecd8", win=(1.05, 1.5, 0.9), bayw=2.7, roof=("hip", "#8f4b38", 4.4), eave_rise=4.4, cornice=("#efe2c0", 0.3, 0.45), fh=3.1, eg_h=3.4)),
    # Heinrichstrasse south-west block (Panoramax dcfbb455 2024, Mapillary 369047507861306): big cream stone-clad block, tall glass strips, dark green gates at ground floor, flat roof
    "heinrich_cream": ("Heinrichstrasse cremefarbener Grossblock", ["ID_38F02D4E"], dict(wall="#e8e2d4", seed=84, base_col="#566056", frame="#c9cfce", glass="#3a4a52", win=(1.9, 2.1, 0.7), bayw=3.4, fh=3.5, eg_h=4.6, eg_kind="plain", cornice=("#d6d0c2", 0.3, 0.3), parapet=0.6, roof=("flat", "#7d7c78"), lit=0.25)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z2b_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
