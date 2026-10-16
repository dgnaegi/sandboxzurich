"""Detailed reference photo research per landmark / place (v3).

Per site: Mapillary (bbox, recent, pointing at the object, spread over 8 sectors, a few close
detail shots, a few night shots), Wikimedia Commons (geosearch, licence+author per file) and
Panoramax (fallback/extra). Images (max 1024 px) go to data/raw/photos/v3/<id>/, metadata to
research/v3/photos.json. Resumable: sites already in photos.json are skipped unless --force.
Existing files are never re-downloaded.

Usage: python fetch_v3.py [--only id,id] [--force] [--list]
Token: MAPILLARY_TOKEN in .env (parsed manually, value contains '|').
"""
import argparse
import html
import io
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "data" / "raw" / "photos" / "v3"
META = ROOT / "research" / "v3" / "photos.json"
SITES_OUT = ROOT / "research" / "v3" / "sites.json"
UA = "sandboxzurich/0.1 (research)"
H = {"User-Agent": UA, "Api-User-Agent": UA}
ML = "https://graph.mapillary.com/images"
COMMONS = "https://commons.wikimedia.org/w/api.php"
PANO = "https://api.panoramax.xyz/api/search"
MAX_SIDE = 1024
N_ML, N_COMMONS, N_PANO = 16, 8, 4
ORIGIN = (2681400.0, 1248700.0)
_to_wgs = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
_last = {}


def log(m):
    print(time.strftime("%H:%M:%S"), m, flush=True)


def token():
    t = re.search(r"MAPILLARY_TOKEN=(.*)", (ROOT / ".env").read_text()).group(1).strip()
    return t.strip("\"'")


def get(kind, url, params=None, pause=1.0, tries=4):
    for i in range(tries):
        w = _last.get(kind, 0) + pause - time.time()
        if w > 0:
            time.sleep(w)
        try:
            r = requests.get(url, params=params, headers=H, timeout=40)
        except requests.RequestException as e:
            log(f"  net error {e}")
            time.sleep(3)
            continue
        _last[kind] = time.time()
        if r.status_code == 200:
            return r
        if r.status_code in (429, 503):
            time.sleep(8 * (i + 1))
            continue
        log(f"  HTTP {r.status_code} {url[:60]}")
        return None
    return None


def local_ll(x, y):
    lon, lat = _to_wgs.transform(ORIGIN[0] + x, ORIGIN[1] + y)
    return lat, lon


