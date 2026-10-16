"""Photo-derived extra objects: overrides/fidelity.json (pixel annotations on photos) -> overrides/places_detail_fidelity.json.
Run: .venv/bin/python pipeline/fidelity.py   (then rebuild the affected tiles; places_detail.py picks the file up by glob)."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "pipeline" / "overrides" / "fidelity.json"
OUT = ROOT / "pipeline" / "overrides" / "places_detail_fidelity.json"
CAND = ROOT / "research" / "fidelity_cand.json"
W, H, VFOV, CAMH = 800, 600, math.radians(80), 1.6
F = (H / 2) / math.tan(VFOV / 2)


def ground(cam, u, v):
    """Pixel on the ground -> local metres."""
    if v <= H / 2 + 4:
        return None
    z = CAMH * F / (v - H / 2)
    lat = (u - W / 2) * z / F
    hd = math.radians(cam["heading"])
    return cam["x"] + math.sin(hd) * z + math.cos(hd) * lat, cam["y"] + math.cos(hd) * z - math.sin(hd) * lat


def build():
    cams = {c["id"]: c for c in json.load(open(CAND))}
    objs = []
    for it in json.load(open(SRC))["items"]:
        cam = cams[it["photo"]]
        extra = {k: it[k] for k in ("a", "b", "c", "d", "col") if k in it}
        if "seg" in it:
            (x0, y0), (x1, y1) = [ground(cam, *p) for p in it["seg"]]
            L = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / L, (y1 - y0) / L
            ox, oy = (uy * it.get("off", 0), -ux * it.get("off", 0))  # right of travel direction
            objs.append({"t": it["t"], "p": [round((x0 + x1) / 2 + ox, 1), round((y0 + y1) / 2 + oy, 1)],
                         "h": round(math.degrees(math.atan2(uy, ux)), 1), "a": round(L, 1), **extra})
            continue
        for u, v in it["px"]:
            g = ground(cam, u, v)
            if g:
                objs.append({"t": it["t"], "p": [round(g[0], 1), round(g[1], 1)], "h": round(90 - cam["heading"], 1), **extra})
    json.dump({"places": [{"id": "fidelity", "center": [0, 0], "src": "research/fidelity.md (Fotopaare)", "objs": objs}]}, open(OUT, "w"), indent=1)
    tiles = sorted({(int(o["p"][0] // 200), int(o["p"][1] // 200)) for o in objs})
    print(len(objs), "objects; tiles", ",".join(f"{a}_{b}" for a, b in tiles))


if __name__ == "__main__":
    build()
