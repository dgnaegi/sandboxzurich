"""Limmathaus (Limmatstrasse 118 at Limmatplatz, 1931): curved cream-plaster commercial block, ribbon of blue-framed windows, ground floor with pillars and shop glazing.
Photos: research/v3/limmathaus.md (Panoramax #23, Mapillary #9 #8 #4, Commons #14-16 for the neighbouring mural gable)"""
from k4w4_kit import *


def build():
    block_model("limmathaus", "Limmathaus Limmatplatz", ["ID_6AC66823"], wall="#d9d2bd", frame="#2d5a96", glass="#33414d", sky="#8da3b3", cols=2, rows=2,
                fh=3.3, bayw=2.3, win=(1.75, 1.55, 0.85), eg_h=4.6, eg_kind="shop", cornice=("#bdb49c", 0.3, 0.5), floor_bands=("#c9c0a8", 0.07, 0.3), roof=("flat", "#7d7b76"),
                seed=81, lit=0.45, base_col="#8f8a7c", curtains=[(236, 232, 222), (190, 196, 205), (170, 160, 140)], surround="#2d5a96", deep_z=9.0)


if __name__ == "__main__":
    build()
