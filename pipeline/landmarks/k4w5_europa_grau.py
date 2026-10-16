"""Europaallee Lagerstrasse Buerobau (Baufeld, 2010s): long grey-brown stone-clad office block, regular tall pale window slots, set-back arcade ground floor with cafes and terraces.
Photos: research/v3/europaallee_lager.md (Mapillary #9 #2 #10 #12 #8)"""
from k4w5_kit import *


def build():
    block5("europa_grau", "Europaallee Buerobau Lagerstrasse", ["ID_87AC3F72"], wall="#8d8c88", frame="#e6e6e2", glass="#3a4650", sky="#9fb0be", cols=4, rows=1,
           fh=3.7, bayw=1.9, win=(1.15, 2.1, 0.8), eg_h=5.6, eg_kind="shop", eg_col="#3a3e3c", cornice=("#a8a7a2", 0.4, 0.5), roof=("flat", "#6d6d6b"), parapet=0.6,
           seed=131, lit=0.45, base_col="#4a4d4b", surround="#a8a7a2", awning=("#d8a52a", 3.8, 0.9), deep_z=10.0, wall_stains=0.015)


if __name__ == "__main__":
    build()
