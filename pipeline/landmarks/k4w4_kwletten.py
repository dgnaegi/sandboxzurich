"""Wasserkraftwerk Letten (Limmat, 1892, Kreis 5): pale grey rendered machine hall with tall slit/arched windows and a lower hall with red-brick-framed arched windows
and a hipped roof, directly on the river. Photos: research/v3/kw_letten.md (Commons #10 'Kraftwerk Letten' + #9/#11, Mapillary #8 #5 #6 (Limmatweg))"""
from k4w4_kit import *


def build():
    block_model("kw_letten", "Wasserkraftwerk Letten", ["ID_E365141C", "ID_5701E4DB"], wall="#d6d8d3", frame="#e9e6dc", glass="#2f3b46", sky="#8fa4b2", cols=2, rows=3,
                fh=7.6, bayw=4.4, win=(1.6, 5.0, 1.2), arch=True, eg_h=None, eg_kind="plain", cornice=("#b9b3a4", 0.35, 0.6), roof=("hip", "#6a6862", 3.5), roof_d=6.0, eave_rise=3.5,
                seed=99, lit=0.3, base_col="#7d776b", surround="#9a4a3a", deep_z=99.0, wall_stains=0.02)


if __name__ == "__main__":
    build()
