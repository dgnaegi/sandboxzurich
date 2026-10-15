"""Load source data for the test area: swissBUILDINGS3D (parsed by the reel) and OSM (reel cache)."""
import json
import pickle

import numpy as np

from config import AREA, REEL, ROOT

import importlib.util  # noqa: E402

# reel helper (read-only); loaded by path so reel modules never shadow ours (e.g. gen_textures)
_spec = importlib.util.spec_from_file_location("reel_geo", REEL.parent / "src" / "geo.py")
geo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(geo)


def buildings(margin=0.0, area=None):
    """Buildings whose centroid lies in area (default config.AREA) +- margin.
    Prefers data/build/bld/*.pkl (parse_sb3d.py, whole game area), else the reel data."""
    x0, y0, x1, y1 = area if area is not None else AREA
    files = sorted((ROOT / "data" / "build" / "bld").glob("*.pkl"))
    if not files:
        files = sorted((REEL / "bld").glob("*.pkl"))
    out = []
    for f in files:
        for b in pickle.load(open(f, "rb")):
            c = np.concatenate([p for _, p in b["polys"]]).mean(0)
            if x0 - margin <= c[0] < x1 + margin and y0 - margin <= c[1] < y1 + margin:
                b["center"] = c
                out.append(b)
    return out


def osm():
    """Return (nodes: id -> local (x, y), elements). Prefers the full fetch (data/raw/osm/kreise.json)."""
    full = ROOT / "data" / "raw" / "osm" / "kreise.json"
    src = full if full.exists() else REEL / "osm" / "k45.json"
    print("osm source:", src.relative_to(ROOT.parent))
    els = json.load(open(src))["elements"]
    ids = [e["id"] for e in els if e["type"] == "node"]
    lon = np.array([e["lon"] for e in els if e["type"] == "node"])
    lat = np.array([e["lat"] for e in els if e["type"] == "node"])
    x, y = geo.to_local(lon, lat)
    return dict(zip(ids, zip(x.tolist(), y.tolist()))), els
