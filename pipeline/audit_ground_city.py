"""City-wide ground/road glitch audit (read-only; no builds, no browser). Complements audit_ground.py (zone AV-vs-OSM) and audit_lidar.py.
Usage: python3 pipeline/audit_ground_city.py     (needs web/public/tiles/t_*.json, web/tests/fixtures/traffic_zones.*, data/cache/props_road_zone.wkb,
data/build/lidar/ for the DTM part, research/lidar/audit_a_ground_blocks.tsv)
Classes:
  shrub_on_road    yards.bushes/hedges (+ lawn/trees) standing on the carriageway raster (cat 1)      source: yards.py (not in props_road.LIST_KEYS)
  hmap_pit/spike   tile hmap cell deviates > 0.7 m from the mean of its 4 neighbours (2 m grid)      source: terrain / road_height / terrain_cuts
  hmap_step        |dz| > 1.5 m between neighbouring cells that are both carriageway                  source: road_height
  lidar_dz         20 m blocks where game ground differs > 1 m from the LiDAR DTM (audit_lidar a)    source: terrain / road_height / cuts
  road_hole/sliver tiny interior rings / slivers in the carriageway polygon (each ring becomes curb faces)  source: streets.py roads
Output: research/ground_audit/findings.tsv (x y class magnitude source street score) + <= 30 summary lines."""
import base64
import glob
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import shapely
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
FX = ROOT / "web/tests/fixtures"
OUT = ROOT / "research/ground_audit"
M = json.load(open(FX / "traffic_zones.json"))
GRID = np.array(Image.open(FX / "traffic_zones.png"))


