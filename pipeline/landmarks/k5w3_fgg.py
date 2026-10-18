"""Frau Gerolds Garten (Geroldstrasse 23): the real plot (OSM way 1409699323, landuse=retail) as a gravel lane garden between Hardbruecke tracks (N)
and Geroldstrasse (S entrance, Freitag-Turm at the SE corner). Gerolds Markt building (swissBUILDINGS3D ID_6999753E) with glass shopfront, container
stacks (bars/kitchens) with timber decks, raised terrace, table sets with umbrellas, planter beds with shrubs, string lights + bunting across the
lane, signposts, entrance gate with the name board. Photos: research/fgg.md, preview/fgg_ref.jpg. Registers in overrides/landmarks_k5w3.json."""
import math
from k5w3_kit import *
import k5w3_freitag as F
import k5w3_fgg_tex as T

IDS = ["ID_6999753E"]                                                    # Gerolds Markt (replaced by the model, footprint stays a collider)
PLOT = [(155.4, 105.0), (176.6, 97.7), (192.0, 93.8), (205.0, 129.7), (209.3, 142.8), (211.3, 148.0), (216.7, 162.6), (218.0, 166.3), (218.4, 167.4), (197.6, 174.9),
        (191.1, 177.1), (190.3, 177.4), (183.6, 179.8), (180.0, 169.9), (170.0, 143.3), (163.4, 126.6)]          # OSM way 1409699323 in local metres
LANE = [(190.0, 180.0), (188.0, 158.0), (180.0, 128.0), (173.0, 111.0), (168.0, 100.0)]                         # OSM footway 400682255 + service way to Geroldstrasse
UMB = ["#b8352a", "#2f8a86", "#2e7d4f", "#d99a2b", "#e8e2d2", "#2f5f94"]
GREENS = ["#3f7a3a", "#4f8c42", "#2f6a3a", "#5b9648"]


class M8(Model):
    max_mats = 8


OXY = [0.0, 0.0]


