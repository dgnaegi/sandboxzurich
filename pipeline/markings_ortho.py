"""Measure yellow road markings (Velostreifen lines, Fussgaengerstreifen, Gelblinien) of the whole Langstrasse from SWISSIMAGE
(swisstopo OGD, WMS, 0.1 m/px, cached in data/raw/ortho_langstrasse/ls_NN.jpg) and write pipeline/overrides/markings_langstrasse.json
(local metres, yellow polygons + coverage region). Applied by markings_override.apply (hook in build_testarea).
usage: .venv/bin/python pipeline/markings_ortho.py [--fetch] [--debug]"""
import json, sys, time, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import shapely
from shapely.geometry import LineString, box, Polygon

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/raw/ortho_langstrasse"; D.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "pipeline/overrides/markings_langstrasse.json"
OX, OY = 2681400, 1248700
# Langstrasse axis, Limmatplatz -> Stauffacher (local metres, from OSM ways named Langstrasse)
AXIS = [(1125, 80), (1104, 36), (1081, -6), (1043, -74), (979, -189), (954, -231), (932, -278), (894, -364), (867, -422), (842, -483),
        (792, -615), (771, -671), (745, -737), (697, -844), (654, -935), (641, -962), (594, -1057), (584, -1083)]
# Langstrassen-Unterfuehrung: markings stay as built (lu_* landmark owns the tunnel); ortho shows the rail deck there
SKIP = LineString([(954, -231), (932, -278), (894, -364), (867, -422)]).buffer(22)
URL = ("https://wms.geo.admin.ch/?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=ch.swisstopo.swissimage&STYLES=&CRS=EPSG:2056"
       "&BBOX={a},{b},{c},{d}&WIDTH=1000&HEIGHT=1000&FORMAT=image/jpeg")
BOX, STEP = 100.0, 70.0


def boxes():
    L = LineString(AXIS); out = []; s = 0.0
    while s < L.length + STEP / 2:
        p = L.interpolate(min(s, L.length)); out.append((round(p.x), round(p.y))); s += STEP
    return out


def fetch(i, x, y):
    f = D / f"ls_{i:02d}.jpg"
    if f.exists() and f.stat().st_size > 20000:
        return f
    u = URL.format(a=OX + x - BOX / 2, b=OY + y - BOX / 2, c=OX + x + BOX / 2, d=OY + y + BOX / 2)
    for k in range(6):
        try:
            f.write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "sandboxzurich-research/1.0"}), timeout=120).read())
            time.sleep(1); return f
        except Exception as e:
            print("retry", i, e, flush=True); time.sleep(4 * (k + 1))
    return None


def yellow_mask(a):
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    yb = (R + G) / 2 - B; lum = (R + G + B) / 3
    rg = np.abs(R - G) < 0.25 * lum + 6
    bright = (yb > 20) & (R > 85) & (np.abs(R - G) < 22) & (G >= R - 22)
    ybs = ndi.gaussian_filter(yb, 0.8); loc = ndi.median_filter(ybs[::2, ::2], size=13)
    loc = np.kron(loc, np.ones((2, 2)))[: yb.shape[0], : yb.shape[1]]
    shade = (lum < 95) & (lum > 25) & (ybs > np.maximum(7, 0.11 * lum)) & (ybs - loc > 4.5) & rg
    return bright | shade


def comps(mask, x0, y1, px=0.1):
    """mask rows north->south. -> list of shapely polygons (local metres)."""
    mask = ndi.binary_closing(mask, iterations=1)
    lab, n = ndi.label(mask, structure=np.ones((3, 3)))
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        if sl is None: continue
        sub = lab[sl] == i
        if sub.sum() < 12: continue
        r0, c0 = sl[0].start, sl[1].start
        rr, cc = np.nonzero(sub)
        bx = [box(x0 + (c0 + c) * px, y1 - (r0 + r + 1) * px, x0 + (c0 + c + 1) * px, y1 - (r0 + r) * px) for r, c in zip(rr, cc)]
        g = shapely.union_all(bx).simplify(0.03)
        out.append(g)
    return out


def good(g):
    if g.is_empty or g.area < 0.12: return False
    r = g.minimum_rotated_rectangle
    c = list(r.exterior.coords); a, b = np.hypot(c[1][0] - c[0][0], c[1][1] - c[0][1]), np.hypot(c[2][0] - c[1][0], c[2][1] - c[1][1])
    short, long_ = min(a, b), max(a, b)
    return short <= 0.95 and long_ >= 0.9 and long_ <= 60


def slim(g, target=0.3):
    """thin over-wide line blobs (shadow/blur) to a realistic marking width; keep zebra stripes (~0.5 m)."""
    if g.geom_type != "Polygon" or g.length < 1: return g
    w = 2 * g.area / g.length
    if 0.45 < w < 0.9:
        e = g.buffer(-(w - target) / 2, join_style=2)
        return e if not e.is_empty else g
    return g


def main():
    bs = boxes(); print(len(bs), "boxes", flush=True)
    polys, cover = [], []
    for i, (x, y) in enumerate(bs):
        f = fetch(i, x, y)
        if f is None: print("missing", i); continue
        a = np.asarray(Image.open(f).convert("RGB")).astype(float)
        x0, y1 = x - BOX / 2, y + BOX / 2
        inner = box(x - BOX / 2 + 1.5, y - BOX / 2 + 1.5, x + BOX / 2 - 1.5, y + BOX / 2 - 1.5)  # seams: boxes overlap 30 m
        cover.append(inner)
        gs = [g for g in comps(yellow_mask(a), x0, y1) if good(g)]
        polys += [g.intersection(inner) for g in gs]
        print(i, (x, y), len(gs), flush=True)
    allp = shapely.union_all([p for p in polys if not p.is_empty])
    parts = [slim(g) for g in shapely.get_parts(allp) if good(g)]
    region = shapely.union_all(cover).difference(SKIP)
    parts = [g.intersection(region) for g in parts]
    parts = [g for g in parts if not g.is_empty and g.geom_type == "Polygon" and g.area > 0.1]
    def ring(g): return [[round(x, 2), round(y, 2)] for x, y in g.exterior.coords]
    d = {"doc": "Gemessen aus SWISSIMAGE (markings_ortho.py). yellow = Polygone (lokale Meter); region = Gebiet, in dem gemessene Gelbmarkierungen die gebauten ersetzen; add_white/add_yellow/cut = Handkorrekturen (Polygone).",
         "yellow": [ring(g) for g in parts], "region": [ring(p) for p in shapely.get_parts(region) if p.geom_type == "Polygon"],
         "add_white": [], "add_yellow": [], "cut": []}
    OUT.write_text(json.dumps(d))
    print("wrote", OUT, len(parts), "yellow polygons", f"{sum(g.area for g in parts):.0f} m2")


if __name__ == "__main__":
    main()
