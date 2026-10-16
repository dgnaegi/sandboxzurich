"""Station geometry (Hardbruecke, Altstetten, Wiedikon): official platform edges + OSM platforms -> research/stations/platforms.json
and data/build/stations_geo.json (richer, used by st_station.py).

Sources: SBB open data 'BehiG Haltekantesegment' (data.sbb.ch dataset 21197_behig-haltekantesegment: perron no., type, edge length,
track-axis positions at start/end of the Haltekante; cached in data/raw/stations/behig_seg_zh.json) + OSM (railway=platform polygons,
highway=steps, elevator nodes). Platform edge = 1.67 m from the track axis (SBB standard, P55 -> 55 cm above rail head).
Run: .venv/bin/python pipeline/landmarks/st_data.py"""
import sys, json, math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, LineString, Point
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / "pipeline"))
from common import ll

EDGE_OFF = 1.67
ST = {"hardbruecke": ("Zürich Hardbrücke", "Zürich Hardbrücke", 47.385106, 8.517025), "altstetten": ("Zürich Altstetten", "Zürich Altstetten", 47.390993, 8.489195),
      "wiedikon": ("Zürich Wiedikon", "Zürich Wiedikon", 47.371413, 8.523581)}
OSM_PL = {"hardbruecke": {30582104: "1", 47122091: "2/3", 30582170: "4"}, "altstetten": {106506131: "2"}, "wiedikon": {111516672: "1", 111516669: "2/3"}}


def rect_frame(pg):
    c = np.array(pg.minimum_rotated_rectangle.exterior.coords)[:4]
    e0, e1 = c[1] - c[0], c[2] - c[1]
    ax = e0 if np.hypot(*e0) >= np.hypot(*e1) else e1
    L = float(np.hypot(*ax)); u = ax / L
    n = np.array([-u[1], u[0]])
    cen = np.array(pg.centroid.coords[0])
    W = float(min(np.hypot(*e0), np.hypot(*e1)))
    return cen, u, n, L, W


