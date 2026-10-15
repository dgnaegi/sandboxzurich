"""Roentgenplatz Randbau (Genossenschafts-Blockrand 1926, Roentgenstrasse 56 / Ostecke des Platzes), Kreis 5.
Dark-red plaster, green folding shutters (painted into the bay texture), round-arched top-floor windows, hip roof with eyebrow dormers,
big arched gate with iron grille + round reliefs + clock in the front facade, low stone planter walls with stone balls in front.
Photo: preview/plaza3_roentgenplatz.jpg (left), research/v3/roentgenplatz.md."""
import math
from PIL import Image, ImageDraw, ImageFont
from common import *
from lm import *
import detail as D
from k45_volkshaus import front_edge
from shapely.geometry import Polygon

WALLC = "#86303a"; FRAME = "#e8e2d2"; SHUT = "#8ba48a"
NFL, FH, Z0 = 5, 3.1, 0.5          # floors, floor height, plinth height
R_EG, R_MID, R_TOP, R_PLAIN = 0, 1, 4, 5   # texture rows (bottom -> top)
NR = 6
HOLE_W, HOLE_Z0, HOLE_H = 1.3, 0.85, 1.55   # window opening inside a floor


def bay_tile(bw, ppm=44):
    """One bay x NR rows. Row r (0 = bottom) occupies v in [r/NR, (r+1)/NR]."""
    W, fh = int(bw * ppm), int(FH * ppm); rng = np.random.default_rng(3)
    im = Image.new("RGB", (W, fh * NR), hexc(WALLC)[:3]); d = ImageDraw.Draw(im)
    a = np.asarray(im).astype(np.int16) + rng.normal(0, 4, (im.height, W, 1)).astype(np.int16)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    px = lambda m: int(round(m * ppm))
    for r in (R_EG, 1, 2, 3, R_TOP):
        yb = im.height - r * fh          # bottom y of the row
        cx = W // 2; hw = px(HOLE_W / 2)
        zt = HOLE_Z0 + HOLE_H
        y0, y1 = yb - px(zt), yb - px(HOLE_Z0)
        arch = r == R_TOP
        # pale surround
        fw = px(0.09)
        if arch:
            d.rectangle([cx - hw - fw, y0 + hw - fw, cx + hw + fw, y1 + fw], fill=hexc(FRAME)[:3])
            d.pieslice([cx - hw - fw, y0 - fw - 0, cx + hw + fw, y0 + 2 * hw + fw], 180, 360, fill=hexc(FRAME)[:3])
        else:
            d.rectangle([cx - hw - fw, y0 - fw, cx + hw + fw, y1 + fw], fill=hexc(FRAME)[:3])
        d.rectangle([cx - hw - px(0.18), y1 + fw, cx + hw + px(0.18), y1 + fw + px(0.1)], fill=hexc(FRAME)[:3])   # sill
        # green folding shutters left/right (flush to the wall, slats)
        sw = px(0.52); sg = hexc(SHUT)[:3]
        for side in (-1, 1):
            xa = cx + side * (hw + fw + px(0.03)); xb = xa + side * sw
            xa, xb = min(xa, xb), max(xa, xb)
            ys0 = int(y0)
            d.rectangle([xa, ys0 - fw, xb, y1 + fw], fill=sg)
            for yy in range(ys0, y1 + fw, 5): d.line([xa, yy, xb, yy], fill=tuple(int(v * 0.82) for v in sg))
            d.rectangle([xa, ys0 - fw, xb, y1 + fw], outline=tuple(int(v * 0.65) for v in sg))
        # top floor: cornice shadow line
        if arch: d.line([0, yb - fh + px(0.1), W, yb - fh + px(0.1)], fill=tuple(int(v * 0.8) for v in hexc(WALLC)[:3]), width=2)
    # plain plaster row is left as is (row R_PLAIN = top of image? no: row 5 -> y in [0, fh])
    return im


def clock_face(d, x, y, s):
    d.ellipse([x, y, x + s, y + s], fill=(236, 232, 218)); d.ellipse([x, y, x + s, y + s], outline=(60, 60, 60), width=2)
    c = x + s / 2
    for k in range(12):
        a = math.radians(k * 30); d.line([c + s * .38 * math.sin(a), y + s / 2 - s * .38 * math.cos(a), c + s * .46 * math.sin(a), y + s / 2 - s * .46 * math.cos(a)], fill=(40, 40, 40))
    d.line([c, y + s / 2, c + s * .3 * math.sin(math.radians(60)), y + s / 2 - s * .3 * math.cos(math.radians(60))], fill=(30, 30, 30), width=2)
    d.line([c, y + s / 2, c - s * .2 * math.sin(math.radians(20)), y + s / 2 + s * .2 * math.cos(math.radians(20))], fill=(30, 30, 30), width=2)


