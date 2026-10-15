"""Restaurant Krone, Lindenplatz Altstetten (Badenerstrasse 705): 3 floors, white plaster, blue shutters, stone ground floor with entrance stair,
black mansard hip roof with dormers. research/v3/lindenplatz_krone.md"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def build():
    c = prep(["ID_E9541A51"], 0.4); rng = np.random.default_rng(12); P = c.P; ring = c.ring
    m = Model("k39w3_krone")
    mw = m.mat("wall", plaster(hexc("#ece8dc"), seed=3, stains=0.03))
    sign = strip([(0, 1024, "RESTAURANT KRONE", "#2a2a2a", "#e6e1d2", None)], size=22, gap_max=3)
    ga = D.glass_atlas_g(frame="#f4f1e8", glass="#2a343e", sky="#8aa0b0", cols=2, rows=3, seed=4, bar=3, lit_p=0.35, sign=sign,
                         curtain_cols=[(236, 228, 210), (240, 236, 226), (200, 120, 100)])
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", D.ashlar(hexc("#cfcbc0"), rows=6, rough=0.05, seed=4))
    SH = hexl("#2f55b8"); PL, FH = 0.9, 3.0
    li = max(range(len(ring)), key=lambda i: math.dist(ring[i], ring[(i + 1) % len(ring)]))
    stone = hexl("#8e8b84")
    m.extrude(mf, mf, P, -3, PL, col=stone, roof=False, mod=(3, 1.4))
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]; L, t, n = D.frame_of(a, b)
        if L < 1.5: m.wall(mw, a, b, PL, PL + 3 * FH, (4, 4), W4); continue
        # ground floor in stone (lower band), windows with shutters on all floors
        nb = max(1, int(round(L / 2.3))); bw = L / nb
        for f in range(3):
            fb = PL + f * FH
            for k in range(nb):
                u0, u1 = k * bw, (k + 1) * bw; uc = (u0 + u1) / 2
                hole = D.rect_pts(uc - 0.45, fb + 0.75, uc + 0.45, fb + 2.35)
                if f == 0:
                    D.bay(m, mf, mg, mf, a, t, n, u0, u1, fb, fb + FH, hole, 0.22, int(rng.integers(0, D.NV)), hexl("#b9b4a6"), hexl("#8e8b84"), (3, 3), None)
                else:
                    D.bay(m, mw, mg, mf, a, t, n, u0, u1, fb, fb + FH, hole, 0.22, int(rng.integers(0, D.NV)), W4, hexl("#cfc9b8"), (4, 4), None)
                    shutters(m, mf, a, t, n, hole, SH, 0.42, 0.07)
                D.surround(m, mw, a, t, n, hole, 0.08, (240, 238, 230, 255), 0.04, sill=0.07)
        D.band(m, mw, a, b, PL + 3 * FH - 0.35, PL + 3 * FH + 0.1, 0.25, (240, 238, 230, 255))
        if i == li:   # entrance with natural-stone stairs and railing, restaurant sign
            uc = L / 2 + 1.0
            for k in range(4):
                p = D.P3(a, t, n, uc, 0.2 + 0.2 * k, 0.3 + (3 - k) * 0.28)
                m.box(mf, p[0], p[1], 2.6, 0.3 * (4 - k) * 0.0 + 0.6 + 0.3 * (3 - k) * 0.0, 0, PL * (k + 1) / 4, rot=math.atan2(t[1], t[0]), col=stone)
            sw = 5.0; sh_ = sw * 32 / 1024 * 6
            m.quad(mg, [D.P3(a, t, n, uc - sw / 2, PL + 3.0 + 0.1, 0.12), D.P3(a, t, n, uc + sw / 2, PL + 3.0 + 0.1, 0.12), D.P3(a, t, n, uc + sw / 2, PL + 3.7, 0.12), D.P3(a, t, n, uc - sw / 2, PL + 3.7, 0.12)],
                   [(0.37, 0.0), (0.63, 0.0), (0.63, 0.25), (0.37, 0.25)], n=(n[0], n[1], 0))
    # mansard: steep lower band, shallow upper band, dormers
    zE = PL + 3 * FH
    q1 = taper(m, mf, P.buffer(0.35, join_style=2), zE, zE + 2.6, 0.8, hexl("#4b4d52"), cap=False)
    q2 = taper(m, mf, q1, zE + 2.6, zE + 3.6, 0.45, hexl("#4b4d52"), cap=True)
    for k in range(2):
        pass
    finish39(m, "k39w3_krone", "Restaurant Krone Altstetten", c.ox, c.oy, c.oz, c.hide)


if __name__ == "__main__":
    build()
