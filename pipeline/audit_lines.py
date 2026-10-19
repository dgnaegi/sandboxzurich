"""Audit of the longitudinal road markings (centre lines, lane lines, yellow bike/bus lines) as built by streets.markings + markings_override.
usage: .venv/bin/python pipeline/audit_lines.py [--tag before|after] [--sheet]    -> data/build/lines_audit_<tag>.json, prints a summary
Per OSM axis (carriageway centre = streets.mline): sample the line every 0.25 m, run-length encode "paint present".
 centre lines (dashed 3/6): coverage (expect ~1/3 between junction gaps), stubs (< 1.5 m dashes), long gaps (> 7.5 m away from junction gaps / way ends of a dead end),
   dash-length spread, way-end gaps (gap across a way boundary where the street continues)
 bike/bus lines (solid): gaps > 3 m away from junction gaps and broken zones
 all lines: share of paint area outside the carriageway polygon (+5 cm)
--sheet: 10 ortho crops (SWISSIMAGE 0.25 m cache data/raw/ortho_025) with the game lines drawn in -> preview/lines_audit.jpg"""
import json, sys, pickle
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point

R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import os
if os.environ.get("AUDIT_STREETS_DIR"):   # run the audit against another copy of streets.py (e.g. git show HEAD:pipeline/streets.py)
    sys.path.insert(0, os.environ["AUDIT_STREETS_DIR"])
import sources, streets, markings_override

STEP = 0.25


def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        j = i
        while j < n and mask[j] == mask[i]:
            j += 1
        out.append((bool(mask[i]), i * STEP, j * STEP))
        i = j
    return out


def sample(line, geom):
    n = max(2, int(line.length / STEP))
    pts = shapely.line_interpolate_point(line, np.arange(n) * STEP)
    return shapely.contains_xy(geom, shapely.get_x(pts), shapely.get_y(pts))


def build():
    cache = R / "data/build/lines_S.pkl"   # parse takes 3-6 min: cached (delete after changes to streets.parse / carriageway.py)
    if cache.exists():
        S = pickle.load(open(cache, "rb"))
    else:
        nodes, els = sources.osm(); S = streets.parse(nodes, els)
        pickle.dump(S, open(cache, "wb"))
    white, yellow = streets.markings(S)
    white, yellow = markings_override.apply(S, white, yellow)
    return S, white, yellow


def near_gap(s, gaps, pad):
    return any(g0 - pad <= s <= g1 + pad for g0, g1 in gaps)


