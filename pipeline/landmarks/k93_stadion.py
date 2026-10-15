"""Stadion Letzigrund (Badenerstrasse 500) -> web/public/models/landmarks/k93_stadion.glb
Footprints: OSM grandstands A-D (stand ring), swissBUILDINGS3D roof (roof ring + heights), OSM pitch (axis).
Origin = pitch centre at pitch level. Run: .venv/bin/python pipeline/landmarks/k93_stadion.py"""
import sys, os, math, random, json
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, k93_kit as K
import sources, terrain
from k93_lib import hexc, shade

ROOT = F.ROOT
OUT = ROOT + "/web/public/models/landmarks/k93_stadion.glb"
random.seed(7)
N = 128

# ---------------------------------------------------------------------------------------------------- geometry input
nodes, els = sources.osm()
ways = {e["id"]: np.array([nodes[n] for n in e["nodes"]]) for e in els if e["type"] == "way" and e["id"] in (1274254437, 1274254438, 1274254439, 1274254440, 168927595)}
stands = unary_union([Polygon(ways[i]).buffer(0) for i in (1274254437, 1274254438, 1274254439, 1274254440)]).buffer(0.5)
s_out = Polygon(stands.exterior).buffer(2).buffer(-2).simplify(0.6)
s_in = Polygon(stands.interiors[0]).buffer(-3).buffer(3).simplify(0.6)
o = [o for o in F.near(-970, -165, 150) if o["id"].startswith("ID_C1FCBE2D")][0]
roofu = unary_union([Polygon(q[:, :2]).buffer(0) for k, q in o["polys"] if k == 2 and len(q) >= 3]).buffer(0.3)
r_out = Polygon(roofu.exterior).buffer(2).buffer(-2).simplify(0.6)
r_in = Polygon(roofu.interiors[0]).buffer(-3).buffer(3).simplify(0.6)
pitch = Polygon(ways[168927595][:-1])
PC = np.array(pitch.centroid.coords[0])
p = ways[168927595]; ALPHA = math.atan2(p[1][1] - p[0][1], p[1][0] - p[0][0])  # long axis (first edge is the long one)
if np.linalg.norm(p[1] - p[0]) < np.linalg.norm(p[2] - p[1]): ALPHA = math.atan2(p[2][1] - p[1][1], p[2][0] - p[1][0])
H = terrain.heights((PC[0] - 20, PC[1] - 20, PC[0] + 20, PC[1] + 20), 2.0, z_shift=-3.06)
ZP = float(H.at(*PC))
C = tuple(PC)
print("pitch centre", PC.round(1), "alpha", round(math.degrees(ALPHA), 1), "ground z", round(ZP, 2))


def hit(poly, th, far=True):
    ring = poly.exterior
    ln = LineString([C, (C[0] + 400 * math.cos(th), C[1] + 400 * math.sin(th))])
    x = ring.intersection(ln)
    pts = [x] if x.geom_type == "Point" else list(x.geoms)
    pts = sorted(pts, key=lambda q: Point(C).distance(q))
    q = pts[-1] if far else pts[0]
    return np.array(q.coords[0])


# equal-arclength rays on the inner stand ring
ths = []
for i in range(N):
    q = s_in.exterior.interpolate(i / N, normalized=True)
    ths.append(math.atan2(q.y - C[1], q.x - C[0]))
d_ = sum(math.atan2(math.sin(ths[(k + 1) % N] - ths[k]), math.cos(ths[(k + 1) % N] - ths[k])) for k in range(N))
if d_ < 0: ths = ths[::-1]
A = [hit(s_in, t, far=False) for t in ths]   # inner edge of stands (field boundary)
B = [hit(s_out, t) for t in ths]              # rear of upper tier
RI = [hit(r_in, t, far=False) for t in ths]   # roof inner edge
RO = [hit(r_out, t) for t in ths]             # roof outer edge
FA = []                                        # facade ring = roof outer, 2 m inboard
for i in range(N):
    d = RO[i] - np.array(C); FA.append(np.array(C) + d * (1 - 2.0 / np.linalg.norm(d)))
