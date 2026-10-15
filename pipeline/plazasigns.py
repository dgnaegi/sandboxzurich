"""Square name signs and dedication plaques (Widmungstafeln) at their real places.

Sources (Stadt Zürich OGD, CC0):
- Widmungstafel points (exact plaque positions + text): the blue name sign hangs right above the plaque.
- Strassennamenverzeichnis lines: squares (…platz, …anlage) get further signs at the ends of their outline.
Signs mount on the nearest facade (like Zürich does); on open squares without a wall nearby they stand on a pole.
Rows: [x, y, z, heading, name, plaque, pole]  (plaque "" = none, pole 0/1).
"""
import json
import math

import numpy as np
from shapely.geometry import Point

import addresses
import sources
from config import POLYGON, ROOT

RAW = ROOT / "data" / "raw" / "stadtzh_more"
WALL_R = 14.0      # max distance anchor -> facade for wall mounting
SPACING = 45.0     # min distance between two signs of the same square
PER_SQUARE = 3


def _is_square(name):
    n = name.lower()
    return ("platz" in n or "anlage" in n) and not n.endswith("strasse")


def _wall(p, d):
    """Nearest facade edge to p: (pos, heading) with the sign on the outside, or None."""
    best = None
    for gi in d["tree"].query(Point(p).buffer(WALL_R)):
        co = np.asarray(d["fps"][gi].exterior.coords)
        for a, b in zip(co[:-1], co[1:]):
            e = b - a
            L = float(np.hypot(*e))
            if L < 2.0:
                continue
            t = min(max(float(np.dot(p - a, e)) / L**2, 0.12), 0.88)
            q = a + e * t
            dist = float(np.hypot(*(q - p)))
            if dist <= WALL_R and (best is None or dist < best[0]):
                best = (dist, gi, q, e / L)
    if not best:
        return None
    _, gi, q, tg = best
    if d["fps"][gi].contains(Point(q[0] + tg[1] * 0.3, q[1] - tg[0] * 0.3)):
        tg = -tg  # outward normal = (ty, -tx)
    nx, ny = tg[1], -tg[0]
    return (q[0] + nx * addresses.OFF, q[1] + ny * addresses.OFF), math.atan2(tg[1], tg[0])


def _pole(p, toward):
    """Free-standing pole; panel faces the given direction (both sides are drawn)."""
    v = np.asarray(toward, float) - p
    h = math.atan2(v[1], v[0]) + math.pi / 2 if np.hypot(*v) > 0.1 else 0.0
    return (float(p[0]), float(p[1])), h


def _clean(t):
    return "\n".join(ln.strip() for ln in t.replace("\r", "").split("\n") if ln.strip())


def rows(H):
    from shapely.geometry import Polygon
    play = Polygon(POLYGON).buffer(-2)
    d = addresses._data()
    out = []

    def add(name, p, plaque, toward):
        w = _wall(np.asarray(p, float), d)
        (x, y), h = w if w else _pole(np.asarray(p, float), toward)
        z = float(H.at(x, y)) + (addresses.SIGN_Z if w else 2.6)
        out.append([round(float(x), 2), round(float(y), 2), round(z, 2), round(float(h), 3), name, plaque, 0 if w else 1])

    # 1) every dedication plaque at its surveyed point, name sign above it
    for ft in json.load(open(RAW / "geo_widmungstafel__v_widmungstafel_geoserver.geojson"))["features"]:
        g = ft.get("geometry")
        if not g:
            continue
        p = sources.geo.to_local(*g["coordinates"][:2])
        if play.contains(Point(p)):
            pr = ft["properties"]
            add(pr["strasse"], p, _clean(pr.get("widmungstext") or ""), p)

    # 2) squares: further signs at far-apart points of the square outline
    lines = {}
    for ft in json.load(open(RAW / "geo_strassennamenverzeichnis__sv_str_lin.geojson"))["features"]:
        n, g = ft["properties"].get("str_name", ""), ft.get("geometry")
        if g and _is_square(n):
            parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
            lines.setdefault(n, []).extend(sources.geo.to_local(*c[:2]) for pt in parts for c in pt)
    squares = 0
    for n, pts in lines.items():
        pts = [np.asarray(p, float) for p in pts if play.contains(Point(p))]
        if not pts:
            continue
        squares += 1
        centre = np.mean(pts, axis=0)
        have = [np.asarray(r[:2]) for r in out if r[4] == n]
        for _ in range(PER_SQUARE - len(have)):
            far = max(pts, key=lambda p: min([float(np.hypot(*(p - h))) for h in have] or [1e9]) if have else float(np.hypot(*(p - centre))))
            if have and min(float(np.hypot(*(far - h))) for h in have) < SPACING:
                break
            add(n, far, "", centre)
            have.append(far)
    print(f"plazasigns: {len(out)} signs ({sum(1 for r in out if r[5])} plaques, {sum(r[6] for r in out)} on poles), {squares} squares")
    return out
