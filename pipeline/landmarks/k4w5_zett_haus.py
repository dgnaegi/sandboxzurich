"""Zett-Haus (Badenerstrasse/Raeckerstrasse, Stauffacher): five-storey cream natural-stone commercial block, tall window rows with stone surrounds, shops under striped awnings and a glass canopy at the tram stop.
Photos: research/v3/zett_haus.md (Mapillary #5 #4 #3 #2 #0 #6 #1, Commons #8 #9)"""
from k4w5_kit import *


def build():
    block5("zett_haus", "Zett-Haus Badenerstrasse", ["ID_F96E5BF1"], wall="#d3c6a8", frame="#efe8da", glass="#35424c", sky="#8fa3b2", cols=2, rows=2,
           fh=3.5, bayw=2.7, win=(1.3, 2.0, 0.85), eg_h=4.8, eg_kind="shop", eg_col="#2e2f30", cornice=("#e4dccb", 0.5, 0.5), roof=("flat", "#74726d"), parapet=0.5,
           seed=111, lit=0.4, base_col="#85796a", surround="#ece4d3", awning=("#a02a2e", 3.6, 1.4), deep_z=8.0, wall_stains=0.03,
           signs=[dict(text="SCHUHE", fg="#f1ece0", bg="#1f2326", pref=None, w=5.0, h=0.7, z=3.9, size=22, px=512),
                  dict(text="PARFUEMERIE", fg="#f1ece0", bg="#6b2a35", pref=None, w=6.0, h=0.7, z=3.9, du=8.0, size=22, px=512)])


if __name__ == "__main__":
    build()