# ensure facade >= stand rear
for i in range(N):
    if np.linalg.norm(FA[i] - C) < np.linalg.norm(B[i] - C) + 0.5: FA[i] = np.array(C) + (B[i] - C) * 1.02
dep = [np.linalg.norm(B[i] - A[i]) for i in range(N)]
print("stand depth min/mean/max", round(min(dep), 1), round(float(np.mean(dep)), 1), round(max(dep), 1))

# ---------------------------------------------------------------------------------------------------- track / pitch fit
STR, RAD, LW, NL = 84.39, 36.5, 1.22, 8
ROUT = RAD + NL * LW
ca, sa = math.cos(ALPHA), math.sin(ALPHA)
def tr_to_world(u, v): return (C[0] + u * ca - v * sa, C[1] + u * sa + v * ca)
obr = unary_union([Polygon([tr_to_world(-STR / 2, -ROUT), tr_to_world(STR / 2, -ROUT), tr_to_world(STR / 2, ROUT), tr_to_world(-STR / 2, ROUT)]),
                   Point(tr_to_world(-STR / 2, 0)).buffer(ROUT), Point(tr_to_world(STR / 2, 0)).buffer(ROUT)])
print("track fits in bowl:", s_in.contains(obr), "margin", round(s_in.exterior.distance(obr), 1), "outside area", round(obr.difference(s_in).area, 1))

# ---------------------------------------------------------------------------------------------------- textures
def field_texture():
    S = 2  # supersample
    W, Hh = 2048 * S, 1228 * S
    ppm = 10.24 * S
    im = Image.new("RGB", (W, Hh), hexc("#7d8379")[:3]); d = ImageDraw.Draw(im)
    X = lambda u: (u + 100) * ppm
    Y = lambda v: (v + 60) * ppm
    def obround(r, fill):
        d.rectangle([X(-STR / 2), Y(-r), X(STR / 2), Y(r)], fill=fill)
        for sx in (-1, 1): d.ellipse([X(sx * STR / 2 - r), Y(-r), X(sx * STR / 2 + r), Y(r)], fill=fill)
    obround(ROUT + 0.25, (226, 226, 222))                  # outer kerb line
    obround(ROUT, (186, 84, 56))                            # red tartan
    for k in range(NL + 1):                                 # lane lines
        r = RAD + k * LW; w = 0.06 * ppm
        d.arc([X(-STR / 2 - r), Y(-r), X(-STR / 2 + r), Y(r)], 90, 270, fill=(238, 238, 234), width=max(2, int(w)))
        d.arc([X(STR / 2 - r), Y(-r), X(STR / 2 + r), Y(r)], 270, 90, fill=(238, 238, 234), width=max(2, int(w)))
        for sgn in (-1, 1): d.line([X(-STR / 2), Y(sgn * r), X(STR / 2), Y(sgn * r)], fill=(238, 238, 234), width=max(2, int(w)))
    # infield grass with mowing stripes
    obround(RAD - 0.18, (230, 230, 226)); obround(RAD - 0.5, (74, 148, 58))
    for i in range(14):
        u0 = -52.5 + i * 7.5
        if i % 2: d.rectangle([X(u0), Y(-34), X(u0 + 7.5), Y(34)], fill=(86, 160, 66))
        else: d.rectangle([X(u0), Y(-34), X(u0 + 7.5), Y(34)], fill=(78, 152, 60))
    lw = max(3, int(0.12 * ppm)); wl = (240, 244, 240)
    d.rectangle([X(-52.5), Y(-34), X(52.5), Y(34)], outline=wl, width=lw); d.line([X(0), Y(-34), X(0), Y(34)], fill=wl, width=lw)
    d.ellipse([X(-9.15), Y(-9.15), X(9.15), Y(9.15)], outline=wl, width=lw); d.ellipse([X(-.3), Y(-.3), X(.3), Y(.3)], fill=wl)
    for sx in (-1, 1):
        d.rectangle([X(sx * 52.5 - (16.5 if sx > 0 else 0)), Y(-20.15), X(sx * 52.5 + (0 if sx > 0 else 16.5)), Y(20.15)], outline=wl, width=lw)
        d.rectangle([X(sx * 52.5 - (5.5 if sx > 0 else 0)), Y(-9.16), X(sx * 52.5 + (0 if sx > 0 else 5.5)), Y(9.16)], outline=wl, width=lw)
    # finish line + start marks on the home straight
    d.rectangle([X(30), Y(RAD), X(30.4), Y(ROUT)], fill=(245, 245, 245))
    for k in range(NL): d.rectangle([X(30.4), Y(RAD + k * LW + .1), X(32.4), Y(RAD + (k + 1) * LW - .1)], fill=(166, 70, 46) if k % 2 else (196, 98, 66))
    return im.resize((2048, 1228), Image.LANCZOS)


