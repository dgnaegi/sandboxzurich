"""Kirche Buehl (Goldbrunnenstrasse 54, Wiedikon, neo-Gothic): salmon-red clinker walls with sandstone surrounds, tall pointed windows, nave under
a slate hip roof, clock tower at the west front with a copper-green spire (~52 m, swissBUILDINGS3D). research/v3/kirche_buehl.md"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def build():
    c = prep(["ID_D4C1DE55"], 1.2); rng = np.random.default_rng(71); P = c.P; ring = c.ring
    m = Model("k39w3_buehl")
    mw = m.mat("wall", clinker((196, 124, 98), seed=4, rows=28))
    ga = D.glass_atlas_g(frame="#d9cfb8", glass="#2a3a4a", sky="#7f9ab0", cols=2, rows=4, seed=41, bar=3, lit_p=0.35, curtains=False,
                         transom=0.25)
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", D.ashlar(hexc("#d3c3a0"), rows=7, rough=0.06, seed=6))
    PL, EV = 0.9, 11.0; zE = PL + EV
    m.extrude(mf, mf, P, -3, PL, col=W4, roof=False, mod=(3, 1.4))
    st = dict(bayw=4.4, kind="pointed", ww=1.25, wh=6.2, so=1.4, depth=0.3, surr=hexl("#e4d6b4"), surr_w=0.18, sill=True,
              bands=[(PL + 0.0, 0.5, 0.1, (214, 196, 160, 255)), (zE - 0.5, 0.5, 0.35, (224, 208, 176, 255))])
    facade(m, mw, mg, mf, ring, PL, 1, EV, st, rng)
    corner_pilasters(m, mf, ring, PL, zE, 0.7, hexl("#e0d2b0"))
    taper(m, mf, P.buffer(0.35, join_style=2), zE, zE + 7.5, 0.5, hexl("#4b4f55"), cap=True)
    # clock tower at the front (+y), square 6 x 6, belfry stage, pyramidal copper spire
    tx, ty = 7.0, 13.0; TW = 3.2
    tp = Polygon([(tx - TW, ty - TW), (tx + TW, ty - TW), (tx + TW, ty + TW), (tx - TW, ty + TW)])
    m.extrude(mw, mf, tp, PL, 34.0, col=W4, rcol=hexl("#4b4f55"), mod=(4, 4))
    for z0_, z1_ in ((11.0, 12.0), (24.0, 24.8)): D.band(m, mf, *[(tx - TW, ty - TW), (tx + TW, ty - TW)], z0_, z1_, 0.3, (224, 208, 176, 255)) if False else None
    for k in range(4):
        ang = k * math.pi / 2; nx_, ny_ = math.cos(ang), math.sin(ang)
        cx_, cy_ = tx + nx_ * (TW + 0.05), ty + ny_ * (TW + 0.05)
        m.box(mf, cx_, cy_, 0.15, 1.9, 27.0, 32.0, rot=ang, col=hexl("#2a2f33"))     # belfry louvres
        m.box(mf, cx_, cy_, 0.2, 2.6, 31.7, 32.0, rot=ang, col=hexl("#e4d6b4"))
        m.box(mf, cx_, cy_, 0.18, 2.4, 20.0, 22.4, rot=ang, col=hexl("#e4d6b4"))     # clock stage frame
        m.box(mf, cx_ + nx_ * 0.1, cy_ + ny_ * 0.1, 0.08, 1.9, 20.2, 22.2, rot=ang, col=hexl("#f4f0e4"))
    taper(m, mf, tp.buffer(0.4, join_style=2), 34.0, 34.0 + 17.5 + PL - 0.9, 0.03, hexl("#5f8e79"), cap=False)
    finish39(m, "k39w3_buehl", "Kirche Buehl Wiedikon", c.ox, c.oy, c.oz, c.hide)


if __name__ == "__main__":
    build()
