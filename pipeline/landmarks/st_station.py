"""Platform-level station models for Hardbruecke / Altstetten / Wiedikon (GLB per station, registered in overrides/landmarks_stations.json).

Needs data/build/stations_geo.json (st_data.py). Content: platform slabs for perrons missing in OSM (Altstetten 3/4, 6/7), canopies there,
light strips under the OSM canopies, benches, bins, departure boards with neutral clock, sector signs, platform number signs, ticket machines,
glass shelters, lamp posts, stair flights (Hardbruecke/Wiedikon to bridge/street), stair openings (Altstetten underpass), lift towers, bike racks.
Run: .venv/bin/python pipeline/landmarks/st_station.py [hardbruecke|altstetten|wiedikon ...]"""
import sys, os, json, math, subprocess
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box as sbox
from shapely.ops import unary_union
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "pipeline"))
import k93_lib as L, k93_kit as K, st_kit as S
from k93_lib import hexc, shade
import terrain

OUTD = ROOT / "web/public/models/landmarks"; OVR = ROOT / "pipeline/overrides/landmarks_stations.json"
LIFT_RISE = {"hardbruecke": 7.4, "altstetten": 3.5, "wiedikon": 8.4}
STYLE = {"altstetten": dict(roof=hexc("#8e8a82"), under=hexc("#7a7368"), col=hexc("#857e72"), conc="#9a9286", colw=0.55, deck=(128, 129, 132, 255), rail=hexc("#8a9096"), backwall=False),
         "hardbruecke": dict(roof=hexc("#8a8b8a"), under=hexc("#6f6d69"), col=hexc("#7d7b76"), conc="#8d8b86", colw=0.9, deck=(128, 129, 132, 255), rail=hexc("#b3261e"), backwall=True),
         "wiedikon": dict(roof=hexc("#8c9296"), under=hexc("#b9bec1"), col=hexc("#6f777c"), colw=0.3, deck=(128, 129, 132, 255), rail=hexc("#7d8387"), backwall=False)}
NAME = {"hardbruecke": "Zürich Hardbrücke", "altstetten": "Zürich Altstetten", "wiedikon": "Zürich Wiedikon"}
HEAD_ALONG = 1.0


def make_zf(p):
    """platform top z at xy: project on the nearest edge polyline and interpolate its per-vertex z_top."""
    E = []
    for e in p["edges"]:
        ls = LineString(e["line"]); pts = np.array(e["line"]); cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
        E.append((ls, cum, np.array(e["z_top"])))
    def zf(pt):
        q = Point(*pt); ls, cum, z = min(E, key=lambda t: t[0].distance(q))
        return float(np.interp(ls.project(q), cum, z))
    return zf


