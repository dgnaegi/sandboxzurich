"""Commons category photos of Letzigrund (viewing reference only) -> data/raw/photos/letzigrund/commons, meta appended to research/letzigrund_photos.json (key commons)."""
import json, os, re, requests, sys
ROOT = "/Users/danielgnagi/sandboxzurich"; OUT = ROOT + "/data/raw/photos/letzigrund/commons"; os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "SandboxZuerich/0.1 (daniel.gnaegi@outlook.com) reference research"}
API = "https://commons.wikimedia.org/w/api.php"
files = []
for q in ("Letzigrund", "Letzigrund Stadion Tribüne", "Letzigrund stadium interior", "Stadion Letzigrund Zürich Dach", "Weltklasse Zürich Letzigrund", "Letzigrund Badenerstrasse", "Letzigrund Herdernstrasse"):
    for off in (0, 50):
        r = requests.get(API, params=dict(action="query", list="search", srsearch=q, srnamespace=6, srlimit=50, sroffset=off, format="json"), headers=UA, timeout=30).json()
        files += [m["title"] for m in r.get("query", {}).get("search", [])]
files = list(dict.fromkeys(files))[:150]; print(len(files), "candidates")
meta = []
for i in range(0, len(files), 25):
    r = requests.get(API, params=dict(action="query", titles="|".join(files[i:i+25]), prop="imageinfo", iiprop="url|extmetadata", iiurlwidth=1000, format="json"), headers=UA, timeout=30).json()
    for p in r["query"]["pages"].values():
        ii = (p.get("imageinfo") or [None])[0]
        if not ii or not re.search(r"\.(jpe?g)$", p["title"], re.I): continue
        em = ii["extmetadata"]; lic = em.get("LicenseShortName", {}).get("value", "")
        if not lic or "NC" in lic or "ND" in lic: continue
        fn = OUT + "/" + re.sub(r"[^A-Za-z0-9._-]", "_", p["title"][5:])[:80]
        if not os.path.exists(fn):
            try: open(fn, "wb").write(requests.get(ii["thumburl"], headers=UA, timeout=60).content)
            except Exception as e: print("fail", p["title"], e); continue
        meta.append(dict(file=fn.replace(ROOT + "/", ""), title=p["title"], license=lic, author=re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", ""))[:80], url=ii["descriptionurl"]))
print(len(meta), "downloaded")
j = json.load(open(ROOT + "/research/letzigrund_photos.json")); j["commons_category"] = meta
json.dump(j, open(ROOT + "/research/letzigrund_photos.json", "w"), indent=1, ensure_ascii=False)
