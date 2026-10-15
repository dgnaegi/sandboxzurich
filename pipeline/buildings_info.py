"""Collect per-address building knowledge + reference photos for the test area (R2).

Sources: OSM (addresses/tags), Stadt Zuerich Denkmalpflege-Inventar (WFS, CC0), Wikidata/Wikipedia
(geosearch), Wikimedia Commons (geotagged files, per-file licence), Panoramax (street photos, crops).
Output: research/buildings/testarea.json, photos in data/raw/photos/buildings/, sheets in preview/.

Usage: python buildings_info.py [stage ...]   stages: addr heritage wiki commons panoramax sheets merge
Everything network-related is cached in data/raw/photos/buildings/_cache (never refetched).
Commons downloads are throttled (>=3.5 s, long back-off on HTTP 429).
"""
import json
import math
import re
import sys
import time

import requests

from config import AREA, ROOT
from sources import geo, osm

OUT = ROOT / "research" / "buildings"
PH = ROOT / "data" / "raw" / "photos" / "buildings"
CACHE = PH / "_cache"
PREVIEW = ROOT / "preview"
UA = {"User-Agent": "gtazurich-research/0.1 (daniel.gnaegi@outlook.com)"}
STREETS = ["Langstrasse", "Militärstrasse", "Hohlstrasse", "Kanonengasse", "Helvetiaplatz", "Bäckerstrasse"]
RELEVANT = ["building", "building:levels", "building:colour", "building:material", "building:part", "roof:shape",
            "roof:colour", "roof:levels", "name", "shop", "amenity", "tourism", "craft", "office", "leisure",
            "start_date", "architect", "heritage", "heritage:operator", "image", "wikimedia_commons", "wikidata",
            "wikipedia", "description", "operator", "brand", "cuisine"]
for d in (OUT, PH, CACHE, PREVIEW):
    d.mkdir(parents=True, exist_ok=True)
HELV = (811.0, -934.0)
X0, Y0, X1, Y1 = 600, -1000, 1200, -400  # test area (local m)


def jget(url, cache, **kw):
    f = CACHE / cache
    if f.exists():
        return json.load(open(f))
    for i in range(4):
        r = requests.get(url, headers=UA, timeout=120, **kw)
        if r.status_code == 429 or (r.ok and '"error"' in r.text[:20]):
            time.sleep(20 * (i + 1))
            continue
        r.raise_for_status()
        f.write_text(r.text)
        return r.json()
    raise RuntimeError("fetch failed " + url[:80])


def ll(x, y):
    lon, lat = geo.lv95_to_wgs(2681400 + x, 1248700 + y)
    return lat, lon


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ---------------------------------------------------------------- addresses
def stage_addr():
    nodes, els = osm()
    pos = {}
    for e in els:
        if e["type"] == "node" and e["id"] in nodes:
            pos[e["id"]] = nodes[e["id"]]

    def center(e):
        if e["type"] == "node":
            return pos.get(e["id"])
        ps = [pos[i] for i in e.get("nodes", []) if i in pos]
        return (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps)) if ps else None

    cents = [(e, center(e)) for e in els if e.get("tags") and e["type"] != "relation"]
    cents = [(e, c) for e, c in cents if c and X0 - 30 <= c[0] <= X1 + 30 and Y0 - 30 <= c[1] <= Y1 + 30]
    pois = [(e, c) for e, c in cents if any(k in e["tags"] for k in ("shop", "amenity", "craft", "office", "tourism"))
            and e["tags"].get("name")]
    addrs = {}
    for e, c in cents:
        t = e["tags"]
        if "addr:housenumber" not in t or "addr:street" not in t or not (X0 <= c[0] <= X1 and Y0 <= c[1] <= Y1):
            continue
        key = f"{t['addr:street']} {t['addr:housenumber']}"
        a = addrs.setdefault(key, {"street": t["addr:street"], "nr": t["addr:housenumber"], "x": round(c[0], 1),
                                   "y": round(c[1], 1), "osm_tags_relevant": {}, "osm_ids": []})
        a["osm_ids"].append(f"{e['type']}/{e['id']}")
        for k in RELEVANT:
            if k in t and k not in a["osm_tags_relevant"]:
                a["osm_tags_relevant"][k] = t[k]
    # enclosing building way tags (building levels etc.) for address nodes: nearest building centroid < 15 m
    blds = [(e, c) for e, c in cents if "building" in e["tags"] and e["type"] == "way"]
    for a in addrs.values():
        if "building" not in a["osm_tags_relevant"]:
            best = min(blds, key=lambda b: dist(b[1], (a["x"], a["y"])), default=None)
            if best and dist(best[1], (a["x"], a["y"])) < 12:
                for k in RELEVANT:
                    if k in best[0]["tags"]:
                        a["osm_tags_relevant"].setdefault(k, best[0]["tags"][k])
        near = []
        for e, c in pois:
            t = e["tags"]
            same = t.get("addr:street") == a["street"] and t.get("addr:housenumber") == a["nr"]
            if same or dist(c, (a["x"], a["y"])) < 14:
                near.append({k: t[k] for k in ("name", "shop", "amenity", "craft", "office", "tourism", "cuisine") if k in t})
        a["ground_floor_pois"] = near[:8]
    json.dump(addrs, open(CACHE / "addrs.json", "w"), ensure_ascii=False, indent=1)
    from collections import Counter
    print("addresses", len(addrs), Counter(a["street"] for a in addrs.values()).most_common(8))


