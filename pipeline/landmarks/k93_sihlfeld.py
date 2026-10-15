"""Friedhof Sihlfeld: Altes Krematorium / Aufbahrungshalle (Kuppelbau mit Saeulenhalle), Kapellen D + Aufbahrung,
Haupttor D mit Pfeilern, Mauer und Figurengruppe «Kauernder Mann, kauernde Frau» -> k93_krematorium.glb
Grabfelder: nicht modelliert (siehe research/landmarks_k93.md)."""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, Point
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, sources, terrain
from k93_lib import hexc, shade
OUT = F.ROOT + "/web/public/models/landmarks/k93_krematorium.glb"
WHITE = (255, 255, 255, 255)
O = (-704.0, -757.0)
H = terrain.heights((-800, -820, -620, -700), 2.0, z_shift=-3.06)
ZO = float(H.at(*O))
GATE = np.array([-706.8, -745.3])

def tex():
    im = Image.new("RGB", (64, 96), (222, 214, 192)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 63, 9], fill=(206, 198, 176)); d.rectangle([0, 86, 63, 95], fill=(190, 182, 160))
    d.rectangle([22, 28, 42, 74], fill=(52, 60, 72)); d.ellipse([22, 18, 42, 38], fill=(52, 60, 72)); d.line([32, 18, 32, 74], fill=(200, 196, 180), width=2)
    d.rectangle([18, 74, 46, 77], fill=(176, 168, 146))
    return im

nodes, els = sources.osm(); W = {e["id"]: e for e in els if e["type"] == "way"}
def osm_fp(i): return Polygon([nodes[n] for n in W[i]["nodes"]]).buffer(0).simplify(0.3)

M = L.Model(origin=(O[0], O[1], 0.0))
mw = M.mat("walls", rough=0.95, tex=tex(), repeat=True); ms = M.mat("stone", rough=0.9); mc = M.mat("copper", rough=0.55, metal=0.2)
SAND = hexc("#d8cfb4"); SLATE = hexc("#5b6066"); COP = hexc("#6fa58f")
def z_at(x, y): return float(H.at(x, y)) - ZO

# ---- Altes Krematorium / Aufbahrungshalle -------------------------------------------------------------------------
o = [o for o in F.near(-703, -761, 15) if o["id"][3:11] == "52331290"][0]
fp = F.footprint(o).simplify(0.3); pts = list(fp.exterior.coords)[:-1]
c = np.array(fp.centroid.coords[0]); zc = z_at(*c)
r = list(fp.minimum_rotated_rectangle.exterior.coords)[:4]
e1 = np.subtract(r[1], r[0]); e2 = np.subtract(r[2], r[1]); ang = math.atan2(e1[1], e1[0])
EAVE = 6.6
M.box(ms, (c[0], c[1], zc + 0.25), (np.hypot(*e1) + 2.0, np.hypot(*e2) + 2.0, 0.5), hexc("#9a968b"), rot=ang)   # plinth
M.prism(mw, pts, zc - 1.0, zc + EAVE, WHITE, tile=(3.4, EAVE + 1.0), top=False)
M.gable(ms, tuple(c), np.hypot(*e1), np.hypot(*e2), zc + EAVE, 2.4, SLATE, rot=ang, eave=0.7, hip=1.0)
# drum + dome
M.cyl(mw, tuple(c), 4.4, zc + EAVE + 1.0, zc + EAVE + 5.6, SAND, n=8, tile=(3.4, 4.6))
for k in range(8):
    a = 2 * math.pi * (k + 0.5) / 8
    M.box(ms, (c[0] + 4.42 * math.cos(a) * math.cos(math.pi / 8) / math.cos(math.pi / 8) * 0.98, c[1] + 4.42 * math.sin(a) * 0.98, zc + EAVE + 3.6), (0.2, 1.4, 2.4), hexc("#2a3038"), rot=a)
M.cyl(ms, tuple(c), 4.9, zc + EAVE + 5.6, zc + EAVE + 6.0, hexc("#b4ab92"), n=8)
M.dome(mc, tuple(c), 4.6, zc + EAVE + 6.0, COP, n=16, rings=5, sq=0.85)
M.cyl(mc, tuple(c), 0.9, zc + EAVE + 9.8, zc + EAVE + 11.0, hexc("#e6dfc8"), n=8)
M.cone(mc, tuple(c), 1.0, zc + EAVE + 11.0, zc + EAVE + 12.6, COP, n=8)
M.box(ms, (c[0], c[1], zc + EAVE + 13.0), (0.12, 0.12, 1.0), hexc("#c8a64a"))
# portico (colonnade + pediment) on the side facing the main gate
best = None
for i in range(len(pts)):
    a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)]); t = b - a
    if np.hypot(*t) < 6: continue
    nn = np.array([t[1], -t[0]]) / np.hypot(*t)
    if np.dot(nn, (a + b) / 2 - c) < 0: nn = -nn
    sc = np.dot(nn, GATE - (a + b) / 2) / np.hypot(*(GATE - (a + b) / 2))
    if best is None or sc > best[0]: best = (sc, (a + b) / 2, nn, math.atan2(t[1], t[0]))
