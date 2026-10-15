"""Official list of licensed restaurants/bars (Stadt Zürich OGD «Gastwirtschaftsbetriebe», CC0): match with OSM POIs,
add venues missing in OSM. Writes research/gastro_match.csv. Used by build_testarea via add_missing(S)."""
import csv
import difflib

from shapely.geometry import Point

import sources
from config import ROOT

SRC = ROOT / "data" / "raw" / "stadtzh_more" / "gastwirtschaft.csv"
KIND = {"Cabaret / Nachtclub": "nightclub", "Dancing / Disco": "nightclub", "Kleinwirtschaft": "cafe",
        "Nebenwirtschaft": "fast_food", "Gastwirtschaft": "restaurant"}
SKIP = {"Ausgabestelle", "Kantine / Mensa", "Tankstelle"}


def load(area_box):
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    year = max(int(r["StichtagDatJahr"]) for r in rows)
    out = []
    for r in rows:
        if int(r["StichtagDatJahr"]) != year or r["BetriebsstatusLang"] != "Offen" or r["BetriebsartLang"] in SKIP:
            continue
        try:
            x, y = float(r["EKoord"]) - sources.geo.ORIGIN_E, float(r["NKoord"]) - sources.geo.ORIGIN_N
        except ValueError:
            continue
        if area_box.contains(Point(x, y)):
            out.append({"name": r["Betriebsname"].strip(), "x": x, "y": y, "addr": f"{r['StrasseLang']} {r['HNr']}",
                        "hours": r["Oeffnungszeit"], "type": r["BetriebsartLang"]})
    return out, year


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def add_missing(S, area_box):
    """Match official venues to OSM POIs (≤35 m and similar name); add the unmatched ones as POIs."""
    venues, year = load(area_box)
    rows, added = [], 0
    for v in venues:
        best, score = None, 0.0
        for p in S["pois"]:
            d = Point(p["x"], p["y"]).distance(Point(v["x"], v["y"]))
            if d > 35:
                continue
            a, b = norm(p["name"]), norm(v["name"])
            for w in ("restaurant", "bar", "cafe", "café", "pizzeria", "takeaway", "gmbh", "ag"):
                a, b = a.replace(w, ""), b.replace(w, "")
            sc = 1.0 if a and b and (a in b or b in a) else difflib.SequenceMatcher(None, a, b).ratio()
            if sc > score:
                best, score = p, sc
        if best is not None and score >= 0.6:
            best["official"] = True
            rows.append([v["name"], v["addr"], v["type"], v["hours"], "matched", best["name"], round(score, 2)])
        else:
            kind = KIND.get(v["type"], "restaurant")
            S["pois"].append({"x": v["x"], "y": v["y"], "name": v["name"], "kind": kind, "osm": f"gwb:{v['name']}", "official": True})
            rows.append([v["name"], v["addr"], v["type"], v["hours"], "added", "", round(score, 2)])
            added += 1
    with open(ROOT / "research" / "gastro_match.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "address", "type", "hours", "result", "osm_name", "score"])
        w.writerows(rows)
    print(f"gastro {year}: {len(venues)} official venues, {len(venues) - added} matched to OSM, {added} added")
