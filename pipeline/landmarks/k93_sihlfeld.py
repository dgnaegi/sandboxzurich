"""Friedhof Sihlfeld: Altes Krematorium / Aufbahrungshalle (Kuppelbau mit Saeulenhalle), Kapellen D + Aufbahrung,
Haupttor D mit Pfeilern, Mauer und Figurengruppe «Kauernder Mann, kauernde Frau» -> k93_krematorium.glb
Grabfelder: nicht modelliert (siehe research/landmarks_k93.md)."""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, Point
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, sources, terrain, k93_kit as K
from k93_lib import hexc, shade
OUT = F.ROOT + "/web/public/models/landmarks/k93_krematorium.glb"
WHITE = (255, 255, 255, 255)
O = (-704.0, -757.0)
H = terrain.heights((-800, -820, -620, -700), 2.0, z_shift=-3.06)
ZO = float(H.at(*O))
GATE = np.array([-706.8, -745.3])

def wall_mats(M):
    """Window textures for the cemetery buildings (painted, lit at night)."""
    house = K.tile(4, 2, 72, 80, K.window(wall="#a9a08e", frame="#efe6cf", glass="#3a4651", fw=0.40, fh=0.50, top=0.22, cols=2, rows=3,
                                            surround="#d7cdb2", sill="#cfc6ad", noise=6), seed=21, lit=0.12)
    hall = K.tile(4, 1, 80, 112, K.window(wall="#d8cfa6", frame="#f1ede0", glass="#42505c", fw=0.56, fh=0.60, top=0.18, cols=3, rows=5, arch=True,
                                            surround="#e8e0c4", sill="#cfc6ad", noise=5), seed=22, lit=0.10)
    dome = K.tile(2, 1, 80, 96, K.window(wall="#cdbf9f", frame="#efe6cf", glass="#3a4651", fw=0.42, fh=0.55, top=0.2, cols=2, rows=4, arch=True, surround="#e4dac0"), seed=23, lit=0.1)
    return (M.mat("house", rough=0.95, tex=house[0], emis=house[1], repeat=True), M.mat("hall", rough=0.95, tex=hall[0], emis=hall[1], repeat=True),
            M.mat("domewall", rough=0.95, tex=dome[0], emis=dome[1], repeat=True))


def gate_leaf(M, mat, gold, p0, tg, w=1.75, h=2.3, hang=0.0):
    """Wrought-iron leaf: 0.42 m lattice of thin bars with gold roundels (open leaf, rotated by `hang` around the hinge)."""
    ang = math.atan2(tg[1], tg[0]) + hang; t = np.array([math.cos(ang), math.sin(ang)]); n_ = int(w / 0.42)
    for k in range(n_ + 1):
        q = p0 + t * (k * w / n_); M.box(mat, (q[0], q[1], h / 2), (0.05, 0.05, h), hexc("#1c1f23"), rot=ang)
    rows_ = int(h / 0.42)
    for r_ in range(rows_ + 1):
        q = p0 + t * w / 2; M.box(mat, (q[0], q[1], r_ * h / rows_), (w, 0.05, 0.05), hexc("#1c1f23"), rot=ang)
    for r_ in range(1, rows_, 2):
        for k in range(n_):
            if (r_ + k) % 3 == 0:
                q = p0 + t * ((k + 0.5) * w / n_); M.cyl(gold, (q[0], q[1]), 0.15, r_ * h / rows_ - 0.15, r_ * h / rows_ + 0.15, hexc("#c89a30"), n=8, cap=False) if False else M.box(gold, (q[0], q[1], r_ * h / rows_ + 0.0), (0.34, 0.07, 0.34), hexc("#d1a03a"), rot=ang)


def sphinx(M, mat, p, z, ang, col=hexc("#8f8a7e")):
    """Recumbent sphinx/lion on the pier: body block, forepaws, raised head with mane."""
    ux, uy = math.cos(ang), math.sin(ang)
    M.box(mat, (p[0], p[1], z + 0.45), (1.9, 1.1, 0.9), col, rot=ang)
    M.box(mat, (p[0] + ux * 1.0, p[1] + uy * 1.0, z + 0.2), (0.7, 0.55, 0.4), shade(col, 0.95), rot=ang)
    M.box(mat, (p[0] + ux * 0.6, p[1] + uy * 0.6, z + 1.2), (0.7, 0.8, 0.8), shade(col, 1.05), rot=ang)
    M.dome(mat, (p[0] + ux * 0.62, p[1] + uy * 0.62), 0.45, z + 1.5, shade(col, 1.0), n=8, rings=2)
    M.box(mat, (p[0] - ux * 0.9, p[1] - uy * 0.9, z + 0.3), (0.5, 0.2, 0.2), shade(col, 0.9), rot=ang + 0.3)


