"""Stadt Zürich OGD point layers (CC0) clipped to an area, cached as compact JSON.

Trees (Baumkataster), street lights (EWZ), street parking, benches, fountains, waste bins, bike parking.
"""
import json

import numpy as np

import sources
from config import ROOT

RAW = ROOT / "data" / "raw"
CACHE = ROOT / "data" / "build"
LAYERS = {
    "trees": ("stadtzh/geo_baumkataster__baumkataster_baumstandorte.geojson",
              lambda p: [p.get("baumgattunglat") or "", _f(p.get("kronendurchmesser"), 6), p.get("kategorie") or ""]),
    "lights": ("stadtzh/geo_oeffentliche_beleuchtung_der_stadt_zuerich__ewz_brennstelle_p.geojson",
               lambda p: [_f(p.get("orientierung"), 0)]),
    "parking": ("stadtzh/geo_oeffentlich_zugaengliche_strassenparkplaetze_ogd__view_pp_ogd.geojson",
                lambda p: [p.get("art") or ""]),
    # bench model text (Sitzbankkataster) -> type code 0 back-rest, 1 no back-rest, 2 table-bench, 3 "046" modern, 4 table, 5 other
    "benches": ("stadtzh/geo_sitzbankkataster_ogd__bankstandorte_ogd.geojson", lambda p: [_bench_type(p.get("sitzbankmodelle"))]),
    # waste bin type (ERZ Abfallgefaesse) -> 0 Zueri-Kuebel, 1 Abfallhai (concrete), 2 Robidog, 3 other; +1 if ashtray fitted
    "bins": ("stadtzh/geo_abfallgefaesse__abfallgefaess_p.geojson", lambda p: [_bin_type(p)]),
    "fountains": ("stadtzh/geo_brunnen__wvz_brunnen.geojson", lambda p: [p.get("brunnenart") or "", p.get("abgestellt") or ""]),
}


def _bench_type(m):
    m = str(m or "")
    if m.startswith("046"):
        return 3
    if "Tisch-Bank" in m:
        return 2
    if m == "Tisch":
        return 4
    if m.startswith("ohne"):
        return 1
    return 0 if m.startswith("mit") else 5


def _bin_type(p):
    t = {"Zuerikuebel": 0, "Abfallhai": 1, "Robidog": 2}.get(p.get("gefaesstyp_txt"), 3)
    ash = any(p.get(f"auspraegung_{i}_txt") == "Ascher" for i in (2, 3))
    return t * 2 + (1 if ash else 0)


def _f(v, d):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _extra(name):
    """Optional layers from the second fetch (data/raw/stadtzh_extra), matched by file-name keyword."""
    for f in sorted((RAW / "stadtzh_extra").glob("*.geojson")):
        if name in f.name:
            return f
    return None


def load(area, margin=50.0):
    """Return {layer: [[x, y, *attrs], ...]} in local metres for the bbox area (x0, y0, x1, y1)."""
    key = "_".join(str(int(v)) for v in area)
    cache = CACHE / f"citydata_v3_{key}.json"
    if cache.exists():
        return json.load(open(cache))
    x0, y0, x1, y1 = area[0] - margin, area[1] - margin, area[2] + margin, area[3] + margin
    out = {}
    layers = dict(LAYERS)
    for name, kw in (("bikes", "zweirad"), ("playgrounds", "spielpl"), ("schools", "schulanlagen")):
        f = _extra(kw)
        if f and name == "bikes":  # spaces per parking and kind (Velo / Motorrad)
            layers[name] = (str(f.relative_to(RAW)), lambda p: [_f(p.get("anzahl_pp"), 6), str(p.get("art") or "")])
        elif f:
            layers[name] = (str(f.relative_to(RAW)), lambda p: [str(p.get("layer", "")), str(p.get("name") or p.get("bezeichnung") or "")])
    for name, (rel, attrs) in layers.items():
        f = RAW / rel
        if not f.exists():
            print("missing", rel)
            continue
        feats = json.load(open(f))["features"]
        pts = [(ft["geometry"]["coordinates"], ft["properties"]) for ft in feats
               if ft.get("geometry") and ft["geometry"]["type"] == "Point"]
        if not pts:
            continue
        c = np.array([p[0][:2] for p in pts], dtype=np.float64)
        if np.abs(c[:, 0]).max() > 1000:  # already LV95
            x, y = c[:, 0] - sources.geo.ORIGIN_E, c[:, 1] - sources.geo.ORIGIN_N
        else:
            x, y = sources.geo.to_local(c[:, 0], c[:, 1])
        m = (x > x0) & (x < x1) & (y > y0) & (y < y1)
        out[name] = [[round(float(x[i]), 2), round(float(y[i]), 2), *attrs(pts[i][1])] for i in np.nonzero(m)[0]]
    CACHE.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(cache, "w"))
    return out


if __name__ == "__main__":
    from config import AREA
    d = load(AREA)
    print({k: len(v) for k, v in d.items()})
    for k, v in d.items():
        print(k, v[:2])
