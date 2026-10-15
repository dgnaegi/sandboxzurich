"""Build the M1 test area (Langstrasse/Helvetiaplatz) into web/public/tiles: one glb + meta per 200 m tile.

Usage: .venv/bin/python pipeline/build_testarea.py
"""
import base64
import json
import math
import multiprocessing as mp
import os
import subprocess

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely.strtree import STRtree

import glb
import addresses
import bridges
import plazasigns
import citydata
import gastro
import groundcover
import visual_overrides
import terrain
import traffic_signs as TS
from gwr import gwr_for_building
import cityprops
import props
import sources
import streets
from config import AREA, HGRID, OUT, POLYGON, TILE, is_backdrop, tiles
from facade import add_building
from mesh import Heights, Mesh, drape
from styles import LAYER, h32

CURB = 0.12  # carriageway is lowered by this much
RAW_OUT = OUT.parent.parent.parent / "data" / "build" / "tiles_raw"


def pack(src, dst):
    """Meshopt-compress a tile (gltfpack): quantised positions/normals, float UVs (they carry the layer index)."""
    subprocess.run(["npx", "--no-install", "gltfpack", "-i", str(src), "-o", str(dst), "-cc", "-kv", "-km", "-vtf", "-vp", "15"],
                   cwd=OUT.parent.parent, check=True, capture_output=True)


def heights_from(blds):
    """IDW terrain from building ground points (flat area; swissALTI3D later)."""
    pts = []
    for b in blds:
        g = [p for k, p in b["polys"] if k == 0]
        if g:
            a = np.concatenate(g)
            pts.append((a[:, 0].mean(), a[:, 1].mean(), a[:, 2].min()))
    pts = np.array(pts)
    # drop sunken ground surfaces (ramps, basements): > 1.5 m below the local median within 60 m
    d2 = ((pts[:, None, :2] - pts[None, :, :2]) ** 2).sum(-1)
    med = np.array([np.median(pts[row < 3600, 2]) for row in d2])
    pts = pts[np.abs(pts[:, 2] - med) < 1.5]
    x0, y0, x1, y1 = AREA
    gx, gy = np.meshgrid(np.arange(x0, x1 + HGRID, HGRID), np.arange(y0, y1 + HGRID, HGRID))
    q = np.column_stack([gx.ravel(), gy.ravel()])
    z = np.empty(len(q))
    for i in range(0, len(q), 4000):
        d2 = ((q[i:i + 4000, None, :] - pts[None, :, :2]) ** 2).sum(-1)
        idx = np.argpartition(d2, 8, axis=1)[:, :8]
        w = 1 / (np.take_along_axis(d2, idx, 1) + 100.0)
        z[i:i + 4000] = (pts[idx, 2] * w).sum(1) / w.sum(1)
    return Heights(x0, y0, HGRID, z.reshape(gx.shape))


def footprint(b):
    rings = [Polygon(p[:, :2]).buffer(0) for k, p in b["polys"] if k == 0 and len(p) >= 4]
    rings = [r for r in rings if not r.is_empty]
    if not rings:
        walls = np.concatenate([p[:, :2] for k, p in b["polys"] if k == 1] or [np.zeros((0, 2))])
        return shapely.MultiPoint(walls).convex_hull if len(walls) >= 3 else None
    return shapely.union_all(rings).simplify(0.3)


def curbs(mesh, segs, H):
    for a, b in segs:
        za, zb = float(H.at(*a)), float(H.at(*b))
        pts = np.array([[a[0], a[1], za - CURB], [b[0], b[1], zb - CURB], [b[0], b[1], zb], [a[0], a[1], za]], np.float32)
        d = b - a
        n = np.array([-d[1], d[0], 0]) / np.hypot(*d)  # road is on the left
        L = np.hypot(*d)
        mesh.add(pts, np.array([[0, 2, 1], [0, 3, 2]], np.uint32), n, (180, 177, 170),
                 uv=np.array([[0, 0], [L, 0], [L, 0.1], [0, 0.1]]), layer=LAYER["white"])


