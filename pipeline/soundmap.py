"""Compact sound map for the ambience layers -> web/public/audio/soundmap.json (lazy-loaded after start).

Source: web/public/data/map/vec.json (OSM, (c) OpenStreetMap contributors, ODbL; built by mapdata.py).
Output (local metres, ints): roads [x,y,w], green [x,y,r], squares [x,y,r], churches [x,y].
Usage: .venv/bin/python pipeline/soundmap.py
"""
import json
import math

from config import ROOT

SRC = ROOT / "web" / "public" / "data" / "map" / "vec.json"
OUT = ROOT / "web" / "public" / "audio" / "soundmap.json"
ROAD_W = {"0": 10, "1": 10, "2": 8, "3": 5}  # loudness weight 0..10 by OSM class
STEP = 30.0


def dec(flat, ox, oy, q):
    x = y = 0
    out = []
    for i in range(0, len(flat), 2):
        x += flat[i]
        y += flat[i + 1]
        out.append((x / q + ox, y / q + oy))
    return out


def ring_stats(pts):
    a = cx = cy = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    a *= 0.5
    if abs(a) < 1:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return sum(xs) / len(xs), sum(ys) / len(ys), 0.0
    return cx / (6 * a), cy / (6 * a), abs(a)


def main():
    d = json.load(open(SRC))
    ox, oy, q = d["ox"], d["oy"], d["q"]
    roads, seen = [], {}
    for cls, w in ROAD_W.items():
        for _, flat in d["roads"].get(cls, []):
            pts = dec(flat, ox, oy, q)
            carry = 0.0
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                L = math.hypot(x1 - x0, y1 - y0)
                t = STEP - carry
                while t <= L:
                    px, py = x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L
                    k = (round(px / 15), round(py / 15))
                    if seen.get(k, -1) < w:
                        seen[k] = w
                        roads.append([round(px), round(py), w])
                    t += STEP
                carry = (carry + L) % STEP if L < STEP - carry else L - (t - STEP)
    # keep only the max weight per 15 m cell
    roads = [r for r in roads if seen[(round(r[0] / 15), round(r[1] / 15))] == r[2]]
    green, squares = [], []
    for kind, lim, dst in (("g", 3000, green), ("w", 3000, green), ("c", 2000, green), ("sq", 250, squares)):
        for a in d["areas"].get(kind, []):
            ring = a if isinstance(a[0], int) else a[0]
            cx, cy, area = ring_stats(dec(ring, ox, oy, q))
            if area >= lim:
                dst.append([round(cx), round(cy), round(math.sqrt(area / math.pi))])
    ch = [[p[1], p[2]] for p in d["pois"] if p[3] == "church" or (p[3] == "lm" and "irche" in p[0])]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"roads": roads, "green": green, "squares": squares, "churches": ch}, open(OUT, "w"), separators=(",", ":"))
    print("roads", len(roads), "green", len(green), "squares", len(squares), "churches", len(ch), OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
