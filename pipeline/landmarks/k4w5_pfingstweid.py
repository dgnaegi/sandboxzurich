"""Hochhaus Pfingstweidstrasse (80 m, 2013, next to Hardbruecke): brown-grey slab with horizontal bands of windows and dark spandrels, dark base with tram stop.
Photos: research/v3/hochhaus_pfingstweid.md (Mapillary #5 #12 #15 #8, Panoramax #24)"""
from k4w5_kit import *


def build():
    block5("pfingstweid", "Hochhaus Pfingstweidstrasse", ["ID_2CC16CA6"], wall="#76675c", frame="#3e3a37", glass="#2e3a42", sky="#8fa0ad", cols=3, rows=1,
           fh=3.35, bayw=2.4, win=(1.7, 1.35, 1.0), eg_h=5.2, eg_kind="shop", eg_col="#26292b", cornice=("#4a423c", 0.4, 0.5), floor_bands=("#5d5148", 0.35, 0.5), roof=("flat", "#4d4a47"), parapet=0.9,
           seed=123, lit=0.5, base_col="#3b3633", surround="#3e3a37", deep_z=10.0, wall_stains=0.02, rooftop=("#6a6764", 7.0, 4.0, 3.0))


if __name__ == "__main__":
    build()
