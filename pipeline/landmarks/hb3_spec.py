"""Zuerich HB v3: levels below the hall (shared dimensions, model frame d/c/z, z = metres above the hall plateau = terrain -2.9 m local).
Schematic: levels and connections follow the SBB station plan (Shopville, Museumstrasse 41-44, Loewenstrasse 31-34); exact plan positions are not published
as open data, so lengths are truncated to the play area (see research/hb/v3.md)."""
import math
SLOPE = 0.5667          # rise / run of the stair decks (0.17 m riser, 0.30 m tread)
ZS, ZM, ZL = -5.3, -10.5, -16.0   # floor heights: Shopville gang, Bahnhof Museumstrasse (41-44), Bahnhof Loewenstrasse (31-34)
HALLZ = 0.14            # hall floor above the plateau (hb_geom.FLOOR)
GANG_C0, GANG_C1, GANG_D0, GANG_D1 = -97.0, -87.0, -33.0, 118.0   # Shopville E-W gang under the Bahnhofplatz
CONN_D, CONN_W = -33.0, 8.0      # N-S connector under the Querhalle
# stairs: name, top (d, c), direction (dd, dc), z_top, z_bot, width
STAIRS = [
    ("S1", (-33.0, -4.0), (0, -1), HALLZ, ZS, 6.0),          # Querhalle -> Shopville connector
    ("S2", (60.0, -77.5), (0, -1), 0.0, ZS, 6.0),            # Bahnhofplatz -> Shopville gang
    ("SC", (114.8, GANG_C1), (0, 1), ZS, ZM, 5.0),           # gang -> Museumstrasse platform
    ("SL", (70.0, GANG_C1), (0, 1), ZS, ZL, 5.0),            # gang -> Loewenstrasse platform
]
OPEN_Z = -3.2           # stair surface below this height lies under a soffit (above it the well is open to the sky)


def run(s):
    return (s[3] - s[4]) / SLOPE


def end(s):
    r = run(s)
    return (s[1][0] + s[2][0] * r, s[1][1] + s[2][1] * r)


def open_rect(s):
    """Rectangle (d0, d1, c0, c1) of the open well (stair surface above OPEN_Z) for the two wells that reach the surface."""
    r = (s[3] - OPEN_Z) / SLOPE; w = s[5] / 2
    a, b = s[1], (s[1][0] + s[2][0] * r, s[1][1] + s[2][1] * r)
    return (min(a[0], b[0]) - w, max(a[0], b[0]) + w, min(a[1], b[1]), max(a[1], b[1]))


WELLS = [open_rect(s) for s in STAIRS[:2]]
# Loewenstrasse: 4 tracks 31-34, two island platforms, truncated length
L_D0, L_D1 = 0.0, 105.0
L_P = [(-82.7, 7.0), (-68.1, 7.0)]          # platform centres c, width
L_TRACKS = [-88.1, -77.3, -73.5, -62.7]
M_D0, M_D1 = 107.5, 136.7                    # Museumstrasse: 4 tracks 41-44 across the head, truncated c range
M_C0, M_C1 = -100.0, 10.0
M_P = [(114.8, 7.0), (129.4, 7.0)]
M_TRACKS = [109.4, 120.2, 124.0, 134.8]
