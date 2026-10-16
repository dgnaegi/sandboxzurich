"""Roentgenstrasse ochre housing row (1920s-30s Genossenschaft, Roentgenplatz edge): four-floor ochre-yellow plaster row, brown shutters, cream window frames, hipped tile roof.
Photos: research/v3/roentgen_zeile.md (Panoramax #14, Mapillary #1 #0 #4 #3)"""
from k4w4_kit import *


def build():
    block_model("roentgen_zeile", "Roentgenstrasse Zeile Ocker", ["ID_DBFB2624"], wall="#dcb676", frame="#5a3a2a", glass="#37424b", sky="#8fa5b4", cols=2, rows=2,
                fh=3.0, bayw=2.55, win=(1.15, 1.5, 0.9), eg_h=3.4, eg_kind="plain", cornice=("#e6d8b5", 0.35, 0.4), roof=("hip", "#8a4a38", 4.8), roof_d=6.0,
                seed=89, lit=0.4, base_col="#8a7d66", surround="#e6d8b5", curtains=[(236, 232, 222), (150, 110, 80)], deep_z=7.0, eave_rise=4.8, wall_stains=0.02)


if __name__ == "__main__":
    build()
