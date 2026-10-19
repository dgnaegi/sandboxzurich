"""Audit of tram track geometry vs the road surface (what build_testarea.py emits for S["tram"]).
usage: .venv/bin/python pipeline/audit_tramtracks.py [tag]  -> research/tram_tracks_<tag>.json (tag default 'now'), prints summary.
Axes are sampled every 2 m. Surface model = the drape offsets of build_testarea._ground_base / tram_track.py (TRACK_MODEL below):
  rail head z = H + head offset (on road / off road), reference = the carriageway surface (H_road - CURB) of the nearest road point
  within 3 m (own trassee further away: reference = the bed surface). 'high'/'low' = head more than 3 cm above/below the reference.
  'wall' = a carriageway edge (kerb face) within 1.2 m of the axis, i.e. kerb stones directly beside the rails (rails sit at +-0.5 m).  Bridge decks excluded (EX)."""
import json, os, sys
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point, box
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridges, road_height, sources, streets, terrain, terrain_cuts, tram_track  # noqa: E402
from config import AREA, HGRID  # noqa: E402

CURB, STEP = 0.12, 2.0


def main(tag):
    BIG = (AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260)
    H = terrain.heights(BIG, HGRID, z_shift=-3.06)
    terrain_cuts.apply(H)
    nodes, els = sources.osm()
    S = streets.parse(nodes, els)
    H_raw = H
    import inspect
    road_height.apply(H, S["ways"], **({"roads": S.get("roads")} if "roads" in inspect.signature(road_height.apply).parameters else {}))
    BR = bridges.bridge_ways(nodes, els, AREA, H, H_raw)
    EX = bridges.exclusion(BR)
    tram = [g for ln in S["tram"] for g in shapely.get_parts(ln.difference(EX)) if g.geom_type == "LineString" and g.length > 0.5]
    roads = tram_track.merge_into_roads(S['roads'], S['plaza'], tram)  # roads polygon as the build uses it for the ground
    S = dict(S, roads=roads)
    edge = roads.boundary
    shapely.prepare(roads); shapely.prepare(edge)
    rows = []
    for ln in tram:
        n = max(2, int(ln.length // STEP))
        for i in range(n):
            p = ln.interpolate((i + 0.5) / n, normalized=True)
            x, y = p.x, p.y
            inroad = roads.contains(p)
            de = edge.distance(p)
            hz = float(H.at(x, y))
            head = tram_track.head_z(hz, inroad, p, S)
            if inroad:
                ref_z = hz - CURB
            else:  # own trassee / plaza / lawn: the surface it sits in (bed or ground); the road kerb next to it is counted as 'wall'
                ref_z = tram_track.bed_z(hz, p, S)
            near_road = (not inroad) and de < 3.0  # off-road but beside a carriageway: head above the carriageway surface
            vs_road = head - (float(H.at(x, y)) - CURB) if near_road else 0.0
            rows.append((x, y, head - ref_z, de < 1.2, inroad, int(de < 1.8), vs_road))
    a = np.array(rows, float)
    d = a[:, 2]
    tot = len(a) * STEP
    out = {"length_m": tot, "high_m": float((d > 0.03).sum() * STEP), "low_m": float((d < -0.03).sum() * STEP),
           "wall_m": float(a[:, 3].sum() * STEP), "wall_offroad_m": float(((a[:, 3] > 0) & (a[:, 4] == 0)).sum() * STEP), "bad_any_m": float(((d > 0.03) | (d < -0.03) | (a[:, 3] > 0)).sum() * STEP),
           "median_dz_cm": float(np.median(d) * 100), "p95_dz_cm": float(np.percentile(d, 95) * 100), "kerb_within_1.8m": float(a[:, 5].sum() * STEP), "high_vs_road_m": float((a[:, 6] > 0.03).sum() * STEP), "offroad_m": float((a[:, 4] == 0).sum() * STEP)}
    Path(sys.argv[0]).resolve().parent.parent.joinpath(f"research/tram_tracks_{tag}.json").write_text(json.dumps({"summary": out, "samples": a.round(3).tolist()}))
    for k, v in out.items():
        print(f"{k:14s} {v:10.1f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "now")
