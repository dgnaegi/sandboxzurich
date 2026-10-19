"""Mapillary map features (traffic signs + a few street-furniture counts) for zones 4 and 1.

Usage:
  python3 pipeline/mapillary_features.py fetch [--zones 4,1]   # Graph API map_features, cached per cell in data/raw/mapillary_features/
  python3 pipeline/mapillary_features.py build                 # classes -> SSV codes -> pipeline/overrides/mly_signs.json
Token MAPILLARY_TOKEN in .env. Data licence CC BY-SA 4.0 (see docs/DATA_SOURCES.md). Local metres: x east, y north,
origin LV95 2681400/1248700.
"""
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

import requests
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "raw" / "mapillary_features"
OUT = ROOT / "pipeline" / "overrides" / "mly_signs.json"
LOG = ROOT / "logs" / "mapillary_features.log"
OX, OY = 2681400.0, 1248700.0
URL = "https://graph.mapillary.com/map_features"
FIELDS = "id,object_value,geometry,first_seen_at,last_seen_at,aligned_direction,images"
CELL = 125.0
PREFIX = ("regulatory--", "warning--", "information--", "complementary--")
COUNT_ONLY = ("object--street-light", "object--bench", "object--fire-hydrant", "object--traffic-light")
_to_wgs = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
_to_lv = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)


def log(m):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a") as f:
        f.write(time.strftime("%H:%M:%S ") + m + "\n")


def token():
    return re.search(r"MAPILLARY_TOKEN=(.*)", (ROOT / ".env").read_text()).group(1).strip().strip("\"'")


def zone_bbox(zid):
    z = [q for q in json.load(open(ROOT / "pipeline/overrides/zones.json"))["zones"] if str(q["id"]) == str(zid)][0]
    pts = [p for pl in z["polys"] for p in pl]
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def fetch_cell(tok, x0, y0, x1, y1, depth=0):
    lo0, la0 = _to_wgs.transform(OX + x0, OY + y0)
    lo1, la1 = _to_wgs.transform(OX + x1, OY + y1)
    rows, params = [], {"access_token": tok, "fields": FIELDS, "limit": 500, "bbox": f"{lo0},{la0},{lo1},{la1}"}
    url = URL
    while url:
        for tries in range(4):
            r = requests.get(url, params=params, timeout=90, headers={"User-Agent": "sandboxzurich/0.1 (research)"})
            if r.status_code == 200:
                break
            if r.status_code in (400, 500) and depth < 4 and "reduce" in r.text:
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                out = []
                for a, b, c, d in ((x0, y0, mx, my), (mx, y0, x1, my), (x0, my, mx, y1), (mx, my, x1, y1)):
                    out += fetch_cell(tok, a, b, c, d, depth + 1)
                return out
            log(f"  http {r.status_code} {r.text[:120]}")
            time.sleep(5 * (tries + 1))
        else:
            raise RuntimeError("fetch failed")
        j = r.json()
        rows += j.get("data", [])
        url = j.get("paging", {}).get("next")
        params = None
        time.sleep(0.4)
    return rows


def fetch(zones):
    tok = token()
    CACHE.mkdir(parents=True, exist_ok=True)
    for zid in zones:
        bx0, by0, bx1, by1 = zone_bbox(zid)
        nx, ny = math.ceil((bx1 - bx0) / CELL), math.ceil((by1 - by0) / CELL)
        log(f"zone {zid}: bbox {bx0:.0f},{by0:.0f},{bx1:.0f},{by1:.0f} cells {nx}x{ny}")
        for i in range(nx):
            for j in range(ny):
                f = CACHE / f"c125_z{zid}_{i}_{j}.json"
                if f.exists():
                    continue
                x0, y0 = bx0 + i * CELL, by0 + j * CELL
                rows = fetch_cell(tok, x0, y0, x0 + CELL, y0 + CELL)
                f.write_text(json.dumps(rows))
                log(f"  z{zid} cell {i},{j}: {len(rows)} features")
    log("fetch done")


def load_all():
    feats = {}
    for f in sorted(CACHE.glob("*.json")):
        for r in json.load(open(f)):
            feats[r["id"]] = r
    return list(feats.values())


