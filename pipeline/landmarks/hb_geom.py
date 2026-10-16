"""Zuerich HB: shared dimensions (model frame d/c/z, metres above terrain). Sources: OSM building:part ways (Wannerhalle 133 x 42, height 24 m,
Nordtrakt / Suedtrakt 134 x 40-44, 4 levels), swissBUILDINGS3D roof heights (research/hb/README.md), SBB perron data (research/hb/tracks.json)."""
import math

# ---- Hauptgebaeude ------------------------------------------------------------------------------------------------------------
HALL_D0, HALL_D1 = -20.0, 113.0          # Wannerhalle (Haupthalle)
HALL_C0, HALL_C1 = -25.0, 17.0
HALL_EAVE = 21.0                          # wall height under the roof
HALL_CROWN = 25.0                         # barrel crown (longitudinal)
HALL_LANT = 28.0                          # skylight ridges
LANT_X = [-7.0 + 18.2 * k for k in range(7)]   # skylight ridge centres (d)
WING_LOW = 11.0                           # roof height of the wing parts next to the hall

S_D0, S_D1 = -8.0, 105.0                  # Suedtrakt facade block (Bahnhofplatz side)
S_C0, S_C1 = -67.0, -45.0                 # facade block depth; inner low part c -45..-25
S_EAVE, S_TOP = 17.5, 20.0
PORTAL_D = 48.0
FACADE = [(-8.0, 6.0, -67.0, 17.5), (6.0, 36.0, -63.0, 15.5), (36.0, 60.0, -68.0, 18.5), (60.0, 90.0, -62.0, 15.5), (90.0, 105.0, -66.0, 17.5)]   # d0, d1, c of the face, eave height (swiss footprint steps)

N_D0, N_D1 = -20.0, 96.0                  # Nordtrakt
N_C0, N_C1 = 17.0, 57.0
N_EAVE, N_CROWN = 15.0, 20.0

Q_D0, Q_D1 = -45.0, -21.0                 # Querhalle (barrel along c)
Q_C0, Q_C1 = -64.0, 57.0
Q_EAVE, Q_CROWN = 11.0, 17.8

# ---- Perrons (frame c relative to ORG: abs c - 23.2) ----------------------------------------------------------------------------
C_OFF = 23.9
PLATFORMS = {  # ref: (c_sw_edge, c_ne_edge) relative
    '3': (-51.0 - C_OFF, -45.2 - C_OFF), '4/5': (-37.5 - C_OFF, -28.0 - C_OFF), '6/7': (-20.3 - C_OFF, -11.3 - C_OFF),
    '8/9': (-2.9 - C_OFF, 6.1 - C_OFF), '10/11': (14.1 - C_OFF, 23.7 - C_OFF), '12/13': (31.3 - C_OFF, 40.9 - C_OFF),
    '14/15': (48.5 - C_OFF, 58.1 - C_OFF), '16/17': (65.5 - C_OFF, 75.0 - C_OFF), '18': (83.1 - C_OFF, 90.0 - C_OFF)}
PLAT_HEAD_D = 1831.0 - 1876.04            # platform heads (-45.0)


def inside(d, c, rect):
    return rect[0] <= d <= rect[2] and rect[1] <= c <= rect[3]

FLOOR = 0.14   # walkable floor height above the terrain plateau (ground decals / lawn drapes are lifted up to ~0.11 m, see build_testarea)
