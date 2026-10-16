"""Hotel-/Buerobau Badenerstrasse 420 (Crowne Plaza area, 1970s): long cream-white block, continuous ribbon windows with grey frames, recessed colonnade ground floor.
Photos: research/v3/crowne_plaza.md (Panoramax #3, Commons #0, Mapillary #1/#2)"""
from k4w5_kit import *


def build():
    block5("crowne", "Hotelbau Badenerstrasse 420", ["ID_B6DC9B98"], wall="#dcd8cc", frame="#6f7476", glass="#3a4a56", sky="#8fa7b8", cols=3, rows=1,
           fh=3.2, bayw=2.5, win=(2.0, 1.45, 0.9), eg_h=4.6, eg_kind="shop", eg_col="#2a2c2e", cornice=("#f0eee6", 0.4, 0.6), floor_bands=("#c7c3b7", 0.3, 0.45), roof=("flat", "#7a7874"), parapet=0.5,
           seed=115, lit=0.45, base_col="#55524c", surround="#6f7476", deep_z=8.0, wall_stains=0.02)


if __name__ == "__main__":
    build()
