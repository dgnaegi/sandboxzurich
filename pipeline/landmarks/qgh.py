"""Quartiergarten Hard (Bullingerstrasse 90, Kreis 4/Hard) seen from outside. Layout from SWISSIMAGE (px grid of data/raw/photos/qgh/ortho.jpg, 0.125 m/px, centre
= local (-616,-172)); look from Panoramax/Mapillary street photos (research/quartiergarten_hard.md): Rundholz-Schranke along the street, wire-mesh fence to the
allotments, white lettering board, brown chalet hut (already a swissBUILDINGS3D building, kept), IBC water tanks, pallet composters, pergola shelter, raised beds,
flower/vegetable rows, wild meadow strips. Everything procedural, no photo pixels. Run: .venv/bin/python pipeline/landmarks/qgh.py"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import Polygon, LineString, Point
import common
import lm
from lm import Model, hexc
import qgh_plants as QP
from k4w4_kit import fnt

ROOT = common.ROOT
OVR = ROOT / "pipeline" / "overrides" / "landmarks_qgh.json"
rng = np.random.default_rng(90)


def PX(a, b): return (-616 + (a - 800) * .125, -172 - (b - 800) * .125)


A_, B_, H_ = PX(335, 615), PX(690, 50), PX(740, 962)
ROT = math.atan2(B_[1] - A_[1], B_[0] - A_[0])              # long axis of beds / sheds (~57.6 deg)
EU, EV = (math.cos(ROT), math.sin(ROT)), (math.sin(ROT), -math.cos(ROT))
SN = math.atan2(-(H_[0] - A_[0]), H_[1] - A_[1]) + math.pi  # placeholder, fixed below
_d = (H_[0] - A_[0], H_[1] - A_[1]); _l = math.hypot(*_d); STREET_N = math.atan2(-_d[0] / _l, _d[1] / _l) + math.pi * 0   # normal (-dy... ) towards NE; fixed next line
_nrm = (-_d[1] / _l, _d[0] / _l)
if _nrm[0] * (PX(700, 400)[0] - A_[0]) + _nrm[1] * (PX(700, 400)[1] - A_[1]) < 0: _nrm = (-_nrm[0], -_nrm[1])   # points into the garden
STREET_FACE = math.atan2(-_nrm[1], -_nrm[0])               # facing the street (SW)
GARDEN = Polygon([PX(*p) for p in [(335, 615), (690, 50), (960, 120), (1120, 320), (1030, 420), (900, 640), (830, 830), (740, 962)]])
OX, OY = GARDEN.centroid.x, GARDEN.centroid.y
OZ = common.ground(OX, OY)
G = lambda x, y: common.ground(x, y) - OZ
col = lambda h, a=255: hexc(h, a)
jit = lambda c, a=12: tuple(int(max(0, min(255, v + rng.integers(-a, a + 1)))) for v in c[:3]) + (255,)

# ---------------- textures ----------------
def noise_tex(base, size, amp, seed, blur=0.6):
    r = np.random.default_rng(seed); a = np.array(base, float)[None, None, :] + r.normal(0, amp, (size, size, 1)); a = np.clip(a, 0, 255).astype(np.uint8)
    im = Image.fromarray(a, "RGB").filter(ImageFilter.GaussianBlur(blur)); im._jpeg_q = 78; return im


def tex_wood():
    im = noise_tex((150, 128, 100), 256, 12, 3); d = ImageDraw.Draw(im)
    for y in range(0, 256, 32): d.line([(0, y), (256, y)], fill=(70, 58, 44), width=2)
    for _ in range(90):
        x, y = rng.integers(0, 256), rng.integers(0, 256); d.line([(x, y), (x + rng.integers(10, 60), y)], fill=(120, 100, 78), width=1)
    im._jpeg_q = 78; return im


def tex_metal():
    a = np.zeros((128, 256, 3)); x = np.arange(256)
    a[:] = (np.array([150, 156, 152])[None, None, :] + (np.sin(x / 256 * 2 * math.pi * 16) * 22)[None, :, None]) + rng.normal(0, 5, (128, 256, 3))
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); im._jpeg_q = 78; return im


def tex_gravel():
    im = noise_tex((176, 170, 158), 128, 22, 4, 0.4); im._jpeg_q = 78; return im


def tex_signs():
    im = Image.new("RGB", (1024, 256), (60, 50, 42)); d = ImageDraw.Draw(im)
    d.text((512, 32), "QUARTIERGARTEN", font=fnt("Oswald-Var", 62), fill=(240, 238, 230), anchor="mm")
    for k, (t, c) in enumerate([("Willkommen im Garten\nkein öffentlicher Park\nGäste täglich 8-20 Uhr", (238, 236, 226)), ("Kompost\nnur Gartenabfälle\nkeine Kochresten", (216, 226, 200)), ("Ruhezone\nWildbienen\nbitte nicht betreten", (240, 226, 170))]):
        x0 = k * 341; d.rectangle([x0 + 6, 70, x0 + 335, 250], fill=c, outline=(50, 50, 50), width=3)
        d.multiline_text((x0 + 170, 160), t, font=fnt("Barlow-Bold", 27), fill=(30, 40, 30), anchor="mm", align="center", spacing=6)
    im._jpeg_q = 82; return im


m = Model("qgh"); m.max_mats = 8
mw = m.mat("wood", tex_wood(), rough=0.95); mm = m.mat("metal", tex_metal(), rough=0.7); ms = m.mat("soil", noise_tex((74, 56, 42), 128, 14, 5), rough=1.0)
mg = m.mat("gravel", tex_gravel(), rough=1.0); mf = m.mat("flat", lm.solid((255, 255, 255)), rough=0.8)
mp = m.mat("plants", QP.tex_atlas(), rough=1.0); mp.alpha_mask = True; msn = m.mat("sign", tex_signs(), rough=0.8)
card = lambda x, y, z, w, h, cell, rot=None, c=(255, 255, 255, 255), cross=True: QP.card(m, mp, x, y, z, w, h, rng.uniform(0, 3.14) if rot is None else rot, cell, c, cross)
COLL = []


def L(x, y): return (x - OX, y - OY)


def box(x, y, w, d, z0, z1, rot=ROT, mat=None, c=(255, 255, 255, 255), roof=None, mod=(2.0, 2.0)):
    mat = mat or mw; m.box(mat, x, y, w, d, z0, z1, rot=rot, mod=mod, col=c, mr=roof or mat, rcol=c)


def rect_ring(x, y, w, d, rot, pad=0.2):
    cr, sr = math.cos(rot), math.sin(rot); h = [(-w / 2 - pad, -d / 2 - pad), (w / 2 + pad, -d / 2 - pad), (w / 2 + pad, d / 2 + pad), (-w / 2 - pad, d / 2 + pad)]
    return [[round(x + px * cr - py * sr, 2), round(y + px * sr + py * cr, 2)] for px, py in h]


def decal(mat, x, y, nang, w, z0, z1, c, uv=(0, 0, 1, 1), off=0.03):
    nx, ny = math.cos(nang), math.sin(nang); tx, ty = -ny, nx; cx, cy = x + nx * off, y + ny * off
    m.quad(mat, [(cx - tx * w / 2, cy - ty * w / 2, z0), (cx + tx * w / 2, cy + ty * w / 2, z0), (cx + tx * w / 2, cy + ty * w / 2, z1), (cx - tx * w / 2, cy - ty * w / 2, z1)],
           [(uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3])], col=c, n=(nx, ny, 0))


def ribbon(pts, w, mat, c=(255, 255, 255, 255), dz=0.04, uvs=1.5):
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        dx, dy = x1 - x0, y1 - y0; l = math.hypot(dx, dy)
        if l < 1e-3: continue
        nx, ny = -dy / l * w / 2, dx / l * w / 2; u0, u1 = s / uvs, (s + l) / uvs; s += l
        m.quad(mat, [(x0 - nx, y0 - ny, G(x0 - nx, y0 - ny) + dz), (x1 - nx, y1 - ny, G(x1 - nx, y1 - ny) + dz), (x1 + nx, y1 + ny, G(x1 + nx, y1 + ny) + dz), (x0 + nx, y0 + ny, G(x0 + nx, y0 + ny) + dz)],
               [(u0, 0), (u1, 0), (u1, w / uvs), (u0, w / uvs)], col=c, n=(0, 0, 1))


def post(x, y, h, w=0.1, c=(170, 150, 120, 255)): box(x, y, w, w, G(x, y) - 0.1, G(x, y) + h, rot=0, c=c)


def fence_run(a, b, kind, gaps=()):
    L_ = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L_ / 2.6)); ux, uy = (b[0] - a[0]) / L_, (b[1] - a[1]) / L_; ang = math.atan2(uy, ux)
    for i in range(n + 1):
        f = i / n; x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
        if any(g0 <= f * L_ <= g1 for g0, g1 in gaps): continue
        post(x, y, 1.15 if kind == "log" else 1.7, 0.22 if kind == "log" else 0.08, jit((176, 146, 108)) if kind == "log" else (96, 100, 98, 255))
    for i in range(n):
        f0, f1 = i / n, (i + 1) / n
        if any(g0 <= (f0 + f1) / 2 * L_ <= g1 for g0, g1 in gaps): continue
        x0, y0, x1, y1 = a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0, a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1; xc, yc = (x0 + x1) / 2, (y0 + y1) / 2; g = G(xc, yc); sl = L_ / n
        if kind == "log":
            for z in (0.4, 0.85): box(xc, yc, sl, 0.15, g + z, g + z + 0.14, rot=ang, c=jit((184, 154, 114)))
        else:
            card(xc, yc, g + 0.05, sl + 0.1, 1.6, "mesh", ang, cross=False)
            card(xc, yc, g + 0.05, sl + 0.1, 1.6, "mesh", ang + math.pi, cross=False)


# ---------------- ground: paths, beds ----------------
PATH = [PX(*p) for p in [(350, 615), (480, 640), (600, 632), (690, 610), (775, 560), (830, 490), (880, 420), (960, 395), (1030, 390)]]
BRANCH = [PX(*p) for p in [(600, 843), (618, 790), (640, 745), (645, 700), (630, 650), (600, 632)]]
ribbon(PATH, 1.5, mg); ribbon(BRANCH, 1.7, mg)
for (px_, py_, w_, d_, ang_) in [(740, 780, 4.2, 3.2, 0.5), (880, 235, 5, 4, .3), (820, 690, 3, 2.4, 0), (1160, 380, 6, 5, .2)]:   # sandy/loamy play patches
    x, y = PX(px_, py_); ribbon([(x - w_ / 2 * math.cos(ang_), y - w_ / 2 * math.sin(ang_)), (x + w_ / 2 * math.cos(ang_), y + w_ / 2 * math.sin(ang_))], d_, mg, c=(206, 186, 140, 255), dz=0.03)
PATHZONE = LineString(PATH).buffer(1.6).union(LineString(BRANCH).buffer(1.7))
OBJ = []   # (x, y, radius) keep-outs for bed rows


def strip_bed(x0, y0, x1, y1, w, crop):
    l = math.hypot(x1 - x0, y1 - y0); nx, ny = -(y1 - y0) / l * w / 2, (x1 - x0) / l * w / 2
    m.quad(ms, [(x0 - nx, y0 - ny, G(x0 - nx, y0 - ny) + .05), (x1 - nx, y1 - ny, G(x1 - nx, y1 - ny) + .05), (x1 + nx, y1 + ny, G(x1 + nx, y1 + ny) + .05), (x0 + nx, y0 + ny, G(x0 + nx, y0 + ny) + .05)],
           [(0, 0), (l / 1.5, 0), (l / 1.5, w / 1.5), (0, w / 1.5)], n=(0, 0, 1), col=(190, 190, 190, 255))
    ang = math.atan2(y1 - y0, x1 - x0); step = {"veg": 0.8, "cab": 0.9, "tomato": 1.5, "beans": 1.4, "tall": 1.8, "flow1": 1.2, "flow2": 1.2, "weeds": 1.0}[crop]; hgt = {"veg": .5, "cab": .55, "tomato": 1.7, "beans": 1.9, "tall": 2.2, "flow1": 1.0, "flow2": .9, "weeds": .5}[crop]
    for i in range(int(l / step)):
        f = (i + .5) * step / l; x, y = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        card(x, y, G(x, y) + .02, step * 1.15 + .2, hgt * rng.uniform(.8, 1.15), crop, ang if crop in ("beans", "tomato", "tall") else None, cross=crop not in ("beans", "tomato", "tall"))


def bed_field(poly_px, v0, v1, step, crops, seed):
    reg = Polygon([PX(*p) for p in poly_px]).buffer(-0.8).difference(PATHZONE.buffer(0.7)); k = 0
    for v in np.arange(v0, v1, step):
        o = (A_[0] + EV[0] * v, A_[1] + EV[1] * v); ln = LineString([(o[0] - EU[0] * 20, o[1] - EU[1] * 20), (o[0] + EU[0] * 130, o[1] + EU[1] * 130)]).intersection(reg)
        for g in ([ln] if ln.geom_type == "LineString" else list(getattr(ln, "geoms", []))):
            if g.geom_type != "LineString" or g.length < 3.5: continue
            (xa, ya), (xb, yb) = g.coords[0], g.coords[-1]; strip_bed(xa, ya, xb, yb, 1.25, crops[k % len(crops)]); k += 1


bed_field([(575, 500), (640, 340), (810, 428), (772, 520), (700, 566), (612, 575)], 0, 70, 2.8, ["veg", "cab", "flow1", "veg", "tall", "flow2", "beans", "cab", "tomato"], 1)
bed_field([(812, 272), (945, 350), (928, 388), (802, 318)], 0, 90, 2.4, ["veg", "flow2", "cab"], 2)
bed_field([(700, 140), (780, 120), (800, 240), (720, 255)], 0, 90, 2.9, ["weeds", "flow1"], 3)   # semi-wild flower meadow strips north of the big shed

# raised beds (Hochbeete) and planters near the entrance side of the west plot
def raised(x, y, w, d, rot, crop):
    g = G(x, y); t = .05; hh = .65
    for sx, sy, ww, dd in ((0, d / 2, w, t), (0, -d / 2, w, t), (w / 2, 0, t, d), (-w / 2, 0, t, d)):
        cr, sr = math.cos(rot), math.sin(rot); box(x + sx * cr - sy * sr, y + sx * sr + sy * cr, ww + (t if ww == w else 0), dd, g, g + hh, rot=rot, c=jit((170, 140, 104), 16))
    ring = [(x + ((-1) ** i * w / 2 - 0 * 1) * math.cos(rot) - ((i // 2 * 2 - 1) * d / 2) * math.sin(rot), 0) for i in range(0)]
    cr, sr = math.cos(rot), math.sin(rot); pts = [(x + a * cr - b * sr, y + a * sr + b * cr) for a, b in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
    m.quad(ms, [(px_, py_, g + hh - .06) for px_, py_ in pts], [(0, 0), (w, 0), (w, d), (0, d)], n=(0, 0, 1))
    for i in range(int(w / 0.9)):
        f = (i + .5) / int(w / 0.9) - .5; card(x + f * w * cr, y + f * w * sr, g + hh - .04, 1.0, 0.9 if crop in ("flow1", "flow2") else .6, crop)
    COLL.append(rect_ring(x, y, w, d, rot, 0.05))


RB0 = PX(470, 555)
for r_ in range(2):
    for i in range(4):
        x, y = RB0[0] + EU[0] * (i * 3.7) + EV[0] * (r_ * 2.8), RB0[1] + EU[1] * (i * 3.7) + EV[1] * (r_ * 2.8); raised(x, y, 3.0, 1.2, ROT, ["veg", "flow1", "cab", "flow2", "veg", "tomato", "flow1", "cab"][r_ * 4 + i])

# ---------------- buildings ----------------
def shed(px_, py_, w, d, h, kind):
    x, y = PX(px_, py_); g = G(x, y) - .05; wc = {"S1": (122, 100, 76, 255), "H2": (104, 108, 104, 255), "H3": (150, 98, 70, 255)}.get(kind, (140, 118, 90, 255))
    box(x, y, w, d, g, g + h, rot=ROT, c=jit(wc, 8), roof=mm); box(x, y, w + .5, d + .6, g + h, g + h + .1, rot=ROT, mat=mm, c=(120, 128, 124, 255))
    fa = ROT - math.pi / 2; fx, fy = x + EV[0] * d / 2, y + EV[1] * d / 2
    decal(mf, fx + EU[0] * w * .18, fy + EU[1] * w * .18, fa, min(1.6, w * .3), g, g + h * .85, (46, 40, 36, 255))   # door
    decal(mf, fx - EU[0] * w * .25, fy - EU[1] * w * .25, fa, min(1.1, w * .22), g + h * .45, g + h * .8, (70, 84, 92, 255))   # window
    COLL.append(rect_ring(x, y, w, d, ROT, .1)); OBJ.append((x, y, max(w, d)))
    return x, y, g, fa


x, y, g, fa = shed(710, 285, 8.0, 5.5, 2.6, "S1")
for i in range(4): card(x + EV[0] * 3.4 + EU[0] * (i - 1.5) * 1.8, y + EV[1] * 3.4 + EU[1] * (i - 1.5) * 1.8, g, 1.2, 1.0, "weeds")
box(x + EV[0] * 3.4 + EU[0] * 2.6, y + EV[1] * 3.4 + EU[1] * 2.6, 1.3, 0.6, g + 0.25, g + .55, rot=ROT, mat=mm, c=(60, 110, 70, 255))   # wheelbarrow tub
x, y, g, fa = shed(570, 750, 4.4, 3.0, 2.3, "H2"); x, y, g, fa = shed(905, 625, 2.6, 2.0, 2.2, "H3")
# greenhouse (white/silver long structure)
x, y = PX(556, 308); g = G(x, y); gw, gd = 5.5, 2.6
box(x, y, gw, gd, g, g + 1.9, rot=ROT, mat=mf, c=(214, 226, 224, 255), roof=mf)
for i in range(7):
    f = (i / 6 - .5) * gw; box(x + EU[0] * f, y + EU[1] * f, .08, gd + .02, g, g + 1.95, rot=ROT, mat=mf, c=(240, 240, 238, 255))
COLL.append(rect_ring(x, y, gw, gd, ROT, .1)); OBJ.append((x, y, 5))

# pergola shelter with table, benches and fire ring
x, y = PX(830, 590); g = G(x, y)
for sx in (-3, 3):
    for sy in (-3, 3): post(x + EU[0] * sx + EV[0] * sy, y + EU[1] * sx + EV[1] * sy, 2.5, .16, jit((140, 112, 84)))
box(x, y, 6.6, 6.6, g + 2.5, g + 2.62, rot=ROT, mat=mm, c=(170, 176, 170, 255))
box(x - EU[0] * 1.2 + EV[0] * 1.5, y - EU[1] * 1.2 + EV[1] * 1.5, 2.4, .9, g + .72, g + .8, rot=ROT, c=(170, 146, 112, 255))   # table
for sy in (.6, 2.4): box(x - EU[0] * 1.2 + EV[0] * sy, y - EU[1] * 1.2 + EV[1] * sy, 2.4, .32, g + .4, g + .46, rot=ROT, c=(160, 136, 104, 255))
m.cylinder(mf, x + EU[0] * 1.5 - EV[0] * 1.2, y + EU[1] * 1.5 - EV[1] * 1.2, .6, g, g + .28, n=10, col=(96, 90, 86, 255), cap=ms, capcol=(40, 34, 30, 255))   # fire ring
for a_ in range(5):
    t = a_ * 1.26; m.cylinder(mw, x + EU[0] * 1.5 - EV[0] * 1.2 + math.cos(t) * 1.4, y + EU[1] * 1.5 - EV[1] * 1.2 + math.sin(t) * 1.4, .22, g, g + .4, n=6, col=jit((160, 130, 100)), cap=mw, capcol=(180, 150, 114, 255))
OBJ.append((x, y, 5))

# silver / blue tarps over mulch heaps
for (px_, py_, w_, d_, c_) in [(740, 780, 4.4, 3.6, (186, 190, 192, 255)), (785, 740, 3.0, 2.4, (52, 118, 176, 255))]:
    x, y = PX(px_, py_); g = G(x, y); box(x, y, w_, d_, g, g + .35, rot=ROT + .2, mat=mf, c=c_)
    for k in range(5): card(x + rng.uniform(-w_ / 2, w_ / 2), y + rng.uniform(-d_ / 2, d_ / 2), g + .3, .9, .3, "weeds")


def ibc(x, y, rot=0.0):
    g = G(x, y); box(x, y, 1.2, 1.0, g, g + .14, rot=rot, c=(172, 142, 104, 255)); box(x, y, 1.0, 1.2, g + .14, g + 1.18, rot=rot, mat=mf, c=(214, 224, 228, 255))
    m.cylinder(mf, x, y, .12, g + 1.18, g + 1.26, n=8, col=(40, 70, 130, 255), cap=mf, capcol=(40, 70, 130, 255)); COLL.append(rect_ring(x, y, 1.2, 1.2, rot, .05))


for p_ in [(595, 498), (678, 358), (932, 310), (755, 602), (498, 790)]: ibc(*PX(*p_), rot=rng.uniform(0, 1.5))
for p_ in [(642, 505), (548, 345)]:   # blue rain barrels
    x, y = PX(*p_); g = G(x, y); m.cylinder(mf, x, y, .3, g, g + .9, n=10, col=(40, 90, 160, 255), cap=mf, capcol=(36, 80, 140, 255))


def compost(x, y, rot):
    g = G(x, y); cr, sr = math.cos(rot), math.sin(rot)
    for k in range(3):
        cx = x + (k - 1) * 1.3 * cr; cy = y + (k - 1) * 1.3 * sr
        for sx, sy, ww, dd in ((0, .6, 1.2, .04), (-.6, 0, .04, 1.2), (.6, 0, .04, 1.2)): box(cx + sx * cr - sy * sr, cy + sx * sr + sy * cr, ww, dd, g, g + .9, rot=rot, c=jit((150, 126, 94), 10))
        m.quad(ms, [(cx + a * cr - b * sr, cy + a * sr + b * cr, g + .15 + .2 * (k % 2)) for a, b in ((-.55, -.55), (.55, -.55), (.55, .55), (-.55, .55))], [(0, 0), (1, 0), (1, 1), (0, 1)], n=(0, 0, 1))
    COLL.append(rect_ring(x, y, 3.9, 1.3, rot, .05))


compost(*PX(700, 646), ROT + .2); compost(*PX(865, 735), ROT - .4)


def bench(x, y, rot):
    g = G(x, y); cr, sr = math.cos(rot), math.sin(rot)
    for s in (-.7, .7): m.cylinder(mw, x + s * cr, y + s * sr, .13, g, g + .42, n=6, col=jit((150, 124, 94)), cap=mw, capcol=(170, 140, 108, 255))
    box(x, y, 1.9, .36, g + .42, g + .5, rot=rot, c=(176, 150, 116, 255))
    if rng.random() < .6: box(x - sr * .2, y + cr * .2, 1.9, .06, g + .55, g + .95, rot=rot, c=(160, 136, 104, 255))


for p_, r_ in [((900, 420), 0.5), ((610, 648), ROT), ((985, 385), 1.0), ((530, 640), ROT - .3)]: bench(*PX(*p_), r_)

# pallet sofa / mobile garden furniture near shelter
x, y = PX(870, 600); g = G(x, y); box(x, y, 1.2, .8, g, g + .5, rot=.3, c=(168, 140, 104, 255)); box(x + .2, y + .3, 1.2, .1, g + .5, g + 1.0, rot=.3, c=(168, 140, 104, 255))

# ---------------- rondell + trees ----------------
x, y = PX(910, 445); g = G(x, y)
for a_ in range(14):
    t = a_ / 14 * 6.28; m.cylinder(mf, x + math.cos(t) * 1.7, y + math.sin(t) * 1.7, .2, g, g + .25, n=5, col=jit((150, 146, 138)))
for a_ in range(10): card(x + rng.uniform(-1.4, 1.4), y + rng.uniform(-1.4, 1.4), g + .1, .9, .9, "flow2" if a_ % 2 else "flow1")


def tree(px_, py_, h, w, cell):
    x, y = PX(px_, py_); g = G(x, y); m.cylinder(mw, x, y, .14, g, g + h * .5, n=6, col=(98, 80, 62, 255), cap=mw, capcol=(98, 80, 62, 255)); card(x, y, g + h * .3, w, h * .8, cell)


for p_ in [(400, 705), (570, 690), (745, 170), (790, 95), (860, 215), (1000, 270), (980, 330), (640, 170), (480, 360), (910, 700), (700, 440), (870, 560)]:
    tree(*p_, rng.uniform(3.5, 5.5), rng.uniform(3.6, 5), "crown" if rng.random() < .5 else "crown2")

# ---------------- fences, gate, signs ----------------
GATE = PX(600, 843); print('QGH_GATE', [round(float(v), 1) for v in GATE]); gu = (H_[0] - A_[0], H_[1] - A_[1]); gl = math.hypot(*gu); gu = (gu[0] / gl, gu[1] / gl)
gpos = math.hypot(GATE[0] - A_[0], GATE[1] - A_[1])
SN_ang = math.atan2(*reversed(gu))
fence_run(A_, B_, "mesh")                                  # wire mesh towards the family gardens
fence_run(A_, GATE, "log", gaps=((gpos - 1.5 - 0, gpos),)) if False else None
fence_run(A_, (A_[0] + gu[0] * (gpos - 1.8), A_[1] + gu[1] * (gpos - 1.8)), "log")
fence_run((A_[0] + gu[0] * (gpos + 1.8), A_[1] + gu[1] * (gpos + 1.8)), (A_[0] + gu[0] * (gpos + 14), A_[1] + gu[1] * (gpos + 14)), "mesh")
fence_run((A_[0] + gu[0] * (gpos + 14), A_[1] + gu[1] * (gpos + 14)), H_, "log")
fence_run(PX(1030, 420), PX(900, 640), "mesh"); fence_run(PX(900, 640), PX(830, 830), "log")
for ring_a, ring_b in ((A_, (A_[0] + gu[0] * (gpos - 1.8), A_[1] + gu[1] * (gpos - 1.8))), ((A_[0] + gu[0] * (gpos + 1.8), A_[1] + gu[1] * (gpos + 1.8)), H_)):
    l_ = math.hypot(ring_b[0] - ring_a[0], ring_b[1] - ring_a[1]); n_ = int(l_ / 8) + 1
    for i in range(n_):
        a2 = (ring_a[0] + (ring_b[0] - ring_a[0]) * i / n_, ring_a[1] + (ring_b[1] - ring_a[1]) * i / n_); b2 = (ring_a[0] + (ring_b[0] - ring_a[0]) * (i + 1) / n_, ring_a[1] + (ring_b[1] - ring_a[1]) * (i + 1) / n_)
        cx, cy = (a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2; COLL.append(rect_ring(cx, cy, l_ / n_, .15, SN_ang, 0.05))
for i in range(int(82 / 8)):
    a2 = (A_[0] + (B_[0] - A_[0]) * i / 10.3, A_[1] + (B_[1] - A_[1]) * i / 10.3); b2 = (A_[0] + (B_[0] - A_[0]) * (i + 1) / 10.3, A_[1] + (B_[1] - A_[1]) * (i + 1) / 10.3)
    COLL.append(rect_ring((a2[0] + b2[0]) / 2, (a2[1] + b2[1]) / 2, 8.1, .15, ROT, 0.05))
# gate: two steel/wood leaves, posts and little roof sign
for s in (-1.6, 1.6): post(GATE[0] + gu[0] * s, GATE[1] + gu[1] * s, 1.9, .18, jit((120, 96, 74)))
for s in (-1.4, .1):
    cx, cy = GATE[0] + gu[0] * (s + .65), GATE[1] + gu[1] * (s + .65); box(cx, cy, 1.3, .06, G(cx, cy) + .1, G(cx, cy) + 1.5, rot=SN_ang, c=jit((88, 120, 90)))
box(GATE[0], GATE[1], 3.4, .14, G(*GATE) + 1.9, G(*GATE) + 2.05, rot=SN_ang, c=(150, 124, 94, 255))
decal(msn, GATE[0] + gu[0] * 2.6 + _nrm[0] * -.05, GATE[1] + gu[1] * 2.6 - _nrm[1] * .05, STREET_FACE, 1.0, G(*GATE) + .9, G(*GATE) + 1.55, (255, 255, 255, 255), uv=(0, 0, 341 / 1024, 186 / 256 * 0.72), off=0.12)
# lettering board on the log-rail section next to the chalet
lx0 = gpos - 9.0; lx1 = gpos - 3.0; lc = (A_[0] + gu[0] * (lx0 + lx1) / 2, A_[1] + gu[1] * (lx0 + lx1) / 2); lg = G(*lc)
box(lc[0], lc[1], lx1 - lx0, .05, lg + .65, lg + 1.3, rot=SN_ang, c=(70, 60, 50, 255)); decal(msn, lc[0], lc[1], STREET_FACE, lx1 - lx0, lg + .68, lg + 1.27, (255, 255, 255, 255), uv=(0, 1 - 64 / 256, 1, 1), off=0.05)
# small signs on posts inside
for (k, (px_, py_)) in enumerate([(700, 640), (615, 560)]):
    x, y = PX(px_, py_); g = G(x, y); post(x, y, 1.1, .08); decal(msn, x, y, ROT + 1.2, .7, g + .7, g + 1.15, (255, 255, 255, 255), uv=((k + 1) * 341 / 1024, 0, (k + 2) * 341 / 1024, 186 / 256 * .74 * 1), off=0.06)

# ---------------- hedges, wild shrubs, climbers, meadow ----------------
def chain(pts, step, hmin, hmax, cells):
    for a, b in zip(pts[:-1], pts[1:]):
        L_ = math.hypot(b[0] - a[0], b[1] - a[1])
        for i in range(int(L_ / step)):
            f = (i + rng.random() * .6) * step / L_; x, y = a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f; h = rng.uniform(hmin, hmax)
            card(x, y, G(x, y) - .05, h * 1.3, h, cells[int(rng.integers(0, len(cells)))])


chain([PX(*p) for p in [(690, 50), (820, 20), (960, 120), (1120, 320)]], 2.3, 1.6, 3.0, ["shrub", "bush2", "crown2"])
chain([PX(*p) for p in [(1120, 320), (1030, 420), (900, 640), (830, 830)]], 2.8, 1.2, 2.2, ["shrub", "bush2"])
chain([PX(*p) for p in [(940, 280), (1000, 340), (960, 300)]], 1.8, 1.8, 3.2, ["bush2", "shrub", "reed"])   # wild thicket NE
for i in range(int(82 / 2.2)):   # climbers on the mesh fence + hedge strip behind it
    f = (i + rng.random()) * 2.2; x, y = A_[0] + EU[0] * f + EV[0] * .35, A_[1] + EU[1] * f + EV[1] * .35
    card(x, y, G(x, y), 2.2, 1.7, "ivy" if i % 2 else "beans", ROT, cross=False)
    if i % 3 == 0: card(x + EV[0] * .9, y + EV[1] * .9, G(x, y), 1.8, 1.2, "weeds")
for k in range(120):   # meadow tufts / reed on non-bed ground
    x, y = rng.uniform(GARDEN.bounds[0], GARDEN.bounds[2]), rng.uniform(GARDEN.bounds[1], GARDEN.bounds[3])
    if not GARDEN.buffer(-1.5).contains(Point(x, y)) or PATHZONE.contains(Point(x, y)) or any(math.hypot(x - ox_, y - oy_) < r_ for ox_, oy_, r_ in OBJ): continue
    card(x, y, G(x, y) - .05, rng.uniform(1.0, 1.8), rng.uniform(.5, 1.3), ["grass", "weeds", "reed", "flow1"][int(rng.integers(0, 4))])
for k in range(18):   # street-side wild strip in front of the log rail
    f = rng.uniform(2, gl - 2); x, y = A_[0] + gu[0] * f - _nrm[0] * 1.0, A_[1] + gu[1] * f - _nrm[1] * 1.0
    card(x, y, G(x, y), 1.4, rng.uniform(.6, 1.2), ["weeds", "grass", "flow2"][k % 3])
# brown timber chalet (swissBUILDINGS3D id ID_8D055786 is hidden and redrawn: dark wood, gabled, solar panel on the roof)
CH = common.bid("ID_8D055786"); rr = CH["fp"].minimum_rotated_rectangle; rc = list(rr.exterior.coords)[:4]
e1 = (rc[1][0] - rc[0][0], rc[1][1] - rc[0][1]); e2 = (rc[2][0] - rc[1][0], rc[2][1] - rc[1][1])
if math.hypot(*e1) < math.hypot(*e2): e1, e2 = e2, e1
cw, cd = math.hypot(*e1), math.hypot(*e2); crot = math.atan2(e1[1], e1[0]); ccx, ccy = rr.centroid.x, rr.centroid.y; cg = G(ccx, ccy) - .1
CH_HIDE = [round(CH["fp"].representative_point().x, 1), round(CH["fp"].representative_point().y, 1)]
wall_c, roof_c = (98, 70, 50, 255), (84, 62, 52, 255); eh, rise = 2.5, 1.35
box(ccx, ccy, cw, cd, cg, cg + eh, rot=crot, c=jit(wall_c, 6), roof=mw)
cr_, sr_ = math.cos(crot), math.sin(crot)
P3 = lambda u, v, z: (ccx + u * cr_ - v * sr_, ccy + u * sr_ + v * cr_, cg + z)
ov = .45
for sgn in (1, -1):   # two roof planes along the long axis
    q = [P3(-cw / 2 - ov, sgn * (cd / 2 + ov), eh - .15), P3(cw / 2 + ov, sgn * (cd / 2 + ov), eh - .15), P3(cw / 2 + ov, 0, eh + rise), P3(-cw / 2 - ov, 0, eh + rise)]
    m.quad(mm, q if sgn > 0 else q[::-1], [(0, 0), (cw / 2, 0), (cw / 2, 1.2), (0, 1.2)], col=roof_c)
    m.quad(mm, [q[0], q[3], q[2], q[1]] if sgn > 0 else [q[0], q[3], q[2], q[1]][::-1], [(0, 0), (1, 0), (1, 1), (0, 1)], col=roof_c)   # underside
for sgn in (1, -1):   # gable ends
    m.tri(mw, [P3(sgn * cw / 2, -cd / 2, eh), P3(sgn * cw / 2, cd / 2, eh), P3(sgn * cw / 2, 0, eh + rise - .1)] if sgn > 0 else [P3(sgn * cw / 2, cd / 2, eh), P3(sgn * cw / 2, -cd / 2, eh), P3(sgn * cw / 2, 0, eh + rise - .1)], col=jit(wall_c, 6))
m.quad(mf, [P3(-cw * .3, cd / 2 + ov * .55, eh + .12), P3(cw * .3, cd / 2 + ov * .55, eh + .12), P3(cw * .3, cd / 2 * .15 + .05, eh + rise * .8), P3(-cw * .3, cd / 2 * .15 + .05, eh + rise * .8)], col=(32, 40, 58, 255))   # solar panel
for u in (-1.2, 1.1): decal(mf, ccx + (cd / 2) * -sr_ * 0 + u * cr_ - cd / 2 * (-sr_), ccy + u * sr_ + cd / 2 * cr_, crot + math.pi / 2, .9, cg + 1.0, cg + 1.9, (200, 205, 196, 255))
decal(mf, ccx - cw / 2 * cr_ * 0 + 0.0 * cr_ + (cd / 2) * -sr_ + .0, ccy + (cd / 2) * cr_, crot + math.pi / 2, .95, cg, cg + 2.0, (62, 42, 30, 255), off=.04)
COLL.append(rect_ring(ccx, ccy, cw, cd, crot, .1))
for k in range(5): card(ccx + rng.uniform(-cw / 2 - 1, cw / 2 + 1), ccy + rng.uniform(-cd / 2 - 1.2, cd / 2 + 1.2), cg, 1.2, rng.uniform(.8, 1.5), ["flow1", "weeds", "flow2"][k % 3])
for k in range(3): card(ccx + (cd / 2 + .3) * -sr_ + (k - 1) * 1.4 * cr_, ccy + (cd / 2 + .3) * cr_ + (k - 1) * 1.4 * sr_, cg, 1.8, 2.0, "ivy", crot, cross=False)


# self-built elements: insect hotel + wild-bee rest zone sign, rose arch over the gate, bean teepees, scarecrow, hose reel, watering cans
x, y = PX(1000, 335); g = G(x, y)
for sx in (-.55, .55): post(x + EU[0] * sx, y + EU[1] * sx, 1.7, .1)
box(x, y, 1.4, .45, g + .5, g + 1.65, rot=ROT, c=(150, 120, 88, 255))
for r_ in range(4):
    for c_ in range(5):
        cx_, cy_ = x + EU[0] * (c_ - 2) * .26 + EV[0] * .23, y + EU[1] * (c_ - 2) * .26 + EV[1] * .23
        box(cx_, cy_, .22, .03, g + .6 + r_ * .25, g + .78 + r_ * .25, rot=ROT, mat=mf, c=[(60, 44, 32, 255), (176, 150, 96, 255), (110, 80, 56, 255), (200, 190, 150, 255)][(r_ + c_) % 4])
box(x, y, 1.7, .6, g + 1.65, g + 1.75, rot=ROT, mat=mm, c=(110, 70, 56, 255))
decal(msn, x + EV[0] * .6, y + EV[1] * .6, ROT - math.pi / 2, .8, g + .1, g + .62, (255, 255, 255, 255), uv=(2 * 341 / 1024, 0, 3 * 341 / 1024, 186 / 256 * .74), off=.05)
for sx in (-1.55, 1.55): post(GATE[0] + gu[0] * sx, GATE[1] + gu[1] * sx, 2.6, .12, jit((150, 120, 90)))
for k in range(7):   # rose arch over the gate
    t = k / 6; px_ = GATE[0] + gu[0] * (-1.55 + 3.1 * t); py_ = GATE[1] + gu[1] * (-1.55 + 3.1 * t); box(px_, py_, .09, .09, G(*GATE) + 2.55 + math.sin(t * math.pi) * .4, G(*GATE) + 2.64 + math.sin(t * math.pi) * .4, rot=0, c=(140, 110, 80, 255))
card(GATE[0] - gu[0] * 1.55, GATE[1] - gu[1] * 1.55, G(*GATE), 1.3, 2.7, "ivy", SN_ang, cross=True); card(GATE[0] + gu[0] * 1.55, GATE[1] + gu[1] * 1.55, G(*GATE), 1.3, 2.7, "ivy", SN_ang, cross=True)
for p_ in [(590, 565), (790, 450), (900, 340), (520, 440)]:   # bean teepees
    x, y = PX(*p_); g = G(x, y)
    for k in range(6):
        t = k / 6 * 6.28; box(x + math.cos(t) * .55, y + math.sin(t) * .55, .05, .05, g, g + 2.0, rot=0, c=(150, 120, 86, 255))
    card(x, y, g, 1.5, 2.1, "beans"); card(x, y, g, 1.5, 2.1, "tall", 1.0)
x, y = PX(730, 480); g = G(x, y); post(x, y, 1.8, .06); box(x, y, 1.3, .04, g + 1.4, g + 1.44, rot=ROT, c=(150, 120, 86, 255)); box(x, y, .45, .25, g + .8, g + 1.4, rot=ROT, mat=mf, c=(98, 112, 140, 255)); m.cylinder(mf, x, y, .16, g + 1.5, g + 1.78, n=8, col=(215, 190, 140, 255), cap=mf, capcol=(215, 190, 140, 255)); box(x, y, .7, .45, g + 1.78, g + 1.84, rot=ROT, mat=mw, c=(200, 170, 80, 255))
x, y = PX(615, 445); g = G(x, y); m.cylinder(mf, x, y, .3, g, g + .12, n=10, col=(60, 100, 60, 255), cap=mf, capcol=(60, 100, 60, 255))   # hose reel
for p_ in [(722, 310), (688, 258)]: x, y = PX(*p_); m.cylinder(mf, x, y, .1, G(x, y), G(x, y) + .28, n=8, col=(60, 130, 170, 255), cap=mf, capcol=(60, 130, 170, 255))


# ---------------- write ----------------
def main():
    out = ROOT / "web" / "public" / "models" / "landmarks"; raw = ROOT / "data" / "build" / "landmarks"; raw.mkdir(parents=True, exist_ok=True)
    # localise: the model is built in local-world metres; shift to the anchor
    for mt in m.mats.values():
        for p in mt.pos: p[0] -= OX; p[1] -= OY
    m.write(str(raw / "qgh.glb"))
    import subprocess
    r = subprocess.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw / "qgh.glb"), "-o", str(out / "qgh.glb"), "-cc", "-kn"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:])
    print("qgh:", m.tri_count(), "tris", {k: v.tris() for k, v in m.mats.items()}, (out / "qgh.glb").stat().st_size // 1024, "kB", "colliders", len(COLL))
    OVR.write_text(json.dumps({"landmarks": [{"name": "Quartiergarten Hard (Aussenansicht)", "model": "/models/landmarks/qgh.glb", "x": round(OX, 2), "y": round(OY, 2), "z": round(OZ, 2), "heading": 0, "hide": [CH_HIDE], "colliders": COLL}]}, indent=1))
    import merge; merge.main()


main()
