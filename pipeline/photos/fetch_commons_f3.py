#!/usr/bin/env python3
"""F3: Referenzfotos ÖV und Strassenmarkierungen aus Wikimedia Commons.

Ablauf (zwei Schritte, reproduzierbar):
  1. fetch KIND  - Commons-Suche, Metadaten, Thumbnails (1024 px) nach
                   data/raw/photos/KIND/, Kandidatenliste nach
                   research/photos/KIND.json, Kontaktbogen nach preview/ref_KIND.jpg
  2. label KIND  - manuelle Sichtung (LABELS unten: Nummer -> Stichwort,
                   leer = verwerfen). Schreibt die finale Liste in
                   research/photos/KIND.json.

Nur Commons-Suche per API, keine Websuche, keine Google-Bilder.
"""
import argparse
import datetime
import html
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
API = "https://commons.wikimedia.org/w/api.php"
UA = "gtazurich/0.1 (research)"
HEADERS = {"User-Agent": UA}
THUMB_W = 1024
SHEET_CELL = 200
SHEET_COLS = 8
CELL_H = 150
CAP_H = 24

TOPICS = {
    "transit": {
        "max": 100,
        "queries": [
            "Be 5/6 Flexity Zürich", "Flexity Zürich tram", "Be 5/6 Cobra Zürich",
            "Cobra tram Zürich", "Tram 2000 Zürich", "Trolleybuses in Zürich",
            "VBZ tram stop", "Tram stops in Zürich", "Overhead lines in Zürich",
            "Tram tracks in Zürich", "Helvetiaplatz tram Zürich", "Linie 8 Zürich tram",
            "Bus 31 Zürich", "Bus 32 Zürich",
        ],
    },
    "roads": {
        "max": 70,
        "queries": [
            "Road markings in Switzerland", "Bicycle lanes in Zürich",
            "Pedestrian crossings in Switzerland yellow", "Bus lanes in Switzerland",
            "Blue zone parking Zürich", "Manhole covers Zürich", "Kerb Zürich",
            "Velostreifen Zürich", "Bicycle pictogram road marking Zürich",
            "Zebra crossing Zürich",
        ],
    },
}

# Manuelle Sichtung nach dem Kontaktbogen: Kandidaten-Nummer -> Stichwort.
# Leerer String = verwerfen (nicht passend). Nicht gelistete Nummern fallen weg.
LABELS = {
    "transit": {},
    "roads": {},
}


