"""Photo research Frau Gerolds Garten (Geroldstrasse 23): fetch_v3 wrapper (Mapillary/Commons by place, own meta file) plus a targeted
Wikimedia Commons text search (800 px thumbs) -> data/raw/photos/fgg/commons/, meta research/v3/photos_fgg_commons.json.
Usage: python fetch_fgg.py"""
import json, re, time, urllib.parse, urllib.request
import fetch_v3 as F

SITES = [("fgg_mitte", "Frau Gerolds Garten", 180, 150, 60), ("fgg_strasse", "Geroldstrasse / Viadukt", 200, 120, 70),
         ("fgg_turm", "Freitag-Turm Umgebung", 207, 177, 50)]


def sites():
    return [(i, n, "landmark", *F.local_ll(x, y), r) for i, n, x, y, r in SITES]


F.sites = sites
F.OUT_DIR = F.ROOT / "data" / "raw" / "photos" / "fgg"
F.META = F.ROOT / "research" / "v3" / "photos_fgg.json"
F.SITES_OUT = F.ROOT / "research" / "v3" / "sites_fgg.json"
F.N_ML, F.N_COMMONS, F.N_PANO = 10, 12, 4
H = {"User-Agent": "sandboxzurich-research/1.0 (contact via repo)"}


def get(u, tries=6):
    for k in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=H)).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(15 * (k + 1))
    raise RuntimeError(u)


def commons_search():
    out = F.ROOT / "data/raw/photos/fgg/commons"; out.mkdir(parents=True, exist_ok=True)
    mp = F.ROOT / "research/v3/photos_fgg_commons.json"; meta = json.load(open(mp)) if mp.exists() else {}
    titles = []
    for q in ("Frau Gerolds Garten", "Frau Gerold's Garten Zürich", "Geroldstrasse Zürich Container Garten"):
        u = "https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srlimit=20&format=json&srsearch=" + urllib.parse.quote(q)
        titles += [r["title"] for r in json.loads(get(u))["query"]["search"]]
    for t in dict.fromkeys(titles):
        fn = re.sub(r"[^A-Za-z0-9.]+", "_", t[5:])[:60]
        if not fn.lower().endswith((".jpg", ".jpeg")): continue
        if (out / fn).exists(): continue
        u = "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=800&format=json&titles=" + urllib.parse.quote(t)
        ii = list(json.loads(get(u))["query"]["pages"].values())[0].get("imageinfo", [{}])[0]
        if not ii.get("thumburl"): continue
        (out / fn).write_bytes(get(ii["thumburl"])); time.sleep(3)
        em = ii.get("extmetadata", {})
        meta[fn] = {"title": t, "license": em.get("LicenseShortName", {}).get("value"), "author": re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", ""))[:60],
                    "date": em.get("DateTimeOriginal", {}).get("value", "")[:30]}
        json.dump(meta, open(mp, "w"), indent=1, ensure_ascii=False); print(fn, meta[fn]["license"])


if __name__ == "__main__":
    commons_search()
    F.main()
