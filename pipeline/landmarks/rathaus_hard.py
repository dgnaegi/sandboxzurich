"""Rathaus Hard = former Bullingerkirche (Bullingerstrasse 4): church volume. research/rathaus_hard/notes.md.
Front (longest edge, facing the forecourt to the south): windowless cream gable wall, 6 white pilasters = 5 fields,
open porch in the 3 central fields (dark recess + stair), perforated brick-screen panels in the 2 outer fields,
wide-eaved shallow hip roof; sides: tall narrow glass bands. Forecourt lion = Mickry 3 'Betonlöwin' fragments (FRAGMENTS)."""
import math
import numpy as np
from PIL import Image
from shapely.geometry import Polygon
from lm import *
import detail as D

# Betonlöwin (Mickry 3, 2023, Kunst am Bau): one lioness cast in grey concrete, scattered as blocky fragments on the forecourt
# (creabeton.ch: head 90x100x60, paw 100x60x60, body incl. tail 180x60x80 cm; photos Gion Pfander in data/raw/photos/rathaus_hard/).
# Entry = (kind, u_along_front_m (viewer's right), d_out_m, yaw_deg). Empty list = no lion. Layout approximated from the photos.
FRAGMENTS = [("head", 7.0, 8.6, 25), ("body", 11.2, 9.4, 4), ("paw", 4.4, 5.6, 8), ("paw", 8.6, 5.2, -12),
             ("paw", 12.6, 5.9, 172), ("paw", 15.2, 8.0, 100)]
COURT = (12.0, 1.0)   # forecourt cobble patch: depth out from the front (m), side margin (m)
PL = 1.0              # plinth top above model origin
EAVE = 12.5


def cobble_tex(size=64):
    rng = np.random.default_rng(4); a = np.zeros((size, size, 4), np.uint8); a[..., 3] = 255; a[..., :3] = (74, 72, 70)
    for r in range(0, size, 8):
        for c in range(0, size, 8):
            v = int(rng.integers(92, 128)); a[r + 1:r + 7, c + 1:c + 7, :3] = (v, v - 2, v - 5)
    return Image.fromarray(a, "RGBA")


def screen_tex(size=64):
    """Perforated brick screen (photo cm_Bullingerkirche_Z_rich_Hard_05): light concrete bricks with dark gaps."""
    a = np.zeros((size, size, 4), np.uint8); a[..., 3] = 255; a[..., :3] = (38, 34, 30)
    for r in range(0, size, 8):
        off = 8 if (r // 8) % 2 else 0
        for c in range(-16, size, 16):
            x0 = c + off + 2; a[r + 1:r + 6, max(0, x0):max(0, min(size, x0 + 10)), :3] = (190, 170, 135)
    return Image.fromarray(a, "RGBA")


def fragment(m, mat, kind, x, y, z, rot):
    c = D.hexl("#a8a7a2"); ca, sa = math.cos(rot), math.sin(rot)
    at = lambda dx, dy: (x + dx * ca - dy * sa, y + dx * sa + dy * ca)
    bx = lambda dx, dy, w, d, z0, z1, col=c: m.box(mat, *at(dx, dy), w, d, z + z0, z + z1, rot=rot, col=col)
    if kind == "body":                     # 180x60x80: long block, stepped top (haunch), tail stub
        bx(0, 0, 1.8, 0.6, 0, 0.55); bx(-0.45, 0, 0.9, 0.6, 0.55, 0.8); bx(0.95, 0, 0.3, 0.2, 0.1, 0.3)
    elif kind == "paw":                    # 100x60x60: block with 4 toes at the front end
        bx(-0.1, 0, 0.8, 0.6, 0, 0.6)
        for k in range(4): bx(0.4, -0.22 + 0.147 * k, 0.28, 0.1, 0, 0.18, D.hexl("#a8a7a2"))
    elif kind == "head":                   # 90x100x60 incl. ears, lying on its side: eye disc + ears on the top face
        bx(0, 0, 0.9, 1.0, 0, 0.6); bx(-0.2, 0.35, 0.3, 0.3, 0.6, 0.78); bx(-0.2, -0.35, 0.3, 0.3, 0.6, 0.78)
        m.cylinder(mat, *at(0.18, 0.0), 0.2, z + 0.6, z + 0.66, n=10, col=D.hexl("#8e8d88"))


def cobbles(m, mat, a, t, n, L, gz, others, rng):
    """Forecourt: dark cobble setts in front of the porch, draped on the terrain (2 m grid, +4 cm)."""
    from shapely.geometry import box as sbox
    dep, mg_ = COURT; u0, u1 = mg_, L - mg_ - 1.5
    pt = lambda u, d: (a[0] + t[0] * u + n[0] * d, a[1] + t[1] * u + n[1] * d)
    cu = max(1, int((u1 - u0) / 2)); cd = max(1, int((dep - 2.4) / 2))
    for i in range(cu):
        for j in range(cd):
            ua, ub = u0 + (u1 - u0) * i / cu, u0 + (u1 - u0) * (i + 1) / cu
            da, db = 2.4 + (dep - 2.4) * j / cd, 2.4 + (dep - 2.4) * (j + 1) / cd
            P = [pt(ua, da), pt(ua, db), pt(ub, db), pt(ub, da)]  # CCW seen from above
            if any(o.intersects(Polygon(P)) for o in others): continue
            m.quad(mat, [(p[0], p[1], gz(*p) + 0.04) for p in P], uv=[(p[0] / 0.8, p[1] / 0.8) for p in P], n=(0, 0, 1))


def church(m, mats, Pl, ring, rng, a_front_idx, gz=None, others=()):
    """mats = dict(wall, glass, flat, screen, dark). Returns nothing; adds geometry in local coords."""
    mw, mg, mf, ms, md = mats["wall"], mats["glass"], mats["flat"], mats["screen"], mats["dark"]
    W = (255, 255, 255, 255); ne = len(ring); li = a_front_idx
    CR = D.hexl("#f1ede0")
    m.extrude(mf, mf, Pl, -3, PL, col=D.hexl("#a9a398"), roof=False)
    m.flat(mf, Pl, PL + 0.01, D.hexl("#a49f94"))            # porch floor
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b)
        if L < 1.5: m.wall(mw, a, b, PL, EAVE, (4, 4), W); continue
        if i == li: front(m, mats, a, b, L, t, n, CR, rng)
        else:
            nb = max(1, int(round(L / 4.6))); bw = L / nb
            for k in range(nb):
                u0, u1 = k * bw, (k + 1) * bw; uc = (u0 + u1) / 2
                if L > 6 and bw > 3.0:
                    hole = D.rect_pts(uc - 0.75, PL + 2.2, uc + 0.75, EAVE - 1.6)
                    D.bay(m, mw, mg, mf, a, t, n, u0, u1, PL, EAVE, hole, 0.2, int(rng.integers(0, D.NV)), W, hexc("#d8d0b8"), (4, 4.5))
                    D.surround(m, mw, a, t, n, hole, 0.12, (245, 242, 230, 255), 0.04)
                else:
                    D.poly_wall(m, mw, Polygon(D.rect_pts(u0, PL, u1, EAVE)), a, t, n, 0.0, W, lambda u, z: (u / 4, z / 4.5))
        D.band(m, mf, a, b, EAVE - 0.35, EAVE + 0.05, 0.3, D.hexl("#efeadb"))
        if i == li and gz:
            cobbles(m, mats["cobble"], a, t, n, L, gz, others, rng)
            for kind, u, d, yaw in FRAGMENTS:
                px, py = a[0] + t[0] * u + n[0] * d, a[1] + t[1] * u + n[1] * d
                fragment(m, mf, kind, px, py, gz(px, py) + 0.04, math.atan2(t[1], t[0]) + math.radians(yaw))