def audit(S, white, yellow):
    wsrc, ysrc = white, yellow
    white, yellow = white.buffer(0.3), yellow.buffer(0.3)   # presence test with 0.3 m tolerance (line position differs by cm between variants)
    shapely.prepare(white); shapely.prepare(yellow)
    res = {"centre": {}, "bike": {}, "outside": {}}
    tram = None
    ends = {}
    for w in S["ways"]:
        for n in (w["nodes"][0], w["nodes"][-1]):
            ends.setdefault(n, []).append(w)
    worst = []
    for w in S["ways"]:
        t = w["tags"]; L = w["line"].length
        if w["hw"] == "service" or w["zone"] in ("beg", "fuss") or L < 40:
            continue
        lanes = int(streets._num(t.get("lanes"), 0))
        ln = streets.mline(w)
        if w["hw"] in streets.MAIN and not w["oneway"] and w["w"] >= 7 and w["zone"] is None and w["tempo"] != 20 and lanes != 1:
            m = sample(ln, white.buffer(0.0) if False else white)
            # side lanes of a 4-lane road also hit; sample is at the centre only
            r = runs(m); k = res["centre"].setdefault(w["hw"], {"m": 0, "paint": 0, "stubs": 0, "longgaps": 0, "endgaps": 0, "dashes": 0, "ways": 0, "dash_len": []})
            k["ways"] += 1; k["m"] += ln.length; k["paint"] += sum(b - a for p, a, b in r if p)
            gaps = w["gaps"]
            for i, (p, a, b) in enumerate(r):
                interior = 0 < i < len(r) - 1
                if p:
                    k["dashes"] += 1
                    if (b - a) < 1.5 and interior:
                        k["stubs"] += 1
                    if interior and abs((b - a) - 3.0) < 1.6:
                        k["dash_len"].append(b - a)
                elif interior or True:
                    mid = (a + b) / 2
                    if (b - a) > 7.5 and not near_gap(mid, gaps, 5) and a > 3 and b < ln.length - 3:
                        k["longgaps"] += 1
                        worst.append((round(b - a, 1), "centre-gap", w["hw"], w["name"] if "name" in w else t.get("name"), [round(v, 1) for v in ln.interpolate(mid).coords[0]]))
                    # gap right across a way end whose node continues into another way (same street)
                    for end, node in ((0, w["nodes"][0]), (ln.length, w["nodes"][-1])):
                        if len(ends.get(node, [])) == 2 and a - 0.01 <= end <= b + 0.01 and (b - a) > 4.5 and not near_gap(end, gaps, 0):
                            k["endgaps"] += 1
        # solid yellow bike lines
        for side, solid, broken in streets.bike_lane_pieces(w):
            sgn = 1 if side == "left" else -1
            off = ln.offset_curve(sgn * (w["w"] / 2 - 1.5))
            if off.is_empty or off.geom_type != "LineString":
                continue
            k = res["bike"].setdefault(w["hw"], {"m": 0, "paint": 0, "longgaps": 0, "ways": 0})
            k["ways"] += 1
            for a, b in solid:
                if b - a < 6:
                    continue
                seg = streets._sub(off, a, b, L)
                if seg.length < 5:
                    continue
                r = runs(sample(seg, yellow)); k["m"] += seg.length; k["paint"] += sum(y - x for p, x, y in r if p)
                for p, x, y in r:
                    if not p and y - x > 3.0 and x > 1 and y < seg.length - 1:
                        k["longgaps"] += 1
                        worst.append((round(y - x, 1), "bike-gap", w["hw"], t.get("name"), [round(v, 1) for v in seg.interpolate((x + y) / 2).coords[0]]))
    # paint outside carriageway
    roads = shapely.set_precision(S["roads"].buffer(0.05), 0.01)
    for nm, g in (("white", wsrc), ("yellow", ysrc)):
        res["outside"][nm] = {"area": g.area, "outside": g.difference(roads).area}
    for k in res["centre"].values():
        d = k.pop("dash_len"); k["dash_mean"] = float(np.mean(d)) if d else 0; k["dash_sd"] = float(np.std(d)) if d else 0
    # way joins of one street (markings_lines chains): a centre line should run across them. hole = no paint within +-4 m of the join
    import markings_lines as ML
    jt = {"joins": 0, "holes": 0}
    for ch in ML.build_chains(S):
        for i in range(1, len(ch["ways"])):
            wa, wb = ch["ways"][i - 1][0], ch["ways"][i][0]
            if not all(w["hw"] in streets.MAIN and not w["oneway"] and w["w"] >= 7 and w["zone"] is None and w["tempo"] != 20 for w in (wa, wb)):
                continue
            j = ch["s0"][i]
            if any(abs(g0 - (wa["line"].length if True else 0)) < 12 or True for g0, g1 in []):
                pass
            gaps_near = [1 for w, jj in ((wa, wa["line"].length), (wb, 0.0)) for g0, g1 in w["gaps"] if g1 > jj - 12 and g0 < jj + 12]
            if gaps_near or min(wa["line"].length, wb["line"].length) < 20:
                continue
            jt["joins"] += 1
            seg = ch["line"].interpolate(j * ch["k"])
            near = ch["line"].buffer(0.01).intersection(seg.buffer(4.0))
            if not white.intersects(seg.buffer(4.0).intersection(ch["line"])):
                jt["holes"] += 1
    res["joins"] = jt
    worst.sort(reverse=True)
    res["worst"] = worst[:25]
    return res


def summary(res):
    for kind in ("centre", "bike"):
        for hw, k in res[kind].items():
            cov = k["paint"] / max(k["m"], 1)
            extra = " stubs=%d endgaps=%d dash=%.2f+-%.2f" % (k["stubs"], k["endgaps"], k["dash_mean"], k["dash_sd"]) if kind == "centre" else ""
            print("%-6s %-10s ways=%-4d km=%.1f coverage=%.2f longgaps=%d dashes=%s%s" % (kind, hw, k["ways"], k["m"] / 1000, cov, k["longgaps"], k.get("dashes", "-"), extra))
    print("way joins (no junction within 12 m): %(joins)d, centre line holes (no paint +-4 m): %(holes)d" % res["joins"])
    for nm, v in res["outside"].items():
        print("outside %s: %.0f of %.0f m2 (%.1f %%)" % (nm, v["outside"], v["area"], 100 * v["outside"] / max(v["area"], 1)))


