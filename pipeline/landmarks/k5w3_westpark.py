"""Westpark / Galaxus (Pfingstweidstrasse 60, Kreis 5): 8-storey office complex, light-grey precast concrete frame (slim piers, deep spandrels),
tall metal-framed window fields with dark louvre panels, glazed ground floor, parapet band. Photos: research/v3/westpark.md."""
from k5w3_kit import *

IDS = ["ID_89288E1A", "ID_5D25DB62"]


def build():
    setup()
    U = unary_union([bid(p)["fp"] for p in IDS]); c = U.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    m = Model("westpark"); rng = np.random.default_rng(9)
    mw = m.mat("wall", tex_concrete("#b4b8bc", panel=(2, 2), seed=4), rough=0.95)
    ga = D.glass_atlas_g(frame="#b4b8bc", glass="#6a7d90", sky="#c5d6e4", cols=2, rows=2, seed=3, lit_p=0.05, curtains=False,
                         sign=text_painter([(0, 1024, "DIGITEC GALAXUS", "#f2f2ee", "#2a2c2e", (200, 200, 190))], size=22))
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W4))
    PIER = hexl("#a9adb1"); hide = []
    for p in IDS:
        v = [(z - oz, localize(g, ox, oy)) for z, g in volumes(p)]
        for z0, z1, S, R in bands(v, -3.0):
            for S1 in polys_of(S):
                def hole(u0, u1, f0, f1, fi, L):
                    uc = (u0 + u1) / 2; w = min(2.3, (u1 - u0) - 0.25); return D.rect_pts(uc - w / 2, f0 + 0.55, uc + w / 2, f0 + 3.15)
                def egh(u0, u1, f0, f1, fi, L):
                    return D.rect_pts(u0 + 0.3, f0 + 0.15, u1 - 0.3, f0 + 3.9)
                facade(m, (mw, mg, mf), S1, z0, z1, None, fh=3.9, bayw=2.7, hole=hole, depth=0.25, wall_col=W4, reveal_col=PIER, rng=rng, wmod=(3.0, 3.0), floor_bands=(hexl('#b4b8bc'), 0.1, 0.4),
                       eg_h=4.5 if z0 < 0.5 else None, eg_hole=egh, base=-3.0, cornice=(hexl("#8f918c"), 0.25, 0.5), deep_z=3.0)
                roofs(m, mf, S1.difference(unary_union([g for z, g in v if z > z1 + 1e-6]).buffer(0.05)) if any(z > z1 + 1e-6 for z, g in v) else S1, z1, hexl("#7c7e7a"))
        hide += hide_pts([p])
    # entrance Pfingstweidstrasse 60b: canopy + lettering on the edge closest to the address point
    tx, ty = -137 - ox, 730 - oy; best = None
    for pp in IDS:
        for S1 in polys_of(localize(bid(pp)["fp"], ox, oy)):
            for a, b in edges_of(S1, 6.0):
                L, t, n = D.frame_of(a, b); d = Point((a[0] + b[0]) / 2, (a[1] + b[1]) / 2).distance(Point(tx, ty))
                if best is None or d < best[0]: best = (d, a, b)
    _, a, b = best; L, t, n = D.frame_of(a, b); u = L / 2
    D.band(m, mf, D.P3(a, t, n, u - 5, 0)[:2], D.P3(a, t, n, u + 5, 0)[:2], 4.7, 5.0, 2.2, hexl("#7d807c"))
    sign_quad(m, mg, a, t, n, u - 4.2, u + 4.2, 5.15, 6.15, 0, 1024, 0.0, 0.25, off=0.1)
    finish(m, "westpark", "Westpark (Galaxus)", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