_, mid, nn, fa = best; tx = np.array([math.cos(fa), math.sin(fa)])
M.box(ms, (*(mid + nn * 2.2), zc + 0.2), (8.4, 4.8, 0.4), hexc("#a29e92"), rot=fa)                     # porch floor
for st in range(3): M.box(ms, (*(mid + nn * (4.8 + 0.4 * st)), zc + 0.1 + 0.1 * (2 - st) * 0), (7.6 - st * 0.0, 0.5, 0.2 + 0.0), hexc("#b5b0a2"), rot=fa)
for k in range(-2, 3):
    p_ = mid + tx * k * 1.8 + nn * 3.9
    M.cyl(ms, tuple(p_), 0.38, zc + 0.4, zc + 5.4, hexc("#e4dcc3"), n=10); M.cyl(ms, tuple(p_), 0.5, zc + 0.4, zc + 0.8, hexc("#c9c1a8"), n=10); M.cyl(ms, tuple(p_), 0.5, zc + 5.2, zc + 5.5, hexc("#c9c1a8"), n=10)
M.box(ms, (*(mid + nn * 2.9), zc + 5.8), (8.4, 4.2, 0.7), hexc("#d2c9ae"), rot=fa)                       # entablature
M.gable(ms, tuple(mid + nn * 2.9), 8.8, 4.4, zc + 6.15, 1.7, hexc("#d6cdb2"), rot=fa, gablecol=hexc("#e0d8c0"))
M.box(ms, (*(mid + nn * 0.1), zc + 2.4), (3.0, 0.2, 4.0), hexc("#2f2a26"), rot=fa)                       # door

# ---- Kapellen -------------------------------------------------------------------------------------------------------
for oid, eave, rise in ((37007820, 5.2, 2.6), (212107152, 5.6, 3.0)):
    f2 = osm_fp(oid); p2 = list(f2.exterior.coords)[:-1]; c2 = np.array(f2.centroid.coords[0]); z2 = z_at(*c2)
    r = list(f2.minimum_rotated_rectangle.exterior.coords)[:4]; a1 = np.subtract(r[1], r[0]); a2 = np.subtract(r[2], r[1])
    if np.hypot(*a1) < np.hypot(*a2): a1, a2 = a2, a1
    an = math.atan2(a1[1], a1[0])
    M.prism(mw, p2, z2 - 1.0, z2 + eave, WHITE, tile=(3.4, eave + 1.0), top=False)
    M.gable(ms, tuple(c2), np.hypot(*a1), np.hypot(*a2), z2 + eave, rise, SLATE, rot=an, eave=0.6, hip=0.0, gablecol=hexc("#d6cdb2"))

# ---- Haupttor D ---------------------------------------------------------------------------------------------------
cem = Polygon([nodes[n] for n in W[10634343]["nodes"]])
q = cem.exterior.interpolate(cem.exterior.project(Point(*GATE))); q2 = cem.exterior.interpolate(cem.exterior.project(Point(*GATE)) + 2.0)
tg = np.array([q2.x - q.x, q2.y - q.y]); tg /= np.hypot(*tg); gang = math.atan2(tg[1], tg[0]); gc = np.array([q.x, q.y]); gz_ = z_at(*gc)
STONE = hexc("#a8a396")
for sg in (-1, 1):
    p_ = gc + tg * sg * 3.4
    M.box(ms, (p_[0], p_[1], gz_ + 2.1), (1.2, 1.2, 4.2), STONE, rot=gang); M.box(ms, (p_[0], p_[1], gz_ + 4.35), (1.5, 1.5, 0.3), hexc("#bdb8a8"), rot=gang)
    M.cone(ms, tuple(p_), 0.6, gz_ + 4.5, gz_ + 5.3, hexc("#8f8b7f"), n=4)
    for k in range(1, 5):                                                                 # boundary wall with coping
        p2_ = gc + tg * sg * (3.4 + 0.6 + k * 3.0)
        M.box(ms, (p2_[0], p2_[1], gz_ + 1.0), (3.0, 0.5, 2.0), hexc("#b3ad9d"), rot=gang); M.box(ms, (p2_[0], p2_[1], gz_ + 2.1), (3.1, 0.7, 0.2), hexc("#8d897d"), rot=gang)
    for k in range(5):                                                                    # open iron gate leaves
        pp = gc + tg * sg * (0.5 + k * 0.5)
        M.box(ms, (pp[0], pp[1], gz_ + 1.6), (0.06, 0.06, 3.0), hexc("#1d2024"), rot=gang)
    pp = gc + tg * sg * 1.5; M.box(ms, (pp[0], pp[1], gz_ + 3.0), (3.0, 0.08, 0.08), hexc("#1d2024"), rot=gang)
M.box(ms, (gc[0], gc[1], gz_ + 4.4), (6.6, 0.6, 0.5), hexc("#2a2d31"), rot=gang) if False else None
# sculpture group «Kauernder Mann, kauernde Frau» (Markwalder) inside the gate
sp = np.array([-706.2, -745.7]); sz = z_at(*sp)
M.box(ms, (sp[0], sp[1], sz + 0.4), (2.6, 1.2, 0.8), hexc("#8a867b"), rot=gang)
for dx in (-0.6, 0.6):
    M.box(ms, (sp[0] + dx * tg[0], sp[1] + dx * tg[1], sz + 1.2), (0.7, 0.6, 0.8), hexc("#6d6a63"), rot=gang)
    M.dome(ms, (sp[0] + dx * tg[0], sp[1] + dx * tg[1]), 0.28, sz + 1.6, hexc("#6d6a63"), n=8, rings=2)
os.makedirs(os.path.dirname(OUT), exist_ok=True); M.write(OUT); print("krematorium tris", M.tris(), "gate", gc.round(1).tolist(), "z", round(ZO, 2))
