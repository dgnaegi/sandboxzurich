"""Swiss traffic signs (SSV) and traffic signals derived from OSM tags (ODbL).

sign_rows(area, H)   -> [x, y, z, heading, code]   heading = facing angle (rad, local x=east, y=north); z = ground
signal_rows(area, H) -> [x, y, z, heading, kind]   kind: car | ped | bike
Rows are meant to be split per tile in build_testarea.py (see research/traffic_signs.md).
"""
import math
from collections import Counter, defaultdict

import numpy as np

from streets import WIDTH

MAIN = {"primary", "secondary", "tertiary"}
LOCAL = {"residential", "unclassified", "living_street"}
EDGE = 0.6  # distance sign pole <-> kerb


def _load(area, nodes=None, els=None):
    if nodes is None:
        import sources
        nodes, els = sources.osm()
    x0, y0, x1, y1 = area
    m = 60
    inside = lambda p: x0 - m <= p[0] <= x1 + m and y0 - m <= p[1] <= y1 + m
    ways, nodetags = [], {}
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "node" and t and e["id"] in nodes and inside(nodes[e["id"]]):
            if t.get("highway") in ("stop", "give_way", "traffic_signals", "crossing") or t.get("crossing"):
                nodetags[e["id"]] = t
        elif e["type"] == "way" and "highway" in t and len(e.get("nodes", [])) >= 2:
            if t.get("tunnel") in ("yes", "building_passage") or str(t.get("layer", "0")).startswith("-"):
                continue
            ids = [n for n in e["nodes"] if n in nodes]
            if len(ids) >= 2 and any(inside(nodes[n]) for n in ids):
                ways.append({"id": e["id"], "ids": ids, "pts": np.array([nodes[n] for n in ids]), "t": t})
    return nodes, ways, nodetags


def _w(t):
    hw = t.get("highway")
    try:
        return float(str(t["width"]).split()[0])
    except (KeyError, ValueError):
        return WIDTH.get(hw, 0)


def _speed(t):
    if t.get("maxspeed:type") == "CH:zone30" or t.get("source:maxspeed") == "CH:zone30":
        return 30
    try:
        return int(t.get("maxspeed", ""))
    except ValueError:
        return None


def _dir(pts, i, step=1):
    """Unit travel direction at vertex i heading to i+step (step=+1 along way, -1 reverse)."""
    j = min(max(i + step, 0), len(pts) - 1)
    v = pts[j] - pts[i]
    n = np.hypot(*v)
    return v / n if n > 1e-6 else np.array([1.0, 0.0])


def _place(p, d, half, along=0.0, side=1.0):
    """Pole position right of travel direction d at point p; sign faces oncoming traffic (-d)."""
    right = np.array([d[1], -d[0]])
    q = np.asarray(p) + d * along + right * side * (half + EDGE)
    return q, math.atan2(-d[1], -d[0])


def oneway_only_back(t):
    return t.get("oneway") == "-1"


def _regime_signs(w, hw, half, oneway, L, add):
    """Signs where a way crosses an official zone / speed-regime boundary (streets_rules.events)."""
    import streets_rules as SR
    from shapely.geometry import LineString
    pts = w["pts"]
    d0, d1 = pts[0] - pts[1], pts[-1] - pts[-2]
    d0, d1 = d0 / (np.hypot(*d0) + 1e-9), d1 / (np.hypot(*d1) + 1e-9)
    ln = LineString(np.vstack([pts[0] + d0 * 12, pts, pts[-1] + d1 * 12]))
    L = ln.length - 24
    for s, prev, new in SR.events(np.asarray(ln.coords)):
        s -= 12.0
        for sgn, enter, leave in ((1, new, prev), (-1, prev, new)):
            if oneway and sgn < 0:
                continue
            code = None
            if enter == "z30" and leave != "z30":
                code = "zone30"
            elif leave == "z30" and enter not in ("z30", "beg", "fuss"):
                code = "zone30end"
            elif enter == "beg" and leave != "beg":
                code = "begegnung"
            elif leave == "beg" and enter not in ("beg", "z30", "fuss"):
                code = "begegnungend"
            elif enter == "t30" and leave not in ("z30", "t30", "beg") and hw in MAIN:
                code = "speed30"
            elif leave in ("t30", "t20") and enter in ("", "t50") and hw in MAIN:
                code = "speed50"
            elif enter == "t50" and leave in ("t30", "t20"):
                code = "speed50"
            if not code:
                continue
            ss = min(max(s, 6.0), L - 6.0) + 12.0
            a, b = ln.interpolate(max(0, ss - 1)), ln.interpolate(min(ln.length, ss + 1))
            d = np.array([b.x - a.x, b.y - a.y]) * sgn
            d /= np.hypot(*d) + 1e-9
            q, h = _place(np.array(ln.interpolate(ss).coords[0]), d, half, 0.0)
            add(q, h, code)


