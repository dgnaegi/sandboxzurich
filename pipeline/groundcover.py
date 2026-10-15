"""Official ground cover (Kanton ZH AV Bodenbedeckung, CC0-ish OGD) as shapely unions in local metres.

load(area) -> dict(carriageway, sidewalk, plaza, green, gravel, water, rail, building, cobble_road, curbs)
Data: Kanton ZH OGD-WFS ogd-0401 avzh_bodenbedeckung_f (AV93, LV95), fetched once into data/raw/groundcover/.
Extras: vas_e_strassenbelag (+ vas_basis axes) -> cobble_road, view_randabschluss_konzept -> curbs.
Class mapping: see MAPPING below / research/groundcover.md.
"""
import json
import pickle
import sys
import time
from pathlib import Path

import requests
import shapely
from shapely.geometry import box
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "groundcover"
STADT = ROOT / "data" / "raw" / "stadtzh_all"
CACHE = ROOT / "data" / "build"
OX, OY = 2681400.0, 1248700.0
WFS = "https://maps.zh.ch/wfs/OGDZHWFS"
LAYER = "ms:ogd-0401_arv_basis_avzh_bodenbedeckung_f"
STEP = 1000.0

# artzh (detailed AV class) -> our class. 'art' (coarse) is the fallback.
MAPPING = {
    "Strasse, Weg": "carriageway", "Parkplatz": "carriageway",
    "Trottoir": "sidewalk", "Verkehrsinsel befestigt": "sidewalk",
    "Veloweg, Fussweg": "plaza", "Sportanlage befestigt": "plaza",
    "Hausumschwung befestigt": "gravel",
    "Verkehrsinsel humusiert": "green", "Hausumschwung humusiert": "green", "Parkanlage": "green",
    "Acker, Wiese, Weide": "green", "Gartenanlage": "green", "Sportanlage humusiert": "green",
    "Wasserbecken": "water", "Fliessgewässer": "water", "Stehendes Gewässer": "water",
    "Bahngebiet": "rail",
}
ART_FALLBACK = {  # coarse 'art' when artzh unknown
    "Gebäude": "building", "befestigte Fläche": "gravel", "humusierte Fläche": "green",
    "Gartenanlage": "green", "Strasse, Weg": "carriageway", "Trottoir": "sidewalk",
    "Verkehrsinsel": "sidewalk", "Wasserbecken": "water", "fliessendes Gewässer": "water",
    "stehendes Gewässer": "water", "Bahngebiet": "rail", "Acker, Wiese, Weide": "green",
}
CLASSES = ["carriageway", "sidewalk", "plaza", "green", "gravel", "water", "rail", "building"]


def _classify(p):
    z = p.get("artzh") or ""
    if z in MAPPING:
        return MAPPING[z]
    if z.startswith("Gebäude") or z == "Nebengebäude":
        return "building"
    if "Gewässer" in z:
        return "water"
    return ART_FALLBACK.get(p.get("art"), "gravel")


