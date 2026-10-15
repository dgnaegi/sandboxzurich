"""Kirchen (Alte Kirche + Kirche Altstetten, Dreifaltigkeitskirche Wiedikon) aus echten Grundrissen/Hoehen.
-> k93_kirche_altstetten.glb, k93_dreifaltigkeit.glb"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, terrain
from k93_lib import hexc, shade
OUTD = F.ROOT + "/web/public/models/landmarks/"
WHITE = (255, 255, 255, 255)

def church_tex():
    im = Image.new("RGB", (64, 96), (226, 220, 204)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 63, 11], fill=(214, 208, 190))
    d.rectangle([22, 30, 42, 80], fill=(60, 70, 84)); d.ellipse([22, 20, 42, 40], fill=(60, 70, 84))
    d.rectangle([19, 27, 45, 29], fill=(196, 190, 172)); d.rectangle([19, 80, 45, 83], fill=(196, 190, 172))
    return im

def info(oid, p):
    o = [o for o in F.near(*p, 30) if o["id"][3:11] == oid][0]
    fp = F.footprint(o).simplify(0.4)
    gz = float(np.vstack([q for k, q in o["polys"] if k == 0])[:, 2].mean())
    roof = np.vstack([q for k, q in o["polys"] if k == 2]); rz = roof[:, 2] - gz
    return fp, roof, rz

def church(M, mw, mr, mg, oid, p, eave, rise, ttop, spire, tw=6.2, tile_col=hexc("#9a4a36"), spire_col=hexc("#5d9a86"), hip=0.0):
    fp, roof, rz = info(oid, p)
    gz = float(np.vstack([q for k, q in [(0, None)]] ) if False else 0)
    z0 = float(H.at(*fp.centroid.coords[0]))
    r = list(fp.minimum_rotated_rectangle.exterior.coords)[:4]
    e1 = np.subtract(r[1], r[0]); e2 = np.subtract(r[2], r[1])
    if np.hypot(*e1) < np.hypot(*e2): e1, e2 = e2, e1
    ang = math.atan2(e1[1], e1[0]); Lg, Sh = np.hypot(*e1), np.hypot(*e2)
    ctr = np.array(fp.centroid.coords[0]); u = e1 / Lg
    top = roof[np.argmax(roof[:, 2])][:2]; sgn = 1 if np.dot(top - ctr, u) > 0 else -1
    base = z0 - 2.5
    pts = list(fp.exterior.coords)[:-1]
    M.prism(mw, pts, base, z0 + eave, WHITE, tile=(4.5, eave + 2.5 + (z0 - z0)), top=False)
    M.gable(mr, tuple(ctr), Lg, Sh, z0 + eave, rise, tile_col, rot=ang, eave=0.45, gablecol=hexc("#d8d2bf"))
    tc = ctr + u * sgn * (Lg / 2 - tw / 2 + 0.3)
    n = np.array([-u[1], u[0]])
    sq = [tc + (u * a + n * b) * tw / 2 for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    M.prism(mr, [tuple(q) for q in sq], base, z0 + ttop - spire, hexc("#d9d3bf") if tile_col[0] > 130 else hexc("#b5b4ae"), top=False)
    zb = z0 + ttop - spire
    # belfry openings and clock faces
    for sg in (-1, 1):
        for ax, ln in ((u, n), (n, u)):
            c = tc + ax * sg * (tw / 2 + 0.03)
            M.box(mg, (c[0], c[1], zb - 3.2), (0.1 if ax is u else 2.2, 2.2 if ax is u else 0.1, 3.0), hexc("#2b3036"), rot=ang)
            M.box(mg, (c[0] + ax[0] * 0.03, c[1] + ax[1] * 0.03, zb - 7.5), (0.1 if ax is u else 1.9, 1.9 if ax is u else 0.1, 1.9), hexc("#f1ede0"), rot=ang)
    M.cap(mg, [tuple(q) for q in sq], zb, shade(spire_col, 0.7))
    # spire: 4-sided pyramid rotated with the tower
    ap = (tc[0], tc[1], z0 + ttop)
    for i in range(4):
        a = sq[i]; b = sq[(i + 1) % 4]
        ea = tc + (a - tc) * 1.06; eb = tc + (b - tc) * 1.06
        M.tri(mr, (*ea, zb), (*eb, zb), ap, shade(spire_col, 0.85 + 0.08 * i))
    M.box(mg, (tc[0], tc[1], z0 + ttop + 0.9), (0.12, 0.12, 1.8), hexc("#c8a64a"))
    return z0

H = terrain.heights((-2500, 150, -2300, 350), 2.0, z_shift=-3.06)
def build(name, items, origin_xy, outname):
    global H
    H = terrain.heights((origin_xy[0] - 80, origin_xy[1] - 80, origin_xy[0] + 80, origin_xy[1] + 80), 2.0, z_shift=-3.06)
    M = L.Model(origin=(origin_xy[0], origin_xy[1], float(H.at(*origin_xy))))
    mw = M.mat("walls", rough=0.95, tex=church_tex(), repeat=True)
    mr = M.mat("roof", rough=0.85); mg = M.mat("trim", rough=0.9)
    for it in items: church(M, mw, mr, mg, **it)
    M.write(OUTD + outname); print(name, "tris", M.tris(), "origin", origin_xy)

if __name__ == "__main__":
    os.makedirs(OUTD, exist_ok=True)
    build("Kirchen Altstetten", [
        dict(oid="96D18134", p=(-2388, 254), eave=7.5, rise=6.5, ttop=32.7, spire=11.0, tw=5.4),
        dict(oid="82C92B3A", p=(-2425, 245), eave=14.0, rise=5.2, ttop=45.7, spire=5.0, tw=7.0, tile_col=hexc("#8a4636"), spire_col=hexc("#9a9a94")),
    ], (-2405.0, 250.0), "k93_kirche_altstetten.glb")
    build("Dreifaltigkeit", [dict(oid="756BF729", p=(457, -1185), eave=17.0, rise=6.0, ttop=32.5, spire=9.0, tw=5.8, tile_col=hexc("#7e4a3c"))], (457.0, -1185.0), "k93_dreifaltigkeit.glb")
