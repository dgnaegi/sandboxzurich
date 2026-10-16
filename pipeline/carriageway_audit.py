"""Audit: OSM carriageway (old) vs AV vs new carriageway vs SWISSIMAGE orthophoto, whole play area.

  .venv/bin/python pipeline/carriageway_audit.py [--md research/carriageway_audit.md] [--map preview/carriageway_audit.jpg]

Per street (OSM name): width error and IoU (within a window around each axis) of the old and the new carriageway against the
AV carriageway; orthophoto check: mean luminance of exclusive regions (asphalt is darker than sidewalk / pavement).
Writes the report, the map of the largest deviations and logs/carriageway_audit.json.
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import shapely
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carriageway  # noqa: E402
import groundcover  # noqa: E402
import ortho_roofs as OR  # noqa: E402
import sources  # noqa: E402
import streets  # noqa: E402
from config import AREA, POLYGON, ROOT  # noqa: E402

PLAY = shapely.Polygon(POLYGON).buffer(-8)


def parse_both():
    import pickle
    cache = ROOT / "data" / "build" / "carr_audit_parse.pkl"
    if cache.exists() and "--cached" in sys.argv:
        return pickle.load(open(cache, "rb"))
    nodes, els = sources.osm()
    os.environ["SBZ_CARRIAGEWAY"] = "osm"
    So = streets.parse(nodes, els)
    os.environ["SBZ_CARRIAGEWAY"] = "av"
    Sn = streets.parse(nodes, els)
    for S in (So, Sn):
        for k in [k for k, v in S.items() if k.startswith("_")]:
            S.pop(k)
        for w in S["ways"]:
            w.pop("_mline", None)
    pickle.dump((So, Sn), open(cache, "wb"))
    return So, Sn


def rgb_at(x, y):
    """RGB (n,3) float at local points from the 0.5 m SWISSIMAGE mosaic (NaN where tile missing)."""
    out = np.full((len(x), 3), np.nan)
    ti, tj = np.floor(x / OR.TILE).astype(int), np.floor(y / OR.TILE).astype(int)
    for i, j in {(a, b) for a, b in zip(ti, tj)}:
        im = OR._tile(i, j)
        if im is None:
            continue
        m = (ti == i) & (tj == j)
        c = np.clip(((x[m] - i * OR.TILE) * OR.PX / OR.TILE).astype(int), 0, OR.PX - 1)
        r = np.clip((((j + 1) * OR.TILE - y[m]) * OR.PX / OR.TILE).astype(int), 0, OR.PX - 1)
        out[m] = im[r, c]
    return out


def iou(a, b):
    u = a.union(b).area
    return a.intersection(b).area / u if u > 0 else float("nan")


def per_way(So, Sn, car_geom):
    """rows per non-service way inside the play area."""
    new = {w["id"]: w for w in Sn["ways"]}
    rows = []
    for wo in So["ways"]:
        wn = new.get(wo["id"])
        if wn is None or wo["hw"] == "service" or not wo["line"].intersects(PLAY) or wo["line"].length < 8 or "audit" not in wn:
            continue
        a = wn["audit"]
        win = wo["line"].buffer(wo["w"] / 2 + 3, cap_style="flat")
        av = car_geom.intersection(win)
        ro, rn = So["roads"].intersection(win), Sn["roads"].intersection(win)
        rows.append({"id": wo["id"], "name": wo["name"] or wo["hw"], "hw": wo["hw"], "len": wo["line"].length, "w_osm": wo["w"],
                     "w_new": wn["w"], "w_av": a["av_w"], "trust": a["trust"], "fb": a["fb"], "off": wn["off"],
                     "iou_old": iou(ro, av), "iou_new": iou(rn, av), "x": wo["line"].interpolate(0.5, normalized=True).x,
                     "y": wo["line"].interpolate(0.5, normalized=True).y})
    return rows


def ortho_check(So, Sn, G):
    """mean luminance in exclusive regions on a 3 m grid over the play area."""
    x0, y0, x1, y1 = PLAY.bounds
    X, Y = np.meshgrid(np.arange(x0, x1, 3.0), np.arange(y0, y1, 3.0))
    X, Y = X.ravel(), Y.ravel()
    ins = shapely.contains_xy(PLAY, X, Y)
    X, Y = X[ins], Y[ins]
    M = {k: carriageway.Mask(g).contains(X, Y) for k, g in (("old", So["roads"]), ("new", Sn["roads"]), ("av_car", G["carriageway"]),
                                                             ("av_side", G["sidewalk"]), ("av_green", G["green"]), ("bld", G["building"]))}
    rgb = rgb_at(X, Y)
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    sat = rgb.max(1) - rgb.min(1)
    greenish = (rgb[:, 1] > rgb[:, 0] + 6) & (rgb[:, 1] > rgb[:, 2] + 2)
    regs = {
        "AV Fahrbahn (Referenz)": M["av_car"] & ~M["bld"],
        "AV Trottoir/Insel": M["av_side"] & ~M["old"] & ~M["new"],
        "alt: von OSM-Fahrbahn gebaut, nicht AV-Fahrbahn": M["old"] & ~M["av_car"],
        "neu: gebaute Fahrbahn, nicht AV-Fahrbahn": M["new"] & ~M["av_car"],
        "alt gebaut, neu entfernt": M["old"] & ~M["new"],
        "neu gebaut, alt nicht": M["new"] & ~M["old"],
        "AV Fahrbahn, alt nicht gebaut": M["av_car"] & ~M["old"] & ~M["bld"],
        "AV Fahrbahn, neu nicht gebaut": M["av_car"] & ~M["new"] & ~M["bld"],
    }
    out = {}
    for k, m in regs.items():
        v = m & ~np.isnan(lum)
        out[k] = {"m2": int(m.sum() * 9), "lum": float(np.nanmean(lum[v])) if v.any() else None,
                  "sat": float(np.nanmean(sat[v])) if v.any() else None, "green": float(greenish[v].mean()) if v.any() else None}
    return out


def draw_map(rows, Sn, path, top=25):
    x0, y0, x1, y1 = AREA
    sc = 0.5
    W, H = int((x1 - x0) * sc), int((y1 - y0) * sc)
    im = Image.new("RGB", (W, H), (28, 28, 32))
    d = ImageDraw.Draw(im)
    P = lambda x, y: ((x - x0) * sc, (y1 - y) * sc)  # noqa: E731
    err = {r["id"]: r["w_osm"] - r["w_new"] for r in rows}
    for w in Sn["ways"]:
        e = err.get(w["id"])
        col = (70, 70, 74) if e is None else ((235, 80, 60) if e > 2.5 else (240, 170, 50) if e > 1.2 else (110, 190, 120) if e > -1.2 else (80, 140, 240))
        d.line([P(*c) for c in w["line"].coords], fill=col, width=2)
    worst = sorted(rows, key=lambda r: -abs(r["w_osm"] - r["w_new"]) * min(r["len"], 120))[:top]
    for i, r in enumerate(worst, 1):
        px, py = P(r["x"], r["y"])
        d.ellipse([px - 7, py - 7, px + 7, py + 7], outline=(255, 255, 255), width=2)
        d.text((px + 9, py - 6), str(i), fill=(255, 255, 255))
    d.text((12, 8), "Fahrbahnbreite OSM alt minus neu (AV): rot > 2.5 m zu breit, orange > 1.2, gruen +-1.2, blau zu schmal", fill=(255, 255, 255))
    im.save(path, quality=85)
    return worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=str(ROOT / "research" / "carriageway_audit.md"))
    ap.add_argument("--map", default=str(ROOT / "preview" / "carriageway_audit.jpg"))
    a = ap.parse_args()
    So, Sn = parse_both()
    G = groundcover.load((AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260))
    car = Sn["av_road"]  # AV carriageway + narrow tram strips
    rows = per_way(So, Sn, car)
    oc = ortho_check(So, Sn, G)
    worst = draw_map(rows, Sn, a.map)
    json.dump({"rows": rows, "ortho": oc}, open(ROOT / "logs" / "carriageway_audit.json", "w"), default=float)
    L = np.array([r["len"] for r in rows])
    wavg = lambda k, rs=rows: float(np.nansum([r[k] * r["len"] for r in rs]) / max(sum(r["len"] for r in rs), 1))  # noqa: E731
    trusted = [r for r in rows if r["trust"] > 0.6 and not np.isnan(r["w_av"])]
    md = ["# Fahrbahn-Abgleich: OSM vs Amtliche Vermessung vs Orthofoto", "",
          f"Spielgebiet, {len(rows)} OSM-Strassenabschnitte (ohne service), {L.sum() / 1000:.1f} km Achse. Skript: `pipeline/carriageway_audit.py`.", "",
          "## Kennzahlen (laengengewichtet)", "",
          "| | alt (OSM-Buffer) | neu (AV + kalibriert) |", "|---|---|---|",
          f"| Fahrbahnbreite im Mittel | {wavg('w_osm'):.2f} m | {wavg('w_new'):.2f} m |",
          f"| IoU Fahrbahn vs AV-Fahrbahn (Fenster um die Achse) | {wavg('iou_old'):.2f} | {wavg('iou_new'):.2f} |",
          f"| Gesamtflaeche Fahrbahn | {So['roads'].intersection(PLAY).area / 1e4:.1f} ha | {Sn['roads'].intersection(PLAY).area / 1e4:.1f} ha |",
          f"| AV-Fahrbahn (Referenz) | {car.intersection(PLAY).area / 1e4:.1f} ha | |", ""]
    if trusted:
        eo = np.array([r["w_osm"] - r["w_av"] for r in trusted])
        en = np.array([r["w_new"] - r["w_av"] for r in trusted])
        md += [f"Breitenfehler gegen die AV-Breite auf Abschnitten, wo die AV Fahrbahn und Trottoir trennt ({len(trusted)} Abschnitte, "
               f"{sum(r['len'] for r in trusted) / 1000:.1f} km): alt Median {np.median(eo):+.2f} m, |Fehler| p90 {np.percentile(np.abs(eo), 90):.2f} m; "
               f"neu Median {np.median(en):+.2f} m, p90 {np.percentile(np.abs(en), 90):.2f} m.", ""]
    md += ["## Nach Strassenklasse", "", "| Klasse | km | OSM alt | AV gemessen (getrennt) | neu | IoU alt | IoU neu |", "|---|---|---|---|---|---|---|"]
    by = defaultdict(list)
    for r in rows:
        by[r["hw"]].append(r)
    for hw, rs in sorted(by.items(), key=lambda kv: -sum(r["len"] for r in kv[1])):
        tr = [r for r in rs if r["trust"] > 0.6 and not np.isnan(r["w_av"])]
        md.append(f"| {hw} | {sum(r['len'] for r in rs) / 1000:.1f} | {wavg('w_osm', rs):.1f} | "
                  f"{(np.average([r['w_av'] for r in tr], weights=[r['len'] for r in tr]) if tr else float('nan')):.1f} | {wavg('w_new', rs):.1f} | "
                  f"{wavg('iou_old', rs):.2f} | {wavg('iou_new', rs):.2f} |")
    md += ["", "Kalibrierte Breiten (Median der AV-Fahrbahn dort, wo Trottoir getrennt erfasst ist): "
           + ", ".join(f"{k[0]} {v:.1f} m" for k, v in sorted(carriageway_cal(Sn).items()) if len(k) == 1), "",
           "## Orthofoto-Kontrolle (SWISSIMAGE 0.5 m, Raster 3 m)", "",
           "Asphalt ist dunkler und weniger hell als Trottoir/Platzbelag. Mittlere Helligkeit (0-255) in sich ausschliessenden Zonen:", "",
           "| Zone | m2 | Helligkeit | gruenlich |", "|---|---|---|---|"]
    for k, v in oc.items():
        md.append(f"| {k} | {v['m2']} | {v['lum']:.0f} | {v['green'] * 100:.0f} % |" if v["lum"] is not None else f"| {k} | {v['m2']} | - | - |")
    md += ["", "## Groesste Abweichungen (Nummern in `preview/carriageway_audit.jpg`)", "",
           "| # | Strasse | Typ | Laenge | OSM alt | AV | neu | Versatz | vertrauenswuerdig |", "|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(worst, 1):
        md.append(f"| {i} | {r['name']} | {r['hw']} | {r['len']:.0f} m | {r['w_osm']:.1f} | {r['w_av']:.1f} | {r['w_new']:.1f} | {r['off']:+.1f} | {r['trust'] * 100:.0f} % |")
    Path(a.md).write_text("\n".join(md) + "\n")
    print("\n".join(md[:24]))


def carriageway_cal(Sn):
    return Sn.get("carriageway_cal", {})


if __name__ == "__main__":
    main()
