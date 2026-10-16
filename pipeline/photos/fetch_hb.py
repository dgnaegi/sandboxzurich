"""Reference photos for Zuerich HB (Commons categories + geosearch + text search, Mapillary, Panoramax).
Images (max 1280 px) -> data/raw/photos/hb/, metadata + licences -> research/hb/photos.json, CREDITS.md.
Reference only (never textures). Resumable: existing files are not re-downloaded."""
import html, io, json, math, re, sys, time
from pathlib import Path
import requests
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F

ROOT = F.ROOT
OUT = ROOT / "data/raw/photos/hb"
META = ROOT / "research/hb/photos.json"
F.MAX_SIDE = 1280
C = F.COMMONS
LAT, LON = F.local_ll(1790, -650)
SKIP = ("Güterbahnhof", "Lokremisen", "Trains at", "Zentralstellwerk", "Rail tracks at", "Plans of", "Historical images")
GROUP = {"Haupthalle": "haupthalle", "Querhalle": "querhalle", "Perronhalle": "perron", "Interior": "interior", "Exterior": "exterior",
         "Christmas": "markt", "Information": "tafeln", "Löwenstrasse": "loewenstrasse", "Museumstrasse": "museumstrasse",
         "track 21": "perron", "shed": "perron", "Pavillon": "pavillon", "Velotunnel": "velo", "night": "nacht", "Aerial": "luft", "Construction": "bau"}


def dl(url, dest, kind):
    if dest.exists(): return True
    r = F.get(kind, url, pause=2.5 if kind == "commons" else 0.3)
    if not r: return False
    try: F.save(r.content, dest); return True
    except Exception as e: log(f"bad image {e}"); return False


def log(m): print(time.strftime("%H:%M:%S"), m, flush=True)


def cat_files(root, depth=3):
    seen, files, q = set(), {}, [(root, 0, "root")]
    while q:
        c, d, g = q.pop(0)
        if c in seen: continue
        seen.add(c)
        for k, v in GROUP.items():
            if k in c: g = v
        cont = {}
        while True:
            r = F.get("commons", C, {"action": "query", "list": "categorymembers", "cmtitle": c, "cmlimit": 500, "cmtype": "subcat|file", "format": "json", **cont}, pause=1.6)
            if not r: break
            j = r.json()
            for m in j["query"]["categorymembers"]:
                if m["ns"] == 14 and d < depth and not any(s in m["title"] for s in SKIP): q.append((m["title"], d + 1, g))
                elif m["ns"] == 6 and m["title"].lower().endswith((".jpg", ".jpeg", ".png")): files.setdefault(m["title"], g)
            if "continue" in j: cont = j["continue"]
            else: break
        log(f"cat {c}: total files {len(files)}")
    return files


def search_files(terms):
    out = {}
    for t in terms:
        r = F.get("commons", C, {"action": "query", "list": "search", "srsearch": t, "srnamespace": 6, "srlimit": 100, "format": "json"}, pause=1.6)
        if r:
            for m in r.json()["query"]["search"]:
                if m["title"].lower().endswith((".jpg", ".jpeg", ".png")): out.setdefault(m["title"], "search")
        log(f"search {t}: {len(out)}")
    r = F.get("commons", C, {"action": "query", "list": "geosearch", "gscoord": f"{LAT}|{LON}", "gsradius": 450, "gsnamespace": 6, "gslimit": 300, "format": "json"}, pause=1.6)
    if r:
        for m in r.json()["query"]["geosearch"]:
            if m["title"].lower().endswith((".jpg", ".jpeg", ".png")): out.setdefault(m["title"], "geo")
    log(f"geo -> {len(out)}")
    return out


def info(titles):
    out = {}
    for i in range(0, len(titles), 40):
        ch = titles[i:i + 40]
        r = F.get("commons", C, {"action": "query", "titles": "|".join(ch), "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1280, "format": "json"}, pause=4.0)
        if not r: continue
        for p in r.json().get("query", {}).get("pages", {}).values():
            ii = (p.get("imageinfo") or [{}])[0]
            md = ii.get("extmetadata", {})
            lic = md.get("LicenseShortName", {}).get("value", "")
            if not ii.get("thumburl") or not re.search(r"CC|Public domain|PD|CC0", lic, re.I) or ii.get("width", 0) < 900: continue
            author = html.unescape(re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "unknown"))).strip()
            date = re.sub(r"<[^>]+>", "", md.get("DateTimeOriginal", {}).get("value", ""))
            out[p["title"]] = dict(url=ii["thumburl"], page=ii.get("descriptionurl"), license=lic, author=author[:80], date=date[:20], w=ii.get("width"), h=ii.get("height"))
    return out


