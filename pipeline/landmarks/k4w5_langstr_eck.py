"""Langstrasse Sued Eckhaus (Langstrasse/Zurlindenstrasse area, 1890s): cream-yellow plaster corner house with dark-green shutters and a steep hip roof, small shops at ground floor.
Photos: research/v3/langstrasse_sued.md (Commons #6, Commons #5 for the neighbour in rust brown)"""
from k4w5_kit import *


def build():
    block5("langstr_eck", "Langstrasse Eckhaus Cremegelb", ["ID_9EA43684"], wall="#e8d9a8", frame="#34503e", glass="#36434c", sky="#8fa5b4", cols=2, rows=2,
           fh=3.0, bayw=2.5, win=(1.1, 1.7, 0.85), eg_h=3.9, eg_kind="shop", eg_col="#2f3a46", cornice=("#f3ead0", 0.4, 0.4), roof=("hip", "#6f4432", 5.0), roof_d=5.5, eave_rise=5.0,
           seed=119, lit=0.4, base_col="#837760", surround="#f3ead0", awning=("#2d4f78", 3.0, 1.0), deep_z=7.0, wall_stains=0.03,
           signs=[dict(text="INTERNET", fg="#f4f1e8", bg="#1d4c8c", pref=(0, -1), w=3.6, h=0.6, z=3.2, size=22, px=512)])


if __name__ == "__main__":
    build()
