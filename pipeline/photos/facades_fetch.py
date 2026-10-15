"""Mapillary facade photos per GWR address (v3 facade research).

1. Targets: GWR addresses on the Blockrand streets inside the play area (>= 3 floors or built <= 1945, no industry).
2. Mapillary image metadata per ~150 m cell (cached in data/raw/photos/facades/cells/), >= 2020, no panos.
3. Per address the best image looking at it from 9-40 m (compass within 22 deg of the bearing to the house).
4. Download (1024 px), crop square around the house, store 512 px in data/raw/photos/facades/crops/.
Meta (author, capture date, ids -> CC BY-SA credits) in research/buildings/sheets_v3/candidates.json.
Resumable. Usage: python facades_fetch.py [--list] [--limit N] [--streets a,b]
Token: MAPILLARY_TOKEN in .env (read via fetch_v3.token()). Do not call with a raw token on the command line.
"""
import argparse
import io
import json
import math
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from shapely.geometry import Point, Polygon

sys.path.insert(0, str(Path(__file__).parent))
import fetch_v3 as F  # noqa: E402

ROOT = F.ROOT
RAW = ROOT / "data" / "raw" / "photos" / "facades"
CELLS = RAW / "cells"
CROPS = RAW / "crops"
CAND = ROOT / "research" / "buildings" / "sheets_v3" / "candidates.json"
TARGETS = ROOT / "research" / "buildings" / "sheets_v3" / "targets.json"

PRIO = ("Langstrasse Badenerstrasse Stauffacherstrasse Hohlstrasse Josefstrasse Limmatstrasse Militärstrasse Zweierstrasse "
        "Weststrasse Seebahnstrasse Hardstrasse Birmensdorferstrasse Kalkbreitestrasse Zurlindenstrasse Heinrichstrasse "
        "Kanzleistrasse Baslerstrasse Neugasse Brauerstrasse Bullingerstrasse").split()
MORE = ("Hardturmstrasse Zwinglistrasse Anwandstrasse Feldstrasse Konradstrasse Dienerstrasse Magnusstrasse Gutstrasse "
        "Sihlfeldstrasse Albisriederstrasse Agnesstrasse Pflanzschulstrasse Ankerstrasse Lagerstrasse Gasometerstrasse "
        "Röntgenstrasse Sihlquai Aemtlerstrasse Zypressenstrasse Hallwylstrasse Quellenstrasse Zollstrasse Fabrikstrasse "
        "Schöneggstrasse Engelstrasse Kasernenstrasse Eichbühlstrasse Altstetterstrasse Müllerstrasse Erismannstrasse").split()
CELL = 70.0
FOV = 70.0


def street_dir(pts, x, y):
    """Bearing (deg, mod 180) of the street axis near (x, y): PCA of the 6 nearest address points of the same street."""
    import numpy as np
    a = np.array(pts)
    near = a[np.argsort(np.hypot(a[:, 0] - x, a[:, 1] - y))[:8]]
    if len(near) < 3:
        return None
    c = near - near.mean(0)
    w, v = np.linalg.eigh(c.T @ c)
    dx, dy = v[:, 1]
    return round(math.degrees(math.atan2(dx, dy)) % 180, 1)


def targets(streets=None):
    pa = json.load(open(ROOT / "data" / "build" / "playarea.json"))
    poly = Polygon(pa["polygon"])
    order = {s: i for i, s in enumerate(PRIO + MORE)}
    out = []
    gwr = json.load(open(ROOT / "data" / "build" / "gwr_kreise.json"))
    by_street = defaultdict(list)
    for r in gwr:
        by_street[r["street"]].append((r["x"], r["y"]))
    for r in gwr:
        s = r["street"]
        if s not in order or (streets and s not in streets):
            continue
        if not poly.contains(Point(r["x"], r["y"])):
            continue
        if not ((r["floors"] or 0) >= 3 or (r["period"] or 99) <= 12) or r["class"] in (1251, 1252):
            continue
        out.append(dict(sdir=street_dir(by_street[s], r["x"], r["y"]), addr=f"{s} {r['nr']}", street=s, nr=r["nr"], x=r["x"], y=r["y"], year=r["year"], floors=r["floors"],
                        period=r["period"], cls=r["class"], prio=order[s]))
    def nrkey(t):
        n = "".join(c for c in t["nr"] if c.isdigit())
        return (t["prio"], int(n) if n else 0, t["nr"])
    out.sort(key=nrkey)
    return out


