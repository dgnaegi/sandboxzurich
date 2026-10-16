"""James Hochhaus + Eckhaus (Dennlerstrasse/Badenerstrasse, Albisrieden, 2010s): periwinkle/white horizontally banded aluminium-panel facades with ribbon windows,
projecting coloured balconies (yellow, green), dark glazed plinth. Photos: research/v3/james_hochhaus.md (Mapillary #1 #3 #4 #0 #2, Commons #6 #7)"""
from k4w4_kit import *


def build():
    block_model("james", "James Hochhaus Albisrieden", ["ID_C4B58043"], wall="#b4bcdc", frame="#f4f4f6", glass="#38465a", sky="#9fb2c8", cols=3, rows=1,
                fh=3.1, bayw=2.4, win=(2.0, 1.5, 0.95), eg_h=4.4, eg_kind="shop", cornice=("#7b88bd", 0.2, 0.5), floor_bands=("#7e8ec4", 0.18, 0.55), roof=("flat", "#80808a"), parapet=0.5,
                seed=101, lit=0.45, base_col="#2b2d33", surround="#f4f4f6", deep_z=8.0, curtains=[(240, 238, 232), (226, 190, 70), (120, 170, 120), (200, 210, 235)])


if __name__ == "__main__":
    build()
