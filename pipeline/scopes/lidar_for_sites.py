"""Fetch and rasterise the LiDAR tiles a ramp site needs (pipeline/lidar_fetch.py order flow, pipeline/lidar_grid.py grids).

  python3 pipeline/scopes/lidar_for_sites.py <site>[,<site>] [--dry]
  python3 pipeline/scopes/lidar_for_sites.py --tiles 2679000_1248500,... [--dry]
Tiles (500 m, LV95 lower-left corner) covering the site's fetch box that are missing under data/raw/lidar/ are ordered from the
Stadt Zürich OGD geoportal (anonymous, CC0, whole tiles delivered) one column at a time, then g_<E>_<N>.npz grids are built.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
from ramp_sites import site as site_cfg  # noqa: E402
import lidar_fetch as LF  # noqa: E402
import lidar_grid as LG  # noqa: E402

OX, OY, T = 2681400, 1248700, 500


def tiles_for_box(box):
    x0, y0, x1, y1 = box
    out = []
    for X in range(int((x0 + OX) // T * T), int(x1 + OX) + 1, T):
        for Y in range(int((y0 + OY) // T * T), int(y1 + OY) + 1, T):
            out.append((X, Y))
    return sorted(set(out))


def main():
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--tiles" in sys.argv:   # explicit list E_N,E_N,... (pipeline/scopes/discover.py --lidar prints it)
        need = sorted(tuple(int(v) for v in t.split("_")) for t in sys.argv[sys.argv.index("--tiles") + 1].split(","))
    else:
        need = sorted({t for n in names[0].split(",") for t in tiles_for_box(site_cfg(n)["fetch"])})
    LF.OUT.mkdir(parents=True, exist_ok=True)
    missing = [t for t in need if not (LF.OUT / f"{t[0]}_{t[1]}.laz").exists()]
    print(f"tiles needed {need}, missing {missing}", flush=True)
    if "--dry" in sys.argv:
        return
    for X, ys in LF.groups(missing) if missing else []:
        job = LF.order(X, ys)
        n, size = LF.fetch(job)
        print(f"X {X} Y {ys[0]}..{ys[-1]}: job {job}, {n} new tiles, {size // 2**20} MB", flush=True)
    for X, Y in need:
        name = f"{X}_{Y}"
        if (LF.OUT / f"{name}.laz").exists() and not (LG.OUT / f"g_{name}.npz").exists():
            print("grid", name, flush=True)
            LG.build_tile(name)
    left = [t for t in need if not (LG.OUT / f"g_{t[0]}_{t[1]}.npz").exists()]
    print("grids missing:", left if left else "none", flush=True)


if __name__ == "__main__":
    main()
