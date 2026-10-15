"""Collect georeferenced reference photos per 200 m playarea tile.

For every tile in data/build/playarea.json (local metres, LV95 origin 2681400/1248700):
  (a) Wikimedia Commons geosearch around the tile centre (radius 142 m, files only),
  (b) Panoramax search inside the tile bbox (street photos with view azimuth).
At most 3 photos per tile; Panoramax first (up to 2, distinct headings), then Commons,
then extra Panoramax if Commons had too little.

Output:
  data/raw/photos/tiles/<ix_iy>/*.jpg   (longest side 1024 px, JPEG)
  research/photos/by_tile.json          {"ix_iy": [{file, source, license, author, url, lat, lon, heading?, title?}]}

Resumable: tiles already present in by_tile.json are skipped.
Usage: python fetch_by_tile.py [--limit N] [--only ix_iy,...]
"""
import argparse
import html
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import requests
from PIL import Image
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent.parent
PLAYAREA = ROOT / "data" / "build" / "playarea.json"
EXISTING_RAW = ROOT / "data" / "raw" / "photos"
TILE_DIR = EXISTING_RAW / "tiles"
META_OUT = ROOT / "research" / "photos" / "by_tile.json"
TILE = 200.0
ORIGIN_E, ORIGIN_N = 2681400.0, 1248700.0
UA = "sandboxzurich/0.1 (research)"
HEADERS = {"User-Agent": UA, "Api-User-Agent": UA}
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
PANO_API = "https://api.panoramax.xyz/api/search"
PANO_PAGE = "https://panoramax.openstreetmap.fr/#focus=pic&pic="
MAX_PER_TILE = 3
MAX_PANO_FIRST = 2
COMMONS_PAUSE = 3.5
PANO_PAUSE = 1.0
MAX_SIDE = 1024
IMG_EXT = (".jpg", ".jpeg", ".png")

_to_wgs = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
_last = {"commons": 0.0, "pano": 0.0}


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def throttle(kind):
    pause = COMMONS_PAUSE if kind == "commons" else PANO_PAUSE
    wait = _last[kind] + pause - time.time()
    if wait > 0:
        time.sleep(wait)
    _last[kind] = time.time()


def get(kind, url, params=None, stream=False):
    """GET with throttle; on 429/5xx back off longer and retry."""
    delay = 60
    for attempt in range(5):
        throttle(kind)
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=60, stream=stream)
            if r.status_code == 200:
                return r
            log(f"  HTTP {r.status_code} {url[:60]} (attempt {attempt + 1})")
        except requests.RequestException as e:
            log(f"  request error {e} (attempt {attempt + 1})")
        if attempt < 4:
            time.sleep(delay)
            delay *= 2
    return None


def tile_bounds_wgs(ix, iy):
    """Return (lon0, lat0, lon1, lat1) of the tile and its centre (lon, lat)."""
    x0, y0 = ix * TILE, iy * TILE
    corners = [_to_wgs.transform(ORIGIN_E + x, ORIGIN_N + y)
               for x, y in [(x0, y0), (x0 + TILE, y0), (x0, y0 + TILE), (x0 + TILE, y0 + TILE)]]
    lons = [c[0] for c in corners]
    lats = [c[1] for c in corners]
    cx, cy = _to_wgs.transform(ORIGIN_E + x0 + TILE / 2, ORIGIN_N + y0 + TILE / 2)
    return min(lons), min(lats), max(lons), max(lats), (cx, cy)


def angle_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


def slug(s, n=50):
    s = re.sub(r"[^\w]+", "_", s, flags=re.UNICODE).strip("_")
    return s[:n] or "img"


def norm_name(s):
    s = re.sub(r"^File:", "", s)
    s = s.replace("_", " ").lower()
    return re.sub(r"\s+", " ", s).strip()


def existing_names():
    """Normalized basenames already on disk under data/raw/photos (outside tiles/)."""
    names = set()
    for p in EXISTING_RAW.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG_EXT and TILE_DIR not in p.parents:
            names.add(norm_name(p.name))
    # Titles already listed in research metadata
    for j in (ROOT / "research" / "photos").glob("*.json"):
        if j.name == "by_tile.json":
            continue
        for m in re.findall(r"File:[^\"\\]+", j.read_text(encoding="utf-8", errors="ignore")):
            names.add(norm_name(m))
    return names


