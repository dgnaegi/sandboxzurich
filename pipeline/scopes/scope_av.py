"""Scope B: the official cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS) for one ramp site.

Layers (same service as pipeline/groundcover.py, EPSG:2056):
  ms:ogd-0402_arv_basis_avzh_einzelobjekte_f   single objects, polygons: Brücke/Passerelle, Pfeiler, Mauer, wichtige Treppe,
                                                Tunnel/Unterführung/Galerie, Unterstand, unterirdisches Gebäude, ...
  ms:ogd-0402_arv_basis_avzh_einzelobjekte_l   single objects, lines (walls, bridge edges, rails)
  ms:ogd-0401_arv_basis_avzh_bodenbedeckung_f  ground cover: Strasse/Weg, Trottoir, Verkehrsinsel, befestigte Fläche, Gebäude, ...
Fetched once per site into data/raw/av/<site>.json (raw GeoJSON in LV95 plus a meta block); `load(site)` returns the geometries
in game metres grouped by class. 2D only: heights stay with Scope A.
Usage:  python3 pipeline/scopes/scope_av.py <site>[,<site>] [--force]      (prints the per-class counts)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
from ramp_sites import site as site_cfg  # noqa: E402

WFS = "https://maps.zh.ch/wfs/OGDZHWFS"
LAYERS = {
    "objects": "ms:ogd-0402_arv_basis_avzh_einzelobjekte_f",
    "object_lines": "ms:ogd-0402_arv_basis_avzh_einzelobjekte_l",
    "cover": "ms:ogd-0401_arv_basis_avzh_bodenbedeckung_f",
}
OX, OY = 2681400.0, 1248700.0
CACHE = os.path.join(ROOT, "data", "raw", "av")
UA = {"User-Agent": "sandboxzurich/0.1 (research)"}

# AV class (property `art`, lower-cased substring) -> our group
OBJECT_GROUPS = [("brücke", "deck"), ("pfeiler", "pier"), ("mauer", "wall"), ("treppe", "stairs"),
                 ("unterführung", "underpass"), ("tunnel", "underpass"), ("unterstand", "shelter"),
                 ("gebäude", "ugbuilding"), ("bahngeleise", "rail_line")]
# ground cover is grouped by the detailed class `artzh` (falls back to `art`): "Veloweg, Fussweg" and "Parkplatz" are
# "Strasse, Weg" / "befestigte Fläche" in the coarse class
COVER_GROUPS = [("veloweg", "path"), ("parkplatz", "parking"), ("strasse", "carriageway"), ("trottoir", "footway"),
                ("verkehrsinsel befestigt", "island"), ("verkehrsinsel", "green"), ("befestigt", "paved"), ("bahnsteig", "platform"),
                ("gebäude", "building"), ("humusiert", "green"), ("gartenanlage", "green"), ("parkanlage", "green"),
                ("acker", "green"), ("bahngebiet", "rail"), ("gewässer", "water"), ("wasserbecken", "water")]


def _group(art, table, default="other"):
    a = (art or "").lower()
    for key, g in table:
        if key in a:
            return g
    return default


def fetch(name, force=False):
    """Download the three layers for the site's fetch box once; returns the cached dict."""
    cfg = site_cfg(name)
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, f"{name}.json")
    if os.path.exists(f) and not force:
        return json.load(open(f))
    import requests
    x0, y0, x1, y1 = cfg["fetch"]
    bb = [OX + x0, OY + y0, OX + x1, OY + y1]
    out = {"site": name, "bbox_game": list(cfg["fetch"]), "bbox_lv95": bb, "fetched": dt.date.today().isoformat(),
           "source": "Kanton Zürich OGD-WFS (AV), CC0 / open data", "layers": {}}
    for key, typename in LAYERS.items():
        params = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": typename,
                  "BBOX": ",".join(f"{v:.1f}" for v in bb) + ",urn:ogc:def:crs:EPSG::2056", "COUNT": "100000",
                  "OUTPUTFORMAT": "application/json"}
        for attempt in range(3):
            try:
                r = requests.get(WFS, params=params, headers=UA, timeout=300)
                r.raise_for_status()
                j = r.json()
                break
            except Exception as e:  # noqa: BLE001
                print("retry", key, e, file=sys.stderr)
                time.sleep(3)
        else:
            raise SystemExit(f"WFS fetch failed for {typename}")
        out["layers"][key] = {"typename": typename, "features": j.get("features", [])}
    json.dump(out, open(f, "w"), ensure_ascii=False)
    return out


class AV:
    """Site cadastre in game metres. Each group is a list of (geometry, props) with props['group'] set; geometries are
    clipped to the fetch box (polygons that extend beyond, e.g. the Hardbrücke deck, keep only their part inside)."""

    def __init__(self, data):
        import shapely
        from shapely.geometry import shape, box
        self.site = data["site"]
        self.bbox = tuple(data["bbox_game"])
        clip = box(*self.bbox)
        self.groups = {}
        for key, table in (("objects", OBJECT_GROUPS), ("object_lines", OBJECT_GROUPS), ("cover", COVER_GROUPS)):
            for ft in data["layers"][key]["features"]:
                g = shape(ft["geometry"])
                g = shapely.transform(g, lambda c: c - [OX, OY])
                if not g.is_valid:
                    g = g.buffer(0)
                g = g.intersection(clip)
                if g.is_empty:
                    continue
                p = dict(ft["properties"])
                grp = _group((p.get("artzh") if key == "cover" else None) or p.get("art"), table)
                if key == "object_lines":
                    grp = grp + "_line" if not grp.endswith("_line") else grp
                p["group"] = grp
                p["layer"] = key
                self.groups.setdefault(grp, []).append((g, p))

    def geoms(self, group):
        return [g for g, _ in self.groups.get(group, [])]

    def union(self, group):
        import shapely
        G = self.geoms(group)
        return shapely.union_all(G) if G else shapely.Polygon()

    def summary(self):
        return {k: len(v) for k, v in sorted(self.groups.items())}

    def classes(self):
        """Raw AV class names per group (for the report)."""
        out = {}
        for k, v in self.groups.items():
            for _, p in v:
                out.setdefault(k, {}).setdefault(p.get("artzh") or p.get("art"), 0)
                out[k][p.get("artzh") or p.get("art")] += 1
        return out


def load(name, force=False):
    return AV(fetch(name, force))


if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")]
    for n in (names[0].split(",") if names else ["gerold", "duttweiler"]):
        av = load(n, force="--force" in sys.argv)
        print(f"{n}: fetch box {av.bbox}")
        for grp, cls in sorted(av.classes().items()):
            print(f"  {grp:12s} {sum(cls.values()):4d}  " + ", ".join(f"{k} {v}" for k, v in sorted(cls.items(), key=lambda kv: -kv[1])))
