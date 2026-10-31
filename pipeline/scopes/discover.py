"""Site discovery: every group of elevated road deck chains that no hand-defined site (ramp_sites.SITES) covers becomes an
automatic site -> data/build/scopes/auto_sites.json (read by ramp_sites.site()).

  python3 pipeline/scopes/discover.py [--tiles web/public/tiles] [--min-el 2.0] [--lidar]
A group is a connected set of chains (pipeline/ramp_lidar.chains_of on the live road rows) with the same name, or unnamed
chains connected to each other; it is kept when one of its chains rises at least --min-el above the game terrain over 30 m
or more. Automatic sites select their rows by signature (rows.row_sig), not by name. --lidar prints the missing LiDAR tiles.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import ramp_lidar as RL  # noqa: E402
from ramp_sites import AUTO, SITES, site as site_cfg  # noqa: E402
from rows import Rows, row_sig  # noqa: E402

OX, OY, T = 2681400, 1248700, 500
JOIN = 3.0
PARALLEL = 6.0   # m


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "unnamed"


def turning(P):
    """Total absolute heading change along a polyline, degrees (a parking-garage helix turns > 300)."""
    v = np.diff(P, axis=0); v = v[np.hypot(v[:, 0], v[:, 1]) > 0.3]
    if len(v) < 2:
        return 0.0
    a = np.unwrap(np.arctan2(v[:, 1], v[:, 0]))
    return float(np.degrees(np.abs(np.diff(a)).sum()))


def main():
    tiles = sys.argv[sys.argv.index("--tiles") + 1] if "--tiles" in sys.argv else os.path.join(ROOT, "web", "public", "tiles")
    min_el = float(sys.argv[sys.argv.index("--min-el") + 1]) if "--min-el" in sys.argv else 2.0
    R = Rows(tiles, "live")
    taken = set()
    for n in SITES:
        for c in R.site_chains(site_cfg(n)):
            taken |= {row_sig(d) for _, _, d in c.rows}
    rows = [(t, k, d) for t, k, d in R.decks() if d["kind"] == "road" and row_sig(d) not in taken]
    chains = RL.chains_of(rows)
    info = []
    for c in chains:
        P = np.vstack([np.array(d["p"], float) for _, _, d in c]); G = np.concatenate([d["g"] for _, _, d in c])
        L = sum(float(np.hypot(*np.diff(np.array(d["p"], float)[:, :2], axis=0).T).sum()) for _, _, d in c)
        info.append({"rows": c, "P": P, "name": c[0][2].get("name") or "", "el": float((P[:, 2] - G).max()), "len": L})
    # connected components: same name (or both unnamed), an end within JOIN of any vertex of the other
    n = len(info); parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            if info[i]["name"] != info[j]["name"]:
                continue
            A, B = info[i]["P"][:, :2], info[j]["P"][:, :2]
            ends = np.vstack([A[[0, -1]], B[[0, -1]]])
            if min(np.hypot(B[:, 0] - e[0], B[:, 1] - e[1]).min() for e in A[[0, -1]]) < JOIN or \
               min(np.hypot(A[:, 0] - e[0], A[:, 1] - e[1]).min() for e in B[[0, -1]]) < JOIN:
                parent[find(i)] = find(j)
    # parallel chains on one structure (split carriageways, a middle lane): an axis that runs inside another chain's live
    # footprint widened by PARALLEL over >= 30 % of its length belongs to the same site, whatever the name
    from shapely.geometry import LineString
    from join import footprint
    fps = []
    for x in info:
        P = x["P"][:, :2]; w = np.concatenate([np.array(d.get("wl") or [d["w"] / 2] * len(d["p"]), float) for _, _, d in x["rows"]])
        wr = np.concatenate([np.array(d.get("wr") or [d["w"] / 2] * len(d["p"]), float) for _, _, d in x["rows"]])
        keep = np.r_[True, np.hypot(*np.diff(P, axis=0).T) > 0.05]
        fps.append(footprint(P[keep], w[keep], wr[keep]).buffer(PARALLEL))
    for i in range(n):
        ax = LineString(info[i]["P"][:, :2])
        for j in range(n):
            if i != j and find(i) != find(j) and ax.intersection(fps[j]).length >= 0.3 * ax.length:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(info[i])
    out, used = {}, set()
    for g in sorted(groups.values(), key=lambda g: -sum(x["len"] for x in g)):
        if max(x["el"] for x in g) < min_el or sum(x["len"] for x in g) < 30:
            continue
        P = np.vstack([x["P"] for x in g])
        x0, y0 = P[:, :2].min(0); x1, y1 = P[:, :2].max(0)
        names = sorted({x["name"] for x in g if x["name"]}, key=lambda m: -sum(x["len"] for x in g if x["name"] == m))
        name = names[0] if names else ""
        key = "auto_" + (slug(name) if name else f"unnamed_{(x0 + x1) / 2:.0f}_{(y0 + y1) / 2:.0f}".replace("-", "m"))
        k2, i = key, 2
        while k2 in used:
            k2 = f"{key}_{i}"; i += 1
        used.add(k2)
        out[k2] = {"title": (name or "unnamed elevated road") + f" ({len(g)} chain{'s' if len(g) > 1 else ''}, {sum(x['len'] for x in g):.0f} m)",
                   "match": name, "kinds": ["road"], "names": names, "sigs": [list(row_sig(d)) for x in g for _, _, d in x["rows"]],
                   "fetch": [round(x0 - 40), round(y0 - 40), round(x1 + 40), round(y1 + 40)],
                   "view": [round(x0 - 20), round(y0 - 20), round(x1 + 20), round(y1 + 20)],
                   "max_el": round(max(x["el"] for x in g), 1), "length": round(sum(x["len"] for x in g)),
                   "shape": "helix" if max(turning(x["P"][:, :2]) for x in g) > 300 else "ramp"}
    os.makedirs(os.path.dirname(AUTO), exist_ok=True)
    json.dump(out, open(AUTO, "w"), ensure_ascii=False, indent=1)
    print(f"{len(out)} automatic sites (hand sites {len(SITES)} cover {len(taken)} rows) -> {AUTO}")
    for k, v in out.items():
        print(f"  {k:40s} {v['length']:5d} m  el {v['max_el']:4.1f}  {v['title']}")
    if "--lidar" in sys.argv:
        have = {f[2:-4] for f in os.listdir(os.path.join(ROOT, "data", "build", "lidar"))}
        need = set()
        for v in out.values():
            x0, y0, x1, y1 = v["fetch"]
            for X in range(int((x0 + OX) // T * T), int(x1 + OX) + 1, T):
                for Y in range(int((y0 + OY) // T * T), int(y1 + OY) + 1, T):
                    need.add(f"{X}_{Y}")
        print("missing LiDAR tiles:", ",".join(sorted(need - have)) or "none")


if __name__ == "__main__":
    main()