def cat(x, y):
    x, y = np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(y, float))
    i, j = ((x - M["x0"]) // M["cell"]).astype(int), ((M["y1"] - y) // M["cell"]).astype(int)
    ok = (i >= 0) & (i < M["w"]) & (j >= 0) & (j < M["h"])
    out = np.zeros(len(x), int)
    out[ok] = GRID[j[ok], i[ok]]
    return out


def real_dev(x, y, zg):
    """True when the game ground deviates > 0.6 m from the LiDAR DTM (no building/bridge return within 3 m); unknown DTM -> False."""
    import lidar
    d = lidar.dtm(x, y)[0] if np.ndim(lidar.dtm(x, y)) else lidar.dtm(x, y)
    if d is None or np.isnan(d):
        return False
    for ox, oy in ((0, 0), (3, 0), (-3, 0), (0, 3), (0, -3)):
        if not np.isnan(np.ravel(lidar.bld(x + ox, y + oy))[0]) or not np.isnan(np.ravel(lidar.bridge(x + ox, y + oy))[0]):
            return False
    return abs(zg - d) > 0.6


def main():
    tiles = {}
    for f in sorted(glob.glob(str(ROOT / "web/public/tiles/t_*.json"))):
        tiles[Path(f).stem] = json.load(open(f))
    # visibility anchors: zone cameras + spawns
    anc = [(c["x"], c["y"]) for z in json.load(open(ROOT / "pipeline/overrides/zones.json"))["zones"] for c in z.get("cams", [])]
    anc += [(s["x"], s["y"]) for s in json.load(open(ROOT / "web/public/data/spawns.json"))["spawns"]]
    anc = np.array(anc)
    names = [(r[0], r[1], r[-1]) for t in tiles.values() for r in t.get("streetsigns") or []]
    nm = np.array([(a, b) for a, b, _ in names]); nn = [c for _, _, c in names]

    def street(x, y):
        if not len(nm):
            return ""
        d = np.hypot(nm[:, 0] - x, nm[:, 1] - y)
        k = int(d.argmin())
        return nn[k] if d[k] < 120 else ""

    def vis(x, y):
        d = np.hypot(anc[:, 0] - x, anc[:, 1] - y).min()
        return 3.0 if d < 40 else 2.0 if d < 120 else 1.0

    zone = shapely.from_wkb((ROOT / "data/cache/props_road_zone.wkb").read_bytes())
    shapely.prepare(zone)
    F = []   # x, y, class, magnitude, source
    # dry run of props_road._bush_edge (T-G2): bushes whose foliage edge is < 0.3 m from the carriageway polygon, before -> after
    import props_road
    props_road.set_zone(zone)
    nb = ne = ne2 = 0
    for t in tiles.values():
        for r in (t.get("yards") or {}).get("bushes") or []:
            nb += 1
            d = zone.distance(shapely.Point(r[0], r[1]))
            if d - r[3] < 0.3:
                ne += 1
                r2 = props_road._bush_edge(r)
                if zone.distance(shapely.Point(r2[0], r2[1])) - r2[3] < 0.3 - 2e-2 and not zone.contains(shapely.Point(r[0], r[1])):
                    ne2 += 1
    print(f"dry-run bushes: {nb} total, edge<0.3 m (incl. centre on road): {ne} -> after _bush_edge still short: {ne2}")

    # --- 1. shrubs etc. on the carriageway
    tot = Counter()
    for t in tiles.values():
        y_ = t.get("yards") or {}
        for r in y_.get("bushes") or []:
            tot["bush"] += 1
            rad = r[3]
            px = [r[0], r[0] + rad * .6, r[0] - rad * .6, r[0], r[0]]
            py = [r[1], r[1], r[1], r[1] + rad * .6, r[1] - rad * .6]
            c = cat(px, py)
            if c[0] == 1:
                F.append((r[0], r[1], "shrub_on_road", round(rad, 2), "yards.bushes"))
            elif (c == 1).any():
                F.append((r[0], r[1], "shrub_edge_road", round(rad, 2), "yards.bushes"))
        for r in y_.get("hedges") or []:
            tot["hedge"] += 1
            L, hd = r[4], r[3]
            s = np.linspace(-.5, .5, 7) * L
            c = cat(r[0] + s * np.cos(hd), r[1] + s * np.sin(hd))
            if (c == 1).mean() >= .5:
                F.append((r[0], r[1], "hedge_on_road", round(L * (c == 1).mean(), 1), "yards.hedges"))
        for k, src in (("trees", "trees"), ("lawn", "lawn")):
            for r in t.get(k) or []:
                tot[k] += 1
                # trunks/lawn centres are judged against the carriageway polygon (zone: roads minus plazas/decks), not the 1 m raster:
                # lane_fix parks trees 0.4 m off the kerb, which the raster rounds onto the road (62 of 63 old findings were this)
                if cat(r[0], r[1])[0] == 1 and (zone is None or zone.buffer(-0.15).contains(shapely.Point(r[0], r[1]))):
                    F.append((r[0], r[1], k + "_on_road", 1, src))
    # --- 2. hmap pits / spikes / road steps
    for tid, t in tiles.items():
        h = t.get("hmap")
        if not h or "zb64" not in h:
            continue
        z = np.frombuffer(base64.b64decode(h["zb64"]), "<i2").astype(float).reshape(h["h"], h["w"]) / 100
        gy, gx = np.mgrid[0:h["h"], 0:h["w"]]
        X, Y = h["x0"] + gx * h["step"], h["y0"] + gy * h["step"]
        C = cat(X.ravel(), Y.ravel()).reshape(z.shape)
        n4 = (z[:-2, 1:-1] + z[2:, 1:-1] + z[1:-1, :-2] + z[1:-1, 2:]) / 4
        lap = z[1:-1, 1:-1] - n4
        # a pit/spike must also be the extreme of its 4 neighbours (excludes ridges/cliff edges)
        nmin = np.minimum.reduce([z[:-2, 1:-1], z[2:, 1:-1], z[1:-1, :-2], z[1:-1, 2:]])
        nmax = np.maximum.reduce([z[:-2, 1:-1], z[2:, 1:-1], z[1:-1, :-2], z[1:-1, 2:]])
        c = z[1:-1, 1:-1]
        import lidar
        for msk, cl, mag in (((lap < -.7) & (c < nmin - .5), "hmap_pit", lap), ((lap > .7) & (c > nmax + .5), "hmap_spike", lap)):
            for j, i in zip(*np.where(msk)):
                x_, y_ = X[j + 1, i + 1], Y[j + 1, i + 1]
                if not real_dev(x_, y_, z[j + 1, i + 1]):
                    continue
                F.append((x_, y_, cl, round(float(mag[j, i]), 2), "road_height" if C[j + 1, i + 1] == 1 else "terrain"))
        for ax in (0, 1):
            d = np.abs(np.diff(z, axis=ax))
            both = (C[1:] == 1) & (C[:-1] == 1) if ax == 0 else (C[:, 1:] == 1) & (C[:, :-1] == 1)
            for j, i in zip(*np.where((d > 1.5) & both)):
                if not real_dev(X[j, i], Y[j, i], z[j, i]):
                    continue
                F.append((X[j, i], Y[j, i], "hmap_step", round(float(d[j, i]), 2), "road_height"))
    # --- 3. LiDAR deviation blocks (from audit_lidar a)
    cuts = json.load(open(ROOT / "pipeline/overrides/terrain_cuts.json"))["cuts"]
    cl = [shapely.LineString(c["line"]).buffer(c.get("width", 10) / 2 + 8) for c in cuts if c.get("line")]
    cl += [shapely.LineString(c["axis"]).buffer(c.get("half", 6) + 8) for c in cuts if c.get("axis")]
    cutu = shapely.union_all(cl) if cl else None
    bf = ROOT / "research/lidar/audit_a_ground_blocks.tsv"
    if bf.exists():
        for ln in open(bf).read().splitlines()[1:]:
            x, y, n, md, mx = ln.split("\t")
            x, y, n, md = float(x), float(y), int(n), float(md)
            if abs(md) < 1.0 or n < 8:
                continue
            src = "terrain_cuts" if cutu is not None and cutu.contains(shapely.Point(x, y)) else "road_height" if cat(x, y)[0] == 1 else "terrain(swissALTI/park)"
            F.append((x, y, "lidar_dz", round(md, 2), src))
    # --- 4. carriageway polygon: tiny holes / slivers (each ring edge becomes a curb face)
    g = shapely.from_wkb((ROOT / "data/cache/props_road_zone.wkb").read_bytes())
    for p in g.geoms:
        for r in p.interiors:
            a = shapely.Polygon(r).area
            if a < 40:
                c_ = shapely.Polygon(r).centroid
                F.append((c_.x, c_.y, "road_hole", round(a, 1), "streets.roads"))
        if p.area < 4:
            c_ = p.centroid
            F.append((c_.x, c_.y, "road_sliver", round(p.area, 1), "streets.roads"))
    # --- ranking
    W = {"shrub_on_road": 8, "hedge_on_road": 6, "trees_on_road": 3, "lawn_on_road": 3, "shrub_edge_road": 1, "hmap_pit": 5, "hmap_spike": 5,
         "hmap_step": 6, "lidar_dz": 3, "road_hole": 4, "road_sliver": 2}
    rows = []
    for x, y, c_, mag, src in F:
        base = W.get(c_, 1) * (min(abs(mag), 4) if c_ in ("hmap_pit", "hmap_spike", "hmap_step", "lidar_dz") else 1)
        rows.append((round(x, 1), round(y, 1), c_, mag, src, street(x, y), round(base * vis(x, y), 1)))
    rows.sort(key=lambda r: -r[6])
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "findings.tsv", "w") as f:
        f.write("x\ty\tclass\tmagnitude\tsource\tstreet\tscore\n")
        for r in rows:
            f.write("\t".join(map(str, r)) + "\n")
    cnt = Counter(r[2] for r in rows)
    print("scanned:", dict(tot), "| tiles", len(tiles))
    print("counts:", dict(cnt))
    print("by source:", dict(Counter((r[2], r[4]) for r in rows).most_common(8)))
    seen, top = [], []
    for r in rows:   # top spots, one per 30 m cell
        k = (round(r[0] / 30), round(r[1] / 30))
        if k in seen:
            continue
        seen.append(k); top.append(r)
        if len(top) >= 20:
            break
    for r in top:
        print(f"  {r[0]:8.1f},{r[1]:8.1f} {r[2]:14s} {r[3]:>6} {r[4]:22s} {r[5]} [{r[6]}]")


if __name__ == "__main__":
    main()