def sign_rows(area, H, nodes=None, els=None):
    nodes, ways, ntags = _load(area, nodes, els)
    x0, y0, x1, y1 = area
    rows = []

    def add(q, h, code):
        if x0 <= q[0] < x1 and y0 <= q[1] < y1:
            rows.append([round(float(q[0]), 2), round(float(q[1]), 2), round(float(H.at(q[0], q[1])), 2),
                         round(h, 3), code])

    roads = [w for w in ways if w["t"]["highway"] in WIDTH and w["t"]["highway"] not in ("service",)]
    deg = Counter(n for w in ways if w["t"]["highway"] in WIDTH for n in w["ids"])
    at_node = defaultdict(list)
    for w in roads:
        for i, n in enumerate(w["ids"]):
            at_node[n].append((w, i))

    for w in roads:
        t, ids, pts = w["t"], w["ids"], w["pts"]
        hw, half = t["highway"], _w(t) / 2
        L = float(np.hypot(*np.diff(pts, axis=0).T).sum())
        a, b = ids[0], ids[-1]
        sp = _speed(t)
        oneway = t.get("oneway") == "yes"
        # Zone 30 / Begegnungszone / signalised Tempo 30 and its end: from the official zones and speed regimes
        if hw in LOCAL | MAIN and L > 20 and not oneway_only_back(t):
            _regime_signs(w, hw, half, oneway, L, add)
        # one-way: Einbahn at the entrance, Einfahrt verboten at the exit (facing wrong-way traffic)
        if oneway and hw in LOCAL | {"tertiary", "secondary"} and L > 20:
            if deg[a] >= 2:
                q, h = _place(pts[0], _dir(pts, 0, 1), half, 5)
                add(q, h, "einbahn")
            if deg[b] >= 2:
                d = _dir(pts, len(pts) - 1, -1)  # direction of wrong-way traffic entering at the end
                q, h = _place(pts[-1], d, half, 4)
                add(q, h, "einfahrt_verboten")
        # Fahrverbot (no motor vehicles, but not just private/destination)
        t_mv = t.get("motor_vehicle") or t.get("access")
        if t_mv == "no" and hw in LOCAL | {"service", "track", "path"} and L > 15 and deg[a] >= 2 and not oneway:
            q, h = _place(pts[0], _dir(pts, 0, 1), max(half, 1.5), 3)
            add(q, h, "fahrverbot")
        # Sackgasse: junction end of a long local street whose other end is a dead end
        if hw in LOCAL and L > 40 and not oneway and t.get("access") not in ("private", "no"):
            for end, n, other in ((0, a, b), (1, b, a)):
                if deg[n] >= 2 and deg[other] == 1:
                    d = _dir(pts, 0, 1) if end == 0 else _dir(pts, len(pts) - 1, -1)
                    q, h = _place(pts[0 if end == 0 else -1], d, half, 4)
                    add(q, h, "sackgasse")
        # blue zone / no parking at the start of a street
        if hw in LOCAL | MAIN and L > 40 and not oneway:
            if t.get("parking:condition") == "disc" or "parking:zone" in t:
                q, h = _place(pts[0], _dir(pts, 0, 1), half, 8)
                add(q, h, "blauzone")
            elif hw in MAIN and "no" in (t.get("parking:both"), t.get("parking:lane:both")):
                q, h = _place(pts[0], _dir(pts, 0, 1), half, 8)
                add(q, h, "halteverbot")
            elif t.get("parking:lane:both") in ("parallel", "perpendicular", "diagonal") and hw in LOCAL and L > 60:
                q, h = _place(pts[0], _dir(pts, 0, 1), half, 8)
                add(q, h, "parkieren")
        # cycleway / footway entrances
        if hw == "cycleway" and t.get("bicycle", "designated") == "designated" and L > 40:
            for end in (0, 1):
                d = _dir(pts, 0, 1) if end == 0 else _dir(pts, len(pts) - 1, -1)
                q, h = _place(pts[0 if end == 0 else -1], d, 1.5, 0.5)
                add(q, h, "radweg")
        if hw == "footway" and "footway" not in t and L > 40 and t.get("foot") != "no" \
                and t.get("bicycle") in ("no", "dismount", None) and "name" in t:
            q, h = _place(pts[0], _dir(pts, 0, 1), 1.2, 0.5)
            add(q, h, "fussweg")

    # stop / give way / pedestrian crossings on road nodes
    for n, t in ntags.items():
        cand = at_node.get(n, [])
        if not cand:
            continue
        if t.get("highway") in ("stop", "give_way"):
            fwd = t.get("direction", "forward") != "backward"
            w, i = cand[0]
            pts = w["pts"]
            d = _dir(pts, i, -1) * -1 if False else (_dir(pts, max(i - 1, 0), 1) if fwd else _dir(pts, min(i + 1, len(pts) - 1), -1))
            if i == 0 and fwd:
                d = _dir(pts, 0, 1)
            q, h = _place(nodes[n], d, _w(w["t"]) / 2, -1.0)
            add(q, h, "stop" if t["highway"] == "stop" else "vortritt")
        elif t.get("highway") == "crossing" and t.get("crossing:markings") != "no" and t.get("crossing") in ("zebra", "marked", "uncontrolled") \
                or t.get("crossing_ref") == "zebra" or t.get("crossing:markings") == "zebra" and t.get("crossing") != "traffic_signals":
            import streets_rules as SR
            R = SR.rules()
            zone = R.zone_point(*nodes[n])
            if zone in ("beg", "fuss"):
                continue
            if zone == "z30" and not R.near_school(*nodes[n], 40):
                w0, i0 = cand[0]
                d0 = _dir(w0["pts"], max(i0 - 1, 0), 1)
                if R.tempo_at(np.array([nodes[n]]), np.array([d0]))[0] != 30:
                    continue  # no Fussgängerstreifen inside Zone 30 (only on signalised T30 streets / school crossings)
            for w, i in cand[:1]:
                hw = w["t"]["highway"]
                if hw not in WIDTH or hw in ("service",) or deg[n] > 2:
                    continue
                pts = w["pts"]
                half = _w(w["t"]) / 2
                d = _dir(pts, max(i - 1, 0), 1) if i > 0 else _dir(pts, 0, 1)
                q, h = _place(nodes[n], d, half, -3.0)
                add(q, h, "fussgaenger")
                if w["t"].get("oneway") != "yes":
                    q, h = _place(nodes[n], -d, half, -3.0)
                    add(q, h, "fussgaenger")
    # dedupe (same code within 3 m)
    out, seen = [], []
    for r in rows:
        if any(r[4] == s[4] and abs(r[0] - s[0]) < 3 and abs(r[1] - s[1]) < 3 for s in seen):
            continue
        seen.append(r)
        out.append(r)
    print("traffic signs:", len(out), ", ".join(f"{k} {v}" for k, v in Counter(r[4] for r in out).most_common(20)))
    return out


