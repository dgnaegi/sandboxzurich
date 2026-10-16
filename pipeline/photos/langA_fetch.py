"""Langstrasse Nord (Limmatplatz -> Unterfuehrung): frontal facade crops from Panoramax/Mapillary 360 images.
Targets: points every ~7 m on both sides of the street axis. Reuses shops_r2_fetch (crop/pick). Output data/raw/photos/langstrasse/, meta research/langstrasse_A_photos.json"""
import json, sys, math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shops_r2_fetch as r2
import sources
from shapely.geometry import LineString
ROOT = r2.ROOT
r2.OUT = ROOT / "data/raw/photos/langstrasse"; r2.API = r2.OUT / "_api"; r2.SRC = r2.OUT / "_src"
AXIS = [(940, -260), (954, -231), (979, -189), (1043, -74), (1081, -6), (1104, 36), (1125, 80)]
META = ROOT / "research/langstrasse_A_photos.json"

def targets(step=7.0, off=9.5):
    L = LineString(AXIS); out = []
    s = 0.0
    while s < L.length:
        p = L.interpolate(s); q = L.interpolate(min(s + 1, L.length)); d = np.array([q.x - p.x, q.y - p.y]); d /= np.hypot(*d)
        for side, sg in (("L", 1), ("R", -1)):
            x, y = p.x + sg * -d[1] * off, p.y + sg * d[0] * off
            lo, la = sources.lv95_to_wgs(sources.geo.ORIGIN_E + x, sources.geo.ORIGIN_N + y) if False else (None, None)
            out.append(dict(id=f"ls{int(s):03d}{side}", x=x, y=y, s=s, side=side, name=f"Langstrasse s={int(s)}{side}", address="", kind="facade", area="Langstrasse"))
        s += step
    return out

if __name__ == "__main__":
    import inspect
    tok = r2.token(); meta = json.load(open(META)) if META.exists() else {}
    cs = targets()
    for c in cs:
        r = sources.geo.lv95_to_wgs(sources.geo.ORIGIN_E + c["x"], sources.geo.ORIGIN_N + c["y"])
        c["lon"], c["lat"] = (r[0], r[1]) if r[0] < 20 else (r[1], r[0])
    todo = [c for c in cs if c["id"] not in meta]
    r2.log(len(todo), "targets")
    with ThreadPoolExecutor(6) as ex:
        list(ex.map(lambda c: r2.work(c, tok, meta), todo))
    json.dump(meta, open(META, "w"), ensure_ascii=False, indent=0)
    n = sum(len(v["photos"]) for v in meta.values()); r2.log("FINISHED", len(meta), "targets", n, "photos")
