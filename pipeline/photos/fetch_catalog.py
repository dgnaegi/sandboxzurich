"""Targeted reference photos for uncertain catalog variants (fountain V3/V7/V8/V9, VBZ stop flag, kiosk).
Wikimedia Commons (geosearch + text search, licence/author recorded) and Panoramax (CC-BY-SA, nearest). Images <= 800 px
to data/raw/photos/catalog/<tag>/, metadata to research/catalog/photos_extra.json. Resumable, existing files skipped.
Usage: python fetch_catalog.py [--only tag,tag]"""
import argparse, io, json, re, time
from pathlib import Path
import requests
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "raw" / "photos" / "catalog"
META = ROOT / "research" / "catalog" / "photos_extra.json"
UA = "sandboxzurich/0.1 (research)"
H = {"User-Agent": UA, "Api-User-Agent": UA}
COMMONS = "https://commons.wikimedia.org/w/api.php"
PANO = "https://api.panoramax.xyz/api/search"
# tag -> (geo points [(lat, lon)], text queries)
T = {
    "V3_bronze": ([(47.38262, 8.53682), (47.38195, 8.50889), (47.3745, 8.5395)], ["Brunnen Zürich Bronze", "Bronzebrunnen Zürich Kreis 4", "Brunnen Zürich Sihlquai", "Schalenbrunnen Zürich"]),
    "V7_wand": ([(47.3835, 8.5300), (47.3768, 8.5290)], ["Wandbrunnen Zürich Schulhaus", "Wandbrunnen Zürich Kreis 4", "Wandbrunnen Schulhaus Zürich Muschel"]),
    "V8_notwasser": ([(47.38059, 8.52541), (47.37716, 8.51656), (47.38213, 8.5154), (47.37374, 8.53045)], ["Notwasserbrunnen Zürich", "Brunnen Zürich Gusseisen Röhrenbrunnen", "Trinkbrunnen Zürich Stadt Zürich"]),
    "V9_holz": ([(47.34617, 8.49938), (47.36191, 8.4932), (47.35094, 8.50568), (47.37524, 8.47842)], ["Holzbrunnen Uetliberg", "Holztrog Brunnen Zürich Wald", "Waldbrunnen Holz Zürichberg"]),
    "flag_vbz": ([(47.37424, 8.52855), (47.3779, 8.5392), (47.3763, 8.5165)], ["VBZ Haltestelle Fahne Zürich", "Zürich Tramhaltestelle Mast Schild", "Haltestellenschild VBZ Bus", "Tramhaltestelle Zürich Haltestellenmast", "VBZ Haltestellentafel"]),
    "kiosk": ([(47.3779, 8.5392), (47.3774, 8.5287), (47.3838, 8.5287)], ["Kiosk Zürich Kreis 4", "k kiosk Zürich Haltestelle", "Kiosk Zürich Kreis 5", "k kiosk Zürich Bahnhof", "Kiosk Zürich Tramhaltestelle"]),
}


def get(url, params=None, tries=3):
    for _ in range(tries):
        try:
            r = requests.get(url, params=params, headers=H, timeout=40)
            if r.status_code == 200: return r
        except requests.RequestException: pass
        time.sleep(2)
    return None


def commons_files(titles):
    if not titles: return []
    r = get(COMMONS, {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 800, "titles": "|".join(titles)})
    out = []
    for p in (r.json().get("query", {}).get("pages", {}).values() if r else []):
        ii = (p.get("imageinfo") or [{}])[0]
        if not ii.get("thumburl"): continue
        em = ii.get("extmetadata", {})
        out.append({"src": "commons", "title": p["title"], "url": ii["thumburl"], "page": ii.get("descriptionurl"),
                    "license": em.get("LicenseShortName", {}).get("value"), "author": re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", ""))[:80]})
    return out


def run(tag):
    geo, qs = T[tag]; titles = []; texts = []
    for lat, lon in geo:
        r = get(COMMONS, {"action": "query", "format": "json", "list": "geosearch", "gscoord": f"{lat}|{lon}", "gsradius": 400, "gslimit": 40, "gsnamespace": 6})
        titles += [g["title"] for g in (r.json().get("query", {}).get("geosearch", []) if r else [])]
        time.sleep(1)
    for q in qs:
        r = get(COMMONS, {"action": "query", "format": "json", "list": "search", "srsearch": q, "srnamespace": 6, "srlimit": 12})
        texts += [g["title"] for g in (r.json().get("query", {}).get("search", []) if r else [])]
        time.sleep(1)
    titles = [t for t in dict.fromkeys(texts + titles[:6]) if re.search(r"\.(jpe?g|png)$", t, re.I)][:20]
    items = []
    for i in range(0, len(titles), 8): items += commons_files(titles[i:i + 8])
    for lat, lon in geo[:2]:
        r = get(PANO, {"place_position": f"{lon},{lat}", "place_distance": "0-40", "limit": 4})
        for f in (r.json().get("features", []) if r else []):
            a = f.get("assets", {}); u = (a.get("sd") or a.get("hd") or {}).get("href")
            if u: items.append({"src": "panoramax", "title": f.get("id"), "url": u, "license": (f.get("properties") or {}).get("license", "CC-BY-SA-4.0"), "author": ""})
    d = OUT / tag; d.mkdir(parents=True, exist_ok=True); done = []
    for k, it in enumerate(items):
        fn = d / f"{k:02d}.jpg"
        if not fn.exists():
            r = get(it["url"])
            if not r: continue
            try: Image.open(io.BytesIO(r.content)).convert("RGB").save(fn, quality=85)
            except Exception: continue
            time.sleep(0.8)
        it["file"] = str(fn.relative_to(ROOT)); done.append(it)
    return done


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--only"); a = ap.parse_args()
    meta = json.loads(META.read_text()) if META.exists() else {}
    for tag in (a.only.split(",") if a.only else T):
        meta[tag] = run(tag); print(tag, len(meta[tag]), flush=True)
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