def load_addrs():
    return json.load(open(CACHE / "addrs.json"))


# ---------------------------------------------------------------- heritage
def stage_heritage():
    f = ROOT / "data" / "raw" / "heritage" / "inv.geojson"
    if not f.exists():
        url = ("https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Denkmalpflege_Inventar?SERVICE=WFS&VERSION=1.1.0"
               "&REQUEST=GetFeature&TYPENAME=denkmalpflege_inventar_p&outputFormat=GeoJSON&srsName=EPSG:4326")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(requests.get(url, headers=UA, timeout=300).text)
    feats = json.load(open(f))["features"]
    items = []
    for ft in feats:
        p = ft["properties"]
        lon, lat = ft["geometry"]["coordinates"]
        x, y = geo.to_local(lon, lat)
        if X0 - 40 <= x <= X1 + 40 and Y0 - 40 <= y <= Y1 + 40:
            items.append((p, (float(x), float(y))))
    addrs = load_addrs()
    n = 0
    for a in addrs.values():
        hit = None
        for p, c in items:
            bez = (p.get("objektbeze") or "") + " " + (p.get("adresse") or "")
            m = re.match(r"\s*([^\d,]+?)\s*(\d.*)$", p.get("objektbeze") or "")
            nrs = set(re.findall(r"\d+[a-z]?", m.group(2))) if m else set()
            street_ok = m and m.group(1).strip().lower() == a["street"].lower()
            if (street_ok and a["nr"].lower() in nrs) or (dist(c, (a["x"], a["y"])) < 12):
                hit = p
                break
        if hit:
            n += 1
            a["heritage"] = {"name": hit.get("objektbeze"), "year": hit.get("baujahr"), "architect": None,
                             "protected": hit.get("unterschut"), "inventory": hit.get("inventarka"),
                             "note": hit.get("naeherebez"), "source": "Stadt Zuerich Denkmalpflege_Inventar (CC0)"}
    json.dump(addrs, open(CACHE / "addrs.json", "w"), ensure_ascii=False, indent=1)
    print("heritage points in area", len(items), "matched addresses", n)


