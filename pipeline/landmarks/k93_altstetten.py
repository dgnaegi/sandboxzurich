"""Bahnhof Altstetten: Sichtbeton-Hochhaus 1966, Flachbau mit Vordach, Luginbuehl «IBM-Stengel».
-> web/public/models/landmarks/k93_altstetten.glb (+ hide points in overrides/landmarks_k93.json via k93_all.py)"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, terrain, k93_kit as K, sources
from k93_lib import hexc, shade
OUT = F.ROOT + "/web/public/models/landmarks/k93_altstetten.glb"
O = (-2082.0, 738.0)
H = terrain.heights((-2200, 650, -2000, 850), 2.0, z_shift=-3.06)
ZG = float(H.at(*O)) 

def wall_tex(spandrel=(190, 188, 182), glass=(52, 62, 74), band=0.38):
    im = Image.new("RGB", (64, 64), spandrel); d = ImageDraw.Draw(im)
    top = int(64 * band)
    d.rectangle([0, 0, 63, 63], fill=spandrel)
    d.rectangle([3, top, 60, 58], fill=glass); d.line([31, top, 31, 58], fill=(150, 150, 146), width=2)
    for y in range(0, 64, 9): d.line([0, y + 5, 63, y + 5], fill=tuple(int(c * .93) for c in spandrel))  # board marks
    return im

M = L.Model(origin=(O[0], O[1], 0.0))
RB, RE = K.tile(8, 4, 48, 64, K.ribbon(wall="#dadcd6", glass="#3c7b7a", mull="#eceee9", band=0.7, y0=0.14, sky=0.55, slab="#e4e5e0"), seed=31, lit=0.28)   # teal ribbon glass, slim white spandrels (photos #24, lm3)
UW = M.mat("ribbon", rough=0.5, tex=RB, emis=RE, repeat=True)
SB, SE = K.tile(4, 1, 96, 104, K.window(wall="#86847f", frame="#2f3335", glass="#566b78", fw=0.9, fh=0.72, top=0.12, cols=3, rows=1, sill="#6c6a66", noise=4, lit_col=(255, 224, 160)), seed=32, lit=0.7)
SH = M.mat("shop", rough=0.8, tex=SB, emis=SE, repeat=True)
C = M.mat("solid", rough=0.9)
WHITE = (255, 255, 255, 255)
def rect(c1, c2, c3, c4): return [c1, c2, c3, c4]
hh = [(-2114.0, 740.2), (-2107.5, 757.2), (-2051.2, 735.6), (-2057.6, 718.7)]
ang = math.atan2(hh[3][1] - hh[0][1], hh[3][0] - hh[0][0])
ZT = 30.0; ZF = 4.2; FLOOR = 2.9
from shapely.geometry import Polygon as _P
hp = _P(hh); inner = list(hp.buffer(-0.5, join_style=2).exterior.coords)[:-1]
CONCR = hexc("#b7b6b0"); CONCD = hexc("#9d9c96")
# ground floor: shop fronts (recessed) + slab
K.wall_band(M, SH, list(hp.buffer(-1.0, join_style=2).exterior.coords)[:-1], -3, ZF, 3.6, ZF + 3, nx=4, ny=1)
nfl = int((ZT - ZF) / FLOOR + 0.5); FL = (ZT - ZF) / nfl
K.wall_band(M, UW, inner, ZF, ZT, 1.8, FL, nx=8, ny=4)           # recessed window bands
for k in range(nfl + 1):                                              # projecting off-form concrete slabs
    zz = ZF + k * FL - 0.3
    M.prism(C, hh, zz, zz + (0.45 if k in (0, nfl) else 0.2), shade(hexc('#dcdcd6'), 1.0 if k % 2 else 0.96), topcol=shade(CONCR, 0.9), tile=(6.0, 1.0))
M.cap(C, hh, ZT + 0.5, hexc("#8f8f8b"))
cx = np.mean([p[0] for p in hh]); cy = np.mean([p[1] for p in hh])
ux, uy = math.cos(ang), math.sin(ang); nx_, ny_ = -uy, ux
# vertical concrete fins on both long faces (every second bay) and slit-window end cores
Lh = math.hypot(hh[3][0] - hh[0][0], hh[3][1] - hh[0][1]); Wh = math.hypot(hh[1][0] - hh[0][0], hh[1][1] - hh[0][1])
# (long faces: glass ribbons with slim slab edges, no fins)
for sgn in (-1, 1):  # stair/lift cores at the ends
    px = cx + ux * sgn * (Lh / 2 + 1.0); py = cy + uy * sgn * (Lh / 2 + 1.0)
    M.box(C, (px, py, (ZT + 3) / 2 + 0.0), (3.2, Wh * 0.45, ZT + 3 + 3.0), CONCD, rot=ang)
    for k in range(7):
        M.box(C, (px + ux * sgn * 1.62, py + uy * sgn * 1.62, 4.2 + k * 3.6), (0.1, 0.5, 1.8), hexc("#2d3640"), rot=ang)
# roof: parapet, plant rooms, antenna mast
M.prism(C, hh, ZT + 0.5, ZT + 1.3, CONCR, top=False, tile=(6, 1))
M.box(C, (cx - 12, cy + 2.5, ZT + 2.4), (9, 6, 3.4), hexc("#b4b2ac"), rot=ang)
M.box(C, (cx + 9, cy - 2, ZT + 2.0), (6, 6, 2.6), hexc("#a9a7a1"), rot=ang)
M.box(C, (cx + 9, cy - 2, ZT + 5.6), (0.15, 0.15, 6), hexc("#555555"), rot=ang)
# shop awnings + canopy over the ground floor on both long faces
for sgn, col in ((-1, hexc("#c24a30")), (1, hexc("#d9a22f"))):
    for k in range(-9, 10, 3):
        px = cx + ux * (k + 1.5) * 3.0 + nx_ * sgn * (Wh / 2 + 0.9); py = cy + uy * (k + 1.5) * 3.0 + ny_ * sgn * (Wh / 2 + 0.9)
        M.box(C, (px, py, ZF - 0.4), (8.4, 1.8, 0.12), col if (k // 3) % 2 == 0 else shade(col, 0.8), rot=ang)
# stepped lower wing
wing = [(-2112, 741), (-2108.5, 750.2), (-2090, 743.2), (-2093.5, 734)]
# ground-floor shops of the Hochhaus (arcade)
M.box(C, (cx, cy, 2.0), (59, 19.4, 0.4), hexc("#7d7f80"), rot=ang)
# low hall (Flachbau) with shopfronts and canopy
fb = [(-2174.5, 803.9), (-2167.9, 821.4), (-2038.1, 772.2), (-2044.8, 754.7)]
K.wall_band(M, SH, fb, -2.5, 4.9, 3.6, 7.4, nx=4, ny=1)
M.cap(C, fb, 4.9, hexc("#7e7f7c"))
fa = math.atan2(fb[3][1] - fb[0][1], fb[3][0] - fb[0][0])
nrm = np.array([math.sin(fa), -math.cos(fa)])  # points to the south-east side of the hall
fm = np.array([np.mean([p[0] for p in fb]), np.mean([p[1] for p in fb])])
cn = fm + nrm * (9 + 2.2) if np.dot(nrm, np.array(O) - fm) > 0 else fm - nrm * (9 + 2.2)
M.box(C, (cn[0], cn[1], 3.9), (126, 4.4, 0.35), hexc("#6f7172"), rot=fa)
for k in range(-6, 7, 2):
    p_ = cn + np.array([math.cos(fa), math.sin(fa)]) * k * 9.5 + (cn - fm) / np.linalg.norm(cn - fm) * 1.8
    M.box(C, (p_[0], p_[1], 1.9), (0.5, 0.5, 3.9), hexc("#a8a8a4"), rot=fa)
# benches along the arcade
for k in range(-5, 6, 2):
    p_ = cn + np.array([math.cos(fa), math.sin(fa)]) * k * 10.5 - (cn - fm) / np.linalg.norm(cn - fm) * 0.4
    M.box(C, (p_[0], p_[1], 0.5), (4.0, 0.5, 0.12), hexc("#6b4a2e"), rot=fa)
CAN = M.mat("canopy", rough=0.4)
# signs on the Flachbau canopy: station name (white on red) and a pharmacy name (white on green) as plain lettering
def sign_img(text, bg, fg="#ffffff", w=640, h=96):
    im = Image.new("RGB", (w, h), K.rgb(bg)); d = ImageDraw.Draw(im); f = K.font("Barlow-Bold", int(h * 0.62)); tw = f.getlength(text)
    d.rectangle([2, 2, w - 3, h - 3], outline=K.mix(K.rgb(bg), (255, 255, 255), 0.5), width=2); d.text(((w - tw) / 2, h * 0.14), text, font=f, fill=K.rgb(fg)); return im
SG1 = M.mat("sign_station", rough=0.5, tex=sign_img("Zürich Altstetten", "#c8372d"), emis=sign_img("Zürich Altstetten", "#c8372d").point(lambda v: int(v * 0.5)), repeat=False)
SG2 = M.mat("sign_shop", rough=0.5, tex=sign_img("AMAVITA", "#10a06a", w=420), emis=sign_img("AMAVITA", "#10a06a", w=420).point(lambda v: int(v * 0.55)), repeat=False)
sdir = (cn - fm) / np.linalg.norm(cn - fm)              # from the hall to the canopy edge (arcade side)
tfa = np.array([math.cos(fa), math.sin(fa)]); nfa = np.array([-tfa[1], tfa[0]])
if np.dot(nfa, sdir) < 0: nfa = -nfa                     # outward normal towards the arcade
def sign_quad(mat, centre, w_, h_, z_):
    d_ = np.array([-nfa[1], nfa[0]])                      # a->b with outward normal nfa
    K.quad_tex(M, mat, centre - d_ * w_ / 2, centre + d_ * w_ / 2, z_, z_ + h_)
sign_quad(SG1, cn + sdir * 2.3 + tfa * 8.0, 6.4, 0.96, 3.95)
sign_quad(SG2, cn + sdir * 2.3 - tfa * 22.0, 4.2, 0.96, 3.95)
# platform / stair canopies: every OSM building=roof way within 130 m as a flat roof on posts
nodes_, els_ = sources.osm()
for e in els_:
    t_ = e.get("tags", {})
    if e["type"] != "way" or t_.get("building") != "roof" or "nodes" not in e: continue
    q_ = [nodes_[n] for n in e["nodes"] if n in nodes_]
    if len(q_) < 4: continue
    g_ = _P(q_).buffer(0)
    if g_.geom_type != "Polygon" or math.hypot(g_.centroid.x - O[0], g_.centroid.y - O[1]) > 130: continue
    pts_ = list(g_.exterior.coords)[:-1]; zc_ = float(H.at(*g_.centroid.coords[0])) - ZG
    zr_ = zc_ + (3.3 if t_.get("layer") != "1" else 3.6)
    M.prism(CAN, pts_, zr_, zr_ + 0.22, hexc("#aab6b4"), topcol=hexc("#8b9795"), top=True, tile=(2.0, 1.0))
    for p2 in pts_[:: max(1, len(pts_) // 4)]:
        M.box(C, (p2[0], p2[1], zc_ + 1.65), (0.2, 0.2, zr_ - zc_), hexc("#6e7377"))
# platform signs under the canopies ("3 | Zürich Altstetten | 4", black with yellow numerals) + yellow emergency lamps
def plat_sign():
    im = Image.new("RGB", (640, 128), (22, 24, 26)); d = ImageDraw.Draw(im); f = K.font("Barlow-Bold", 96); f2 = K.font("Barlow-Bold", 54)
    d.text((22, 12), "3", font=f, fill=(255, 205, 40)); d.text((560, 12), "4", font=f, fill=(255, 205, 40))
    t = "Zürich Altstetten"; d.text(((640 - f2.getlength(t)) / 2, 32), t, font=f2, fill=(244, 244, 238)); d.rectangle([2, 2, 637, 125], outline=(90, 92, 94), width=2)
    return im
PS_ = plat_sign(); PSG = M.mat("sign_platform", rough=0.5, tex=PS_, emis=PS_.point(lambda v: int(v * 0.5)), repeat=False)
for e in els_:
    t_ = e.get("tags", {})
    if e["type"] != "way" or t_.get("building") != "roof" or "nodes" not in e: continue
    q_ = [nodes_[n] for n in e["nodes"] if n in nodes_]
    if len(q_) < 4: continue
    g_ = _P(q_).buffer(0)
    if g_.geom_type != "Polygon" or math.hypot(g_.centroid.x - O[0], g_.centroid.y - O[1]) > 130 or g_.area < 120: continue
    rc_ = list(g_.minimum_rotated_rectangle.exterior.coords)[:4]
    e0_, e1_ = np.array(rc_[1]) - np.array(rc_[0]), np.array(rc_[2]) - np.array(rc_[1])
    T_ = e0_ if np.linalg.norm(e0_) >= np.linalg.norm(e1_) else e1_; Ln_ = np.linalg.norm(T_); T_ = T_ / Ln_
    N_ = np.array([-T_[1], T_[0]]); Wd_ = min(np.linalg.norm(e0_), np.linalg.norm(e1_))
    if Ln_ < 20: continue
    zc_ = float(H.at(*g_.centroid.coords[0])) - ZG; zr_ = zc_ + (3.3 if t_.get("layer") != "1" else 3.6)
    cen_ = np.array(g_.centroid.coords[0])
    for off_ in ([0.0] if Ln_ < 55 else [-Ln_ / 3, Ln_ / 3]):
        p_ = cen_ + T_ * off_
        for sd in (1, -1):
            out_ = T_ * sd; d_ = np.array([-out_[1], out_[0]])
            K.quad_tex(M, PSG, p_ + out_ * 0.05 - d_ * 1.2, p_ + out_ * 0.05 + d_ * 1.2, zr_ - 1.0, zr_ - 0.52)
        M.box(C, (p_[0] + N_[0] * 1.15, p_[1] + N_[1] * 1.15, zr_ - 0.5), (0.05, 0.05, 0.5), hexc("#3a3d3f"))
        M.box(C, (p_[0] - N_[0] * 1.15, p_[1] - N_[1] * 1.15, zr_ - 0.5), (0.05, 0.05, 0.5), hexc("#3a3d3f"))
        M.box(C, (p_[0] + T_[0] * 0.3 + N_[0] * Wd_ * 0.3, p_[1] + T_[1] * 0.3 + N_[1] * Wd_ * 0.3, zr_ - 0.12), (0.22, 0.22, 0.12), hexc("#ffc21a"))
# platform clock on a post in front of the arcade (two faces)
import k93_kirchen as KK
_ck = KK.round_clock(); CKM = M.mat("clock", rough=0.5, tex=_ck, emis=_ck.point(lambda v: int(v * 0.55)), repeat=False)
pc_ = cn + sdir * 1.0 + tfa * 14.0
M.box(C, (pc_[0], pc_[1], 1.7), (0.14, 0.14, 3.4), hexc("#4a4d50"))
for sd in (1, -1):
    out = tfa * sd; d_ = np.array([-out[1], out[0]])
    K.quad_tex(M, CKM, pc_ + out * 0.12 - d_ * 0.55, pc_ + out * 0.12 + d_ * 0.55, 3.4, 4.5)
# Luginbuehl «IBM-Stengel»: rust-red welded steel sculpture on a round base plate
sx, sy = -2133.2, 755.6
RED = hexc("#8a3523"); RED2 = hexc("#74291a")
M.cyl(C, (sx, sy), 2.2, 0, 0.18, hexc("#8d8c88"), n=18)
M.box(C, (sx, sy, 0.3), (2.6, 1.6, 0.25), RED2, rot=0.4)
for a_ in (0.3, 1.9, 3.5, 5.1):
    K.tube(M, C, (sx + 1.1 * math.cos(a_), sy + 1.1 * math.sin(a_), 0.25), (sx + 0.25 * math.cos(a_ + 0.6), sy + 0.25 * math.sin(a_ + 0.6), 3.4), 0.11, RED, n=6)
for dx_, dy_, h_, w_ in ((-0.55, 0.1, 6.2, 0.45), (0.5, -0.15, 5.4, 0.4), (0.0, 0.5, 4.2, 0.35)):
    M.box(C, (sx + dx_, sy + dy_, h_ / 2 + 0.2), (w_, 0.32, h_), RED, rot=0.25)
for z, a_, l_ in ((1.8, 0.4, 3.4), (3.4, 2.1, 2.8), (4.9, 1.1, 3.6), (5.7, 3.5, 2.4), (2.6, 5.2, 2.6)):
    M.box(C, (sx + math.cos(a_) * l_ * .2, sy + math.sin(a_) * l_ * .2, z), (l_, 0.3, 0.3), RED2, rot=a_)
K.sphere(M, C, (sx + 0.3, sy - 0.2), 0.62, RED, z=1.1)
K.sphere(M, C, (sx - 0.3, sy + 0.4), 0.38, RED2, z=5.9)
M.cyl(C, (sx, sy), 0.9, 2.5, 2.8, RED, n=12); M.cyl(C, (sx, sy), 0.6, 4.9, 5.1, RED2, n=10)
os.makedirs(os.path.dirname(OUT), exist_ok=True); M.write(OUT)
print("tris", M.tris(), "origin", O, round(ZG, 2))