def sheet(S, white, yellow, res):
    from PIL import Image, ImageDraw
    OX, OY, T, PX = 2681400, 1248700, 250.0, 1000
    spots = []
    for nm in ("Badenerstrasse", "Hardstrasse", "Langstrasse", "Birmensdorferstrasse", "Hohlstrasse", "Seebahnstrasse", "Weststrasse", "Rosengartenstrasse"):
        ws = sorted([w for w in S["ways"] if w["name"] == nm and w["w"] >= 7], key=lambda w: -w["line"].length)
        if ws:
            p = ws[0]["line"].interpolate(ws[0]["line"].length * 0.5); spots.append((p.x, p.y))
    spots += [tuple(w[4]) for w in res["worst"][:2]]
    tiles = []
    for (x, y) in spots[:10]:
        ix, iy = int(np.floor(x / T)), int(np.floor(y / T)); f = R / f"data/raw/ortho_025/o_{ix}_{iy}.jpg"
        if not f.exists():
            continue
        im = Image.open(f).convert("RGB"); px = (x - ix * T) * 4; py = (T - (y - iy * T)) * 4; h = 80
        im = im.crop((int(px - h), int(py - h), int(px + h), int(py + h))).resize((320, 320))
        tiles.append((im, x, y))
    W = Image.new("RGB", (320 * 5, 320 * 2 * ((len(tiles) + 4) // 5)), (30, 30, 30))
    for i, (im, x, y) in enumerate(tiles):
        pair = im.copy(); d = ImageDraw.Draw(pair)
        for g, col in ((white, (255, 60, 60)), (yellow, (60, 160, 255))):
            c = g.intersection(shapely.geometry.box(x - 20, y - 20, x + 20, y + 20))
            for p in shapely.get_parts(c):
                if p.geom_type == "Polygon" and len(p.exterior.coords) > 2:
                    d.polygon([((a - x) * 8 + 160, 160 - (b - y) * 8) for a, b in p.exterior.coords], outline=col)
        W.paste(im, ((i % 5) * 320, (i // 5) * 640)); W.paste(pair, ((i % 5) * 320, (i // 5) * 640 + 320))
    W.save(R / "preview/lines_audit.jpg", quality=80)


def buried(glbs):
    """Built tile meshes: how much line paint (layer 39 white/yellow triangles) lies BELOW the asphalt surface (layer 34) at the same x,y?
    Samples the triangle centroids and vertices of every marking triangle; asphalt height = barycentric interpolation of the asphalt triangle
    below. Returns {n, below_0mm (z_line - z_asphalt < 0), below_3mm (< 3 mm: z-fighting), mean_mm, p5_mm}."""
    import audit_markings as AM
    dz = []
    for f in glbs:
        g = AM.read_ground(f)
        if g is None:
            continue
        pos, col, lay, idx = g
        T = idx.reshape(-1, 3)
        asp = T[lay[T[:, 0]] == 34]
        mk = np.array([lay[t[0]] == 39 and AM.CLS.get(tuple(int(v) for v in col[t[0], :3])) in (2, 3) for t in T])
        mt = T[mk]
        if not len(asp) or not len(mt):
            continue
        P = pos[:, [0, 2]].astype(np.float64); Z = pos[:, 1]
        P[:, 1] = -P[:, 1]
        trees = shapely.STRtree(shapely.polygons(P[asp]))
        # sample points: centroids of marking triangles
        C = P[mt].mean(axis=1); zc = Z[mt].mean(axis=1)
        pts = shapely.points(C)
        qi, ti = trees.query(pts, predicate="within")
        best = {}
        for q, t in zip(qi, ti):
            a, b, c = P[asp[t]]
            M = np.array([[b[0] - a[0], c[0] - a[0]], [b[1] - a[1], c[1] - a[1]]])
            if abs(np.linalg.det(M)) < 1e-9:
                continue
            u, v = np.linalg.solve(M, C[q] - a)
            za = (1 - u - v) * Z[asp[t][0]] + u * Z[asp[t][1]] + v * Z[asp[t][2]]
            d = zc[q] - za
            if q not in best or abs(d) < abs(best[q]):   # decks / overlaps: nearest surface
                best[q] = d
        dz += list(best.values())
    dz = np.array(dz)
    if not len(dz):
        return {}
    return {"n": int(len(dz)), "below_0mm": float((dz < 0).mean()), "below_3mm": float((dz < 0.003).mean()), "mean_mm": float(dz.mean() * 1000), "p5_mm": float(np.percentile(dz, 5) * 1000)}


if __name__ == "__main__" and "--glb" in sys.argv:
    d = Path(sys.argv[sys.argv.index("--glb") + 1])
    print("buried paint", d, buried(sorted(d.glob("t_*.glb"))))
    sys.exit(0)

if __name__ == "__main__":
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "before"
    S, white, yellow = build()
    res = audit(S, white, yellow)
    json.dump(res, open(R / f"data/build/lines_audit_{tag}.json", "w"), indent=1)
    summary(res)
    if "--sheet" in sys.argv:
        sheet(S, white, yellow, res)