def cell_images(cx, cy, tok):
    """All usable images in a 150 m cell (local metres), cached."""
    f = CELLS / f"{cx}_{cy}.json"
    if f.exists():
        return json.load(open(f))
    lat0, lon0 = F.local_ll((cx + 0.5) * CELL, (cy + 0.5) * CELL)
    pad = 42  # a camera within 40 m of any house in the cell lies inside the bbox (bigger bboxes return truncated, inconsistent results)
    dlat, dlon = (CELL / 2 + pad) / 110574, (CELL / 2 + pad) / (111320 * math.cos(math.radians(lat0)))
    FIELDS = "id,thumb_1024_url,compass_angle,computed_compass_angle,computed_geometry,captured_at,creator,is_pano,camera_type,camera_parameters"

    def q(x0, y0, x1, y1, tries=2):
        for _ in range(tries):
            r = F.get("ml", F.ML, {"access_token": tok, "bbox": f"{x0:.6f},{y0:.6f},{x1:.6f},{y1:.6f}", "fields": FIELDS, "limit": 2000}, pause=0.25)
            if r:
                return r.json().get("data", [])
            time.sleep(3)
        return None

    data = q(lon0 - dlon, lat0 - dlat, lon0 + dlon, lat0 + dlat)
    if data is None:  # dense cell: the API answers 500; ask quadrant by quadrant
        data = []
        for sx in (-1, 0):
            for sy in (-1, 0):
                part = q(lon0 + sx * dlon, lat0 + sy * dlat, lon0 + sx * dlon + dlon, lat0 + sy * dlat + dlat)
                if part is None:
                    return None
                data += part
    r = type("R", (), {"json": lambda self: {"data": data}})()
    ims = []
    for im in r.json().get("data", []):
        if im.get("is_pano") or not im.get("computed_geometry") or im.get("captured_at", 0) < 1577836800000:
            continue
        lon, lat = im["computed_geometry"]["coordinates"]
        cp = im.get("camera_parameters") or []
        if im.get("camera_type") not in (None, "perspective") and not cp:
            continue  # fisheye / spherical: no usable pinhole geometry
        ims.append(dict(f=cp[0] if cp and 0.2 < cp[0] < 2 else 0.85, id=im["id"], lat=lat, lon=lon, hd=im.get("computed_compass_angle", im.get("compass_angle")),
                        ts=im["captured_at"], by=(im.get("creator") or {}).get("username", "unknown"), u=im["thumb_1024_url"]))
    CELLS.mkdir(parents=True, exist_ok=True)
    json.dump(ims, open(f, "w"))
    return ims


def best(t, ims):
    lat, lon = F.local_ll(t["x"], t["y"])
    cands = []
    for im in ims:
        if im["hd"] is None:
            continue
        dx, dy = F.metres(lat, lon, im["lat"], im["lon"])
        d = math.hypot(dx, dy)
        if d < 9 or d > 40:
            continue
        b = F.bearing(dx, dy)
        diff = F.adiff(im["hd"], b)
        if diff > 24 or F.is_night(im["ts"]):
            continue
        # frontal view: camera looks roughly across the street (perpendicular to the street axis)
        pe = abs(((im["hd"] - t["sdir"]) % 180) - 90) if t.get("sdir") is not None else 30
        if pe > 70:
            continue
        yr = datetime.fromtimestamp(im["ts"] / 1000, timezone.utc).year
        cands.append((abs(d - 22) * 0.3 + diff * 0.5 + pe * 0.5 + (2026 - yr) * 1.2, dict(im, d=round(d, 1), diff=round(diff, 1), rel=(b - im["hd"] + 540) % 360 - 180, year=yr)))
    cands.sort(key=lambda c: c[0])
    return [c[1] for c in cands[:3]]


def crop(content, rel, f, d):
    """Square crop around the bearing to the house (pinhole model, f = focal / max(w, h)); None if outside the frame."""
    im = Image.open(io.BytesIO(content)).convert("RGB")
    w, h = im.size
    m = max(w, h)
    cx = w / 2 + math.tan(math.radians(rel)) * f * m
    if cx < 40 or cx > w - 40:
        return None
    s = int(max(300, min(h, 2 * (12.5 / d) * f * m)))
    x0 = int(max(0, min(w - s, cx - s / 2)))
    y0 = int(max(0, h * 0.5 - s * 0.80))   # horizon a little below the middle: keep the upper floors
    y0 = min(y0, h - s)
    return im.crop((x0, y0, x0 + s, y0 + s)).resize((512, 512), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--streets", default="")
    a = ap.parse_args()
    T = targets(set(a.streets.split(",")) if a.streets else None)
    TARGETS.parent.mkdir(parents=True, exist_ok=True)
    json.dump(T, open(TARGETS, "w"), ensure_ascii=False)
    F.log(f"{len(T)} targets, {len({t['street'] for t in T})} streets")
    if a.list:
        return
    tok = F.token()
    cand = json.load(open(CAND)) if CAND.exists() else {}
    CROPS.mkdir(parents=True, exist_ok=True)
    n = ok = 0
    for t in T:
        if t["addr"] in cand:
            continue
        if a.limit and n >= a.limit:
            break
        n += 1
        cx, cy = int(t["x"] // CELL), int(t["y"] // CELL)
        got = cell_images(cx, cy, tok)
        failed = got is None
        ims = got or []
        seen, uniq = set(), []
        for im in ims:
            if im["id"] not in seen:
                seen.add(im["id"])
                uniq.append(im)
        bs = best(t, uniq)
        rec = dict(t, imgs=[])
        for im in bs[:1]:
            r = F.get("dl", im["u"], pause=0.15)
            if not r:
                continue
            slug = t["addr"].replace(" ", "_").replace("/", "-")
            c = crop(r.content, im["rel"], im["f"], im["d"])
            if c is None:
                continue
            c.save(CROPS / f"{slug}.jpg", "JPEG", quality=85)
            rec["imgs"].append(dict(id=im["id"], by=im["by"], year=im["year"], d=im["d"], diff=im["diff"], file=f"crops/{slug}.jpg"))
            ok += 1
        if failed and not rec["imgs"]:
            F.log(f"  retry later: {t['addr']}")
            continue
        cand[t["addr"]] = rec
        if n % 25 == 0:
            json.dump(cand, open(CAND, "w"), ensure_ascii=False)
            F.log(f"{n} processed, {ok} with photo")
    json.dump(cand, open(CAND, "w"), ensure_ascii=False)
    F.log(f"done: {n} processed, {ok} with photo, total {len(cand)}")


if __name__ == "__main__":
    main()
