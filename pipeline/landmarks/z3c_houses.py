"""Zone 3 (Kreis 4 Mitte), area west/north: landmark houses at Zypressenstrasse, Hardstrasse/Bullingerstrasse, Albisriederplatz,
Hardplatz / Hohlstrasse. Colours estimated from Mapillary/Panoramax photos (research/zones/zone3_cam_photos.json, data/raw/photos/z3/*);
no logos, no names. swissBUILDINGS3D ids via the colour-coded footprint map (research/zones/z3/area_west.md).
Registers into overrides/landmarks_z3c.json. Usage: python z3c_houses.py [name,name]"""
import sys
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z3c.json"
HIP = lambda col, rise=5.0: ("hip", col, rise)
COMMON = dict(cols=2, rows=3, fh=3.1, bayw=2.5, win=(1.15, 1.75, 0.85), eg_h=4.0, eg_kind="shop", cornice=("#e9e2d0", 0.4, 0.5), roof=HIP("#6a625e"), eave_rise=4.6, frame="#f1ede2", lit=0.35, base_col="#8f8a80")
SPECS = {  # name: (title, ids, overrides)
    # Zypressenstrasse / Badenerstrasse (Mapillary 2023-25 dashcam, Panoramax): light-blue corner house with blue shutters, shop at the corner
    "zy_endi": ("Zypressenstrasse hellblaues Eckhaus", ["ID_9AD3B91C"], dict(wall="#bdd0e6", seed=101, frame="#3a6aa8", eave_rise=5.2, roof=HIP("#6c6a6c"), cornice=("#f1f1ec", 0.35, 0.45), eg_col="#2f3234")),
    "zy_pink": ("Zypressenstrasse rosa-weisses Haus", ["ID_2D81AF8B"], dict(wall="#e8d8d3", seed=102, frame="#f3efe8", roof=HIP("#7d5448"), eave_rise=4.4)),
    "zy_se": ("Badenerstrasse Eckhaus grau (Zypressenstrasse Ost)", ["ID_32F49980"], dict(wall="#cfccc3", seed=103, frame="#8d9398", roof=HIP("#6b6460", 5.5), eave_rise=5.0, cornice=("#e4e0d4", 0.4, 0.5))),
    "zy_s1": ("Badenerstrasse weisses Haus mit grauen Laeden", ["ID_AA8A4CD3"], dict(wall="#e8e6df", seed=104, frame="#8d9398", roof=HIP("#6b6460"), eave_rise=4.6, floor_bands=("#d9d6cc", 0.25, 0.5))),
    "zy_s2": ("Badenerstrasse weisses Haus 2", ["ID_26FB7E34"], dict(wall="#e6e4dc", seed=105, frame="#8d9398", roof=HIP("#6b6460"), eave_rise=4.6)),
    "zy_ne": ("Badenerstrasse ockerfarbenes Eckhaus", ["ID_70C160EA"], dict(wall="#d9ba86", seed=106, frame="#f3efe6", roof=HIP("#4f4a48", 5.5), eave_rise=5.4, cornice=("#efe3c8", 0.4, 0.5))),
    # Hardstrasse / Bullingerstrasse: rose-red corner house, white and yellow neighbours (photos 2015-2024, Mapillary)
    "hb_red": ("Hardstrasse/Bullingerstrasse rotes Eckhaus", ["ID_1ED7BBD6"], dict(wall="#c8737b", seed=111, frame="#f3efe8", roof=HIP("#5b5553"), eave_rise=4.6, cornice=("#efe9de", 0.35, 0.45))),
    "hb_white": ("Hardstrasse weisses Haus", ["ID_74F4FB69"], dict(wall="#ebe8e0", seed=112, frame="#f3efe8", roof=HIP("#5b5553"), eave_rise=4.6)),
    "hb_cream": ("Bullingerstrasse cremeweisses Haus", ["ID_6FB491AB"], dict(wall="#e3e0d8", seed=113, frame="#f3efe8", roof=HIP("#5b5553"), eave_rise=4.6)),
    "hb_pale": ("Hardstrasse hellgelbes Haus", ["ID_21C561B8"], dict(wall="#e8dfb8", seed=114, frame="#f3efe8", roof=HIP("#5b5553"), eave_rise=4.6)),
    "hb_yellow": ("Hardstrasse gelbes Eckhaus mit Balkonen", ["ID_1F784F3E"], dict(wall="#e2b45c", seed=115, frame="#f3efe8", roof=HIP("#6a5048", 5.5), eave_rise=5.0, floor_bands=("#d8a24a", 0.2, 0.55))),
    "hb_peach": ("Hardstrasse pfirsichfarbenes Haus", ["ID_F972B450"], dict(wall="#e7cda4", seed=116, frame="#f3efe8", roof=HIP("#6a5048"), eave_rise=4.6)),
    "hb_ochre": ("Hardstrasse ockerfarbenes Haus", ["ID_7799E92B"], dict(wall="#e0b97c", seed=117, frame="#f3efe8", roof=HIP("#6a5048"), eave_rise=4.6)),
    "hb_sw1": ("Hardstrasse cremegelbes Eckhaus SW", ["ID_CDE387C9"], dict(wall="#e6d9a8", seed=118, frame="#f3efe8", roof=HIP("#6a5048", 5.5), eave_rise=5.0)),
    "hb_sw2": ("Bullingerstrasse cremegelbes Haus", ["ID_8B7AD8F5"], dict(wall="#e8dcb8", seed=119, frame="#f3efe8", roof=HIP("#6a5048"), eave_rise=4.6)),
    # Albisriederplatz: grey 1950s block with Apotheke arcade (SW), blue-grey and yellow houses on the NW side, salmon/ochre houses on the south side
    "al_apo": ("Albisriederplatz graues Geschaeftshaus", ["ID_D4E1A40D"], dict(wall="#d0cbbd", seed=121, frame="#f4f1ea", win=(1.7, 1.3, 0.95), bayw=2.9, fh=3.2, eg_h=4.6, roof=("flat", "#8a8780"), eave_rise=0.0, floor_bands=("#b8b3a6", 0.3, 0.55), cornice=("#b0ab9e", 0.35, 0.4), parapet=0.5)),
    "al_nw_blue": ("Albisriederplatz blaugraues Haus", ["ID_C0AA6D7C"], dict(wall="#8f9bad", seed=122, frame="#e9e6de", roof=HIP("#6b5a54", 5.5), eave_rise=5.0, cornice=("#d7d3c8", 0.4, 0.5))),
    "al_nw_yellow": ("Albisriederplatz gelbes Haus", ["ID_161C02B5"], dict(wall="#e6d68e", seed=123, frame="#f1ede2", roof=HIP("#6b5a54", 5.5), eave_rise=5.0)),
    "al_s_pink": ("Albisriederplatz lachsfarbenes Haus", ["ID_9CE0B083"], dict(wall="#e2b6a4", seed=124, frame="#f1ede2", roof=HIP("#7a4a3e", 5.5), eave_rise=5.0)),
    "al_s_ochre": ("Albisriederplatz ockergelbes Haus", ["ID_03B78CB2"], dict(wall="#e6cf90", seed=125, frame="#f1ede2", roof=HIP("#6b5a54"), eave_rise=4.6)),
    "al_s_cream": ("Albisriederplatz cremefarbenes Haus", ["ID_F6F5122D"], dict(wall="#e8dcc2", seed=126, frame="#f1ede2", roof=HIP("#6b5a54"), eave_rise=4.6)),
    # Hardplatz S side, W to E (Mapillary beat 2019 tram-loop photos + 2024): orange-brick house, lilac-grey corner house, white house with hip roof, red-brick block; W side big white house with red roofs
    "hp_brickw": ("Hardplatz Backsteinhaus West", ["ID_7A68C4A5"], dict(wall="#b8694e", seed=132, frame="#efe9de", roof=HIP("#7a4a3e", 5.5), eave_rise=5.0, cornice=("#d8cdbb", 0.3, 0.4))),
    "hp_lilac": ("Hardplatz fliederfarbenes Eckhaus", ["ID_60A5511C"], dict(wall="#cbcad2", seed=131, frame="#f4f1ea", roof=HIP("#6b605a", 5.5), eave_rise=5.0, cornice=("#ece8de", 0.4, 0.5))),
    "hp_whitehip": ("Hardplatz weisses Haus mit Walmdach", ["ID_CEF9BE8C"], dict(wall="#e7e4da", seed=133, frame="#f1ede2", roof=HIP("#6b605a", 5.5), eave_rise=5.0)),
    "hohl_white": ("Hohlstrasse grosses weisses Haus mit roten Daechern", ["ID_4DA33FD9"], dict(wall="#e6e2d6", seed=135, frame="#f1ede2", roof=HIP("#9a4a3a", 6.0), eave_rise=5.5, cornice=("#f1ede2", 0.4, 0.5))),
    "hohl_brick": ("Hohlstrasse Backsteinhaus", ["ID_1D94D9F5"], dict(wall="#b9634e", seed=136, frame="#efe9de", roof=("flat", "#7c7770"), eave_rise=0.0, win=(1.3, 1.5, 0.9), bayw=2.6, fh=3.0, parapet=0.5)),
    "hohl_cream": ("Hohlstrasse cremeweisses Haus", ["ID_63421F79"], dict(wall="#e4dcc4", seed=137, frame="#f1ede2", roof=HIP("#7a4a3e"), eave_rise=4.6)),
}


def build(only=None):
    _k4.OVR4 = OVRZ
    for k, (title, ids, kw) in SPECS.items():
        if only and k not in only: continue
        _k4.block_model("z3c_" + k, title, ids, **{**COMMON, **kw})


if __name__ == "__main__":
    build(set(sys.argv[1].split(",")) if len(sys.argv) > 1 else None)
