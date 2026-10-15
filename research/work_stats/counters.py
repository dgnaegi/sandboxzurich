"""Hourly pedestrian profile (FUSS_IN+OUT) for counters inside Kreis 4 polygon, 2024-2025. Prints JSON."""
import csv, glob, collections, json
RAW = "/Users/danielgnagi/gtazurich/data/raw/stats"
poly = json.load(open("/Users/danielgnagi/gtazurich/research/kreise_poly_simplified.json"))
def lv95_to_wgs(E, N):
    y = (E - 2600000) / 1e6; x = (N - 1200000) / 1e6
    lon = 2.6779094 + 4.728982*y + 0.791484*y*x + 0.1306*y*x*x - 0.0436*y**3
    lat = 16.9023892 + 3.238272*x - 0.270978*y*y - 0.002528*x*x - 0.0447*y*y*x - 0.0140*x**3
    return lat*100/36, lon*100/36
def inside(pt, poly):  # ray casting; poly = [[lat, lon], ...]
    lat, lon = pt; c = False; n = len(poly)
    for i in range(n):
        a = poly[i]; b = poly[(i+1) % n]
        if (a[0] > lat) != (b[0] > lat) and lon < (b[1]-a[1])*(lat-a[0])/(b[0]-a[0]+1e-12)+a[1]:
            c = not c
    return c
K4 = poly["Kreis 4"]
rows = []
for f in sorted(glob.glob(f"{RAW}/*verkehrszaehlungen_werte_fussgaenger_velo*2025*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        rows.append(r)
stations = {}
for r in rows:
    key = r["FK_STANDORT"]
    if key not in stations:
        try: E, N = float(r["OST"]), float(r["NORD"])
        except: continue
        stations[key] = lv95_to_wgs(E, N)
k4 = {k for k, p in stations.items() if inside(p, K4)}
prof = collections.defaultdict(lambda: collections.defaultdict(float)); days = collections.defaultdict(set)
from datetime import datetime
for r in rows:
    if r["FK_STANDORT"] not in k4: continue
    try: dt = datetime.fromisoformat(r["DATUM"])
    except: continue
    if dt.year != 2025: continue
    try: v = float(r["VELO_IN"] or 0) + float(r["VELO_OUT"] or 0)  # Kreis-4 counters are velo-only
    except: continue
    grp = "fri_sat" if dt.weekday() in (4, 5) else "wkday_mo_do"
    prof[grp][dt.hour] += v * (4 if False else 1)
    days[grp].add(dt.date())
out = {"counters_in_kreis4_velo_2025": len(k4), "n_days": {g: len(days[g]) for g in days}}
for g in prof:
    tot = sum(prof[g].values()) or 1
    out[g + "_hour_share_pct"] = [round(100 * prof[g][h] / tot, 2) for h in range(24)]
json.dump(out, open("/Users/danielgnagi/gtazurich/research/work_stats/counter_profile.json", "w"))
print(json.dumps({k: v for k, v in out.items() if not k.endswith("pct")}, ensure_ascii=False))
print([round(x, 1) for x in out.get("fri_sat_hour_share_pct", [])])
print([round(x, 1) for x in out.get("wkday_mo_do_hour_share_pct", [])])
