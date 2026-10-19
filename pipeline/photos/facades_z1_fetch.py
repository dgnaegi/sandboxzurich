"""Zone 1 facade photos: reuses facades_k4_fetch (pick/crop) on research/zones/z1/targets.json. Crops -> data/raw/photos/facades/z1/crops,
meta -> research/zones/z1/photos.json. Resumable. Usage: python facades_z1_fetch.py [--relax] [--pass2] [--max N]"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import facades_k4_fetch as K
R, ROOT = K.R, K.ROOT
CR = ROOT / "data/raw/photos/facades/z1/crops"; CR.mkdir(parents=True, exist_ok=True)
K.CR = CR
PASS3 = "--pass3" in sys.argv   # still unnoted: widest selection (90 m, oblique 88 deg)
PASS2 = "--pass2" in sys.argv or PASS3   # remaining targets without a note, much looser photo selection (distance 60 m, oblique 85 deg)
if PASS2: K.DMAX, K.DIFF, K.OBL = (90, 90, 88) if PASS3 else (60, 60, 85)
META = ROOT / "research/zones/z1" / ("photos3.json" if PASS3 else "photos2.json" if PASS2 else "photos.json")
OFF = 1300000 if PASS3 else 1200000 if PASS2 else 1100000
if __name__ == "__main__":
    mx = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10**9
    T = json.load(open(ROOT / "research/zones/z1/targets.json"))
    meta = json.load(open(META)) if META.exists() else {}
    tok = R.token()
    if PASS2:
        vn = json.load(open(ROOT / "research/buildings/visual_notes_v3.json")); T = [t for t in T if t["addr"] not in vn]
        if PASS3:
            have = {a for f in ("photos.json", "photos2.json") for a, m in json.load(open(ROOT / "research/zones/z1" / f)).items() if m["photos"]}
            T = [t for t in T if t["addr"] not in have]
    todo = [(i, t) for i, t in enumerate(T) if t["addr"] not in meta or ("--relax" in sys.argv and not meta[t["addr"]]["photos"])][:mx]
    R.log(len(todo), "to do"); n = 0
    with ThreadPoolExecutor(6) as ex:
        for _ in ex.map(lambda it: K.work(OFF + it[0], it[1], tok, meta), todo):
            n += 1
            if n % 50 == 0:
                json.dump(meta, open(META, "w"), ensure_ascii=False); R.log(n, "done,", sum(1 for m in meta.values() if m["photos"]), "with photos")
    json.dump(meta, open(META, "w"), ensure_ascii=False); R.log("finished", len(meta), sum(1 for m in meta.values() if m["photos"]), "with photos")
