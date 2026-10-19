"""Which swissBUILDINGS3D buildings (ids) and OSM buildings (points) Zuerich HB replaces. Zones in the model frame."""
import sys, glob, pickle, json, math
sys.path.insert(0, '.')
from hb_kit import *
import hb_geom as G
ZONES = {"haupt": (-50, 118, -72, 62), "perron": (-480, -45, -110, 75)}


def zone_of(d, c):
    for k, (d0, d1, c0, c1) in ZONES.items():
        if d0 <= d <= d1 and c0 <= c <= c1: return k


def swiss():
    out = {"haupt": [], "perron": []}
    for f in sorted(glob.glob(str(ROOT / 'data/build/bld/*.pkl'))):
        for b in pickle.load(open(f, 'rb')):
            allp = np.concatenate([p for _, p in b['polys']]); ctr = allp[:, :2].mean(0)
            d, c = from_world(*ctr); z = zone_of(d, c)
            if z:
                ext = allp[:, :2].max(0) - allp[:, :2].min(0)
                out[z].append((b['id'], round(d), round(c), [round(v) for v in ext], round(float(allp[:, 2].max()), 1)))
    return out


def canopies(taken):
    """Roof-only swissBUILDINGS3D canopies (no wall footprint) around the station that nothing else hides: without walls/posts they float
    6-7 m over the Bahnhofplatz / Bahnhofquai (the 'grey boxes over the east gable'); stops.ts builds the real shelters."""
    out = []
    for f in sorted(glob.glob(str(ROOT / 'data/build/bld/*.pkl'))):
        for b in pickle.load(open(f, 'rb')):
            if b['id'] in taken or any(k == 0 for k, _ in b['polys']): continue
            allp = np.concatenate([p for _, p in b['polys']]); d, c = from_world(*allp[:, :2].mean(0))
            if -500 < d < 260 and -200 < c < 170: out.append(b['id'])
    return out


def osm_points():
    import sources
    nodes, els = sources.osm(); pts = {"haupt": [], "perron": []}
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way" and "building" in t and len(e.get("nodes", [])) > 3:
            P_ = [nodes[n] for n in e["nodes"] if n in nodes]
            if len(P_) < 4: continue
            g = Polygon(P_).buffer(0)
            if g.is_empty or g.area < 20: continue
            rp = g.representative_point(); d, c = from_world(rp.x, rp.y); z = zone_of(d, c)
            if z: pts[z].append([round(rp.x, 1), round(rp.y, 1)])
    return pts


if __name__ == "__main__":
    S = swiss()
    for k, v in S.items():
        print(k, len(v))
        for r in sorted(v, key=lambda r: r[1]): print("  ", r)
    O = osm_points(); print({k: len(v) for k, v in O.items()})
    S["perron"] = [r for r in S["perron"] if r[4] <= 12.5 and r[2] >= -85]   # no towers / buildings south of the tracks
    out = {k: [r[0] for r in v] for k, v in S.items()}
    out["canopy"] = canopies(set(out["haupt"]) | set(out["perron"]) | {i for f in glob.glob(str(ROOT / "pipeline/overrides/landmarks_*.json")) for e in json.load(open(f))["landmarks"] for i in e.get("hide_ids", [])})
    print("canopy", len(out["canopy"]))
    json.dump({"swiss": out, "osm_points": O}, open(ROOT / "research/hb/hide.json", "w"))
