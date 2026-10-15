"""Stadion Letzigrund (Badenerstrasse 500) -> web/public/models/landmarks/k93_stadion.glb
Footprints: OSM grandstands A-D (stand ring), swissBUILDINGS3D roof (roof ring + heights), OSM pitch (axis).
Origin = pitch centre at pitch level. Run: .venv/bin/python pipeline/landmarks/k93_stadion.py"""
import sys, os, math, random, json
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F
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
    obround(ROUT, (176, 62, 44))                            # red tartan
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
    for k in range(NL): d.rectangle([X(30.4), Y(RAD + k * LW + .1), X(32.4), Y(RAD + (k + 1) * LW - .1)], fill=(160, 54, 38) if k % 2 else (190, 72, 52))
    return im.resize((2048, 1228), Image.LANCZOS)


def seat_texture():
    im = Image.new("RGB", (128, 128), (60, 60, 64)); d = ImageDraw.Draw(im)
    for k in range(4):                                   # 4 seats per tile along u, rows along v
        x0 = k * 32
        d.rounded_rectangle([x0 + 3, 4, x0 + 29, 62], 5, fill=(246, 246, 246))     # seat back
        d.rounded_rectangle([x0 + 3, 66, x0 + 29, 118], 5, fill=(206, 206, 210))   # cushion
    return im

