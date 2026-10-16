"""Schulhaus Wengi: Schulhaus an der Hohlstrasse, hellocker Putz, Walmdach.
Photos: research/v3/sh_wengi.md"""
from k4w6_kit import *


def build():
    block6('sh_wengi', 'Schulhaus Wengi', ['ID_10BBD2B5'], wall='#d1c6a6', frame='#ece5d2', cols=2, rows=2, fh=3.9, bayw=2.9, win=(1.3, 2.0, 0.8), eg_h=4.3, eg_kind='win', base_col='#908978', cornice=('#bfb18e', 0.35, 0.5), roof=('hip', '#7c5646', 6.5), eave_rise=5.0, seed=77, surround='#e6dec8')


if __name__ == "__main__":
    build()