def house(M, fp, wallm, plinth, roofm, eave, rise, trimm, roof_col=WHITE, hip=1.0, bw=3.2, sh=3.1, base_z=None, gz=None, entry_dir=None, eave_out=0.7, nx=1, ny=1):
    """Prism walls on a footprint with window texture, stone plinth, hip/gable roof on the min rotated rectangle. Returns (centre, ang, Lg, Sh)."""
    pts = list(fp.exterior.coords)[:-1]; c = np.array(fp.centroid.coords[0]); zc = gz(*c)
    r = list(fp.minimum_rotated_rectangle.exterior.coords)[:4]; e1 = np.subtract(r[1], r[0]); e2 = np.subtract(r[2], r[1])
    if np.hypot(*e1) < np.hypot(*e2): e1, e2 = e2, e1
    ang = math.atan2(e1[1], e1[0]); Lg, Sh = float(np.hypot(*e1)), float(np.hypot(*e2))
    K.wall_band(M, plinth, pts, zc - 1.0, zc + 0.8, 3.0, 1.5)
    K.wall_band(M, wallm, [tuple(p) for p in pts], zc + 0.8, zc + eave, bw, sh, nx=nx, ny=ny)
    M.prism(trimm, list(fp.buffer(0.18, join_style=2).exterior.coords)[:-1], zc + eave - 0.55, zc + eave + 0.05, hexc("#d9cfb2"), top=False)
    K.pitched(M, roofm, tuple(c), Lg, Sh, zc + eave, rise, rot=ang, eave=eave_out, hip=hip, tile=1.0, col=roof_col)
    return c, ang, Lg, Sh, zc

nodes, els = sources.osm(); W = {e["id"]: e for e in els if e["type"] == "way"}
def osm_fp(i): return Polygon([nodes[n] for n in W[i]["nodes"]]).buffer(0).simplify(0.3)

M = L.Model(origin=(O[0], O[1], 0.0))
HOUSE, HALL, DOMEW = wall_mats(M)
PLINTH = M.mat("plinth", rough=0.95, tex=K.stone_tex("#8f8a7c", 0.25, seed=4, rustic=0.12), repeat=True)
ROOFT = M.mat("tiles", rough=0.85, tex=K.tile_roof_tex("#8a503f", seed=3, var=0.22, moss=0.04), repeat=True)
ROOFS = M.mat("slate", rough=0.85, tex=K.slate_tex("#5b6066"), repeat=True)
STONE = M.mat("stone", rough=0.95, tex=K.stone_tex("#9d988b", 0.3, seed=8, rustic=0.25), repeat=True)
IVY = M.mat("ivy_wall", rough=1.0, tex=None)
ms = M.mat("trim", rough=0.9); mc = M.mat("copper", rough=0.55, metal=0.2)
GOLD = M.mat("gold", rough=0.4, metal=0.3)
SAND = hexc("#d8cfb4"); SLATE = hexc("#5b6066"); COP = hexc("#6fa58f")
def z_at(x, y): return float(H.at(x, y)) - ZO

# ---- Altes Krematorium / Aufbahrungshalle (dome hall with colonnade) ---------------------------------------------------
o = [o for o in F.near(-703, -761, 15) if o["id"][3:11] == "52331290"][0]
fp = F.footprint(o).simplify(0.3); pts = list(fp.exterior.coords)[:-1]
c = np.array(fp.centroid.coords[0]); zc = z_at(*c)
r = list(fp.minimum_rotated_rectangle.exterior.coords)[:4]
e1 = np.subtract(r[1], r[0]); e2 = np.subtract(r[2], r[1]); ang = math.atan2(e1[1], e1[0])
EAVE = 6.6
M.box(ms, (c[0], c[1], zc + 0.25), (np.hypot(*e1) + 2.0, np.hypot(*e2) + 2.0, 0.5), hexc("#9a968b"), rot=ang)   # plinth
K.wall_band(M, PLINTH, pts, zc - 1.0, zc + 0.9, 3.0, 1.9)
K.wall_band(M, DOMEW, pts, zc + 0.9, zc + EAVE, 3.4, EAVE - 0.9, nx=2, ny=1)
M.prism(ms, list(fp.buffer(0.25, join_style=2).exterior.coords)[:-1], zc + EAVE - 0.6, zc + EAVE + 0.1, hexc("#e2d9bd"), top=False)
K.pitched(M, ROOFS, tuple(c), np.hypot(*e1), np.hypot(*e2), zc + EAVE, 2.4, rot=ang, eave=0.7, hip=1.0, tile=1.0)
# drum with 8 arched windows + dome
M.cyl(ms, tuple(c), 4.4, zc + EAVE + 1.0, zc + EAVE + 5.6, hexc("#d3c8a8"), n=8)
for k in range(8):
    a = 2 * math.pi * (k + 0.5) / 8
    M.box(ms, (c[0] + 4.1 * math.cos(a), c[1] + 4.1 * math.sin(a), zc + EAVE + 3.6), (0.2, 1.3, 2.4), hexc("#2a3038"), rot=a)
    M.box(ms, (c[0] + 4.08 * math.cos(a), c[1] + 4.08 * math.sin(a), zc + EAVE + 4.9), (0.22, 1.7, 0.3), hexc("#e8e0c8"), rot=a)
