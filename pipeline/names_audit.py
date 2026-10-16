"""Coverage of real names/labels in the built tiles (summary <= 30 lines).  .venv/bin/python pipeline/names_audit.py [outfile]
Compares tile meta (web/public/tiles/t_*.json) against OSM POIs (research/pois_*_osm.csv), GWR entrances, OSM junctions."""
import csv, glob, json, re, sys
from collections import defaultdict
import numpy as np


class cKDTree:
    def __init__(self, pts, cell=40.0):
        self.p, self.c, self.g = list(pts), cell, defaultdict(list)
        for i, (x, y) in enumerate(self.p):
            self.g[int(x // cell), int(y // cell)].append(i)

    def query_ball_point(self, q, r):
        cx, cy, k = int(q[0] // self.c), int(q[1] // self.c), int(r // self.c) + 1
        return [i for a in range(cx - k, cx + k + 1) for b in range(cy - k, cy + k + 1) for i in self.g.get((a, b), [])
                if (self.p[i][0] - q[0]) ** 2 + (self.p[i][1] - q[1]) ** 2 <= r * r]

from config import ROOT, AREA

OX, OY = 2681400.0, 1248700.0
import os
_TL = [tuple(map(int, t.split("_"))) for t in os.environ.get("NAMES_TILES", "").split(",") if t]  # e.g. 3_-4,2_-4: audit only these tiles


def inreg(x, y):
    return not _TL or (int(x // 200), int(y // 200)) in _TL
T = defaultdict(list)
for f in [f for f in glob.glob(str(ROOT / "web/public/tiles/t_*.json")) if not _TL or tuple(map(int, f.split("t_")[1][:-5].split("_"))) in _TL]:
    m = json.load(open(f))
    for k in ("signs", "housenumbers", "streetsigns", "trafficsigns", "landmarks"):
        T[k] += m.get(k, [])
sx = [(s["x"], s["y"], s["name"].lower(), str(s["osm"])) for s in T["signs"]]
lm = json.load(open(ROOT / "web/public/data/landmarks.json"))
lm = next(iter(lm.values())) if isinstance(lm, dict) else lm
named = [(r["x"], r["y"], r["name"].lower(), "") for r in lm]
for r in json.load(open(ROOT / "web/public/data/landmarks.json")).values():
    pass
sg = [(r[0], r[1], r[4].lower()) for r in T["streetsigns"]]
SIGN = sx + named
tree = cKDTree([(a, b) for a, b, *_ in SIGN]) if SIGN else None

def has_sign(x, y, name, oid):
    n = name.lower()
    for i in tree.query_ball_point((x, y), 70):
        s = SIGN[i]
        if s[3] == oid or s[2] == n or n in s[2] or s[2] in n:
            return True
    return False

CATS = {
 "Laeden (shop=*)": lambda k, n: k.startswith("shop=") and k not in ("shop=hairdresser", "shop=kiosk", "shop=supermarket"),
 "Gastro/Lokale": lambda k, n: k.split("=")[-1] in ("restaurant", "cafe", "bar", "pub", "fast_food", "nightclub", "ice_cream"),
 "Schulen": lambda k, n: k in ("amenity=school", "amenity=college", "amenity=university"),
 "Kindergaerten/Kitas": lambda k, n: k in ("amenity=kindergarten", "amenity=childcare"),
 "Kirchen": lambda k, n: k == "amenity=place_of_worship",
 "GZ/Quartiertreff": lambda k, n: k == "amenity=community_centre",
 "Bibliotheken": lambda k, n: k == "amenity=library",
 "Apotheken": lambda k, n: k == "amenity=pharmacy",
 "Aerzt:innen": lambda k, n: k in ("amenity=doctors", "amenity=dentist", "healthcare=doctor"),
 "Coiffeure": lambda k, n: k == "shop=hairdresser",
 "Kioske": lambda k, n: k == "shop=kiosk",
 "Grossverteiler": lambda k, n: bool(re.match(r"(migros|coop|denner|aldi|lidl|volg|spar)\b", n.lower())) or k == "shop=supermarket",
}
tot = defaultdict(int); ok = defaultdict(int)
for f in glob.glob(str(ROOT / "research/pois_kreis?_osm.csv")):
    for r in csv.DictReader(open(f)):
        x, y = float(r["x"]), float(r["y"])
        if not (AREA[0] <= x <= AREA[2] and AREA[1] <= y <= AREA[3]) or not inreg(x, y):
            continue
        for c, fn in CATS.items():
            if fn(r["kind"], r["name"]):
                tot[c] += 1
                ok[c] += has_sign(x, y, r["name"], r["osm_id"][1:])
out = [f"tiles: signs {len(T['signs'])}, housenumbers {len(T['housenumbers'])}, streetsigns {len(T['streetsigns'])}, trafficsigns {len(T['trafficsigns'])}"]
for c in CATS:
    out.append(f"{c:22s} {ok[c]:5d}/{tot[c]:5d} = {100 * ok[c] / max(1, tot[c]):3.0f}%")
# house numbers vs GWR entrances
hn = ([(r[0], r[1]) for r in T["housenumbers"]]); hnt = [str(r[5]).lower() for r in T["housenumbers"]]
ht = cKDTree(hn)
n = hit = 0
for r in csv.DictReader(open(ROOT / "data/raw/gwr/eingang_entree_entrata.csv"), delimiter="\t"):
    if r["DPLZNAME"] != "Zürich" or not r["DKODE"]:
        continue
    x, y = float(r["DKODE"]) - OX, float(r["DKODN"]) - OY
    if not (AREA[0] <= x <= AREA[2] and AREA[1] <= y <= AREA[3]) or not inreg(x, y):
        continue
    n += 1
    hit += any(hnt[i] == r["DEINR"].lower() for i in ht.query_ball_point((x, y), 20))
out.append(f"Hausnummer GWR-Eingang    {hit:5d}/{n:5d} = {100 * hit / max(1, n):3.0f}%")
# junction street signs
import addresses
d = addresses._data(); ways = addresses._streets(AREA)
by = defaultdict(set); pos = {}
for name, ids, pts in ways:
    for nid in ids:
        if nid in d["nodes"]:
            by[nid].add(name); pos[nid] = d["nodes"][nid]
st = cKDTree([(a, b) for a, b, _ in sg])
jn = jh = 0
for nid, names in by.items():
    p = pos[nid]
    if len(names) < 2 or not (AREA[0] <= p[0] <= AREA[2] and AREA[1] <= p[1] <= AREA[3]) or not inreg(*p):
        continue
    for nm in names:
        jn += 1
        jh += any(sg[i][2] == nm.lower() for i in st.query_ball_point(p, 40))
out.append(f"Kreuzung Strassenschild   {jh:5d}/{jn:5d} = {100 * jh / max(1, jn):3.0f}%")
tr = json.load(open(ROOT / "web/public/data/transit.json"))["lines"]
stops = {s["name"] for l in tr for s in l.get("stops", [])}
out.append(f"Haltestellen mit Name: {len(stops)} (alle Masten tragen Namen, stops.ts)")
out.append("Velo-/Fussweg-Wegweiser: 0 (nicht vorhanden)")
txt = "\n".join(out); print(txt)
if len(sys.argv) > 1:
    open(sys.argv[1], "w").write(txt + "\n")
if "--miss" in sys.argv:
    import random
    random.seed(1)
    miss = []
    for f in glob.glob(str(ROOT / "research/pois_kreis?_osm.csv")):
        for r in csv.DictReader(open(f)):
            x, y = float(r["x"]), float(r["y"])
            if AREA[0] <= x <= AREA[2] and AREA[1] <= y <= AREA[3] and CATS["Laeden (shop=*)"](r["kind"], r["name"]) and not has_sign(x, y, r["name"], r["osm_id"][1:]):
                miss.append((r["osm_id"], r["name"], r["kind"], x, y))
    print(len(miss)); [print(m) for m in random.sample(miss, 8)]