def sites():
    """(id, name, kind, lat, lon, radius_m)."""
    S = []
    land = {  # id -> (override name prefix, radius)
        "prime_tower": ("Prime Tower", 130), "kva_kamin": ("KVA-Kamin", 100),
        "viadukt": ("Im Viadukt", 110), "schiffbau": ("Schiffbau", 100),
        "lochergut": ("Lochergut", 110), "kalkbreite": ("Kalkbreite", 90),
        "st_jakob": ("Kirche St. Jakob", 90), "bullingerkirche": ("Bullingerkirche", 80),
        "kanzlei_schulhaus": ("Kanzlei-Schulhaus", 90),
        "bhf_hardbruecke": ("Bahnhof Hardbruecke", 110), "volkshaus": ("Volkshaus", 80),
        "toni_areal": ("Toni-Areal", 130), "hardau_ii": ("Hardau II", 120),
        "letzigrund": ("Stadion Letzigrund", 150), "bhf_altstetten": ("Bahnhof Altstetten", 130),
        "kirchen_altstetten": ("Alte Kirche und Kirche Altstetten", 100),
        "dreifaltigkeit_wiedikon": ("Dreifaltigkeitskirche", 90),
        "bhf_wiedikon": ("Bahnhof Wiedikon", 90),
        "krematorium_sihlfeld": ("Altes Krematorium", 110),
        "loewenbrunnen": ("Loewenbrunnen", 60),
    }
    allm = []
    for f in ("landmarks_k45", "landmarks_k93"):
        allm += json.load(open(ROOT / f"pipeline/overrides/{f}.json"))["landmarks"]
    for sid, (pre, rad) in land.items():
        m = next(x for x in allm if x["name"].startswith(pre))
        lat, lon = local_ll(m["x"], m["y"])
        S.append((sid, m["name"], "landmark", lat, lon, rad))
    # Haupttor Krematorium (entrance gate, approx. 45 m SW of centre; refine by photos)
    k = next(s for s in S if s[0] == "krematorium_sihlfeld")
    S.append(("krematorium_haupttor", "Friedhof Sihlfeld Haupttor (Eingang)", "landmark",
              k[3] - 0.0003, k[4] - 0.0005, 50))
    places = [  # id, name, lat, lon, radius
        ("helvetiaplatz", "Helvetiaplatz", 47.3762, 8.5258, 100),
        ("langstrasse", "Langstrasse (Ecke Militaerstrasse)", 47.379, 8.5265, 110),
        ("baeckeranlage", "Baeckeranlage", 47.3778, 8.5235, 100),
        ("kasernenareal", "Kasernenareal", 47.3775, 8.533, 130),
        ("josefwiese", "Josefwiese", 47.38585, 8.5231, 100),
        ("roentgenplatz", "Roentgenplatz", 47.3852, 8.5268, 90),
        ("idaplatz", "Idaplatz", 47.3742, 8.5195, 90),
        ("albisriederplatz", "Albisriederplatz", 47.37815, 8.5103, 110),
        ("lindenplatz", "Lindenplatz Altstetten", 47.388, 8.484, 100),
        ("limmatplatz", "Limmatplatz", 47.3847, 8.5316, 110),
        ("escher_wyss_platz", "Escher-Wyss-Platz", 47.3889, 8.5195, 110),
        ("turbinenplatz", "Turbinenplatz", 47.3898, 8.5167, 100),
        ("stauffacher", "Stauffacher", 47.373, 8.529, 100),
        ("bullingerplatz", "Bullingerplatz", 47.37965, 8.516, 90),
        ("hardplatz", "Hardplatz", 47.3825, 8.5147, 90),
        ("hohlstrasse", "Hohlstrasse (Kreis 4, Ecke Langstrasse)", 47.3775, 8.525, 110),
        ("zentralwaescherei", "Zentralwaescherei", 47.3871, 8.5204, 90),
    ]
    for pid, n, la, lo, r in places:
        S.append((pid, n, "place", la, lo, r))
    la, lo = local_ll(-1468.0, 468.5)
    S.append(("rosa_luxemburg_platz", "Rosa-Luxemburg-Platz (Hohlstrasse 444, K9)", "place", la, lo, 80))
    for sid, n, x, y, r in [  # Langstrasse-Unterfuehrung (OSM tunnel way 4592588, ped tunnels 4803419/4803422) and Ole Ole Bar (OSM node 4424003110)
        ("langstr_unterf", "Langstrassen-Unterfuehrung (Mitte)", 913, -321, 75),
        ("langstr_unterf_sued", "Langstrassen-Unterfuehrung Portal Sued (Ole-Ole-Seite)", 893, -366, 45),
        ("langstr_unterf_nord", "Langstrassen-Unterfuehrung Portal Nord (Kreis 5)", 934, -276, 45),
        ("oleole", "Ole Ole Bar, Langstrasse 138", 869, -441, 55),
    ]:
        la, lo = local_ll(x, y)
        S.append((sid, n, "landmark", la, lo, r))
    return S


def metres(lat, lon, lat0, lon0):
    return (lon - lon0) * 111320 * math.cos(math.radians(lat0)), (lat - lat0) * 110574


def bearing(dx, dy):
    return math.degrees(math.atan2(dx, dy)) % 360


def adiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def save(content, dest):
    im = Image.open(io.BytesIO(content)).convert("RGB")
    if max(im.size) > MAX_SIDE:
        s = MAX_SIDE / max(im.size)
        im = im.resize((round(im.size[0] * s), round(im.size[1] * s)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=85, optimize=True)


def is_night(ts_ms):
    d = datetime.fromtimestamp(ts_ms / 1000, timezone.utc)
    h = (d.hour + (2 if 4 <= d.month <= 10 else 1)) % 24
    return h >= 20 or h < 5


def mapillary(sid, lat, lon, rad, tok):
    dlat, dlon = rad / 110574, rad / (111320 * math.cos(math.radians(lat)))
    r = get("ml", ML, {"access_token": tok, "bbox": f"{lon-dlon:.6f},{lat-dlat:.6f},{lon+dlon:.6f},{lat+dlat:.6f}",
                       "fields": "id,thumb_1024_url,compass_angle,computed_geometry,captured_at,creator,is_pano",
                       "limit": 2000}, pause=0.3)
    if not r:
        return []
    cands = []
    for im in r.json().get("data", []):
        if im.get("is_pano") or not im.get("thumb_1024_url") or not im.get("computed_geometry"):
            continue
        ilon, ilat = im["computed_geometry"]["coordinates"]
        dx, dy = metres(lat, lon, ilat, ilon)  # vector image -> object
        d = math.hypot(dx, dy)
        if d > rad or d < 6:
            continue
        diff = adiff(im.get("compass_angle", 0), bearing(dx, dy))
        if diff > 40:
            continue
        yr = datetime.fromtimestamp(im["captured_at"] / 1000, timezone.utc).year
        night = is_night(im["captured_at"])
        score = (0 if yr >= 2020 else 40) + (20 - min(yr - 2014, 10) * 2 if yr >= 2014 else 30) \
            + diff * 0.5 + abs(d - 45) * 0.15
        cands.append(dict(id=im["id"], url=im["thumb_1024_url"], lat=ilat, lon=ilon, d=d, diff=diff,
                          heading=im.get("compass_angle"), ts=im["captured_at"], year=yr, night=night,
                          sector=int(bearing(-dx, -dy) // 45), score=score,
                          author=(im.get("creator") or {}).get("username", "unknown")))
    cands.sort(key=lambda c: c["score"])
    chosen = []

    def ok(c):
        return all(math.hypot(*metres(c["lat"], c["lon"], x["lat"], x["lon"])) > 9 or adiff(c["heading"], x["heading"]) > 30
                   for x in chosen)

    def add(pool, n):
        for c in pool:
            if len(chosen) >= n:
                return
            if c not in chosen and ok(c):
                chosen.append(c)

    for s in range(8):  # one per viewing sector
        add([c for c in cands if c["sector"] == s and not c["night"]], len(chosen) + 1)
    add([c for c in cands if c["d"] < 32 and not c["night"]], min(len(chosen) + 3, N_ML - 2))  # detail
    add([c for c in cands if c["night"]], len(chosen) + 2)  # night
    add([c for c in cands if not c["night"]], N_ML)
    log(f"  mapillary: {len(cands)} usable candidates, {len(chosen)} chosen")
    return chosen


def commons(lat, lon, rad):
    r = get("commons", COMMONS, {"action": "query", "list": "geosearch", "gscoord": f"{lat}|{lon}",
                                 "gsradius": min(rad + 40, 400), "gsnamespace": 6, "gslimit": 60,
                                 "format": "json"}, pause=3.0)
    if not r:
        return []
    hits = [h for h in r.json().get("query", {}).get("geosearch", [])
            if h["title"].lower().endswith((".jpg", ".jpeg", ".png"))][:40]
    if not hits:
        return []
    r2 = get("commons", COMMONS, {"action": "query", "titles": "|".join(h["title"] for h in hits),
                                  "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": MAX_SIDE,
                                  "format": "json"}, pause=3.0)
    if not r2:
        return []
    pos = {h["title"]: h for h in hits}
    out = []
    for p in r2.json().get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        if not ii.get("thumburl") or not re.search(r"CC|Public domain|PD|CC0", lic, re.I):
            continue
        if ii.get("width", 0) < 1000:
            continue
        author = html.unescape(re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "unknown"))).strip()
        date = re.sub(r"<[^>]+>", "", md.get("DateTimeOriginal", {}).get("value", ""))
        h = pos.get(p["title"], {})
        out.append(dict(title=p["title"], url=ii["thumburl"], page=ii.get("descriptionurl"), license=lic,
                        author=author, date=date, lat=h.get("lat"), lon=h.get("lon"), dist=h.get("dist", 999),
                        year=int(date[:4]) if date[:4].isdigit() else 0))
    out.sort(key=lambda c: (-(c["year"] >= 2012), c["dist"]))
    return out[:N_COMMONS]