def relief(d, x, y, s):
    d.ellipse([x, y, x + s, y + s], fill=(196, 188, 168)); d.ellipse([x + 3, y + 3, x + s - 3, y + s - 3], outline=(150, 142, 124), width=2)
    d.ellipse([x + s * .3, y + s * .3, x + s * .7, y + s * .7], fill=(150, 142, 124))   # roundel motif


def strip_paint(d, de, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(120, 120, 120))
    clock_face(d, x, y, 31); relief(d, x + 40, y, 31)
    de.ellipse([x, y, x + 31, y + 31], fill=(70, 66, 50))           # clock faintly lit at night


STRIP = {"clock": (0, 32), "relief": (40, 72)}


def strip_quad(m, mg, p0, p1, h, key, n, off=0.0):
    x0, x1 = STRIP[key]
    m.quad(mg, [p0, p1, (p1[0], p1[1], p0[2] + h), (p0[0], p0[1], p0[2] + h)], [(x0 / 1024, 0.0), (x1 / 1024, 0.0), (x1 / 1024, 0.25), (x0 / 1024, 0.25)], n=(n[0], n[1], 0))


def ball(m, mf, cx, cy, z, r, col):
    zs = [(-1.0, 0.0), (-0.8, 0.6), (-0.4, 0.92), (0.0, 1.0), (0.4, 0.92), (0.8, 0.6), (1.0, 0.0)]
    for (za, ra), (zb, rb) in zip(zs[:-1], zs[1:]):
        if ra < 0.01 and rb < 0.01: continue
        m.cylinder(mf, cx, cy, max(ra, 0.001) * r, z + za * r, z + zb * r, n=8, col=col, r1=max(rb, 0.001) * r, smooth=True)


def dquad(m, mat, pts, col):
    m.quad(mat, pts, col=col); m.quad(mat, pts[::-1], col=col)


