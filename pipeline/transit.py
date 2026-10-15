"""Build tram/bus lines (from OSM route relations) clipped to the test area -> web/public/data/transit.json."""
import json
import math
from collections import defaultdict

from config import AREA, ROOT
import sources

MARGIN = 300.0
OUT = ROOT / "web" / "public" / "data" / "transit.json"
MODES = {"tram": "tram", "bus": "bus", "trolleybus": "trolleybus"}
BOX = (AREA[0] - MARGIN, AREA[1] - MARGIN, AREA[2] + MARGIN, AREA[3] + MARGIN)


def inside(p):
    return BOX[0] <= p[0] <= BOX[2] and BOX[1] <= p[1] <= BOX[3]


def chain(ways):
    """Chain way node-id lists in member order into runs of node ids (gaps start a new run)."""
    runs, cur = [], []
    for w in ways:
        if not cur:
            cur = list(w)
            continue
        if cur[-1] == w[0]:
            cur += w[1:]
        elif cur[-1] == w[-1]:
            cur += w[::-1][1:]
        else:
            runs.append(cur)
            cur = list(w)
    if cur:
        runs.append(cur)
    return runs


def first_orient(ways):
    """Orient the first way so that it joins the second one."""
    if len(ways) >= 2:
        a, b = ways[0], ways[1]
        if a[0] in (b[0], b[-1]) and a[-1] not in (b[0], b[-1]):
            ways[0] = a[::-1]
    return ways


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def best_run(pts):
    """Longest contiguous in-box run of a point list."""
    runs, cur = [], []
    for p in pts:
        if inside(p):
            cur.append(p)
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    return max(runs, key=plen) if runs else []


def project(pts, cum, q):
    """Nearest point on polyline: (distance, s)."""
    best = (1e9, 0.0)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]; bx, by = pts[i + 1]
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy or 1e-9
        t = max(0, min(1, ((q[0] - ax) * dx + (q[1] - ay) * dy) / l2))
        d = math.hypot(ax + t * dx - q[0], ay + t * dy - q[1])
        if d < best[0]:
            best = (d, cum[i] + t * math.sqrt(l2))
    return best


def main():
    nodes, els = sources.osm()
    ways = {e["id"]: e["nodes"] for e in els if e["type"] == "way"}
    ntags = {e["id"]: e.get("tags", {}) for e in els if e["type"] == "node" and e.get("tags")}
    cands = defaultdict(list)
    for r in els:
        t = r.get("tags", {})
        if r["type"] != "relation" or t.get("route") not in MODES or not t.get("ref") or t["ref"].startswith("N"):  # night lines skipped
            continue
        wl = [[n for n in ways[m["ref"]] if n in nodes] for m in r["members"]
              if m["type"] == "way" and m["ref"] in ways and m["role"] in ("", "forward", "backward")]
        wl = [w for w in wl if len(w) >= 2]
        if not wl:
            continue
        runs = chain(first_orient(wl))
        run = max(runs, key=lambda ids: plen([nodes[i] for i in ids]))
        pts = best_run([nodes[i] for i in run])
        # drop duplicate consecutive points
        pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        if len(pts) < 2 or plen(pts) < 150:
            continue
        # only lines that really touch the core test area
        if not any(AREA[0] <= p[0] <= AREA[2] and AREA[1] <= p[1] <= AREA[3] for p in pts):
            continue
        cum = [0.0]
        for i in range(len(pts) - 1):
            cum.append(cum[-1] + math.dist(pts[i], pts[i + 1]))
        stops = []
        for m in r["members"]:
            if m["type"] == "node" and m["role"].startswith("stop") and m["ref"] in nodes:
                d, s = project(pts, cum, nodes[m["ref"]])
                name = ntags.get(m["ref"], {}).get("name", "").replace("Zürich, ", "")
                if d < 30 and name and not any(abs(s - x["s"]) < 40 or x["name"] == name for x in stops):
                    stops.append({"name": name, "s": round(s, 1)})
        stops.sort(key=lambda x: x["s"])
        if not stops:
            continue
        cands[(t["route"], t["ref"])].append({
            "ref": t["ref"], "mode": MODES[t["route"]], "colour": t.get("colour", "#1f4e8c"),
            "pts": [[round(x, 1), round(y, 1)] for x, y in pts], "stops": stops, "len": cum[-1]})
    lines = []
    for key, vs in sorted(cands.items()):
        groups = []  # direction groups by chord direction
        for v in vs:
            p = v["pts"]; ch = (p[-1][0] - p[0][0], p[-1][1] - p[0][1])
            for g in groups:
                if ch[0] * g[0][0] + ch[1] * g[0][1] > 0:
                    g[1].append(v); break
            else:
                groups.append((ch, [v]))
        for gi, (_, g) in enumerate(groups[:2]):
            v = max(g, key=lambda a: (len(a["stops"]), a["len"]))
            v["dir"] = gi
            del v["len"]
            lines.append(v)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"lines": lines}, open(OUT, "w"), separators=(",", ":"))
    print(f"{len(lines)} lines -> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} kB)")
    for ref in sorted({l['ref'] for l in lines}, key=lambda r: (not r.isdigit(), r.rjust(4))):
        ls = [l for l in lines if l["ref"] == ref]
        print(ref.ljust(8), ls[0]["mode"].ljust(10), " ".join(f"d{l['dir']}:{plen(l['pts']) :.0f}m/{len(l['stops'])}H" for l in ls))


if __name__ == "__main__":
    main()
