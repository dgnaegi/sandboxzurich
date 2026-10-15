"""Add Wikimedia Commons text-search photos to sites that have little Commons coverage (geosearch only
finds files with coordinates). Appends to research/v3/photos.json and data/raw/photos/v3/<id>/.
Usage: python fetch_v3_extra.py [id,id]   (default: all sites in QUERIES)
"""
import html
import re
import sys

import fetch_v3 as F
import json

QUERIES = {
    "kalkbreite": "Kalkbreite Zürich Genossenschaft", "lochergut": "Lochergut Zürich",
    "prime_tower": "Prime Tower Zürich", "toni_areal": "Toni-Areal Zürich",
    "letzigrund": "Stadion Letzigrund Zürich", "bhf_hardbruecke": "Bahnhof Zürich Hardbrücke",
    "bhf_altstetten": "Bahnhof Zürich Altstetten", "bhf_wiedikon": "Bahnhof Zürich Wiedikon",
    "volkshaus": "Volkshaus Zürich", "st_jakob": "Kirche St. Jakob Zürich Stauffacher",
    "bullingerkirche": "Bullingerkirche Zürich", "kanzlei_schulhaus": "Schulhaus Kanzlei Zürich",
    "hardau_ii": "Hardau Hochhäuser Zürich", "kirchen_altstetten": "Kirche Altstetten Zürich",
    "dreifaltigkeit_wiedikon": "Dreifaltigkeitskirche Zürich Wiedikon",
    "krematorium_sihlfeld": "Friedhof Sihlfeld Krematorium Zürich",
    "krematorium_haupttor": "Friedhof Sihlfeld Eingang Zürich", "viadukt": "Im Viadukt Zürich Markthalle",
    "schiffbau": "Schiffbau Zürich", "kva_kamin": "Josefstrasse Zürich Kehrichtverbrennung",
    "loewenbrunnen": "Löwenbrunnen Zürich Wiedikon", "helvetiaplatz": "Helvetiaplatz Zürich",
    "langstrasse": "Langstrasse Zürich", "baeckeranlage": "Bäckeranlage Zürich",
    "kasernenareal": "Kasernenareal Zürich", "josefwiese": "Josefwiese Zürich",
    "roentgenplatz": "Röntgenplatz Zürich", "idaplatz": "Idaplatz Zürich",
    "albisriederplatz": "Albisriederplatz Zürich", "lindenplatz": "Lindenplatz Altstetten Zürich",
    "limmatplatz": "Limmatplatz Zürich", "escher_wyss_platz": "Escher-Wyss-Platz Zürich",
    "turbinenplatz": "Turbinenplatz Zürich", "stauffacher": "Stauffacher Zürich",
    "bullingerplatz": "Bullingerplatz Zürich", "hardplatz": "Hardplatz Zürich",
    "rosa_luxemburg_platz": "Rosa-Luxemburg-Platz Zürich",
}
MAXN = 10


def main():
    ids = sys.argv[1].split(",") if len(sys.argv) > 1 else list(QUERIES)
    meta = json.load(open(F.META))
    for sid in ids:
        site = meta[sid]
        have = {p.get("title") for p in site["photos"] if p["source"] == "commons"}
        r = F.get("commons", F.COMMONS, {"action": "query", "generator": "search", "gsrnamespace": 6,
                                         "gsrsearch": QUERIES[sid] + " filetype:bitmap", "gsrlimit": 40,
                                         "prop": "imageinfo", "iiprop": "url|extmetadata|size",
                                         "iiurlwidth": F.MAX_SIDE, "format": "json"}, pause=3.0)
        if not r:
            continue
        cands = []
        for p in r.json().get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            md = ii.get("extmetadata", {})
            lic = md.get("LicenseShortName", {}).get("value", "")
            t = p["title"]
            if t in have or not ii.get("thumburl") or not t.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            if not re.search(r"CC|Public domain|PD", lic, re.I) or ii.get("width", 0) < 1000:
                continue
            author = html.unescape(re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "unknown"))).strip()
            date = re.sub(r"<[^>]+>", "", md.get("DateTimeOriginal", {}).get("value", ""))
            cands.append(dict(title=t, url=ii["thumburl"], page=ii.get("descriptionurl"), license=lic,
                              author=author, year=int(date[:4]) if date[:4].isdigit() else 0))
        cands.sort(key=lambda c: -c["year"])
        n = 0
        for c in cands[:MAXN]:
            f = F.OUT_DIR / sid / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", c["title"][5:])[:60] + ".jpg")
            if F.download(c["url"], f, "commons"):
                site["photos"].append(dict(file=str(f.relative_to(F.ROOT)), source="commons", license=c["license"],
                                           author=c["author"], url=c["page"], title=c["title"], lat=None, lon=None,
                                           heading=None, year=c["year"], night=False, dist_m=None, via="search"))
                n += 1
        F.META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        F.log(f"{sid}: +{n} commons (search)")


if __name__ == "__main__":
    main()