# ---------------------------------------------------------------- wikidata / wikipedia
def stage_wiki():
    q = ('SELECT ?i ?iLabel ?c ?aLabel ?inc ?img ?art WHERE { SERVICE wikibase:box { ?i wdt:P625 ?c . '
         'bd:serviceParam wikibase:cornerSouthWest "Point(8.5230 47.3740)"^^geo:wktLiteral . '
         'bd:serviceParam wikibase:cornerNorthEast "Point(8.5335 47.3815)"^^geo:wktLiteral } '
         'OPTIONAL{?i wdt:P84 ?a} OPTIONAL{?i wdt:P571 ?inc} OPTIONAL{?i wdt:P18 ?img} '
         'OPTIONAL{?art schema:about ?i; schema:isPartOf <https://de.wikipedia.org/>} '
         'SERVICE wikibase:label { bd:serviceParam wikibase:language "de,en". } }')
    wd = jget("https://query.wikidata.org/sparql", "wd.json", params={"format": "json", "query": q})["results"]["bindings"]
    ents = {}
    for b in wd:
        qid = b["i"]["value"].rsplit("/", 1)[1]
        m = re.match(r"Point\(([\d.]+) ([\d.]+)\)", b["c"]["value"])
        x, y = geo.to_local(float(m.group(1)), float(m.group(2)))
        e = ents.setdefault(qid, {"qid": qid, "title": b.get("iLabel", {}).get("value"), "x": float(x), "y": float(y)})
        if "aLabel" in b:
            e["architect"] = b["aLabel"]["value"]
        if "inc" in b:
            e["year"] = b["inc"]["value"][:4]
        if "art" in b:
            e["url"] = b["art"]["value"]
    # de.wikipedia geosearch (articles with coordinates)
    gs = jget("https://de.wikipedia.org/w/api.php?action=query&list=geosearch&gscoord=47.3777|8.5284&gsradius=500"
              "&gslimit=500&format=json", "dewiki_geo.json")["query"]["geosearch"]
    wp = []
    for g in gs:
        x, y = geo.to_local(g["lon"], g["lat"])
        wp.append({"title": g["title"], "url": "https://de.wikipedia.org/wiki/" + g["title"].replace(" ", "_"),
                   "x": float(x), "y": float(y)})
    addrs = load_addrs()
    n = 0
    for a in addrs.values():
        c = (a["x"], a["y"])
        tag = a["osm_tags_relevant"]
        w = None
        a.pop("wikidata", None)
        a.pop("wiki", None)
        if "source" not in a.get("heritage", {}):
            a.pop("heritage", None)
        for q_ in wp:
            if dist(c, (q_["x"], q_["y"])) < 12:
                w = {"title": q_["title"], "url": q_["url"]}
                break
        for e in ents.values():
            if (dist(c, (e["x"], e["y"])) < 12 and e["title"] and not re.fullmatch(r"Q\d+", e["title"])) or \
                    tag.get("wikidata") == e["qid"]:
                a.setdefault("wikidata", []).append({k: e.get(k) for k in ("qid", "title", "architect", "year", "url")})
        if a.get("wikidata") and not w:
            u = next((d["url"] for d in a["wikidata"] if d.get("url")), None)
            if u:
                w = {"title": u.rsplit("/", 1)[1].replace("_", " "), "url": u}
        if w:
            a["wiki"] = w
            n += 1
        for d in a.get("wikidata", []):
            h = a.setdefault("heritage", {"name": None, "year": None, "architect": None, "protected": None})
            h["architect"] = h.get("architect") or d.get("architect")
            h["year"] = h.get("year") or d.get("year")
    json.dump(addrs, open(CACHE / "addrs.json", "w"), ensure_ascii=False, indent=1)
    print("wikidata ents", len(ents), "wikipedia geo", len(wp), "addresses with wiki", n)


# ---------------------------------------------------------------- commons
def commons_files():
    lst = jget("https://commons.wikimedia.org/w/api.php?action=query&list=geosearch&gscoord=47.3777|8.5284"
               "&gsradius=520&gslimit=500&gsnamespace=6&format=json", "commons_geo.json")["query"]["geosearch"]
    meta = {}
    for i in range(0, len(lst), 40):
        part = lst[i:i + 40]
        titles = "|".join(p["title"] for p in part)
        d = jget("https://commons.wikimedia.org/w/api.php", f"commons_info_{i}.json", params={
            "action": "query", "titles": titles, "prop": "imageinfo", "iiprop": "url|extmetadata|size",
            "iiurlwidth": 800, "format": "json"})
        for pg in d["query"]["pages"].values():
            ii = (pg.get("imageinfo") or [None])[0]
            if ii:
                em = ii.get("extmetadata", {})
                meta[pg["title"]] = {
                    "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"),
                    "license": em.get("LicenseShortName", {}).get("value"),
                    "author": re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip()[:120],
                    "desc": re.sub("<[^>]+>", "", em.get("ImageDescription", {}).get("value", "")).strip()[:160]}
    return lst, meta


def throttle_get(url, dest, pause, tries=5):
    wait = pause
    for _ in range(tries):
        time.sleep(wait)
        try:
            r = requests.get(url, headers=UA, timeout=60)
        except requests.RequestException as ex:
            print("ERR", repr(ex)[:80], flush=True)
            wait = 10
            continue
        if r.status_code == 429:
            wait = max(wait * 3, 30)
            print("429, waiting", wait, flush=True)
            continue
        if r.status_code != 200:
            print("HTTP", r.status_code, url[:90], flush=True)
            return False
        dest.write_bytes(r.content)
        return True
    return False


