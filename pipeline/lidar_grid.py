"""Build cached 0.5 m rasters from the LiDAR tiles (one pass, streamed, low RAM).

Per source tile (500 m, data/raw/lidar/<E>_<N>.laz) -> data/build/lidar/g_<E>_<N>.npz with int16 cm game heights
(z_game = Z - 408 - 3.06, NODATA = -32768), 1000 x 1000 cells, row = y (south->north), col = x:
  dtm    mean of class 2 (ground)
  bridge max of class 17 (bridge deck top)
  top    max of classes 1,2,6,17 (solid surfaces incl. buildings, cars, furniture)
  bld    max of class 6
  veg    max of classes 3,4,5 (canopy height model source; CHM = veg - dtm)
  mast   Nx5 float32 array [x, y, z_top, z_base, n_points] of class-15/1 poles (clustered)
Loader API lives in lidar.py (dtm/bridge/top/veg/bld/chm/masts).
Run:  .venv/bin/python pipeline/lidar_grid.py [-j 2] > logs/lidar_grid.log
"""
from __future__ import annotations

import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "lidar"
OUT = ROOT / "data" / "build" / "lidar"
OX, OY, Z0 = 2681400.0, 1248700.0, 408.0 + 3.06
T, RES = 500, 0.5
N = int(T / RES)
ND = -32768


def _cm(z):
    return np.clip(np.round(z * 100), -32767, 32767).astype(np.int16)


def build_tile(name: str):
    import laspy
    from scipy import ndimage as ndi

    e, n = (int(v) for v in name.split("_"))
    ox, oy = e - OX, n - OY
    sm = np.zeros(N * N); cn = np.zeros(N * N)
    g = {k: np.full(N * N, -1e9, np.float32) for k in ("bridge", "top", "bld", "veg")}
    wire = []
    npts = 0
    with laspy.open(RAW / f"{name}.laz") as r:
        for ch in r.chunk_iterator(2_000_000):
            x = np.asarray(ch.x) - e
            y = np.asarray(ch.y) - n
            z = (np.asarray(ch.z) - Z0).astype(np.float32)
            c = np.asarray(ch.classification)
            npts += len(z)
            ix = np.clip((x / RES).astype(np.int64), 0, N - 1)
            iy = np.clip((y / RES).astype(np.int64), 0, N - 1)
            f = iy * N + ix
            m = c == 2
            sm += np.bincount(f[m], z[m], N * N)
            cn += np.bincount(f[m], None, N * N)
            for key, cls in (("bridge", (17,)), ("top", (1, 2, 6, 17)), ("bld", (6,)), ("veg", (3, 4, 5))):
                m = np.isin(c, cls)
                if m.any():
                    o = np.argsort(z[m], kind="stable")  # ascending, last write wins = max
                    ff, zz = f[m][o], z[m][o]
                    g[key][ff] = np.maximum(g[key][ff], zz)
            m = (c == 15) | (c == 1)
            if m.any():
                wire.append(np.c_[x[m] + ox, y[m] + oy, z[m]].astype(np.float32))
    out = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        dtm = np.where(cn > 0, sm / cn, np.nan)
    out["dtm"] = np.where(np.isnan(dtm), ND, _cm(np.nan_to_num(dtm))).reshape(N, N)
    for k, v in g.items():
        out[k] = np.where(v < -1e8, ND, _cm(v)).reshape(N, N)
    # masts: class-15 points, 1 m cells; pole = cell cluster with a vertical extent above local ground
    masts = np.zeros((0, 5), np.float32)
    if wire:
        w = np.concatenate(wire)
        dt = dtm.reshape(N, N).copy()
        # fill dtm holes nearest for height-above-ground
        bad = np.isnan(dt)
        if bad.any() and not bad.all():
            _, (jy, jx) = ndi.distance_transform_edt(bad, return_indices=True)
            dt = dt[jy, jx]
        gi = np.clip(((w[:, 0] - ox) / RES).astype(int), 0, N - 1)
        gj = np.clip(((w[:, 1] - oy) / RES).astype(int), 0, N - 1)
        h = w[:, 2] - dt[gj, gi]
        M = int(T)  # 1 m cells
        ci = np.clip((w[:, 0] - ox).astype(int), 0, M - 1)
        cj = np.clip((w[:, 1] - oy).astype(int), 0, M - 1)
        cf = cj * M + ci
        cnt = np.bincount(cf, minlength=M * M)
        hmax = np.full(M * M, -1e9); hmin = np.full(M * M, 1e9)
        np.maximum.at(hmax, cf, h); np.minimum.at(hmin, cf, h)
        zmax = np.full(M * M, -1e9); np.maximum.at(zmax, cf, w[:, 2])
        # vertical structure: low points near ground and high top; wires are horizontal (small span)
        pole = ((hmax - hmin) >= 2.0) & (cnt >= 3) & (hmin < 2.5) & (hmax >= 3.5)
        pole = pole.reshape(M, M)
        blk = lambda a: (a.reshape(M, 2, M, 2) != ND).any(axis=(1, 3))
        nobuild = ~ndi.binary_dilation(blk(out["bld"]), iterations=1)
        hv = (out["veg"].astype(np.float32) - np.where(out["dtm"] == ND, 0, out["dtm"])) > 100  # canopy > 1 m above ground
        pole &= nobuild & ~blk(np.where(hv, 1, ND).astype(np.int16))
        lab, nl = ndi.label(pole, structure=np.ones((3, 3)))
        rows = []
        if nl:
            idx = np.arange(1, nl + 1)
            cy_, cx_ = np.array(ndi.center_of_mass(pole, lab, idx)).T
            zt = ndi.maximum(zmax.reshape(M, M), lab, idx)
            hb = ndi.minimum(hmin.reshape(M, M), lab, idx)
            ht = ndi.maximum(hmax.reshape(M, M), lab, idx)
            ns = ndi.sum(cnt.reshape(M, M), lab, idx)
            sz = ndi.sum(np.ones((M, M)), lab, idx)
            for a in range(nl):
                if sz[a] <= 12:  # wide clusters = wires on slopes / building edges
                    rows.append((ox + cx_[a] + 0.5, oy + cy_[a] + 0.5, zt[a], zt[a] - ht[a], ns[a]))
        masts = np.array(rows, np.float32).reshape(-1, 5)
    np.savez_compressed(OUT / f"g_{name}.npz", **out, mast=masts, origin=np.array([ox, oy], np.float64))
    return name, npts, int(masts.shape[0])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = 2
    if "-j" in sys.argv:
        jobs = int(sys.argv[sys.argv.index("-j") + 1])
    names = sorted(p.stem for p in RAW.glob("*_*.laz"))
    if "--force" not in sys.argv:
        names = [n for n in names if not (OUT / f"g_{n}.npz").exists()]
    t0 = time.time()
    print(f"{len(names)} tiles, jobs={jobs}", flush=True)
    with ProcessPoolExecutor(jobs) as ex:
        for name, npts, nm in ex.map(build_tile, names):
            print(f"{name} pts={npts/1e6:.1f}M masts={nm} t={time.time()-t0:.0f}s", flush=True)
    print(f"done {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