def signal_rows(area, H, nodes=None, els=None):
    nodes, ways, ntags = _load(area, nodes, els)
    x0, y0, x1, y1 = area
    rows = []

    def add(q, h, kind):
        if x0 <= q[0] < x1 and y0 <= q[1] < y1:
            rows.append([round(float(q[0]), 2), round(float(q[1]), 2), round(float(H.at(q[0], q[1])), 2),
                         round(h, 3), kind])

    roads = [w for w in ways if w["t"]["highway"] in WIDTH and w["t"]["highway"] != "service"]
    at_node = defaultdict(list)
    for w in roads:
        for i, n in enumerate(w["ids"]):
            at_node[n].append((w, i))
    for n, t in ntags.items():
        mid = t.get("highway") == "crossing" and t.get("crossing") == "traffic_signals"
        if not (t.get("highway") == "traffic_signals" or mid):
            continue
        p = np.array(nodes[n])
        arms = []  # (travel direction toward node, half width, has bike lane, oneway)
        for w, i in at_node.get(n, []):
            pts, tg = w["pts"], w["t"]
            half = _w(tg) / 2
            cyc = any(tg.get(k, "") in ("lane", "track") for k in ("cycleway", "cycleway:right", "cycleway:left", "cycleway:both"))
            if i > 0 and tg.get("oneway") != "-1":
                arms.append((_dir(pts, i, -1) * -1, half, cyc))
            if i < len(pts) - 1 and tg.get("oneway") != "yes":
                arms.append((_dir(pts, i, 1) * -1, half, cyc))
        if mid:  # mid-block crossing: pedestrian lights on both kerbs facing the crossing
            for d, half, cyc in arms[:2]:
                q, h = _place(p, d, half, -2.5)
                add(q, h, "car")
                right = np.array([d[1], -d[0]])
                for s in (1, -1):
                    pos = p + right * s * (half + EDGE) + d * 1.5
                    add(pos, math.atan2(-s * right[1], -s * right[0]), "ped")
                break
            continue
        for d, half, cyc in arms:
            q, h = _place(p, d, half, -2.5)
            add(q, h, "car")
            right = np.array([d[1], -d[0]])
            if cyc:
                add(q + d * -0.2 + right * 0.0, h, "bike")
            # pedestrian light on the same pole line, facing across the arm (towards the right-hand crossing)
            if len(arms) >= 3:
                pos = p + d * -3.5 + right * (half + EDGE)
                add(pos, math.atan2(right[1], right[0]) + math.pi, "ped")
    out, seen = [], set()
    for r in rows:
        k = (round(r[0] / 1.5), round(r[1] / 1.5), r[4])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    print("signals:", len(out), ", ".join(f"{k} {v}" for k, v in Counter(r[4] for r in out).items()))
    return out


if __name__ == "__main__":
    from config import AREA
    from terrain import heights
    H = heights(AREA, 2.0, z_shift=-3.06)
    s = sign_rows(AREA, H)
    g = signal_rows(AREA, H)
