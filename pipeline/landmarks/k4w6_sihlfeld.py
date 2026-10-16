"""Schulhaus Sihlfeld: Schulhaus von 1919, hell-sandfarbener Putz, Walmdach (OSM start_date 1919, 4 Geschosse).
Photos: research/v3/sh_sihlfeld.md"""
from k4w6_kit import *


def build():
    block6('sh_sihlfeld', 'Schulhaus Sihlfeld', ['ID_108473A2'], wall='#d4cab0', frame='#eee8d8', cols=2, rows=2, fh=3.9, bayw=2.9, win=(1.3, 2.0, 0.8), eg_h=4.3, eg_kind='win', base_col='#8f8878', cornice=('#c1b494', 0.35, 0.5), roof=('hip', '#7a5646', 6.5), eave_rise=5.0, seed=74, surround='#e8e0cb')


if __name__ == "__main__":
    build()
