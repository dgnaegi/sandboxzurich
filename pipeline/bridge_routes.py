"""Ride routes over every bridge/ramp for web/tests/bridges_ride.mjs -> logs/bridge_routes.json.
Connected components of roads.json edges with a deck z (cars, bikes), longest path through the component,
extended 60 m onto the ground at both ends. Names come from the nearest deck row in the tile meta."""
import glob
import json
import math
import os
from collections import defaultdict

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(f"{ROOT}/web/public/data/roads.json"))
nodes = R["nodes"]

decks = []
for f in glob.glob(f"{ROOT}/web/public/tiles/t_*.json"):
    m = json.load(open(f)).get("bridges") or {}
    for d in m.get("decks", []):
        if d["kind"] in ("road", "foot") and d.get("name"):
            decks.append((np.array(d["p"])[:, :2].mean(0), d["name"]))
for f in ("hb_decks.json", "station_decks.json"):
    for d in json.load(open(f"{ROOT}/web/public/data/{f}")).get("decks", []):
        decks.append((np.array(d["p"])[:, :2].mean(0), d.get("name", "")))
dc = np.array([c for c, _ in decks])


def name_at(x, y):
    d = np.hypot(dc[:, 0] - x, dc[:, 1] - y)
    i = int(d.argmin())
    return decks[i][1] if d[i] < 120 else ""


def pts_of(e):
    p = e["p"]
    return [(p[i], p[i + 1]) for i in range(0, len(p), 2)]


def build(kind):
    E = R[kind]
    adj = defaultdict(list)
    for i, e in enumerate(E):
        adj[e["a"]].append((i, e["b"]))
        adj[e["b"]].append((i, e["a"]))
    deck = [i for i, e in enumerate(E) if e.get("z") and any(v is not None for v in e["z"])]
    seen, out = set(), []
    for s in deck:
        if s in seen:
            continue
        comp, st = [], [s]
        seen.add(s)
        while st:
            i = st.pop(); comp.append(i)
            for n in (E[i]["a"], E[i]["b"]):
                for j, _ in adj[n]:
                    if j in deck and j not in seen:
                        seen.add(j); st.append(j)
        dset = set(comp)

        def bfs(n0):
            dist, prev, q = {n0: 0.0}, {}, [n0]
            while q:
                n = q.pop(0)
                for j, m in adj[n]:
                    if j in dset and m not in dist:
                        dist[m] = dist[n] + 1; prev[m] = (n, j); q.append(m)
            return dist, prev
        n0 = E[comp[0]]["a"]
        d0, _ = bfs(n0)
        nA = max(d0, key=d0.get)
        dA, prev = bfs(nA)
        nB = max(dA, key=dA.get)
        path, n = [], nB
        while n != nA:
            pn, j = prev[n]; path.append((j, n)); n = pn
        path.reverse()
        poly = []
        cur = nA
        for j, nxt in path:
            e = E[j]
            pp = pts_of(e)
            if e["a"] != cur:
                pp = pp[::-1]
            poly += pp if not poly else pp[1:]
            cur = nxt
        # extend 60 m at both ends along the straightest non-deck edge
        def ext(poly, node):
            L = 0.0
            used = set(path_ids)
            while L < 60:
                best = None
                for j, m in adj[node]:
                    if j in used:
                        continue
                    pp = pts_of(E[j])
                    if E[j]["a"] != node:
                        pp = pp[::-1]
                    a = np.array(poly[-1]) - np.array(poly[-2]); b = np.array(pp[1]) - np.array(pp[0])
                    c = float(a @ b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
                    if best is None or c > best[0]:
                        best = (c, j, m, pp)
                if not best or best[0] < 0.3:
                    break
                _, j, m, pp = best
                used.add(j)
                for q in pp[1:]:
                    L += math.hypot(q[0] - poly[-1][0], q[1] - poly[-1][1]); poly.append(q)
                node = m
            return poly
        path_ids = {j for j, _ in path}
        poly = ext(poly, nB)
        poly = ext(poly[::-1], nA)[::-1]
        length = sum(math.hypot(poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]) for i in range(len(poly) - 1))
        zs = [v for j in comp for v in (E[j].get("z") or []) if v is not None]
        mid = poly[len(poly) // 2]
        out.append({"kind": kind, "name": name_at(*mid) or f"{kind} {mid[0]:.0f},{mid[1]:.0f}", "pts": [[round(a, 1), round(b, 1)] for a, b in poly],
                    "len": round(length), "zmax": max(zs)})
    return out


res = build("cars") + build("bikes")
res = [r for r in res if r["len"] > 40]
json.dump(res, open(f"{ROOT}/logs/bridge_routes.json", "w"))
for r in sorted(res, key=lambda r: -r["len"]):
    print(r["kind"], r["name"][:30], r["len"], r["pts"][0])
print(len(res))
