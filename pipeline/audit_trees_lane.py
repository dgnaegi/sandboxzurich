"""Audit: tree trunks standing on the carriageway (tile road mask, 1 m cells) in web/public/tiles/*.json.
usage: .venv/bin/python pipeline/audit_trees_lane.py [tiles_dir] -> counts + 5 worst examples."""
import base64, glob, json, sys
import numpy as np
D = sys.argv[1] if len(sys.argv) > 1 else "web/public/tiles"
tot = on = street_on = 0; ex = []
for f in glob.glob(D + "/t_*.json"):
    d = json.load(open(f)); m = d.get("mask"); tr = d.get("trees") or []
    if not m or not tr: continue
    n = m["n"]; bits = np.unpackbits(np.frombuffer(base64.b64decode(m["bits"]), np.uint8))
    rows = len(bits) // n if n else 0
    # packbits is over the flattened array; trailing pad is irrelevant
    for t in tr:
        tot += 1
        i, j = int((t[0] - m["x0"]) // m["res"]), int((t[1] - m["y0"]) // m["res"])
        if 0 <= i < n and 0 <= j * n + i < len(bits) and bits[j * n + i]:
            on += 1; street_on += t[7] > 0
            if len(ex) < 5: ex.append((f.split("/")[-1], round(t[0]), round(t[1])))
print(f"trees {tot}, on carriageway {on} ({100*on/max(tot,1):.2f} %), of those street trees {street_on}")
print("examples", ex)