def build(sid, geo, osm):
    st = geo[sid]; per = st["perrons"]; STY = STYLE[sid]
    M = L.Model(); refs = [p["ref"].replace("/", " ") for p in per]
    A, E, uv = S.make_atlas(refs, NAME[sid]); kit = S.Kit(M, A, E, uv, conc=STY.get("conc")); SO = kit.S; kit.rail_col = STY['rail']
    rng = np.random.default_rng(hash(sid) % 1000)
    roofs = [Polygon(r["pts"]).buffer(0) for r in osm["roofs"] if len(r["pts"]) >= 4 and r["tags"].get("building") in ("roof", "train_station")]
    allp = unary_union([Polygon(p["polygon"]) for p in per])
    spots = {"waiting": [], "sit": []}; walk = []; decks = []
    for pi, p in enumerate(per):
        pg = Polygon(p["polygon"]).buffer(0); c = np.array(p["centre"]); u = np.array(p["axis"]); n = np.array([-u[1], u[0]]); Lp, W = p["length_m"], p["width_m"]
        zf = make_zf(p)
        P = lambda du, dv: c + u * du + n * dv
        # which lateral sides have a track edge
        tracksides = []
        for e in p["edges"]:
            mid = np.array(LineString(e["line"]).interpolate(0.5, normalized=True).coords[0])
            s = 1.0 if np.dot(mid - c, n) > 0 else -1.0
            if s not in tracksides: tracksides.append(s)
        island = len(tracksides) >= 2
        vrow = 0.0 if island else -tracksides[0] * max(0.5, W / 2 - 2.6)       # furniture row (centre line or back side)
        ang = math.atan2(u[1], u[0])
        inside = lambda pt, b=0.35: pg.buffer(-b).contains(Point(*pt))
        rf = unary_union([r.intersection(pg.buffer(1.0)) for r in roofs if r.intersects(pg)]) if roofs else Polygon()
        covered = lambda pt: (not rf.is_empty) and rf.contains(Point(*pt))
        # ---- walkable platform deck: centre line through the polygon (follows curvature), z from the edge heights
        cl, wmin = [], 99.0
        for du in np.arange(-Lp / 2, Lp / 2 + 0.1, 12.0):
            ch = pg.intersection(LineString([P(du, -W), P(du, W)]))
            if ch.is_empty: continue
            ch = ch if ch.geom_type == "LineString" else max(getattr(ch, "geoms", [ch]), key=lambda g: g.length)
            m_ = np.array(ch.interpolate(0.5, normalized=True).coords[0]); cl.append([round(float(m_[0]), 2), round(float(m_[1]), 2), round(zf(m_), 2)]); wmin = min(wmin, ch.length)
        if len(cl) > 1:
            decks.append({"p": cl, "g": [round(q[2] - 0.55, 2) for q in cl], "b": [round(q[2] - 0.9, 2) for q in cl], "w": round(max(2.0, wmin * 0.9), 2), "kind": "foot", "name": f"Perron {p['ref']} {NAME[sid]}"})
        # ---- derived perron: slab, kerb, safety line, tactile strip, canopy
        if not p["in_osm"]:
            EA, EB = [np.array(q) for q in p["edges"][0]["line"]], [np.array(q) for q in p["edges"][1]["line"]]
            ZA, ZB = p["edges"][0]["z_top"], p["edges"][1]["z_top"]
            for k in range(len(EA) - 1):
                a0, a1, b0, b1 = EA[k], EA[k + 1], EB[k], EB[k + 1]
                kit.fq(SO, [(*a0, ZA[k]), (*a1, ZA[k + 1]), (*b1, ZB[k + 1]), (*b0, ZB[k])], STY["deck"], (0, 0, 1))
                for (q0, q1, zq0, zq1, o0, o1) in ((a0, a1, ZA[k], ZA[k + 1], b0, b1), (b0, b1, ZB[k], ZB[k + 1], a0, a1)):
                    d0 = (o0 - q0) / max(1e-6, np.hypot(*(o0 - q0))); d1 = (o1 - q1) / max(1e-6, np.hypot(*(o1 - q1)))
                    def ln(t0, t1):
                        return [(*(q0 + d0 * t0), zq0 + 0.012), (*(q1 + d1 * t0), zq1 + 0.012), (*(q1 + d1 * t1), zq1 + 0.012), (*(q0 + d0 * t1), zq0 + 0.012)]
                    kit.fq(SO, ln(0.0, 0.40), hexc("#c9cacb"), (0, 0, 1)); kit.fq(SO, ln(0.62, 1.1), hexc("#e6e6e4"), (0, 0, 1)); kit.fq(SO, ln(1.14, 1.24), hexc("#b4673a"), (0, 0, 1))
                    kit.fq(SO, [(*q0, zq0), (*q1, zq1), (*q1, zq1 - 0.65), (*q0, zq0 - 0.65)], hexc("#a9a7a1"), (-d0[0], -d0[1], 0))
            for idx, sg in ((0, -1), (-1, 1)):    # end walls
                a, b = EA[idx], EB[idx]; zz = ZA[idx]
                kit.fq(SO, [(*a, zz), (*b, zz), (*b, zz - 0.65), (*a, zz - 0.65)], hexc("#a9a7a1"), (u[0] * sg * (-1 if idx == 0 else 1), u[1] * sg * (-1 if idx == 0 else 1), 0))
            # canopy over OSM roof outline
            for r in roofs:
                if not r.intersects(pg): continue
                ro = r.intersection(pg.buffer(1.4))
                for g in ([ro] if ro.geom_type == "Polygon" else list(ro.geoms)):
                    if g.area < 20: continue
                    zr = zf(g.representative_point().coords[0]) + 4.2
                    kit.canopy(g, zr, 0.38, col=STY["roof"], under=STY["under"], under_tex=True)
                    gg = np.array(g.representative_point().coords[0]); lo = [np.dot(np.array(q) - c, u) for q in g.exterior.coords]
                    for du in np.arange(min(lo) + 4, max(lo) - 3, 12.0):
                        pt = P(du, vrow if not island else 0.0)
                        if g.buffer(0.5).contains(Point(*pt)): kit.column(pt, zf(pt), zr, STY["colw"], ang, STY["col"])
        # ---- light strips under every canopy over this perron (OSM canopies hang at +3.6 m, own canopies at +4.2)
        if not rf.is_empty:
            for du in np.arange(-Lp / 2 + 3, Lp / 2 - 2, 5.0):
                for dv in ((-1.4, 1.4) if island else (vrow,)):
                    pt = P(du, dv)
                    if covered(pt) and inside(pt):
                        zt = zf(pt); zr = zt + (3.6 if p["in_osm"] else 4.2)
                        M.box(kit.LM, (pt[0], pt[1], zr - 0.08), (1.25, 0.32, 0.1), (255, 255, 255, 255), rot=ang)
        # ---- red platform back wall with showcases under the canopy (Hardbruecke photos: red wall, showcases, silver building above)
        if STY["backwall"] and not island and not rf.is_empty:
            bs = -tracksides[0]; la = c + n * bs * (W / 2 - 0.25) - u * Lp / 2; lb = c + n * bs * (W / 2 - 0.25) + u * Lp / 2
            cut = LineString([la, lb]).intersection(rf)
            for g in ([cut] if cut.geom_type == "LineString" else list(getattr(cut, "geoms", []))):
                if g.geom_type != "LineString" or g.length < 8: continue
                a_, b_ = np.array(g.coords[0]), np.array(g.coords[-1]); a_ = a_ + (b_ - a_) / g.length * 0.5; b_ = b_ - (b_ - a_) / g.length * 0.5
                z_a, z_b = zf(a_), zf(b_); inn = -n * bs
                kit.fq(SO, [(*a_, z_a), (*b_, z_b), (*b_, z_b + 3.0), (*a_, z_a + 3.0)], hexc("#a9281f"), (inn[0], inn[1], 0))
                for t0 in np.arange(10.0, g.length - 8, 22.0):
                    q0 = a_ + (b_ - a_) / g.length * t0; q1 = a_ + (b_ - a_) / g.length * (t0 + 4.5); qa = q0 + inn * 0.04; qb = q1 + inn * 0.04
                    kit.fq(kit.GL, [(*qa, zf(qa) + 1.1), (*qb, zf(qb) + 1.1), (*qb, zf(qb) + 2.25), (*qa, zf(qa) + 2.25)], W4 if False else (255, 255, 255, 255), (inn[0], inn[1], 0))
        # ---- furniture
        S_ = lambda du, dv=None: P(du, vrow if dv is None else dv)
        def ok(pt, b=0.5): return inside(pt, b)
        for i, du in enumerate(np.arange(-Lp / 2 + 14, Lp / 2 - 10, 26.0)):             # benches (alternate sides on islands)
            dv = (vrow + (0.55 if i % 2 else -0.55)) if island else vrow
            pt = P(du + rng.uniform(-3, 3), dv)
            if ok(pt):
                kit.bench(pt, ang, zf(pt)); spots["sit"].append([round(float(pt[0]), 2), round(float(pt[1]), 2), round(zf(pt), 2), round((ang + (math.pi / 2 if (dv - vrow) < 0 or not island else 0)) % (2 * math.pi), 3), 6])
        for du in np.arange(-Lp / 2 + 30, Lp / 2 - 20, 42.0):                          # bins
            pt = P(du, vrow + (0.4 if island else 0.55))
            if ok(pt): kit.bin(pt, zf(pt))
        for k, fr in enumerate((0.18, 0.5, 0.82)):                                       # departure board + neutral clock
            pt = P(-Lp / 2 + Lp * fr, vrow)
            if ok(pt, 0.3): kit.board_pylon(pt, ang, zf(pt))
        for k, fr in enumerate((0.07, 0.35, 0.65, 0.93)):                                # platform number signs
            pt = P(-Lp / 2 + Lp * fr, vrow + (0.0 if island else 0.0))
            if ok(pt, 0.3) and not covered(pt): kit.perron_sign(pt, ang, zf(pt), pi)
            elif ok(pt, 0.3): kit.perron_sign(pt, ang, zf(pt), pi, hang=zf(pt) + (4.2 if not p["in_osm"] else 3.6) - 1.0, rods=True)
        for k, letter in enumerate("ABCDEF"):                                            # sector signs
            pt = P(-Lp / 2 + Lp * (k + 0.5) / 6, vrow + (0.0 if island else 0.0))
            pt = P(-Lp / 2 + Lp * (k + 0.5) / 6 + 6.0, vrow + (-0.9 if island else 0.9) )
            if ok(pt, 0.3): kit.sector_sign(pt, ang, zf(pt), letter)
        for fr in (0.3, 0.7):                                                            # station name plates
            pt = P(-Lp / 2 + Lp * fr, vrow + (1.0 if island else -0.2))
            if ok(pt, 0.3): kit.name_plate(pt, ang, zf(pt), hang=2.9)
        pt = P(-Lp / 2 + Lp * 0.36, vrow + (-1.4 if island else 0.0))                    # glass shelter
        if ok(pt, 1.4): kit.waiting_room(pt, ang, zf(pt))
        for du in np.arange(-Lp / 2 + 10, Lp / 2 - 8, 26.0):                             # lamp posts on uncovered stretches
            pt = P(du, vrow + (0.0 if island else 0.0))
            if ok(pt, 0.5) and not covered(pt): kit.lamp_post(pt, zf(pt))
        # ---- waiting people: along the edge zone (1.6-2.4 m from the track edge), facing the tracks
        for e in p["edges"]:
            ls_ = LineString(e["line"]); a, b = np.array(ls_.coords[0]), np.array(ls_.coords[-1]); d = (b - a) / np.hypot(*(b - a)); Le = float(ls_.length)
            mid = np.array(ls_.interpolate(0.5, normalized=True).coords[0]); inw = n * (1.0 if np.dot(c - mid, n) > 0 else -1.0)
            for k, s in enumerate(np.arange(8.0, Le - 8, 11.0)):
                for j in range(1 + (k % 2)):
                    base_ = np.array(ls_.interpolate(float(np.clip(s + rng.uniform(-3, 3) + j * 0.8, 0, Le))).coords[0]); pt = base_ + inw * rng.uniform(1.7, 2.4)
                    if inside(pt, 0.4):
                        face = -inw; spots["waiting"].append([round(float(pt[0]), 2), round(float(pt[1]), 2), round(zf(pt), 2), round(float(face[0]), 3), round(float(face[1]), 3)])
        # ---- stairs / lifts / openings that belong to this perron
        for s in st["steps"]:
            pts = np.array(s["pts"]); lng = LineString(pts).length
            if lng < 4.5: continue
            d0, d1 = pg.buffer(0.2).distance(Point(*pts[0])), pg.buffer(0.2).distance(Point(*pts[-1]))
            lv = (s.get("level") or "").split(";")[0]
            try: a_lv = int(lv)
            except ValueError: a_lv = None
            pl = int(p.get("level", 0))
            rising = (a_lv >= pl) if a_lv is not None else (sid != "altstetten")      # Altstetten: unlevelled steps lead down into the passage
            if rising and d0 < 3.2 and d0 <= d1:     # run starts on the platform and rises: real stair flight
                rise = min(lng * 0.17 / 0.30, LIFT_RISE[sid] + 0.4)
                z0 = zf(pts[0])
                if (s.get("incline") or "up") == "up" and rise > 1.8:
                    kit.stair_flight(pts[0], pts[-1], z0, z0 + rise, 2.4 if lng > 9 else 1.9)
                    walk.append({"perron": p["ref"], "from": pts[0].round(2).tolist(), "to": pts[-1].round(2).tolist(), "z0": round(z0, 2), "z1": round(z0 + rise, 2), "width": 2.4, "osm_steps": s["id"]})
                    decks.append({"p": [[round(float(pts[0][0]), 2), round(float(pts[0][1]), 2), round(z0, 2)], [round(float(pts[-1][0]), 2), round(float(pts[-1][1]), 2), round(z0 + rise, 2)]], "g": [round(z0 - 0.5, 2), round(z0 + rise - 0.5, 2)], "b": [round(z0 - 1, 2), round(z0 + rise - 1, 2)], "w": 2.2, "kind": "foot", "name": f"Treppe Perron {p['ref']} {NAME[sid]}"})
            elif not rising and (d1 < 3.2 or d0 < 3.2):   # run ends on the platform and descends: opening
                top, bot = (pts[-1], pts[0]) if d1 <= d0 else (pts[0], pts[-1])
                zl = zf(top); dirv = bot - top
                kit.stair_opening(top, dirv, zl, 2.4 if lng > 6 else 1.8, min(lng, 5.0))
                walk.append({"perron": p["ref"], "from": top.round(2).tolist(), "to": bot.round(2).tolist(), "z0": round(zl, 2), "z1": round(zl - lng * 0.17 / 0.30, 2), "width": 2.4, "osm_steps": s["id"], "kind": "down"})
        for l in st["lifts"]:
            pt = np.array(l["pt"])
            if pg.buffer(0.8).contains(Point(*pt)) or pg.distance(Point(*pt)) < 1.2:
                kit.lift(pt, ang, zf(pt), zf(pt) + LIFT_RISE[sid])
                if pi == 0 or True: pass
        # ticket machine near the first access
        acc = [np.array(l["pt"]) for l in st["lifts"] if pg.distance(Point(*l["pt"])) < 1.5] + [np.array(s["pts"][0]) for s in st["steps"] if pg.distance(Point(*s["pts"][0])) < 1.5 and LineString(s["pts"]).length > 4.5]
        for a_ in acc[:2]:
            pt = a_ + (c - a_) / max(1e-6, np.hypot(*(c - a_))) * 3.2
            if ok(pt, 0.5): kit.ticket_machine(pt, ang + math.pi / 2, zf(pt))
    # bike stands on OSM bicycle_parking areas near the platforms (uncovered ones; nodes have no outline)
    zg = terrain.heights((allp.bounds[0] - 200, allp.bounds[1] - 200, allp.bounds[2] + 200, allp.bounds[3] + 200), 2.0, z_shift=-3.06)
    nrack = 0
    for o in osm["other"]:
        t = o["tags"]
        if t.get("amenity") != "bicycle_parking" or o["type"] != "way" or len(o["pts"]) < 4 or t.get("covered") == "yes" or t.get("layer") not in (None, "0", "1"): continue
        pg = Polygon(o["pts"]).buffer(0)
        if pg.is_empty or pg.area < 20 or pg.distance(allp) > 140: continue
        rr = np.array(pg.minimum_rotated_rectangle.exterior.coords)[:4]; e0, e1 = rr[1] - rr[0], rr[2] - rr[1]
        ax = e0 if np.hypot(*e0) >= np.hypot(*e1) else e1; ax = ax / np.hypot(*ax); nn = np.array([-ax[1], ax[0]]); a_ = math.atan2(ax[1], ax[0])
        cen = np.array(pg.centroid.coords[0]); ext = pg.buffer(-0.4)
        for dv in np.arange(-5, 6) * 2.2:
            run = [cen + ax * du + nn * dv for du in np.arange(-25, 25, 0.7)]
            run = [q for q in run if ext.contains(Point(*q))]
            if len(run) >= 3:
                mid = np.mean(run, 0); kit.bike_rack(mid, a_, float(zg.at(*mid)), n=len(run), pitch=0.7); nrack += len(run)
    print("  bike stands:", nrack)
    return M, spots, walk, allp, decks


