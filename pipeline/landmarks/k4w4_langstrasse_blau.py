"""Langstrasse blue corner block (Langstrasse at Militaer-/Dienerstrasse, 1950s): five-floor blue-grey plaster block with roller-shutter windows, set-back top floor,
ground-floor Beizen under dark-red awnings with terrace tables. Photos: research/v3/langstrasse.md + langstrasse_nord (Mapillary #9 #10 #8 #5, Panoramax #16 #17)"""
from k4w4_kit import *


def build():
    block_model("langstrasse_blau", "Langstrasse Eckhaus blau", ["ID_D038A8FB"], wall="#8396b4", frame="#e9e6de", glass="#2c3844", sky="#8aa0ae", cols=2, rows=3,
                fh=3.0, bayw=2.5, win=(1.05, 1.6, 0.85), eg_h=4.2, eg_kind="shop", eg_col="#33302e", cornice=("#cfc8b8", 0.25, 0.4), roof=("flat", "#6f6d69"),
                seed=85, lit=0.45, base_col="#6d6a62", awning=("#8a1f2a", 3.2, 1.3), curtains=[(206, 200, 188), (150, 140, 120), (240, 238, 230), (120, 130, 150)], deep_z=6.0,
                signs=[dict(text="BAR", fg="#f2eee6", bg="#8a1f2a", pref=None, w=3.0, h=0.5, z=3.35, size=22, du=-8.0)])


if __name__ == "__main__":
    build()
