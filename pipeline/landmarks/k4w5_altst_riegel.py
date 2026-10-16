"""Altstetten Bahnhofplatz Wohn-/Geschaeftsriegel (1960s): ten-storey cream slab with dark balcony bands over a wide dark arcade with kiosks and shops.
Photos: research/v3/altstetten_platz.md (Commons #14 #15, Mapillary #2 #4 #9)"""
from k4w5_kit import *


def build():
    block5("altst_riegel", "Altstetten Bahnhofplatz Riegel", ["ID_5991DA16"], wall="#d6cfbf", frame="#5a5754", glass="#3a444c", sky="#8fa3b2", cols=3, rows=1,
           fh=3.1, bayw=2.3, win=(1.5, 1.3, 1.0), eg_h=4.6, eg_kind="shop", eg_col="#2a2a2b", cornice=("#4a4845", 0.5, 0.7), floor_bands=("#6a6663", 0.4, 0.5), roof=("flat", "#74726f"), parapet=0.5,
           seed=135, lit=0.45, base_col="#444240", surround="#5a5754", deep_z=8.0, wall_stains=0.03, awning=("#3c3a38", 4.6, 1.0))


if __name__ == "__main__":
    build()
