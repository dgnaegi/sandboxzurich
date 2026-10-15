"""Shared helpers for landmark model scripts: coordinates, footprints, ground height."""
import pickle, sys, glob
from pathlib import Path
import numpy as np
from pyproj import Transformer
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
_t = Transformer.from_crs(4326, 2056, always_xy=True).transform


def ll(lat, lon):
    e, n = _t(lon, lat)
    return e - 2681400.0, n - 1248700.0


_cache = None


def all_buildings():
    global _cache
    if _cache is None:
        _cache = []
        for f in sorted(glob.glob(str(ROOT / "data/build/bld/*.pkl"))):
            for b in pickle.load(open(f, "rb")):
                g = [p[:, :2] for k, p in b["polys"] if k == 0]
                allp = np.concatenate([p for _, p in b["polys"]])
                polys = []
                for q in g:
                    try:
                        pg = Polygon(q).buffer(0)
                        if pg.area > 0.5: polys.append(pg)
                    except Exception: pass
                if not polys: continue
                fp = unary_union(polys)
                _cache.append({"id": b["id"], "zmax": float(allp[:, 2].max()), "zmin": float(allp[:, 2].min()), "fp": fp, "c": allp[:, :2].mean(0)})
    return _cache


def near(x, y, r):
    return [b for b in all_buildings() if np.hypot(b["c"][0] - x, b["c"][1] - y) < r]


def ground(x, y):
    global _h
    try:
        _h
    except NameError:
        import terrain
        from config import AREA
        _h = terrain.heights(tuple([AREA[0]-260, AREA[1]-260, AREA[2]+260, AREA[3]+260]), 2.0, z_shift=-3.06)
    return float(_h.at(x, y))


_osm = None


def osm_named(x, y, r, keys=("name",)):
    """OSM ways with building tag or name near (x, y): list of (tags, shapely Polygon)."""
    global _osm
    if _osm is None:
        import sources
        nodes, els = sources.osm()
        _osm = []
        for e in els:
            if e["type"] == "way" and "nodes" in e and len(e["nodes"]) > 3:
                t = e.get("tags", {})
                if "building" in t or "man_made" in t:
                    try:
                        _osm.append((t, Polygon([nodes[n] for n in e["nodes"] if n in nodes]).buffer(0)))
                    except Exception: pass
    return [(t, g) for t, g in _osm if g.centroid.distance(Point(x, y)) < r]


def outline(fp, tol=0.5):
    """Merge wall-split polygons into one clean Polygon (largest), simplified."""
    g = fp.buffer(0.4, join_style=2).buffer(-0.4, join_style=2)
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda p: p.area)
    return g.simplify(tol)


def bid(prefix):
    return [b for b in all_buildings() if b["id"].startswith(prefix)][0]


def hide_points(fps):
    return [[round(p.representative_point().x, 1), round(p.representative_point().y, 1)] for p in fps]


import json as _json, subprocess as _sp

OUTDIR = ROOT / "web" / "public" / "models" / "landmarks"
RAWDIR = ROOT / "data" / "build" / "landmarks"
OVR = ROOT / "pipeline" / "overrides" / "landmarks_k45.json"


def finish(model, name, title, ox, oy, oz, hide, reg=True):
    """Write GLB, compress with gltfpack, register in overrides/landmarks_k45.json."""
    OUTDIR.mkdir(parents=True, exist_ok=True); RAWDIR.mkdir(parents=True, exist_ok=True)
    raw = RAWDIR / f"{name}.glb"; model.write(str(raw))
    out = OUTDIR / f"{name}.glb"
    r = _sp.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(out), "-cc", "-kn"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:])
    print(f"{name}: {model.tri_count()} tris, " + ", ".join(f"{k}={m.tris()}" for k, m in model.mats.items()) + f", glb {out.stat().st_size // 1024} kB")
    if reg:
        d = _json.load(open(OVR)) if OVR.exists() else {"landmarks": []}
        d["landmarks"] = [e for e in d["landmarks"] if e["name"] != title]
        d["landmarks"].append({"name": title, "model": f"/models/landmarks/{name}.glb", "x": round(ox, 2), "y": round(oy, 2),
                               "z": round(oz, 2), "heading": 0, "hide": hide})
        _json.dump(d, open(OVR, "w"), indent=1)
        import merge; merge.main() if hasattr(merge, 'main') else None


def localize(poly, ox, oy):
    from shapely.affinity import translate
    return translate(poly, -ox, -oy)
