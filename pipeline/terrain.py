"""Real terrain from swissALTI3D (DTM, 0.5 m GeoTIFF, LV95) -> mesh.Heights in local metres."""
import re
import numpy as np
import tifffile
from config import ROOT
from mesh import Heights

E0, N0, H0 = 2681400.0, 1248700.0, 408.0
RAW = ROOT / "data" / "raw" / "alti3d"
CACHE = ROOT / "data" / "build"


def _tiles():
    """Yield (path, left_E, top_N) from file names (km SW corner -> top-left = (E, N+1000))."""
    for f in sorted(RAW.glob("swissalti3d_*.tif")):
        m = re.search(r"_(\d{4})-(\d{4})_", f.name)
        if m:
            yield f, int(m[1]) * 1000.0, (int(m[2]) + 1) * 1000.0


def despike(x0, y0, step, z, z_shift=0.0, report=False):
    """Remove isolated pits/spikes of the raw swissALTI3D grid (research/ground_audit/audit.md: 1-3 cell wells 1-4 m deep on flat roads, e.g.
    Stauffacherstrasse (990,-1202)). A cell is replaced by the 5x5 median only when ALL hold: it deviates > 0.7 m from that median, the LiDAR
    DTM (data/build/lidar, class 2) contradicts it (|z - dtm| > 0.6) but agrees with the median (< 0.6), the DTM itself is flat there
    (4 cardinal samples at 4 m within 0.5 m) and no building/bridge return is within 3 m. Without LiDAR grids nothing changes. z: grid in the
    frame of z_shift (game frame = z + z_shift; only meaningful for z_shift = -3.06). Returns (z, n_changed)."""
    from scipy.ndimage import median_filter
    if abs(z_shift + 3.06) > 1e-6:
        return z, 0
    med = median_filter(z, size=5, mode="nearest")
    cand = np.argwhere(np.abs(z - med) > 0.7)
    if not len(cand):
        return z, 0
    try:
        import lidar
    except Exception:
        return z, 0
    j, i = cand[:, 0], cand[:, 1]
    x, y = x0 + i * step, y0 + j * step
    zg, mg = z[j, i] + z_shift, med[j, i] + z_shift
    d = lidar.dtm(x, y)
    with np.errstate(invalid="ignore"):
        ok = ~np.isnan(d) & (np.abs(zg - d) > 0.6) & (np.abs(mg - d) < 0.6)
        for ox, oy in ((4, 0), (-4, 0), (0, 4), (0, -4)):
            ok &= np.abs(lidar.dtm(x + ox, y + oy) - d) < 0.5          # NaN -> False
    for ox, oy in ((0, 0), (3, 0), (-3, 0), (0, 3), (0, -3)):
        ok &= np.isnan(lidar.bld(x + ox, y + oy)) & np.isnan(lidar.bridge(x + ox, y + oy))
    if not ok.any():
        return z, 0
    z = z.copy()
    z[j[ok], i[ok]] = med[j[ok], i[ok]]
    if report:
        print(f"terrain.despike: {int(ok.sum())} pit/spike cells levelled (of {len(cand)} candidates)")
    return z, int(ok.sum())


def heights(area=(600.0, -1000.0, 1200.0, -400.0), step=1.0, z_shift=0.0):
    """z_shift is added to the result (not cached); building bases sit ~3.06 m below the DTM -> z_shift=-3.06."""
    x0, y0, x1, y1 = area
    key = f"{int(x0)}_{int(y0)}_{int(x1)}_{int(y1)}_{step:g}"
    cf = CACHE / f"terrain_{key}.npz"
    if cf.exists():
        d = np.load(cf)
        zc, _ = despike(float(d["x0"]), float(d["y0"]), float(d["step"]), d["z"], z_shift, report=True)
        return Heights(float(d["x0"]), float(d["y0"]), float(d["step"]), zc + z_shift)
    xs = np.arange(x0, x1 + step * 0.5, step)
    ys = np.arange(y0, y1 + step * 0.5, step)
    z = np.full((len(ys), len(xs)), np.nan, np.float32)
    px = 0.5
    for f, left, top in _tiles():
        lx, ty = left - E0, top - N0  # local x of left edge, local y of top edge
        w = 2000
        ix = np.where((xs >= lx) & (xs < lx + w * px))[0]
        iy = np.where((ys <= ty) & (ys > ty - w * px))[0]
        if not len(ix) or not len(iy):
            continue
        a = tifffile.imread(f).astype(np.float32)  # row 0 = north
        a[a < -1000] = np.nan
        # bilinear at pixel-centre coordinates
        fc = np.clip((xs[ix] - lx) / px - 0.5, 0, w - 1.001)
        fr = np.clip((ty - ys[iy]) / px - 0.5, 0, w - 1.001)
        c0, r0 = fc.astype(int), fr.astype(int)
        tc, tr = (fc - c0)[None, :], (fr - r0)[:, None]
        R0, R1, C0, C1 = r0[:, None], (r0 + 1)[:, None], c0[None, :], (c0 + 1)[None, :]
        v = (a[R0, C0] * (1 - tc) * (1 - tr) + a[R0, C1] * tc * (1 - tr)
             + a[R1, C0] * (1 - tc) * tr + a[R1, C1] * tc * tr)
        z[np.ix_(iy, ix)] = v
    if np.isnan(z).any():
        n = int(np.isnan(z).sum())
        print(f"terrain: {n} cells without data, filled with nearest row/col mean")
        z[np.isnan(z)] = np.nanmean(z) if not np.isnan(z).all() else H0
    z -= H0
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cf, x0=x0, y0=y0, step=step, z=z)
    z, _ = despike(x0, y0, step, z, z_shift, report=True)   # after the cache write: the cache keeps the raw swissALTI3D
    return Heights(x0, y0, step, z + z_shift)
