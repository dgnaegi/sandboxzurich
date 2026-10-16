"""Measure road surface quality along all street axes (height profile, gaps, sharp corners).

  .venv/bin/python pipeline/roads_audit.py [--post] [--md research/roads_audit.md] [--map preview/roads_audit_map.jpg]
--post applies pipeline/road_height.py first (what the build now does); without it the raw terrain is measured.
Writes JSON summary to logs/roads_audit_<pre|post>.json as well.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Point

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridges  # noqa: E402
import road_height  # noqa: E402
import sources  # noqa: E402
import streets  # noqa: E402
import terrain  # noqa: E402
import terrain_cuts  # noqa: E402
from config import AREA, HGRID, POLYGON, ROOT  # noqa: E402

PLAY = shapely.Polygon(POLYGON).buffer(-8)

SLOPE, JUMP, CURV = 0.08, 0.25, 0.10  # 8 %, 0.25 m per 1 m, 2nd difference over 3 m


def load(post):
    nodes, els = sources.osm()
    BIG = (AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)
    H = terrain.heights(BIG, HGRID, z_shift=-3.06)
    terrain_cuts.apply(H)
    S = streets.parse(nodes, els)
    if post:
        road_height.apply(H, S["ways"])
    BR = bridges.bridge_ways(nodes, els, AREA, H)
    EX = bridges.exclusion(BR)
    S["chain"] = {i for b in BR for i in b["ids"]}
    return H, S, road_height.ground_exclusion(EX, BR, S["ways"])


def profile_stats(H, ways):
    ev, tot = [], 0.0
    rough = []
    for w in ways:
        t = w.get("tags", {})
        if t.get("bridge") in road_height.SKIP_BRIDGE or t.get("tunnel") in ("yes", "building_passage"):
            continue
        ln = w["line"]
        ln = ln.intersection(PLAY)
        if ln.geom_type != "LineString" or ln.length < 8:
            continue
        s = np.arange(0, ln.length, 1.0)
        xy = np.array([(p.x, p.y) for p in shapely.line_interpolate_point(ln, s)])
        z = H.at(xy[:, 0], xy[:, 1]).astype(float)
        tot += ln.length
        d1 = np.diff(z)  # per 1 m
        d2 = np.zeros_like(z)
        d2[3:-3] = z[:-6] - 2 * z[3:-3] + z[6:]  # over 3 m
        sl = np.zeros_like(z)
        sl[2:-2] = np.abs(z[4:] - z[:-4]) / 4.0  # slope over 4 m
        jm = np.zeros_like(z)
        jm[1:] = np.abs(d1)
        rough.append(float(np.sqrt(np.mean(d2[3:-3] ** 2))) if len(z) > 8 else 0.0)
        score = np.maximum.reduce([sl / SLOPE, jm / JUMP, np.abs(d2) / CURV])
        flag = score > 1
        i = 0
        while i < len(z):
            if flag[i]:
                j = i
                while j + 6 < len(z) and flag[j + 1: j + 7].any():
                    j += 1
                k = i + int(np.argmax(score[i:j + 1]))
                kind = [n for n, v in (("slope", sl[k] / SLOPE), ("jump", jm[k] / JUMP), ("curv", abs(d2[k]) / CURV)) if v > 1]
                ev.append({"x": float(xy[k, 0]), "y": float(xy[k, 1]), "score": float(score[k]), "len": int(j - i + 1),
                           "kind": "+".join(kind), "name": w["name"] or w["hw"], "slope": float(sl[k]), "jump": float(jm[k]), "d2": float(d2[k])})
                i = j + 7
            else:
                i += 1
    return ev, tot, rough


def geometry_stats(S, EX, ways):
    chain = S.get("chain", set())
    roads = S["roads"]
    polys = list(getattr(roads, "geoms", [roads]))
    sharp = []
    holes = []
    polys = [p for p in polys if p.intersects(PLAY)]
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            c = np.asarray(ring.coords)[:-1]
            a, b, d = np.roll(c, 1, 0), c, np.roll(c, -1, 0)
            v1, v2 = a - b, d - b
            l1, l2 = np.hypot(*v1.T), np.hypot(*v2.T)
            ok = (l1 > 0.3) & (l2 > 0.3)
            cos = np.einsum("ij,ij->i", v1, v2) / np.maximum(l1 * l2, 1e-9)
            ang = np.degrees(np.arccos(np.clip(cos, -1, 1)))
            for i in np.where(ok & (ang < 50))[0]:
                if not PLAY.contains(Point(b[i])):
                    continue
                sharp.append({"x": float(b[i, 0]), "y": float(b[i, 1]), "ang": float(ang[i])})
        for r in p.interiors:
            a = shapely.Polygon(r).area
            if a < 400:
                holes.append({"x": float(r.centroid.x), "y": float(r.centroid.y), "area": float(a)})
    # axis parts inside bridge exclusions that are not themselves bridges (road underneath: expected), and gaps after EX
    gaps = []
    for w in ways:
        t = w.get("tags", {})
        if t.get("bridge") in road_height.SKIP_BRIDGE or t.get("tunnel") in ("yes", "building_passage"):
            continue
        if w["hw"] in ("service",) or w["id"] in chain:  # bridge chains have no ground road by design
            continue
        if not w["line"].intersects(PLAY):
            continue
        r = w["line"].intersection(PLAY).difference(roads.difference(EX) if not EX.is_empty else roads)
        for g in getattr(r, "geoms", [r]):
            if g.geom_type == "LineString" and g.length > 3:
                m = g.interpolate(0.5, normalized=True)
                gaps.append({"x": float(m.x), "y": float(m.y), "len": float(g.length), "name": w["name"] or w["hw"]})
    return sharp, holes, gaps


def draw_map(ev, sharp, ways, path, post):
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = AREA
    sc = 0.5  # px per m
    W, Hh = int((x1 - x0) * sc), int((y1 - y0) * sc)
    im = Image.new("RGB", (W, Hh), (245, 245, 240))
    dr = ImageDraw.Draw(im)
    P = lambda x, y: ((x - x0) * sc, (y1 - y) * sc)
    for w in ways:
        dr.line([P(*c) for c in w["line"].coords], fill=(190, 190, 190), width=1)
    for e in ev:
        r = 2 + min(e["score"], 4)
        px, py = P(e["x"], e["y"])
        col = (220, 30, 30) if e["score"] > 2 else (240, 150, 0)
        dr.ellipse([px - r, py - r, px + r, py + r], outline=col)
    for s in sharp:
        px, py = P(s["x"], s["y"])
        dr.point([px, py], fill=(30, 60, 220))
    for i, e in enumerate(sorted(ev, key=lambda e: -e["score"])[:30]):
        px, py = P(e["x"], e["y"])
        dr.text((px + 5, py - 5), str(i + 1), fill=(0, 0, 0))
    im.save(path, quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--md", default=None)
    ap.add_argument("--map", default=None)
    a = ap.parse_args()
    H, S, EX = load(a.post)
    ways = [w for w in S["ways"] if w["hw"] != "service"]
    ev, tot, rough = profile_stats(H, ways)
    sharp, holes, gaps = geometry_stats(S, EX, ways)
    ev.sort(key=lambda e: -e["score"])
    n_km = tot / 1000
    lab = "post" if a.post else "pre"
    summ = {"mode": lab, "axis_km": round(n_km, 1), "events": len(ev), "events_per_km": round(len(ev) / n_km, 2),
            "slope>8%": sum("slope" in e["kind"] for e in ev), "jump>0.25": sum("jump" in e["kind"] for e in ev),
            "curv": sum("curv" in e["kind"] for e in ev), "rough_rms_mean": round(float(np.mean(rough)), 4),
            "sharp_corners<50deg": len(sharp), "holes<400m2": len(holes), "axis_gaps": len(gaps)}
    print(json.dumps(summ))
    (ROOT / "logs").mkdir(exist_ok=True)
    json.dump({"summary": summ, "top": ev[:60], "sharp": sharp[:60], "holes": holes[:30], "gaps": gaps[:30]},
              open(ROOT / "logs" / f"roads_audit_{lab}.json", "w"))
    if a.md:
        L = [f"# Strassen-Audit ({lab})", "", "Messung entlang aller OSM-Achsen (ohne Brücken/Tunnel/Service), 1-m-Schritte, Höhe = H.at wie im Build.",
             f"Schwellen: Steigung > {SLOPE:.0%} (über 4 m), Sprung > {JUMP} m auf 1 m, 2. Differenz > {CURV} m über 3 m.", "",
             "## Zusammenfassung", "", "| Kennzahl | Wert |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in summ.items()]
        L += ["", "## Top 30 Höhenstellen", "", "| # | x | y | Strasse | Art | Score | Steigung | Sprung | d2 |", "|---|---|---|---|---|---|---|---|---|"]
        for i, e in enumerate(ev[:30]):
            L.append(f"| {i + 1} | {e['x']:.0f} | {e['y']:.0f} | {e['name'][:28]} | {e['kind']} | {e['score']:.1f} | {e['slope']:.1%} | {e['jump']:.2f} | {e['d2']:+.2f} |")
        L += ["", "## Spitze Polygonecken (< 50 Grad), 15 schärfste", ""]
        L += [f"- ({s['x']:.0f}, {s['y']:.0f}) {s['ang']:.0f} Grad" for s in sorted(sharp, key=lambda s: s["ang"])[:15]]
        L += ["", "## Löcher in der Fahrbahn (< 400 m2)", ""] + [f"- ({h['x']:.0f}, {h['y']:.0f}) {h['area']:.0f} m2" for h in holes[:15]]
        L += ["", "## Achsen ohne Fahrbahn (nicht-Brücke, nach Brücken-Exklusion)", ""]
        L += [f"- ({g['x']:.0f}, {g['y']:.0f}) {g['len']:.0f} m {g['name']}" for g in sorted(gaps, key=lambda g: -g["len"])[:15]]
        Path(a.md).write_text("\n".join(L) + "\n")
    if a.map:
        draw_map(ev, sharp, ways, a.map, a.post)


if __name__ == "__main__":
    main()
