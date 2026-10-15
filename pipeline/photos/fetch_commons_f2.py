#!/usr/bin/env python3
"""F2: Referenzfotos Velos und Stadtmobiliar aus Wikimedia Commons (API via requests).

Usage:
  fetch_commons_f2.py bikes|furniture        # Suche, Download, JSON, Kontaktbogen
  fetch_commons_f2.py bikes --set-keywords '{"1": "Seilleuchte", ...}'

Schreibt:
  data/raw/photos/<topic>/<pageid>_<name>.<ext>   (Thumbnail, Breite 1024)
  research/photos/<topic>.json                    (Metadaten, Lizenz, Stichwort)
  preview/ref_<topic>.jpg                         (Kontaktbogen, 200 px Thumbs)
"""
import datetime
import html
import json
import math
import os
import re
import sys
import time

import requests
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
API = "https://commons.wikimedia.org/w/api.php"
UA = "sandboxzurich/0.1 (research)"
HDR = {"User-Agent": UA}
THUMB_W = 1024
CELL = 200
COLS = 8
PER_SOURCE = 30
ALLOWED_MIME = {"image/jpeg", "image/png"}

TOPICS = {
    "bikes": {
        "cap": 80,
        "categories": [
            "Bicycles in Zürich", "Bicycle parking in Zürich", "Cargo bikes in Switzerland",
            "Publibike", "Bicycle racks in Zürich", "Bicycles in Switzerland",
        ],
        "searches": [
            "Bicycles in Zürich", "Bicycle parking in Zürich", "Cargo bikes in Switzerland",
            "Publibike", "Velo Zürich", "Bicycle racks Zürich", "Bicycle racks Switzerland",
            "child seat bicycle", "bicycle basket", "e-bike Zürich", "Dutch bicycle",
            "city bicycle", "road bicycle",
        ],
    },
    "furniture": {
        "cap": 120,
        "categories": [
            "Street lights in Zürich", "Benches in Zürich", "Waste containers in Zürich",
            "Fountains in Zürich", "Fire hydrants in Switzerland", "Street signs in Zürich",
            "Bollards in Zürich", "Advertising columns in Zürich", "Glass recycling containers in Zürich",
        ],
        "searches": [
            "Seilleuchte Zürich", "Street lights in Zürich", "Kandelaber Zürich",
            "Waste containers in Zürich", "Züri-Kübel", "Brunnen der Stadt Zürich",
            "Fountains in Zürich", "Benches in Zürich", "Fire hydrants in Switzerland",
            "Litfasssäule Zürich", "Advertising columns Zürich", "Street signs in Zürich",
            "House numbers Zürich", "Bollards Zürich", "Glass container Zürich", "Robidog",
        ],
    },
}


