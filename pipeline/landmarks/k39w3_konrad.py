"""Kirche St. Konrad (Fellenbergstrasse 231b, Albisrieden): 1950s church hall with tall narrow vertical windows under a low roof, slender
sand-coloured concrete bell tower (~38 m) with a grid of slit openings and a cross. research/v3/st_konrad.md"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def build():
    c = prep(["ID_CA9A6315"], 0.8); rng = np.random.default_rng(81); P = c.P; ring = c.ring
    ct = prep(["ID_6861C12E"], 0.3)
    tx, ty = ct.ox - c.ox, ct.oy - c.oy
    m = Model("k39w3_konrad")
    mw = m.mat("wall", plaster(hexc("#d8c9a2"), seed=14, stains=0.035, amp=3))
    ga = D.glass_atlas_g(frame="#9a9385", glass="#2a3844", sky="#8ba2b4", cols=2, rows=5, seed=51, bar=2, lit_p=0.45, curtains=False)
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", D.ashlar(hexc("#c9bda0"), rows=6, rough=0.05, seed=8))
    PL, EV = 0.5, 6.8; zE = PL + EV
    m.extrude(mf, mf, P, -3, PL, col=W4, roof=False, mod=(3, 1.4))
    st = dict(bayw=3.4, kind="rect", ww=0.34, wh=0.72, so=0.2, depth=0.25, surr=hexl("#efe8d4"), surr_w=0.1, sill=False,
              bands=[(zE - 0.4, 0.4, 0.3, (232, 222, 196, 255))])
    facade(m, mw, mg, mf, ring, PL, 1, EV, st, rng)
    taper(m, mf, P.buffer(0.5, join_style=2), zE, zE + 3.8, 0.55, hexl("#8a5c4a"), cap=True)
    # bell tower
    tring = [(x + tx, y + ty) for x, y in ct.ring]; tp = Polygon(tring)
    TH = 36.5
    tst = dict(bayw=1.5, kind="rect", ww=0.4, wh=0.62, so=0.7, depth=0.4, surr=None, sill=False,
               bands=[(TH - 0.7, 0.7, 0.2, (226, 214, 186, 255))])
    facade(m, mw, mg, mf, tring, PL, 15, (TH - PL) / 15, tst, rng, minL=1.0)
    m.extrude(mw, mf, tp.buffer(0.2, join_style=2), TH, TH + 0.8, col=(226, 214, 186, 255), rcol=hexl("#8d8a82"), roof=True)
    cx_, cy_ = tp.centroid.x, tp.centroid.y
    m.box(mf, cx_, cy_, 0.3, 0.3, TH + 0.8, TH + 4.0, col=hexl("#35373a")); m.box(mf, cx_, cy_, 0.3, 1.6, TH + 2.6, TH + 3.0, col=hexl("#35373a"))
    finish39(m, "k39w3_konrad", "Kirche St. Konrad Albisrieden", c.ox, c.oy, c.oz, c.hide + ct.hide)


if __name__ == "__main__":
    build()