def ground_tile(gm, S, tb, H, white, yellow, rails, bed, bays_white=None, bays_blue=None, grooves=None):
    roads = S["roads"].intersection(tb)
    plaza, parks = S["plaza"].intersection(tb), S["parks"].intersection(tb)
    walk = tb.difference(S["roads"]).difference(S["plaza"]).difference(S["parks"])
    if S.get("av_rail") is not None:  # railway land: low ballast, the rail tiles (railways.py) sit on top
        rl = walk.intersection(S["av_rail"].intersection(tb))
        drape(gm, rl, H, -0.45, (150, 142, 132), cell=TILE / 10, layer=LAYER["dach_kies"], uv_scale=1.5)
        walk = walk.difference(rl)
    # sidewalks along streets; everything further away is courtyard / front garden
    side = walk.intersection(S["roads"].buffer(6.0).union(S["plaza"].buffer(3.0)))
    yard = walk.difference(side)
    drape(gm, side, H, 0.0, (255, 255, 255), cell=TILE / 10, layer=LAYER["sidewalk"], uv_scale=5.0)
    if S.get("av_green") is not None:  # official land cover decides courtyards: lawn vs paved (AV Kanton ZH)
        g_av = yard.intersection(S["av_green"].intersection(tb))
        drape(gm, g_av, H, 0.005, (235, 240, 225), cell=TILE / 10, layer=LAYER["grass"], uv_scale=5.0)
        p_av = yard.difference(g_av).intersection(S["av_paved"].intersection(tb))
        drape(gm, p_av, H, 0.005, (215, 210, 200), cell=TILE / 10, layer=LAYER["roof_flat"], uv_scale=2.0)
        yard = yard.difference(g_av).difference(p_av)
    for p in getattr(yard, "geoms", [yard]):
        if p.is_empty:
            continue
        big = p.area > 60
        drape(gm, p, H, 0.005, (235, 240, 225) if big else (215, 210, 200), cell=TILE / 10,
              layer=LAYER["grass"] if big else LAYER["roof_flat"], uv_scale=5.0 if big else 2.0)
    for bays, col in ((bays_white, (238, 238, 232)), (bays_blue, (40, 90, 200))):
        if bays is not None and not bays.is_empty:
            drape(gm, bays.intersection(roads), H, -CURB + 0.008, col, cell=10, layer=LAYER["white"])
    drape(gm, plaza, H, 0.0, (255, 255, 255), layer=LAYER["cobble"], uv_scale=2.5)
    drape(gm, parks, H, 0.01, (255, 255, 255), layer=LAYER["grass"], uv_scale=5.0)
    drape(gm, roads, H, -CURB, (255, 255, 255), layer=LAYER["asphalt"], uv_scale=5.0)
    curbs(gm, streets.curb_faces(roads, tb), H)
    top = S["roads"].boundary.buffer(0.16).difference(S["roads"]).difference(S["plaza"]).intersection(tb)
    drape(gm, top, H, 0.006, (205, 203, 196), cell=10, layer=LAYER["white"])
    drape(gm, bed.difference(S["roads"]).intersection(tb), H, 0.015, (190, 185, 175), layer=LAYER["roof_flat"], uv_scale=2)
    drape(gm, white.intersection(roads), H, -CURB + 0.008, (238, 238, 232), cell=10, layer=LAYER["white"])
    drape(gm, yellow.intersection(roads), H, -CURB + 0.008, (246, 200, 30), cell=10, layer=LAYER["white"])
    drape(gm, grooves.intersection(S["roads"]).intersection(tb), H, -CURB + 0.011, (28, 28, 30), cell=10, layer=LAYER["white"])
    on_road = rails.intersection(S["roads"])
    drape(gm, on_road.intersection(tb), H, -CURB + 0.012, (175, 175, 178), cell=10, layer=LAYER["white"])  # polished rail head
    drape(gm, rails.difference(S["roads"]).intersection(tb), H, 0.07, (120, 118, 116), cell=10, layer=LAYER["white"])


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    blds = sources.buildings(margin=240)  # includes the backdrop ring outside the fence
    # swissALTI3D terrain; swissBUILDINGS3D ground surfaces sit 3.06 m lower on average (research/terrain.md)
    BIG = (AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)  # play area + backdrop ring
    H = terrain.heights(BIG, HGRID, z_shift=-3.06)
    nodes, els = sources.osm()
    LMS = [[s["x"], s["y"], round(float(H.at(s["x"], s["y"])), 2), s["heading"], s["name"], s.get("plaque", ""), int(s.get("flowers", False))]
           for s in json.load(open(os.path.join(os.path.dirname(__file__), "overrides", "landmark_signs.json")))["signs"]]
    BR = bridges.bridge_ways(nodes, els, AREA, H)  # elevated decks + piers (research/bridges.md)
    EX = bridges.exclusion(BR)
    S = streets.parse(nodes, els)
    G = groundcover.load(BIG)  # Amtliche Vermessung land cover (research/groundcover.md)
    S["av_green"] = G["green"].buffer(0)
    S["av_paved"] = G["gravel"].buffer(0)
    S["av_rail"] = G["rail"].buffer(0)
    S["ways"] = bridges.clip_ways(S["ways"], EX)  # no ground road/markings under bridge decks
    S["roads"] = S["roads"].difference(EX)
    S["plaza"] = S["plaza"].difference(EX)
    S["tram"] = [g for ln in S["tram"] for g in shapely.get_parts(ln.difference(EX)) if g.geom_type == "LineString" and g.length > 0.5]
    gastro.add_missing(S, box(*AREA).buffer(30))  # official licensed restaurants/bars (OGD) complete the OSM list
    # visible (above-ground) hydrants from the city water utility (OGD WVZ)
    hyd = json.load(open(OUT.parent.parent.parent / "data" / "raw" / "stadtzh_more" / "geo_hydranten__wvz_hydranten.geojson"))["features"]
    for ft in hyd:
        if ft["properties"].get("art_txt") == "Oberflurhydrant" and ft.get("geometry"):
            lon, lat = ft["geometry"]["coordinates"][:2]
            S["hydrants"].append(tuple(sources.geo.to_local(lon, lat)))
    white, yellow = streets.markings(S)
    rails = shapely.union_all([ln.offset_curve(o).buffer(0.035) for ln in S["tram"] for o in (-0.5, 0.5)])
    # grooved rails: the dark flangeway groove on the inner side of each rail
    grooves = shapely.union_all([ln.offset_curve(o).buffer(0.022) for ln in S["tram"] for o in (-0.44, 0.44)])
    bed = shapely.union_all([ln.buffer(1.4, cap_style="flat") for ln in S["tram"]])
    way_tree = STRtree([w["line"] for w in S["ways"] if w["hw"] != "service"])
    way_w = [w["w"] for w in S["ways"] if w["hw"] != "service"]
    main = shapely.union_all([w["line"] for w in S["ways"] if w["hw"] in streets.MAIN])
    C = citydata.load(BIG)
    AD, SG = addresses.address_rows(AREA, H), addresses.sign_rows(AREA, H)
    PS = plazasigns.rows(H)  # squares + dedication plaques at their surveyed places
    SG = [r for r in SG if not any(q[4] == r[4] and math.hypot(q[0] - r[0], q[1] - r[1]) < 12 for q in PS)] + PS
    TSG, TSL = TS.sign_rows(AREA, H, nodes, els), TS.signal_rows(AREA, H, nodes, els)
    # real parking bays are part of the carriageway (OSM widths are often too narrow for them)
    S["roads"] = shapely.union_all([S["roads"], cityprops.parking_bays(C, S)])
    poi_pts = shapely.points([(p["x"], p["y"]) for p in S["pois"]]) if S["pois"] else []

    def street_dist(x, y):
        p = Point(x, y)
        i = way_tree.nearest(p)
        return way_tree.geometries[i].distance(p) - way_w[i] / 2

    # OSM building tags (use, levels, colour, name) for every swissBUILDINGS3D building, via its footprint centre
    osm_bld = []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way" and "building" in t and len(e.get("nodes", [])) >= 4:
            pts = [nodes[n] for n in e["nodes"] if n in nodes]
            if len(pts) >= 4:
                poly = Polygon(pts).buffer(0)
                if not poly.is_empty:
                    osm_bld.append((poly, t))
    osm_tree = STRtree([p for p, _ in osm_bld])
    for b in blds:
        c = Point(b["center"][:2])
        hit = [osm_bld[j] for j in osm_tree.query(c) if osm_bld[j][0].contains(c)]
        b["osm"] = dict(hit[0][1]) if hit else {}
        fp = footprint(b)
        if fp is not None and fp.geom_type == "Polygon":
            b["osm"]["_gwr"] = gwr_for_building(np.asarray(fp.exterior.coords))

    # facade colour/style per address from photo notes (research/buildings/visual_notes.json)
    VIS = visual_overrides.load()
    addr_pts = []
    for e in els:
        t = e.get("tags", {})
        if (t.get("addr:street"), t.get("addr:housenumber")) in VIS:
            pts = [nodes[e["id"]]] if e["type"] == "node" and e["id"] in nodes else [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if pts:
                c = np.mean(pts, axis=0)
                addr_pts.append((Point(c), VIS[(t["addr:street"], t["addr:housenumber"])]))
    for b in blds:
        fp = footprint(b)
        if fp is None:
            continue
        hit = [v for p, v in addr_pts if fp.buffer(1.5).contains(p)]
        if hit:
            b["osm"]["_visual"] = hit[0]

    # footprints of all buildings, to detect party walls (Brandmauern)
    fps = [(b["id"], footprint(b)) for b in sources.buildings(margin=60)]
    fps = [(i, f) for i, f in fps if f is not None and not f.is_empty]
    fp_tree = STRtree([f for _, f in fps])

    def neighbour_fn(bid):
        def inside(x, y):
            p = Point(x, y)
            return any(fps[j][0] != bid and fps[j][1].contains(p) for j in fp_tree.query(p))
        return inside

    OUTDOOR = props.outdoor_ids()

    def inside_any(x, y):
        p = Point(x, y)
        return any(fps[j][1].contains(p) for j in fp_tree.query(p))

    play = Polygon(POLYGON)

    def hmap(tb):
        """Per-tile 2 m height map (int16 cm, base64) for exact walking height."""
        x0, y0 = tb.bounds[0], tb.bounds[1]
        n = int(TILE / HGRID) + 1
        gx, gy = np.meshgrid(x0 + np.arange(n) * HGRID, y0 + np.arange(n) * HGRID)
        z = H.at(gx.ravel(), gy.ravel())
        return {"x0": x0, "y0": y0, "step": HGRID, "w": n, "h": n,
                "zb64": base64.b64encode(np.round(z * 100).astype("<i2").tobytes()).decode()}

    def fence(tb):
        """Construction fence along the play-area edge: polylines [[x, y, z], ...] inside the tile."""
        edge = play.exterior.intersection(tb)
        out = []
        for g in getattr(edge, "geoms", [edge]):
            if g.geom_type == "LineString" and g.length > 1:
                pts = [g.interpolate(d) for d in np.append(np.arange(0, g.length, 3.5), g.length)]
                out.append([[round(p.x, 2), round(p.y, 2), round(float(H.at(p.x, p.y)), 2)] for p in pts])
        return out

    def do_tile(ix, iy):
        backdrop = is_backdrop(ix, iy)
        tb = box(ix * TILE, iy * TILE, (ix + 1) * TILE, (iy + 1) * TILE)
        bm, gm = Mesh(), Mesh()
        colliders, segs = [], []
        for b in blds:
            if not tb.contains(Point(b["center"][:2])):
                continue
            fp = footprint(b)
            near_poi = fp is not None and len(poi_pts) and bool(shapely.dwithin(poi_pts, fp, 4).any())
            b["shops"] = near_poi or main.distance(Point(b["center"][:2])) < 22
            b["pois"] = [(p["x"], p["y"], p["kind"]) for p in S["pois"]
                         if fp is not None and fp.distance(Point(p["x"], p["y"])) < 6]
            segs += add_building(bm, b, street_dist, neighbour_fn(b["id"]))
            if fp is not None and not fp.is_empty:
                for p in getattr(fp, "geoms", [fp]):
                    if p.geom_type == "Polygon":
                        colliders.append(np.round(np.asarray(p.exterior.coords)[:-1], 2).tolist())
        name = f"t_{ix}_{iy}"
        if backdrop:  # outside the fence: buildings, ground and trees only
            ground_tile(gm, S, tb, H, white, yellow, rails, bed, None, None, grooves)
            raw = RAW_OUT / f"{name}.glb"
            glb.write(raw, {"ground": gm.arrays(), "buildings": bm.arrays()})
            pack(raw, OUT / f"{name}.glb")
            mask, mask_n = props.road_mask(S["roads"], tb)
            meta = {"backdrop": 1, "colliders": [], "signs": [], "posters": [], "paths": [], "hmap": hmap(tb),
                    "trees": cityprops.city_props(C, S, tb, H, CURB)[0]["trees"],
                    "mask": {"x0": tb.bounds[0], "y0": tb.bounds[1], "n": mask_n, "res": 1.0, "depth": CURB, "bits": mask}}
            json.dump(meta, open(OUT / f"{name}.json", "w"), separators=(",", ":"))
            return {"name": name, "ix": ix, "iy": iy, "backdrop": 1}
        P, bays_w, bays_b = cityprops.city_props(C, S, tb, H, CURB)
        ground_tile(gm, S, tb, H, white, yellow, rails, bed, bays_w, bays_b, grooves)
        colliders += cityprops.car_colliders(P["cars"])
        mask, mask_n = props.road_mask(S["roads"], tb)
        P["bikes"] += props.wall_bikes(segs, tb, H)
        fz = fence(tb)
        for line in fz:  # the fence blocks the player
            for a, b2 in zip(line[:-1], line[1:]):
                seg = LineString([a[:2], b2[:2]]).buffer(0.3, cap_style="flat")
                if seg.geom_type == "Polygon" and not seg.is_empty:
                    colliders.append(np.round(np.asarray(seg.exterior.coords)[:-1], 2).tolist())
        sg = props.signs(S, [s for s in segs if not s.get("blank")], tb)
        meta = {
            "colliders": colliders,
            "hmap": hmap(tb),
            "fence": fz,
            **P,
            "wires": props.tram_wires(S["tram"], tb, H),
            "posters": (al := props.posters([s for s in segs if s.get("blank")], tb)),
            "lawn": props.lawn_spots(S["parks"], tb, H) + (tr := props.terraces(sg, S["roads"], OUTDOOR, H, inside_any))[1],
            "terraces": tr[0],
            "decals": props.decals(S, tb, H, CURB),
            "construction": props.construction(blds, segs, tb, lambda x, y: main.distance(Point(x, y))),
            "scooters": [[x, y, round(float(H.at(x, y)), 2), h, c] for x, y, h, c in
                         props.scooters(props.walk_paths(S["roads"], S["plaza"], tb), tb)],
            "schools": [[round(r[0], 1), round(r[1], 1)] for r in C.get("schools", []) if tb.contains(Point(r[0], r[1]))],
            "bridges": bridges.tile_rows(BR, tb),
            "landmarks": [r for r in LMS if tb.contains(Point(r[0], r[1]))],
            "trafficsigns": [r for r in TSG if tb.contains(Point(r[0], r[1]))],
            "signals": [r for r in TSL if tb.contains(Point(r[0], r[1]))],
            **{k: [[round(x, 2), round(y, 2), round(float(H.at(x, y)), 2), (h32(f"{k}{x:.0f}") % 628) / 100]
                   for x, y in S[k] if tb.contains(Point(x, y))] for k in ("hydrants", "bollards", "pingpong")},
            "housenumbers": [r for r in AD if tb.contains(Point(r[0], r[1]))],
            "streetsigns": [r for r in SG if tb.contains(Point(r[0], r[1]))],
            "wild": (wild := props.wild_posters([s for s in segs if s.get("blank")], al, tb)),
            "graffiti": props.graffiti([s for s in segs if s.get("blank")], al + wild, tb,
                                       lambda x, y: main.distance(Point(x, y))),
            "signs": sg,
            "paths": props.walk_paths(S["roads"], S["plaza"], tb),
            "mask": {"x0": tb.bounds[0], "y0": tb.bounds[1], "n": mask_n, "res": 1.0, "depth": CURB, "bits": mask},
        }
        raw = RAW_OUT / f"{name}.glb"
        glb.write(raw, {"ground": gm.arrays(), "buildings": bm.arrays()})
        pack(raw, OUT / f"{name}.glb")
        json.dump(meta, open(OUT / f"{name}.json", "w"), separators=(",", ":"))
        print(f"{name}: glb {(OUT / f'{name}.glb').stat().st_size / 1e6:.2f} MB, "
              + ", ".join(f"{k} {len(v)}" for k, v in meta.items() if isinstance(v, list)), flush=True)
        return {"name": name, "ix": ix, "iy": iy}

    # build tiles in parallel (fork: workers share the prepared data copy-on-write)
    global _DO
    _DO = do_tile
    todo = tiles()
    only = os.environ.get("GTZ_TILES")  # e.g. "4_-4,3_-5" to rebuild a few tiles
    if only:
        todo = [t for t in todo if f"{t[0]}_{t[1]}" in only.split(",")]
    with mp.get_context("fork").Pool(max(1, os.cpu_count() - 1)) as pool:
        index = pool.map(_run, todo, chunksize=1)
    if only:  # keep the full index
        index = [{"name": f"t_{ix}_{iy}", "ix": ix, "iy": iy, **({"backdrop": 1} if is_backdrop(ix, iy) else {})} for ix, iy in tiles()]
    # coarse 8 m height grid for the whole area (fallback before a tile's own height map is loaded)
    x0, y0, x1, y1 = play.buffer(240).bounds
    gx, gy = np.meshgrid(np.arange(x0, x1 + 8, 8.0), np.arange(y0, y1 + 8, 8.0))
    zc = H.at(gx.ravel(), gy.ravel())
    world = {"tile": TILE, "area": AREA, "polygon": POLYGON, "tiles": index,
             "heights": {"x0": x0, "y0": y0, "step": 8.0, "w": gx.shape[1], "h": gx.shape[0],
                         "zb64": base64.b64encode(np.round(zc * 100).astype("<i2").tobytes()).decode()}}
    json.dump(world, open(OUT / "world.json", "w"), separators=(",", ":"))
    print("pois", len(S["pois"]), "crossings", len(S["crossings"]))


_DO = None


def _run(t):
    try:
        return _DO(*t)
    except Exception:  # one bad tile must not abort the whole build
        import traceback
        print(f"TILE FAILED t_{t[0]}_{t[1]}:\n{traceback.format_exc()}", flush=True)


if __name__ == "__main__":
    build()
