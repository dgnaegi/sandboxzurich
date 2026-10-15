import json, struct, os
D = "/Users/danielgnagi/sandboxzurich/web/public/models/cars"
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from specs import SPECS
out = []
for t, s in SPECS.items():
    p = f"{D}/{t}.glb"
    if not os.path.exists(p): continue
    b = open(p, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n])
    pos = j["accessors"][j["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
    mn, mx = pos["min"], pos["max"]
    out.append(dict(type=t, file=f"{t}.glb", drive=os.path.exists(f"{D}/{t}_drive.glb"), length=round(mx[2] - mn[2], 2), width=round(s["W"], 2), height=round(mx[1] - mn[1], 2)))
json.dump(out, open(f"{D}/manifest.json", "w"), indent=1)
for o in out: print(o)
