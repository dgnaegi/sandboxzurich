"""Shared pipeline settings: play area, tile grid, source paths.

The play area is data/build/playarea.json (pipeline/playarea.py: Kreis 4 + 5 and parts of 3 and 9).
SBZ_AREA=test switches back to the 600 m test area (Langstrasse/Helvetiaplatz) for quick builds.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REEL = ROOT.parent / "gta6" / "data"  # read-only reuse of the reel data (DECISIONS #1)
OUT = ROOT / "web" / "public" / "tiles"

TILE = 200.0  # metres
HGRID = 2.0  # height grid spacing in metres (pipeline sampling and per-tile height maps)
TEST_AREA = (600.0, -1000.0, 1200.0, -400.0)
_PLAY = ROOT / "data" / "build" / "playarea.json"
PLAY = json.load(open(_PLAY)) if _PLAY.exists() and os.environ.get("SBZ_AREA") != "test" else None
# x0 y0 x1 y1 in local metres (x east, y north)
AREA = tuple(PLAY["bbox"]) if PLAY else TEST_AREA
POLYGON = PLAY["polygon"] if PLAY else [[TEST_AREA[0], TEST_AREA[1]], [TEST_AREA[2], TEST_AREA[1]],
                                        [TEST_AREA[2], TEST_AREA[3]], [TEST_AREA[0], TEST_AREA[3]]]


def tiles():
    """(ix, iy) of every tile to build (play area + backdrop ring)."""
    if PLAY:
        return [(t[0], t[1]) for t in PLAY["tiles"]]
    x0, y0, x1, y1 = AREA
    return [(ix, iy) for ix in range(int(x0 // TILE), int(x1 // TILE))
            for iy in range(int(y0 // TILE), int(y1 // TILE))]


def is_backdrop(ix, iy):
    """Backdrop tiles lie outside the fence: buildings and ground only."""
    return bool(PLAY) and any(t[0] == ix and t[1] == iy and len(t) > 2 and t[2] == 0 for t in PLAY["tiles"])
