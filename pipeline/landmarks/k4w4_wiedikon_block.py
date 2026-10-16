"""Bahnhof-Wiedikon-Platz block (Birmensdorferstrasse / Seebahnstrasse, 1950s): six-floor pink-cream plaster slab with regular window grid, red and blue shutter panels,
wide overhanging flat roof, shops at ground floor. Photos: research/v3/wiedikon_platz.md (Mapillary #11 #2 #5 #15)"""
from k4w4_kit import *


def build():
    block_model("wiedikon_block", "Wiedikon-Platz Wohn- und Geschaeftshaus", ["ID_EBF6EB64"], wall="#e6d2c3", frame="#f1ede4", glass="#34404b", sky="#8fa5b4", cols=2, rows=2,
                fh=3.05, bayw=2.7, win=(1.35, 1.45, 0.95), eg_h=4.4, eg_kind="shop", cornice=("#cdbfae", 0.7, 0.35), roof=("flat", "#7c7a76"), parapet=0.2,
                seed=87, lit=0.4, base_col="#8e867a", curtains=[(176, 58, 58), (58, 90, 144), (226, 220, 206), (176, 58, 58)], deep_z=8.0, wall_stains=0.02)


if __name__ == "__main__":
    build()
