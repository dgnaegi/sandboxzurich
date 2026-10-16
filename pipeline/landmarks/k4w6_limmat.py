"""Schulhaus Limmat (Limmatstrasse, Kreis 5): Schulanlage 1900er, ochre plaster, steep red-brown hip roofs, arched entrances; fountain pavilion with copper dome at the corner.
Photos: research/v3/sh_limmat.md (Mapillary #3 #5 #0, Commons #6 #8, Panoramax #14)"""
from k4w6_kit import *


def build():
    block6("sh_limmat", "Schulhaus Limmat", ["ID_369AF482", "ID_4363EB0A", "ID_726862BC", "ID_152CF36F", "ID_9557D6B6"], wall="#d6c28c", frame="#efe9d8", glass="#2d3a44", sky="#8aa0ae",
           cols=2, rows=2, fh=3.9, bayw=2.9, win=(1.3, 2.1, 0.8), eg_h=4.2, eg_kind="win", eg_col="#8a8a7e", cornice=("#c9b27a", 0.35, 0.5), floor_bands=None,
           roof=("hip", "#8c4a3a", 6.5), eave_rise=5.0, seed=61, lit=0.35, base_col="#9d9684", surround="#ece4cc", deep_z=8.0, wall_stains=0.03)


if __name__ == "__main__":
    build()
