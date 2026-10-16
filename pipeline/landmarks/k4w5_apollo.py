"""Apollo-Haus (Stauffacherstrasse/Badenerstrasse): 1960s office block, horizontal bands of green-tinted glass between light-grey spandrels, set-back top floor, dark ground floor.
Photos: research/v3/apollo_stauffacher.md (Mapillary #2 #3 #0 #1, Panoramax #12)"""
from k4w5_kit import *


def build():
    block5("apollo", "Apollo-Haus Stauffacherstrasse", ["ID_A3A62D5D"], wall="#b8bdb7", frame="#d8dcd8", glass="#3d5a60", sky="#a5bcc6", cols=3, rows=1,
           fh=3.3, bayw=2.4, win=(2.2, 1.7, 0.85), eg_h=4.4, eg_kind="shop", eg_col="#2b2f31", cornice=("#cfd3cf", 0.3, 0.5), floor_bands=("#9ea6a2", 0.25, 0.5), roof=("flat", "#6c6e6c"), parapet=0.4,
           seed=113, lit=0.5, base_col="#44484a", surround="#d8dcd8", deep_z=8.0, wall_stains=0.015, rooftop=("#8d918e", 8.0, 5.0, 2.6))


if __name__ == "__main__":
    build()