M.cyl(ms, tuple(c), 4.9, zc + EAVE + 5.6, zc + EAVE + 6.0, hexc("#b4ab92"), n=8)
M.dome(mc, tuple(c), 4.6, zc + EAVE + 6.0, COP, n=16, rings=5, sq=0.85)
M.cyl(mc, tuple(c), 0.9, zc + EAVE + 9.8, zc + EAVE + 11.0, hexc("#e6dfc8"), n=8)
M.cone(mc, tuple(c), 1.0, zc + EAVE + 11.0, zc + EAVE + 12.6, COP, n=8)
M.box(ms, (c[0], c[1], zc + EAVE + 13.0), (0.12, 0.12, 1.0), hexc("#c8a64a"))
# portico towards the main gate
best = None
for i in range(len(pts)):
    a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)]); t = b - a
    if np.hypot(*t) < 6: continue
    nn = np.array([t[1], -t[0]]) / np.hypot(*t)
    if np.dot(nn, (a + b) / 2 - c) < 0: nn = -nn
    sc = np.dot(nn, GATE - (a + b) / 2) / np.hypot(*(GATE - (a + b) / 2))
    if best is None or sc > best[0]: best = (sc, (a + b) / 2, nn, math.atan2(t[1], t[0]))
_, mid, nn, fa = best; tx = np.array([math.cos(fa), math.sin(fa)])
M.box(ms, (*(mid + nn * 2.2), zc + 0.2), (8.4, 4.8, 0.4), hexc("#a29e92"), rot=fa)
for st in range(3): M.box(ms, (*(mid + nn * (4.8 + 0.4 * st)), zc + 0.1), (7.6, 0.5, 0.2), hexc("#b5b0a2"), rot=fa)
for k in range(-2, 3):
    p_ = mid + tx * k * 1.8 + nn * 3.9
    M.cyl(ms, tuple(p_), 0.38, zc + 0.4, zc + 5.4, hexc("#e4dcc3"), n=10); M.cyl(ms, tuple(p_), 0.5, zc + 0.4, zc + 0.8, hexc("#c9c1a8"), n=10); M.cyl(ms, tuple(p_), 0.5, zc + 5.2, zc + 5.5, hexc("#c9c1a8"), n=10)
M.box(ms, (*(mid + nn * 2.9), zc + 5.8), (8.4, 4.2, 0.7), hexc("#d2c9ae"), rot=fa)
K.pitched(M, ROOFS, tuple(mid + nn * 2.9), 8.8, 4.4, zc + 6.15, 1.7, rot=fa, eave=0.0, tile=1.0, col=hexc("#d6cdb2"), gable_mat=ms, gable_col=hexc("#e0d8c0"))
M.box(ms, (*(mid + nn * 0.1), zc + 2.4), (3.0, 0.2, 4.0), hexc("#2f2a26"), rot=fa)

