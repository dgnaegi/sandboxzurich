"""Ortsmuseum Wiedikon: kleines Wohnhaus aus dem 19. Jh., cremegelber Putz, Satteldach (Commons).
Photos: research/v3/ortsmuseum_wiedikon.md"""
from k4w6_kit import *


def build():
    block6('ortsmuseum_wiedikon', 'Ortsmuseum Wiedikon', ['ID_AD990490'], wall='#e0d4b2', frame='#f4eedc', cols=2, rows=2, fh=3.2, bayw=2.5, win=(1.1, 1.6, 0.9), eg_h=3.8, eg_kind='win', base_col='#9b937f', cornice=('#cdbf98', 0.3, 0.4), roof=('gable', '#7a4a3a', 5.0), seed=79, surround='#f0e8d0')


if __name__ == "__main__":
    build()