def front(m, mats, a, b, L, t, n, CR, rng):
    mw, mf, ms, md = mats["wall"], mats["flat"], mats["screen"], mats["dark"]
    W = (255, 255, 255, 255)
    nf = 5; pw = 0.5; step = (L - pw) / nf
    wuv = lambda u, z: (u / 4, z / 4.5)
    for k in range(nf):
        u0, u1 = pw / 2 + k * step, pw / 2 + (k + 1) * step
        if k in (1, 2, 3):          # open porch: dark recess 2.4 m deep
            hole = D.rect_pts(u0 + 0.25, PL, u1 - 0.25, PL + 4.6)
            D.bay(m, mw, md, mf, a, t, n, u0, u1, PL, EAVE, hole, 2.4, 0, W, hexc("#cfc7ae"), (4, 4.5))
        else:                       # perforated screen panel, flush
            hole = D.rect_pts(u0 + 0.3, PL + 0.3, u1 - 0.3, PL + 4.4)
            D.poly_wall(m, mw, Polygon(D.rect_pts(u0, PL, u1, EAVE)).difference(Polygon(hole)), a, t, n, 0.0, W, wuv)
            D.poly_wall(m, ms, Polygon(hole), a, t, n, -0.12, W, lambda u, z: (u * 2.2, z * 2.2))
            D.surround(m, mw, a, t, n, hole, 0.1, (245, 242, 230, 255), 0.05)
    # lead-in strip left/right of first/last pilaster
    for u0, u1 in ((0, pw / 2), (L - pw / 2, L)):
        D.poly_wall(m, mw, Polygon(D.rect_pts(u0, PL, u1, EAVE)), a, t, n, 0.0, W, wuv)
    for k in range(nf + 1):         # pilasters
        uc = pw / 2 + k * step
        m.box(mf, a[0] + t[0] * uc + n[0] * 0.15, a[1] + t[1] * uc + n[1] * 0.15, pw, 0.3, PL, EAVE, rot=math.atan2(t[1], t[0]), col=CR)
    # lintel over porch + stair (3 steps, full width of the porch)
    ps, pe = pw / 2 + step, pw / 2 + 4 * step; pc = (ps + pe) / 2; rot = math.atan2(t[1], t[0])
    for s in range(5):              # 5 steps of 0.2 m down to the forecourt; step s reaches 0.45*(s+1) m out
        dep = 0.45 * (s + 1)
        m.box(mf, a[0] + t[0] * pc + n[0] * (dep / 2), a[1] + t[1] * pc + n[1] * (dep / 2), pe - ps + 0.6, dep, -0.6, PL - 0.2 * (s + 1) + 0.2 * 0, rot=rot, col=D.hexl("#a49f94"))
    # handrails
    for uu in (ps - 0.2, pe + 0.2):
        m.box(mf, a[0] + t[0] * uu + n[0] * 1.1, a[1] + t[1] * uu + n[1] * 1.1, 0.06, 2.2, PL - 0.9, PL + 0.2, rot=rot, col=D.hexl("#555555"))
