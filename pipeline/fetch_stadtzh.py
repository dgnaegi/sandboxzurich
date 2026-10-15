"""Fetch Stadt Zuerich OGD (WFS via CKAN resource URLs) as GeoJSON to data/raw/stadtzh/.
Every feature type of each service -> <package>__<layer>.geojson. Skips existing.
Writes data/raw/stadtzh/_licenses.json (license per package)."""
import json
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import area  # noqa: E402

OUT = area.ROOT / "data" / "raw" / "stadtzh"
H = {"User-Agent": "gtazurich/0.1"}
CKAN = "https://data.stadt-zuerich.ch/api/3/action/package_show"
PACKAGES = [
    "geo_baumkataster", "geo_brunnen", "geo_velonetzplanung", "geo_fuss__und_velowegnetz",
    "geo_verkehrszonen", "geo_stadtkreise", "geo_oeffentliche_beleuchtung_der_stadt_zuerich",
    "geo_sitzbankkataster_ogd", "geo_abfallgefaesse", "geo_zueri_wc",
    "geo_oeffentlich_zugaengliche_strassenparkplaetze_ogd",
    "geo_oeffentlich_zugaengliche_parkplaetze_dav",
]


SKIP = {"baumkataster_kronendurchmesser", "baumstandorte_k"}  # 430/505 MB, redundant with baumstandorte


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lic = {}
    for pkg in PACKAGES:
        try:
            p = requests.get(CKAN, params={"id": pkg}, headers=H, timeout=60).json()["result"]
            lic[pkg] = p.get("license_id")
            wfs = next(r["url"] for r in p["resources"] if r["format"].upper() == "WFS")
            base = wfs.split("?")[0]
            cap = requests.get(base, params={"SERVICE": "WFS", "REQUEST": "GetCapabilities", "VERSION": "1.1.0"},
                               headers=H, timeout=60).text
            layers = re.findall(r"<FeatureType[^>]*>\s*<Name>([^<]+)</Name>", cap)
            print(pkg, lic[pkg], layers, flush=True)
            for lyr in layers:
                if lyr in SKIP:
                    continue
                dest = OUT / f"{pkg}__{lyr}.geojson"
                if dest.exists():
                    continue
                r = requests.get(base, params={
                    "SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature", "TYPENAME": lyr,
                    "outputFormat": "GeoJSON", "srsName": "EPSG:4326"}, headers=H, timeout=600)
                if r.status_code != 200 or not r.text.lstrip().startswith("{"):
                    print("  FAIL", lyr, r.status_code, r.text[:150].replace("\n", " "), flush=True)
                    continue
                dest.write_text(r.text)
                print("  got", dest.name, len(r.content), flush=True)
        except Exception as e:
            print("ERROR", pkg, repr(e), flush=True)
    (OUT / "_licenses.json").write_text(json.dumps(lic, indent=1))


if __name__ == "__main__":
    main()
