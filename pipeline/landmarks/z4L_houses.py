"""Zone 4 landmark round (agent z4L): landmark houses at the 16 camera points of Wiedikon, read from Mapillary/Panoramax/Commons photos
(research/zones/zone4_cam_photos.json, data/raw/photos/z4/*, protocol research/zones/z4/area_landmarks.md). Colours estimated from the photos, no logos.
swissBUILDINGS3D ids from footprint maps around each camera point (photo poses only +-15 m, heading up to 90 deg off). Registers into overrides/landmarks_z4L.json.
Usage: python z4L_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z4L.json"
COMMON = dict(cols=2, rows=3, fh=3.0, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=3.8, eg_kind="plain", cornice=("#e9e2d0", 0.35, 0.45), roof=("hip", "#5d5f61", 5.0), eave_rise=4.6, frame="#f1ede2", lit=0.3)
SPECS = {  # name: (title, ids, overrides)
    # Bertastrasse/Idastrasse crossing, north corner (Mapillary 0/1/2 at cam 2+4, Panoramax): ochre-apricot corner house with round bay, salmon-pink stone ground floor, dark mansard
    "berta_corner": ("Bertastrasse Eckhaus Erkerturm aprikose", ["ID_73CE65F7"], dict(wall="#e2b98f", seed=91, base_col="#c79a86", cornice=("#f0dfc4", 0.4, 0.5))),
    # Zurlindenstrasse / Steinstrasse (Ortsmuseum point, Mapillary 15.0-15.2): curved 1930s block, orange-brown plaster, cream balcony ribbons, flat roof
    "curved_stein": ("Steinstrasse geschwungener Wohnblock", ["ID_39E73AF7", "ID_3C0C73EF", "ID_294CDD5E", "ID_212C768A"], dict(wall="#c99468", seed=92, base_col="#8f6a50", frame="#f3ead7", win=(1.7, 1.2, 1.0), bayw=3.3, floor_bands=("#eadfc7", 0.28, 0.4), eg_h=3.6, cornice=("#eadfc7", 0.3, 0.4), parapet=0.5, roof=("flat", "#85705f"), eave_rise=0.0)),
    "curved_stein_w": ("Steinstrasse geschwungener Wohnblock West", ["ID_F8D774F8", "ID_F5A9251E", "ID_B056B3A7", "ID_F939C481"], dict(wall="#c99468", seed=100, base_col="#8f6a50", frame="#f3ead7", win=(1.7, 1.2, 1.0), bayw=3.3, floor_bands=("#eadfc7", 0.28, 0.4), eg_h=3.6, cornice=("#eadfc7", 0.3, 0.4), parapet=0.5, roof=("flat", "#85705f"), eave_rise=0.0)),
    # Kalkbreite point (Commons 16.2 + Mapillary): detached white house with dark shutters and steep dark hip roof beside the tram crossing
    "kalk_house": ("Kalkbreite weisses Haus mit Fensterlaeden", ["ID_9C8144E4"], dict(wall="#efece4", seed=93, base_col="#8c867c", frame="#4a3b33", win=(1.0, 1.6, 0.9), bayw=2.8, eg_h=0, cornice=None, roof=("hip", "#4b3a34", 5.0), eave_rise=4.4)),
    # Schmiede Wiedikon (Mapillary 11.1/11.2, 2024/25): grey-white balcony block over the Migros ground floor, concrete balcony slabs, flat roof
    "migros_block": ("Birmensdorferstrasse grauweisser Balkonblock", ["ID_F1D13DBA", "ID_13D1BD0B", "ID_4FF1E905"], dict(wall="#d7d4cd", seed=94, base_col="#7d7a74", frame="#eeeeea", glass="#3c4650", win=(1.3, 1.5, 0.9), bayw=3.0, floor_bands=("#f0efea", 0.3, 0.45), eg_h=4.4, cornice=("#cfccc4", 0.3, 0.3), parapet=0.5, roof=("flat", "#76777a"), eave_rise=0.0)),
    # Zurlindenstrasse West (Mapillary 8.0/8.1/8.3): cream corner house with red-brown shutters + mansard, long low cream school hall opposite
    "zurl_cream": ("Zurlindenstrasse cremefarbenes Eckhaus Mansarde", ["ID_E8B3B705", "ID_EE5026FA"], dict(wall="#ece3cc", seed=95, base_col="#9a9080", frame="#7d4235", cornice=("#f4efe0", 0.35, 0.5), roof=("hip", "#4f4c4a", 5.0), eave_rise=4.6)),
    "zurl_hall": ("Zurlindenstrasse langer Putzbau creme", ["ID_E0E3141D"], dict(wall="#e6e0cd", seed=96, base_col="#8f8a7c", frame="#f3f1e8", win=(2.2, 1.7, 0.9), bayw=3.4, fh=3.8, eg_h=0, cornice=None, parapet=0.4, roof=("flat", "#8b8a86"), eave_rise=0.0)),
    # Thomasweg (Mapillary 10.0/10.2): NE row salmon-pink Gruenderzeit, SW 1960s block cream-grey with stacked balconies
    "thomas_pink": ("Thomasweg lachsrosa Zeile", ["ID_FF32AF40", "ID_0A1E597D"], dict(wall="#dba899", seed=97, base_col="#a37f72", cornice=("#f1e4d4", 0.4, 0.5), roof=("hip", "#6a4a40", 5.0), eave_rise=4.6)),
    "thomas_pink2": ("Thomasweg hellrosa Zeile", ["ID_8B58C21D", "ID_3047D6E4"], dict(wall="#e8c3a6", seed=98, base_col="#a58a74", cornice=("#f4ead8", 0.4, 0.5), roof=("hip", "#6a4a40", 5.0), eave_rise=4.6)),
    "thomas_slab": ("Thomasweg cremegrauer Balkonblock", ["ID_77853EEB"], dict(wall="#d9d4c8", seed=99, base_col="#86817a", frame="#e9e6de", win=(1.3, 1.5, 0.9), bayw=3.0, floor_bands=("#b8b4ac", 0.22, 0.4), eg_h=3.8, parapet=0.5, roof=("flat", "#7a7a78"), eave_rise=0.0)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z4L_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
