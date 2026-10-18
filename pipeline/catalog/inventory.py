"""Object-catalog inventory (Nacht 0, Auftrag K1).

Stage 1 (default): collect objects (Brunnen, Haltestellen-Ausstattung, grosse Moebel) inside
Kreis 3/4/5/9, attach local geotagged photos within RADIUS_M, write research/catalog/objects.json.
Stage 2 (--sheets): write contact sheets preview/ref_cat_<art>_<n>.jpg, one per hypothesis group.

Only uses local data (data/raw, research/*.json). No downloads.
Usage: .venv/bin/python pipeline/catalog/inventory.py [--sheets]
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
CAT = ROOT / "research" / "catalog"
PREVIEW = ROOT / "preview"
RADIUS_M = 25.0
KREISE = {"Kreis 3", "Kreis 4", "Industriequartier", "Kreis 9"}
_t = Transformer.from_crs(4326, 2056, always_xy=True)


def to_local(lon, lat):
    e, n = _t.transform(lon, lat)
    return e - 2681400.0, n - 1248700.0


def load_area():
    """Union of the Kreis 3/4/5/9 polygons (lat/lon lists) as a shapely geometry in local metres."""
    kreise = json.load(open(CAT.parent / "kreise_poly_simplified.json"))
    polys = []
    for name in KREISE:
        ring = [to_local(lon, lat) for lat, lon in kreise[name]]
        polys.append(shape({"type": "Polygon", "coordinates": [ring]}).buffer(0))
    return unary_union(polys)


def feats(path):
    return json.load(open(path))["features"]


def centroid_local(geom):
    """Centroid of a lon/lat geometry, returned in local metres."""
    p = shape(geom).centroid
    return to_local(p.x, p.y)


def collect_brunnen(area):
    out = []
    for f in feats(RAW / "stadtzh" / "geo_brunnen__wvz_brunnen.geojson"):
        p = f["properties"]
        if str(p.get("stadtkreis")) not in ("3", "4", "5", "9"):
            continue
        x, y = p["hkoord"] - 2681400.0, p["vkoord"] - 1248700.0
        out.append({"id": f"BR-{p['objectid']}", "kind": "brunnen", "x": x, "y": y,
                    "attrs": {k: p.get(k) for k in (
                        "art", "brunnenart", "material_trog", "material_saeule", "material_figur",
                        "architekt_bildhauer", "wasserart", "historisches_baujahr", "baujahr",
                        "ortsbezeichnung", "standort", "quartier", "stadtkreis", "abgestellt")},
                    "foto_url": p.get("foto")})
    return out


STOP_LAYERS = {
    "wartehalle": "WH", "ticketautomat": "TA", "dfi_anzeiger": "DFI", "sitzgelegenheit": "SB",
    "plakatstelle": "PL", "haltebalken": "HB", "infosystem": "IS",
}


def collect_stops(area):
    out = []
    for layer, prefix in STOP_LAYERS.items():
        path = next((RAW / "stadtzh_all").glob(f"*haltestellen_{layer}.geojson"))
        for f in feats(path):
            x, y = centroid_local(f["geometry"]) if f["geometry"]["type"] not in ("Point", "MultiPoint") \
                else _pt(f["geometry"])
            if not area.contains(Point(x, y)):
                continue
            p = f["properties"]
            attrs = {k: p.get(k) for k in ("typ", "typtext", "bezeichnung", "orientierung", "einbaudatum",
                                           "plakatstellenrvbz", "lagequalitaet") if k in p}
            out.append({"id": f"{prefix}-{p['objectid']}", "kind": "haltestellen", "layer": layer,
                        "x": x, "y": y, "attrs": attrs, "foto_url": None})
    return out


def _pt(g):
    c = g["coordinates"][0] if g["type"] == "MultiPoint" else g["coordinates"]
    return to_local(c[0], c[1])


def collect_moebel(area):
    out = []
    for e in json.load(open(RAW / "osm" / "part_pois_r.json"))["elements"]:
        t = e.get("tags", {})
        if t.get("shop") != "kiosk" or "lat" not in e:
            continue
        x, y = to_local(e["lon"], e["lat"])
        if area.contains(Point(x, y)):
            out.append({"id": f"KI-{e['id']}", "kind": "moebel", "layer": "kiosk", "x": x, "y": y,
                        "attrs": {k: t.get(k) for k in ("name", "brand", "branch", "opening_hours")},
                        "foto_url": None})
    for f in feats(RAW / "stadtzh_extra" / "sammelstellen.geojson"):
        x, y = _pt(f["geometry"])
        if area.contains(Point(x, y)):
            p = f["properties"]
            out.append({"id": f"SA-{p.get('objectid', len(out))}", "kind": "moebel", "layer": "sammelstelle",
                        "x": x, "y": y, "attrs": {k: str(v)[:60] for k, v in p.items()
                                                  if k not in ("geometrie_gdo",)}, "foto_url": None})
    # Kandelaber/Leuchten: ewz Brennstellen (42k). Only kept when a photo is near (see match step).
    for f in feats(next((RAW / "stadtzh").glob("geo_oeffentliche_beleuchtung*ewz_brennstelle*"))):
        x, y = _pt(f["geometry"])
        if area.contains(Point(x, y)):
            p = f["properties"]
            out.append({"id": f"LA-{p.get('objectid')}", "kind": "moebel", "layer": "leuchte",
                        "x": x, "y": y, "attrs": {"orientierung": p.get("orientierung"),
                                                  "art_txt": p.get("art_txt")}, "foto_url": None})
    return out


def load_photos():
    """Geotagged local photos from research/catalog/photo_index.json (built by photo_index.py)."""
    idx = json.load(open(CAT / "photo_index.json"))
    for e in idx:
        e["x"], e["y"] = to_local(e["lon"], e["lat"])
    return idx


def match(objects, photos):
    """Spatial bucket (50 m) lookup; attach photos within RADIUS_M to each object."""
    grid = defaultdict(list)
    for ph in photos:
        grid[(int(ph["x"] // 50), int(ph["y"] // 50))].append(ph)
    for o in objects:
        gx, gy = int(o["x"] // 50), int(o["y"] // 50)
        hits = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for ph in grid.get((gx + dx, gy + dy), ()):
                    d = math.hypot(ph["x"] - o["x"], ph["y"] - o["y"])
                    if d <= RADIUS_M:
                        hits.append({"file": ph["file"], "dist_m": round(d, 1), "source": ph.get("source"),
                                     "license": ph.get("license"), "author": ph.get("author"),
                                     "url": ph.get("url"), "origin": ph.get("origin")})
        hits.sort(key=lambda h: h["dist_m"])
        o["photos"] = hits
    return objects


def main_inventory():
    area = load_area()
    photos = load_photos()
    objs = collect_brunnen(area) + collect_stops(area) + collect_moebel(area)
    objs = match(objs, photos)
    for o in objs:
        for k in ("x", "y"):
            o[k] = round(o[k], 2)
    with open(CAT / "objects.json", "w", encoding="utf-8") as fh:
        json.dump(objs, fh, ensure_ascii=False)
    summ = Counter()
    withph = Counter()
    for o in objs:
        key = o["kind"] if o["kind"] != "haltestellen" else o["layer"]
        summ[key] += 1
        if o["photos"]:
            withph[key] += 1
    print("objects / with photo<=25m:")
    for k in summ:
        print(f"  {k}: {summ[k]} / {withph[k]}")


if __name__ == "__main__":
    if "--sheets" in sys.argv:
        from sheets import make_sheets
        make_sheets()
    else:
        main_inventory()
