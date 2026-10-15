"""Fetch all OSM data for the study area in parts, merge to data/raw/osm/kreise.json.
Usage: python pipeline/fetch_osm.py   (skips parts that already exist)"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import area  # noqa: E402
import overpass  # noqa: E402

# overpass-api.de is the only mirror that answered reliably (2026-10-14); others hang -> put it first
overpass.MIRRORS = [m for m in overpass.MIRRORS if 'overpass-api.de' in m] + [m for m in overpass.MIRRORS if 'overpass-api.de' not in m]
OUT = area.ROOT / "data" / "raw" / "osm"
P = "(__B__)"  # replaced per bbox tile (poly: filter gave 504 on all mirrors)
NX = NY = 3

PARTS = {
    "highway": [f'nwr["highway"]{P}', f'nwr["footway"~"sidewalk|crossing"]{P}'],
    "cycle": [f'way["cycleway"]{P}', f'way["cycleway:left"]{P}', f'way["cycleway:right"]{P}',
              f'way["cycleway:both"]{P}', f'nwr["barrier"]{P}', f'nwr["advertising"]{P}'],
    "transit": [f'nwr["railway"]{P}', f'nwr["public_transport"]{P}',
                f'rel["route"~"^(tram|bus|trolleybus)$"]{P}'],
    "buildings": [f'nwr["building"]{P}', f'nwr["building:part"]{P}'],
    "landscape": [
        f'nwr["landuse"]{P}', f'nwr["leisure"]{P}',
        f'nwr["natural"~"^(tree|tree_row|water|wood|scrub|grassland|wetland)$"]{P}',
        f'nwr["waterway"]{P}', f'nwr["man_made"]{P}',
    ],
    "pois": [
        f'nwr["amenity"]{P}', f'nwr["shop"]{P}', f'nwr["craft"]{P}',
        f'nwr["office"]{P}', f'nwr["tourism"]{P}',
    ],
}


def fetch_tile(name, stmts, bb, key, depth=0):
    """Fetch one bbox (s,w,n,e); on failure split into 4 (quadtree, max depth 4). Markers: .split files."""
    f = OUT / f"part_{name}_{key}.json"
    mark = OUT / f"part_{name}_{key}.split"
    if f.exists():
        return
    if not mark.exists():
        b = ",".join(f"{v:.5f}" for v in bb)
        q = ("[out:json][timeout:300];(" + ";".join(x.replace("__B__", b) for x in stmts)
             + ";);out body;>;out skel qt;")
        try:
            f.write_text(overpass.run(q, timeout=400))
            print("wrote", f.name, f.stat().st_size, flush=True)
            return
        except RuntimeError:
            if depth >= 4:
                print("GIVEUP", f.name, flush=True)
                return
            mark.write_text("")
            print("split", f.name, flush=True)
            time.sleep(10)
    s, w, n, e = bb
    ms, mw = (s + n) / 2, (w + e) / 2
    for i, sub in enumerate([(s, w, ms, mw), (s, mw, ms, e), (ms, w, n, mw), (ms, mw, n, e)]):
        fetch_tile(name, stmts, sub, f"{key}{i}", depth + 1)


def fetch(name, stmts):
    w, s, e, n = area.bbox_wgs84()
    fetch_tile(name, stmts, (s, w, n, e), "r")


def merge():
    seen, els, meta = set(), [], None
    for pf in sorted(OUT.glob("part_*.json")):
        d = json.loads(pf.read_text())
        meta = meta or {k: v for k, v in d.items() if k != "elements"}
        for e in d["elements"]:
            k = (e["type"], e["id"])
            if k not in seen:
                seen.add(k)
                els.append(e)
    (OUT / "kreise.json").write_text(json.dumps({**meta, "elements": els}, separators=(",", ":")))
    print("merged", len(els), "elements")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for n, s in PARTS.items():
        fetch(n, s)
    if not (OUT / "kreise.json").exists():
        merge()
