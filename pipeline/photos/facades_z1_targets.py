"""Zone 1 (Kreis 5 Industrie, south of the Limmat) facade targets: GWR addresses in the zone rectangle on the main streets, without a note in visual_notes_v3.json.
Sorted by distance to the nearest camera point (zones.json). Writes research/zones/z1/targets.json. Usage: python facades_z1_targets.py"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parent.parent))
from zones import inside
import fetch_v3 as F, facades_fetch as ff
ROOT = F.ROOT
def main():
    z = [v for v in json.load(open(ROOT / "pipeline/overrides/zones.json"))["zones"] if v["id"] == 1][0]
    poly = z["polys"][0]
    cams = [(c["x"], c["y"]) for c in z["cams"]]
    gwr = json.load(open(ROOT / "data/build/gwr_kreise.json"))
    by = {}
    for r in gwr: by.setdefault(r["street"], []).append((r["x"], r["y"]))
    vn = json.load(open(ROOT / "research/buildings/visual_notes_v3.json"))
    zf = json.load(open(ROOT / "research/zones/zone2_facades.json"))["entries"]
    out = []
    for r in gwr:
        if not inside(poly, r["x"], r["y"]): continue
        if r["class"] in (1251, 1252, 1271, 1272): continue
        a = f"{r['street']} {r['nr']}"
        if a in vn or a in zf: continue
        la, lo = F.local_ll(r["x"], r["y"])
        dc = min(math.hypot(r["x"] - cx, r["y"] - cy) for cx, cy in cams)
        out.append(dict(sdir=ff.street_dir(by[r["street"]], r["x"], r["y"]), addr=a, street=r["street"], nr=r["nr"], x=r["x"], y=r["y"], lat=la, lon=lo,
                        year=r["year"], floors=r["floors"], period=r["period"], cls=r["class"], dcam=round(dc)))
    out.sort(key=lambda t: t["dcam"])
    (ROOT / "research/zones/z1").mkdir(exist_ok=True)
    json.dump(out, open(ROOT / "research/zones/z1/targets.json", "w"), ensure_ascii=False)
    print(len(out), "targets; within 150 m of a camera:", sum(t["dcam"] < 150 for t in out))
main()
