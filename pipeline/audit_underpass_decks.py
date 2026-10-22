"""Audit: bridge decks that end up inside underpasses/cuts, buried, or lie across a road at < 3 m clearance (they form walls/curbs).
usage: .venv/bin/python pipeline/audit_underpass_decks.py [--before]   (--before: bridges._ROOF disabled = old behaviour)
-> research/underpass_decks/audit[_before].tsv, summary <= 30 lines on stdout.
Flags per chain vertex (decks only, el = z - ground > 0.3 or inside a hole):
  HOLE   vertex inside a terrain_cuts "hole" footprint (covered underpass) with z below the roof (ground - 0.5 at the hole rim)
  BURIED deck z < terrain - 0.8 (deck under the ground)
  LOW    deck over a foreign ground road/path (not connected, layer<=0, also tunnel mouths) with clearance z - H < 3.0
  CURB   as LOW but clearance < 1.0 (acts as a wall/curb across the street)"""
import sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridges, road_height, sources, streets, terrain, terrain_cuts  # noqa: E402
from config import AREA, HGRID  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main(before):
    if before:
        bridges._ROOF = None
    BIG = (AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)
    H = terrain.heights(BIG, HGRID, z_shift=-3.06)
    terrain_cuts.apply(H)
    nodes, els = sources.osm()
    S = streets.parse(nodes, els)
    import copy
    H_raw = copy.deepcopy(H)
    import inspect
    road_height.apply(H, S["ways"], **({"roads": S.get("roads")} if "roads" in inspect.signature(road_height.apply).parameters else {}))
    terrain_cuts.apply(H, lock_only=True)
    BR = bridges.bridge_ways(nodes, els, AREA, H, H_raw)
    holes = terrain_cuts.holes()
    # foreign ground ways (roads/paths, tunnel mouths included)
    gw = []
    for e in els:
        if e["type"] != "way" or len(e.get("nodes", [])) < 2:
            continue
        t = e.get("tags", {})
        k = bridges._kind(t)
        if k not in ("road", "foot") or bridges._is_bridge(t) or t.get("area") == "yes" or t.get("highway") == "steps":
            continue
        pts = [nodes[n] for n in e["nodes"] if n in nodes]
        if len(pts) < 2:
            continue
        w = bridges._width(t, k)
        gw.append((e["id"], set(e["nodes"]), shapely.LineString(pts).buffer(w / 2 + 0.3, cap_style="flat"), t.get("highway"), t.get("name", ""), shapely.LineString(pts)))
    tree = STRtree([g[2] for g in gw])
    rows = []
    for b in BR:
        P = np.array(b["p"]); mynodes = set()
        ids = set(b["ids"])
        own = {e["id"]: set(e["nodes"]) for e in els if e["type"] == "way" and e["id"] in ids}
        for v in own.values():
            mynodes |= v
        flags = {}
        for vi, ((x, y, z), g0) in enumerate(zip(P, b["g"])):
            gz = float(H.at(x, y)); pt = Point(x, y); el = z - g0
            if holes is not None and holes.buffer(1.0).contains(pt) and z < gz + 2.0:
                # roof = ground at rim; deck below the street roof inside the tunnel box
                flags.setdefault("HOLE", []).append((x, y, z, gz))
            if z < float(H_raw.at(x, y)) - 0.8:
                flags.setdefault("BURIED", []).append((x, y, z, gz))
            if el > 0.15 and z - gz < 3.0:
                for j in tree.query(pt):
                    wid, wn, geom, hw, nm, line = gw[j]
                    if wid in ids or (wn & mynodes) or not geom.contains(pt):
                        continue
                    d1 = P[min(vi + 1, len(P) - 1), :2] - P[max(vi - 1, 0), :2]  # only decks CROSSING the street (>= 35 deg): parallel flush tram decks are no walls
                    q = line.project(pt); a0, a1 = line.interpolate(max(q - 2, 0)), line.interpolate(min(q + 2, line.length))
                    d2 = np.array([a1.x - a0.x, a1.y - a0.y])
                    if np.hypot(*d1) < 1e-6 or np.hypot(*d2) < 1e-6 or abs(np.dot(d1, d2)) / (np.hypot(*d1) * np.hypot(*d2)) > 0.82:
                        continue
                    flags.setdefault("CURB" if z - gz < 1.0 else "LOW", []).append((x, y, z, gz, wid, hw, nm))
                    break
        for f, v in flags.items():
            if f in ("LOW", "CURB") and len(v) < 2:
                continue
            a = v[0]
            rows.append((f, b["ids"][0], b["kind"], b.get("name", ""), len(v), round(a[0], 1), round(a[1], 1), round(a[2], 2), round(a[3], 2),
                         v[0][4] if len(v[0]) > 4 else "", v[0][6] if len(v[0]) > 6 else ""))
    out = ROOT / "research/underpass_decks" / ("audit_before.tsv" if before else "audit.tsv")
    out.write_text("flag\tchain_first_id\tkind\tname\tn_vertices\tx\ty\tdeck_z\tground_z\tway_id\tway_name\n" + "\n".join("\t".join(map(str, r)) for r in rows) + "\n")
    from collections import Counter
    c = Counter(r[0] for r in rows)
    print(f"chains {len(BR)}; flagged rows {len(rows)} {dict(c)} -> {out}")
    for r in sorted(rows, key=lambda r: (r[0], r[7] - r[8]))[:22]:
        print("\t".join(map(str, r)))


if __name__ == "__main__":
    main("--before" in sys.argv)
