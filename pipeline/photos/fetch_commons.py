"""Fetch reference photos from Wikimedia Commons (and optionally Panoramax).

Usage:
  python fetch_commons.py --categories "Langstrasse (Zürich)|Helvetiaplatz (Zürich)" \
      --out data/raw/photos/streetscape --meta research/photos/streetscape.json \
      --max 150 --min-year 2015 [--panoramax]

Writes 1280 px thumbnails into --out (one subfolder per category) and a JSON
file with title, URL, author, license, category, date per image.
Keyword fields ("tag") are added later by hand in the JSON.
"""
import argparse
import json
import os
import re
import sys
import time

import requests

API = "https://commons.wikimedia.org/w/api.php"
PANORAMAX_API = "https://api.panoramax.xyz/api/search"
UA = "gtazurich/0.1 (research)"
HEADERS = {"User-Agent": UA, "Api-User-Agent": UA}
THUMB_WIDTH = 1280
PANORAMAX_BBOX = "8.518,47.372,8.535,47.385"  # Kreis 4/5 core area


def get(url, params=None, retries=5):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                return r
            print(f"  HTTP {r.status_code} for {url}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"  request error: {e}", file=sys.stderr)
        # Wikimedia answers 429 when hammered: back off hard.
        time.sleep(8 * (attempt + 1))
    return None


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def slugify(s):
    s = s.replace("Category:", "")
    s = re.sub(r"[^\w]+", "_", s, flags=re.UNICODE).strip("_")
    return s[:60] or "cat"


def subcategories(cat, depth):
    """Return [cat] plus its subcategories down to `depth` levels."""
    result = [cat]
    frontier = [cat]
    for _ in range(depth):
        nxt = []
        for c in frontier:
            cont = {}
            while True:
                params = {"action": "query", "list": "categorymembers", "cmtitle": c,
                          "cmtype": "subcat", "cmlimit": 500, "format": "json", **cont}
                r = get(API, params)
                if r is None:
                    break
                data = r.json()
                for m in data.get("query", {}).get("categorymembers", []):
                    nxt.append(m["title"])
                if "continue" not in data:
                    break
                cont = data["continue"]
            time.sleep(0.2)
        frontier = nxt
        result += nxt
    return list(dict.fromkeys(result))


def category_files(cat):
    """Yield (title, imageinfo) for image files in a category, with 1280 px thumb URL."""
    cont = {}
    while True:
        params = {"action": "query", "generator": "categorymembers",
                  "gcmtitle": cat, "gcmtype": "file", "gcmlimit": 50,
                  "prop": "imageinfo",
                  "iiprop": "url|extmetadata|mime|size",
                  "iiurlwidth": THUMB_WIDTH, "format": "json", **cont}
        r = get(API, params)
        if r is None:
            return
        data = r.json()
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [None])[0]
            if info:
                yield page["title"], info
        if "continue" not in data:
            return
        cont = data["continue"]


def year_of(meta):
    for key in ("DateTimeOriginal", "DateTime", "DateTimeDigitized"):
        val = strip_html(meta.get(key, {}).get("value", ""))
        m = re.match(r"(\d{4})", val)
        if m:
            return int(m.group(1)), val
    d = strip_html(meta.get("DateTime", {}).get("value", ""))
    return None, d


def record_from_commons(title, info, cat):
    meta = info.get("extmetadata", {})
    year, date_raw = year_of(meta)
    license_short = strip_html(meta.get("LicenseShortName", {}).get("value", ""))
    return {
        "source": "commons",
        "title": title,
        "page_url": info.get("descriptionurl"),
        "thumb_url": info.get("thumburl"),
        "thumb_width": info.get("thumbwidth"),
        "thumb_height": info.get("thumbheight"),
        "author": strip_html(meta.get("Artist", {}).get("value", "")),
        "license": license_short,
        "license_url": meta.get("LicenseUrl", {}).get("value", ""),
        "attribution_required": meta.get("AttributionRequired", {}).get("value", ""),
        "description": strip_html(meta.get("ImageDescription", {}).get("value", ""))[:300],
        "category": cat,
        "date": date_raw,
        "year": year,
        "tag": "",
    }


