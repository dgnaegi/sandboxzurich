"""Audit of bridge/ramp decks in the built tiles (web/public/tiles/t_*.json). Prints counts + worst places (<= 40 lines), writes the
full list as TSV (--tsv file). Usage: .venv/bin/python pipeline/audit_decks.py [--tsv out.tsv] [--top N]

Checks (per deck = one chain stored in a tile; chains crossing tile borders appear once per tile):
  steep   segment slope > limit (road 0.10, foot 0.16, tram 0.08)
  kink    slope change between neighbour segments > 0.10 (vertical profile twists)
  openend deck end clearly above ground (> 0.5 m) with no other deck end within 4 m at +-0.8 m height (vertical cut-off edge)
  stack   two decks side by side (parallel, centre distance < half widths + 1.5 m) with height difference 1.2..8 m (wedge slabs)
  buried  prop (lamp/bin/bench/sign/hydrant/bike) standing on the ground inside a solid deck footprint (skirt to the ground)
  pierce  tree whose crown reaches the deck underside (see audit_trees_deck.py)
Score = visibility: deck width * length weight + 3 if within 60 m of a zone camera / main street."""
import glob, json, math, sys
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

R = Path(__file__).resolve().parent.parent
LIM = {"road": 0.10, "foot": 0.16, "tram": 0.08, "rail": 0.15}
PROPS = ("lamps", "bins", "benches", "trafficsigns", "hydrants", "bikes", "bollards")


def load():
    decks, meta = [], {}
    for f in sorted(glob.glob(str(R / "web/public/tiles/t_*.json"))):
        m = json.load(open(f))
        t = Path(f).stem[2:]
        meta[t] = m
        for k, d in enumerate(m.get("bridges", {}).get("decks", [])):
            d["tile"], d["k"] = t, k
            d["P"] = np.array([q[:2] for q in d["p"]]); d["Z"] = np.array([q[2] for q in d["p"]])
            d["G"] = np.array(d["g"]); d["B"] = np.array(d["b"])
            d["s"] = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(d["P"], axis=0).T))])
            decks.append(d)
    return decks, meta


