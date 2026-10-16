"""Langstrasse Sued grauer Geschaeftsbau (1960s): five-floor light-grey rendered block with regular ribbon windows and a dark plinth, loading dock at ground floor.
Photos: research/v3/langstrasse_sued.md (Mapillary #0 #3 #1 #4 same view)"""
from k4w5_kit import *


def build():
    block5("langstr_grau", "Langstrasse Geschaeftsbau grau", ["ID_C76A3133"], wall="#c4c6c4", frame="#f0f1ef", glass="#3a4852", sky="#8fa3b2", cols=3, rows=1,
           fh=3.1, bayw=2.4, win=(1.6, 1.3, 1.0), eg_h=4.0, eg_kind="plain", eg_col="#3b3e40", cornice=("#e0e1df", 0.3, 0.4), roof=("flat", "#74767a"), parapet=0.5,
           seed=121, lit=0.4, base_col="#3d4144", surround="#f0f1ef", deep_z=7.0, wall_stains=0.025)


if __name__ == "__main__":
    build()
