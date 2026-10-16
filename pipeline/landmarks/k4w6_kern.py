"""Schulhaus Kern (Aussersihl): Putz sandbeige, Rundbogenfenster im Sockelgeschoss, Walmdach rotbraun (Mapillary #8).
Photos: research/v3/sh_kern.md"""
from k4w6_kit import *


def build():
    block6('sh_kern', 'Schulhaus Kern (Aussersihl)', ['ID_5F0BF24D'], wall='#cdb995', frame='#ece4d0', cols=2, rows=2, fh=3.7, bayw=2.8, win=(1.25, 2.0, 0.8), eg_h=4.4, eg_kind='arch', base_col='#8f877a', cornice=('#bba983', 0.4, 0.5), roof=('hip', '#7d4c3c', 6.0), eave_rise=4.5, seed=71, surround='#e6dcc2')


if __name__ == "__main__":
    build()
