"""Schulhaus Hohl (Aussersihl): Putz cremegelb, Walmdach, Hochformatfenster (Mapillary #2 #5, Commons #6).
Photos: research/v3/sh_hohl.md"""
from k4w6_kit import *


def build():
    block6('sh_hohl', 'Schulhaus Hohl (Aussersihl)', ['ID_AD4DDF26'], wall='#d9ccaa', frame='#efe8d6', cols=2, rows=2, fh=3.9, bayw=2.9, win=(1.3, 2.1, 0.8), eg_h=4.3, eg_kind='win', base_col='#9a927f', cornice=('#c8b88f', 0.35, 0.5), roof=('hip', '#86503f', 6.5), eave_rise=5.0, seed=72, surround='#ebe3cc')


if __name__ == "__main__":
    build()