def local(r):
    lo, la = r["geometry"]["coordinates"]
    e, n = _to_lv.transform(lo, la)
    return e - OX, n - OY



# Mapillary class (prefix match, first hit wins) -> SSV code of pipeline/traffic_signs.py / web trafficsigns.ts textures
CLASS2CODE = [
    ("regulatory--maximum-speed-limit-30", "speed30"), ("regulatory--maximum-speed-limit-50", "speed50"),
    ("regulatory--speed-limit-zone", "zone30"), ("regulatory--end-of-speed-limit-zone", "zone30end"),
    ("regulatory--stop--", "stop"), ("regulatory--yield--", "vortritt"),
    ("regulatory--one-way-", "einbahn"), ("regulatory--no-entry--", "einfahrt_verboten"),
    ("regulatory--road-closed-to-vehicles", "fahrverbot"), ("regulatory--no-motor-vehicles", "fahrverbot"),
    ("regulatory--pedestrians-only", "fussweg"), ("regulatory--bicycles-only", "radweg"),
    ("regulatory--no-parking", "halteverbot"), ("regulatory--no-stopping", "halteverbot"),
    ("information--pedestrians-crossing", "fussgaenger"), ("information--parking", "parkieren"),
    ("information--dead-end", "sackgasse"),
]
MIN_IMAGES, MIN_YEAR = 2, 2022


def code_of(cls):
    for pre, code in CLASS2CODE:
        if cls.startswith(pre):
            return code
    return None


def zone_polys(zids):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    zs = json.load(open(ROOT / "pipeline/overrides/zones.json"))["zones"]
    return unary_union([Polygon(pl) for q in zs if str(q["id"]) in zids for pl in q["polys"]])


def build(zids=("4", "1")):
    from shapely.geometry import Point
    poly = zone_polys(zids)
    allf = load_all()
    cnt, kept, rows, other, old = Counter(), Counter(), [], Counter(), Counter()
    for r in allf:
        v = r["object_value"]
        x, y = local(r)
        if not poly.contains(Point(x, y)):
            continue
        if v.startswith(COUNT_ONLY):
            cnt["count:" + v.split("--")[1]] += 1
            continue
        if not v.startswith(PREFIX):
            continue
        t = v.split("--")[0]
        cnt[t] += 1
        n_img = len(r.get("images", {}).get("data", []))
        year = int(r.get("last_seen_at", "0")[:4] or 0)
        if n_img < MIN_IMAGES:
            cnt["dropped(<2 img)"] += 1
            continue
        if year < MIN_YEAR:
            cnt["dropped(last_seen<2022)"] += 1
            old[code_of(v) or "-"] += 1
            continue
        code = code_of(v)
        if not code:
            other[v] += 1
            continue
        kept[code] += 1
        rows.append({"x": round(x, 2), "y": round(y, 2), "code": code, "cls": v, "dir": r.get("aligned_direction"),
                     "n": n_img, "seen": r["last_seen_at"][:10], "id": r["id"]})
    sys.path.insert(0, str(ROOT / "pipeline"))
    import traffic_signs as TS
    ways = []
    for z in zids:
        ways += TS._load(zone_bbox(z))[1]
    for r in rows:
        r["h"] = round(heading_of(r, ways), 3)
    OUT.write_text(json.dumps({"licence": "Mapillary map features, CC BY-SA 4.0", "zones": list(zids), "signs": rows}))
    print("features in zones:", dict(cnt))
    print("old (<2022) by SSV code, dropped:", dict(old))
    print("kept with SSV code:", dict(kept))
    print("confirmed but unmapped:", other.most_common(12))
    return rows



def heading_of(row, ways):
    """Facing angle (rad, atan2(dy,dx)). aligned_direction is a compass bearing (deg cw from north)."""
    if row.get("dir") is not None:
        return math.pi / 2 - math.radians(row["dir"])
    import numpy as np
    best, tan = 1e9, (1.0, 0.0)
    for w in ways:
        P = w["pts"]
        for a, b in zip(P[:-1], P[1:]):
            d = b - a
            L2 = float(d @ d) or 1e-9
            t = min(max(float((np.array([row["x"], row["y"]]) - a) @ d) / L2, 0), 1)
            dist = float(np.hypot(*(a + d * t - [row["x"], row["y"]])))
            if dist < best:
                best, tan = dist, d / math.sqrt(L2)
    return math.atan2(-tan[1], -tan[0])