def existing_pano_ids():
    ids = set()
    for j in (ROOT / "research" / "photos").glob("*.json"):
        ids.update(re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                              j.read_text(encoding="utf-8", errors="ignore")))
    return ids


def save_image(resp_content, dest):
    import io
    im = Image.open(io.BytesIO(resp_content))
    im = im.convert("RGB")
    if max(im.size) > MAX_SIDE:
        s = MAX_SIDE / max(im.size)
        im = im.resize((round(im.size[0] * s), round(im.size[1] * s)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=85, optimize=True)


def pano_candidates(lon0, lat0, lon1, lat1, centre):
    r = get("pano", PANO_API, {"bbox": f"{lon0:.6f},{lat0:.6f},{lon1:.6f},{lat1:.6f}", "limit": 50})
    if r is None:
        return []
    out = []
    for f in r.json().get("features", []):
        lon, lat = f["geometry"]["coordinates"]
        if not (lon0 <= lon <= lon1 and lat0 <= lat <= lat1):
            continue
        props = f.get("properties", {})
        sd = f.get("assets", {}).get("sd", {}).get("href") or f.get("assets", {}).get("hd", {}).get("href")
        if not sd:
            continue
        d = math.hypot((lon - centre[0]) * 71000, (lat - centre[1]) * 111000)
        out.append({"id": f["id"], "lon": lon, "lat": lat, "heading": props.get("view:azimuth"),
                    "license": props.get("license", ""), "author": props.get("geovisio:producer", ""),
                    "href": sd, "dist": d})
    out.sort(key=lambda c: c["dist"])
    return out


def pick_pano(cands, excluded):
    """Up to MAX_PANO_FIRST candidates with mutually distinct headings (>=60 deg)."""
    chosen = []
    for c in cands:
        if c["id"] in excluded:
            continue
        h = c["heading"]
        if h is None:
            if any(x["heading"] is None for x in chosen):
                continue
        elif any(x["heading"] is not None and angle_diff(h, x["heading"]) < 60 for x in chosen):
            continue
        chosen.append(c)
        if len(chosen) >= MAX_PANO_FIRST:
            break
    return chosen


def commons_candidates(cx, cy, excluded):
    r = get("commons", COMMONS_API, {"action": "query", "list": "geosearch",
                                     "gscoord": f"{cy:.6f}|{cx:.6f}", "gsradius": 142,
                                     "gsnamespace": 6, "gslimit": 30, "format": "json"})
    if r is None:
        return []
    hits = r.json().get("query", {}).get("geosearch", [])
    hits = [h for h in hits if h["title"].lower().endswith(IMG_EXT)
            and norm_name(h["title"]) not in excluded]
    hits.sort(key=lambda h: h["dist"])
    hits = hits[:10]
    if not hits:
        return []
    titles = "|".join(h["title"] for h in hits)
    r2 = get("commons", COMMONS_API, {"action": "query", "titles": titles, "prop": "imageinfo",
                                      "iiprop": "url|extmetadata", "iiurlwidth": MAX_SIDE,
                                      "format": "json"})
    if r2 is None:
        return []
    pages = r2.json().get("query", {}).get("pages", {})
    info = {}
    for p in pages.values():
        if p.get("imageinfo"):
            info[p["title"]] = (p["pageid"], p["imageinfo"][0])
    out = []
    for h in hits:
        if h["title"] not in info:
            continue
        pid, ii = info[h["title"]]
        meta = ii.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "") or "unbekannt"
        author = html.unescape(re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", ""))).strip()
        thumb = ii.get("thumburl") or ii.get("url")
        out.append({"id": str(pid), "title": h["title"], "lat": h["lat"], "lon": h["lon"],
                    "license": lic, "author": author or "unbekannt", "href": thumb,
                    "url": ii.get("descriptionurl", ""), "dist": h["dist"]})
    return out


def process_tile(ix, iy, state, seen_global, excluded_pano, excluded_titles):
    lon0, lat0, lon1, lat1, centre = tile_bounds_wgs(ix, iy)
    key = f"{ix}_{iy}"
    tile_dir = TILE_DIR / key
    cands = pano_candidates(lon0, lat0, lon1, lat1, centre)
    chosen_p = pick_pano(cands, excluded_pano)
    commons = commons_candidates(*centre, excluded_titles)
    chosen_c = commons[:MAX_PER_TILE - len(chosen_p)]
    if len(chosen_p) + len(chosen_c) < MAX_PER_TILE:
        rest = [c for c in cands if c["id"] not in {x["id"] for x in chosen_p}
                and c["id"] not in excluded_pano]
        chosen_p += rest[:MAX_PER_TILE - len(chosen_p) - len(chosen_c)]

    entries = []
    for c in chosen_p:
        k = "pano:" + c["id"]
        if k in seen_global:
            entries.append(dict(seen_global[k]))
            continue
        dest = tile_dir / f"pano_{slug(c['id'], 36)}.jpg"
        if not dest.exists():
            r = get("pano", c["href"])
            if r is None:
                continue
            save_image(r.content, dest)
        e = {"file": str(dest.relative_to(ROOT)), "source": "panoramax", "license": c["license"],
             "author": c["author"], "url": PANO_PAGE + c["id"], "lat": round(c["lat"], 7),
             "lon": round(c["lon"], 7)}
        if c["heading"] is not None:
            e["heading"] = c["heading"]
        entries.append(e)
        seen_global[k] = e

    for c in chosen_c:
        k = "commons:" + c["title"]
        if k in seen_global:
            entries.append(dict(seen_global[k]))
            continue
        dest = tile_dir / f"commons_{c['id']}_{slug(re.sub(r'^File:', '', c['title']).rsplit('.', 1)[0], 40)}.jpg"
        if not dest.exists():
            r = get("commons", c["href"])
            if r is None:
                continue
            save_image(r.content, dest)
        e = {"file": str(dest.relative_to(ROOT)), "source": "commons", "license": c["license"],
             "author": c["author"], "url": c["url"], "lat": round(c["lat"], 7),
             "lon": round(c["lon"], 7), "title": c["title"]}
        entries.append(e)
        seen_global[k] = e

    state[key] = entries
    return entries


def save_meta(state):
    META_OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = META_OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, META_OUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    args = ap.parse_args()

    # tiles may carry a third flag column (current playarea.json); only ix, iy matter here
    tiles = [(t[0], t[1]) for t in json.loads(PLAYAREA.read_text())["tiles"]]
    if args.only:
        wanted = set(args.only.split(","))
        tiles = [t for t in tiles if f"{t[0]}_{t[1]}" in wanted]
    state = json.loads(META_OUT.read_text()) if META_OUT.exists() else {}
    todo = [t for t in tiles if f"{t[0]}_{t[1]}" not in state]
    if args.limit:
        todo = todo[:args.limit]
    log(f"tiles total {len(tiles)}, done {len(tiles) - len(todo)}, todo {len(todo)}")

    excluded_titles = existing_names()
    excluded_pano = existing_pano_ids()
    seen_global = {}
    for entries in state.values():
        for e in entries:
            if e["source"] == "panoramax":
                seen_global["pano:" + e["url"].split("pic=")[-1]] = e
            else:
                seen_global["commons:" + e["title"]] = e

    for n, (ix, iy) in enumerate(todo, 1):
        try:
            entries = process_tile(ix, iy, state, seen_global, excluded_pano, excluded_titles)
        except Exception as ex:  # keep the run alive; tile is retried on next start
            log(f"tile {ix}_{iy} failed: {ex!r}")
            continue
        save_meta(state)
        log(f"[{n}/{len(todo)}] {ix}_{iy}: {len(entries)} photos "
            f"({sum(e['source'] == 'commons' for e in entries)} commons, "
            f"{sum(e['source'] == 'panoramax' for e in entries)} panoramax)")

    covered = sum(1 for v in state.values() if v)
    log(f"done. tiles with >=1 photo: {covered}/{len(tiles)}")


if __name__ == "__main__":
    sys.exit(main())
