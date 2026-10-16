"""Kino-Houdini block (Hohlstrasse / Idaplatz side, 2010s): seven-storey sand-yellow/pink brick block, irregular square window pattern with dark frames, dark glazed ground floor
with bicycle racks, big gold lettering KINO HOUDINI, KIND shop sign. Photos: research/v3/idaplatz_block.md (Mapillary #10 #7 #13 #4 #11, Panoramax #24)"""
from k4w4_kit import *


def build():
    block_model("houdini", "Block Kino Houdini Hohlstrasse", ["ID_B7D39928"], wall="#cfa971", wall_tex=tex_brick("#c9a46c", "#d3c19c", 256, 16, seed=9, var=0.1), wmod=(1.5, 1.2), frame="#2b2b2c", glass="#2f3a42", sky="#a0b0b8", cols=1, rows=1,
                fh=3.1, bayw=2.8, win=(1.4, 1.5, 0.95), eg_h=5.4, eg_kind="shop", eg_col="#2a2a2a", cornice=("#b99660", 0.15, 0.4), roof=("flat", "#8c8a84"),
                seed=83, lit=0.4, base_col="#6e5f4b", surround="#2b2b2c", deep_z=8.0, wall_stains=0.03,
                signs=[dict(text="KINO HOUDINI", fg="#b8955a", bg="#cba56d", pref=None, w=24.0, h=1.2, z=5.8, size=26, font="Barlow-Bold", px=700),
                       dict(text="KIND", fg="#f2f0e8", bg="#1c1c1e", pref=None, w=3.2, h=0.9, z=4.0, du=-14.0, size=26, font="Barlow-Bold", px=324)])


if __name__ == "__main__":
    build()