def stage_commons():
    lst, meta = commons_files()
    addrs = load_addrs()
    cand = []
    for p in lst:
        m = meta.get(p["title"])
        if not m or not m["thumb"]:
            continue
        x, y = geo.to_local(p["lon"], p["lat"])
        best = min(addrs.values(), key=lambda a: dist((a["x"], a["y"]), (x, y)))
        d = dist((best["x"], best["y"]), (x, y))
        if d < 30 and X0 <= x <= X1 and Y0 <= y <= Y1:
            cand.append((d, p["title"], best, m))
    print("commons geotagged", len(lst), "near an address", len(cand), flush=True)
    d2 = PH / "commons"
    d2.mkdir(exist_ok=True)
    cand.sort(key=lambda t: t[0])
    for d, title, a, m in cand[:150]:
        fn = re.sub(r"[^\w.-]+", "_", title[5:])[:70]
        if not fn.lower().endswith((".jpg", ".jpeg", ".png")):
            fn += ".jpg"
        dest = d2 / fn
        if not dest.exists() and not throttle_get(m["thumb"], dest, 3.5):
            continue
        if any(p["file"] == str(dest.relative_to(ROOT)) for p in a.get("photos", [])):
            continue
        a.setdefault("photos", []).append({"file": str(dest.relative_to(ROOT)), "source": "Wikimedia Commons",
                                           "license": m["license"], "author": m["author"], "url": m["page"],
                                           "caption": m["desc"], "dist_m": round(d, 1)})
        json.dump(addrs, open(CACHE / "addrs.json", "w"), ensure_ascii=False, indent=1)
    print("commons done")


# ---------------------------------------------------------------- panoramax
def px_features():
    feats = {}
    nx, ny = 4, 4
    lat0, lon0 = ll(X0 - 20, Y0 - 20)
    lat1, lon1 = ll(X1 + 20, Y1 + 20)
    for i in range(nx):
        for j in range(ny):
            w = lon0 + (lon1 - lon0) * i / nx
            e = lon0 + (lon1 - lon0) * (i + 1) / nx
            s = lat0 + (lat1 - lat0) * j / ny
            n = lat0 + (lat1 - lat0) * (j + 1) / ny
            d = jget(f"https://api.panoramax.xyz/api/search?bbox={w:.6f},{s:.6f},{e:.6f},{n:.6f}&limit=1000",
                     f"px_{i}_{j}.json")
            if len(d["features"]) >= 1000:
                print("WARNING cell saturated", i, j)
            for f in d["features"]:
                feats[f["id"]] = f
    return list(feats.values())


def stage_panoramax():
    from PIL import Image
    feats = px_features()
    cams = []
    for f in feats:
        p = f["properties"]
        if "view:azimuth" not in p or "sd" not in f["assets"]:
            continue
        x, y = geo.to_local(*f["geometry"]["coordinates"])
        pi = p.get("pers:interior_orientation", {})
        fl, sw = pi.get("focal_length"), (pi.get("sensor_array_dimensions") or [None])[0]
        cams.append({"id": f["id"], "x": float(x), "y": float(y), "az": p["view:azimuth"], "sd": f["assets"]["sd"]["href"],
                     "date": p.get("datetime", "")[:10], "producer": p.get("geovisio:producer"),
                     "license": p.get("license"), "focal": fl, "sensor": sw,
                     "url": "https://api.panoramax.xyz/api/search?ids=" + f["id"]})
    print("panoramax images", len(cams), flush=True)
    addrs = load_addrs()
    chosen = {}
    used = set()
    order = sorted(addrs.values(), key=lambda a: (a["street"] not in STREETS, a["street"], a["nr"]))
    for a in order:
        best = None
        for c in cams:
            dx, dy = a["x"] - c["x"], a["y"] - c["y"]
            d = math.hypot(dx, dy)
            if not 5 <= d <= 40:
                continue
            brg = math.degrees(math.atan2(dx, dy)) % 360  # azimuth east of north
            dl = (brg - c["az"] + 180) % 360 - 180
            if abs(dl) > 42:
                continue
            s = d + 0.35 * abs(dl) - (10 if c["id"] in used else 0) - (3 if c["date"] >= "2025" else 0)
            if best is None or s < best[0]:
                best = (s, c, d, dl)
        if best:
            chosen[a["street"] + " " + a["nr"]] = best
            used.add(best[1]["id"])
    print("addresses with a candidate image", len(chosen), "unique images", len(used), flush=True)
    d2 = PH / "panoramax"
    d2.mkdir(exist_ok=True)
    (CACHE / "px").mkdir(exist_ok=True)
    for key, (s, c, d, dl) in chosen.items():
        a = addrs[key]
        raw = CACHE / "px" / (c["id"] + ".jpg")
        if not raw.exists() and not throttle_get(c["sd"], raw, 1.0):
            continue
        im = Image.open(raw).convert("RGB")
        W, H = im.size
        if W / H > 1.8:  # equirectangular, skip
            continue
        hf = 90.0
        if c["focal"] and c["sensor"] and c["focal"] > 0:
            # focal given in mm, sensor px -> assume 1/2.3" (6.17 mm) sensors are not known; keep 90 deg default
            hf = 90.0
        t = math.tan(math.radians(hf / 2))
        half = math.atan(11.0 / max(d, 6)) * 1.0
        half = min(max(half, math.radians(14)), math.radians(40))
        cx = 0.5 + math.tan(math.radians(dl)) / (2 * t)
        w = (math.tan(half) * 2) / (2 * t) * 1.0
        w = min(max(w, 0.3), 1.0)
        x0 = min(max(cx - w / 2, 0), 1 - w)
        crop = im.crop((int(x0 * W), 0, int((x0 + w) * W), H))
        crop.thumbnail((900, 700))
        fn = f"{re.sub(r'[^A-Za-z0-9]+', '_', key)}_{c['id'][:6]}.jpg"
        crop.save(d2 / fn, quality=82)
        a.setdefault("photos", []).append({
            "file": str((d2 / fn).relative_to(ROOT)), "source": "Panoramax", "license": c["license"],
            "author": c["producer"], "url": c["url"], "date": c["date"], "dist_m": round(d, 1),
            "crop_note": "crop of street image towards address; bearing offset %.0f deg" % dl})
    json.dump(addrs, open(CACHE / "addrs.json", "w"), ensure_ascii=False, indent=1)
    print("panoramax crops done")


