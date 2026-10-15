"""nDSM (canopy height) cache: swissSURFACE3D (DSM) minus swissALTI3D (DTM), 0.5 m -> 1 m max-pool,
building footprints (swissBUILDINGS3D, buffered 1 m) set to NaN. One float16 .npy per 1 km tile in data/build/ndsm/.
Run: .venv/bin/python pipeline/trees/ndsm.py   (inputs: data/raw/surface3d, data/raw/alti3d; swisstopo OGD)"""
import re, sys, pickle
from pathlib import Path
import numpy as np, tifffile
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import Polygon
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import ROOT  # noqa: E402

E0, N0 = 2681400.0, 1248700.0
OUT = ROOT / "data/build/ndsm"


def footprints():
    out = []
    for f in sorted((ROOT / "data/build/bld").glob("*.pkl")):
        for b in pickle.load(open(f, "rb")):
            rings = [Polygon(p[:, :2]).buffer(0) for k, p in b["polys"] if k == 0 and len(p) >= 4]
            rings = [r for r in rings if not r.is_empty]
            if rings:
                out.append(shapely.union_all(rings).buffer(1.0))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    flist = footprints()
    tree = shapely.STRtree(flist)
    print("footprints", len(flist))
    for f in sorted((ROOT / "data/raw/surface3d").glob("*.tif")):
        m = re.search(r"_(\d{4})-(\d{4})_", f.name)
        e, n = int(m[1]) * 1000, int(m[2]) * 1000
        dtm = next((ROOT / "data/raw/alti3d").glob(f"swissalti3d_*_{m[1]}-{m[2]}_*.tif"), None)
        if dtm is None:
            continue
        a = tifffile.imread(f).astype(np.float32) - tifffile.imread(dtm).astype(np.float32)
        a[~np.isfinite(a) | (a < -50) | (a > 80)] = np.nan
        a = np.nanmax(a.reshape(1000, 2, 1000, 2), axis=(1, 3)) if False else np.fmax.reduce([a[i::2, j::2] for i in (0, 1) for j in (0, 1)])
        x0, y1 = e - E0, n + 1000 - N0  # local x of left edge, local y of top edge
        im = Image.new("1", (1000, 1000), 0)
        d = ImageDraw.Draw(im)
        for i in tree.query(shapely.box(x0, y1 - 1000, x0 + 1000, y1)):
            g = flist[i]
            for p in getattr(g, "geoms", [g]):
                d.polygon([(px - x0, y1 - py) for px, py in p.exterior.coords], fill=1)
        a[np.asarray(im, bool)] = np.nan
        np.save(OUT / f"{e // 1000}-{n // 1000}.npy", a.astype(np.float16))
        print(f.name, "done", flush=True)


if __name__ == "__main__":
    main()
