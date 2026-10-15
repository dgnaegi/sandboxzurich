"""Fetch more Stadt Zürich OGD layers via WFS (CC0): hydrants, street-name dedication plates, street-name register.
Usage: .venv/bin/python pipeline/fetch_stadtzh_more.py"""
import re

import requests

from config import ROOT

OUT = ROOT / "data" / "raw" / "stadtzh_more"
H = {"User-Agent": "sandboxzurich/0.1 (research)"}
CKAN = "https://data.stadt-zuerich.ch/api/3/action/package_show"
PACKAGES = ["geo_hydranten", "geo_widmungstafel", "geo_strassennamenverzeichnis"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for pkg in PACKAGES:
        p = requests.get(CKAN, params={"id": pkg}, headers=H, timeout=60).json()["result"]
        wfs = next(r["url"] for r in p["resources"] if r["format"].upper() == "WFS").split("?")[0]
        cap = requests.get(wfs, params={"SERVICE": "WFS", "REQUEST": "GetCapabilities", "VERSION": "1.1.0"}, headers=H, timeout=60).text
        for lyr in re.findall(r"<FeatureType[^>]*>\s*<Name>([^<]+)</Name>", cap):
            dest = OUT / f"{pkg}__{lyr}.geojson"
            if dest.exists():
                continue
            r = requests.get(wfs, params={"SERVICE": "WFS", "VERSION": "1.1.0", "REQUEST": "GetFeature", "TYPENAME": lyr,
                                          "outputFormat": "GeoJSON", "srsName": "EPSG:4326"}, headers=H, timeout=600)
            if r.status_code == 200 and r.text.lstrip().startswith("{"):
                dest.write_text(r.text)
                print("got", dest.name, len(r.content) // 1024, "KB")
            else:
                print("FAIL", lyr, r.status_code)


if __name__ == "__main__":
    main()
