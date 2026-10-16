"""Extract OSM station data (platforms, tracks, steps, lifts, shelters, benches, bike parking) near the 3 stations.
-> research/stations/osm_<id>.json (local metres). Run: .venv/bin/python pipeline/landmarks/st_osm.py [summary]"""
import sys, os, json
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import sources
from shapely.geometry import LineString, Polygon

ST = {"hardbruecke": (-1000, 1000, 330), "altstetten": (-2082, 738, 330), "wiedikon": (210, -150, 260)}

def run():
    nodes, els = sources.osm()
    # station centres from lat/lon
    sys.path.insert(0, str(ROOT / "pipeline" / "landmarks"))
    from common import ll
    centres = {"hardbruecke": ll(47.385106, 8.517025), "altstetten": ll(47.390993, 8.489195), "wiedikon": ll(47.371413, 8.523581)}
    out = {k: {"platforms": [], "tracks": [], "steps": [], "lifts": [], "other": [], "roofs": []} for k in centres}
    for e in els:
        t = e.get("tags", {})
        if not t: continue
        if e["type"] == "way":
            pts = [nodes[n] for n in e["nodes"] if n in nodes]
        elif e["type"] == "node" and e["id"] in nodes:
            pts = [nodes[e["id"]]]
        else: continue
        if not pts: continue
        c = np.mean(pts, 0)
        for k, cc in centres.items():
            if np.hypot(c[0] - cc[0], c[1] - cc[1]) > 380: continue
            rec = {"id": e["id"], "type": e["type"], "tags": t, "pts": [[round(float(x), 2), round(float(y), 2)] for x, y in pts]}
            r = out[k]
            if t.get("railway") == "platform" or t.get("public_transport") == "platform" and t.get("train") == "yes": r["platforms"].append(rec)
            elif t.get("railway") in ("rail", "light_rail", "tram") : r["tracks"].append(rec)
            elif t.get("highway") == "steps": r["steps"].append(rec)
            elif t.get("highway") == "elevator" or t.get("building:part") == "elevator" or t.get("elevator") : r["lifts"].append(rec)
            elif t.get("building") in ("roof", "train_station") or t.get("railway") in ("station", "halt", "stop"): r["roofs"].append(rec)
            elif t.get("amenity") in ("bench", "shelter", "vending_machine", "bicycle_parking", "waste_basket", "ticket", "clock") or t.get("shelter") or t.get("bench") or t.get("tunnel") == "yes" and t.get("highway"): r["other"].append(rec)
    for k, r in out.items():
        json.dump({"centre": centres[k], **r}, open(ROOT / "research" / "stations" / f"osm_{k}.json", "w"))
        print(k, {a: len(b) for a, b in r.items()})
        if len(sys.argv) > 1:
            for p in r["platforms"]:
                t = p["tags"]; ls = LineString(p["pts"]) if len(p["pts"]) > 1 else None
                print("  PL", p["id"], t.get("ref"), t.get("name"), t.get("height"), "len %.0f" % (ls.length if ls else 0), np.mean(p["pts"], 0).round(0))
            for p in r["steps"][:20]: print("  ST", p["id"], p["tags"].get("highway"), p["tags"].get("incline"), p["tags"].get("level"), np.mean(p["pts"], 0).round(0))
            for p in r["lifts"][:10]: print("  LI", p["id"], np.mean(p["pts"], 0).round(0))
            for p in r["other"][:15]: print("  OT", p["id"], {a: b for a, b in p["tags"].items() if a in ("amenity", "tunnel", "highway", "name")}, np.mean(p["pts"], 0).round(0))
run()