def main():
    meta = json.load(open(META)) if META.exists() else {"photos": []}
    have = {p["title"] for p in meta["photos"] if p.get("title")}
    CAND = ROOT / "research/hb/_cands.json"
    if CAND.exists(): files = json.load(open(CAND))
    else:
      files = cat_files("Category:Zürich Hauptbahnhof")
      for k, v in search_files(["Hauptbahnhof Zürich Haupthalle", "Zürich HB Halle Engel", "Zürich Hauptbahnhof Perron", "Zürich HB Bahnhofplatz Fassade", "Zürich Hauptbahnhof Querhalle", "Zürich HB Shopville", "Zürich HB Gleis", "Zürich Hauptbahnhof Anzeigetafel", "Zürich Hauptbahnhof Rolltreppe", "Landesmuseum Zürich Bahnhof Perron"]).items():
          files.setdefault(k, v)
      json.dump(files, open(CAND, "w"), ensure_ascii=False)
    titles = [t for t in files if t not in have]
    log(f"{len(files)} candidate files, {len(titles)} new")
    INF = ROOT / "research/hb/_info.json"
    inf = json.load(open(INF)) if INF.exists() else {}
    todo = [t for t in titles if t not in inf]
    for i in range(0, len(todo), 40):
        inf.update(info(todo[i:i + 40])); json.dump(inf, open(INF, "w"), ensure_ascii=False); log(f"info {i + 40}/{len(todo)}")
    inf = {t: v for t, v in inf.items() if t in titles}
    log(f"{len(inf)} with usable licence")
    n = 0
    PRI = ["haupthalle", "querhalle", "perron", "interior", "exterior", "tafeln", "markt", "loewenstrasse", "museumstrasse", "pavillon", "nacht", "velo", "bau"]
    order = sorted(inf, key=lambda t: PRI.index(files[t]) if files[t] in PRI else 50)
    for t in order:
        m = inf[t]
        f = OUT / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", t[5:])[:70] + ".jpg")
        if dl(m["url"], f, "commons"):
            meta["photos"].append(dict(file=str(f.relative_to(ROOT)), source="commons", title=t, group=files[t], **m))
            n += 1
            if n % 20 == 0: META.write_text(json.dumps(meta, ensure_ascii=False, indent=1)); log(f"downloaded {n}")
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    # Mapillary + Panoramax
    tok = F.token()
    for rad_c in ((1790, -650, 230), (1700, -640, 120)):
        la, lo = F.local_ll(rad_c[0], rad_c[1])
        for c in F.mapillary("hb", la, lo, rad_c[2], tok)[:40]:
            f = OUT / f"ml_{c['id']}.jpg"
            if dl(c["url"], f, "ml") and not any(p["file"].endswith(f.name) for p in meta["photos"]):
                meta["photos"].append(dict(file=str(f.relative_to(ROOT)), source="mapillary", license="CC BY-SA 4.0", author=c["author"],
                                           page=f"https://www.mapillary.com/app/?pKey={c['id']}", lat=c["lat"], lon=c["lon"], heading=c["heading"], year=c["year"], group="mapillary"))
        for c in F.panoramax(la, lo, rad_c[2]):
            f = OUT / f"px_{c['id'][:12]}.jpg"
            if dl(c["url"], f, "pano") and not any(p["file"].endswith(f.name) for p in meta["photos"]):
                meta["photos"].append(dict(file=str(f.relative_to(ROOT)), source="panoramax", license=c["license"], author=c["author"],
                                           page="https://api.panoramax.xyz/#focus=pic&pic=" + c["id"], lat=c["lat"], lon=c["lon"], heading=c["heading"], group="panoramax"))
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    L = ["# HB photo credits (reference only, not used as textures)\n", f"{len(meta['photos'])} images, data/raw/photos/hb/\n", "| file | source | licence | author | page |", "|---|---|---|---|---|"]
    for p in meta["photos"]:
        L.append(f"| {Path(p['file']).name} | {p['source']} | {p['license']} | {str(p.get('author',''))[:50].replace('|','/')} | {p.get('page','')} |")
    (ROOT / "research/hb/CREDITS.md").write_text("\n".join(L) + "\n")
    log(f"DONE {len(meta['photos'])} photos")


if __name__ == "__main__":
    main()