def compare(zid="4", tol=8.0):
    """Mapillary signs vs OSM-derived sign_rows in one zone -> research table + preview/mly_signs_z4.jpg."""
    import numpy as np
    from PIL import Image, ImageDraw
    sys.path.insert(0, str(ROOT / "pipeline"))
    import traffic_signs as TS
    bx = zone_bbox(zid)
    rows = [r for r in json.load(open(OUT))["signs"] if bx[0] <= r["x"] < bx[2] and bx[1] <= r["y"] < bx[3]]
    poly = zone_polys([zid])
    class Flat:
        def at(self, x, y):
            return 0.0
    osm = [r for r in TS.sign_rows(bx, Flat()) if poly.contains(__import__("shapely.geometry", fromlist=["Point"]).Point(r[0], r[1]))]
    _, ways, _ = TS._load(bx)
    codes = sorted({r["code"] for r in rows} | {o[4] for o in osm})
    tab, matched_o, dh = {}, set(), []
    for c in codes:
        m = [r for r in rows if r["code"] == c]
        o = [(i, q) for i, q in enumerate(osm) if q[4] == c]
        hit = 0
        used = set()
        for r in m:
            cand = [(math.hypot(r["x"] - q[0], r["y"] - q[1]), i, q) for i, q in o if i not in used]
            cand = [t for t in cand if t[0] <= tol]
            if cand:
                d, i, q = min(cand, key=lambda t: t[0])
                used.add(i)
                hit += 1
                dh.append(abs((r["h"] - q[3] + math.pi) % (2 * math.pi) - math.pi))
        matched_o |= {i for i in used}
        tab[c] = (len(m), len(o), hit)
    print("code        mly  osm  match  mly_only(missing_here)  osm_only(too_many)")
    T = [0, 0, 0]
    for c, (a, b, h) in tab.items():
        print(f"{c:18s}{a:4d}{b:5d}{h:6d}{a - h:8d}{b - h:10d}")
        T[0] += a; T[1] += b; T[2] += h
    print("TOTAL", T, "mean |dheading| deg:", round(math.degrees(float(np.mean(dh))), 1) if dh else None,
          "share >90deg:", round(float(np.mean([d > math.pi / 2 for d in dh])), 2) if dh else None)
    # map
    S, W = 1.1, 1500
    x0, y0, x1, y1 = bx
    sc = min(W / (x1 - x0), 1100 / (y1 - y0))
    im = Image.new("RGB", (int((x1 - x0) * sc), int((y1 - y0) * sc)), "white")
    d = ImageDraw.Draw(im)
    px = lambda x, y: ((x - x0) * sc, (y1 - y) * sc)
    for w in ways:
        d.line([px(*p) for p in w["pts"]], fill=(200, 200, 200), width=2)
    for q in osm:
        a, b = px(q[0], q[1])
        d.ellipse([a - 4, b - 4, a + 4, b + 4], outline=(220, 40, 40), width=2)
    for r in rows:
        a, b = px(r["x"], r["y"])
        d.rectangle([a - 2.5, b - 2.5, a + 2.5, b + 2.5], fill=(20, 90, 220))
        d.line([a, b, a + 9 * math.cos(r["h"]), b - 9 * math.sin(r["h"])], fill=(20, 90, 220), width=1)
    d.text((8, 8), f"zone {zid}: red circle = OSM-derived ({len(osm)}), blue square+tick = Mapillary ({len(rows)}), tick = facing", fill="black")
    im.save(ROOT / "preview" / "mly_signs_z4.jpg", quality=85)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fetch":
        zs = "4,1"
        if "--zones" in sys.argv:
            zs = sys.argv[sys.argv.index("--zones") + 1]
        fetch(zs.split(","))
    elif len(sys.argv) > 1 and sys.argv[1] == "build":
        build()
    elif len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare()
    else:
        print(__doc__)
