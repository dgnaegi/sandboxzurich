"""Volkshaus Zuerich (Stauffacherstrasse 60 / Helvetiaplatz), 1910 Heimatstil. Salmon plaster, EG round-arched windows in stone
surrounds, floor 1 large pair windows, floor 2 smaller, attic with three-arch loggia, balcony over centre, wide hip roof on corbels,
round tower at the right corner, lettering on the wall (VOLKSHAUS, RESTAURANT, CAFE BAR). Photos: research/v3/volkshaus.md."""
import math
from PIL import Image
from common import *
from lm import *
import detail as D
from shapely.geometry import Polygon, Point


def plaster(color, seed=3, size=128, stains=0.04):
    rng = np.random.default_rng(seed)
    a = np.full((size, size, 4), 255, np.uint8); a[..., :3] = color[:3]
    n = rng.normal(0, 3, (size, size, 1)); a[..., :3] = np.clip(a[..., :3] + n, 0, 255).astype(np.uint8)
    for _ in range(10):
        x, y, r = rng.integers(0, size), rng.integers(0, size), rng.integers(10, 30); f = 1 + rng.normal(0, stains)
        yy, xx = np.ogrid[:size, :size]; mk = ((xx - x) ** 2 + (yy - y) ** 2) < r * r
        a[mk, :3] = np.clip(a[mk, :3] * f, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def slate(size=64):
    a = np.zeros((size, size, 4), np.uint8); a[..., 3] = 255
    base = np.array([62, 63, 70]); rng = np.random.default_rng(2)
    for r in range(0, size, 8):
        for c in range(0, size, 8):
            a[r:r + 8, c:c + 8, :3] = np.clip(base + rng.normal(0, 4), 0, 255)
        a[r, :, :3] = (base * 0.7).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def front_edge(ring, tgt):
    best = None
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]; L, t, n = D.frame_of(a, b)
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); dt = (tgt[0] - mid[0], tgt[1] - mid[1]); dn = math.hypot(*dt)
        sc = L * max(0, (n[0] * dt[0] + n[1] * dt[1]) / dn)
        if best is None or sc > best[0]: best = (sc, i)
    return best[1]


