"""Bahnhof Altstetten: Sichtbeton-Hochhaus 1966, Flachbau mit Vordach, Luginbuehl «IBM-Stengel».
-> web/public/models/landmarks/k93_altstetten.glb (+ hide points in overrides/landmarks_k93.json via k93_all.py)"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, terrain
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
W = M.mat("walls", rough=0.95, tex=wall_tex(), repeat=True)
SH = M.mat("shop", rough=0.8, tex=wall_tex((120, 118, 114), (70, 90, 104), 0.12), repeat=True)
C = M.mat("solid", rough=0.9)
WHITE = (255, 255, 255, 255)
def rect(c1, c2, c3, c4): return [c1, c2, c3, c4]
hh = [(-2114.0, 740.2), (-2107.5, 757.2), (-2051.2, 735.6), (-2057.6, 718.7)]
ang = math.atan2(hh[3][1] - hh[0][1], hh[3][0] - hh[0][0])
ZT = 30.0; ZF = 4.2; FLOOR = 2.9
from shapely.geometry import Polygon as _P
hp = _P(hh); inner = list(hp.buffer(-0.5, join_style=2).exterior.coords)[:-1]
UW = M.mat("glasswall", rough=0.5, tex=wall_tex((150, 148, 142), (44, 58, 76), 0.1), repeat=True)
CONCR = hexc("#b7b6b0"); CONCD = hexc("#9d9c96")
# ground floor: shop fronts (recessed) + slab
M.prism(SH, list(hp.buffer(-1.0, join_style=2).exterior.coords)[:-1], -3, ZF, WHITE, tile=(3.0, ZF + 3), top=False)
nfl = int((ZT - ZF) / FLOOR + 0.5); FL = (ZT - ZF) / nfl
M.prism(UW, inner, ZF, ZT, WHITE, tile=(3.0, FL), top=False)           # recessed window bands
for k in range(nfl + 1):                                              # projecting off-form concrete slabs
    zz = ZF + k * FL - 0.3
    M.prism(C, hh, zz, zz + (0.75 if k in (0, nfl) else 0.55), shade(CONCR, 1.0 if k % 2 else 0.94), topcol=shade(CONCR, 0.85), tile=(6.0, 1.0))
M.cap(C, hh, ZT + 0.5, hexc("#8f8f8b"))
cx = np.mean([p[0] for p in hh]); cy = np.mean([p[1] for p in hh])
ux, uy = math.cos(ang), math.sin(ang); nx_, ny_ = -uy, ux
# vertical concrete fins on both long faces (every second bay) and slit-window end cores
Lh = math.hypot(hh[3][0] - hh[0][0], hh[3][1] - hh[0][1]); Wh = math.hypot(hh[1][0] - hh[0][0], hh[1][1] - hh[0][1])
for sgn in (-1, 1):
    for k in range(-9, 10):
        px = cx + ux * k * 3.0 + nx_ * sgn * (Wh / 2 + 0.05); py = cy + uy * k * 3.0 + ny_ * sgn * (Wh / 2 + 0.05)
        M.box(C, (px, py, (ZF + ZT) / 2), (0.35, 0.6, ZT - ZF), shade(CONCR, 0.96), rot=ang)
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
M.prism(SH, fb, -2.5, 4.9, WHITE, tile=(3.0, 3.0), top=False)
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
# Luginbuehl «IBM-Stengel»: red lacquered steel sculpture (~6.5 m)
sx, sy = -2133.2, 755.6
RED = hexc("#c9261c")
M.cyl(C, (sx, sy), 0.28, 0, 6.6, RED, n=8)
for z, a_, l_ in ((1.8, 0.4, 3.2), (3.4, 2.1, 2.6), (4.9, 1.1, 3.6), (5.9, 3.5, 2.2)):
    M.box(C, (sx + math.cos(a_) * l_ * .25, sy + math.sin(a_) * l_ * .25, z), (l_, 0.35, 0.35), RED, rot=a_)
M.cyl(C, (sx, sy), 1.1, 2.6, 2.9, RED, n=14)
M.cyl(C, (sx, sy), 0.7, 5.2, 5.4, RED, n=10)
M.box(C, (sx + 0.9, sy - 0.6, 6.2), (0.9, 0.9, 0.9), RED, rot=0.6)
M.box(C, (sx, sy, 0.3), (1.6, 1.6, 0.6), hexc("#7b7b78"))
os.makedirs(os.path.dirname(OUT), exist_ok=True); M.write(OUT)
print("tris", M.tris(), "origin", O, round(ZG, 2))