def api_get(params):
    payload = {"format": "json", "formatversion": 2, "action": "query", **params}
    for attempt in range(5):
        try:
            r = requests.get(API, params=payload, headers=HEADERS, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                print(f"  HTTP {r.status_code}, Pause", file=sys.stderr)
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            print(f"  API-Fehler ({exc}), neuer Versuch", file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise SystemExit("Commons API nicht erreichbar")


def search(query, limit=30):
    data = api_get({
        "generator": "search", "gsrsearch": f"{query} filetype:bitmap", "gsrnamespace": 6,
        "gsrlimit": limit, "prop": "imageinfo|categories",
        "iiprop": "url|size|mime|extmetadata", "iiurlwidth": THUMB_W,
        "cllimit": "max", "clprop": "hidden",
    })
    time.sleep(1.0)
    return data.get("query", {}).get("pages", [])


def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def to_item(page, query):
    infos = page.get("imageinfo") or []
    if not infos:
        return None
    ii = infos[0]
    if ii.get("mime") not in ("image/jpeg", "image/png") or not ii.get("thumburl"):
        return None
    ext = ii.get("extmetadata", {})

    def val(key):
        return ext.get(key, {}).get("value")

    cats = [c["title"].removeprefix("Category:") for c in page.get("categories", [])
            if not c.get("hidden")]
    return {
        "file": page["title"],
        "title": page["title"].removeprefix("File:"),
        "url": ii.get("descriptionurl"),
        "thumb_url": ii["thumburl"],
        "width": ii.get("thumbwidth"),
        "height": ii.get("thumbheight"),
        "author": strip_html(val("Artist")),
        "license": val("LicenseShortName"),
        "license_url": val("LicenseUrl"),
        "date": val("DateTimeOriginal"),
        "description": strip_html(val("ImageDescription"))[:200],
        "categories": cats[:8],
        "query": query,
    }


def download(url, dest):
    """curl mit hartem Zeitlimit: requests hing bei einzelnen Wikimedia-Verbindungen."""
    if dest.exists() and dest.stat().st_size > 0:
        return True
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(5):
        res = subprocess.run(
            ["curl", "-sS", "-L", "--fail", "--max-time", "120", "-A", UA, "-o", str(tmp), url],
            capture_output=True, text=True,
        )
        if res.returncode == 0 and tmp.exists() and tmp.stat().st_size > 0:
            tmp.replace(dest)
            time.sleep(4.0)
            return True
        print(f"  Download-Versuch {attempt + 1} fehlgeschlagen: {res.stderr.strip()[:120]}", file=sys.stderr)
        time.sleep(60 * (attempt + 1))
    return False


def contact_sheet(items, out):
    font = ImageFont.load_default(size=12)
    rows = -(-len(items) // SHEET_COLS)
    row_h = CELL_H + CAP_H
    sheet = Image.new("RGB", (SHEET_COLS * SHEET_CELL, rows * row_h), (240, 240, 240))
    draw = ImageDraw.Draw(sheet)
    for i, it in enumerate(items):
        x = (i % SHEET_COLS) * SHEET_CELL
        y = (i // SHEET_COLS) * row_h
        try:
            im = Image.open(ROOT / it["local"]).convert("RGB")
            im.thumbnail((SHEET_CELL - 6, CELL_H))
            sheet.paste(im, (x + 3 + (SHEET_CELL - 6 - im.width) // 2,
                             y + (CELL_H - im.height) // 2))
        except OSError:
            pass
        draw.rectangle([x, y + CELL_H, x + SHEET_CELL - 1, y + row_h - 1], fill=(30, 30, 30))
        draw.text((x + 4, y + CELL_H + 5), f"{it['n']} {it['title'][:30]}",
                  fill=(255, 255, 255), font=font)
    sheet.save(out, quality=85)


def cmd_fetch(kind):
    cfg = TOPICS[kind]
    cand = {}
    for q in cfg["queries"]:
        pages = search(q)
        new = 0
        for page in pages:
            item = to_item(page, q)
            if item and item["file"] not in cand:
                cand[item["file"]] = item
                new += 1
        print(f"[{kind}] {q}: {len(pages)} Treffer, {new} neu")
    # Kandidaten begrenzen, damit der Download klein bleibt
    items = list(cand.values())[: int(cfg["max"] * 1.5)]
    out_dir = ROOT / "data/raw/photos" / kind
    out_dir.mkdir(parents=True, exist_ok=True)
    kept = []
    for n, it in enumerate(items, start=1):
        it["n"] = n
        dest = out_dir / re.sub(r"[^A-Za-z0-9._-]+", "_", it["title"])[:150]
        it["local"] = str(dest.relative_to(ROOT))
        if download(it["thumb_url"], dest):
            kept.append(it)
        else:
            print(f"  Download fehlgeschlagen: {it['file']}", file=sys.stderr)
    write_json(kind, kept, stage="candidates")
    (ROOT / "preview").mkdir(exist_ok=True)
    contact_sheet(kept, ROOT / "preview" / f"ref_{kind}.jpg")
    print(f"[{kind}] Kandidaten: {len(kept)} (Ziel {cfg['max']}-Obergrenze)")


def cmd_label(kind):
    src = ROOT / "research/photos" / f"{kind}.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    labels = LABELS[kind]
    final = []
    for it in data["items"]:
        kw = labels.get(it["n"])
        if not kw:
            continue
        it["keyword"] = kw
        final.append(it)
    write_json(kind, final, stage="final")
    print(f"[{kind}] final: {len(final)} (Ziel {TOPICS[kind]['max']}-Obergrenze)")


def write_json(kind, items, stage):
    path = ROOT / "research/photos" / f"{kind}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "kind": kind,
        "stage": stage,
        "source": "Wikimedia Commons (API, commons.wikimedia.org)",
        "user_agent": UA,
        "thumb_width": THUMB_W,
        "generated": datetime.date.today().isoformat(),
        "count": len(items),
        "items": items,
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["fetch", "label"])
    ap.add_argument("kind", choices=sorted(TOPICS))
    args = ap.parse_args()
    if args.step == "fetch":
        cmd_fetch(args.kind)
    else:
        cmd_label(args.kind)


if __name__ == "__main__":
    main()
