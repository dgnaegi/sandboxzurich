"""Wohnhochhaus Altstetten (20 floors, ~65 m, near Vulkanstrasse): beige exposed-concrete grid facade with deep punched square windows,
tall glazed base with columns, flat roof with crown parapet. research/v3/hochhaus_altst64.md"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def build():
    c = prep(["ID_2F7262AB"], 0.5); rng = np.random.default_rng(61); P = c.P; ring = c.ring
    m = Model("k39w3_hochhaus_vulkan")
    mw = m.mat("wall", plaster(hexc("#cdbf9f"), seed=11, stains=0.025, amp=2))
    ga = D.glass_atlas_g(frame="#7c786f", glass="#303c46", sky="#9bb0be", cols=2, rows=2, seed=33, bar=3, lit_p=0.4,
                         curtain_cols=[(236, 228, 210), (205, 205, 200), (190, 180, 160), (160, 175, 190)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", panels("#c4b898", nx=2, ny=2, gap="#9f9578", seed=4))
    GF, FH, NF = 4.6, 3.2, 19; PL = 0.3; zE = PL + GF + NF * FH
    st = dict(bayw=3.6, kind="rect", ww=0.62, wh=0.66, so=0.5, depth=0.55, surr=None, sill=False,
              gf=dict(kind="rect", ww=0.9, wh=0.8, so=0.2, depth=0.4))
    m.extrude(mf, mf, P, -3, PL, col=W4, roof=False)
    # base floor taller than the regular floors
    facade(m, mw, mg, mf, ring, PL, 1, GF, dict(st, top=None, gf=None, kind="rect", ww=0.9, wh=0.8, so=0.25, depth=0.4, bands=[(PL + GF - 0.4, 0.4, 0.2, (190, 178, 150, 255))]), rng)
    facade(m, mw, mg, mf, ring, PL + GF, NF, FH, dict(st, gf=None), rng)
    corner_pilasters(m, mf, ring, PL, zE, 0.9, W4)
    m.extrude(mw, mf, P, zE, zE + 1.0, col=(205, 192, 160, 255), rcol=hexl("#6c6a66"), roof=True)
    A = P.buffer(-2.5, join_style=2)
    if not A.is_empty and A.geom_type == "Polygon": m.extrude(mw, mf, A, zE + 1.0, zE + 4.0, col=(190, 178, 150, 255), rcol=hexl("#6c6a66"))
    finish39(m, "k39w3_hochhaus_vulkan", "Wohnhochhaus Altstetten (Vulkanstrasse)", c.ox, c.oy, c.oz, c.hide)


if __name__ == "__main__":
    build()
