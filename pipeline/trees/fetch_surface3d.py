"""Fetch swissSURFACE3D Raster 0.5 m (swisstopo OGD) for the game area into data/raw/surface3d/ (cached, skips existing).
Same tiles as swissALTI3D. nDSM = surface3d - alti3d gives vegetation+building heights. Run: .venv/bin/python pipeline/trees/fetch_surface3d.py"""
import re, sys
from pathlib import Path
from shapely.geometry import box
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import area, fetch_swisstopo as F  # noqa: E402

out = F.RAW / "surface3d"; out.mkdir(parents=True, exist_ok=True)
poly = area.area_lv95()
best = F.newest_per_tile(F.items("ch.swisstopo.swisssurface3d-raster"), re.compile(r"swisssurface3d-raster_(\d{4})_(\d+-\d+)$"))
for tile, f in sorted(best.items()):
    x, y = (int(v) * 1000 for v in tile.split("-"))
    if not poly.intersects(box(x, y, x + 1000, y + 1000)):
        continue
    a = next((v for k, v in f["assets"].items() if k.endswith("_0.5_2056_5728.tif")), None)
    if a:
        F.download(a["href"], out / Path(a["href"]).name)
