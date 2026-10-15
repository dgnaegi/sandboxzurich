"""Mobimo Tower (Renaissance Hotel, Turbinenstrasse 18), Puls 5 (Giessereihalle block), Technopark (+ MAN hall) and the Migros high-rise at
Limmatplatz (Migros-Genossenschafts-Bund). One parametric block builder per site. Photos: research/v3/<id>.md."""
import sys
from k5w3_kit import *


def block(name, title, ids, *, wall, wall_tex=None, frame, glass="#2a3844", cols=2, rows=3, bay, hole_w, hole_h, sill, fh, eg_h, eg_glass=True, tol=0.8,
          corn="#8f918c", roof="#7c7e7a", sign=None, deep_z=5.0, depth=0.3, wmod=(3, 3), extra=None, seed=3, lit=0.3, skip_edge=None, minA=14.0, wcol=None, simp=0.6, curtains=True, fbands=None, post=None):
    setup()
    U = unary_union([bid(p)["fp"] for p in ids]); c = U.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    m = Model(name); rng = np.random.default_rng(seed)
    mw = m.mat("wall", wall_tex if wall_tex is not None else tex_plain(wall), rough=0.9)
    ga = D.glass_atlas_g(frame=frame, glass=glass, sky="#8fa9bb", cols=cols, rows=rows, seed=seed, lit_p=lit, sign=sign, curtains=curtains)
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W4))
    wc = wcol or W4
    hide = []
    for p in ids:
        v = [(z - oz, localize(g, ox, oy)) for z, g in volumes(p, tol=tol, min_area=minA, simp=simp)]
        for z0, z1, S, R in bands(v, -3.0):
            Tn = unary_union([g for z, g in v if z > z1 + 1e-6]) if any(z > z1 + 1e-6 for z, g in v) else None
            for S1 in polys_of(S):
                def hole(u0, u1, f0, f1, fi, L):
                    uc = (u0 + u1) / 2; w = min(hole_w, (u1 - u0) - 0.4); return D.rect_pts(uc - w / 2, f0 + sill, uc + w / 2, f0 + sill + hole_h)
                def egh(u0, u1, f0, f1, fi, L):
                    return D.rect_pts(u0 + 0.3, f0 + 0.2, u1 - 0.3, f0 + eg_h - 0.5)
                facade(m, (mw, mg, mf), S1, z0, z1, None, fh=fh, bayw=bay, hole=hole, depth=depth, wall_col=wc, reveal_col=hexl(corn), rng=rng, wmod=wmod,
                       eg_h=eg_h if z0 < 0.5 else None, eg_hole=egh, base=-3.0, cornice=(hexl(corn), 0.22, 0.5), deep_z=deep_z, floor_bands=fbands)
                roofs(m, mf, S1.difference(Tn.buffer(0.05)) if Tn is not None else S1, z1, hexl(roof))
        hide += hide_pts([p])
    if extra: extra(m, mw, mg, mf, ox, oy, oz, ids)
    if post: post(m, mw, mg, mf, ox, oy, oz, ids)
    finish(m, name, title, ox, oy, oz, hide)


def mobimo():
    sign = text_painter([(0, 1024, "RENAISSANCE", "#e8e4da", "#3a3630", (200, 190, 150))], size=24)
    block("mobimo_tower", "Mobimo Tower", ["ID_0A974ED3"], wall="#b6aa94", wall_tex=tex_concrete("#b8ad98", panel=(1, 1), seed=6), frame="#e2dccd", cols=1, rows=2,
          bay=3.2, hole_w=2.3, hole_h=2.0, sill=0.8, fh=3.4, eg_h=5.0, tol=2.5, minA=60, corn="#a39880", roof="#8a8578", sign=sign, deep_z=4.0, depth=0.4, lit=0.35, seed=12)


def puls5():
    sign = text_painter([(0, 1024, "PULS 5", "#1c1d1f", "#8d9d95", None)], size=26)
    block("puls5", "Puls 5", ["ID_94796D93"], wall="#8d9d95", wall_tex=tex_corrugated("#8d9d95", n=8, horizontal=True), frame="#6d7a74", glass="#34423f", cols=4, rows=1,
          bay=3.8, hole_w=3.3, hole_h=1.5, sill=0.9, fh=3.6, eg_h=5.0, tol=2.0, minA=60, corn="#5c5a55", roof="#85857f", sign=sign, deep_z=4.0, seed=14,
          curtains=False, lit=0.15, fbands=(hexl("#79877f"), 0.06, 0.35))


def techno():
    block("technopark", "Technopark", ["ID_04D471F8", "ID_D784D2A2", "ID_B2A31DCD"], wall="#c9b48e", wall_tex=tex_plain("#c9b48e", amp=7), frame="#f1efe8", cols=3, rows=2,
          bay=2.6, hole_w=1.9, hole_h=1.7, sill=0.85, fh=3.4, eg_h=4.2, tol=2.0, minA=40, corn="#e6e1d4", roof="#8a8a86", deep_z=5.0, seed=16)


def migros():
    sign = text_painter([(0, 1024, "MIGROS", "#f2eee6", "#e8731c", (255, 150, 60))], size=28)
    block("migros_limmatplatz", "Migros-Hochhaus Limmatplatz", ["ID_BC82F91E"], wall="#dcdad4", wall_tex=tex_concrete("#d4d3cd", panel=(2, 2), seed=3), frame="#e6e6e2", glass="#34414c", cols=2, rows=2,
          bay=5.0, hole_w=3.2, hole_h=1.5, sill=0.9, fh=3.4, eg_h=5.0, tol=6.0, minA=400, simp=3.5, corn="#bfbdb6", roof="#8a8a86", sign=sign, deep_z=2.0, seed=18)


if __name__ == "__main__":
    for k in sys.argv[1:] or ["mobimo", "puls5", "techno", "migros"]:
        globals()[k]()
