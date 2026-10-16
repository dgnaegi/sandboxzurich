"""Albisriederplatz Eckhaus (Badenerstrasse, Gruenderzeit/1900s): five-storey ochre-cream plaster corner block with green shutters, bay balconies suggested by deeper reveals, shops below, mansard-like hip roof.
Photos: research/v3/albisriederplatz_ost.md (Commons #1, Mapillary #2, Panoramax #6)"""
from k4w5_kit import *


def build():
    block5("albis_ost", "Albisriederplatz Eckhaus", ["ID_0A8340B3"], wall="#e0c79c", frame="#3f5f48", glass="#35424b", sky="#8fa5b4", cols=2, rows=2,
           fh=3.1, bayw=2.6, win=(1.15, 1.75, 0.8), eg_h=4.2, eg_kind="shop", eg_col="#34302c", cornice=("#efe3c8", 0.45, 0.45), roof=("hip", "#7d4a3a", 5.0), roof_d=6.0, eave_rise=5.0,
           seed=117, lit=0.4, base_col="#8a7b64", surround="#efe3c8", awning=("#8a2a2a", 3.4, 1.0), deep_z=8.0, wall_stains=0.03, curtains=[(236, 232, 222), (190, 150, 110), (150, 160, 150)])


if __name__ == "__main__":
    build()
