"""GWR (BFS building register, OGD) -> data/build/gwr_kreise.json for Kreise 3/4/5/9.

Run:  python3 pipeline/gwr.py [--test]
Use:  from gwr import gwr_for_building;  g = gwr_for_building(footprint_xy)  # local metres
Source: BFS GWR, https://public.madd.bfs.admin.ch/zh.zip (cached in data/raw/gwr/).
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "gwr"
OUT = ROOT / "data" / "build" / "gwr_kreise.json"
POLY = ROOT / "research" / "kreise_poly_simplified.json"
OX, OY = 2681400.0, 1248700.0
KEYS = ["egid", "x", "y", "street", "nr", "year", "period", "floors", "flats", "class", "class_txt", "area"]
_cache = {}


def _int(s):
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def build():
    from pyproj import Transformer
    from shapely.geometry import Polygon, Point
    from shapely.prepared import prep
    t = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    polys = []
    for name, ring in json.load(open(POLY)).items():
        if name.split()[-1] in ("3", "4", "9") or name == "Industriequartier":  # Kreis 5
            polys.append(prep(Polygon([t.transform(lon, lat) for lat, lon in ring])))
    codes = {}
    for r in csv.DictReader(open(RAW / "kodes_codes_codici.csv"), delimiter="\t"):
        if r["CMERKM"] == "GKLAS":
            codes[int(r["CECODID"])] = r["CODTXTLD"].replace("  ", " ")
    addr = {}
    for r in csv.DictReader(open(RAW / "eingang_entree_entrata.csv"), delimiter="\t"):
        e = int(r["EGID"])
        if e not in addr and r["STRNAME"]:
            addr[e] = (r["STRNAME"], r["DEINR"])
    rows = []
    for r in csv.DictReader(open(RAW / "gebaeude_batiment_edificio.csv"), delimiter="\t"):
        if r["GDEKT"] != "ZH" or r["GGDENR"] != "261" or not r["GKODE"] or r["GSTAT"] != "1004":
            continue
        e, n = float(r["GKODE"]), float(r["GKODN"])
        p = Point(e, n)
        if not any(pp.contains(p) for pp in polys):
            continue
        egid = int(r["EGID"])
        st, nr = addr.get(egid, ("", ""))
        k = _int(r["GKLAS"])
        per = _int(r["GBAUP"])
        rows.append([egid, round(e - OX, 1), round(n - OY, 1), st, nr, _int(r["GBAUJ"]),
                     per - 8000 if per else None, _int(r["GASTW"]), _int(r["GANZWHG"]), k,
                     codes.get(k, ""), _int(r["GAREA"])])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump([dict(zip(KEYS, v)) for v in rows], open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
    print(len(rows), "GWR buildings ->", OUT)


def _load():
    if "t" not in _cache:
        import numpy as np
        d = json.load(open(OUT))
        _cache["d"] = d
        _cache["t"] = np.array([(g["x"], g["y"]) for g in d])
    return _cache["d"], _cache["t"]


def gwr_for_building(footprint, max_dist=8.0):
    """footprint: Nx2 local metres. Returns GWR dict: point-in-polygon (largest area if several),
    else nearest point within max_dist of the polygon; None otherwise."""
    from shapely.geometry import Polygon, Point
    d, t = _load()
    poly = Polygon(footprint)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty:
        return None
    minx, miny, maxx, maxy = poly.bounds
    c = poly.centroid
    rad = max(maxx - minx, maxy - miny) / 2 + max_dist + 1
    best, bd = None, 1e9
    import numpy as np
    for i in np.nonzero((abs(t[:, 0] - c.x) < rad) & (abs(t[:, 1] - c.y) < rad))[0]:
        g = d[i]
        dist = poly.distance(Point(g["x"], g["y"]))
        if dist == 0:
            dist = -(g["area"] or 0) / 1e6  # inside: prefer larger footprint
        if dist < bd and dist <= max_dist:
            best, bd = g, dist
    return best


def test():
    import collections
    sys.path.insert(0, str(Path(__file__).parent))
    import sources
    bs = sources.buildings()
    hit = 0
    per = collections.Counter()
    cls = collections.Counter()
    for b in bs:
        for _, p in b["polys"]:
            g = gwr_for_building(p)
            if g:
                hit += 1
                per[g["period"]] += 1
                cls[g["class_txt"]] += 1
                break
    print(f"{hit}/{len(bs)} = {hit/len(bs):.0%} with GWR")
    print("period", sorted(per.items(), key=lambda kv: (kv[0] is None, kv[0])))
    print("class", cls.most_common(8))


if __name__ == "__main__":
    build() if "--test" not in sys.argv else test()
