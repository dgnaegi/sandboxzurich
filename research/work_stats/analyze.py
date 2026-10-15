"""Aggregate Stadt Zuerich OGD CSVs (data/raw/stats) for Kreise 3,4,5,9 and city total. Prints JSON."""
import csv, glob, collections, json, sys
RAW = "/Users/danielgnagi/sandboxzurich/data/raw/stats"
KREISE = ["3", "4", "5", "9"]
def rd(pat):
    return csv.DictReader(open(glob.glob(f"{RAW}/{pat}")[0], encoding="utf-8-sig"))
def grp(a):
    a = int(a)
    if a <= 5: return "0-5"
    if a <= 12: return "6-12"
    if a <= 19: return "13-19"
    if a <= 39: return "20-39"
    if a <= 64: return "40-64"
    return "65+"
out = {}
# --- population by Kreis and age, 2025 (and city)
YEAR = "2025"
age = collections.defaultdict(lambda: collections.defaultdict(int))
pop = collections.defaultdict(int); forn = collections.defaultdict(int)
for r in rd("*od3903*.csv"):
    if r["StichtagDatJahr"] != YEAR: continue
    n = int(r["AnzBestWir"]); k = r["KreisCd"]
    for kk in (k, "Stadt"):
        age[kk][grp(r["AlterVCd"])] += n
        pop[kk] += n
        if r["HerkunftCd"] == "2": forn[kk] += n
out["year"] = YEAR
out["population_2025"] = dict(pop)
out["age_shares"] = {kk: {g: round(v / pop[kk], 3) for g, v in age[kk].items()} for kk in ["Stadt"] + KREISE}
out["child_0_12_share"] = {kk: round(sum(age[kk][g] for g in ["0-5", "6-12"]) / pop[kk], 3) for kk in ["Stadt"] + KREISE}
out["foreigner_share"] = {kk: round(forn[kk] / pop[kk], 3) for kk in ["Stadt"] + KREISE}
# --- Kreis population time series (Stichtag, one row per Kreis/year)
kp = {}
for r in rd("*od3242*.csv"):
    if r["StichtagDatJahr"] in ("2015", "2020", "2024", "2025"):
        kp.setdefault(r["KreisCd"] if "KreisCd" in r else r["KreisLang"], {})[r["StichtagDatJahr"]] = int(r["AnzBestWir"])
out["kreis_pop_series"] = {k: v for k, v in kp.items() if k.split()[-1] in KREISE}
# --- Dogs: snapshot per Stichtag; take latest Stichtag date of 2025 per Kreis
snap = collections.defaultdict(lambda: collections.defaultdict(int))
dates = collections.defaultdict(set)
for r in rd("*hundebestand*.csv"):
    if r["StichtagDatJahr"] not in ("2024", "2025"): continue
    dates[r["StichtagDatJahr"]].add(r["StichtagDat"])
    snap[(r["StichtagDatJahr"], r["StichtagDat"])][r["KreisCd"]] += int(r["AnzHunde"])
out["dog_snapshot_dates"] = {y: sorted(d)[-3:] for y, d in dates.items()}
last = max(k for k in snap if k[0] == "2025")
dogs = snap[last]
out["dogs_latest"] = {"date": last[1], "city": sum(dogs.values()), "by_kreis": {k: dogs[k] for k in KREISE}}
out["dogs_per_100_pop"] = {k: round(100 * dogs[k] / pop[k], 2) for k in KREISE}
out["dogs_per_100_pop"]["Stadt"] = round(100 * sum(dogs.values()) / pop["Stadt"], 2)
# --- Households 2025 by Kreis
hh_size = collections.defaultdict(lambda: collections.defaultdict(int))
for r in rd("*haushaltsgroesse*"):
    if r["StichTagDatJahr"] != YEAR: continue
    for kk in (r["KreisSort"], "Stadt"):
        hh_size[kk][r["hh_groesseLang"]] += int(r["AnzHH"])
hh_form = collections.defaultdict(lambda: collections.defaultdict(int))
FAM = {"Ehepaar mit Kind(ern)", "Paar mit Kind(ern)", "Eingetragenes Paar mit Kind(ern)", "Ein-Elternhaushalt", "Patchwork-Haushalt"}
for r in rd("*haushaltsform*"):
    if r["StichtagDatJahr"] != YEAR: continue
    for kk in (r["KreisSort"], "Stadt"):
        hh_form[kk][r["HHtypLang"]] += int(r["AnzHH"])
out["households_2025"] = {}
for kk in ["Stadt"] + KREISE:
    tot = sum(hh_form[kk].values())
    size_tot = sum(hh_size[kk].values())
    out["households_2025"][kk] = {
        "total_hh": tot,
        "single_share": round(hh_form[kk]["Einpersonenhaushalt"] / tot, 3),
        "family_with_kids_share": round(sum(hh_form[kk][t] for t in FAM) / tot, 3),
        "size_share": {s: round(v / size_tot, 3) for s, v in hh_size[kk].items()},
    }
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