def lane_pt(s, off):
    """Point at arc length s along LANE, lateral offset off (left of travel = +)."""
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(LANE[:-1], LANE[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if s <= acc + L or (x1, y1) == LANE[-1]:
            f = (s - acc) / L; dx, dy = (x1 - x0) / L, (y1 - y0) / L
            return x0 + dx * (s - acc) - dy * off - OXY[0], y0 + dy * (s - acc) + dx * off - OXY[1], math.atan2(dy, dx)
        acc += L


def build():
    setup()
    P0 = Polygon(PLOT); c = P0.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    gl = lambda x, y: ground(x + ox, y + oy) - oz; OXY[0], OXY[1] = ox, oy
    rng = np.random.default_rng(31)
    F.COLS = T.CCOLS; F.LAB = {}
    m = M8("frau_gerolds_garten")
    ma = m.mat("cont", *T.containers(), rough=0.6); mf = m.mat("flat", solid(W4)); mg = m.mat("gravel", T.gravel(), rough=1.0); mw = m.mat("wood", T.wood(), rough=0.9)
    sg = T.signs(); ms = m.mat("sign", sg[0], sg[1], rough=0.7); gs = T.shopglass(); mgl = m.mat("glass", gs[0], gs[1], rough=0.5)
    mco = m.mat("corr", tex_corrugated("#3b4044"), rough=0.7)
    ml = m.mat("light", solid((255, 236, 180, 255)), solid((255, 214, 130, 255)), rough=0.5)
    Ht = 2 * F.CHPX + 64
    # ---- free ground: plot minus all game buildings ----------------------------------------------------
    blds = []
    for f in glob.glob(str(ROOT / "data/build/bld/*.pkl")):
        for b in pickle.load(open(f, "rb")):
            g = [Polygon(np.array(p)[:, :2]).buffer(0) for k, p in b["polys"] if k == 0 and len(p) >= 3]
            if g and unary_union(g).distance(P0) < 1: blds.append(unary_union(g))
    BU = unary_union(blds).buffer(0.6) if blds else Polygon()
    FREE = P0.buffer(-0.7).difference(BU)
    loc = lambda g: localize(g, ox, oy); FREE = loc(FREE)
    def free_rect(x, y, ang, L, W, pad=0.2):
        cr, sr = math.cos(ang), math.sin(ang); h = [(-L / 2 - pad, -W / 2 - pad), (L / 2 + pad, -W / 2 - pad), (L / 2 + pad, W / 2 + pad), (-L / 2 - pad, W / 2 + pad)]
        return FREE.contains(Polygon([(x + a * cr - b * sr, y + a * sr + b * cr) for a, b in h]))
    used = []
    def claim(x, y, ang, L, W):
        if not free_rect(x, y, ang, L, W): return False
        r = Point(x, y).buffer(max(L, W) / 2 * 0.78)
        if any(r.intersects(u) for u in used): return False
        used.append(r); return True
    # gravel (4 m cells following the terrain), lane core darker
    cell = 4.0; minx, miny, maxx, maxy = FREE.bounds; n_g = 0
    for gx in np.arange(math.floor(minx / cell) * cell, maxx, cell):
        for gy in np.arange(math.floor(miny / cell) * cell, maxy, cell):
            q = FREE.intersection(sbox(gx, gy, gx + cell, gy + cell))
            for pg in polys_of(q):
                if pg.area < 0.3: continue
                zz = gl(pg.centroid.x, pg.centroid.y) + 0.05; lp = pg
                for tri in shapely.constrained_delaunay_triangles(lp).geoms:
                    cc = list(tri.exterior.coords)[:3]
                    if not lp.buffer(1e-6).contains(tri.representative_point()): continue
                    pts = [(x, y, zz) for x, y in cc]
                    if Polygon(cc).exterior.is_ccw is False: pts = pts[::-1]
                    m.tri(mg, pts, [(p[0] * 0.25, p[1] * 0.25) for p in pts], W4); n_g += 1
    # ---- Gerolds Markt building ---------------------------------------------------------------------------
    mk = loc(bid(IDS[0])["fp"]); H_MK = 8.6
    for pg in polys_of(mk):
        g0 = gl(pg.centroid.x, pg.centroid.y)
        for a, b in edges_of(pg, 0.6):
            L = math.hypot(b[0] - a[0], b[1] - a[1]); gz = gl((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            m.wall(mco, a, b, gz - 0.4, gz + H_MK, (3.0, 3.0), W4)
            if L >= 4:
                tt = ((b[0] - a[0]) / L, (b[1] - a[1]) / L); nn = (tt[1], -tt[0]); nb = max(1, int(L // 2.6)); bw = L / nb
                for k in range(nb):
                    P = lambda u, z: (a[0] + tt[0] * u + nn[0] * 0.05, a[1] + tt[1] * u + nn[1] * 0.05, z)
                    D._oriented(m, mgl, [P(k * bw + 0.15, gz + 0.1), P((k + 1) * bw - 0.15, gz + 0.1), P((k + 1) * bw - 0.15, gz + 3.3), P(k * bw + 0.15, gz + 3.3)], (nn[0], nn[1], 0), [(0, 0), (1, 0), (1, 1), (0, 1)], W4)
                    if L > 8 and k % 2 == 0 and gz + 6.0 < gz + H_MK: pass
        m.flat(mf, pg, g0 + H_MK, hexl("#6e7066"))
        for a, b in edges_of(pg, 0.6): D.band(m, mf, a, b, g0 + H_MK - 0.1, g0 + H_MK + 0.9, 0.15, hexl("#2c2f31"))
        longest = max(edges_of(pg, 0.6), key=lambda e: math.hypot(e[1][0] - e[0][0], e[1][1] - e[0][1]))
        a, b = longest; L = math.hypot(b[0] - a[0], b[1] - a[1]); tt = ((b[0] - a[0]) / L, (b[1] - a[1]) / L); nn = (tt[1], -tt[0]); gz = gl((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        P = lambda u, z, off=0.12: (a[0] + tt[0] * u + nn[0] * off, a[1] + tt[1] * u + nn[1] * off, z)
        D._oriented(m, ms, [P(L / 2 - 3.2, gz + 3.5), P(L / 2 + 3.2, gz + 3.5), P(L / 2 + 3.2, gz + 4.6), P(L / 2 - 3.2, gz + 4.6)], (nn[0], nn[1], 0), T.uvr("markt"), W4)
        cx, cy = pg.centroid.x, pg.centroid.y                                         # roof terrace: umbrellas + planters
        for k in range(5):
            ux, uy = cx + rng.uniform(-6, 6), cy + rng.uniform(-9, 9)
            if pg.buffer(-1.5).contains(Point(ux, uy)):
                m.cylinder(mf, ux, uy, 0.04, g0 + H_MK, g0 + H_MK + 2.4, n=6, col=hexl("#4a4038")); m.cylinder(mf, ux, uy, 1.5, g0 + H_MK + 2.2, g0 + H_MK + 2.7, n=10, col=hexl(UMB[k % 6]), r1=0.05, cap=None)
    # ---- containers (bars/kitchens): stacks along both sides of the lane ---------------------------------
    def cont(cx, cy, z0, rot, k):
        hl, hw = F.CL / 2, F.CW / 2; cr, sr = math.cos(rot), math.sin(rot)
        P = [(cx + x * cr - y * sr, cy + x * sr + y * cr) for x, y in [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]]
        col = hexl(F.COLS[k]); z1 = z0 + F.CH; cu0, cv0 = (k % 4) / 4, 1 - ((k // 4) + 1) * F.CHPX / Ht; dv = F.CHPX / Ht
        for i in range(4):
            a, b = P[i], P[(i + 1) % 4]
            if i in (0, 2): m.quad(ma, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], [(cu0, cv0), (cu0 + .25, cv0), (cu0 + .25, cv0 + dv), (cu0, cv0 + dv)], W4)
            else: m.wall(mf, a, b, z0, z1, (3, 3), tuple(int(v * .8) for v in col[:3]) + (255,))
        m.flat(mf, Polygon(P), z1, tuple(min(255, int(v * 1.1)) for v in col[:3]) + (255,))
    def deck(x, y, ang, L, W, h=0.3):
        cr, sr = math.cos(ang), math.sin(ang); pts = [(x + a * cr - b * sr, y + a * sr + b * cr) for a, b in [(-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2)]]
        g = gl(x, y); poly = Polygon(pts)
        m.extrude(mw, mw, poly, g, g + h, mod=(1.0, 1.0), col=W4, rcol=W4, roof=False); m.flat(mw, poly, g + h, W4, uvscale=0.5)
    tops = []; n_c = 0; stacks = [(18, -1, 2), (54, -1, 2), (66, 1, 3), (12, -1, 3), (30, -1, 2), (47, -1, 3), (63, -1, 2), (7, 1, 2), (58, 1, 3), (70, 1, 2), (22, 1, 3), (40, 1, 2)]
    for s, side, lv in stacks:
        for off in (7.2, 8.4, 6.0, 9.6):
            x, y, ang = lane_pt(s, side * off)
            if claim(x, y, ang, F.CL * 1.05, F.CW * 1.05 * (2 if lv == 3 else 1)):
                g = gl(x, y)
                for j in range(2 if lv == 3 else 1):                                   # two containers side by side on 3-level stacks
                    xx, yy = x - math.sin(ang) * (j - (0.5 if lv == 3 else 0)) * F.CW * 1.0, y + math.cos(ang) * (j - (0.5 if lv == 3 else 0)) * F.CW * 1.0
                    for z in range(lv if j == 0 else lv - 1): cont(xx, yy, g + 0.1 + z * F.CH, ang, int(rng.integers(0, 8))); n_c += 1
                tops.append((x, y, ang, g + 0.1 + lv * F.CH, 2.2 if lv == 3 else 0.0))
                dx, dy, _ = lane_pt(s, side * (off - 4.3)); 
                if claim(dx, dy, ang, 6.0, 3.0): deck(dx, dy, ang, 6.0, 3.0)
                break
    # raised terrace (north end, photo 6): deck 0.9 m high with posts + rail
    for s, off in ((66, 2.5), (66, -2.5), (60, 3.0), (70, 0.0)):
        x, y, ang = lane_pt(s, off)
        if claim(x, y, ang, 11.0, 6.0):
            deck(x, y, ang, 11.0, 6.0, 0.9); cr, sr = math.cos(ang), math.sin(ang); g = gl(x, y) + 0.9
            for u in np.arange(-5.5, 5.6, 1.1):
                for v in (-3.0, 3.0): m.box(mw, x + u * cr - v * sr, y + u * sr + v * cr, 0.07, 0.07, g, g + 1.0, col=hexl("#6a4a30"))
            for v in (-3.0, 3.0): m.box(mw, x - v * sr, y + v * cr, 11.0, 0.08, g + 1.0, g + 1.1, rot=ang, col=hexl("#6a4a30"))
            for k in range(3): cu = rng.uniform(-4, 4); cv = rng.uniform(-1.5, 1.5); ux, uy = x + cu * cr - cv * sr, y + cu * sr + cv * cr; m.cylinder(mf, ux, uy, 0.04, g, g + 2.3, n=6, col=hexl("#4a4038")); m.cylinder(mf, ux, uy, 1.4, g + 2.1, g + 2.6, n=10, col=hexl(UMB[(k + 2) % 6]), r1=0.05)
            break
    def stall(x, y, ang, col):
        cr, sr = math.cos(ang), math.sin(ang); g = gl(x, y); L, W = 3.2, 2.4
        for u, v in ((-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2)): m.box(mw, x + u * cr - v * sr, y + u * sr + v * cr, 0.12, 0.12, g, g + (2.5 if v < 0 else 2.0), col=hexl("#5a4632"))
        p = [(x + u * cr - v * sr, y + u * sr + v * cr) for u, v in ((-L / 2 - 0.2, -W / 2 - 0.2), (L / 2 + 0.2, -W / 2 - 0.2), (L / 2 + 0.2, W / 2 + 0.2), (-L / 2 - 0.2, W / 2 + 0.2))]
        zz = [g + 2.65, g + 2.65, g + 2.15, g + 2.15]; c_ = hexl(col)
        m.quad(mf, [(p[0][0], p[0][1], zz[0]), (p[1][0], p[1][1], zz[1]), (p[2][0], p[2][1], zz[2]), (p[3][0], p[3][1], zz[3])], col=c_)
        m.quad(mf, [(p[0][0], p[0][1], zz[0] - 0.05), (p[3][0], p[3][1], zz[3] - 0.05), (p[2][0], p[2][1], zz[2] - 0.05), (p[1][0], p[1][1], zz[1] - 0.05)], col=shade(c_, 0.6))
        m.wall(mw, (x + (-L / 2) * cr - (-W / 2) * sr, y + (-L / 2) * sr + (-W / 2) * cr), (x + (L / 2) * cr - (-W / 2) * sr, y + (L / 2) * sr + (-W / 2) * cr), g + 0.1, g + 2.4, (1.2, 1.2), W4)
        m.box(mw, x + 0.0 * cr - (W / 2 - 0.2) * sr, y + 0.0 * sr + (W / 2 - 0.2) * cr, L - 0.3, 0.5, g + 0.9, g + 1.0, rot=ang, col=hexl("#8a6a48"))
        for k in range(4): m.box(mf, x + (-1.0 + k * 0.7) * cr - (W / 2 - 0.2) * sr, y + (-1.0 + k * 0.7) * sr + (W / 2 - 0.2) * cr, 0.4, 0.3, g + 1.0, g + 1.3, rot=ang, col=hexl(["#c9482c", "#d9a526", "#4a7d56", "#d8d0b0"][k]))
    n_s = 0
    for s in np.arange(6, 76, 4.6):
        for side in (-1, 1):
            for off in (5.4, 6.8, 8.2, 9.8):
                x, y, ang = lane_pt(s + rng.uniform(-1, 1), side * off)
                if claim(x, y, ang, 3.4, 2.6):
                    stall(x, y, ang + (math.pi if side > 0 else 0), ["#b8352a", "#2f8a86", "#2e7d4f", "#d99a2b", "#2f5f94"][n_s % 5]); n_s += 1; break
    # ---- table sets, planters, shrubs -------------------------------------------------------------------
    def table(x, y, ang, umb):
        cr, sr = math.cos(ang), math.sin(ang); g = gl(x, y)
        m.box(mw, x, y, 1.8, 0.8, g + 0.72, g + 0.77, rot=ang, col=hexl("#8a6a48")); 
        for u in (-0.7, 0.7): m.box(mf, x + u * cr, y + u * sr, 0.08, 0.6, g, g + 0.72, rot=ang, col=hexl("#4a3a2a"))
        for v in (-0.75, 0.75): m.box(mw, x - v * sr, y + v * cr, 1.7, 0.3, g + 0.42, g + 0.47, rot=ang, col=hexl("#7a5a3c")); m.box(mf, x - v * sr, y + v * cr, 1.5, 0.08, g, g + 0.42, rot=ang, col=hexl("#4a3a2a"))
        if umb:
            col = hexl(UMB[int(rng.integers(0, 6))]); m.cylinder(mf, x, y, 0.04, g, g + 2.5, n=6, col=hexl("#4a4038")); m.cylinder(mf, x, y, 1.6, g + 2.2, g + 2.8, n=10, col=col, r1=0.05)
    def shrub(x, y, r, h, g=None):
        g = gl(x, y) if g is None else g; col = hexl(GREENS[int(rng.integers(0, 4))])
        m.cylinder(mf, x, y, 0.08, g, g + h * 0.4, n=6, col=hexl("#5a4632")); m.cylinder(mf, x, y, r, g + h * 0.3, g + h * 0.7, n=8, col=col, r1=r * 0.9); m.cylinder(mf, x, y, r * 0.9, g + h * 0.7, g + h, n=8, col=col, r1=0.1)
    for (x, y, ang, zt, wd) in tops:                                              # greenery on the container roofs
        for k in range(4):
            u = (k - 1.5) * 1.4; v = rng.uniform(-0.6, 0.6) + (0.0 if wd == 0 else rng.uniform(-1.0, 1.0)); shrub(x + u * math.cos(ang) - v * math.sin(ang), y + u * math.sin(ang) + v * math.cos(ang), 0.5 + rng.random() * 0.3, 0.9 + rng.random() * 0.7, g=zt)
    def planter(x, y, ang, L):
        cr, sr = math.cos(ang), math.sin(ang); g = gl(x, y)
        m.box(mw, x, y, L, 0.9, g, g + 0.6, rot=ang, col=hexl("#7a5a3c"), mr=mf, rcol=hexl("#4a3a2a"))
        for k in range(int(L // 0.9)):
            u = -L / 2 + 0.5 + k * 0.9; shrub(x + u * cr, y + u * sr, 0.4, 1.0 + rng.random() * 0.8) if False else m.cylinder(mf, x + u * cr, y + u * sr, 0.38, g + 0.6, g + 1.2 + rng.random() * 0.5, n=7, col=hexl(GREENS[int(rng.integers(0, 4))]), r1=0.1)
    n_t = 0
    for s in np.arange(4, 76, 2.8):
        for side in (-1, 1):
            for off in (3.0, 4.2, 5.4, 7.6, 9.0):
                x, y, ang = lane_pt(s + rng.uniform(-0.8, 0.8), side * (off + rng.uniform(-0.3, 0.3)))
                if claim(x, y, ang + math.pi / 2, 2.0, 2.2): table(x, y, ang, rng.random() < 0.7); n_t += 1; break
    n_p = 0
    for s in np.arange(3, 78, 2.6):
        for side in (-1, 1):
            x, y, ang = lane_pt(s, side * rng.uniform(9.5, 12.5))
            if rng.random() < 0.9 and claim(x, y, ang, 2.4, 1.2): planter(x, y, ang, 2.4); n_p += 1
            x, y, ang = lane_pt(s + 1.2, side * rng.uniform(2.0, 2.6))
            if rng.random() < 0.28 and claim(x, y, ang, 1.2, 1.2): shrub(x, y, 0.55 + rng.random() * 0.25, 1.4 + rng.random() * 0.8); n_p += 1
    # ---- string lights + bunting across the lane ----------------------------------------------------------
    fl = ["#d9362c", "#f0c02a", "#2f7fb8", "#3f9a4e", "#e8e4da", "#d4772a"]; n_b = 0
    for si, s in enumerate((4, 15, 26, 37, 48, 59, 70)):
        wid = 8.4 + rng.uniform(0, 2.5)
        A = lane_pt(s, -wid); B = lane_pt(s + rng.uniform(-2, 2), wid); za = gl(A[0], A[1]) + 4.9; zb = gl(B[0], B[1]) + 5.1
        for xy in (A, B): g = gl(xy[0], xy[1]); m.box(mw, xy[0], xy[1], 0.16, 0.16, g, g + 5.2, col=hexl("#5a4a3a"))
        kind = si % 2; N = 22
        def Q(f): return (A[0] + (B[0] - A[0]) * f, A[1] + (B[1] - A[1]) * f, za + (zb - za) * f - 1.3 * 4 * f * (1 - f))
        for i in range(N):
            p0, p1 = Q(i / N), Q((i + 1) / N)
            m.quad(mf, [(p0[0], p0[1], p0[2]), (p1[0], p1[1], p1[2]), (p1[0], p1[1], p1[2] + 0.05), (p0[0], p0[1], p0[2] + 0.05)], col=hexl("#2a2a2a")); m.quad(mf, [(p0[0], p0[1], p0[2] + 0.05), (p1[0], p1[1], p1[2] + 0.05), (p1[0], p1[1], p1[2]), (p0[0], p0[1], p0[2])], col=hexl("#2a2a2a"))
            if kind == 0:
                for ang_ in (0, math.pi / 2):
                    dx, dy = math.cos(ang_) * 0.16, math.sin(ang_) * 0.16
                    m.quad(ml, [(p0[0] - dx, p0[1] - dy, p0[2] - 0.34), (p0[0] + dx, p0[1] + dy, p0[2] - 0.34), (p0[0] + dx, p0[1] + dy, p0[2]), (p0[0] - dx, p0[1] - dy, p0[2])], col=W4); n_b += 1
            else:
                mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, p0[2] - 0.55); c_ = hexl(fl[i % 6])
                m.tri(mf, [p0, p1, mid], col=c_); m.tri(mf, [p1, p0, mid], col=c_)
    # ---- signposts + entrance gate with name board --------------------------------------------------------
    for s, off, names in ((14, 3.4, ("bar", "kueche")), (34, -3.2, ("grill", "bar")), (56, 3.2, ("kueche", "grill"))):
        x, y, ang = lane_pt(s, off); g = gl(x, y)
        if not claim(x, y, ang, 0.6, 0.6): continue
        m.box(mw, x, y, 0.14, 0.14, g, g + 3.0, col=hexl("#5a4632"))
        for j, nm in enumerate(names):
            zz = g + 2.9 - j * 0.55; cr, sr = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2); nx, ny = -math.sin(ang), math.cos(ang)
            q = lambda u, z, off_=0.1: (x + cr * u + nx * 0 + (math.cos(ang)) * off_, y + sr * u + math.sin(ang) * off_, z)
            a0 = (x - 0.9 * nx, y - 0.9 * ny, zz); b0 = (x + 0.9 * nx, y + 0.9 * ny, zz)
            for side_ in (1, -1):
                o = 0.09 * side_; d_ = (math.cos(ang) * o, math.sin(ang) * o); pa = (a0[0] + d_[0], a0[1] + d_[1]); pb = (b0[0] + d_[0], b0[1] + d_[1])
                if side_ < 0: pa, pb = pb, pa
                pts = [(pa[0], pa[1], zz - 0.25), (pb[0], pb[1], zz - 0.25), (pb[0], pb[1], zz + 0.25), (pa[0], pa[1], zz + 0.25)]
                D._oriented(m, ms, pts, (d_[0], d_[1], 0), [(0, 0.0), (1, 0.0), (1, 1), (0, 1)] if False else T.uvr(nm), W4)
    gx, gy, gang = lane_pt(1.5, 0.0); gg = gl(gx, gy); nx, ny = -math.sin(gang), math.cos(gang); tx, ty = math.cos(gang), math.sin(gang)
    for sd in (-1, 1): m.box(mw, gx + nx * 4.2 * sd, gy + ny * 4.2 * sd, 0.4, 0.4, gg, gg + 6.6, col=hexl("#6a4a30"), rot=gang)
    bl = (gx - tx * 0.0 - nx * 4.4, gy - ty * 0.0 - ny * 4.4); br = (gx + nx * 4.4, gy + ny * 4.4)
    m.box(mw, gx, gy, 0.35, 9.4, gg + 6.5, gg + 6.85, rot=gang, col=hexl("#6a4a30"))
    # the board faces south (against the lane direction)
    sx_, sy_ = -tx, -ty
    for sgn, off_ in ((-1, 0.0),):
        P = lambda u, z: (gx + nx * u + sx_ * 0.22, gy + ny * u + sy_ * 0.22, z)
        D._oriented(m, ms, [P(4.1, gg + 5.0), P(-4.1, gg + 5.0), P(-4.1, gg + 6.5), P(4.1, gg + 6.5)], (sx_, sy_, 0), T.uvr("gate"), W4)
        P2 = lambda u, z: (gx + nx * u - sx_ * 0.22, gy + ny * u - sy_ * 0.22, z)
        D._oriented(m, ms, [P2(-4.1, gg + 5.0), P2(4.1, gg + 5.0), P2(4.1, gg + 6.5), P2(-4.1, gg + 6.5)], (-sx_, -sy_, 0), T.uvr("gate"), W4)
    # chalk boards at the entrance
    for u in (-2.6, 2.6):
        P = lambda uu, z: (gx + nx * (u + uu) + sx_ * 0.6, gy + ny * (u + uu) + sy_ * 0.6, z)
        D._oriented(m, ms, [P(0.5, gg + 0.0), P(-0.5, gg + 0.0), P(-0.5, gg + 1.05), P(0.5, gg + 1.05)], (sx_, sy_, 0), T.uvr("chalk" if u < 0 else "cocktail"), W4)
    print(f"fgg: stalls {n_s}, gravel {n_g} tris, containers {n_c}, tables {n_t}, planters/shrubs {n_p}, bulbs {n_b}")
    assert m.tri_count() <= 30000
    finish(m, "frau_gerolds_garten", "Frau Gerolds Garten", ox, oy, oz, hide_pts(IDS))


if __name__ == "__main__":
    build()