def seat_texture():
    """Top half = seat backs (rounded shells on a dark gap), bottom half = cushions; tinted by vertex colour."""
    im = Image.new("RGB", (128, 128), (40, 36, 38)); d = ImageDraw.Draw(im)
    for k in range(4):
        x0 = k * 32
        d.rounded_rectangle([x0 + 3, 4, x0 + 29, 62], 7, fill=(255, 255, 255))
        d.rounded_rectangle([x0 + 8, 10, x0 + 24, 36], 5, fill=(236, 236, 236))
        d.rounded_rectangle([x0 + 3, 68, x0 + 29, 124], 6, fill=(232, 232, 232))
        d.line([x0 + 6, 76, x0 + 26, 76], fill=(255, 255, 255), width=2)
    return im


def board_texture():
    """Perimeter advertising boards: dark blue panels with a white stripe and a thin light rim."""
    im = Image.new("RGB", (256, 32), (28, 52, 98)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 255, 2], fill=(210, 214, 220)); d.rectangle([0, 13, 255, 17], fill=(236, 238, 242))
    for x in range(0, 256, 128): d.line([x, 3, x, 31], fill=(18, 34, 70), width=2)
    return im


# ---------------------------------------------------------------------------------------------------- model
M = L.Model(origin=(C[0], C[1], 0.0))
CONC = M.mat("concrete", rough=0.95)
SEAT = M.mat("seats", rough=0.8, tex=seat_texture(), repeat=True)
FLD = M.mat("field", rough=0.95, tex=field_texture(), repeat=False)
SLAT_IM = K.slat_tex("#8a4a38", 256, 16)
WHITE = (255, 255, 255, 255)
ROOFU = M.mat("roof_under", rough=0.7, tex=SLAT_IM, repeat=True,
              emis=SLAT_IM.point(lambda v: int(v * 0.42)))
