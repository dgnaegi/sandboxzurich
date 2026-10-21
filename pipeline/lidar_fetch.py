"""Download the Kanton Zürich LiDAR point cloud 2021/22 (OGD, CC0) for the play area into data/raw/lidar/<X>_<Y>.laz.

Orders go through the Stadt Zürich OGD geoportal (anonymous, no e-mail; max 4 km2 per order), see research/lidar/README.md.
Tiles are 500 m (LV95 lower-left corner in the file name); tiles already on disk are skipped. Usage:
    .venv/bin/python pipeline/lidar_fetch.py [--dry]
"""
import io
import math
import sys
import time
import zipfile

import requests
from shapely.geometry import Polygon, box

from config import POLYGON, ROOT

OX, OY, T = 2681400, 1248700, 500
OUT = ROOT / "data" / "raw" / "lidar"
ORDER = "https://www.ogd.stadt-zuerich.ch/geoportal_order/"
DL = "https://geoservices.zh.ch/geoshopapi/v1/orders/{}/download"
UA = {"User-Agent": "sandboxzurich-pipeline/1.0 (lidar_fetch)"}
RUN = 8   # tiles per order (8 x 0.25 km2 = 2 km2, below the 4 km2 cap)


def tiles():
    P = Polygon(POLYGON).buffer(120)
    x0, y0, x1, y1 = P.bounds
    out = []
    for X in range(int(math.floor((x0 + OX) / T) * T), int(x1 + OX) + 1, T):
        for Y in range(int(math.floor((y0 + OY) / T) * T), int(y1 + OY) + 1, T):
            if P.intersects(box(X - OX, Y - OY, X + T - OX, Y + T - OY)):
                out.append((X, Y))
    return sorted(out)


def groups(todo):
    """Contiguous runs along a column (same X), at most RUN tiles each -> one rectangle per order."""
    out = []
    for X in sorted({t[0] for t in todo}):
        ys = sorted(t[1] for t in todo if t[0] == X)
        run = [ys[0]]
        for y in ys[1:]:
            if y == run[-1] + T and len(run) < RUN:
                run.append(y)
            else:
                out.append((X, run)); run = [y]
        out.append((X, run))
    return out


def order(X, ys):
    e = 5   # inset so neighbouring tiles are not included
    X0, X1, Y0, Y1 = X + e, X + T - e, ys[0] + e, ys[-1] + T - e
    ring = [[X0, Y0], [X0, Y1], [X1, Y1], [X1, Y0], [X0, Y0]]
    o = {"order": {"stzh": False, "geoportal_name": "LIDAR Laserscanning-Punktwolke - 2021 bis 2022 (OGD)", "geoportal_id": "557",
                   "geodatensatz_id": None, "paket_id": None, "email": "", "extent_name": "bbox", "extent": [ring],
                   "selected_format": {"id": 61, "name": "LAZ (.laz)"}}}
    r = requests.post(ORDER, json=o, headers=UA, timeout=60)
    r.raise_for_status()
    return r.json()["job_id"]


def fetch(job):
    for _ in range(60):
        time.sleep(10)
        s = requests.get(ORDER + job, headers=UA, timeout=60)
        if s.ok and "SUCCESS" in s.text:
            break
    else:
        raise RuntimeError(f"order {job} not ready")
    z = requests.get(DL.format(job), headers=UA, timeout=900)
    z.raise_for_status()
    n = 0
    with zipfile.ZipFile(io.BytesIO(z.content)) as zf:
        for m in zf.namelist():
            name = m.rsplit("/", 1)[-1]
            if name.endswith(".laz") and not (OUT / name).exists():
                (OUT / name).write_bytes(zf.read(m)); n += 1
    return n, len(z.content)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    all_t = tiles()
    todo = [t for t in all_t if not (OUT / f"{t[0]}_{t[1]}.laz").exists()]
    gs = groups(todo) if todo else []
    print(f"tiles {len(all_t)}, on disk {len(all_t) - len(todo)}, to fetch {len(todo)} in {len(gs)} orders", flush=True)
    if "--dry" in sys.argv:
        return
    for X, ys in gs:
        job = order(X, ys)
        n, size = fetch(job)
        print(f"X {X} Y {ys[0]}..{ys[-1]}: job {job}, {n} new tiles, {size // 2**20} MB", flush=True)
        time.sleep(5)
    left = [t for t in all_t if not (OUT / f"{t[0]}_{t[1]}.laz").exists()]
    print("missing:", left if left else "none", flush=True)


if __name__ == "__main__":
    main()
