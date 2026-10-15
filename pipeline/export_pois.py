"""Export named POIs (shops, gastro, services, schools …) from OSM per Kreis to research/pois_<kreis>_osm.csv
for web verification. Usage: .venv/bin/python pipeline/export_pois.py"""
import csv
import json

import numpy as np
from shapely.geometry import Point, Polygon

import sources
from config import ROOT

KEYS = ("shop", "amenity", "craft", "office", "tourism", "leisure", "healthcare")
SKIP_AMENITY = {"bench", "waste_basket", "bicycle_parking", "parking", "parking_space", "vending_machine", "recycling",
                "post_box", "telephone", "drinking_water", "fountain", "toilets", "parking_entrance", "motorcycle_parking",
                "charging_station", "atm", "clock", "shelter", "waste_disposal", "bbq", "grit_bin", "hunting_stand", "loading_dock"}


def main():
    K = {}
    for name, ll in json.load(open(ROOT / "research" / "kreise_poly_simplified.json")).items():
        a = np.array(ll)
        x, y = sources.geo.to_local(a[:, 1], a[:, 0])
        K["kreis5" if name == "Industriequartier" else name.lower().replace(" ", "")] = Polygon(np.column_stack([x, y])).buffer(0)
    nodes, els = sources.osm()
    rows = {k: [] for k in K}
    for e in els:
        t = e.get("tags", {})
        if not t.get("name") or not any(k in t for k in KEYS) or t.get("amenity") in SKIP_AMENITY:
            continue
        if e["type"] == "node":
            p = nodes.get(e["id"])
        elif e["type"] == "way":
            pts = [nodes[n] for n in e.get("nodes", []) if n in nodes]
            p = tuple(np.mean(pts, 0)) if pts else None
        else:
            continue
        if p is None:
            continue
        for k, poly in K.items():
            if poly.contains(Point(p)):
                kind = next(f"{k2}={t[k2]}" for k2 in KEYS if k2 in t)
                addr = f"{t.get('addr:street', '')} {t.get('addr:housenumber', '')}".strip()
                rows[k].append([f"{e['type'][0]}{e['id']}", t["name"], kind, addr, round(p[0], 1), round(p[1], 1),
                                t.get("website", t.get("contact:website", ""))])
                break
    for k, r in rows.items():
        with open(ROOT / "research" / f"pois_{k}_osm.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["osm_id", "name", "kind", "address", "x", "y", "website"])
            w.writerows(sorted(r, key=lambda x: (x[3], x[1])))
    print({k: len(v) for k, v in rows.items()})


if __name__ == "__main__":
    main()
