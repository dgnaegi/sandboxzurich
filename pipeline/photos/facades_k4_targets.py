"""Kreis 4 facade targets: GWR addresses inside the Stadtkreis 4 polygon (OGD), residential/commercial, >=3 floors or built <=1945.
Writes research/buildings/k4/targets.json. Usage: python facades_k4_targets.py"""
import json, sys
from collections import Counter
from pathlib import Path
from shapely.geometry import Point, shape
sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F, facades_fetch as ff
ROOT = F.ROOT
def main():
    d = json.load(open(ROOT / "data/raw/stadtzh/geo_stadtkreise__adm_stadtkreise_a.geojson"))
    poly = [shape(f["geometry"]) for f in d["features"] if f["properties"]["name"] == 4][0]
    gwr = json.load(open(ROOT / "data/build/gwr_kreise.json"))
    by = {}
    for r in gwr: by.setdefault(r["street"], []).append((r["x"], r["y"]))
    cand = json.load(open(ROOT / "research/buildings/sheets_v3/candidates.json"))
    vn = json.load(open(ROOT / "research/buildings/visual_notes_v3.json"))
    out = []
    for r in gwr:
        la, lo = F.local_ll(r["x"], r["y"])
        if not poly.contains(Point(lo, la)): continue
        if not ((r["floors"] or 0) >= 3 or (r["period"] or 99) <= 12) or r["class"] in (1251, 1252): continue
        a = f"{r['street']} {r['nr']}"
        out.append(dict(sdir=ff.street_dir(by[r["street"]], r["x"], r["y"]), addr=a, street=r["street"], nr=r["nr"], x=r["x"], y=r["y"], lat=la, lon=lo,
                        year=r["year"], floors=r["floors"], period=r["period"], cls=r["class"], cand=a in cand, note=a in vn))
    json.dump(out, open(ROOT / "research/buildings/k4/targets.json", "w"), ensure_ascii=False)
    print(len(out), "targets;", sum(t["cand"] for t in out), "with candidates;", sum(t["note"] for t in out), "with notes")
    for s, n in Counter(t["street"] for t in out).most_common(60): print(s, n, end="; ")
main()
