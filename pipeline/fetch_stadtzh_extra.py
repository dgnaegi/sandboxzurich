"""Fetch additional Stadt Zuerich OGD layers (social infrastructure, street furniture) as GeoJSON.

Source: CKAN package_show (data.stadt-zuerich.ch) -> WFS GetCapabilities/GetFeature
on ogd.stadt-zuerich.ch. Output CRS is EPSG:2056 (LV95), declared in the GeoJSON `crs` member,
so the files match the project's local coordinates without transformation.

Output: data/raw/stadtzh_extra/<out>.geojson (skipped if it exists) and
        data/raw/stadtzh_extra/manifest.json (license, source URL, feature count, properties).
Run:    .venv/bin/python pipeline/fetch_stadtzh_extra.py
"""
import datetime
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "stadtzh_extra"
CKAN = "https://data.stadt-zuerich.ch/api/3/action/package_show?id="
DATASET_PAGE = "https://data.stadt-zuerich.ch/dataset/"
H = {"User-Agent": "gtazurich/0.1"}
TIMEOUT = 60

# out name -> CKAN package name (geo_* packages carry a WFS resource)
DATASETS = {
    "kitas": "geo_kindertagesstaette",
    "schulanlagen": "geo_schulanlagen",
    "spielplaetze": "geo_poi_oeffentliche_spielplaetze",
    "gemeinschaftszentren": "geo_gemeinschaftszentrum",
    "quartiertreffs": "geo_quartiertreff",
    "zueri_wc": "geo_zueri_wc",
    "sport": "geo_sport",
    "erholungs_sporteinrichtungen": "geo_erholungs__und_sporteinrichtungen",
    "abfallgefaesse": "geo_abfallgefaesse",
    "hundezonen": "geo_hundezonen",
    "sammelstellen": "geo_sammelstelle",
    "kehrichtcontainer": "geo_erz_kehrichtcontainer_im_oeffentlichen_raum",
    "zweiradparkierung": "geo_zweiradparkierung",
    "sitzbaenke": "geo_sitzbankkataster_ogd",
    "brunnen": "geo_brunnen",
    "kunst_im_stadtraum": "geo_kunst_im_stadtraum",
}
# Not in the catalog (checked 2026-10-14): Bibliotheken (PBZ), Horte, Pingpong/Boccia,
# Plakatstellen, Badeanlagen as own layer. Recorded in research/social_infra.md.


def ckan(package):
    r = requests.get(CKAN + package, headers=H, timeout=TIMEOUT)
    r.raise_for_status()
    body = r.json()
    if not body.get("success"):
        raise RuntimeError(f"CKAN package not found: {package}")
    return body["result"]


def wfs_base(pkg):
    for res in pkg["resources"]:
        if (res.get("format") or "").upper() == "WFS":
            return res["url"].split("?")[0]
    raise RuntimeError("no WFS resource")


def feature_types(base):
    r = requests.get(base, params={"SERVICE": "WFS", "REQUEST": "GetCapabilities", "VERSION": "1.1.0"},
                     headers=H, timeout=TIMEOUT)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    names = []
    for ft in root.iter():
        if ft.tag.endswith("}FeatureType") or ft.tag == "FeatureType":
            for child in ft:
                if child.tag.endswith("Name"):
                    names.append(child.text.strip())
                    break
    return names


def get_features(base, typename):
    r = requests.get(base, params={
        "SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature",
        "TYPENAME": typename, "outputFormat": "application/vnd.geo+json", "SRSNAME": "EPSG:2056",
    }, headers=H, timeout=300)
    r.raise_for_status()
    data = r.json()
    if data.get("type") != "FeatureCollection":
        raise RuntimeError(f"unexpected response for {typename}")
    return data


def merge_layers(base, typenames):
    feats = []
    for t in typenames:
        fc = get_features(base, t)
        for f in fc["features"]:
            f.setdefault("properties", {})
            if f["properties"] is None:
                f["properties"] = {}
            f["properties"]["layer"] = t
        feats.extend(fc["features"])
    return {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::2056"}},
            "features": feats}


def summarize(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    feats = data.get("features", [])
    props = sorted({k for f in feats[:500] for k in (f.get("properties") or {})})
    return len(feats), props


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mpath = OUT / "manifest.json"
    manifest = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
    failed = []
    for out, pkg_name in DATASETS.items():
        target = OUT / f"{out}.geojson"
        try:
            pkg = ckan(pkg_name)
            base = wfs_base(pkg)
            entry = {
                "catalog_name": pkg_name,
                "title": pkg.get("title"),
                "license_id": pkg.get("license_id"),
                "license_title": pkg.get("license_title"),
                "metadata_modified": pkg.get("metadata_modified"),
                "source_url": DATASET_PAGE + pkg_name,
                "wfs": base,
            }
            if target.exists():
                count, props = summarize(target)
                status = "skipped (exists)"
            else:
                types = feature_types(base)
                if not types:
                    raise RuntimeError("no FeatureType in capabilities")
                entry["typenames"] = types
                # Multi-layer packages: take the *_view layers (point POIs), skip *_att (attribute
                # tables) and *_l/*_p (lines/polygons). Each feature gets a "layer" property.
                views = [t for t in types if t.endswith("_view")] or types[:1]
                entry["layers_used"] = views
                data = merge_layers(base, views)
                tmp = target.with_suffix(".geojson.tmp")
                tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                tmp.replace(target)
                count = len(data["features"])
                props = sorted({k for f in data["features"][:500] for k in (f.get("properties") or {})})
                status = "downloaded"
            entry.update({
                "file": f"data/raw/stadtzh_extra/{out}.geojson",
                "features": count,
                "properties": props,
                "fetched": datetime.date.today().isoformat(),
            })
            manifest[out] = entry
            print(f"{out:30} {status:18} {count:6} features  {pkg.get('license_id')}")
        except Exception as e:  # keep going; report at the end
            failed.append(f"{out} ({pkg_name}): {e}")
            print(f"{out:30} FAILED: {e}")
        mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    if failed:
        print("\nFailed:", *failed, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
