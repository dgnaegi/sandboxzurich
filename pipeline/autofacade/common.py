"""Shared helpers for the automatic facade colour prototype (local metres, LV95 origin, see CLAUDE.md)."""
import math
import re
from pathlib import Path

import numpy as np
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = (2681400.0, 1248700.0)
_to_lv = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
_to_wgs = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
CACHE = ROOT / "data" / "raw" / "autofacade"
OUT = ROOT / "research" / "autofacade"
ZONES = {1: [400, -1010, 2000, -300], 4: [-750, -2200, 650, -900]}  # x0,y0,x1,y1 local m


def token():
    t = re.search(r"MAPILLARY_TOKEN=(.*)", (ROOT / ".env").read_text()).group(1).strip()
    return t.strip("\"'")


def ll2xy(lon, lat):
    e, n = _to_lv.transform(lon, lat)
    return e - ORIGIN[0], n - ORIGIN[1]


def xy2ll(x, y):
    return _to_wgs.transform(x + ORIGIN[0], y + ORIGIN[1])


def srgb2lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin2srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def rgb2lab(rgb):
    l = srgb2lin(rgb)
    M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = l @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab2rgb(lab):
    lab = np.asarray(lab, float)
    fy = (lab[..., 0] + 16) / 116
    fx = fy + lab[..., 1] / 500
    fz = fy - lab[..., 2] / 200
    inv = lambda f: np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27))
    xyz = np.stack([inv(fx), inv(fy), inv(fz)], -1) * np.array([0.95047, 1.0, 1.08883])
    Mi = np.linalg.inv(np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]]))
    return lin2srgb(xyz @ Mi.T)


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def rgb2hex(rgb):
    r = np.clip(np.round(rgb), 0, 255).astype(int)
    return "#%02x%02x%02x" % tuple(r)


def de2000(l1, l2):
    L1, a1, b1 = l1; L2, a2, b2 = l2
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cm = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1 = math.degrees(math.atan2(b1, a1p)) % 360 if C1p else 0
    h2 = math.degrees(math.atan2(b2, a2p)) % 360 if C2p else 0
    dL, dC = L2 - L1, C2p - C1p
    dh = h2 - h1
    if C1p * C2p == 0: dh = 0
    elif dh > 180: dh -= 360
    elif dh < -180: dh += 360
    dH = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dh / 2))
    Lm, Cmp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0: hm = h1 + h2
    elif abs(h1 - h2) <= 180: hm = (h1 + h2) / 2
    else: hm = (h1 + h2 + 360) / 2 if h1 + h2 < 360 else (h1 + h2 - 360) / 2
    T = 1 - 0.17 * math.cos(math.radians(hm - 30)) + 0.24 * math.cos(math.radians(2 * hm)) + 0.32 * math.cos(math.radians(3 * hm + 6)) - 0.2 * math.cos(math.radians(4 * hm - 63))
    dth = 30 * math.exp(-(((hm - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7))
    Sl = 1 + 0.015 * (Lm - 50) ** 2 / math.sqrt(20 + (Lm - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cmp, 1 + 0.015 * Cmp * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dL / Sl) ** 2 + (dC / Sc) ** 2 + (dH / Sh) ** 2 + Rt * (dC / Sc) * (dH / Sh))
