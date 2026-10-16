"""Langstrasse Sued: GWR entrances (Langstrasse + corner houses of cross streets within 28 m) -> research/shops_v3/entrances_langB.json
(id, addr, x, y, lat, lon). Source: data/raw/gwr (CC BY / OGD)."""
import csv, json, math
from pathlib import Path
from pyproj import Transformer
ROOT = Path(__file__).resolve().parent.parent.parent
t = Transformer.from_crs(2056, 4326, always_xy=True)
rows = []
for r in csv.DictReader(open(ROOT / "data/raw/gwr/eingang_entree_entrata.csv", encoding="utf-8"), delimiter="\t"):
    if r["DPLZ4"] not in ("8004", "8005", "8003") or not r["DKODE"]: continue
    x = float(r["DKODE"]) - 2681400; y = float(r["DKODN"]) - 1248700
    if 440 < x < 1000 and -1010 < y < -330: rows.append((r["STRNAME"], r["DEINR"], x, y, r["EGAID"]))
L = [(x, y) for s, n, x, y, e in rows if s == "Langstrasse" and -1010 < y < -330]
out = []
for s, n, x, y, e in rows:
    if s == "Langstrasse" or min(math.hypot(x - a, y - b) for a, b in L) < 28:
        lo, la = t.transform(x + 2681400, y + 1248700)
        out.append(dict(id="e" + e, addr=f"{s} {n}", x=round(x, 1), y=round(y, 1), lat=la, lon=lo))
json.dump(out, open(ROOT / "research/shops_v3/entrances_langB.json", "w"), ensure_ascii=False)
print(len(out), sum(1 for o in out if o["addr"].startswith("Langstrasse")))
