"""Commons search for HB surroundings (Europaallee, passerelle, Velostation, Bahnhofbruecke, Perron details); reference only. Output data/raw/photos/hbx/ + research/hb/hbx_photos.json"""
import json, os, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data/raw/photos/hbx"); UA = {"User-Agent": "sandboxzurich-research/1.0 (reference photos)"}
Q = {"europaallee": ["Europaallee Zürich", "Passerelle Europaallee", "Velostation Europaallee", "Europaallee Gleisfeld Passerelle"],
     "bruecke": ["Bahnhofbrücke Zürich", "Bahnhofquai Zürich", "Sihlquai Zürich Carterminal", "Carparkplatz Sihlquai"],
     "perron": ["Zürich HB Perron Sektortafel", "Zürich HB Perron Dach", "Zürich Hauptbahnhof Gleis Perron Bank", "Billettautomat Perron", "Zürich HB Perron Anzeigetafel"],
     "platz": ["Zürich Bahnhofplatz Tramhaltestelle", "Alfred Escher Brunnen Zürich", "Velo Parkierung Bahnhofplatz Zürich", "Zürich Bahnhofplatz Tram"]}
def get(req):
    for k in range(6):
        try: return urllib.request.urlopen(req, timeout=40).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(20 * (k + 1))
    raise RuntimeError("429")
def api(p):
    return json.loads(get(urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({**p, "format": "json"}), headers=UA)))
res = []; seen = set()
for g, qs in Q.items():
    for q in qs:
        d = api({"action": "query", "generator": "search", "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": 12, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1000})
        for p in d.get("query", {}).get("pages", {}).values():
            ii = p["imageinfo"][0]; t = p["title"]
            if t in seen or not t.lower().endswith((".jpg", ".jpeg")): continue
            seen.add(t); md = ii.get("extmetadata", {})
            res.append({"group": g, "title": t, "url": ii["thumburl"], "lic": md.get("LicenseShortName", {}).get("value", "?"), "author": md.get("Artist", {}).get("value", "?")[:80], "page": ii["descriptionurl"]})
        time.sleep(3)
n = 0
for r in res:
    fn = f"{r['group']}_{n:03d}.jpg"; fp = os.path.join(OUT, fn)
    try:
        open(fp, "wb").write(get(urllib.request.Request(r["url"], headers=UA))); r["file"] = fn; n += 1
    except Exception as e: r["err"] = str(e)[:60]
    time.sleep(2)
json.dump(res, open(os.path.join(ROOT, "research/hb/hbx_photos.json"), "w"), indent=1, ensure_ascii=False)
print(n, "downloaded of", len(res))