def main(ids):
    geo = json.load(open(ROOT / "data/build/stations_geo.json"))
    reg = json.load(open(OVR)) if OVR.exists() else {"landmarks": []}
    for sid in ids:
        osm = json.load(open(ROOT / f"research/stations/osm_{sid}.json"))
        M, spots, walk, allp, decks = build(sid, geo, osm)
        json.dump(decks, open(ROOT / f"research/stations/decks_{sid}.json", "w"))
        cen = allp.centroid; ox, oy = round(float(cen.x), 1), round(float(cen.y), 1)
        H = terrain.heights((ox - 20, oy - 20, ox + 20, oy + 20), 2.0, z_shift=-3.06); oz = round(float(H.at(ox, oy)), 2)
        M.ox, M.oy, M.oz = ox, oy, oz
        raw = ROOT / f"data/build/landmarks/stp_{sid}.glb"; raw.parent.mkdir(parents=True, exist_ok=True); M.write(str(raw))
        out = OUTD / f"stp_{sid}.glb"
        r = subprocess.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(out), "-cc", "-kn"], capture_output=True, text=True)
        if r.returncode: print(r.stderr[-300:]); import shutil; shutil.copy(raw, out)
        print(sid, "tris", M.tris(), "glb kB", out.stat().st_size // 1024, "origin", ox, oy, oz, "spots", {k: len(v) for k, v in spots.items()}, "walk", len(walk))
        title = f"Perrons {NAME[sid]}"
        reg["landmarks"] = [e for e in reg["landmarks"] if e["name"] != title]
        reg["landmarks"].append({"name": title, "model": f"/models/landmarks/stp_{sid}.glb", "x": ox, "y": oy, "z": oz, "heading": 0, "hide": []})
        json.dump({"waiting": spots["waiting"], "sit": spots["sit"], "walkable_flights": walk, "note": "waiting [x,y,z,faceDx,faceDy]; sit [x,y,z,heading,type6]; flights: stair ramps for a future height collider"},
                  open(ROOT / f"research/stations/spots_{sid}.json", "w"))
    json.dump(reg, open(OVR, "w"), indent=1)
    alld = []
    for sid in ("hardbruecke", "altstetten", "wiedikon"):
        f = ROOT / f"research/stations/decks_{sid}.json"
        if f.exists(): alld += json.load(open(f))
    json.dump({"decks": alld, "piers": []}, open(ROOT / "web/public/data/station_decks.json", "w"), separators=(",", ":"))
    print("station_decks.json:", len(alld), "decks")
    import merge; merge.main()


if __name__ == "__main__":
    main(sys.argv[1:] or ["hardbruecke", "altstetten", "wiedikon"])