def main():
    import terrain, sources
    # own copy of the rail height logic (railways.py is owned by another agent): terrain z, smoothed along the track, +0.29 rail head
    AREA = (-2849.0, -2069.0, 1952.0, 1454.0)
    H = terrain.heights(AREA, 2.0, z_shift=-3.06)
    nodes, els = sources.osm()
    pts_all = []
    for e in els:
        t = e.get("tags", {})
        if e["type"] != "way" or t.get("railway") != "rail" or t.get("service") not in (None, "yard", "crossover") or t.get("tunnel") in ("yes", "building_passage"): continue
        if not all(n in nodes for n in e["nodes"]): continue
        xy = np.array([nodes[n] for n in e["nodes"]])
        if len(xy) < 2 or not (-2400 < xy[:, 0].mean() < 1200 and -1700 < xy[:, 1].mean() < 1300): continue
        seg = np.linalg.norm(np.diff(xy, axis=0), axis=1); pts = [xy[0]]
        for i in range(len(seg)):
            k = max(1, int(math.ceil(seg[i] / 4.0)))
            for j in range(1, k + 1): pts.append(xy[i] + (xy[i + 1] - xy[i]) * j / k)
        pts = np.array(pts); z = np.asarray(H.at(pts[:, 0], pts[:, 1]), float)
        if t.get("bridge") not in (None, "no") and len(z) > 2: z = np.interp(np.arange(len(z)), [0, len(z) - 1], [z[0], z[-1]])
        elif len(z) > 4:
            pad = np.pad(z, 3, mode="edge"); z = np.convolve(pad, np.ones(7) / 7, mode="valid"); z[0], z[-1] = H.at(*pts[0]), H.at(*pts[-1])
        pts_all.append(np.column_stack([pts, z]))
    from shapely import STRtree
    samp = np.concatenate(pts_all)
    tree = STRtree([Point(p[0], p[1]) for p in samp])
    rz = lambda x, y: float(samp[tree.nearest(Point(x, y))][2]) + 0.29
    beh = json.load(open(ROOT / "data/raw/stations/behig_seg_zh.json"))
    out, geo = {}, {}
    for sid, (nm, bez, lat, lon) in ST.items():
        osm = json.load(open(ROOT / f"research/stations/osm_{sid}.json"))
        from shapely.ops import linemerge, unary_union
        rails = [LineString(t["pts"]) for t in osm["tracks"] if t["tags"].get("railway") == "rail" and len(t["pts"]) > 1 and t["tags"].get("tunnel") not in ("yes",)]
        rail_u = unary_union(rails)
        # official track-axis points at the Haltekante start/end
        tr = {}
        for r in beh:
            if r["bezeichnung_offiziell"] != bez: continue
            k = (r["perron_nr"], r["kundengleisnr"]); d = tr.setdefault(k, {"len": r["perronkante_laenge"], "typ": r["perrontyp"]})
            if r["segment_info"] == "Beginn Haltekante": d["b"] = ll(r["geopos"]["lat"], r["geopos"]["lon"])
            if r["segment_info"] == "Ende Haltekante": d["e"] = ll(r["geopos"]["lat"], r["geopos"]["lon"])
        pls = {}
        for k, d in tr.items():
            if "b" in d and "e" in d: pls.setdefault(k[0], []).append((k[1], d))
        osmpoly = {}
        for p in osm["platforms"]:
            ref = OSM_PL[sid].get(p["id"])
            if ref and len(p["pts"]) > 3: osmpoly[ref] = (p["id"], Polygon(p["pts"]).buffer(0))
        fmt = lambda pts: [[round(float(x), 2), round(float(y), 2)] for x, y in pts]
        import shapely
        rails_main = [r for r, t in ((LineString(t["pts"]), t) for t in osm["tracks"] if t["tags"].get("railway") == "rail" and len(t["pts"]) > 1 and t["tags"].get("tunnel") != "yes") if t["tags"].get("service") is None]
        def track_for(a, b):
            """OSM main-track line that runs along the official axis a->b (OSM and the official data differ by up to ~3 m),
            extended straight at both ends so the platform can have its official length."""
            ax = LineString([a, b]); Lx = ax.length; cands = []
            for r in rails_main:
                pts = [Point(c) for c in shapely.segmentize(r, 5.0).coords]
                pr = [(ax.project(q), ax.distance(q)) for q in pts]
                pr = [(t_, d_) for t_, d_ in pr if 0 < t_ < Lx]
                if len(pr) < 2: continue
                cands.append((float(np.mean([d_ for _, d_ in pr])), max(t_ for t_, _ in pr) - min(t_ for t_, _ in pr), r))
            cands = [c for c in cands if c[1] > 60 and c[0] < 4.8]
            if not cands: return None
            bd = min(c[0] for c in cands)
            sel = [c[2] for c in cands if c[0] <= bd + 0.8]
            m = unary_union(sel)
            if m.geom_type == "MultiLineString": m = linemerge(m)
            m = max(list(m.geoms), key=lambda g: g.length) if m.geom_type == "MultiLineString" else m
            co = list(m.coords)
            if np.dot(np.array(co[-1]) - np.array(co[0]), np.array(b) - np.array(a)) < 0: co = co[::-1]
            t0 = np.array(co[1]) - np.array(co[0]); t1 = np.array(co[-1]) - np.array(co[-2])
            co = [tuple(np.array(co[0]) - t0 / np.hypot(*t0) * 60)] + co + [tuple(np.array(co[-1]) + t1 / np.hypot(*t1) * 60)]
            return LineString(co)
        perrons = []
        for ref in sorted(set(list(pls) + list(osmpoly))):
            rec = {"ref": ref, "tracks": [], "height_above_rail_m": 0.55, "edge_offset_from_track_axis_m": EDGE_OFF}
            gl = sorted(pls.get(ref, []))
            for g_, d in gl: rec["type"], rec["edge_length_m"] = d["typ"], round(d["len"], 1)
            poly = None; psrc = None; ed = []; strips = None
            if ref in osmpoly:
                oid, poly = osmpoly[ref]; psrc = f"osm:way/{oid}"
                ring = np.array(poly.exterior.coords)
                flag = [rail_u.distance(Point((ring[i] + ring[i + 1]) / 2)) < 2.8 for i in range(len(ring) - 1)]
                # group consecutive flagged segments (ring is closed: start at an unflagged segment)
                n_ = len(flag); st0 = next((i for i in range(n_) if not flag[i]), 0); run = []
                groups = []
                for k in range(n_):
                    i = (st0 + k) % n_
                    if flag[i]: run.append(i)
                    elif run: groups.append(run); run = []
                if run: groups.append(run)
                for gr in groups:
                    pts = [ring[gr[0]]] + [ring[i + 1] for i in gr]
                    if LineString(pts).length < 25: continue
                    ed.append({"pts": pts})
                # official gleis number for each edge by distance to the official axis
                for e in ed:
                    mid = Point(LineString(e["pts"]).interpolate(0.5, normalized=True))
                    best = min(((LineString([d["b"], d["e"]]).distance(mid), g_) for g_, d in gl), default=(99, "?"))
                    e["track"] = best[1] if best[0] < 7.0 else "?"
            elif len(gl) == 2:
                (g1, d1), (g2, d2) = gl
                Ta, Tb = track_for(d1["b"], d1["e"]), track_for(d2["b"], d2["e"])
                if Ta is None or Tb is None: print("  no OSM track for", sid, ref); continue
                bb = np.array([d1["b"], d2["b"]]); ee = np.array([d1["e"], d2["e"]]); u = ee.mean(0) - bb.mean(0); Lu = float(np.hypot(*u)); u = u / Lu
                n_s = max(2, int(Lu / 4.0)); Ea, Eb, zs = [], [], []
                for k in range(n_s + 1):
                    x = bb.mean(0) + u * Lu * k / n_s
                    pa = np.array(Ta.interpolate(Ta.project(Point(*x))).coords[0]); pb = np.array(Tb.interpolate(Tb.project(Point(*x))).coords[0])
                    dd = pb - pa; w = float(np.hypot(*dd)); dd = dd / w
                    Ea.append(pa + dd * EDGE_OFF); Eb.append(pb - dd * EDGE_OFF)
                poly = Polygon(Ea + Eb[::-1]).buffer(0); psrc = "derived: SBB BehiG length/position + OSM track lines, edge = axis -+ 1.67 m"
                ed = [{"pts": Ea, "track": g1}, {"pts": Eb, "track": g2}]
            if poly is None: continue
            if poly.geom_type != "Polygon": poly = max(poly.geoms, key=lambda g: g.area)
            cen, u, n, Lr, W = rect_frame(poly)
            lvl = 0
            if ref in osmpoly:
                tg = next((q["tags"] for q in osm["platforms"] if q["id"] == osmpoly[ref][0]), {})
                try: lvl = int(str(tg.get("level", "0")).split(";")[0])
                except ValueError: lvl = 0
            elif sid == "wiedikon": lvl = -1
            rec.update(level=lvl, length_m=round(Lr, 1), width_m=round(W, 1), centre=[round(float(cen[0]), 2), round(float(cen[1]), 2)],
                       axis=[round(float(u[0]), 4), round(float(u[1]), 4)], polygon=fmt(list(poly.exterior.coords)), polygon_source=psrc, in_osm=ref in osmpoly)
            rec["edges"] = [{"track": e["track"], "line": fmt(e["pts"]), "z_top": [round(rz(x, y) + 0.55, 2) for x, y in e["pts"]], "source": "osm-polygon track side" if ref in osmpoly else "derived"} for e in ed]
            rec["tracks"] = [e["track"] for e in ed]
            rec["z_top_centre"] = round(rz(*cen) + 0.55, 2)
            perrons.append(rec)
        steps = [{"id": s["id"], "pts": s["pts"], "incline": s["tags"].get("incline"), "level": s["tags"].get("level")} for s in osm["steps"]]
        lifts = [{"id": s["id"], "pt": np.mean(s["pts"], 0).round(2).tolist()} for s in osm["lifts"]]
        out[sid] = {"name": nm, "didok": {"hardbruecke": 3000, "altstetten": 3001, "wiedikon": 3002}.get(sid), "ref_latlon": [lat, lon], "ref_local": [round(v, 1) for v in ll(lat, lon)], "perrons": perrons}
        geo[sid] = {**out[sid], "steps": steps, "lifts": lifts}
    meta = {"generated_by": "pipeline/landmarks/st_data.py", "units": "local metres (origin LV95 2681400/1248700), z = world height of platform top incl. terrain z_shift -3.06",
            "sources": ["SBB Open Data: BehiG Haltekantesegment (data.sbb.ch/explore/dataset/21197_behig-haltekantesegment), Perron nr/type/length, track axis at Haltekante start/end; licence https://data.sbb.ch/page/licence (Open-Data-Lizenz, attribution 'Quelle: SBB')",
                        "OpenStreetMap contributors (ODbL): railway=platform polygons"],
               "note": "edges[].line = polyline of the TRACK-SIDE platform edge (local m); z_top per vertex = rail head (terrain z + 0.29) + 0.55 m. Track axis = edge shifted 1.67 m away from the platform (SBB P55 standard). For in_osm=true perrons the edge is the OSM polygon side that lies <2.8 m from an OSM rail; for in_osm=false (Altstetten 3/4, 6/7: not mapped in OSM) polygon and edges are derived from the OSM track lines (edge = track -+ 1.67 m) with the official SBB length/position; these perrons' slab, kerb, white line, tactile strip and canopy are built in web/public/models/landmarks/stp_*.glb, so pipeline/railways.py must NOT build them again (keep OSM tracks as they are: official and OSM track positions differ by up to ~3 m, the platforms follow OSM). edges[].track = official track number ('?' = not in the official list).",}
    (ROOT / "research/stations/platforms.json").write_text(json.dumps({"meta": meta, "stations": out}, ensure_ascii=False, indent=1))
    (ROOT / "data/build").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/build/stations_geo.json").write_text(json.dumps(geo, ensure_ascii=False))
    for sid, s in out.items():
        for p in s["perrons"]: print(sid, p["ref"], p.get("type"), p["length_m"], "x", p["width_m"], "osm" if p["in_osm"] else "DERIVED", p["centre"], "z", p["z_top_centre"], [(e["track"], len(e["line"])) for e in p["edges"]])


if __name__ == "__main__":
    main()
