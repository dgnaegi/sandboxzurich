"""Zone 4 ground audit: AV land cover (official) vs the game's OSM-derived road polygon, per 200 m tile.
Prints per tile: AV carriageway missing in game roads (would be drawn as walk/lawn), game road on AV green/building,
and the worst blobs (centre x,y, area). Usage: .venv/bin/python pipeline/audit_ground_z4.py [min_area]"""
import json, sys, os
import shapely
from shapely.geometry import box, shape
sys.path.insert(0, os.path.dirname(__file__))
import sources, streets, groundcover
from config import AREA

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
Z = next(z for z in json.load(open(f"{ROOT}/pipeline/overrides/zones.json"))["zones"] if z["id"] == 4)
poly = shapely.geometry.Polygon(Z["polys"][0])
nodes, els = sources.osm()
S = streets.parse(nodes, els)
G = groundcover.load((AREA[0] - 260, AREA[1] - 260, AREA[2] + 260, AREA[3] + 260))
roads = shapely.set_precision(S["roads"].buffer(0), 0.01)
carr = G["carriageway"].buffer(0)
miss = carr.difference(roads.buffer(1.5)).intersection(poly)
badr = roads.intersection(G["green"].buffer(0).union(G["building"].buffer(0))).difference(carr.buffer(2)).intersection(poly)
def blobs(g, tag):
    out = []
    for p in getattr(g, "geoms", [g]):
        if not p.is_empty and p.area >= MIN:
            c = p.centroid
            out.append((p.area, round(c.x), round(c.y), tag))
    return sorted(out, reverse=True)
b1, b2 = blobs(miss, "AV-road-missing"), blobs(badr, "game-road-on-green/bld")
print("zone4 AV carriageway %.0f m2, missing in game %.0f m2 (%d blobs >=%.0f), game road on AV green/building %.0f m2 (%d)" %
      (carr.intersection(poly).area, miss.area, len(b1), MIN, badr.area, len(b2)))
for a, x, y, t in (b1[:15] + b2[:15]):
    print("  %-22s %6.0f m2 at (%d,%d)" % (t, a, x, y))
json.dump({"missing": b1, "on_green": b2}, open(f"{ROOT}/logs/audit_ground_z4.json", "w"))

# --- part 2: AV paved classes (carriageway/sidewalk/plaza) that fall through to the 'yard' branch of _ground_base and become LAWN
# (not within 6 m of a road/3 m of a plaza, not in av_green/av_paved(gravel)); only counted inside the play area.
play = shapely.Polygon(__import__("config").POLYGON)
paved = shapely.union_all([carr, G["sidewalk"].buffer(0), G["plaza"].buffer(0)])
near = roads.buffer(6.0).union(S["plaza"].buffer(3.0))
fall = paved.difference(near).difference(G["green"].buffer(0)).difference(G["gravel"].buffer(0)).difference(G["building"].buffer(0)).difference(roads)
fall = fall.intersection(poly).intersection(play)
b3 = blobs(fall, "paved-would-be-lawn")
print("AV paved falling to lawn in zone4 play area: %.0f m2 (%d blobs >=%.0f)" % (fall.area, len(b3), MIN))
for a, x, y, t in b3[:20]:
    print("  %6.0f m2 at (%d,%d)" % (a, x, y))
