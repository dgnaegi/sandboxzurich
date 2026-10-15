"""Zum Froschauer (Wiedikon, Birmensdorferstr./Gertrudstr. block): light-grey concrete frame, vertical piers, louvred ribbon bands, louvre doors
on the ground floor, stepped roofs from the swissBUILDINGS3D roof classes. research/v3/froschauer.md"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
from k39w3_kit import *


def build():
    c = prep(["ID_CB87E366"], 0.6); rng = np.random.default_rng(51)
    parts = roof_parts("CB87E366", c.ox, c.oy, c.oz, step=3.0, min_area=60)
    m = Model("k39w3_froschauer")
    mw = m.mat("wall", panels("#cfcdc6", nx=2, ny=3, gap="#a9a7a0", seed=5, amp=2))
    ga = D.glass_atlas_g(frame="#bfc2c4", glass="#35424b", sky="#93a8b6", cols=3, rows=5, seed=23, bar=2, lit_p=0.3, curtains=False)
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", panels("#d6d5d0", nx=2, ny=2, gap="#9b9a95", seed=3))
    PL = 0.4
    for pi, (poly, h) in enumerate(parts):
        hi = [q for q, hh in parts if hh > h + 0.5]
        nf = max(1, int(round((h - PL) / 3.5))); fh = (h - PL) / nf
        ring = list(poly.exterior.coords)[:-1]
        def edge(i, a, b, L, hi=hi):
            if L < 3.5: return "blind"
            mid = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if any(q.buffer(0.3).contains(mid) for q in hi): return "blind"
            return None
        st = dict(bayw=6.8, kind="rect", ww=0.86, wh=0.6, so=0.3, depth=0.2, surr=None, sill=False, edge=edge,
                  gf=dict(wh=0.82, so=0.0, ww=0.8, surr=None), bands=[(h - 0.5, 0.5, 0.12, (225, 224, 218, 255))])
        m.extrude(mf, mf, poly, -3, PL, col=W4, roof=False)
        facade(m, mw, mg, mf, ring, PL, nf, fh, st, rng)
        top = poly
        for q in hi: top = top.buffer(0).difference(q.buffer(0.05).buffer(0))
        if not top.is_empty:
            for g in ([top] if top.geom_type == "Polygon" else list(top.geoms)):
                if g.area > 2: m.flat(mf, g, h, hexl("#6b6e70"))
        corner_pilasters(m, mf, ring, PL, h, 0.5, hexl("#d6d5d0"))
    finish39(m, "k39w3_froschauer", "Zum Froschauer", c.ox, c.oy, c.oz, c.hide)


if __name__ == "__main__":
    build()
