"""Europaallee Lagerstrasse Riegel (Baufeld, 2010s): beige natural-stone block with dark glass ground floor, projecting dark box over the base, ribbon windows in pale frames.
Photos: research/v3/europaallee_lager.md (Mapillary #0 #4 #14 #13)"""
from k4w5_kit import *


def build():
    block5("europa_riegel", "Europaallee Riegel Lagerstrasse", ["ID_AF3E9C29"], wall="#b0a28c", frame="#d9d5cb", glass="#334450", sky="#9fb0be", cols=3, rows=1,
           fh=3.6, bayw=2.2, win=(1.6, 2.0, 0.8), eg_h=6.0, eg_kind="shop", eg_col="#2b2a29", cornice=("#4a423a", 0.8, 0.6), roof=("flat", "#6d6d6b"), parapet=0.6,
           seed=133, lit=0.45, base_col="#3c3a37", surround="#d9d5cb", deep_z=11.0, wall_stains=0.02)


if __name__ == "__main__":
    build()
