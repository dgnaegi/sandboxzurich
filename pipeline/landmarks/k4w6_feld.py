"""Schulhaus Feld (Aussersihl): Putz ockergelb, weisse Gewände, dunkles Walmdach (Mapillary #7 #1).
Photos: research/v3/sh_feld.md"""
from k4w6_kit import *


def build():
    block6('sh_feld', 'Schulhaus Feld (Aussersihl)', ['ID_09DFCDA0'], wall='#d8c58e', frame='#f1ecdc', cols=2, rows=2, fh=3.9, bayw=2.8, win=(1.3, 2.1, 0.8), eg_h=4.4, eg_kind='win', base_col='#958d7a', cornice=('#c4b07a', 0.4, 0.5), roof=('hip', '#6b4a40', 7.0), eave_rise=5.5, seed=73, surround='#eee6ce')


if __name__ == "__main__":
    build()
