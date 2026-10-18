"""Idaplatz quarter facade photos: GWR addresses within R m of the square -> best frontal view crops (reuses facades_k4_fetch.work).
Writes research/buildings/ida/{targets,photos}.json, crops in data/raw/photos/ida/facades/. Resumable. Usage: python facades_ida.py [--r 330] [--max N]"""
import json, math, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F, facades_fetch as ff
import facades_k4_fetch as K
import shops_r2_fetch as R

ROOT = F.ROOT
OUT = ROOT / "data/raw/photos/ida/facades"; D = ROOT / "research/buildings/ida"
for d in (OUT / "_api", OUT / "_src", OUT / "crops", D): d.mkdir(parents=True, exist_ok=True)
K.API, K.SRC, K.CR = OUT / "_api", OUT / "_src", OUT / "crops"
R.API, R.SRC = K.API, K.SRC
R.pmx = lambda c: []  # Panoramax search returns HTTP 500 for minutes -> Mapillary only
CX, CY = -125, -1115
rad = float(sys.argv[sys.argv.index("--r") + 1]) if "--r" in sys.argv else 330


def targets():
    gwr = json.load(open(ROOT / "data/build/gwr_kreise.json"))
    by = {}
    for r in gwr: by.setdefault(r["street"], []).append((r["x"], r["y"]))
    vn = json.load(open(ROOT / "research/buildings/visual_notes_v3.json"))
    out = []
    for r in gwr:
        if math.hypot(r["x"] - CX, r["y"] - CY) > rad or r["class"] in (1251, 1252): continue
        la, lo = F.local_ll(r["x"], r["y"]); a = f"{r['street']} {r['nr']}"
        out.append(dict(sdir=ff.street_dir(by[r["street"]], r["x"], r["y"]), addr=a, street=r["street"], nr=r["nr"], x=r["x"], y=r["y"], lat=la, lon=lo,
                        year=r["year"], floors=r["floors"], period=r["period"], cls=r["class"], note=a in vn))
    out.sort(key=lambda t: math.hypot(t["x"] - CX, t["y"] - CY))
    return out


if __name__ == "__main__":
    T = targets(); json.dump(T, open(D / "targets.json", "w"), ensure_ascii=False)
    print(len(T), "targets,", sum(t["note"] for t in T), "already noted")
    META = D / "photos.json"; meta = json.load(open(META)) if META.exists() else {}
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9
    tok = R.token()
    todo = [(i, t) for i, t in enumerate(T) if t["addr"] not in meta][:mx]
    with ThreadPoolExecutor(5) as ex:
        list(ex.map(lambda it: K.work(it[0], it[1], tok, meta), todo))
    json.dump(meta, open(META, "w"), ensure_ascii=False)
    print("with photos", sum(1 for m in meta.values() if m["photos"]), "of", len(meta))
