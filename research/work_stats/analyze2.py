"""Jobs per Kreis, nationalities per Kreis, weekly residents, hotel guests. Prints compact JSON."""
import csv, glob, collections, json
RAW = "/Users/danielgnagi/gtazurich/data/raw/stats"
KREISE = ["3", "4", "5", "9"]
def rd(pat, delim=",", enc="utf-8-sig"):
    return csv.DictReader(open(glob.glob(f"{RAW}/{pat}")[0], encoding=enc), delimiter=delim)
out = {}
# --- jobs by Kreis (quarter -> Kreis = quartier code // 10)
jobs = collections.defaultdict(lambda: collections.defaultdict(int)); qn = {}
for r in rd("*noga*.csv", ";", "cp1252"):
    y = r["Jahr"]; q = int(r["Stadtquartier (num)"]); k = str(q // 10)
    v = r["Besch�ftigte total"] if "Besch�ftigte total" in r else r.get("Beschäftigte total", "0")
    try: v = int(float(v.replace(",", ".")))
    except: v = 0
    jobs[(y, k)][r["Abteilung NOGA2008 Name (2. Stufe)"] if False else "total"] += v
    jobs[(y, "Stadt")]["total"] += v
    if k in KREISE: qn[q] = r["Stadtquartier (Name)"]
years = sorted({y for y, _ in jobs}); Y = years[-1]
out["jobs_year"] = Y  # NOTE: only 2001/2005/2008 exist in this OGD dataset
out["jobs_by_kreis"] = {k: jobs[(Y, k)]["total"] for k in KREISE + ["Stadt"]}
out["quartier_names_kreis4_5"] = {q: n for q, n in sorted(qn.items())}
# --- weekly residents (Wochenaufenthalter) by Kreis, latest year
wa = collections.defaultdict(int)
Yw = None
rows = list(rd("*woauha*.csv"))
Yw = max(r["StichtagDatJahr"] for r in rows)
for r in rows:
    if r["StichtagDatJahr"] != Yw: continue
    wa[r["KreisCd"]] += int(r["AnzBestWir"]); wa["Stadt"] += int(r["AnzBestWir"])
out["weekly_residents"] = {"year": Yw, **{k: wa[k] for k in KREISE + ["Stadt"]}}
# --- nationalities by Kreis (latest year) top 8 per Kreis
nat = collections.defaultdict(lambda: collections.defaultdict(int)); popk = collections.defaultdict(int)
Yn = None
rows = list(rd("*nationalitaet*.csv"))
Yn = max(r["StichtagDatJahr"] for r in rows)
for r in rows:
    if r["StichtagDatJahr"] != Yn: continue
    q = int(r["QuarSort"]); k = str(q // 10); n = int(r["AnzBestWir"])
    for kk in (k, "Stadt"):
        nat[kk][r["NationLang"]] += n; popk[kk] += n
out["nationality_year"] = Yn
out["top_nationalities"] = {kk: [(nm, round(v / popk[kk], 3)) for nm, v in sorted(nat[kk].items(), key=lambda x: -x[1])[:8]] for kk in KREISE + ["Stadt"]}
out["nationalities_count"] = {kk: len(nat[kk]) for kk in KREISE + ["Stadt"]}
# --- hotel guests (city) by year, monthly shares 2025
hot = collections.defaultdict(float); kind = collections.Counter()
for r in rd("*od1104*.csv"):
    kind[r["Kennzahl"]] += 0
    if r["StichtagDatMMYY"][:4] == "2025":
        hot[(r["Kennzahl"], r["StichtagDatMMYY"][5:7])] += float(r["Anzahl"] or 0)
out["hotel_kennzahlen"] = sorted(kind)
tot = sum(v for (k, m), v in hot.items() if k == "Logiernächte") or 1
out["hotel_2025_logiernaechte_total"] = round(tot)
out["hotel_2025_monthly_share_logiernaechte"] = {m: round(v / tot, 3) for (k, m), v in sorted(hot.items()) if k == "Logiernächte"}
# residents 2008 by Kreis (od3242) for jobs-to-residents ratio (jobs data only goes to 2008)
res08 = {}
for r in rd("*od3242*.csv"):
    if r["StichtagDatJahr"] == "2008": res08[r["KreisLang"].split()[-1]] = int(r["AnzBestWir"])
out["jobs_2008_per_resident_2008"] = {k: round(jobs[("2008", k)]["total"] / res08[k], 2) for k in KREISE}
out["jobs_2008_share_of_city"] = {k: round(jobs[("2008", k)]["total"] / jobs[("2008", "Stadt")]["total"], 3) for k in KREISE}
out["residents_2008"] = {k: res08.get(k) for k in KREISE}
print(json.dumps(out, ensure_ascii=False, indent=1))