# ---------------------------------------------------------------------------------------------------- model
M = L.Model(origin=(C[0], C[1], 0.0))
CONC = M.mat("concrete", rough=0.95)
SEAT = M.mat("seats", rough=0.8, tex=seat_texture(), repeat=True)
FLD = M.mat("field", rough=0.95, tex=field_texture(), repeat=False)
P3 = lambda xy, z: (float(xy[0]), float(xy[1]), z)
lerp = lambda a, b, t: a + (b - a) * t
PAL = [hexc("#1f5aa6"), hexc("#f0f0f2"), hexc("#7fb0e0"), hexc("#2d3f66"), hexc("#d8dadf"), hexc("#1f5aa6"), hexc("#f0f0f2")]
RARE = hexc("#c8312b")
def seat_col(i, k, tier):
    r = random.Random(i // 3 * 131 + k // 4 * 17 + tier * 1000)
    c = r.choice(PAL)
    if r.random() < 0.07: c = RARE
    return c
GREY = hexc("#a9a9a5"); GREY2 = hexc("#8e8f8c"); DARK = hexc("#3b3e43")

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

# tier definitions: (s0, s1, rows, z_start, rise)
LOW = dict(s0=0.0, s1=0.44, rows=13, z0=1.3, dz=0.46)
UPP = dict(s0=0.53, s1=0.95, rows=15, z0=8.0, dz=0.5)
def at(i, s): return A[i] + (B[i] - A[i]) * s
cum = [0.0]
for i in range(N): cum.append(cum[-1] + np.linalg.norm(A[(i + 1) % N] - A[i]))
BOARD = hexc("#244a8c")
for i in range(N):
    j = (i + 1) % N
    u0, u1 = cum[i] / 2.0, cum[i + 1] / 2.0
    # perimeter wall (advertising boards, plain blue)
    M.quad(CONC, P3(A[i], 0), P3(A[i], 1.3), P3(A[j], 1.3), P3(A[j], 0), BOARD)
    for tier, T in enumerate((LOW, UPP)):
        for k in range(T["rows"]):
            sa_, sb_ = lerp(T["s0"], T["s1"], k / T["rows"]), lerp(T["s0"], T["s1"], (k + 1) / T["rows"])
            z = T["z0"] + T["dz"] * k
            col = seat_col(i, k, tier)
            M.quad(SEAT, P3(at(i, sa_), z), P3(at(i, sb_), z), P3(at(j, sb_), z), P3(at(j, sa_), z), col, [(u0, 0), (u0, 1), (u1, 1), (u1, 0)])
            # riser at the back edge of this row up to next row
            z2 = z + T["dz"]
            M.quad(CONC, P3(at(i, sb_), z), P3(at(i, sb_), z2), P3(at(j, sb_), z2), P3(at(j, sb_), z), shade(GREY, 0.85))
    # lower tier last riser -> concourse level, concourse, vomitory wall up to upper tier, upper last riser -> rear promenade
    zl = LOW["z0"] + LOW["dz"] * LOW["rows"]
    s_l = LOW["s1"]; s_c = UPP["s0"]
    M.quad(CONC, P3(at(i, s_l), zl), P3(at(i, s_c), zl), P3(at(j, s_c), zl), P3(at(j, s_l), zl), shade(GREY, 1.0))           # concourse
    M.quad(CONC, P3(at(i, s_c), zl), P3(at(i, s_c), UPP["z0"]), P3(at(j, s_c), UPP["z0"]), P3(at(j, s_c), zl), DARK if (i % 8) in (3, 4) else shade(GREY2, 0.9))  # wall / vomitories
    zu = UPP["z0"] + UPP["dz"] * UPP["rows"]
    M.quad(CONC, P3(at(i, UPP["s1"]), zu), P3(B[i], zu), P3(B[j], zu), P3(at(j, UPP["s1"]), zu), shade(GREY, 1.05))        # rear promenade
    M.quad(CONC, P3(B[i], zu), P3(FA[i], zu), P3(FA[j], zu), P3(B[j], zu), shade(GREY, 1.0))
    # rear railing line
    M.quad(CONC, P3(at(i, UPP["s1"]), zu), P3(at(i, UPP["s1"]), zu + 1.0), P3(at(j, UPP["s1"]), zu + 1.0), P3(at(j, UPP["s1"]), zu), shade(GREY2, .8))

# facade: concrete plinth + light cladding, ribs
ZPL, ZTOP = 9.0, 23.0
zr_in, zr_out = 17.0, 23.0
for i in range(N):
    j = (i + 1) % N
    M.quad(CONC, P3(FA[i], -1.5), P3(FA[j], -1.5), P3(FA[j], ZPL), P3(FA[i], ZPL), shade(hexc("#9a9b97"), 0.9 + 0.1 * math.cos(ths[i])))
    M.quad(CONC, P3(FA[i], ZPL), P3(FA[j], ZPL), P3(FA[j], ZTOP - 0.8), P3(FA[i], ZTOP - 0.8), shade(hexc("#d2d8dc"), 0.88 + 0.12 * math.cos(ths[i] + 0.8)))
    M.quad(CONC, P3(FA[i], ZPL + 0.0), P3(FA[j], ZPL + 0.0), P3(FA[j], ZPL + 0.5), P3(FA[i], ZPL + 0.5), hexc("#5d6064"))  # band
    # vertical rib every 2nd segment, standing 0.6 m proud
    if i % 2 == 0:
        t = FA[j] - FA[i]; ang = math.atan2(t[1], t[0]); nrm = np.array([t[1], -t[0]]) / np.linalg.norm(t)
        pos = FA[i] + nrm * 0.25
        M.box(CONC, (pos[0], pos[1], (ZPL + ZTOP - 0.8) / 2), (1.0, 0.6, ZTOP - 0.8 - ZPL), hexc("#aeb4b9"), rot=ang)

# roof (top lighter, underside darker, fascias)
for i in range(N):
    j = (i + 1) % N
    ci = hexc("#e3e6e8"); cu = hexc("#7e8388"); cf = hexc("#f4f5f6")
    M.quad(CONC, P3(RI[i], zr_in), P3(RO[i], zr_out), P3(RO[j], zr_out), P3(RI[j], zr_in), shade(ci, 0.96 + 0.04 * math.cos(ths[i])))
    M.quad(CONC, P3(RI[i], zr_in - 0.5), P3(RI[j], zr_in - 0.5), P3(RO[j], zr_out - 0.5), P3(RO[i], zr_out - 0.5), cu)
    M.quad(CONC, P3(RO[i], zr_out - 0.5), P3(RO[j], zr_out - 0.5), P3(RO[j], zr_out), P3(RO[i], zr_out), cf)
    M.quad(CONC, P3(RI[i], zr_in - 0.5), P3(RI[i], zr_in), P3(RI[j], zr_in), P3(RI[j], zr_in - 0.5), cf)
    M.quad(CONC, P3(RO[i], zr_out - 0.5), P3(RO[j], zr_out - 0.5), P3(FA[j], ZTOP - 0.8), P3(FA[i], ZTOP - 0.8), cu) if False else None
    # roof support: steel rafters (underside) every 4th ray
    if i % 4 == 0:
        a, b = FA[i], RI[i]
        m_ = (np.array(a) + np.array(b)) / 2; dv = np.array(b) - np.array(a); ang = math.atan2(dv[1], dv[0])
        M.box(CONC, (m_[0], m_[1], (ZTOP - 0.8 + zr_in - 0.5) / 2 - 0.2), (np.linalg.norm(dv), 0.5, 0.6), hexc("#555a60"), rot=ang)
    # floodlight bars on the inner roof edge
    if i % 5 == 2:
        pdir = np.array(C) - RI[i]; pdir = pdir / np.linalg.norm(pdir); ang = math.atan2(pdir[1], pdir[0]) + math.pi / 2
        for dz in (0.0, 1.3):
            q = RI[i] + pdir * 0.7
            M.box(CONC, (q[0], q[1], zr_in + 0.9 + dz), (4.2, 0.5, 0.9), hexc("#fff3c4"), rot=ang)
        M.box(CONC, (RI[i][0], RI[i][1], zr_in + 1.2), (0.3, 0.3, 2.4), hexc("#444444"), rot=ang)
# roof-top ring walkway rail omitted. columns under roof edge at the facade (every 8th)
for i in range(0, N, 4):
    t = FA[(i + 1) % N] - FA[i]
    a = np.array(FA[i]) * 0.5 + np.array(RO[i]) * 0.5
    M.box(CONC, (a[0], a[1], (ZTOP + 5) / 2 - 4), (1.0, 1.0, ZTOP + 5 - 1), hexc("#c9ccce")) if False else None

# entrances: portals on the facade
for ph in np.linspace(0.04, 0.96, 11):
    i = int(ph * N) % N; j = (i + 1) % N
    t = FA[j] - FA[i]; ang = math.atan2(t[1], t[0]); nrm = np.array([t[1], -t[0]]) / np.linalg.norm(t)
    mid = (FA[i] + FA[j]) / 2
    z0 = -1.0
    M.box(CONC, (*(mid + nrm * 0.9), z0 + 3.5), (9.0, 1.8, 7.0), hexc("#c4c7c9"), rot=ang, top=hexc("#8d9094"))            # portal frame
    M.box(CONC, (*(mid + nrm * 1.75), z0 + 3.0), (6.2, 0.2, 5.4), hexc("#1c1f24"), rot=ang)                                 # dark doorway
    M.box(CONC, (*(mid + nrm * 1.8), z0 + 6.4), (7.4, 0.3, 0.7), hexc("#e8453c"), rot=ang)                                  # lintel marker
    for st in range(3):
        M.box(CONC, (*(mid + nrm * (2.6 + st * 0.7)), z0 + 0.25 + 0.0 * st), (8.4, 0.7, 0.5 + 0.0), shade(GREY, 0.9), rot=ang)

# video walls at both ends of the long axis, hanging at the roof inner edge
for sgn in (-1, 1):
    th = ALPHA + (0 if sgn > 0 else math.pi)
    i = min(range(N), key=lambda k: abs(math.atan2(math.sin(ths[k] - th), math.cos(ths[k] - th))))
    pdir = np.array(C) - RI[i]; pdir = pdir / np.linalg.norm(pdir); ang = math.atan2(pdir[1], pdir[0]) + math.pi / 2
    q = RI[i] + pdir * 0.3
    M.box(CONC, (q[0], q[1], zr_in - 3.6), (15.0, 0.8, 5.6), hexc("#2a2d32"), rot=ang)
    q2 = RI[i] + pdir * 0.75
    M.box(CONC, (q2[0], q2[1], zr_in - 3.6), (13.6, 0.1, 4.4), hexc("#3d6fa8"), rot=ang)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
M.write(OUT)
print("tris", M.tris(), [(m.name, len(m.idx) // 3) for m in M.mats])
json.dump({"name": "Stadion Letzigrund", "x": round(C[0], 1), "y": round(C[1], 1), "z": round(ZP, 2)}, open(os.path.dirname(OUT) + "/k93_stadion.meta.json", "w"))