def build():
    B = bid("ID_8DDAEB92")
    P = outline(B["fp"], 0.3)
    c = P.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    Pl = orient(localize(P, ox, oy), 1.0)
    rng = np.random.default_rng(7)
    m = Model("roentgen")
    BW = 2.7
    mw = m.mat("wall", bay_tile(BW))
    mg = m.mat("glass", *D.glass_atlas_g(frame="#e8e2d2", glass="#27323b", sky="#8aa3b4", cols=2, rows=3, seed=8, lit_p=0.35, sign=strip_paint), rough=0.35)
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    STONE, DARK, IRON, CAP = D.hexl("#8d887c"), D.hexl("#1b1a1a"), D.hexl("#2c2d2e"), D.hexl("#b8b2a2")
    CREAM, ROOF = D.hexl("#d8cfba"), D.hexl("#7e4034")
    W = (255, 255, 255, 255)
    ring = list(Pl.exterior.coords)[:-1]; ne = len(ring)
    fi = front_edge(ring, (760 - ox, 128 - oy))
    m.extrude(mf, mf, Pl, -3, Z0, col=STONE, roof=False)
    ztop = Z0 + NFL * FH

    def uvf_row(u0, bw, row, z0):
        v0 = row / NR
        return lambda u, z: ((u - u0) / bw, v0 + (z - z0) / FH / NR)

    def window_bay(a, t, n, u0, u1, zf, row, hole, depth=0.22):
        bw = u1 - u0
        Hh = Polygon(hole)
        D.poly_wall(m, mw, Polygon(D.rect_pts(u0, zf, u1, zf + FH)).difference(Hh), a, t, n, 0.0, W, uvf_row(u0, bw, row, zf))
        h = list(hole)
        for i in range(len(h)):
            p, q = h[i], h[(i + 1) % len(h)]
            l = math.hypot(q[0] - p[0], q[1] - p[1])
            if l < 1e-4: continue
            du, dz = q[0] - p[0], q[1] - p[1]
            nl = (t[0] * (-dz / l), t[1] * (-dz / l), du / l)
            D._oriented(m, mf, [D.P3(a, t, n, p[0], p[1], 0), D.P3(a, t, n, q[0], q[1], 0), D.P3(a, t, n, q[0], q[1], -depth), D.P3(a, t, n, p[0], p[1], -depth)], nl, [(0, 0), (1, 0), (1, 1), (0, 1)], D.hexl(FRAME))
        k = int(rng.integers(0, D.NV)); cu0, cu1 = k / D.NV, (k + 1) / D.NV
        hz0 = min(p[1] for p in h); hz1 = max(p[1] for p in h); hu0 = min(p[0] for p in h); hu1 = max(p[0] for p in h)
        D.poly_wall(m, mg, Hh, a, t, n, -depth, W, lambda u, z: (cu0 + (cu1 - cu0) * (u - hu0) / (hu1 - hu0), 0.25 + 0.75 * (z - hz0) / (hz1 - hz0)))

    gate = {}
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b)
        if L < 1.8: m.wall(mw, a, b, Z0, ztop, (BW, 1e4), W, u0=0.0, v0=R_PLAIN / NR); continue
        nb = max(1, int(round(L / BW))); bw = L / nb
        ig = nb // 2 - 1 if (i == fi and nb >= 4) else None
        for f in range(NFL):
            zf = Z0 + f * FH
            row = R_EG if f == 0 else (R_TOP if f == NFL - 1 else R_MID)
            for j in range(nb):
                u0, u1 = j * bw, (j + 1) * bw; uc = (u0 + u1) / 2
                if f == 0 and ig is not None and j in (ig, ig + 1):
                    if j == ig:   # both gate bays in one piece, arch cut out
                        ug_ = (ig + 1) * bw; hg = D.arch_pts(ug_ - 1.7, Z0, ug_ + 1.7, Z0 + 2.75)
                        D.poly_wall(m, mw, Polygon(D.rect_pts(u0, zf, u0 + 2 * bw, zf + FH)).difference(Polygon(hg)), a, t, n, 0.0, W, uvf_row(u0, bw, R_PLAIN, zf))
                    continue
                ww = min(HOLE_W, bw - 1.1)
                if row == R_TOP: hole = D.arch_pts(uc - ww / 2, zf + HOLE_Z0, uc + ww / 2, zf + HOLE_Z0 + HOLE_H - ww / 2)
                else: hole = D.rect_pts(uc - ww / 2, zf + HOLE_Z0, uc + ww / 2, zf + HOLE_Z0 + HOLE_H)
                window_bay(a, t, n, u0, u1, zf, row, hole)
        # bands: plinth top, floor-1 sill, eaves cornice
        D.band(m, mf, a, b, Z0 - 0.15, Z0 + 0.05, 0.08, CAP)
        D.band(m, mf, a, b, ztop - 0.5, ztop + 0.1, 0.35, CREAM)
        if ig is not None: gate = dict(a=a, t=t, n=n, L=L, bw=bw, ig=ig)
    # ---- gate, grille, reliefs, clock, planter walls on the front edge
    a, b = ring[fi], ring[(fi + 1) % ne]
    if gate:
        a, t, n, bw, ig = gate["a"], gate["t"], gate["n"], gate["bw"], gate["ig"]
        ug = (ig + 1) * bw; gw = 3.4; zs = Z0 + 2.75; ang = math.atan2(t[1], t[0])
        hole = D.arch_pts(ug - gw / 2, Z0 + 0.0, ug + gw / 2, zs)
        Hh = Polygon(hole); dep = 1.4
        D.poly_wall(m, mf, Polygon(D.rect_pts(ug - gw / 2 - 0.4, Z0, ug + gw / 2 + 0.4, Z0 + 4.6)).difference(Hh).intersection(Polygon(D.rect_pts(ug - gw / 2 - 0.4, Z0, ug + gw / 2 + 0.4, Z0 + 4.6))), a, t, n, 0.03, D.hexl(FRAME), lambda u, z: (0, 0)) if False else None
        # arch surround (stone voussoirs band) + dark passage
        D.surround(m, mf, a, t, n, hole, 0.28, CAP, 0.06, 0.0)
        h = list(hole)
        for i2 in range(len(h)):
            p, q = h[i2], h[(i2 + 1) % len(h)]; l = math.hypot(q[0] - p[0], q[1] - p[1])
            if l < 1e-4 or (p[1] == q[1] == Z0): continue
            du, dz = q[0] - p[0], q[1] - p[1]; nl = (t[0] * (-dz / l), t[1] * (-dz / l), du / l)
            D._oriented(m, mf, [D.P3(a, t, n, p[0], p[1], 0), D.P3(a, t, n, q[0], q[1], 0), D.P3(a, t, n, q[0], q[1], -dep), D.P3(a, t, n, p[0], p[1], -dep)], nl, [(0, 0), (1, 0), (1, 1), (0, 1)], D.hexl("#75706a"))
        D.poly_wall(m, mf, Hh, a, t, n, -dep, D.hexl("#3a3733"), lambda u, z: (0, 0))
        # iron grille in the opening: vertical bars + sunburst spokes
        def Q(u, z, d=-0.18): return D.P3(a, t, n, u, z, d)
        r = gw / 2
        for k in range(-11, 12):
            u = ug + k * r / 11.5; dz = math.sqrt(max(0.0, r * r - (u - ug) ** 2))
            dquad(m, mf, [Q(u - 0.02, Z0), Q(u + 0.02, Z0), Q(u + 0.02, zs + dz), Q(u - 0.02, zs + dz)], IRON)
        for k in range(1, 12):
            an = math.pi * k / 12; ux_, uz_ = math.cos(an), math.sin(an)
            dquad(m, mf, [Q(ug - 0.02 * uz_, zs - 0.02 * ux_), Q(ug + 0.02 * uz_, zs + 0.02 * ux_), Q(ug + r * ux_ + 0.02 * uz_, zs + r * uz_ + 0.02 * ux_), Q(ug + r * ux_ - 0.02 * uz_, zs + r * uz_ - 0.02 * ux_)], IRON) if False else None
            dquad(m, mf, [Q(ug, zs - 0.015, -0.2), Q(ug + r * 0.97 * ux_, zs + r * 0.97 * uz_ - 0.015, -0.2), Q(ug + r * 0.97 * ux_, zs + r * 0.97 * uz_ + 0.015, -0.2), Q(ug, zs + 0.015, -0.2)], IRON)
        for rr in (r * 0.55, r * 0.97):
            pts = [(ug + rr * math.cos(math.pi * s / 24), zs + rr * math.sin(math.pi * s / 24)) for s in range(25)]
            for p, q in zip(pts[:-1], pts[1:]): dquad(m, mf, [Q(p[0], p[1] - 0.02, -0.2), Q(q[0], q[1] - 0.02, -0.2), Q(q[0], q[1] + 0.02, -0.2), Q(p[0], p[1] + 0.02, -0.2)], IRON)
        dquad(m, mf, [Q(ug - r, Z0 + 1.0), Q(ug + r, Z0 + 1.0), Q(ug + r, Z0 + 1.05), Q(ug - r, Z0 + 1.05)], IRON)
        # round reliefs beside the gate (EG) and the clock above (floor 3, centre)
        for s in (-1, 1):
            uu = ug + s * (gw / 2 + 1.05); p0, p1 = D.P3(a, t, n, uu - 0.5, Z0 + 2.6, 0.04), D.P3(a, t, n, uu + 0.5, Z0 + 2.6, 0.04)
            strip_quad(m, mg, p0, p1, 1.0, "relief", n)
        zc = Z0 + 2 * FH + 1.55
        strip_quad(m, mg, D.P3(a, t, n, ug - 0.5, zc, 0.04), D.P3(a, t, n, ug + 0.5, zc, 0.04), 1.0, "clock", n)
        # planter walls with piers + stone balls in front
        for s in (-1, 1):
            u_in, u_out = ug + s * (gw / 2 + 0.6), ug + s * (gw / 2 + 0.6 + 5.2); dd = 2.9
            lo, hi = min(u_in, u_out), max(u_in, u_out)
            def wl(ua, da, ub, db, th=0.32):
                pa, pb = D.P3(a, t, n, ua, 0, da), D.P3(a, t, n, ub, 0, db)
                cx_, cy_ = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2; ln = math.hypot(pb[0] - pa[0], pb[1] - pa[1]); rot = math.atan2(pb[1] - pa[1], pb[0] - pa[0])
                m.box(mf, cx_, cy_, ln, th, -0.8, 0.62, rot=rot, col=STONE); m.box(mf, cx_, cy_, ln + 0.08, th + 0.1, 0.62, 0.7, rot=rot, col=CAP)
            wl(lo, dd, hi, dd); wl(lo, 0.3, lo, dd); wl(hi, 0.3, hi, dd)
            gc = D.P3(a, t, n, (lo + hi) / 2, 0.0, dd / 2 + 0.15); inner = Polygon([D.P3(a, t, n, lo + 0.2, 0, 0.4)[:2], D.P3(a, t, n, hi - 0.2, 0, 0.4)[:2], D.P3(a, t, n, hi - 0.2, 0, dd - 0.2)[:2], D.P3(a, t, n, lo + 0.2, 0, dd - 0.2)[:2]])
            m.flat(mf, inner, 0.55, D.hexl("#56703f"))
            for uu in (lo, hi):
                for dd_ in (dd,) + ((0.3,) if uu == lo and s == 1 or uu == hi and s == -1 else ()):
                    p = D.P3(a, t, n, uu, 0, dd_); m.box(mf, p[0], p[1], 0.5, 0.5, -0.8, 0.95, rot=ang, col=STONE); m.box(mf, p[0], p[1], 0.6, 0.6, 0.95, 1.02, rot=ang, col=CAP)
                    ball(m, mf, p[0], p[1], 1.28, 0.27, D.hexl("#9c968a"))
    # ---- hip roof (ridge along the long axis) with eyebrow dormers + chimneys
    (cx, cy), ux, uy, L_, W_ = rect_of(Pl, 0.0)
    oh = 0.65; rise = 6.2
    vx, vy = -uy, ux; hl, hw = L_ / 2 + oh, W_ / 2 + oh
    Pt = lambda s, tt, zz: (cx + ux * s + vx * tt, cy + uy * s + vy * tt, zz)
    rl = max(0.5, L_ / 2 - W_ / 2)
    m.extrude(mf, mf, Pl, ztop, ztop + 0.2, col=CREAM, roof=False) if False else None
    r0, r1 = Pt(-rl, 0, ztop + rise), Pt(rl, 0, ztop + rise)
    c00, c10, c11, c01 = Pt(-hl, -hw, ztop - 0.2), Pt(hl, -hw, ztop - 0.2), Pt(hl, hw, ztop - 0.2), Pt(-hl, hw, ztop - 0.2)
    m.quad(mf, [c00, c10, r1, r0], col=ROOF); m.quad(mf, [c11, c01, r0, r1], col=ROOF)
    m.tri(mf, [c10, c11, r1], col=D.hexl("#744036")); m.tri(mf, [c01, c00, r0], col=D.hexl("#744036"))
    for sgn in (-1, 1):   # tile courses as thin darker lines
        for k in range(1, 14):
            f = k / 14; zz = ztop - 0.2 + (rise + 0.2) * f; tt = sgn * (hw * (1 - f)); half = (L_ / 2 + oh) - (L_ / 2 + oh - rl) * f
            half = hl * (1 - f) + rl * f
            dquad(m, mf, [Pt(-half, tt, zz), Pt(half, tt, zz), Pt(half, tt + sgn * 0.0, zz + 0.03), Pt(-half, tt, zz + 0.03)], D.hexl("#5e2f27")) if False else None
    # dormers: eyebrow, 5 per long slope
    for sgn in (-1, 1):
        for k in range(5):
            s = -L_ / 2 + L_ * (k + 0.5) / 5
            if abs(s) > rl + hw * 0.25: continue
            f = 0.30; tt = sgn * hw * (1 - f); zz = ztop - 0.2 + (rise + 0.2) * f
            p = Pt(s, tt, zz); rot = math.atan2(uy, ux)
            m.box(mf, p[0], p[1], 1.5, 1.2, zz - 0.4, zz + 0.95, rot=rot, col=D.hexl("#8d3a3a"))
            fr = Pt(s, tt + sgn * 0.62, zz)
            q0, q1 = Pt(s - 0.55, tt + sgn * 0.62, zz - 0.2), Pt(s + 0.55, tt + sgn * 0.62, zz - 0.2)
            m.quad(mg, [q0, q1, (q1[0], q1[1], zz + 0.8), (q0[0], q0[1], zz + 0.8)] if sgn > 0 else [q1, q0, (q0[0], q0[1], zz + 0.8), (q1[0], q1[1], zz + 0.8)],
                   [(0.0, 0.25), (0.125, 0.25), (0.125, 1.0), (0.0, 1.0)], n=(vx * sgn, vy * sgn, 0))
            top = Pt(s, tt, zz + 1.35)
            m.quad(mf, [Pt(s - 0.85, tt - sgn * 0.7, zz + 0.95), Pt(s + 0.85, tt - sgn * 0.7, zz + 0.95), Pt(s + 0.85, tt + sgn * 0.75, zz + 0.95), Pt(s - 0.85, tt + sgn * 0.75, zz + 0.95)][::sgn], col=ROOF)
    for s, tt in ((-rl * 0.6, 0.9), (rl * 0.7, -1.0)):
        p = Pt(s, tt, 0); m.box(mf, p[0], p[1], 0.9, 0.9, ztop + rise - 1.5, ztop + rise + 1.3, rot=math.atan2(uy, ux), col=D.hexl("#9a4a3a")); m.box(mf, p[0], p[1], 1.1, 1.1, ztop + rise + 1.3, ztop + rise + 1.45, rot=math.atan2(uy, ux), col=CAP)
    hide = [[round(p.x, 1), round(p.y, 1)] for p in (g_.representative_point() for g_ in (B["fp"].geoms if hasattr(B["fp"], "geoms") else [B["fp"]]))]
    finish(m, "roentgen_randbau", "Roentgenplatz Randbau", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