def panoramax_records(limit):
    params = {"bbox": PANORAMAX_BBOX, "limit": limit}
    r = get(PANORAMAX_API, params)
    if r is None:
        return []
    out = []
    for f in r.json().get("features", []):
        props = f.get("properties", {})
        assets = f.get("assets", {})
        thumb = (assets.get("thumb") or assets.get("sd") or assets.get("hd") or {}).get("href")
        if not thumb:
            continue
        year = None
        dt = props.get("datetime", "")
        m = re.match(r"(\d{4})", dt or "")
        if m:
            year = int(m.group(1))
        out.append({
            "source": "panoramax",
            "title": f.get("id"),
            "page_url": f.get("links", [{}])[0].get("href", ""),
            "thumb_url": thumb,
            "author": props.get("geovisio:producer", ""),
            "license": props.get("license", ""),
            "license_url": "",
            "attribution_required": "",
            "description": "",
            "category": "panoramax:bbox",
            "date": dt,
            "year": year,
            "tag": "",
        })
    return out


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    r = get(url)
    if r is None:
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(r.content)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", required=True, help="pipe-separated category names")
    ap.add_argument("--out", required=True)
    ap.add_argument("--meta", required=True, help="output JSON path")
    ap.add_argument("--max", type=int, default=150)
    ap.add_argument("--min-year", type=int, default=2015)
    ap.add_argument("--depth", type=int, default=1, help="subcategory levels")
    ap.add_argument("--panoramax", action="store_true")
    ap.add_argument("--per-cat", type=int, default=0, help="cap per category (0 = none)")
    args = ap.parse_args()

    cats = []
    for c in args.categories.split("|"):
        c = c.strip()
        if not c:
            continue
        if not c.startswith("Category:"):
            c = "Category:" + c
        cats.append(c)

    # Collect candidates; dedupe by file title.
    seen = {}
    for cat in cats:
        allc = subcategories(cat, args.depth)
        print(f"{cat}: {len(allc)} categories incl. subcats", file=sys.stderr)
        for sc in allc:
            n = 0
            for title, info in category_files(sc):
                if title in seen:
                    continue
                if info.get("mime") not in ("image/jpeg", "image/png"):
                    continue
                if not info.get("thumburl"):
                    continue
                rec = record_from_commons(title, info, sc.replace("Category:", ""))
                seen[title] = rec
                n += 1
                if args.per_cat and n >= args.per_cat:
                    break
            time.sleep(0.5)
        print(f"  candidates so far: {len(seen)}", file=sys.stderr)

    recs = list(seen.values())
    pano_slots = 20 if args.panoramax else 0
    # Prefer photos from min-year on; fill with older only if needed.
    recent = [r for r in recs if r["year"] and r["year"] >= args.min_year]
    older = [r for r in recs if not (r["year"] and r["year"] >= args.min_year)]
    recent.sort(key=lambda r: (-(r["year"] or 0), r["title"]))
    older.sort(key=lambda r: r["title"])
    chosen = (recent + older)[: args.max - pano_slots]
    print(f"candidates={len(recs)} recent(>={args.min_year})={len(recent)} chosen={len(chosen)}",
          file=sys.stderr)

    if args.panoramax:
        pano = panoramax_records(50)
        print(f"panoramax features: {len(pano)}", file=sys.stderr)
        chosen += pano[: max(0, args.max - len(chosen))]
        print(f"panoramax added: {min(len(pano), args.max - len(chosen))}", file=sys.stderr)

    # Download thumbnails.
    for i, rec in enumerate(chosen, 1):
        ext = ".png" if rec["thumb_url"].lower().endswith(".png") else ".jpg"
        sub = slugify(rec["category"]) if rec["source"] == "commons" else "panoramax"
        fname = f"{i:03d}_{slugify(rec['title'].split(':', 1)[-1])[:50]}{ext}"
        dest = os.path.join(args.out, sub, fname)
        ok = download(rec["thumb_url"], dest)
        rec["index"] = i
        rec["local_path"] = os.path.relpath(dest) if ok else None
        rec["ok"] = ok
        if i % 20 == 0:
            print(f"  downloaded {i}/{len(chosen)}", file=sys.stderr)
        time.sleep(0.3)

    chosen = [r for r in chosen if r["ok"]]
    for i, r in enumerate(chosen, 1):
        r["index"] = i
    os.makedirs(os.path.dirname(args.meta), exist_ok=True)
    with open(args.meta, "w", encoding="utf-8") as f:
        json.dump({"categories": cats, "min_year": args.min_year, "count": len(chosen),
                   "images": chosen}, f, ensure_ascii=False, indent=1)
    print(f"wrote {len(chosen)} records to {args.meta}", file=sys.stderr)


if __name__ == "__main__":
    main()
