"""Build the M1 test area (Langstrasse/Helvetiaplatz) into web/public/tiles: one glb + meta per 200 m tile.

Usage: .venv/bin/python pipeline/build_testarea.py
"""
import os

# one BLAS/OpenMP thread per worker: 9 forked workers x N threads oversubscribed the CPU (load ~90 on 10 cores)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")
import base64
import json
import time
import math
import multiprocessing as mp
import os
import subprocess

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box
from shapely.strtree import STRtree
import markings_override  # langA hook
import glb
import addresses
import bridges
import plazasigns
import names_inst
import playgrounds
import sites
import citydata
import gastro
import ground_paint
import places_detail
import osm_buildings
import ortho_roofs
import rooftops  # roof furniture (pipeline/rooftops.py)
import terrain_cuts
import tram_track
import water  # rivers/canals (pipeline/water.py)
import road_height
import groundcover
import visual_overrides
import shopfronts_v3
import terrain
import traffic_signs as TS
from gwr import gwr_for_building
import cityprops
import yards  # YARDS: courtyards/front gardens (pipeline/yards.py)
import details_osm  # street details from OSM tags (pipeline/details_osm.py)
import props
import sources
import streets
from config import AREA, HGRID, OUT, POLYGON, TILE, is_backdrop, tiles
from facade import add_building
from mesh import Heights, Mesh, drape
from styles import LAYER, h32

CURB = 0.12  # carriageway is lowered by this much
ROAD_CELL = float(os.environ.get("SBZ_ROAD_CELL", "6"))  # drape cell of the asphalt: the mesh only has vertices on cell borders (road_cell, research/bumps.md)
GUT = 0.22  # Rinnstein width (fidelity S4: narrower)
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
        mesh.add(pts, np.array([[0, 2, 1], [0, 3, 2]], np.uint32), n, (255, 255, 255),  # procedural granite (ground_tex.curb), tint = none
                 uv=np.array([[0, 0], [L, 0], [L, CURB], [0, CURB]]), layer=LAYER["curb"])
        if L > 0.3:  # Rinnstein: setts, 0.22 m wide, along the curb foot
            q = np.array([[a[0], a[1], za - CURB + 0.004], [b[0], b[1], zb - CURB + 0.004],
                          [b[0] + n[0] * GUT, b[1] + n[1] * GUT, zb - CURB + 0.004], [a[0] + n[0] * GUT, a[1] + n[1] * GUT, za - CURB + 0.004]], np.float32)
            mesh.add(q, np.array([[0, 1, 2], [0, 2, 3]], np.uint32), np.array([0, 0, 1.0]), (255, 255, 255),
                     uv=np.array([[0, 0], [L, 0], [L, GUT], [0, GUT]]), layer=LAYER["gutter"])


def ground_tile(gm, S, tb, H, white, yellow, rails, bed, bays_white=None, bays_blue=None, grooves=None):
    try:
        return _ground_tile(gm, S, tb, H, white, yellow, rails, bed, bays_white, bays_blue, grooves)
    except shapely.errors.GEOSException:  # rare overlay failure: retry without the AV land cover refinement
        print("ground_tile: GEOS overlay failed, falling back to OSM-only ground", flush=True)
        S2 = {k: v for k, v in S.items() if not k.startswith("av_")}
        return _ground_tile(gm, S2, tb, H, white, yellow, rails, bed, bays_white, bays_blue, grooves)


def _ground_tile(gm, S, tb, H, white, yellow, rails, bed, bays_white=None, bays_blue=None, grooves=None):
    _ground_base(gm, S, tb, H, white, yellow, rails, bed, bays_white, bays_blue, grooves)
    ground_paint.paint(gm, S, tb, H)  # coloured markings (pipeline/ground_paint.py)
    places_detail.ground(gm, tb, H, S["roads"])  # square/park ground patterns (pipeline/places_detail.py)


