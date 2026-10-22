"""Read-only audit for floating / pointless bridge decks and floating props (cause of the Lochergut passerelle bug).
Usage: .venv/bin/python pipeline/audit_float.py  -> research/audit_float.md (+ research/audit_float.json)
Part 1: OSM bridge ways without obstacle underneath / with dangling ends / duplicating a road bridge's sidewalk / absurd height.
Part 2: tile prop rows (audit_props.py), landmarks vs terrain, swissBUILDINGS3D-independent checks from tile data."""
import base64
import glob
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridges as B  # noqa: E402
import lidar  # noqa: E402  (LiDAR ground reference, pipeline/lidar_grid.py)
import sources  # noqa: E402
from config import AREA  # noqa: E402

TILE = 200


def tk(x, y):
    return f"{math.floor(x / TILE)}_{math.floor(y / TILE)}"


# ---- terrain from tile hmaps ----------------------------------------------------------------------------------------
HM = {}
for f in glob.glob(str(R / "web/public/tiles/t_*.json")):
    try:
        m = json.load(open(f))
    except Exception:
        continue
    h = m.get("hmap")
    if h and "zb64" in h:
        z = np.frombuffer(base64.b64decode(h["zb64"]), dtype="<i2").astype(float).reshape(h["h"], h["w"]) / 100
        HM[(int(round(h["x0"])) // TILE, int(round(h["y0"])) // TILE)] = (h, z)


def ground(x, y):
    e = HM.get((math.floor(x / TILE), math.floor(y / TILE)))
    if not e:
        return None
    d, z = e
    fx = min(max((x - d["x0"]) / d["step"], 0), d["w"] - 1.001)
    fy = min(max((y - d["y0"]) / d["step"], 0), d["h"] - 1.001)
    ix, iy = int(fx), int(fy)
    tx, ty = fx - ix, fy - iy
    return (z[iy, ix] * (1 - tx) + z[iy, ix + 1] * tx) * (1 - ty) + (z[iy + 1, ix] * (1 - tx) + z[iy + 1, ix + 1] * tx) * ty


def excluded():
    s = set()
    for fn in ("lochergut_excl.json", "bridges_excl.json"):
        p = R / "pipeline/overrides" / fn
        if p.exists():
            raw = json.load(open(p))
            ids = raw.get("bridge_way_ids", [])
            s |= {int(i["id"] if isinstance(i, dict) else i) for i in ids}
    return s


def part1(out):
    nodes, els = sources.osm()
    ab = shapely.geometry.box(*AREA).buffer(60)
    skip = excluded()
    ways, water = [], []
    for e in els:
        if e["type"] != "way" or len(e.get("nodes", [])) < 2:
            continue
        t = e.get("tags", {})
        pts = [nodes[n] for n in e["nodes"] if n in nodes]
        if len(pts) < 2:
            continue
        ln = LineString(pts)
        if not ln.intersects(ab):
            continue
        if t.get("waterway") in ("river", "canal", "stream") and not B._is_bridge(t) and t.get("tunnel") not in ("yes", "culvert"):
            water.append(ln.buffer(3.0 if t["waterway"] == "stream" else 8.0))
            continue
        if t.get("natural") == "water" and pts[0] == pts[-1] and len(pts) >= 4:
            water.append(shapely.Polygon(pts).buffer(0))
            continue
        k = B._kind(t)
        if k is None or t.get("area") == "yes":
            continue
        tunnel = t.get("tunnel") in ("yes", "building_passage", "culvert") or B._layer(t, False) < 0
        ways.append({"id": e["id"], "nodes": [n for n in e["nodes"] if n in nodes], "line": ln, "kind": k, "tunnel": tunnel,
                     "bridge": B._is_bridge(t), "layer": B._layer(t, B._is_bridge(t)), "w": B._width(t, k),
                     "name": t.get("name", ""), "hw": t.get("highway") or t.get("railway")})
    flat = [w for w in ways if not w["tunnel"]]
    by_node = defaultdict(list)
    for w in flat:
        for n in w["nodes"]:
            by_node[n].append(w)
    geoms = [w["line"].buffer(w["w"] / 2 + 0.3, cap_style="flat") for w in flat]
    tree = STRtree(geoms)
    wtree = STRtree(water) if water else None
    allln = STRtree([w["line"] for w in flat])
    roadbr = [w for w in flat if w["bridge"] and w["kind"] in ("road", "tram")]
    rbt = STRtree([w["line"] for w in roadbr])
    rows = []
    for w in flat:
        if not w["bridge"]:
            continue
        ln = w["line"]
        pts = list(ln.coords)
        cat, why = [], []
        # obstacle: lower-layer way / water crossing or terrain depression
        obst = False
        for j in tree.query(ln):
            o = flat[j]
            if o["id"] == w["id"] or set(o["nodes"]) & set(w["nodes"]):
                continue
            if o["layer"] < w["layer"] and not o["bridge"] and geoms[j].intersects(ln):
                obst = True
                break
        if not obst and wtree is not None and len(wtree.query(ln, predicate="intersects")):
            obst = True
        gz = [ground(x, y) for x, y in (ln.interpolate(d).coords[0] for d in np.linspace(0, ln.length, max(3, int(ln.length / 4))))]
        gz = [g for g in gz if g is not None]
        dep = 0.0
        if len(gz) >= 3:
            ends = (gz[0] + gz[-1]) / 2
            dep = ends - min(gz)
            if dep > 2.0:
                obst = True
        if not obst and w["tunnel"] is False:
            cat.append("no_obstacle")
            why.append("nothing underneath (no lower way/water, terrain depression %.1f m)" % dep)
        # dangling ends
        dang = 0
        for n, p in ((w["nodes"][0], pts[0]), (w["nodes"][-1], pts[-1])):
            ok = any(o["id"] != w["id"] and (o["kind"] == w["kind"] or w["kind"] == "foot" and o["kind"] == "road" or o["kind"] == "foot" and w["kind"] == "road") for o in by_node[n])
            if not ok:
                for j in allln.query(Point(p).buffer(3.0)):
                    o = flat[j]
                    if o["id"] != w["id"] and o["layer"] == w["layer"] and o["line"].distance(Point(p)) < 3.0:
                        ok = True
                        break
            dang += (not ok)
        if dang:
            cat.append("dangling_%d" % dang)
            why.append("%d end(s) connect to no way" % dang)
        # duplicate sidewalk next to road bridge
        if w["kind"] == "foot" and len(ln.coords):
            for j in rbt.query(ln.buffer(16)):
                r = roadbr[j]
                near = r["line"].buffer(r["w"] / 2 + 9)
                frac = ln.intersection(near).length / max(ln.length, 1e-6)
                if frac > 0.75 and ln.length > 8:
                    cat.append("dup_sidewalk")
                    why.append("%.0f%% inside road bridge %d %s" % (frac * 100, r["id"], r["name"]))
                    break
        if cat:
            c = ln.interpolate(0.5, normalized=True)
            rows.append({"id": w["id"], "kind": w["kind"], "name": w["name"], "x": round(c.x), "y": round(c.y), "len": round(ln.length),
                         "cat": cat, "why": "; ".join(why), "tile": tk(c.x, c.y), "layer": w["layer"], "hw": w["hw"]})
    # deck height mismatch of duplicate sidewalks vs the road bridge chain they run along (what made the Lochergut passerelle float)
    chs = B.load_chains() or []
    byid = {i: c for c in chs for i in c["ids"]}
    for r in rows:
        r["mismatch"] = None
        m = __import__("re").search(r"bridge (\d+)", r["why"])
        f, rd = byid.get(r["id"]), (byid.get(int(m.group(1))) if m else None)
        if "dup_sidewalk" in r["cat"] and f and rd:
            P = np.array(rd["p"])
            ds = []
            for x, y, z in f["p"]:
                d2 = (P[:, 0] - x) ** 2 + (P[:, 1] - y) ** 2
                k = int(np.argmin(d2))
                gg = ground(P[k, 0], P[k, 1])
                if d2[k] < (rd["w"] / 2 + 5) ** 2 and gg is not None and P[k, 2] - gg > 2.0:
                    ds.append(z - P[k, 2])
            if len(ds) >= 2:
                r["mismatch"] = round(sum(abs(d) > 1.2 for d in ds) / len(ds), 2)
                r["dz"] = round(float(np.mean(ds)), 2)
    out["bridge_rows"] = rows
    out["bridges_total"] = sum(1 for w in flat if w["bridge"])
    # chain heights (real build)
    ch = B.load_chains() or []
    hi = []
    for c in ch:
        p = np.array(c["p"])
        g = [ground(a, b) for a, b, _ in p]
        cl = [z - gg for z, gg in zip(p[:, 2], g) if gg is not None]
        if cl and max(cl) > (22 if c["kind"] in ("rail", "road") else 14):
            i = int(np.argmax(cl))
            hi.append({"ids": c["ids"], "kind": c["kind"], "name": c.get("name", ""), "x": round(p[i][0]), "y": round(p[i][1]), "clear": round(max(cl), 1), "tile": tk(p[i][0], p[i][1])})
    out["high"] = hi
    out["chains"] = len(ch)


def part2(out):
    import audit_props as ap
    files = sorted(glob.glob(str(R / "web/public/tiles/t_*.json")))
    dk = []
    for extra in ("station_decks", "hb_decks", "hb3_decks", "velotunnel_decks"):
        try:
            dk += json.load(open(R / f"web/public/data/{extra}.json")).get("decks", [])
        except Exception:
            pass
    metas = {}
    for f in files:
        m = json.load(open(f))
        metas[f] = m
        dk += (m.get("bridges") or {}).get("decks", [])
    ap.build_grid(dk)
    issues, tot, lissues, ltot = [], Counter(), [], Counter()
    for f, m in metas.items():
        if not m.get("hmap"):
            continue
        h = ap.load_h(m["hmap"])
        for k in ap.KINDS + ["benches", "bins", "playground", "signs", "streetsigns", "housenumbers", "hydrants"]:
            for r in m.get(k, []):
                if isinstance(r, dict):
                    x, y, z = r.get("x"), r.get("y"), r.get("z")
                elif len(r) >= 3 and isinstance(r[2], (int, float)):
                    x, y, z = r[0], r[1], r[2]
                else:
                    continue
                if z is None or k in ("streetsigns", "housenumbers", "signs"):
                    continue  # wall mounted: z is not ground contact
                tot[k] += 1
                g = ap.at(h, x, y)
                dz = ap.deck_z(dk, x, y)
                ref = [g] + ([dz] if dz is not None else [])
                d = min((z - q for q in ref), key=abs)
                if dz is None:   # LiDAR ground (class 2) where no deck: independent of the game's own terrain
                    lg = float(lidar.dtm(x, y)[0])
                    if not math.isnan(lg) and math.isnan(float(lidar.bld(x, y)[0])) and math.isnan(float(lidar.bridge(x, y)[0])):
                        ltot[k] += 1
                        dl = z - lg
                        if dl > 0.6 or dl < -0.9:
                            lissues.append({"kind": k, "x": round(x, 1), "y": round(y, 1), "dz": round(dl, 2), "pg": round(z - g, 2), "tile": Path(f).stem[2:]})
                if d > 0.6 or d < -0.9:
                    issues.append({"kind": k, "x": round(x, 1), "y": round(y, 1), "dz": round(d, 2), "deck": dz is not None, "tile": Path(f).stem[2:]})
    out["prop_issues"] = issues
    out["lidar_issues"], out["lidar_total"] = lissues, dict(ltot)
    out["prop_total"] = dict(tot)
    # landmarks
    lm = json.load(open(R / "web/public/data/landmarks.json"))["landmarks"]
    lrows = []
    for l in lm:
        x, y, z = l.get("x"), l.get("y"), l.get("z", l.get("z0"))
        if x is None or z is None:
            continue
        e = HM.get((math.floor(x / TILE), math.floor(y / TILE)))
        if not e:
            continue
        g = ap.at(ap.load_h(e[0]) if False else (e[0], e[1]), x, y)
        d = z - g
        if abs(d) > 1.5:
            lrows.append({"name": l.get("id") or l.get("name"), "x": round(x), "y": round(y), "dz": round(d, 2), "tile": tk(x, y)})
    out["landmark_issues"] = lrows
    out["landmark_total"] = len(lm)


def write(out):
    L = ["# Audit: schwebende / versunkene Dinge", "", "Erzeugt von `pipeline/audit_float.py` (read-only). Kachel = floor(x/200)_floor(y/200).", ""]
    br = out["bridge_rows"]
    L.append("## 1. Brücken-Decks (OSM bridge=yes), %d geprüft, %d Chains im Build" % (out["bridges_total"], out["chains"]))
    cnt = Counter(c.split("_")[0] + ("_" + c.split("_")[1] if c.startswith("no") else "") for r in br for c in r["cat"])
    for k, n in sorted(cnt.items()):
        L.append("- %s: %d" % (k, n))
    mm = [r for r in br if (r.get("mismatch") or 0) >= 0.5]
    L.append("- dup_sidewalk mit Höhen-Versatz (>=50%% der Deckpunkte >1.2 m neben der Strassenbrücke): %d" % len(mm))
    sev = lambda r: (("dup_sidewalk" in r["cat"]) * 4 + sum(c.startswith("dangling") for c in r["cat"]) * 3 + ("no_obstacle" in r["cat"]) * 2, r["len"])
    L += ["", "Top 20 (id kind name x,y len Kachel Ursache):"]
    for r in sorted(br, key=sev, reverse=True)[:20]:
        L.append("- %d %s «%s» (%d,%d) %dm [%s] %s" % (r["id"], r["kind"], r["name"], r["x"], r["y"], r["len"], r["tile"], r["why"]))
    L += ["", "Unrealistisch hohe Decks (Chains, Freiraum > 22/14 m): %d" % len(out["high"])]
    for r in sorted(out["high"], key=lambda r: -r["clear"])[:8]:
        L.append("- %s «%s» %.1f m bei (%d,%d) [%s] ids=%s" % (r["kind"], r["name"], r["clear"], r["x"], r["y"], r["tile"], r["ids"][:2]))
    L += ["", "## 2. Props / Landmarks gegen Gelände (Toleranz +0.6 / -0.9 m)"]
    pc = Counter(i["kind"] for i in out["prop_issues"])
    L.append("- Props geprüft: %d, auffällig: %d" % (sum(out["prop_total"].values()), len(out["prop_issues"])))
    L.append("- je Art: " + ", ".join("%s %d/%d" % (k, n, out["prop_total"].get(k, 0)) for k, n in pc.most_common()))
    L.append("- Landmarks: %d geprüft, %d mit |dz|>1.5 m" % (out["landmark_total"], len(out["landmark_issues"])))
    L += ["", "Top 20 Props (Kachel-Cluster):"]
    cl = Counter((i["kind"], i["tile"]) for i in out["prop_issues"])
    ex = {}
    for i in sorted(out["prop_issues"], key=lambda i: -abs(i["dz"])):
        ex.setdefault((i["kind"], i["tile"]), i)
    for (k, t), n in cl.most_common(20):
        i = ex[(k, t)]
        L.append("- %s x%d [%s] schlimmster (%.0f,%.0f) dz %+.2f%s" % (k, n, t, i["x"], i["y"], i["dz"], " auf Deck" if i["deck"] else ""))
    L += ["", "Landmarks:"]
    for r in sorted(out["landmark_issues"], key=lambda r: -abs(r["dz"]))[:10]:
        L.append("- %s (%d,%d) dz %+.1f [%s]" % (r["name"], r["x"], r["y"], r["dz"], r["tile"]))
    li = out.get("lidar_issues", [])
    L += ["", "## 2b. Props gegen LiDAR-Boden (Klasse 2, ohne Deck/Gebaeude; Toleranz +0.6 / -0.9 m)",
          "- Props mit LiDAR-Messung: %d, auffällig: %d (%s)" % (sum(out.get("lidar_total", {}).values()), len(li), ", ".join("%s %d" % kv for kv in Counter(i["kind"] for i in li).most_common(6))),
          "- davon steht das Prop auf dem Spielboden (|z - hmap| < 0.35 m, also Gelaende weicht von LiDAR ab, Prop ist korrekt): %d; Prop selbst daneben: %d" % (sum(abs(i.get("pg", 9)) < 0.35 for i in li), sum(abs(i.get("pg", 9)) >= 0.35 for i in li)),
          "- schlechteste 8 (Art x,y dz Kachel): " + "; ".join("%s (%d,%d) %+.2f [%s]" % (i["kind"], i["x"], i["y"], i["dz"], i["tile"]) for i in sorted(li, key=lambda i: -abs(i["dz"]))[:8])]
    L += ["", "## Einordnung",
          "- Props: praktisch sauber (nur Stichproben-Ausreisser, siehe oben); Vegetation `wild` wird nicht geprüft (z hat dort andere Bedeutung).",
          "- Landmarks mit dz > 0: Bahnhöfe Hardbrücke/Wiedikon und Velotunnel liegen gewollt auf Viadukt bzw. im Tunnel (Gelände ist darunter); Hardau II -2 m: Gebäudesockel-Konvention (-3.06 m DTM).",
          "- Behoben: Ausschluss `pipeline/overrides/bridges_excl.json` (Kriterium: dup_sidewalk mit Höhen-Versatz >= 100% der Deckpunkte, siehe `mismatch`).",
          "- Nicht behoben (Beurteilung nötig): `no_obstacle` / `dangling` Stege ohne Höhenversatz. Meist echte Gehwege auf Strassenbrücken (z-fighting-frei, harmlos) oder Brücken über nicht kartierte Hindernisse (Böschung, Bach)."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    out = {}
    part1(out)
    part2(out)
    (R / "research/audit_float.json").write_text(json.dumps(out))
    (R / "research/audit_float.md").write_text(write(out))
    print((R / "research/audit_float.md").read_text()[:3500])
