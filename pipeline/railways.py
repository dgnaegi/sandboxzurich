"""Railway layer for the play area: tracks on ballast, catenary, platforms, station signs, S-Bahn routes.

Reads OSM (sources.osm) and the terrain. Writes
  web/public/models/trains/tiles/r_{ix}_{iy}.glb   one merged mesh per 200 m tile (world material, layer = texture index)
  web/public/data/rail.json                          per tile: wires, sign/clock anchors; plus S-Bahn routes + stations
Run: python3 pipeline/railways.py   (needs data/raw/osm/kreise.json, swissALTI3D cache)
Integration: web/src/world/railways.ts (loads rail.json + tiles near the player).
"""
import json
import math
import subprocess
from pathlib import Path
from collections import defaultdict
from heapq import heappop, heappush

import mapbox_earcut as earcut
import numpy as np
import shapely
from shapely.geometry import LineString, MultiLineString, Point, Polygon
from shapely.ops import unary_union
from shapely import STRtree

import glb
import rail_build as RB
import rail_net
import rail_routes
import terrain
from config import ROOT, TILE, tiles
from rail_acc import Acc, TrackAcc
from rail_build import tile_of

OUT_DIR = ROOT / "web" / "public" / "models" / "trains" / "tiles"
RAW_DIR = ROOT / "data" / "build" / "rail_raw"
DATA = ROOT / "web" / "public" / "data" / "rail.json"
TERRAIN_AREA = (-2849.0, -2069.0, 1952.0, 1454.0)
Z_SHIFT = -3.06
STEP = 4.0           # track sampling (m)
RAIL_TOP = 0.29      # rail head above terrain
BALLAST = 0.12
WIRE_H = 5.5         # contact wire above rail head
SPAN = 60.0          # mast spacing
PLATFORM_H = 0.55    # platform edge above rail head (SBB standard)
SERVICES = (None, "yard", "siding", "crossover", "spur")
ROUTE_SERVICES = (None, "crossover", "yard")

C_STEEL, C_RUST, C_SLEEP = (112, 108, 104), (98, 84, 74), (128, 124, 120)
C_MAST, C_DECK, C_KERB, C_LINE, C_WALL = (92, 98, 104), (150, 150, 152), (205, 205, 207), (245, 245, 245), (172, 170, 166)
C_ROOF_T, C_ROOF_B = (118, 124, 130), (205, 207, 212)


# ---------------------------------------------------------------- platforms