def _ground_base(gm, S, tb, H, white, yellow, rails, bed, bays_white=None, bays_blue=None, grooves=None):
    roads = S["roads"].intersection(tb)
    plaza, parks = S["plaza"].intersection(tb), S["parks"].intersection(tb)
    walk = tb.difference(S["roads"]).difference(S["plaza"]).difference(S["parks"])
    if S.get("water_poly") is not None:  # water bodies: bed + water surface come from pipeline/water.py
        walk = walk.difference(S["water_poly"])
    if S.get("av_rail") is not None:  # railway land: low ballast, the rail tiles (railways.py) sit on top
        rl = walk.intersection(S["av_rail"].intersection(tb))
        drape(gm, rl, H, -0.08, (150, 142, 132), cell=TILE / 10, layer=LAYER["dach_kies"], uv_scale=1.5)
        walk = walk.difference(rl)
    # sidewalks along streets; everything further away is courtyard / front garden
    side = walk.intersection(S["roads"].buffer(6.0).union(S["plaza"].buffer(3.0)))
    if S.get("av_green") is not None:  # the AV never marks a Trottoir green: lawn strips, tree pits and green traffic islands stay lawn
        side = side.difference(S["av_green"].intersection(tb))
    yard = walk.difference(side)
    drape(gm, side, H, 0.0, (255, 255, 255), cell=TILE / 10, layer=LAYER["sidewalk"], uv_scale=5.0)
    if S.get("av_green") is not None:  # official land cover decides courtyards: lawn vs paved (AV Kanton ZH)
        g_av = yard.intersection(S["av_green"].intersection(tb))
        drape(gm, g_av, H, 0.005, (235, 240, 225), cell=TILE / 10, layer=LAYER["grass"], uv_scale=5.0)
        p_av = yard.difference(g_av).intersection(S["av_paved"].intersection(tb))
        drape(gm, p_av, H, 0.005, (215, 210, 200), cell=TILE / 10, layer=LAYER["roof_flat"], uv_scale=2.0)
        yard = yard.difference(g_av).difference(p_av)
    if S.get("av_bld") is not None:  # roads2: ground under AV buildings that are hidden by a landmark model (Bahnhofplatz/HB) is paved, never lawn
        pb = yard.intersection(S["av_bld"].intersection(tb))
        if not pb.is_empty:
            drape(gm, pb, H, 0.005, (215, 210, 200), cell=TILE / 10, layer=LAYER["roof_flat"], uv_scale=2.0)
            yard = yard.difference(pb)
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
    drape(gm, roads, H, -CURB, (255, 255, 255), cell=ROAD_CELL, layer=LAYER["asphalt"], uv_scale=5.0)  # road_cell: bump fix, see research/bumps.md
    curbs(gm, streets.curb_faces(roads, tb), H)
    top = S["roads"].boundary.buffer(0.16).difference(S["roads"]).difference(S["plaza"]).intersection(tb)
    drape(gm, top, H, 0.006, (205, 203, 196), cell=10, layer=LAYER["white"])
    drape(gm, white.intersection(roads), H, -CURB + 0.008, (238, 238, 232), cell=10, layer=LAYER["white"])
    drape(gm, yellow.intersection(roads), H, -CURB + 0.008, (246, 200, 30), cell=10, layer=LAYER["white"])
    tram_track.paint(gm, S, tb, H, rails, grooves, bed)  # rails flush in the asphalt, own trassee ballast without kerb


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW_OUT.mkdir(parents=True, exist_ok=True)
    _t0 = time.time()
    _lap = lambda what: print(f"[{time.time() - _t0:7.1f}s] {what}", flush=True)  # prep profiling
    blds = sources.buildings(margin=240)  # includes the backdrop ring outside the fence
    nodes0, els0 = sources.osm()
    # detailed landmark models replace swissBUILDINGS3D buildings: overrides/landmarks_*.json "hide" points
    import glob as _g
    _lme = [e for f in _g.glob(os.path.join(os.path.dirname(__file__), "overrides", "landmarks_*.json"))
            for e in json.load(open(f)).get("landmarks", [])]
    hide = [Point(p) for e in _lme for p in e.get("hide", [])]
    hide_ids = tuple(i for e in _lme for i in e.get("hide_ids", []))  # swissBUILDINGS3D / OSM building ids (roof-only canopies have no footprint to hit)
    # walkable landmarks (e.g. Zuerich HB hall): the hidden buildings' footprints are NOT colliders; the entry's own "colliders" rings are
    walk_hide = [Point(p) for e in _lme if e.get("walkable") for p in e.get("hide", [])]
    walk_ids = tuple(i for e in _lme if e.get("walkable") for i in e.get("hide_ids", []))
    lm_colliders = [r for e in _lme for r in e.get("colliders", [])]
    # tram/bus shelters come from world/stops.ts: drop low swissBUILDINGS3D canopies right at stops
    _st = shapely.points([nodes0[e["id"]] for e in els0 if e["type"] == "node" and e["id"] in nodes0 and (
        (e.get("tags") or {}).get("public_transport") in ("platform", "stop_position")
        or (e.get("tags") or {}).get("highway") == "bus_stop" or (e.get("tags") or {}).get("railway") == "tram_stop")])
    _stt, n0 = STRtree(_st), len(blds)

    def _shelter(b):
        g = [p for k, p in b["polys"] if k == 0 and len(p) >= 3]
        if not g or (b["h"] or 0) >= 5.0:
            return False
        fp = Polygon(np.asarray(g[0])[:, :2]).buffer(0)
        return fp.area < 1200 and len(_stt.query(fp.buffer(10))) > 0
    blds = [b for b in blds if not _shelter(b)]
    print(f"stops: {n0 - len(blds)} shelter canopies dropped")
    def _hidden(b):
        if hide_ids and str(b.get("id", "")).startswith(hide_ids):
            return True
        return any(Polygon(np.asarray(p)[:, :2]).buffer(0).contains(h)
                   for h in hide if abs(h.x - b["center"][0]) < 200 and abs(h.y - b["center"][1]) < 200
                   for k, p in b["polys"] if k == 0 and len(p) >= 3)
    lm_hidden = []  # buildings replaced by landmark models: no mesh, but their footprint stays a collider
    if hide or hide_ids:
        n0 = len(blds)
        lm_hidden += [b for b in blds if _hidden(b)]
        blds = [b for b in blds if not _hidden(b)]
        print(f"landmarks: {n0 - len(blds)} buildings replaced by models")
    # swissALTI3D terrain; swissBUILDINGS3D ground surfaces sit 3.06 m lower on average (research/terrain.md)
    BIG = (AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)  # play area + backdrop ring
    H = terrain.heights(BIG, HGRID, z_shift=-3.06)
    terrain_cuts.apply(H)  # rail cuttings under buildings (overrides/terrain_cuts.json)
    nodes, els = nodes0, els0
    S = streets.parse(nodes, els)
    import copy as _copy; H_raw = _copy.deepcopy(H)  # roads2: terrain before road smoothing (bridge clearance over trenches)
    if not os.environ.get("SBZ_NO_ROADH"):  # A/B switch for the ride test
        road_height.apply(H, S["ways"])  # smooth road surface (pipeline/road_height.py): carriageway, sidewalks, hmap, vehicles share it
    terrain_cuts.apply(H, lock_only=True)  # sunken underpass floors ("lock": true) must survive the road smoothing (Langstrassen-Unterfuehrung)
    blds = osm_buildings.update(blds, nodes, els, H, footprint, Polygon(POLYGON))  # post-2019 changes
    if hide or hide_ids:  # OSM re-adds footprints of the hidden landmarks (no 2019 building left under them): hide them again
        n0 = len(blds)
        lm_hidden += [b for b in blds if _hidden(b)]
        blds = [b for b in blds if not _hidden(b)]
        print(f"landmarks: {n0 - len(blds)} OSM buildings replaced by models")
    LMS = [[s["x"], s["y"], round(float(H.at(s["x"], s["y"])), 2), s["heading"], s["name"], s.get("plaque", ""), int(s.get("flowers", False))]
           for s in json.load(open(os.path.join(os.path.dirname(__file__), "overrides", "landmark_signs.json")))["signs"]]
    BR = bridges.bridge_ways(nodes, els, AREA, H, H_raw)  # roads2; elevated decks + piers (research/bridges.md)
    EX = bridges.exclusion(BR)
    _lap("osm/terrain/bridges/streets")
    G = groundcover.load(BIG)  # Amtliche Vermessung land cover (research/groundcover.md)
    # snapped to 1 cm: robust overlays with the OSM-derived street polygons
    S["av_green"] = shapely.set_precision(G["green"].buffer(0), 0.01)
    S["av_paved"] = shapely.set_precision(G["gravel"].buffer(0), 0.01)
    S["av_rail"] = shapely.set_precision(G["rail"].buffer(0), 0.01)
    S["av_bld"] = shapely.set_precision(G["building"].buffer(0), 0.01)  # roads2
    # OSM parks/playgrounds include paved schoolyards (Kanzlei): lawn only where AV says green, the rest is paved
    parks = S["parks"]
    S["parks"] = shapely.set_precision(parks.intersection(S["av_green"].buffer(0.5)), 0.01)
    S["av_paved"] = shapely.set_precision(shapely.union_all([S["av_paved"], parks.difference(S["parks"])]), 0.01)
    # ground streets that pass UNDER a deck keep their carriageway (the exclusion only removes the bridge's own chain)
    EXR = road_height.ground_exclusion(EX, BR, S["ways"])
    S["ways"] = road_height.clip_ways(S["ways"], EX, EXR, BR)  # no ground road/markings under the bridge's own deck
    S["roads"] = S["roads"].difference(EXR)
    S["plaza"] = S["plaza"].difference(EX)
    # --- water (pipeline/water.py): lowers the bed into H, removes the water polygon from the ground layers
    W = water.prepare(H, G, EX, BR, nodes, els)
    S["water_poly"] = None if W.empty else W.poly
    if not W.empty:
        for _k in ("roads", "plaza", "parks"):
            S[_k] = S[_k].difference(W.poly)
    # --- /water
    import road_exclude  # roads2
    OBJ_ZONE = road_exclude.object_zone(W, BR)  # roads2: no bikes/racks/scooters/bins/workers/parked cars in open water or on tracks
    S["tram"] = [g for ln in S["tram"] for g in shapely.get_parts(ln.difference(EX)) if g.geom_type == "LineString" and g.length > 0.5]
    gastro.add_missing(S, box(*AREA).buffer(30))  # official licensed restaurants/bars (OGD) complete the OSM list
    # visible (above-ground) hydrants from the city water utility (OGD WVZ)
    hyd = json.load(open(OUT.parent.parent.parent / "data" / "raw" / "stadtzh_more" / "geo_hydranten__wvz_hydranten.geojson"))["features"]
    for ft in hyd:
        if ft["properties"].get("art_txt") == "Oberflurhydrant" and ft.get("geometry"):
            lon, lat = ft["geometry"]["coordinates"][:2]
            S["hydrants"].append(tuple(sources.geo.to_local(lon, lat)))
    white, yellow = streets.markings(S)
    white, yellow = markings_override.apply(S, white, yellow)  # HOOK langA: measured Langstrasse markings (pipeline/markings_override.py)
    rails, grooves, bed = tram_track.geometry(S["tram"])  # rails, flangeways, bed (pipeline/tram_track.py)
    S["roads"] = tram_track.merge_into_roads(S["roads"], S["plaza"], S["tram"])  # street-running track is carriageway: no kerb walls beside the rails
    S["plaza"] = S["plaza"].difference(S["roads"])
    way_tree = STRtree([w["line"] for w in S["ways"] if w["hw"] != "service"])
    way_w = [w["w"] for w in S["ways"] if w["hw"] != "service"]
    main = shapely.union_all([w["line"] for w in S["ways"] if w["hw"] in streets.MAIN])
    _lap("groundcover + tram geometry")
    C = citydata.load(BIG)
    details_osm.prepare(nodes, els)
    # private trees (courtyards, gardens) are missing in the city tree register: add OSM natural=tree
    _ct = STRtree([Point(t[0], t[1]) for t in C.get("trees", [])]) if C.get("trees") else None
    _n = 0
    for e in els:
        tg = e.get("tags") or {}
        if e["type"] == "node" and tg.get("natural") == "tree" and e["id"] in nodes:
            x, y = nodes[e["id"]]
            if _ct is not None and len(_ct.query(Point(x, y).buffer(3.0))):
                continue
            try:
                cr = float(str(tg.get("diameter_crown", "")).split()[0])
            except (ValueError, IndexError):
                cr = 7.0
            C["trees"].append((x, y, (tg.get("genus") or tg.get("species", "")).split(" ")[0], cr, "osm"))
            _n += 1
    print(f"trees: {_n} private trees from OSM")
    AD, SG = addresses.address_rows(AREA, H), addresses.sign_rows(AREA, H)
    PG = playgrounds.rows(nodes, els, H)  # real playgrounds incl. courtyards
    PS = plazasigns.rows(H)  # squares + dedication plaques at their surveyed places
    SG = [r for r in SG if not any(q[4] == r[4] and math.hypot(q[0] - r[0], q[1] - r[1]) < 12 for q in PS)] + PS
    AD = AD + names_inst.gwr_numbers(AREA, H, AD, S)  # every GWR entrance gets its house number
    SG = SG + names_inst.junction_poles(AREA, H, SG, S)  # pole signs at junctions without a wall corner
    names_inst.add_institutions(S, nodes, els)  # schools, churches, GZ, big shops (also mapped as areas)
    TSG, TSL = TS.sign_rows(AREA, H, nodes, els), TS.signal_rows(AREA, H, nodes, els)
    # real parking bays are part of the carriageway (OSM widths are often too narrow for them)
    S["roads"] = shapely.union_all([S["roads"], cityprops.parking_bays(C, S)])
    if S["roads"].geom_type not in ("Polygon", "MultiPolygon"):  # a GeometryCollection has boundary None -> crash in _ground_base
        S["roads"] = shapely.union_all([g for g in shapely.get_parts(S["roads"]) if g.geom_type in ("Polygon", "MultiPolygon")])
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
    _lap("citydata/trees/playgrounds/parking")
    VIS = visual_overrides.load()
    addr_pts = []
    for e in els:
        t = e.get("tags", {})
        if (t.get("addr:street"), t.get("addr:housenumber")) in VIS:
            pts = [nodes[e["id"]]] if e["type"] == "node" and e["id"] in nodes else [nodes[n] for n in e.get("nodes", []) if n in nodes]
            if pts:
                c = np.mean(pts, axis=0)
                addr_pts.append((Point(c), VIS[(t["addr:street"], t["addr:housenumber"])]))
    addr_tree = STRtree([p for p, _ in addr_pts]) if addr_pts else None  # was O(buildings x addresses)
    for b in blds:
        fp = footprint(b)
        if fp is None or addr_tree is None:
            continue
        hit = addr_tree.query(fp.buffer(1.5), predicate="contains")
        if len(hit):
            b["osm"]["_visual"] = addr_pts[int(min(hit))][1]  # first match in address order, as before
    # fallback: OSM building without addr tags (e.g. Aemtlerstrasse 82) -> note by the GWR entrance address inside the footprint
    for b in blds:
        if "_visual" in b["osm"]:
            continue
        g = b["osm"].get("_gwr") or {}
        v = VIS.get((g.get("street"), g.get("nr")))
        fp = footprint(b)
        if v and fp is not None and fp.buffer(1.5).contains(Point(g["x"], g["y"])):
            b["osm"]["_visual"] = v

    # footprints of all buildings, to detect party walls (Brandmauern)
    fps = [(b["id"], footprint(b)) for b in sources.buildings(margin=60)]
    fps = [(i, f) for i, f in fps if f is not None and not f.is_empty]
    fp_tree = STRtree([f for _, f in fps])
    # YARDS: shrub areas + private nDSM trees missing in the register (before tiles are built)
    yards.prepare(els, nodes, [(r[0], r[1]) for r in PG])
    yards.add_private_trees(C, [f for _, f in fps], AREA)
    yards.drop_deck_trees(C, BR, H)  # no trees on / through bridge decks (pipeline/audit_trees_deck.py)

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
        colliders, segs, roof_rows = [], [], []
        for b in blds:
            if not tb.contains(Point(b["center"][:2])):
                continue
            fp = footprint(b)
            near_poi = fp is not None and len(poi_pts) and bool(shapely.dwithin(poi_pts, fp, 4).any())
            b["shops"] = near_poi or main.distance(Point(b["center"][:2])) < 22
            b["pois"] = [(p["x"], p["y"], p["kind"], shopfronts_v3.shop_notes(p)) for p in S["pois"]
                         if fp is not None and fp.distance(Point(p["x"], p["y"])) < 6]
            fpb = footprint(b)
            b["_roof_rgb"] = ortho_roofs.roof_rgb(fpb) if fpb is not None and fpb.geom_type == "Polygon" else None
            try:  # ROOFTOPS hook: dormers, PV, units, terraces (rooftops.py)
                _rr, _rf = rooftops.analyse(b)
                roof_rows += _rr
                b["_roofs"] = _rf
            except Exception as _e:
                print("rooftops failed", b.get("id"), _e, flush=True)
            segs += add_building(bm, b, street_dist, neighbour_fn(b["id"]))
            if fp is not None and not fp.is_empty:
                for p in getattr(fp, "geoms", [fp]):
                    if p.geom_type == "Polygon":
                        colliders.append(np.round(np.asarray(p.exterior.coords)[:-1], 2).tolist())
        for ring in lm_colliders:  # walkable landmarks bring their own wall rings (every tile the ring's bbox touches)
            rx, ry = [p[0] for p in ring], [p[1] for p in ring]
            if min(rx) < tb.bounds[2] and max(rx) > tb.bounds[0] and min(ry) < tb.bounds[3] and max(ry) > tb.bounds[1]:
                colliders.append(ring)
        for b in lm_hidden:  # landmark models have no colliders of their own: walls of the replaced buildings
            if (walk_ids and str(b.get("id", "")).startswith(walk_ids)) or any(Polygon(np.asarray(p)[:, :2]).buffer(0).contains(h) for h in walk_hide
                                                                                  for k, p in b["polys"] if k == 0 and len(p) >= 3):
                continue  # walkable interior: no solid footprint
            if tb.contains(Point(b["center"][:2])):
                fp = footprint(b)
                for p in getattr(fp, "geoms", [fp]) if fp is not None and not fp.is_empty else []:
                    if p.geom_type == "Polygon":
                        colliders.append(np.round(np.asarray(p.exterior.coords)[:-1], 2).tolist())
        name = f"t_{ix}_{iy}"
        if backdrop:  # outside the fence: buildings, ground and trees only
            ground_tile(gm, S, tb, H, white, yellow, rails, bed, None, None, grooves)
            WM = water.tile(W, gm, tb)  # water
            raw = RAW_OUT / f"{name}.glb"
            glb.write(raw, {"ground": gm.arrays(), "buildings": bm.arrays(), "water": WM.arrays() if WM else None})
            pack(raw, OUT / f"{name}.glb")
            mask, mask_n = props.road_mask(S["roads"], tb)
            meta = {"backdrop": 1, **water.meta(W, tb), "colliders": [], "signs": [], "posters": [], "paths": [], "hmap": hmap(tb),
                    "trees": cityprops.city_props(C, S, tb, H, CURB)[0]["trees"],
                    "mask": {"x0": tb.bounds[0], "y0": tb.bounds[1], "n": mask_n, "res": 1.0, "depth": CURB, "bits": mask}}
            json.dump(meta, open(OUT / f"{name}.json", "w"), separators=(",", ":"))
            return {"name": name, "ix": ix, "iy": iy, "backdrop": 1}
        P, bays_w, bays_b = cityprops.city_props(C, S, tb, H, CURB)
        ground_tile(gm, S, tb, H, white, yellow, rails, bed, bays_w, bays_b, grooves)
        WM = water.tile(W, gm, tb)  # water
        colliders += water.colliders(W, tb)  # water
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
        PD = places_detail.tile_meta(tb, H, P)  # square/park furniture (overrides/places_detail.json)
        colliders += PD.pop("_colliders", [])
        DT = details_osm.tile_meta(tb, H, S, C, P, inside_any, segs)  # columns, post boxes, hedges, leaves ... (details.ts)
        colliders += DT.pop("_colliders")
        YD = yards.tile_meta(tb, H, S, C, P, [fps[j][1] for j in fp_tree.query(tb.buffer(20))])  # YARDS
        SM = sites.tile_meta(tb, H)  # real construction sites (Stadt Zürich OGD), research/sites.md
        colliders += SM.pop("colliders")
        meta = {
            **SM,
            **DT,
            **YD,
            **water.meta(W, tb),  # water
            "places": PD,
            "playground": [r for r in PG if tb.contains(Point(r[0], r[1]))],
            "colliders": colliders,
            "hmap": hmap(tb),
            "fence": fz,
            "roofs": rooftops.pack(roof_rows),
            **P,
            "wires": props.tram_wires(S["tram"], tb, H),
            "posters": (al := props.posters([s for s in segs if s.get("blank")], tb)),
            "lawn": props.lawn_spots(S["parks"], tb, H) + (tr := props.terraces(sg, S["roads"], OUTDOOR, H, inside_any))[1],
            "terraces": tr[0],
            "decals": markings_override.decals(props.decals(S, tb, H, CURB), tb, H, CURB),  # HOOK langA
            "construction": props.construction(blds, segs, tb, lambda x, y: main.distance(Point(x, y))) + sites.scaffold_rows(tb, segs),
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
            "wild": (wild := props.wild_posters([s for s in segs if s.get("blank")], al, tb, main_dist=lambda x, y: main.distance(Point(x, y)))),
            "graffiti": props.graffiti([s for s in segs if s.get("blank")], al + wild, tb,
                                       lambda x, y: main.distance(Point(x, y))),
            "signs": names_inst.fallback(sg, tb, H, S),  # + wall signs for venues without a shopfront segment
            "paths": props.walk_paths(S["roads"], S["plaza"], tb),
            "mask": {"x0": tb.bounds[0], "y0": tb.bounds[1], "n": mask_n, "res": 1.0, "depth": CURB, "bits": mask},
        }
        _rx = road_exclude.filter_meta(meta, OBJ_ZONE)  # roads2
        raw = RAW_OUT / f"{name}.glb"
        glb.write(raw, {"ground": gm.arrays(), "buildings": bm.arrays(), "water": WM.arrays() if WM else None})
        pack(raw, OUT / f"{name}.glb")
        json.dump(meta, open(OUT / f"{name}.json", "w"), separators=(",", ":"))
        print(f"{name}: glb {(OUT / f'{name}.glb').stat().st_size / 1e6:.2f} MB, rx {_rx}, "
              + ", ".join(f"{k} {len(v)}" for k, v in meta.items() if isinstance(v, list)), flush=True)
        return {"name": name, "ix": ix, "iy": iy}

    # build tiles in parallel (fork: workers share the prepared data copy-on-write)
    global _DO
    _DO = do_tile
    todo = tiles()
    only = os.environ.get("SBZ_TILES")  # e.g. "4_-4,3_-5" to rebuild a few tiles
    if only:
        todo = [t for t in todo if f"{t[0]}_{t[1]}" in only.split(",")]
    _lap("prep done, tiles start")
    with mp.get_context("fork").Pool(max(1, os.cpu_count() - 1)) as pool:
        index = pool.map(_run, todo, chunksize=1)
    _lap("tiles done")
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
