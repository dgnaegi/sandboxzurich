"""Langstrassen-Unterfuehrung (Kreis 4 / 5): shared geometry of the underpass model and of the terrain cut.
Axis = OSM tunnel way 4592588 (894.04,-363.94) -> (931.68,-278.28), 93.56 m. s = metres along the axis (south -> north), o = offset to the
right of the travel direction (east side, +). Floor profile fits the swissALTI3D axis samples (research/v3/langstr_unterf.md)."""
import math
import numpy as np

A = np.array([894.04, -363.94]); B = np.array([931.68, -278.28])
L = float(np.linalg.norm(B - A)); D = (B - A) / L; N = np.array([D[1], -D[0]])   # N = right of travel (east side)
Z_S, Z_N = -8.2, -8.8        # floor at the south / north portal (m, game z)
RAMP = 0.0694                # approach gradient
GROUND = -3.1                # street level around the approach troughs
ROAD_W = 5.8                 # carriageway half width (floor)
KERB_W, KERB_H = 6.7, 1.6    # foot of the vertical wall / chamfer height
CLEAR = 4.6                  # clear height of the road tunnel
PED_IN, PED_OUT, PED_FOOT = 7.85, 12.6, 11.5   # passage: inner wall, outer wall at ceiling, foot of the slanted outer wall
PED_H = 3.4
HALF = 12.6                  # outer half width of the structure
S_MIN, S_MAX = -75.0, L + 75.0


def floor_z(s):
    """Road/floor height (game z) along the axis."""
    s = np.asarray(s, float)
    inner = Z_S + (Z_N - Z_S) * np.clip(s, 0, L) / L
    return np.where(s < 0, Z_S - RAMP * s, np.where(s > L, Z_N + RAMP * (s - L), inner))


DECK = [(0, -2.2), (32, -2.3), (40, -2.6), (60, -2.85), (L, -2.7)]    # rail deck top (swissALTI3D / rail height)


def deck_z(s):
    return np.interp(s, [p[0] for p in DECK], [p[1] for p in DECK])


def xy(s, o):
    return A + D * s + N * o


def profile_pts():
    return [[S_MIN, round(float(floor_z(S_MIN)), 3)], [0, Z_S], [round(L, 2), Z_N], [round(S_MAX, 1), round(float(floor_z(S_MAX)), 3)]]


def cut_entry():
    return {"name": "Langstrassen-Unterfuehrung: sunken road + passages (floor profile along the OSM tunnel axis, approaches as troughs)",
            "axis": [[round(A[0], 2), round(A[1], 2)], [round(B[0], 2), round(B[1], 2)]], "profile": profile_pts(), "half": HALF, "blend": 1.0,
            "mode": "min", "lock": True,
            "source": "OSM tunnel way 4592588 + footway tunnels 4803419/4803422; pipeline/landmarks/lu_geom.py; photos research/v3/langstr_unterf.md"}


def deck_json():
    c = [xy(0, -HALF - 0.5), xy(0, HALF + 0.5), xy(L, HALF + 0.5), xy(L, -HALF - 0.5)]
    return {"_doc": "Underpass deck under the SBB track field (Langstrasse). Rails keep their raw DTM height (railways.py reads terrain.heights without terrain_cuts), "
            "so tracks already lie on this deck; polygon + top height (game z) for rail consumers that need the deck explicitly.",
            "name": "Langstrassen-Unterfuehrung", "poly": [[round(float(p[0]), 2), round(float(p[1]), 2)] for p in c],
            "top_z": [[round(float(s), 1), round(float(deck_z(s)), 2)] for s in (0, 32, 40, 60, L)], "thickness": 1.3,
            "floor_z": [Z_S, Z_N], "clear_height": CLEAR, "axis": [A.tolist(), B.tolist()], "length": round(L, 2)}


if __name__ == "__main__":
    import json, sys
    F = "/Users/danielgnagi/sandboxzurich/pipeline/overrides/terrain_cuts.json"
    d = json.load(open(F)); e = cut_entry()
    d["cuts"] = [c for c in d["cuts"] if not c["name"].startswith("Langstrassen-Unterfuehrung")] + [e]
    json.dump(d, open(F, "w"), indent=1, ensure_ascii=False)
    json.dump(deck_json(), open("/Users/danielgnagi/sandboxzurich/research/v3/langstr_unterf_deck.json", "w"), indent=1)
    print("cut + deck written", L)
