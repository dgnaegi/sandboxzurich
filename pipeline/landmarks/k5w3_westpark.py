"""Westpark / Galaxus (Pfingstweidstrasse 60, Kreis 5): 8-storey office complex, light-grey precast concrete frame (slim piers, deep spandrels),
tall metal-framed window fields with dark louvre panels, glazed ground floor, parapet band. Photos: research/v3/westpark.md."""
from k5w3_kit import *

IDS = ["ID_89288E1A", "ID_5D25DB62"]


def build():
    setup()
    U = unary_union([bid(p)["fp"] for p in IDS]); c = U.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    m = Model("westpark"); rng = np.random.default_rng(9)
    mw = m.mat("wall", tex_concrete("#aeb0ab", panel=(2, 2), seed=4), rough=0.95)
    ga = D.glass_atlas_g(frame="#8d9294", glass="#2a3844", sky="#8fa9bb", cols=3, rows=2, seed=3, lit_p=0.3, curtains=True,
                         sign=text_painter([(0, 1024, "WESTPARK", "#e8e8e4", "#3a3c3e", None)], size=22))
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W4))
    PIER = hexl("#9a9c97"); hide = []
    for p in IDS:
        v = [(z - oz, localize(g, ox, oy)) for z, g in volumes(p)]
        for z0, z1, S, R in bands(v, -3.0):
            for S1 in polys_of(S):
                def hole(u0, u1, f0, f1, fi, L):
                    uc = (u0 + u1) / 2; w = (u1 - u0) - 0.55; return D.rect_pts(uc - w / 2, f0 + 0.45, uc + w / 2, f0 + 2.95)
                def egh(u0, u1, f0, f1, fi, L):
                    return D.rect_pts(u0 + 0.3, f0 + 0.15, u1 - 0.3, f0 + 3.9)
                facade(m, (mw, mg, mf), S1, z0, z1, None, fh=3.55, bayw=3.4, hole=hole, depth=0.35, wall_col=W4, reveal_col=PIER, rng=rng, wmod=(3.0, 3.0),
                       eg_h=4.6 if z0 < 0.5 else None, eg_hole=egh, base=-3.0, cornice=(hexl("#8f918c"), 0.25, 0.5), deep_z=5.0)
                roofs(m, mf, S1.difference(unary_union([g for z, g in v if z > z1 + 1e-6]).buffer(0.05)) if any(z > z1 + 1e-6 for z, g in v) else S1, z1, hexl("#7c7e7a"))
        hide += hide_pts([p])
    finish(m, "westpark", "Westpark (Galaxus)", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