def panoramax(lat, lon, rad):
    rr = min(rad, 70)
    dlat, dlon = rr / 110574, rr / (111320 * math.cos(math.radians(lat)))
    r = get("pano", PANO, {"bbox": f"{lon-dlon:.6f},{lat-dlat:.6f},{lon+dlon:.6f},{lat+dlat:.6f}", "limit": 60})
    if not r:
        return []
    out, used = [], []
    for f in r.json().get("features", []):
        a = f.get("assets", {})
        href = (a.get("sd") or a.get("hd") or {}).get("href")
        hd = f.get("properties", {}).get("view:azimuth")
        if not href or hd is None:
            continue
        ilon, ilat = f["geometry"]["coordinates"]
        dx, dy = metres(lat, lon, ilat, ilon)
        if adiff(hd, bearing(dx, dy)) > 45 or any(adiff(hd, u) < 40 for u in used):
            continue
        used.append(hd)
        p = f["properties"]
        out.append(dict(id=f["id"], url=href, lat=ilat, lon=ilon, heading=hd, license=p.get("license", ""),
                        author=p.get("geovisio:producer", "unknown"), date=p.get("datetime", "")[:10]))
        if len(out) >= N_PANO:
            break
    return out


def download(url, dest, kind):
    if dest.exists():
        return True
    r = get(kind, url, pause=1.2 if kind == "commons" else 0.2)
    if not r:
        return False
    try:
        save(r.content, dest)
        return True
    except Exception as e:
        log(f"  bad image {e}")
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    S = sites()
    SITES_OUT.parent.mkdir(parents=True, exist_ok=True)
    SITES_OUT.write_text(json.dumps([dict(id=s[0], name=s[1], kind=s[2], lat=round(s[3], 6), lon=round(s[4], 6),
                                          radius=s[5]) for s in S], ensure_ascii=False, indent=1))
    if a.list:
        print(len(S), "sites")
        return
    meta = json.load(open(META)) if META.exists() else {}
    tok = token()
    only = set(a.only.split(",")) if a.only else None
    for sid, name, kind, lat, lon, rad in S:
        if (only and sid not in only) or (sid in meta and not a.force):
            continue
        log(f"== {sid} ({name})")
        photos = []
        d = OUT_DIR / sid
        for c in mapillary(sid, lat, lon, rad, tok):
            f = d / f"ml_{c['id']}.jpg"
            if download(c["url"], f, "ml"):
                photos.append(dict(file=str(f.relative_to(ROOT)), source="mapillary", license="CC BY-SA 4.0",
                                   author=c["author"], url=f"https://www.mapillary.com/app/?pKey={c['id']}",
                                   lat=c["lat"], lon=c["lon"], heading=c["heading"], year=c["year"],
                                   night=c["night"], dist_m=round(c["d"])))
        for c in commons(lat, lon, rad):
            f = d / ("cm_" + re.sub(r"[^A-Za-z0-9]+", "_", c["title"][5:])[:60] + ".jpg")
            if download(c["url"], f, "commons"):
                photos.append(dict(file=str(f.relative_to(ROOT)), source="commons", license=c["license"],
                                   author=c["author"], url=c["page"], title=c["title"], lat=c["lat"],
                                   lon=c["lon"], heading=None, year=c["year"], night=False,
                                   dist_m=round(c["dist"])))
        for c in panoramax(lat, lon, rad):
            f = d / f"px_{c['id'][:12]}.jpg"
            if download(c["url"], f, "pano"):
                photos.append(dict(file=str(f.relative_to(ROOT)), source="panoramax", license=c["license"],
                                   author=c["author"], url="https://api.panoramax.xyz/#focus=pic&pic=" + c["id"],
                                   lat=c["lat"], lon=c["lon"], heading=c["heading"],
                                   year=int(c["date"][:4]) if c["date"][:4].isdigit() else 0, night=False, dist_m=None))
        meta[sid] = dict(name=name, kind=kind, lat=round(lat, 6), lon=round(lon, 6), photos=photos)
        META.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
        log(f"  -> {len(photos)} photos")


if __name__ == "__main__":
    main()