def api(params):
    """GET against the Commons API with retries."""
    p = {"format": "json", "formatversion": 2, "action": "query", **params}
    err = None
    time.sleep(1.5)  # gentle pacing: Commons answers 429 on bursts
    for attempt in range(5):
        try:
            r = requests.get(API, params=p, headers=HDR, timeout=30)
            if r.status_code == 429:
                err = r.status_code
                time.sleep(20 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001 - retry on any transport error
            err = e
            time.sleep(3 + 3 * attempt)
    raise RuntimeError(f"API failed: {err}")


def collect(gen_params, limit):
    """Yield pages from a generator query, following 'continue' up to the end."""
    base = {
        "prop": "imageinfo|categories",
        "iiprop": "url|extmetadata|mime|size",
        "iiurlwidth": THUMB_W,
        "cllimit": "max",
    }
    cont = {}
    n = 0
    while True:
        data = api({**gen_params, **base, **cont})
        for page in data.get("query", {}).get("pages", []):
            yield page
            n += 1
            if n >= limit:
                return
        if "continue" not in data:
            return
        cont = data["continue"]
        time.sleep(0.3)


def meta(ext, key):
    raw = (ext or {}).get(key, {}).get("value", "") or ""
    return html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()


def safe_name(title):
    base = os.path.splitext(title[len("File:"):] if title.startswith("File:") else title)[0]
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("_")
    return base[:80] or "img"


def candidates(cfg, cache):
    """Collect unique image pages from categories and searches, in priority order."""
    if os.path.exists(cache):  # reuse earlier API results instead of querying again
        with open(cache, encoding="utf-8") as f:
            return json.load(f)
    seen = {}
    sources = [("cat", c) for c in cfg["categories"]] + [("search", s) for s in cfg["searches"]]
    for kind, term in sources:
        if len(seen) >= cfg["cap"]:
            break
        if kind == "cat":
            gen = {"generator": "categorymembers", "gcmtitle": f"Category:{term}",
                   "gcmtype": "file", "gcmlimit": PER_SOURCE}
        else:
            gen = {"generator": "search", "gsrsearch": f"filetype:bitmap {term}",
                   "gsrnamespace": 6, "gsrlimit": PER_SOURCE}
        taken = 0
        try:
            pages = list(collect(gen, limit=PER_SOURCE))
        except RuntimeError as e:
            print(f"  {kind:6} {term!r}: skipped ({e})", flush=True)
            continue
        for page in pages:
            if taken >= PER_SOURCE or len(seen) >= cfg["cap"]:
                break
            ii = (page.get("imageinfo") or [{}])[0]
            title = page.get("title", "")
            if page.get("missing") or not ii or ii.get("mime") not in ALLOWED_MIME:
                continue
            if page["pageid"] in seen:
                continue
            ext = ii.get("extmetadata")
            seen[page["pageid"]] = {
                "pageid": page["pageid"],
                "title": title,
                "page_url": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
                "author": meta(ext, "Artist") or meta(ext, "Credit"),
                "license": meta(ext, "LicenseShortName"),
                "license_url": meta(ext, "LicenseUrl"),
                "description": meta(ext, "ImageDescription")[:300],
                "categories": [c["title"].replace("Category:", "")
                               for c in page.get("categories", [])][:10],
                "query": f"{kind}:{term}",
                "thumb_url": ii.get("thumburl") or ii.get("url"),
                "width": ii.get("thumbwidth") or ii.get("width"),
                "height": ii.get("thumbheight") or ii.get("height"),
                "mime": ii.get("mime"),
                "keyword": None,
                "_ext": os.path.splitext(title)[1].lower(),
            }
            taken += 1
        print(f"  {kind:6} {term!r}: total {len(seen)}", flush=True)
    result = list(seen.values())
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    return result


def download(url, path):
    for attempt in range(4):
        try:
            r = requests.get(url, headers=HDR, timeout=60)
            if r.status_code == 429:
                time.sleep(5 + 5 * attempt)
                continue
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            return True
        except Exception:  # noqa: BLE001
            time.sleep(2 + 2 * attempt)
    return False


def fetch(topic):
    cfg = TOPICS[topic]
    img_dir = os.path.join(ROOT, "data/raw/photos", topic)
    os.makedirs(img_dir, exist_ok=True)
    cands = candidates(cfg, os.path.join(img_dir, "_candidates.json"))
    print(f"candidates: {len(cands)}", flush=True)

    items, failed = [], 0
    for c in cands:
        if len(items) >= cfg["cap"]:
            break
        ext = c["_ext"] if c["_ext"] in (".jpg", ".jpeg", ".png") else ".jpg"
        local = os.path.join(img_dir, f"{c['pageid']}_{safe_name(c['title'])}{ext}")
        if not os.path.exists(local) and not download(c["thumb_url"], local):
            failed += 1
            continue
        c.pop("_ext")
        c.pop("thumb_url")
        c["local"] = os.path.relpath(local, ROOT)
        c["no"] = len(items) + 1
        items.append(c)
        time.sleep(0.2)
    print(f"downloaded: {len(items)} (failed {failed})", flush=True)

    out_json = os.path.join(ROOT, "research/photos", f"{topic}.json")
    keep = {}
    if os.path.exists(out_json):  # keep manual keywords across reruns
        with open(out_json, encoding="utf-8") as f:
            keep = {i["pageid"]: i.get("keyword") for i in json.load(f).get("items", [])}
    for it in items:
        it["keyword"] = keep.get(it["pageid"]) or it["keyword"]
    doc = {
        "topic": topic,
        "source": "Wikimedia Commons API (commons.wikimedia.org/w/api.php)",
        "user_agent": UA,
        "fetched": datetime.date.today().isoformat(),
        "count": len(items),
        "thumb_width": THUMB_W,
        "items": items,
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    make_sheet(topic, items)
    print(f"wrote {os.path.relpath(out_json, ROOT)} and preview/ref_{topic}.jpg", flush=True)


def make_sheet(topic, items):
    rows = max(1, math.ceil(len(items) / COLS))
    sheet = Image.new("RGB", (COLS * CELL, rows * CELL), "white")
    draw = ImageDraw.Draw(sheet)
    for i, it in enumerate(items):
        x, y = (i % COLS) * CELL, (i // COLS) * CELL
        try:
            im = Image.open(os.path.join(ROOT, it["local"])).convert("RGB")
            im.thumbnail((CELL - 4, CELL - 4))
            sheet.paste(im, (x + (CELL - im.width) // 2, y + (CELL - im.height) // 2))
        except Exception:  # noqa: BLE001 - unreadable file: leave cell blank
            pass
        draw.rectangle([x, y, x + 26, y + 16], fill="black")
        draw.text((x + 3, y + 2), str(it["no"]), fill="white")
    sheet.save(os.path.join(ROOT, "preview", f"ref_{topic}.jpg"), quality=85)


def set_keywords(topic, mapping):
    out_json = os.path.join(ROOT, "research/photos", f"{topic}.json")
    with open(out_json, encoding="utf-8") as f:
        doc = json.load(f)
    n = 0
    for it in doc["items"]:
        kw = mapping.get(str(it["no"]))
        if kw:
            it["keyword"] = kw
            n += 1
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f"keywords set: {n}/{len(doc['items'])}")


def main(argv):
    if len(argv) < 2 or argv[1] not in TOPICS:
        print(__doc__)
        return 1
    topic = argv[1]
    if "--set-keywords" in argv:
        set_keywords(topic, json.loads(argv[argv.index("--set-keywords") + 1]))
    else:
        fetch(topic)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