def build():
    B = bid("ID_B4A079F1")
    P = outline(B["fp"], 0.5)
    c = P.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    Pl = orient(localize(P, ox, oy), 1.0)
    rng = np.random.default_rng(11)
    m = Model("volkshaus")
    WALL = hexc("#c46f58")
    mw = m.mat("wall", plaster(WALL))
    # 3 glass atlases cannot exceed 3 materials (wall, glass, flat) -> one glass atlas: 4x3 grid; EG variant via cols
    sign = D.letters_strip([(0, 480, "VOLKSHAUS", "#e6dcc8", "#c46f58", None), (480, 760, "RESTAURANT", "#3a2a26", "#c46f58", None),
                            (760, 1024, "CAFE BAR", "#3a2a26", "#c46f58", None)], size=26)
    ga = D.glass_atlas_g(frame="#f1ece0", glass="#26323d", sky="#8fa9bb", cols=4, rows=3, seed=5, sign=sign, lit_p=0.4)
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", solid((255, 255, 255, 255)))
    STONE, CREAM, SURR, SLATE = D.hexl("#9a948a"), D.hexl("#d2c6ae"), D.hexl("#bdb09a"), D.hexl("#3c3e45")
    W = (255, 255, 255, 255)
    G0, F1, F2, FA = 5.6, 4.6, 3.9, 3.3
    z1 = 0.9 + G0; z2 = z1 + F1; z3 = z2 + F2; zc = z3 + FA
    ring = list(Pl.exterior.coords)[:-1]; ne = len(ring)
    fi = front_edge(ring, (783 - ox, -881 - oy))
    m.extrude(mf, mf, Pl, -3, 0.9, col=STONE, roof=False)

    def run(a, b, zb, fh, bayw, fn, depth, surr_w, sill, isfront):
        L, t, n = D.frame_of(a, b); nb = max(1, int(round(L / bayw))); bw = L / nb
        for i in range(nb):
            u0, u1 = i * bw, (i + 1) * bw
            hole = fn(u0, u1, zb, zb + fh, i, nb, L)
            if hole is None:
                D.poly_wall(m, mw, Polygon(D.rect_pts(u0, zb, u1, zb + fh)), a, t, n, 0.0, W, lambda u, z: (u / 4, z / 4)); continue
            dep = depth(i, nb, L) if callable(depth) else depth
            D.bay(m, mw, mg, mf, a, t, n, u0, u1, zb, zb + fh, hole, dep, int(rng.integers(0, D.NV)), W, SURR, (4.0, 4.0), None)
            if surr_w: D.surround(m, mf, a, t, n, hole, surr_w, SURR, 0.05, sill)

    def eg(u0, u1, f0, f1, i, nb, L):
        uc = (u0 + u1) / 2; w = min(3.3, (u1 - u0) - 1.2)
        return D.arch_pts(uc - w / 2, f0 + 0.55, uc + w / 2, f0 + 3.1)

    def upper(h, w0=3.3, lo=0.8):
        def f(u0, u1, f0, f1, i, nb, L):
            uc = (u0 + u1) / 2; w = min(w0, (u1 - u0) - 1.3)
            return D.rect_pts(uc - w / 2, f0 + lo, uc + w / 2, f0 + lo + h)
        return f

    def attic(isfront):
        def f(u0, u1, f0, f1, i, nb, L):
            uc = (u0 + u1) / 2
            if isfront and abs(uc - L / 2) < 6.6:      # three-arch loggia in the middle
                w = 3.4; return D.arch_pts(uc - w / 2, f0 + 0.55, uc + w / 2, f0 + 1.45)
            w = min(2.0, (u1 - u0) - 1.3); return D.rect_pts(uc - w / 2, f0 + 0.7, uc + w / 2, f0 + 2.3)
        return f

    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b); fr = i == fi
        if L < 1.8: m.wall(mw, a, b, 0.9, zc, (4, 4), W); continue
        run(a, b, 0.9, G0, 6.1, eg, 0.45, 0.32, 0.0, fr)
        run(a, b, z1, F1, 6.1, upper(3.0, 3.3, 0.8), 0.3, 0.26, 0.14, fr)
        run(a, b, z2, F2, 6.1, upper(2.2, 3.3, 0.8), 0.3, 0.24, 0.14, fr)
        run(a, b, z3, FA, 6.1, attic(fr), lambda i_, nb, L_: 1.1 if fr and abs((i_ + .5) * L_ / nb - L_ / 2) < 6.6 else 0.3, 0.2, 0.0, fr)
        D.band(m, mf, a, b, z1 - 0.2, z1 + 0.15, 0.1, CREAM)
        D.band(m, mf, a, b, zc - 0.5, zc + 0.05, 0.25, CREAM)
        # eaves: slate-grey fascia + corbels
        for k in range(int(L // 1.9)):
            u = 1.0 + k * (L - 2.0) / max(1, int(L // 1.9) - 1)
            p = D.P3(a, t, n, u, 0, 0.45); ang = math.atan2(t[1], t[0])
            m.box(mf, p[0], p[1], 0.16, 0.8, zc - 1.5, zc - 0.5, rot=ang + math.pi / 2 * 0, col=D.hexl("#6b5a4c"))
    # facade features on the front edge
    a, b = ring[fi], ring[(fi + 1) % ne]; L, t, n = D.frame_of(a, b); ang = math.atan2(t[1], t[0]); u = L / 2
    # first-floor balcony (cast-iron rail) over the centre
    bw_ = 9.0; zb = z1 - 0.05
    D.band(m, mf, D.P3(a, t, n, u - bw_ / 2, 0)[:2], D.P3(a, t, n, u + bw_ / 2, 0)[:2], zb - 0.3, zb + 0.1, 1.1, D.hexl("#a29c90"))
    for k in range(5):
        p = D.P3(a, t, n, u - bw_ / 2 + 0.5 + k * (bw_ - 1) / 4, 0, 0.45)
        m.box(mf, p[0], p[1], 0.35, 0.5, zb - 1.2, zb - 0.3, rot=ang, col=D.hexl("#a29c90"))
    iron = D.hexl("#2f302f")
    for k in range(int(bw_ / 0.3)):
        p = D.P3(a, t, n, u - bw_ / 2 + 0.15 + k * 0.3, 0, 1.0); m.box(mf, p[0], p[1], 0.03, 0.03, zb + 0.1, zb + 1.05, rot=ang, col=iron)
    for zz in (zb + 0.12, zb + 1.05):
        p = D.P3(a, t, n, u, 0, 1.05); m.box(mf, p[0], p[1], bw_, 0.05, zz, zz + 0.05, rot=ang, col=iron)
    # lettering (atlas strip regions)
    def txt(u0, u1, zc_, h, x0, x1, off=0.07):
        p0 = D.P3(a, t, n, u0, zc_, off); p1 = D.P3(a, t, n, u1, zc_, off); v0, v1 = 0.0, 0.25
        m.quad(mg, [p0, p1, (p1[0], p1[1], zc_ + h), (p0[0], p0[1], zc_ + h)], [(x0 / 1024, v0), (x1 / 1024, v0), (x1 / 1024, v1), (x0 / 1024, v1)], n=(n[0], n[1], 0))
    txt(u - 5.2, u + 0.6, z2 - 0.95, 0.75 * 0.0 + 0.8, 0, 480)
    txt(L * 0.22 - 2.2, L * 0.22 + 2.2, z1 - 0.95, 0.5, 480, 760)
    txt(L * 0.80 - 2.0, L * 0.80 + 2.0, z1 - 0.95, 0.5, 760, 1024)
    # round tower at the right (b) corner
    tc = (b[0] - t[0] * 1.9 - n[0] * 1.6, b[1] - t[1] * 1.9 - n[1] * 1.6)
    m.cylinder(mw, tc[0], tc[1], 2.5, z2, zc + 3.4, n=20, mod=(4, 4), col=D.hexl("#d08a72"), cap=mf, capcol=D.hexl("#b9ae9a"))
    # hip roof with overhang (shallow skirt, then main hip)
    A = Pl.buffer(1.4, join_style=2)
    q1 = taper(m, mf, A, zc + 0.05, zc + 1.9, 0.94, SLATE, cap=False)
    q2 = taper(m, mf, q1, zc + 1.9, zc + 10.2, 0.2, D.hexl("#202226"), cap=True)
    for fx, fy in [(0.3, 0.15), (-0.28, -0.2)]:
        px, py = q2.centroid.x + fx * (q2.bounds[2] - q2.bounds[0]), q2.centroid.y + fy * (q2.bounds[3] - q2.bounds[1])
        m.box(mf, px, py, 1.1, 1.1, zc + 8.0, zc + 11.2, col=D.hexl("#9a5a45")); m.box(mf, px, py, 1.4, 1.4, zc + 11.2, zc + 11.5, col=D.hexl("#5a5a58"))
    hide = [[round(p.x, 1), round(p.y, 1)] for p in (g_.representative_point() for g_ in (B["fp"].geoms if hasattr(B["fp"], "geoms") else [B["fp"]]))]
    finish(m, "volkshaus", "Volkshaus", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
