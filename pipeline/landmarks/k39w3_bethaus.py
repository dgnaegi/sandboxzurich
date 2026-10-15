"""Bethaus Wiedikon (Schlossgasse 10): yellow-ochre plaster, two floors of round-headed windows with white frames, slate hip roof and a slim
bell turret with pointed spire (swissBUILDINGS3D ridge ~23 m). research/v3/bethaus_wiedikon.md (Mapillary/Panoramax street views)"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def build():
    c = prep(["ID_0C263A8D"], 0.4); rng = np.random.default_rng(41); P = c.P; ring = c.ring
    m = Model("k39w3_bethaus")
    mw = m.mat("wall", plaster(hexc("#e2bb62"), seed=8, stains=0.04))
    ga = D.glass_atlas_g(frame="#f1ede0", glass="#2b3640", sky="#8aa0b0", cols=2, rows=3, seed=18, bar=3, lit_p=0.3, curtains=False)
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", D.ashlar(hexc("#c3bba9"), rows=6, rough=0.06, seed=3))
    PL, FH = 0.7, 3.4; z0 = PL; zE = z0 + 2 * FH + 0.6
    m.extrude(mf, mf, P, -3, PL, col=W4, roof=False, mod=(3, 1.4))
    st = dict(bayw=3.0, kind="arch", ww=1.0, wh=2.2, so=0.5, depth=0.25, surr=hexl("#f2eee2"), surr_w=0.12, sill=True,
              gf=dict(wh=2.4, so=0.4), bands=[(zE - 0.6, 0.6, 0.25, (240, 236, 224, 255))])
    facade(m, mw, mg, mf, ring, z0, 2, FH + 0.3, st, rng)
    A = P.buffer(0.5, join_style=2)
    taper(m, mf, A, zE, zE + 5.0, 0.3, hexl("#4a4c50"), cap=True)
    # bell turret on the longest edge
    li = max(range(len(ring)), key=lambda i: math.dist(ring[i], ring[(i + 1) % len(ring)]))
    a, b = ring[li], ring[(li + 1) % len(ring)]; L, t, n = D.frame_of(a, b)
    p = D.P3(a, t, n, L / 2, 0, -2.2); ang = math.atan2(t[1], t[0])
    box = Polygon([(p[0] + math.cos(ang) * dx - math.sin(ang) * dy, p[1] + math.sin(ang) * dx + math.cos(ang) * dy) for dx, dy in ((-1.5, -1.5), (1.5, -1.5), (1.5, 1.5), (-1.5, 1.5))])
    m.extrude(mw, mf, box, zE - 0.5, zE + 7.5, col=W4, rcol=hexl("#4a4c50"), mod=(3, 3))
    for k in range(4):   # belfry openings
        ang2 = ang + k * math.pi / 2; q = (p[0] + math.cos(ang2) * 1.52, p[1] + math.sin(ang2) * 1.52)
        m.box(mf, q[0], q[1], 0.1, 0.9, zE + 5.0, zE + 6.8, rot=ang2, col=hexl("#2b2f33"))
    taper(m, mf, box.buffer(0.2, join_style=2), zE + 7.5, zE + 7.5 + 11.5, 0.02, hexl("#4f5a52"), cap=False)
    finish39(m, "k39w3_bethaus", "Bethaus Wiedikon", c.ox, c.oy, c.oz, c.hide)


if __name__ == "__main__":
    build()
