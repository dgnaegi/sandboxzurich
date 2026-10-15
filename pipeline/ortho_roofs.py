"""Roof colours per building from the SWISSIMAGE orthophoto (swisstopo, open data, WMS wms.geo.admin.ch).

fetch(): mosaic of 500 m tiles at 0.5 m/px over the game bbox -> data/raw/ortho_wms/r_<ix>_<iy>.jpg (cached, throttled).
roof_rgb(footprint): robust roof colour (median of the brighter half of the pixels inside the footprint shrunk by 1 m,
so shadows and edges do not darken it). None outside the mosaic.
"""
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "data" / "raw" / "ortho_wms"
OX, OY, TILE, PX = 2681400, 1248700, 500.0, 1000  # local origin (LV95), tile size (m), px per tile
URL = ("https://wms.geo.admin.ch/?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=ch.swisstopo.swissimage&STYLES="
       "&CRS=EPSG:2056&BBOX={x0},{y0},{x1},{y1}&WIDTH={px}&HEIGHT={px}&FORMAT=image/jpeg")
_cache = {}


def fetch(bbox):
    DIR.mkdir(parents=True, exist_ok=True)
    x0, y0, x1, y1 = bbox
    n = 0
    for ix in range(int(np.floor(x0 / TILE)), int(np.floor(x1 / TILE)) + 1):
        for iy in range(int(np.floor(y0 / TILE)), int(np.floor(y1 / TILE)) + 1):
            f = DIR / f"r_{ix}_{iy}.jpg"
            if f.exists() and f.stat().st_size > 10000:
                continue
            u = URL.format(x0=OX + ix * TILE, y0=OY + iy * TILE, x1=OX + (ix + 1) * TILE, y1=OY + (iy + 1) * TILE, px=PX)
            req = urllib.request.Request(u, headers={"User-Agent": "sandboxzurich-pipeline (open data, roof colours)"})
            f.write_bytes(urllib.request.urlopen(req, timeout=60).read())
            n += 1
            time.sleep(1.5)
    print(f"ortho_roofs: fetched {n} tiles")


def _tile(ix, iy):
    k = (ix, iy)
    if k not in _cache:
        f = DIR / f"r_{ix}_{iy}.jpg"
        _cache[k] = np.asarray(Image.open(f).convert("RGB")) if f.exists() else None
    return _cache[k]


def roof_rgb(fp):
    """fp: shapely Polygon in local metres."""
    g = fp.buffer(-1.0)
    if g.is_empty or g.area < 4:
        g = fp
    x0, y0, x1, y1 = g.bounds
    m = PX / TILE
    samples = []
    xs = np.arange(x0 + 0.25, x1, 0.5)
    ys = np.arange(y0 + 0.25, y1, 0.5)
    if len(xs) * len(ys) > 40000:  # very large roofs: subsample
        xs, ys = xs[::3], ys[::3]
    import shapely
    X, Y = np.meshgrid(xs, ys)
    inside = shapely.contains_xy(g, X.ravel(), Y.ravel())
    for x, y in zip(X.ravel()[inside], Y.ravel()[inside]):
        ix, iy = int(np.floor(x / TILE)), int(np.floor(y / TILE))
        im = _tile(ix, iy)
        if im is None:
            continue
        c = int((x - ix * TILE) * m)
        r = int(((iy + 1) * TILE - y) * m)
        if 0 <= r < PX and 0 <= c < PX:
            samples.append(im[r, c])
    if len(samples) < 6:
        return None
    s = np.asarray(samples, np.float32)
    lum = s @ np.array([0.299, 0.587, 0.114], np.float32)
    s = s[lum >= np.median(lum)]  # brighter half: sunlit roof, not shadow
    return tuple(int(v) for v in np.median(s, axis=0))


if __name__ == "__main__":
    import json
    pa = json.load(open(ROOT / "data" / "build" / "playarea.json"))
    x0, y0, x1, y1 = pa["bbox"]
    fetch((x0 - 250, y0 - 250, x1 + 250, y1 + 250))
