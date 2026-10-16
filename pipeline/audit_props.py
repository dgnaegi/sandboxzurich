"""Data audit: prop rows in web/public/tiles/*.json whose z is far from the terrain / bridge deck below (floating or sunk).
Usage: .venv/bin/python pipeline/audit_props.py [out.json]  -> summary (<=30 lines), full list in out.json."""
import base64, glob, json, sys
from collections import Counter, defaultdict
import numpy as np

KINDS = ["trees", "lamps", "masts", "bins", "bikes", "racks", "benches", "hydrants", "cars", "mopeds", "scooters", "decals", "bollards", "signals", "trafficsigns", "fountains", "pingpong"]
TOL = 0.6


def load_h(d):
    z = np.frombuffer(base64.b64decode(d["zb64"]), dtype="<i2").astype(float) / 100 if "zb64" in d else np.array(d["z"], float)
    return d, z.reshape(d["h"], d["w"])


def at(h, x, y):
    d, z = h
    fx = min(max((x - d["x0"]) / d["step"], 0), d["w"] - 1.001); fy = min(max((y - d["y0"]) / d["step"], 0), d["h"] - 1.001)
    ix, iy = int(fx), int(fy); tx, ty = fx - ix, fy - iy
    return (z[iy, ix] * (1 - tx) + z[iy, ix + 1] * tx) * (1 - ty) + (z[iy + 1, ix] * (1 - tx) + z[iy + 1, ix + 1] * tx) * ty


GRID = {}


def build_grid(decks):
    for dk in decks:
        if dk.get("kind") == "rail":
            continue
        r = dk["w"] / 2 + 2
        for a, b in zip(dk["p"], dk["p"][1:]):
            for cx in range(int((min(a[0], b[0]) - r) // 10), int((max(a[0], b[0]) + r) // 10) + 1):
                for cy in range(int((min(a[1], b[1]) - r) // 10), int((max(a[1], b[1]) + r) // 10) + 1):
                    GRID.setdefault((cx, cy), []).append(dk)


def deck_z(decks, x, y):
    best = None
    for dk in GRID.get((int(x // 10), int(y // 10)), []):
        p = dk["p"]
        for a, b in zip(p, p[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy or 1
            t = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / L))
            if (a[0] + dx * t - x) ** 2 + (a[1] + dy * t - y) ** 2 <= (dk["w"] / 2 + 1.5) ** 2:
                zz = a[2] + (b[2] - a[2]) * t
                best = zz if best is None else max(best, zz)  # highest deck
    return best


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "research/audit_props.json"
    files = sorted(glob.glob("web/public/tiles/t_*.json"))
    dk_all = []
    for extra in ("web/public/data/station_decks.json", "web/public/data/hb_decks.json"):
        try:
            dk_all += json.load(open(extra)).get("decks", [])
        except Exception:
            pass
    metas = {}
    for f in files:
        m = json.load(open(f)); metas[f] = m
        dk_all += (m.get("bridges") or {}).get("decks", [])
    build_grid(dk_all)
    issues = []
    cnt = Counter(); tot = Counter()
    for f, m in metas.items():
        h = load_h(m["hmap"]) if m.get("hmap") else None
        if h is None:
            continue
        for k in KINDS:
            for r in m.get(k, []):
                if len(r) < 3 or not isinstance(r[2], (int, float)):
                    continue
                x, y, z = r[0], r[1], r[2]
                tot[k] += 1
                g = at(h, x, y)
                dz = deck_z(dk_all, x, y)
                ref = [g] + ([dz] if dz is not None else [])
                # nearest reference surface (ground without the kerb drop, or a deck)
                d = min((z - q for q in ref), key=abs)
                if d > TOL or d < -TOL - 0.3:
                    cnt[(k, "floating" if d > 0 else "sunk")] += 1
                    issues.append({"kind": k, "type": "floating" if d > 0 else "sunk", "x": round(x, 1), "y": round(y, 1), "z": round(z, 2), "dz": round(d, 2), "deck": dz is not None, "tile": f.split("/")[-1][:-5]})
    json.dump(issues, open(out, "w"))
    print("rows checked:", dict(tot))
    for (k, t), n in cnt.most_common(30):
        print(f"{k:14s} {t:9s} {n}/{tot[k]}")


if __name__ == "__main__":
    main()
