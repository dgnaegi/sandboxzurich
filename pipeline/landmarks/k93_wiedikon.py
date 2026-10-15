"""Bahnhof Wiedikon (Reiterbahnhof 1927, H. Herter) + Loewenbrunnen Schmiede Wiedikon.
-> k93_wiedikon.glb, k93_schmiede.glb"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, terrain, k93_kit as K
from k93_lib import hexc, shade
OUTD = F.ROOT + "/web/public/models/landmarks/"
WHITE = (255, 255, 255, 255)

def bay_tex(wallc="#d0ad73", w=5.4, h=12.6, ppm=22):
    """One facade bay of the Reiterbahnhof: ochre ashlar wall, two pilaster strips, tall two-storey window with
    stone frame and small-pane lattice, frieze band, cornice. Returns (base, emissive) for a 1x1 module."""
    W_, H_ = int(w * ppm), int(h * ppm)
    im = K.noisy(Image.new("RGB", (W_, H_), K.rgb(wallc)), 4, 3, 0.4); d = ImageDraw.Draw(im)
    wc = K.rgb(wallc); jn = K.mix(wc, (0, 0, 0), 0.10)
    for y in range(0, H_, int(0.55 * ppm)): d.line([0, y, W_, y], fill=jn)          # ashlar courses
    for k, y in enumerate(range(0, H_, int(0.55 * ppm))):
        for x in range((k % 2) * int(0.6 * ppm), W_, int(1.2 * ppm)): d.line([x, y, x, y + int(0.55 * ppm)], fill=jn)
    em = im.point(lambda v: int(v * 0.30)); em = Image.merge("RGB", (em.getchannel(0), em.getchannel(1).point(lambda v: int(v * 0.8)), em.getchannel(2).point(lambda v: int(v * 0.5)))); de = ImageDraw.Draw(em)   # floodlit stone at night
    px = lambda m: int(m * ppm)
    pil = px(0.55)   # pilasters at both module edges
    for x0 in (0, W_ - pil):
        d.rectangle([x0, px(0.4), x0 + pil, px(10.3)], fill=K.mix(wc, (255, 255, 255), 0.10))
        d.line([x0 + (pil if x0 == 0 else 0), px(0.4), x0 + (pil if x0 == 0 else 0), px(10.3)], fill=K.mix(wc, (0, 0, 0), 0.25))
    # window opening 3.0 x 8.4 m from z=0.7
    ww, wh = px(3.1), px(8.5); x0 = (W_ - ww) // 2; ytop = H_ - px(0.7) - wh
    fr = K.rgb("#ebe7d8"); fb = px(0.28)
    d.rectangle([x0 - fb, ytop - fb, x0 + ww + fb, ytop + wh + fb], fill=K.mix(wc, (255, 255, 255), 0.25))   # stone surround
    d.rectangle([x0 - 2, ytop - 2, x0 + ww + 2, ytop + wh + 2], fill=K.mix(wc, (0, 0, 0), 0.6))              # reveal
    d.rectangle([x0, ytop, x0 + ww, ytop + wh], fill=fr)
    cols, rows = 3, 9
    gx0, gy0, gx1, gy1 = x0 + 3, ytop + 3, x0 + ww - 3, ytop + wh - 3
    for r in range(rows):
        for c in range(cols):
            a_ = gx0 + (gx1 - gx0) * c // cols + 2; b_ = gx0 + (gx1 - gx0) * (c + 1) // cols - 2
            c_ = gy0 + (gy1 - gy0) * r // rows + 2; e_ = gy0 + (gy1 - gy0) * (r + 1) // rows - 2
            t = (r / rows)
            d.rectangle([a_, c_, b_, e_], fill=K.mix((52, 62, 74), (120, 150, 172), 0.35 * (1 - t)))
            de.rectangle([a_, c_, b_, e_], fill=(255, 190, 110) if (c + r) % 5 else (255, 214, 150))
    d.rectangle([x0 - fb - 3, ytop + wh + fb, x0 + ww + fb + 3, ytop + wh + fb + px(0.22)], fill=K.mix(wc, (255, 255, 255), 0.3))   # sill
    # frieze band (plain) and cornice
    d.rectangle([0, px(1.55), W_, px(2.75)], fill=K.mix(wc, (255, 255, 255), 0.05))
    d.rectangle([0, px(0.35), W_, px(1.0)], fill=K.mix(wc, (255, 255, 255), 0.22)); d.line([0, px(1.0), W_, px(1.0)], fill=K.mix(wc, (0, 0, 0), 0.35), width=2)
    return im, em


def frieze_tex(text, wallc="#d8bd8e"):
    f = K.font("Barlow-Bold", 84)
    tw = int(f.getlength(text) + 84 * 0.4 * (len(text) - 1) * 0.25 + 40)
    im = Image.new("RGB", (tw + 60, 150), K.rgb(wallc)); d = ImageDraw.Draw(im)
    x = 30
    for ch in text:
        d.text((x + 1, 29), ch, font=f, fill=K.mix(K.rgb(wallc), (255, 255, 255), 0.5))      # chiselled highlight
        d.text((x, 28), ch, font=f, fill=(58, 56, 52)); x += f.getlength(ch) + 84 * 0.1
    return im.crop((0, 0, int(x + 30), 150)), (x + 30) / 150


def sbb_sign(text, w=420):
    im = Image.new("RGB", (w, 96), (24, 58, 112)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, 95], outline=(235, 235, 235), width=3)
    f = K.font("Barlow-Bold", 54); tw = f.getlength(text); d.text(((w - tw) / 2, 18), text, font=f, fill=(255, 255, 255))
    return im


def cobbles(r=5.0, size=1024, seed=3, col="#8b887f", rings=True):
    """Top view of concentric rows of cobbles (Kopfsteinringe) for a round island, r metres -> size px."""
    rng = np.random.default_rng(seed); im = Image.new("RGB", (size, size), (60, 58, 54)); d = ImageDraw.Draw(im)
    c = size / 2; ppm = size / (2 * r); C0 = K.rgb(col)
    ring_w = 0.11
    k = 0
    while True:
        rr = 0.4 + k * ring_w
        if rr > r: break
        n = max(6, int(2 * math.pi * rr / 0.12))
        for q in range(n):
            a0 = 2 * math.pi * q / n; a1 = 2 * math.pi * (q + 0.88) / n
            t = 1 + (rng.random() - 0.5) * 0.3
            pts = [(c + (rr + dr) * ppm * math.cos(a), c + (rr + dr) * ppm * math.sin(a)) for dr, a in ((0, a0), (0, a1), (ring_w * 0.88, a1), (ring_w * 0.88, a0))]
            d.polygon(pts, fill=tuple(int(v * t) for v in C0))
        k += 1
    return im


def station():
    oid, p = "BE5BEAB6", (544, -1403)
    o = [o for o in F.near(*p, 30) if o["id"][3:11] == oid][0]; fp = F.footprint(o).simplify(0.4)
    c = np.array(fp.centroid.coords[0]); H = terrain.heights((c[0] - 60, c[1] - 60, c[0] + 60, c[1] + 60), 2.0, z_shift=-3.06)
    z0 = float(H.at(*c)); M = L.Model(origin=(c[0], c[1], 0.0))
    bb, be = bay_tex()
    WALL = M.mat("walls", rough=0.95, tex=bb, emis=be, repeat=True)
    BASE = M.mat("base", rough=0.95, tex=K.stone_tex("#8d877a", 0.25, seed=5, rustic=0.1), repeat=True)
    mr = M.mat("trim", rough=0.9)
    ROOF = M.mat("roof", rough=0.85, tex=K.slate_tex("#565b61"), repeat=True)
    fz, far = frieze_tex("ZÜRICH-WIEDIKON-SBB"); FR = M.mat("frieze", rough=0.9, tex=fz, repeat=False)
    CLK = M.mat("clock", rough=0.5, tex=K.clock_tex(256), emis=K.clock_tex(256).point(lambda v: int(v * 0.5)), repeat=False)
    SGN = M.mat("sign", rough=0.5, tex=sbb_sign("Zürich Wiedikon"), emis=sbb_sign("Zürich Wiedikon").point(lambda v: int(v * 0.35)), repeat=False)
    r = list(fp.minimum_rotated_rectangle.exterior.coords)[:4]; e1 = np.subtract(r[1], r[0]); e2 = np.subtract(r[2], r[1])
    if np.hypot(*e1) < np.hypot(*e2): e1, e2 = e2, e1
    Lg, Sh = np.hypot(*e1), np.hypot(*e2); u = e1 / Lg; ang = math.atan2(u[1], u[0]); n = np.array([-u[1], u[0]])
    if np.dot(n, np.array([500, -1360]) - c) < 0: n = -n
    eave = 12.6
    up = np.array([math.cos(math.radians(-135.3)), math.sin(math.radians(-135.3))])
    if np.dot(u, up) < 0: u = -u; n = -n; ang = math.atan2(u[1], u[0])
    if np.dot(n, np.array([500, -1360]) - c) < 0: n = -n  # n -> NW (open cutting side)
    from shapely.geometry import Polygon as _P, box as _box
    S0, S1, ZB, ZR = -3.0, 15.0, -1.5, -7.8   # opening across the cutting (s along u), bridge soffit, rail level (rel. to street)
    BW, SC = 4.38, 0.0                         # facade bay width on the end faces (5 bays over 21.9 m)
    w2l = lambda pts: [(float(np.dot(np.array(p) - c, u)), float(np.dot(np.array(p) - c, n))) for p in pts]
    l2w = lambda pts: [tuple(c + u * s_ + n * k_) for s_, k_ in pts]
    fl = _P(w2l(fp.exterior.coords))
    for lo, hi, base in ((-99, S0, -9.0), (S0, S1, ZB), (S1, 99, -9.0)):
        part = fl.intersection(_box(lo, -99, hi, 99))
        for g in ([part] if part.geom_type == "Polygon" else list(getattr(part, "geoms", []))):
            if g.area < 1: continue
            pts = l2w(list(g.exterior.coords)[:-1])
            K.wall_band(M, BASE, pts, base, 0.0, 3.0, 3.0, flat=0.0)
            K.wall_aligned(M, WALL, pts, 0.0, eave, BW, eave, c, n, -11.4)
            if base == ZB: M.cap(mr, pts, ZB, hexc("#4a4c4e"), flip=True)   # soffit of the bridge
    # cornice around the whole building + plinth course
    M.prism(mr, list(fp.buffer(0.4, join_style=2).exterior.coords)[:-1], eave - 0.9, eave + 0.1, hexc("#cfb68a"), topcol=hexc("#8a8478"), top=True, shade_sides=True)
    M.prism(mr, list(fp.buffer(0.12, join_style=2).exterior.coords)[:-1], -0.1, 0.45, hexc("#9d9786"), top=False)
    # cutting retaining walls and portal wing walls (stone), open towards the north-west
    for sw in (S0, S1):
        for k0, k1 in ((-11.5, -26.0),):
            a_ = c + u * sw + n * k0; b_ = c + u * sw + n * k1; m_ = (a_ + b_) / 2
            K.box_tex(M, BASE, (m_[0], m_[1], (ZR + 0.6) / 2), (0.7, abs(k1 - k0), 0.6 - ZR), rot=ang + math.pi / 2, col=WHITE, tile=(2.0, 1.4))
            M.box(mr, (m_[0], m_[1], 0.9), (1.0, abs(k1 - k0), 0.35), hexc("#a7a291"), rot=ang + math.pi / 2)
    # hipped slate roof with dormers (skylights) and chimneys
    K.pitched(M, ROOF, tuple(c), Lg, Sh, eave + 0.1, 4.6, rot=ang, eave=0.9, hip=1.0, tile=1.0, col=WHITE)
    for k in (-1, 0, 1):
        q = c + u * (k * 9) + n * (-(Sh / 2 - 4) if k % 2 == 0 else (Sh / 2 - 4))
        K.box_tex(M, BASE, (q[0], q[1], eave + 3.0), (1.1, 1.1, 2.4), rot=ang, col=hexc("#cdbfa4"), tile=(1.0, 1.0))
        M.box(mr, (q[0], q[1], eave + 4.3), (1.5, 1.5, 0.25), hexc("#85837d"), rot=ang)
    nr = np.array([-u[1], u[0]])   # right-hand normal of u: ordering a->b = +nr gives outward normal +u
    for sg in (-1, 1):   # the two end faces (u = +-16.8): 5-bay front with frieze, clock, entrance canopy
        face, kc = 16.8, -0.45
        q = c + u * sg * (face + 0.12) + n * kc
        fh = 0.95; fw = fh * far
        if fw > 17.0: fw = 17.0; fh = fw / far
        d_ = nr if sg > 0 else -nr
        K.quad_tex(M, FR, q - d_ * fw / 2 + u * sg * 0.08, q + d_ * fw / 2 + u * sg * 0.08, 10.1, 10.1 + fh)
        cs = 1.7
        K.quad_tex(M, CLK, q - d_ * cs / 2 + u * sg * 0.12, q + d_ * cs / 2 + u * sg * 0.12, 7.4, 7.4 + cs)
        qq = c + u * sg * (face + 1.2) + n * kc
        M.box(mr, (qq[0], qq[1], 4.6), (2.4, BW - 1.0, 0.18), hexc("#3d4146"), rot=ang)
        for dk in (-1.6, 1.6):
            qp = qq + n * dk
            M.box(mr, (qp[0], qp[1], 2.3), (0.12, 0.12, 4.6), hexc("#3d4146"))
    # station name sign on both long faces next to the cutting
    for sg in (1, -1):
        face = 10.5 if sg > 0 else -9.9                     # k of the face; outward normal is +-n
        qa = c + n * (face + 0.06 * sg) + u * (-13.0)
        sgn_w = 3.4; sgn_h = sgn_w * 96 / 420
        out = n * sg                                        # outward direction
        d_ = np.array([-out[1], out[0]])                    # a->b with cross(d, z) = out
        K.quad_tex(M, SGN, qa - d_ * sgn_w / 2, qa + d_ * sgn_w / 2, 3.0, 3.0 + sgn_h)
    return M, c, z0


def fountain():
    x, y = 314.2, -1561.5
    H = terrain.heights((x - 30, y - 30, x + 30, y + 30), 2.0, z_shift=-3.06); z0 = float(H.at(x, y))
    M = L.Model(origin=(x, y, 0.0))
    R = 5.0
    COB = M.mat("cobbles", rough=0.95, tex=cobbles(R), repeat=False)
    ST = M.mat("stone", rough=0.9, tex=K.stone_tex("#b9ae98", 0.5, seed=9), repeat=True)
    WAT = M.mat("water", rough=0.2, tex=Image.new("RGB", (4, 4), (88, 134, 150)), repeat=True)
    # cobbled island: flat disc, slightly raised over the road (0.05)
    n_ = 40
    for i in range(n_):
        a0, a1 = 2 * math.pi * i / n_, 2 * math.pi * (i + 1) / n_
        p0 = (x + R * math.cos(a0), y + R * math.sin(a0)); p1 = (x + R * math.cos(a1), y + R * math.sin(a1))
        uv = lambda p: ((p[0] - x) / (2 * R) + 0.5, 0.5 - (p[1] - y) / (2 * R))
        M.tri(COB, (x, y, 0.06), (*p0, 0.06), (*p1, 0.06), WHITE, [uv((x, y)), uv(p0), uv(p1)])
    # outer basin ring (low kerb) and inner water basin
    def ring(r0, r1, z0_, z1_, mat, col, n=32):
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            P = lambda r, a, z: (x + r * math.cos(a), y + r * math.sin(a), z)
            M.quad(mat, P(r1, a0, z0_), P(r1, a1, z0_), P(r1, a1, z1_), P(r1, a0, z1_), shade(col, 0.85 + 0.15 * math.cos((a0 + a1) / 2 - 0.9)), [(i * 0.5, 1), ((i + 1) * 0.5, 1), ((i + 1) * 0.5, 0), (i * 0.5, 0)])
            M.quad(mat, P(r0, a0, z1_), P(r1, a0, z1_), P(r1, a1, z1_), P(r0, a1, z1_), col, [(i * 0.5, 0), (i * 0.5, 1), ((i + 1) * 0.5, 1), ((i + 1) * 0.5, 0)])
    ring(2.0, 2.45, 0.0, 0.5, ST, hexc("#b9ae98"))
    n_ = 32
    for i in range(n_):   # water surface
        a0, a1 = 2 * math.pi * i / n_, 2 * math.pi * (i + 1) / n_
        M.tri(WAT, (x, y, 0.38), (x + 2.0 * math.cos(a0), y + 2.0 * math.sin(a0), 0.38), (x + 2.0 * math.cos(a1), y + 2.0 * math.sin(a1), 0.38), WHITE)
    # stem, shallow bowl, sculpted column (stylised lion figure, sandstone)
    for (r0, r1, z0_, z1_) in ((0.6, 0.5, 0.0, 0.7), (0.5, 0.42, 0.7, 1.05)):
        for i in range(12):
            a0, a1 = 2 * math.pi * i / 12, 2 * math.pi * (i + 1) / 12
            P = lambda r, a, z: (x + r * math.cos(a), y + r * math.sin(a), z)
            M.quad(ST, P(r0, a0, z0_), P(r0, a1, z0_), P(r1, a1, z1_), P(r1, a0, z1_), shade(WHITE, 0.85 + 0.15 * math.cos((a0 + a1) / 2)), [(0, 1), (1, 1), (1, 0), (0, 0)])
    for i in range(20):   # bowl (cone dish)
        a0, a1 = 2 * math.pi * i / 20, 2 * math.pi * (i + 1) / 20
        P = lambda r, a, z: (x + r * math.cos(a), y + r * math.sin(a), z)
        M.quad(ST, P(0.4, a0, 1.0), P(0.4, a1, 1.0), P(1.05, a1, 1.45), P(1.05, a0, 1.45), shade(WHITE, 0.9), [(0, 1), (1, 1), (1, 0), (0, 0)])
        M.quad(ST, P(1.05, a0, 1.45), P(1.05, a1, 1.45), P(0.95, a1, 1.45), P(0.95, a0, 1.45), shade(WHITE, 1.0))
        M.tri(WAT, (x, y, 1.33), P(0.95, a0, 1.33), P(0.95, a1, 1.33), WHITE)
    K.box_tex(M, ST, (x, y, 2.55), (0.55, 0.42, 2.2), rot=0.3, col=WHITE, tile=(1.0, 1.0), top=hexc("#c8bda7"))
    K.box_tex(M, ST, (x + 0.05, y, 3.75), (0.42, 0.36, 0.7), rot=0.3, col=shade(WHITE, 1.05), tile=(1.0, 1.0))   # head of the figure
    K.box_tex(M, ST, (x + 0.25, y + 0.12, 3.3), (0.22, 0.2, 0.5), rot=0.5, col=WHITE, tile=(1.0, 1.0))           # paw
    return M

if __name__ == "__main__":
    M, c, z0 = station(); M.write(OUTD + "k93_wiedikon.glb"); print("wiedikon tris", M.tris(), "origin", c.round(1).tolist(), round(z0, 2))
    Mf = fountain(); Mf.write(OUTD + "k93_schmiede.glb"); print("schmiede tris", Mf.tris())