def fetch(area):
    """Download AV tiles covering area (x0,y0,x1,y1 local m) once; returns list of files."""
    RAW.mkdir(parents=True, exist_ok=True)
    x0, y0, x1, y1 = area
    files = []
    gx0, gx1 = int((x0 - 20) // STEP), int((x1 + 20) // STEP)
    gy0, gy1 = int((y0 - 20) // STEP), int((y1 + 20) // STEP)
    for gx in range(gx0, gx1 + 1):
        for gy in range(gy0, gy1 + 1):
            f = RAW / f"bb_{gx}_{gy}.geojson"
            files.append(f)
            if f.exists() and f.stat().st_size > 0:
                continue
            b = [OX + gx * STEP - 20, OY + gy * STEP - 20, OX + (gx + 1) * STEP + 20, OY + (gy + 1) * STEP + 20]
            for attempt in range(3):
                try:
                    r = requests.get(WFS, params={
                        "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": LAYER,
                        "BBOX": ",".join(map(str, b)) + ",urn:ogc:def:crs:EPSG::2056", "COUNT": "100000",
                        "OUTPUTFORMAT": "application/json"}, headers={"User-Agent": "sandboxzurich/0.1 (research)"}, timeout=300)
                    r.raise_for_status()
                    f.write_bytes(r.content)
                    break
                except Exception as e:
                    print("retry", f.name, e, file=sys.stderr)
                    time.sleep(3)
            else:
                files.pop()
    return files


def _local(geom):
    return shapely.transform(geom, lambda c: c - [OX, OY])


def _cobble(roadmask):
    """Cobble carriageway: vas_basis axes whose (name, measure range) overlaps a 'Pflästerung' belag row."""
    belag = json.load(open(STADT / "geo_verkehrsachsensystem_stadt_zuerich__vas_e_strassenbelag.geojson"))["features"]
    basis = json.load(open(STADT / "geo_verkehrsachsensystem_stadt_zuerich__vas_basis.geojson"))["features"]
    rows = {}
    for f in belag:
        p = f["properties"]
        if (p.get("belagsart") or "").startswith("Pfl") or p.get("belagsart") == "Chaussierung":
            rows.setdefault(p["lokalisationsname"], []).append((float(p["messwert_von"]), float(p["messwert_bis"])))
    lines = []
    for f in basis:
        p = f["properties"]
        iv = rows.get(p["lokalisationsname"])
        if iv and f["geometry"]:
            a, b = float(p["messwert_von"]), float(p["messwert_bis"])
            if any(a < hi and b > lo for lo, hi in iv):
                lines.append(shapely.geometry.shape(f["geometry"]))
    if not lines:
        return shapely.Polygon()
    from pyproj import Transformer
    t = Transformer.from_crs(4326, 2056, always_xy=True)
    ax = shapely.union_all([shapely.transform(g, lambda c: __import__("numpy").column_stack(t.transform(c[:, 0], c[:, 1])) - [OX, OY]) for g in lines])
    return roadmask.intersection(ax.buffer(5, cap_style="flat"))


def _curbs(area):
    from pyproj import Transformer
    import numpy as np
    t = Transformer.from_crs(4326, 2056, always_xy=True)
    feats = json.load(open(STADT / "geo_randabschluesse_konzeptplan__view_randabschluss_konzept.geojson"))["features"]
    out = []
    ab = box(*area).buffer(30)
    for f in feats:
        g = shapely.geometry.shape(f["geometry"])
        g = shapely.transform(g, lambda c: np.column_stack(t.transform(c[:, 0], c[:, 1])) - [OX, OY])
        if g.intersects(ab):
            out.append({"geom": g, "code": int(float(f["properties"]["abschluss"]))})
    return out


def load(area, force=False):
    area = tuple(round(float(v)) for v in area)
    cache = CACHE / ("groundcover_%d_%d_%d_%d.pkl" % area)
    if cache.exists() and not force:
        return pickle.load(open(cache, "rb"))
    files = fetch(area)
    ab = box(*area).buffer(20)
    parts = {c: [] for c in CLASSES}
    seen = set()
    for f in files:
        for ft in json.load(open(f))["features"]:
            p = ft["properties"]
            if p["objid"] in seen or not ft["geometry"]:
                continue
            seen.add(p["objid"])
            g = shapely.geometry.shape(ft["geometry"])
            g = _local(g)
            if g.intersects(ab):
                parts[_classify(p)].append(g.buffer(0))
    out = {c: (shapely.union_all(v).intersection(ab) if v else shapely.Polygon()) for c, v in parts.items()}
    out["cobble_road"] = _cobble(out["carriageway"])
    out["curbs"] = _curbs(area)
    CACHE.mkdir(parents=True, exist_ok=True)
    pickle.dump(out, open(cache, "wb"))
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "pipeline"))
    from config import AREA
    t0 = time.time()
    G = load(AREA, force="--force" in sys.argv)
    print("area", AREA, "%.1fs" % (time.time() - t0))
    for c in CLASSES + ["cobble_road"]:
        print("%-12s %10.0f m2" % (c, G[c].area))
    print("curbs", len(G["curbs"]))
