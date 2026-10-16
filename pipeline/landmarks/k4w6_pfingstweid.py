"""Schulhaus Pfingstweid: Neubau 2019, Betonbau mit Fensterbaendern (Mapillary, Panoramax #24).
Photos: research/v3/sh_pfingstweid.md"""
from k4w6_kit import *


def build():
    block6('sh_pfingstweid', 'Schulhaus Pfingstweid', ['ID_15B31CC5'], wall='#a9a69c', frame='#d8d6cf', glass='#36434d', cols=4, rows=1, fh=3.6, bayw=2.5, win=(1.9, 1.5, 0.9), eg_h=3.8, eg_kind='shop', eg_col='#4a4540', base_col='#7c7a74', cornice=('#8a8780', 0.3, 0.4), roof=('flat', '#5f5e5a'), parapet=0.8, seed=76, surround='#cfcdc6')


if __name__ == "__main__":
    build()