# ---------------------------------------------------------------- sheets
def stage_sheets():
    from PIL import Image, ImageDraw
    addrs = load_addrs()
    for st in STREETS:
        items = []
        sel = (lambda a: dist((a["x"], a["y"]), HELV) < 70) if st == "Helvetiaplatz" else (lambda a: a["street"] == st)
        for a in sorted((a for a in addrs.values() if sel(a)),
                        key=lambda a: [int(v) if v.isdigit() else v for v in re.split(r"(\d+)", a["nr"])]):
            for p in a.get("photos", []):
                if p["source"] == "Panoramax":
                    items.append((a["nr"] if st != "Helvetiaplatz" else a["street"][:4] + a["nr"], p["file"]))
                    break
            else:
                if a.get("photos"):
                    items.append((a["nr"], a["photos"][0]["file"]))
        per, cols, tw, th = 12, 4, 400, 300
        sheets = [items[i:i + per] for i in range(0, len(items), per)][:3]
        if len(sheets) > 1 and len(sheets[-1]) < 5:
            last = sheets.pop()
            sheets[-1] += last
        for si, chunk in enumerate(sheets):
            rows = math.ceil(len(chunk) / cols)
            sh = Image.new("RGB", (cols * tw, rows * th), (30, 30, 30))
            for k, (nr, fp) in enumerate(chunk):
                im = Image.open(ROOT / fp).convert("RGB")
                im.thumbnail((tw - 4, th - 4))
                px, py = (k % cols) * tw + 2, (k // cols) * th + 2
                sh.paste(im, (px, py))
                dr = ImageDraw.Draw(sh)
                dr.rectangle((px, py, px + 34 + 9 * len(nr), py + 20), fill=(0, 0, 0))
                dr.text((px + 4, py + 4), f"{st[:4]} {nr}", fill=(255, 255, 0))
            name = f"ref_buildings_{st}{'' if si == 0 else '_' + str(si + 1)}.jpg"
            sh.save(PREVIEW / name, quality=80)
            print(name, [n for n, _ in chunk])


# ---------------------------------------------------------------- merge
def stage_merge():
    addrs = load_addrs()
    notes = {}
    nf = OUT / "visual_notes.json"
    if nf.exists():
        notes = json.load(open(nf))
    out = []
    for key, a in sorted(addrs.items()):
        a = dict(a)
        a.setdefault("heritage", {"name": None, "year": None, "architect": None, "protected": None})
        a.setdefault("wiki", None)
        a.setdefault("photos", [])
        a["notes"] = notes.get(key, "")
        out.append(a)
    json.dump(out, open(OUT / "testarea.json", "w"), ensure_ascii=False, indent=1)
    n = len(out)
    ph = sum(1 for a in out if a["photos"])
    nt = sum(1 for a in out if a["notes"])
    h = sum(1 for a in out if a["heritage"].get("name"))
    w = sum(1 for a in out if a["wiki"])
    print(f"addresses {n} photo {ph} notes {nt} heritage {h} wiki {w}")


STAGES = {"addr": stage_addr, "heritage": stage_heritage, "wiki": stage_wiki, "commons": stage_commons,
          "panoramax": stage_panoramax, "sheets": stage_sheets, "merge": stage_merge}

if __name__ == "__main__":
    for s in sys.argv[1:] or ["addr", "heritage", "wiki", "panoramax", "sheets", "merge"]:
        STAGES[s]()