FAC = M.mat("facade", rough=0.7, tex=K.metal_panel_tex("#3d3b3a", 256, 8, rust=0.25), repeat=True)
GLZ_P = K.window(wall="#2c2b2a", frame="#1d1d1e", glass="#2e3b45", fw=0.82, fh=0.74, top=0.1, cols=2, rows=2, sill="#3a3a3a", noise=3, mun=3)
GB, GE = K.tile(4, 2, 64, 128, GLZ_P, seed=11, lit=0.55)
GLASS = M.mat("loge_glass", rough=0.3, tex=GB, emis=GE, repeat=True)
BRD = M.mat("boards", rough=0.8, tex=board_texture(), repeat=True)
LAMP = K.lamp_mat(M, "lamps", "#fff6d8")
SCR = K.lamp_mat(M, "screens", "#3e72b8", emcol=(60, 120, 230))
STEEL = M.mat("steel", rough=0.5, metal=0.0)
TXT = {}
P3 = lambda xy, z: (float(xy[0]), float(xy[1]), z)
lerp = lambda a, b, t: a + (b - a) * t
RED = [hexc("#a8222a"), hexc("#9a1e26"), hexc("#b42a31"), hexc("#a8222a")]
def seat_col(i, k, tier):
    r = random.Random(i // 3 * 131 + k // 4 * 17 + tier * 1000)
    c = r.choice(RED)
    if r.random() < 0.05: c = hexc("#3b3f46")           # dark spare seats
    return c
GREY = hexc("#9a9893"); GREY2 = hexc("#7d7b78"); DARK = hexc("#32353b"); STAIR = hexc("#4a505a")

# field fan
for i in range(N):
    j = (i + 1) % N
    pts = [C, A[i], A[j]]
    uv = []
    for q in pts:
        dx, dy = q[0] - C[0], q[1] - C[1]
        uu, vv = dx * ca + dy * sa, -dx * sa + dy * ca
        uv.append(((uu + 100) / 200, (vv + 60) / 120))
    M.tri(FLD, P3(C, 0.04), P3(A[i], 0.04), P3(A[j], 0.04), (255, 255, 255, 255), uv)

LOW = dict(s0=0.0, s1=0.44, rows=13, z0=1.3, dz=0.46)
UPP = dict(s0=0.53, s1=0.95, rows=15, z0=8.0, dz=0.5)
def at(i, s): return A[i] + (B[i] - A[i]) * s
cum = [0.0]
for i in range(N): cum.append(cum[-1] + np.linalg.norm(A[(i + 1) % N] - A[i]))
AISLE = lambda i: (i % 8) in (0,)
for i in range(N):
    j = (i + 1) % N
    u0, u1 = cum[i] / 2.0, cum[i + 1] / 2.0
    # perimeter boards
    M.quad(BRD, P3(A[i], 0), P3(A[i], 1.1), P3(A[j], 1.1), P3(A[j], 0), WHITE, [(cum[i] / 16, 1), (cum[i] / 16, 0), (cum[i + 1] / 16, 0), (cum[i + 1] / 16, 1)])
    M.quad(CONC, P3(A[i], 1.1), P3(A[i], 1.3), P3(A[j], 1.3), P3(A[j], 1.1), shade(GREY, 0.8))
    for tier, T in enumerate((LOW, UPP)):
        for k in range(T["rows"]):
            sa_, sb_ = lerp(T["s0"], T["s1"], k / T["rows"]), lerp(T["s0"], T["s1"], (k + 1) / T["rows"])
            z = T["z0"] + T["dz"] * k
            if AISLE(i):   # stair aisle: plain steps, no seats
                M.quad(CONC, P3(at(i, sa_), z), P3(at(i, sb_), z), P3(at(j, sb_), z), P3(at(j, sa_), z), STAIR)
                M.quad(CONC, P3(at(i, sb_), z), P3(at(i, sb_), z + T["dz"]), P3(at(j, sb_), z + T["dz"]), P3(at(j, sb_), z), shade(STAIR, 0.8))
            else:
                col = seat_col(i, k, tier); z2 = z + T["dz"]
                M.quad(SEAT, P3(at(i, sa_), z), P3(at(i, sb_), z), P3(at(j, sb_), z), P3(at(j, sa_), z), shade(col, 0.8), [(u0, 0.5), (u0, 1), (u1, 1), (u1, 0.5)])   # cushion
                M.quad(SEAT, P3(at(i, sb_), z), P3(at(i, sb_), z2), P3(at(j, sb_), z2), P3(at(j, sb_), z), col, [(u0, 0.5), (u0, 0), (u1, 0), (u1, 0.5)])         # backrest
    zl = LOW["z0"] + LOW["dz"] * LOW["rows"]
    s_l = LOW["s1"]; s_c = UPP["s0"]
    M.quad(CONC, P3(at(i, s_l), zl), P3(at(i, s_c), zl), P3(at(j, s_c), zl), P3(at(j, s_l), zl), shade(GREY, 1.0))
    M.quad(CONC, P3(at(i, s_c), zl), P3(at(i, s_c), UPP["z0"]), P3(at(j, s_c), UPP["z0"]), P3(at(j, s_c), zl), DARK if (i % 8) in (3, 4) else shade(GREY2, 0.75))
    zu = UPP["z0"] + UPP["dz"] * UPP["rows"]
    M.quad(CONC, P3(at(i, UPP["s1"]), zu), P3(B[i], zu), P3(B[j], zu), P3(at(j, UPP["s1"]), zu), shade(GREY, 1.05))
    M.quad(CONC, P3(B[i], zu), P3(FA[i], zu), P3(FA[j], zu), P3(B[j], zu), shade(GREY, 1.0))
    M.quad(CONC, P3(at(i, UPP["s1"]), zu), P3(at(i, UPP["s1"]), zu + 1.0), P3(at(j, UPP["s1"]), zu + 1.0), P3(at(j, UPP["s1"]), zu), shade(GREY2, .7))

# facade: lower dark-metal skin with ribs, glazed loge band under the roof (lit at night)
ZPL, ZTOP = 9.0, 23.0
zr_in, zr_out = 13.0, 23.6
ZG0 = zu = UPP["z0"] + UPP["dz"] * UPP["rows"]
for i in range(N):
    j = (i + 1) % N
    Lseg = cum[i + 1] - cum[i]; uu0, uu1 = cum[i] / 8.0, cum[i + 1] / 8.0
    M.quad(FAC, P3(FA[i], -1.5), P3(FA[j], -1.5), P3(FA[j], ZG0), P3(FA[i], ZG0), shade(WHITE, 0.9 + 0.1 * math.cos(ths[i])), [(uu0, 3.0), (uu1, 3.0), (uu1, 0), (uu0, 0)])
    zt = ZTOP - 0.8
    M.quad(GLASS, P3(FA[i], ZG0), P3(FA[j], ZG0), P3(FA[j], zt), P3(FA[i], zt), shade(WHITE, 0.9 + 0.1 * math.cos(ths[i] + .8)), [(cum[i] / 8.0, 1), (cum[i + 1] / 8.0, 1), (cum[i + 1] / 8.0, 0), (cum[i] / 8.0, 0)])
    M.quad(CONC, P3(FA[i], ZG0 - 0.1), P3(FA[j], ZG0 - 0.1), P3(FA[j], ZG0 + 0.3), P3(FA[i], ZG0 + 0.3), hexc("#2a2928"))
    t = FA[j] - FA[i]; ang = math.atan2(t[1], t[0]); nrm = np.array([t[1], -t[0]]) / np.linalg.norm(t)
    if i % 2 == 0:   # vertical ribs
        pos = FA[i] + nrm * 0.3
        M.box(CONC, (pos[0], pos[1], (ZG0 + ZTOP - 0.8) / 2), (0.5, 0.5, ZTOP - 0.8 - ZG0), hexc("#2b2a29"), rot=ang)
        M.box(CONC, (pos[0], pos[1], (-1.5 + ZG0) / 2), (0.6, 0.6, ZG0 + 1.5), hexc("#2e2d2c"), rot=ang)

# roof: dark top, timber underside (slats), red-brown fascia
for i in range(N):
    j = (i + 1) % N
    ci = hexc("#3b2f2d"); cf = hexc("#7d3b2c")
    M.quad(CONC, P3(RI[i], zr_in), P3(RO[i], zr_out), P3(RO[j], zr_out), P3(RI[j], zr_in), shade(ci, 0.9 + 0.1 * math.cos(ths[i])))
    d0 = np.linalg.norm(RO[i] - RI[i])
    M.quad(ROOFU, P3(RI[i], zr_in - 0.5), P3(RI[j], zr_in - 0.5), P3(RO[j], zr_out - 0.5), P3(RO[i], zr_out - 0.5), shade(WHITE, 0.82),
           [(cum[i] / 12.0, 0), (cum[i + 1] / 12.0, 0), (cum[i + 1] / 12.0, d0 / 12.0), (cum[i] / 12.0, d0 / 12.0)])
    M.quad(CONC, P3(RO[i], zr_out - 0.9), P3(RO[j], zr_out - 0.9), P3(RO[j], zr_out + 0.15), P3(RO[i], zr_out + 0.15), cf)
    M.quad(CONC, P3(RI[i], zr_in - 1.9), P3(RI[j], zr_in - 1.9), P3(RI[j], zr_in + 0.1), P3(RI[i], zr_in + 0.1), cf)   # inner fascia (towards pitch)
    pdir = np.array(C) - RI[i]; pdir = pdir / np.linalg.norm(pdir)
    # downlights on the underside (3 per ray every 2nd ray)
    if i % 2 == 0:
        for f in (0.22, 0.5, 0.78):
            q = RI[i] + (RO[i] - RI[i]) * f; zq = lerp(zr_in, zr_out, f) - 0.52
            M.quad(LAMP, P3(q + pdir * 0.35, zq), P3(q - pdir * 0.35, zq), P3(q - pdir * 0.35 + np.array([-pdir[1], pdir[0]]) * 0.7, zq), P3(q + pdir * 0.35 + np.array([-pdir[1], pdir[0]]) * 0.7, zq), WHITE, flip=True)
    # steel rafters visible at the inner edge
    if i % 4 == 0:
        a, b = FA[i], RI[i]
        m_ = (np.array(a) + np.array(b)) / 2; dv = np.array(b) - np.array(a); ang_ = math.atan2(dv[1], dv[0])
        M.box(STEEL, (m_[0], m_[1], (ZTOP - 0.8 + zr_in - 0.5) / 2 - 0.2), (np.linalg.norm(dv), 0.45, 0.55), hexc("#4a4d52"), rot=ang_)

# roof-edge masts with floodlights + cable stays, inclined columns at the facade
MAST_H = 12.5
for i in range(0, N, 6):
    out = (RO[i] - np.array(C)); out /= np.linalg.norm(out)
    base = RO[i] - out * 0.4
    top = base + out * 1.5
    K.tube(M, STEEL, (*base, zr_out), (*top, zr_out + MAST_H), 0.18, hexc("#d9dcde"), n=6)
    ang_ = math.atan2(out[1], out[0]) + math.pi / 2
    for dz in (0.0, 0.9, 1.8):  # lamp battery facing the pitch
        q = top - out * 0.7
        M.box(STEEL, (q[0], q[1], zr_out + MAST_H - 0.3 - dz), (3.6, 0.35, 0.8), hexc("#454a50"), rot=ang_)
        M.box(LAMP, (q[0] - out[0] * 0.25, q[1] - out[1] * 0.25, zr_out + MAST_H - 0.3 - dz), (3.4, 0.12, 0.62), hexc("#fff6d8"), rot=ang_)
    for dj in (-4, 4):  # stays to the roof edge
        tgt = RO[(i + dj) % N]
        K.tube(M, STEEL, (*top, zr_out + MAST_H - 0.5), (*tgt, zr_out + 0.1), 0.04, hexc("#b9bec2"), n=4)
    # inclined column from the ground outside the facade to the roof edge
    foot = FA[i] + out * 3.0
    K.tube(M, STEEL, (*foot, -1.5), (*RO[i], zr_out - 0.6), 0.3, hexc("#c9cdd0"), n=6)

# entrance portals with sector letters
for n_, ph in enumerate(np.linspace(0.04, 0.96, 11)):
    i = int(ph * N) % N; j = (i + 1) % N
    t = FA[j] - FA[i]; ang = math.atan2(t[1], t[0]); nrm = np.array([t[1], -t[0]]) / np.linalg.norm(t)
    mid = (FA[i] + FA[j]) / 2
    z0 = -1.0
    M.box(CONC, (*(mid + nrm * 0.9), z0 + 3.5), (9.0, 1.8, 7.0), hexc("#b9bbbd"), rot=ang, top=hexc("#8d9094"))
    M.box(CONC, (*(mid + nrm * 1.75), z0 + 3.0), (6.2, 0.2, 5.4), hexc("#14171b"), rot=ang)
    M.box(LAMP, (*(mid + nrm * 1.8), z0 + 5.9), (5.6, 0.12, 0.35), hexc("#fff0c0"), rot=ang)          # lit canopy strip
    M.box(CONC, (*(mid + nrm * 1.9), z0 + 6.5), (7.4, 0.3, 0.7), hexc("#c62a2f"), rot=ang)            # red lintel
    for st in range(3):
        M.box(CONC, (*(mid + nrm * (2.6 + st * 0.7)), z0 + 0.25), (8.4, 0.7, 0.5), shade(GREY, 0.9), rot=ang)
    for dx in (-2.2, 0.0, 2.2):   # turnstile bars
        q = mid + nrm * 1.2 + np.array([t[0], t[1]]) / np.linalg.norm(t) * dx
        M.box(STEEL, (q[0], q[1], z0 + 1.1), (0.08, 0.08, 1.0), hexc("#9ea3a8"))

# video walls on the roof inner edge at both ends of the long axis (screens glow at night)
for sgn in (-1, 1):
    th = ALPHA + (0 if sgn > 0 else math.pi)
    i = min(range(N), key=lambda k: abs(math.atan2(math.sin(ths[k] - th), math.cos(ths[k] - th))))
    pdir = np.array(C) - RI[i]; pdir = pdir / np.linalg.norm(pdir); ang = math.atan2(pdir[1], pdir[0]) + math.pi / 2
    q = RI[i] + pdir * 0.3
    M.box(CONC, (q[0], q[1], zr_in - 3.6), (15.0, 0.8, 5.6), hexc("#26292e"), rot=ang)
    q2 = RI[i] + pdir * 0.75
    M.box(SCR, (q2[0], q2[1], zr_in - 3.6), (13.6, 0.1, 4.4), hexc("#3d6fa8"), rot=ang)

# goals at both ends of the pitch + corner flags + dugouts
for sgn in (-1, 1):
    gx, gy = C[0] + sgn * 52.5 * ca, C[1] + sgn * 52.5 * sa
    gang = ALPHA + math.pi / 2
    for dd in (-3.66, 3.66):
        K.tube(M, STEEL, (gx + (-sa) * dd * 1 + 0 * ca, gy + ca * dd, 0.05), (gx - sa * dd, gy + ca * dd, 2.44), 0.06, hexc("#f2f2f2"), n=4)
    K.tube(M, STEEL, (gx + sa * 3.66, gy - ca * 3.66, 2.44), (gx - sa * 3.66, gy + ca * 3.66, 2.44), 0.06, hexc("#f2f2f2"), n=4)
# technical dugouts along the near touchline
for sgn in (-1, 1):
    px, py = C[0] - sa * 38.5 + ca * sgn * 8, C[1] + ca * 38.5 + sa * sgn * 8
    M.box(CONC, (px, py, 1.0), (7.0, 1.4, 1.4), hexc("#2f343a"), rot=ALPHA, top=hexc("#8fb4cf"))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
M.write(OUT)
print("tris", M.tris(), [(m.name, len(m.idx) // 3) for m in M.mats])
json.dump({"name": "Stadion Letzigrund", "x": round(C[0], 1), "y": round(C[1], 1), "z": round(ZP, 2)}, open(os.path.dirname(OUT) + "/k93_stadion.meta.json", "w"))
