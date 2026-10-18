"""No tree/lamp/bench/... props inside the HB halls and on the platforms (they stood on the platforms): writes research/hb/prop_excl.json (world polygons),
read by pipeline/cityprops.py. Zones in the model frame: platform hall d -480..-40 x c -77..68, Haupthalle + Querhalle d -48..118 x c -68..60."""
import json, sys
sys.path.insert(0, '.')
from hb_kit import to_world, ROOT
Z = [(-480, -40, -77, 68), (-48, 118, -68, 60)]
polys = [[[round(v, 1) for v in to_world(d, c)] for d, c in ((a, b), (a2, b), (a2, b2), (a, b2))] for a, a2, b, b2 in Z]
json.dump({"polys": polys}, open(ROOT / "research/hb/prop_excl.json", "w"))
print(polys)
