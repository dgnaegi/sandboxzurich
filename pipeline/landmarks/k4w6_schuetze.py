"""Schulhaus und Quartierzentrum Schuetze: rosa Putzbau mit Fensterbaendern neben weissgrauem Schulhaus (Commons #8, Mapillary #5 #6, Panoramax #16).
Photos: research/v3/sh_schuetze.md"""
from k4w6_kit import *


def build():
    block6('sh_schuetze', 'Schulhaus und Quartierzentrum Schuetze', ['ID_D6F315C6', 'ID_28E1DD42', 'ID_1E68A3BF'], wall='#b98a84', frame='#ececea', glass='#34414c', cols=4, rows=1, fh=3.4, bayw=2.4, win=(1.8, 1.4, 1.0), eg_h=4.2, eg_kind='shop', eg_col='#2c3236', base_col='#8a8886', cornice=('#a97a74', 0.3, 0.4), floor_bands=('#e4e2de', 0.3, 0.4), roof=('flat', '#6f6f6c'), parapet=0.7, seed=75, surround='#e4e2de')


if __name__ == "__main__":
    build()