def cameras():
    try:
        zs = json.load(open(R / "pipeline/overrides/zones.json"))
    except Exception:
        return []
    out = []
    def walk(o):
        if isinstance(o, dict):
            if "x" in o and "y" in o and isinstance(o["x"], (int, float)):
                out.append((o["x"], o["y"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            if len(o) >= 2 and all(isinstance(v, (int, float)) for v in o[:2]) and abs(o[0]) < 5000:
                out.append((o[0], o[1]))
            else:
                for v in o:
                    walk(v)
    walk(zs)
    return out


def run():
    decks, meta = load()
    cams = np.array(cameras()) if cameras() else np.zeros((0, 2))
    res = []

    def add(kind, d, i, detail, sev):
        x, y = d["P"][i]
        vis = d["w"] * min(d["s"][-1], 200) / 100.0
        if len(cams):
            vis += 3.0 * (np.hypot(cams[:, 0] - x, cams[:, 1] - y).min() < 70)
        res.append((round(vis * sev, 2), kind, d["tile"], d["name"] or d["kind"], round(float(x)), round(float(y)), detail))

    ends = [(d["P"][e], d["Z"][e], id(d)) for d in decks for e in (0, -1)]
    et = STRtree([Point(*e[0]) for e in ends])
    for d in decks:
        P, Z, G, s = d["P"], d["Z"], d["G"], d["s"]
        if d["kind"] == "rail":
            continue
        dz, ds = np.diff(Z), np.maximum(np.diff(s), 1e-3)
        sl = dz / ds
        if d.get("st"):   # stairs (bridges._stairs) are steep by design; their end points are still checked (openend / stack)
            sl = sl * 0
        for i in np.where(np.abs(sl) > LIM[d["kind"]])[0]:
            add("steep", d, i, f"slope {sl[i]:.2f}", 1.0 + abs(sl[i]))
        for i in np.where(np.abs(np.diff(sl)) > 0.10)[0]:
            add("kink", d, i + 1, f"dslope {abs(sl[i + 1] - sl[i]):.2f}", 1.0 + 3 * abs(sl[i + 1] - sl[i]))
        for e in (0, -1):
            if Z[e] - G[e] < 0.5:
                continue
            ok = False
            for j in et.query(Point(*P[e]).buffer(4.0)):
                q, z, did = ends[j]
                if did != id(d) and abs(z - Z[e]) < 0.8:
                    ok = True
                    break
            if not ok:
                # a neighbour deck passing by (not at its end) also continues this one
                for o in decks:
                    if o is d or o["kind"] == "rail":
                        continue
                    ln = LineString(o["P"])
                    if ln.distance(Point(*P[e])) < o["w"] / 2 + 1.0:
                        t = ln.project(Point(*P[e]))
                        if abs(np.interp(t, o["s"], o["Z"]) - Z[e]) < 0.8:
                            ok = True
                            break
            if not ok:
                add("openend", d, e if e == 0 else len(P) - 1, f"end {Z[e] - G[e]:.1f} m above ground", 1.0 + (Z[e] - G[e]) / 3)
    # stacks (parallel decks at different heights)
    lines = [LineString(d["P"]) for d in decks]
    tr = STRtree(lines)
    seen = set()
    for a, d in enumerate(decks):
        for b in tr.query(lines[a].buffer(d["w"] / 2 + 6)):
            if b <= a or (decks[b]["tile"] != d["tile"] and False):
                continue
            o = decks[b]
            if o["kind"] == "rail" or d["kind"] == "rail":
                continue
            n = 0; worst = 0.0; at = 0
            for i in range(0, len(d["P"])):
                pt = Point(*d["P"][i]); dist = lines[b].distance(pt)
                if dist < (d["w"] + o["w"]) / 2 + 1.5:
                    t = lines[b].project(pt)
                    zo = np.interp(t, o["s"], o["Z"])
                    # parallel only
                    a0 = lines[b].interpolate(max(t - 2, 0)); a1 = lines[b].interpolate(min(t + 2, lines[b].length))
                    e = np.array([a1.x - a0.x, a1.y - a0.y]); v = d["P"][min(i + 1, len(d["P"]) - 1)] - d["P"][max(i - 1, 0)]
                    if abs(v @ e) / (np.hypot(*v) * np.hypot(*e) + 1e-9) < 0.9:
                        continue
                    dzz = abs(zo - d["Z"][i])
                    if 1.2 < dzz < 8.0:
                        n += 1
                        if dzz > worst:
                            worst, at = dzz, i
            if n >= 3 and (d["tile"], round(d["P"][at][0]), round(d["P"][at][1])) not in seen:
                seen.add((d["tile"], round(d["P"][at][0]), round(d["P"][at][1])))
                add("stack", d, at, f"{o['name'] or o['kind']}({o['kind']}) beside, dz {worst:.1f} over {n} vertices", 1.0 + worst / 3)
    # props buried in solid decks / trees piercing
    segs, segd = [], []
    for d in decks:
        if d["kind"] == "rail":
            continue
        for i in range(len(d["P"]) - 1):
            if min(d["Z"][i] - d["G"][i], d["Z"][i + 1] - d["G"][i + 1]) < 0.3:
                continue
            segs.append(LineString(d["P"][i:i + 2]).buffer(d["w"] / 2 + 0.2, cap_style="flat")); segd.append((d, i))
    st = STRtree(segs)
    for t, m in meta.items():
        for key in PROPS:
            for o in m.get(key, []):
                x, y, z = o[0], o[1], o[2]
                for j in st.query(Point(x, y)):
                    if not segs[j].contains(Point(x, y)):
                        continue
                    d, i = segd[j]
                    g = float(np.interp(0.5, [0, 1], d["G"][i:i + 2])); zd = float(np.interp(0.5, [0, 1], d["Z"][i:i + 2]))
                    bot = float(np.interp(0.5, [0, 1], d["B"][i:i + 2]))
                    if abs(z - g) < 0.6 and bot <= g + 0.1 and zd - g > 0.6:
                        add("buried", d, i, f"{key} at ground inside solid deck ({x:.0f},{y:.0f}) deck {zd - g:.1f} m above", 1.2)
                    break
        for o in m.get("trees", []):
            x, y, z, _, dc, h = o[:6]
            for j in st.query(Point(x, y).buffer(dc * 0.25)):
                d, i = segd[j]
                bot = float(min(d["B"][i:i + 2]))
                if segs[j].intersects(Point(x, y).buffer(dc * 0.25)) and z + h > bot - 0.1 and z < bot:
                    add("pierce", d, i, f"tree ({x:.0f},{y:.0f}) top {z + h - bot:.1f} m above underside", 1.1)
                    break
    return res


if __name__ == "__main__":
    res = run()
    res.sort(key=lambda r: -r[0])
    from collections import Counter
    c = Counter(r[1] for r in res)
    print(f"{len(res)} findings {dict(c)}")
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 30
    for r in res[:top]:
        print("\t".join(map(str, r)))
    if "--tsv" in sys.argv:
        with open(sys.argv[sys.argv.index("--tsv") + 1], "w") as f:
            f.write("score\tkind\ttile\tname\tx\ty\tdetail\n")
            for r in res:
                f.write("\t".join(map(str, r)) + "\n")
