"""Collect all located local photos (any research/*.json with lat/lon/heading/file) near the Zone-4-south camera points and Birmensdorferstrasse.
Writes research/zones/z4/corners_south_cands.json (best photo per ~35 m cell/heading octant)."""
import glob, json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from zones import wgs_to_local

CAMS = {"Gertrudstrasse": (-149.2, -1235.4), "Aemtler/Wiesendangerstr": (-229.6, -1220.9), "Goldbrunnenplatz": (-191.3, -1515.9),
        "Friedhof Sihlfeld": (-405.3, -939.1), "Schmiede": (265, -1562), "Bhf Wiedikon": (455, -1441), "Ortsmuseum": (239, -1732), "Kalkbreite": (355, -1094)}


def walk(o, out):
    if isinstance(o, dict):
        if "lat" in o and "lon" in o and "file" in o and o.get("heading") is not None:
            out.append(o)
        else:
            for v in o.values(): walk(v, out)
    elif isinstance(o, list):
        for v in o: walk(v, out)


def birm_pts():
    d = json.load(open(ROOT / "web/public/data/districts.json"))
    pts = []
    for s in d["streets"]:
        if s["n"].startswith("Birmensdorferstr"):
            p = s["p"]
            for a, b in zip(p, p[1:]):
                n = max(1, int(math.dist(a, b) / 10))
                pts += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n)]
    return pts


def main():
    allp, seen = [], set()
    for f in glob.glob(str(ROOT / "research/**/*.json"), recursive=True):
        if "cands" in f: continue
        try: o = json.load(open(f))
        except Exception: continue
        l = []; walk(o, l)
        for p in l:
            if p["file"] in seen: continue
            seen.add(p["file"]); allp.append(p)
    bp = birm_pts(); res = []
    for p in allp:
        if p.get("night") or not (ROOT / p["file"]).exists(): continue
        x, y = wgs_to_local(p["lat"], p["lon"])
        near = [n for n, c in CAMS.items() if math.dist((x, y), c) < 80]
        bd = min((math.dist((x, y), q) for q in bp), default=999)
        if near or bd < 25:
            res.append(dict(file=p["file"], x=round(x, 1), y=round(y, 1), h=p["heading"], year=p.get("year"), src=p.get("source"), author=p.get("author"), url=p.get("url"), near=near[0] if near else "Birmensdorferstr"))
    print(len(allp), "photos total,", len(res), "in area,", len(bp), "birm pts; bbox of birm:", (min(q[0] for q in bp), max(q[0] for q in bp), min(q[1] for q in bp), max(q[1] for q in bp)))
    json.dump(res, open(ROOT / "research/zones/z4/corners_south_cands.json", "w"), indent=0)
    from collections import Counter
    print(Counter(r["near"] for r in res))
main()