def platform_polys(plats, ways):
    """Platform polygons near passenger tracks (not tram-only stops)."""
    lines = [LineString(w["pts"][:, :2]) for w in ways if w["cls"] != "tunnel" and w["svc"] in (None, "crossover", "yard")]
    tracks = unary_union(lines)
    out = []
    for p in plats:
        xy = p["xy"]
        if tracks.distance(Point(*xy[len(xy) // 2])) > 14 and tracks.distance(Point(*xy[0])) > 14:
            continue
        if (xy[0] == xy[-1]).all() and len(xy) >= 4:
            poly = Polygon(xy).buffer(0)
        else:
            ls = LineString(xy)
            sgn = 1
            o = ls.offset_curve(3.2)
            if not o.is_empty and tracks.distance(o) < tracks.distance(ls.offset_curve(-3.2)):
                sgn = -1
            o = ls.offset_curve(3.2 * sgn)
            if o.is_empty or o.geom_type != "LineString":
                continue
            poly = Polygon(list(ls.coords) + list(o.coords)[::-1]).buffer(0)
        if poly.geom_type == "MultiPolygon":
            poly = max(poly.geoms, key=lambda g: g.area)
        if poly.is_empty or poly.area < 8 or poly.area > 6000:
            continue
        out.append(poly)
    return out, tracks, lines


def _hb_excl():
    f = Path(__file__).resolve().parent.parent / "research" / "hb" / "prop_excl.json"   # written by pipeline/landmarks/hb_propexcl.py
    return shapely.union_all([Polygon(q) for q in json.load(open(f))["polys"]]) if f.exists() else None


_HB_EX = _hb_excl()


def add_platforms(polys, tracks, ways, roofs, accs, H, signs, stops):
    samp = np.concatenate([w["pts"] for w in ways if w["cls"] != "tunnel" and w["svc"] in (None, "crossover", "yard")])
    tree = STRtree([Point(p[0], p[1]) for p in samp])
    def rail_z(x, y):
        return float(samp[tree.nearest(Point(x, y))][2]) + RAIL_TOP

    n_roof = 0
    for poly in polys:
        poly = shapely.segmentize(poly, 20.0)
        if not poly.exterior.is_ccw:
            poly = Polygon(list(poly.exterior.coords)[::-1])
        ring = np.asarray(poly.exterior.coords)[:-1]
        zt = np.array([rail_z(x, y) + PLATFORM_H for x, y in ring])
        tri = earcut.triangulate_float64(ring, np.array([len(ring)], np.uint32)).reshape(-1, 3)
        # deck top (triangles as degenerate quads), keyed to the tile of the centroid
        c = poly.centroid
        acc = accs[tile_of(c.x, c.y)]
        if len(tri):
            tq = np.stack([ring[tri[:, 0]], ring[tri[:, 1]], ring[tri[:, 2]], ring[tri[:, 2]]], 1)
            zq = zt[tri]
            P = np.concatenate([tq, np.concatenate([zq, zq[:, 2:3]], 1)[..., None]], 2)
            acc.quads(P, (0, 0, 1), C_DECK)
        for i in range(len(ring)):
            a, b = ring[i], ring[(i + 1) % len(ring)]
            za, zb = zt[i], zt[(i + 1) % len(ring)]
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            d = math.hypot(*(b - a))
            if d < 0.2:
                continue
            tx, ty = (b - a) / d
            out = np.array([ty, -tx, 0.0])  # outward for CCW ring
            trackside = tracks.distance(Point(mx, my)) < 4.5
            bot_a = (rail_z(*a) - RAIL_TOP + 0.1) if trackside else float(H.at(*a)) - 0.3
            bot_b = (rail_z(*b) - RAIL_TOP + 0.1) if trackside else float(H.at(*b)) - 0.3
            bot_a, bot_b = min(bot_a, za - 0.3), min(bot_b, zb - 0.3)
            acc.quads([[a[0], a[1], bot_a], [b[0], b[1], bot_b], [b[0], b[1], zb], [a[0], a[1], za]], out, C_WALL)
            if trackside:  # kerb band and white safety line, inset from the edge
                inn = -out[:2]
                def pp(p, z, u): return [p[0] + inn[0] * u, p[1] + inn[1] * u, z + 0.012]
                acc.quads([pp(a, za, 0.0), pp(b, zb, 0.0), pp(b, zb, 0.45), pp(a, za, 0.45)], (0, 0, 1), C_KERB)
                acc.quads([pp(a, za, 0.85), pp(b, zb, 0.85), pp(b, zb, 0.97), pp(a, za, 0.97)], (0, 0, 1), C_LINE)
        # roofs over this platform
        rect = poly.minimum_rotated_rectangle
        rc = np.asarray(rect.exterior.coords)[:4]
        e0, e1 = rc[1] - rc[0], rc[2] - rc[1]
        ax = (e0 if np.linalg.norm(e0) >= np.linalg.norm(e1) else e1)
        plen = np.linalg.norm(ax)
        ax = ax / max(plen, 1e-6)
        mid = np.array([poly.centroid.x, poly.centroid.y])
        zp = float(np.mean(zt))
        for roof in roofs:
            rp = Polygon(roof).buffer(0)
            if rp.is_empty or not rp.intersects(poly):
                continue
            if _HB_EX is not None and _HB_EX.contains(rp.representative_point()):
                continue   # Zuerich HB: the hall/platform vaults are the landmark model (hb_perron.py); the flat OSM roof slab hung a grey ceiling at platform + 3.6 m
            inter = rp.intersection(poly)
            if inter.area < 15:
                continue
            n_roof += 1
            rz = zp + 3.6
            rr = np.asarray(rp.exterior.coords)[:-1]
            if not rp.exterior.is_ccw:
                rr = rr[::-1]
            t = earcut.triangulate_float64(rr, np.array([len(rr)], np.uint32)).reshape(-1, 3)
            if len(t):
                tq = np.stack([rr[t[:, 0]], rr[t[:, 1]], rr[t[:, 2]], rr[t[:, 2]]], 1)
                for zz, col, hint in ((rz + 0.3, C_ROOF_T, 1), (rz, C_ROOF_B, -1)):
                    P = np.concatenate([tq, np.full(tq.shape[:2] + (1,), zz)], 2)
                    accs[tile_of(*mid)].quads(P, (0, 0, hint), col)
            for i in range(len(rr)):
                a, b = rr[i], rr[(i + 1) % len(rr)]
                d = np.linalg.norm(b - a)
                if d < 0.2:
                    continue
                out = np.array([(b - a)[1], -(b - a)[0], 0.0])
                accs[tile_of(*mid)].quads([[a[0], a[1], rz], [b[0], b[1], rz], [b[0], b[1], rz + 0.3], [a[0], a[1], rz + 0.3]], out, C_ROOF_T)
            ci = inter.centroid
            sub = np.arange(-plen / 2 + 3, plen / 2 - 2, 12.0)
            for sd in sub:
                p = mid + ax * sd
                if inter.buffer(0.5).contains(Point(*p)):
                    accs[tile_of(*p)].box(-0.18, 0.18, -0.18, 0.18, zp, rz, C_MAST, 0.0, p[0], p[1])
        # name signs + clock posts along the platform centre line
        near = [s for s in stops if math.hypot(s["x"] - mid[0], s["y"] - mid[1]) < 120]
        if near and plen > 25:
            nm = min(near, key=lambda s: math.hypot(s["x"] - mid[0], s["y"] - mid[1]))["name"]
            yaw = math.atan2(ax[1], ax[0])
            for frac, kind in ((-0.3, 0), (0.0, 1), (0.3, 0)):
                p = mid + ax * plen * frac
                if not poly.buffer(-0.3).contains(Point(*p)):
                    continue
                zd = rail_z(*p) + PLATFORM_H
                h = 2.5 if kind == 0 else 3.0
                accs[tile_of(*p)].box(-0.05, 0.05, -0.05, 0.05, zd, zd + h, C_MAST, 0.0, p[0], p[1])
                signs[tile_of(*p)].append([round(p[0], 2), round(p[1], 2), round(zd + h, 2), round(yaw, 3), nm, kind])
    return n_roof


def build_tracks(ways, taccs, runs):
    """Distribute track geometry over tile accumulators; collect electrified runs per tile (wires are built in the client)."""
    for w in ways:
        if w["cls"] == "tunnel":
            continue
        pts = w["pts"]
        mid = (pts[:-1, :2] + pts[1:, :2]) / 2
        keys = np.floor(mid / TILE).astype(int)
        i = 0
        while i < len(keys):
            j = i
            while j + 1 < len(keys) and (keys[j + 1] == keys[i]).all():
                j += 1
            run = pts[i:j + 2]
            if len(run) >= 2:
                key = (int(keys[i][0]), int(keys[i][1]))
                RB.add_track(taccs[key], run, w["svc"] is None, 0.9 + 0.2 * (((w["id"] * 2654435761) >> 9) % 100) / 100)
                if w["elec"] and w["svc"] in (None, "yard", "crossover", "siding"):
                    runs[("wr" if w["svc"] is None else "w1", key)].append(np.round(run * 10).astype(int).ravel().tolist())
            i = j + 1


def write_tiles(accs, taccs, runs, signs, routes, parked):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for f in list(OUT_DIR.glob("r_*.glb")) + list(OUT_DIR.glob("rt_*.glb")):
        f.unlink()
    keep = {(ix, iy) for ix, iy in tiles()}
    names = sorted({s[4] for v in signs.values() for s in v})
    meta, tris = {}, 0
    keys = set(accs) | set(taccs) | {k for (_, k) in runs} | set(parked)
    for key in sorted(keys):
        if key not in keep:
            continue
        nm = f"r_{key[0]}_{key[1]}"
        arr = accs[key].arrays() if key in accs else None
        if arr is not None:
            raw = RAW_DIR / f"{nm}.glb"
            glb.write(raw, {"rail": arr})
            subprocess.run(["npx", "--no-install", "gltfpack", "-i", str(raw), "-o", str(OUT_DIR / f"{nm}.glb"), "-cc", "-kv", "-km", "-vtf", "-vp", "15"],
                           cwd=ROOT / "web", check=True, capture_output=True)
            tris += len(arr["idx"])
        m = {}
        for kind in ("wr", "w1"):
            if runs.get((kind, key)):
                m[kind] = runs[(kind, key)]
        if signs.get(key):
            m["sg"] = [[*s[:4], names.index(s[4]), s[5]] for s in signs[key]]
        if parked.get(key):
            m["pk"] = parked[key]
        if arr is not None:
            m["glb"] = 1
        tarr = taccs[key].arrays() if key in taccs else None
        if tarr is not None:
            raw = RAW_DIR / f"rt_{key[0]}_{key[1]}.glb"
            glb.write(raw, {"track": tarr})
            subprocess.run(["npx", "--no-install", "gltfpack", "-i", str(raw), "-o", str(OUT_DIR / f"rt_{key[0]}_{key[1]}.glb"), "-cc", "-kv", "-km", "-vtf", "-vp", "15"],
                           cwd=ROOT / "web", check=True, capture_output=True)
            tris += len(tarr["idx"])
            m["tg"] = 1
        meta[f"{key[0]}_{key[1]}"] = m
    DATA.write_text(json.dumps({"tile": TILE, "stations": names, "tiles": meta, "routes": routes}, separators=(",", ":")))
    print("tiles", len(meta), "tris", tris, "rail.json KB", DATA.stat().st_size // 1024)


def main():
    H = terrain.heights(TERRAIN_AREA, 2.0, z_shift=Z_SHIFT)
    net = rail_net.load(H)
    ways = net.ways
    accs, taccs, runs, signs = defaultdict(Acc), defaultdict(TrackAcc), defaultdict(list), defaultdict(list)
    build_tracks(ways, taccs, runs)
    nidx = RB.node_index(net)
    ns, nsig, nbuf = RB.add_track_detail(net, accs, nidx, taccs)
    npt = RB.add_portals(net, accs, nidx)
    nm = RB.add_masts(ways, accs, H)
    polys, tracks, _ = platform_polys(net.plats, ways)
    nr = add_platforms(polys, tracks, ways, net.roofs, accs, H, signs, net.stops)
    print("ways", len(ways), "masts", nm, "switches", ns, "signals", nsig, "buffers", nbuf, "portals", npt,
          "platforms", len(polys), "roofs", nr, "signs", sum(len(v) for v in signs.values()))
    routes = rail_routes.build_routes(net, net.stops)
    used = {wi for r in routes for wi in r["ways"]}
    for r in routes:
        del r["ways"]
    parked = RB.parked_trains(net, used)
    write_tiles(accs, taccs, runs, signs, routes, parked)


if __name__ == "__main__":
    main()