# ---- Verwaltungshaus am Haupteingang (Heimatstil, 2 Geschosse, Walmdach) --------------------------------------------------
f3 = osm_fp(36997317); house(M, f3, HOUSE, PLINTH, ROOFT, 7.4, 3.6, ms, hip=1.0, bw=3.3, sh=3.4, gz=z_at, nx=4, ny=2)
c3 = np.array(f3.centroid.coords[0])
# ---- Kapellen (Saal mit hohen Rundbogenfenstern, Saeulen/Pilaster, Freitreppe) --------------------------------------------
for oid, eave, rise, gable in ((37007820, 5.6, 2.8, False), (212107152, 6.0, 3.2, False)):
    f2 = osm_fp(oid); cc, an, Lg, Sh, z2 = house(M, f2, HALL, PLINTH, ROOFT, eave, rise, ms, hip=0.0, bw=4.0, sh=eave - 0.8, gz=z_at, eave_out=0.8, nx=4, ny=1)
    for sgn in (-1, 1):   # entrance steps on the long side facing the gate
        pass
    # pilasters along the long faces
    ux, uy = math.cos(an), math.sin(an); nx_, ny_ = -uy, ux
    for sg in (-1, 1):
        for k in range(-int(Lg / 4.0) // 2, int(Lg / 4.0) // 2 + 1):
            q = cc + np.array([ux, uy]) * k * 4.0 + np.array([nx_, ny_]) * sg * (Sh / 2 + 0.08)
            M.box(ms, (q[0], q[1], z2 + eave / 2), (0.5, 0.3, eave - 0.2), hexc("#e6dcc0"), rot=an)

# ---- Haupttor D: Bruchstein-Pfeiler mit Sphingen, Mauer, schmiedeeisernes Tor mit Goldmedaillons ---------------------------
cem = Polygon([nodes[n] for n in W[10634343]["nodes"]])
q = cem.exterior.interpolate(cem.exterior.project(Point(*GATE))); q2 = cem.exterior.interpolate(cem.exterior.project(Point(*GATE)) + 2.0)
tg = np.array([q2.x - q.x, q2.y - q.y]); tg /= np.hypot(*tg); gang = math.atan2(tg[1], tg[0]); gc = np.array([q.x, q.y]); gz_ = z_at(*gc)
PIER = M.mat("pier", rough=0.95, tex=K.metal_panel_tex("#a39e90", 256, 6, rust=0.0), repeat=True)
for sg in (-1, 1):
    p_ = gc + tg * sg * 3.1
    K.box_tex(M, PIER, (p_[0], p_[1], gz_ + 2.1), (1.7, 1.7, 4.2), rot=gang, col=WHITE, tile=(1.7, 4.2), top=hexc("#a8a396"))
    M.box(ms, (p_[0], p_[1], gz_ + 0.25), (2.0, 2.0, 0.5), hexc("#8f8a7e"), rot=gang)             # base course
    M.box(ms, (p_[0], p_[1], gz_ + 4.3), (2.1, 2.1, 0.3), hexc("#b3ae9f"), rot=gang)             # cap slab
    sphinx(M, ms, p_, gz_ + 4.45, gang + (math.pi / 2 if sg > 0 else -math.pi / 2), col=hexc("#7f7a6e"))
    for k in range(1, 6):                                                                         # boundary wall with coping
        p2_ = gc + tg * sg * (3.1 + 0.85 + k * 3.0 - 1.5)
        K.box_tex(M, STONE, (p2_[0], p2_[1], gz_ + 1.0), (3.0, 0.6, 2.0), rot=gang, col=WHITE, tile=(2.0, 1.0), top=hexc("#9a9588"))
        M.box(ms, (p2_[0], p2_[1], gz_ + 2.08), (3.1, 0.8, 0.16), hexc("#8d897d"), rot=gang)
# gate: one leaf closed in the opening (left), the other swung open (right), both 2.4 m wide
gate_leaf(M, ms, GOLD, gc - tg * 2.2, tg, w=2.2, h=2.7, hang=0.0)
hinge = gc + tg * 2.2
gate_leaf(M, ms, GOLD, hinge, -tg, w=2.2, h=2.7, hang=math.radians(-75))
# fixed lantern posts at the entrance
for sg in (-1, 1):
    p_ = gc + tg * sg * 5.6 + np.array([-tg[1], tg[0]]) * 1.4
    M.cyl(ms, tuple(p_), 0.06, gz_, gz_ + 3.0, hexc("#2a2d31"), n=6)
# sculpture group «Kauernder Mann, kauernde Frau» (Markwalder) inside the gate
sp = np.array([-706.2, -745.7]); sz = z_at(*sp)
M.box(ms, (sp[0], sp[1], sz + 0.4), (2.6, 1.2, 0.8), hexc("#8a867b"), rot=gang)
for dx in (-0.6, 0.6):
    M.box(ms, (sp[0] + dx * tg[0], sp[1] + dx * tg[1], sz + 1.2), (0.7, 0.6, 0.8), hexc("#6d6a63"), rot=gang)
    M.dome(ms, (sp[0] + dx * tg[0], sp[1] + dx * tg[1]), 0.28, sz + 1.6, hexc("#6d6a63"), n=8, rings=2)
os.makedirs(os.path.dirname(OUT), exist_ok=True); M.write(OUT); print("krematorium tris", M.tris(), "gate", gc.round(1).tolist(), "z", round(ZO, 2))
