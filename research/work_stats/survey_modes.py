"""Weighted use frequency of Velo/OEV/Auto by Kreis from Bevoelkerungsbefragung 2019+ (OGD od4732)."""
import csv, glob, collections, json
F = glob.glob("/Users/danielgnagi/gtazurich/data/raw/stats/*BEV473OD4732.csv")[0]
VARS = {"velo": "A5002aa01", "oev": "A5004aa01", "auto": "A5006aa01"}
rd = csv.DictReader(open(F, encoding="utf-8-sig"))
years = collections.Counter(); res = collections.defaultdict(lambda: collections.defaultdict(float))
tot = collections.defaultdict(float); n = collections.Counter()
rows = []
for r in rd:
    rows.append((r["Jahr"], r["A1BVSKreis01"], r["pgewicht"], {m: r[v] for m, v in VARS.items()}))
years = collections.Counter(y for y, *_ in rows)
Y = "2023-2025 gepoolt"
YEARS = {"2023", "2024", "2025"}
for y, k, w, vals in rows:
    if y not in YEARS: continue
    try: w = float(w.replace(",", "."))
    except: continue
    kreis = k.replace("Kreis ", "")
    for kk in (kreis, "Stadt"):
        n[kk] += 1; tot[kk] += w
        for m, lab in vals.items():
            if lab in ("Täglich", "2-5 Mal pro Woche"): res[kk][m + "_taeglich_bis_2_5pw"] += w
            if lab == "Nie": res[kk][m + "_nie"] += w
out = {"year": Y, "n_respondents": {k: n[k] for k in ["Stadt", "3", "4", "5", "9"]}, "shares": {}}
for kk in ["Stadt", "3", "4", "5", "9"]:
    out["shares"][kk] = {key: round(v / tot[kk], 3) for key, v in res[kk].items()}
print(json.dumps(out, ensure_ascii=False, indent=1))
