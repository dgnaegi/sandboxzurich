"""Loewenbraeu-Areal (Limmatstrasse 264-270, Kreis 5): red-clad 'Loewenbraeu Red' block (deep white-framed square windows, glazed EG),
grey concrete silo tower, red-brick brewery buildings with arched windows and cream bands (Kunsthalle). Photos: research/v3/loewenbraeu.md."""
import math
from k5w3_kit import *

BRICK = ["ID_719878A5", "ID_37918C0E", "ID_2C8A677A"]
RED, SILO = "ID_122F13C2", "ID_B7CFABAE"


def build():
    setup()
    allb = BRICK + [RED, SILO]
    U = unary_union([bid(p)["fp"] for p in allb]); c = U.centroid; ox, oy = round(c.x, 1), round(c.y, 1)
    oz = ground(ox, oy)
    m = Model("loewenbraeu"); rng = np.random.default_rng(5)
    mw = m.mat("wall", tex_brick("#9a4636", "#c6b9a4"), rough=0.95)
    sign = text_painter([(0, 1024, "KUNSTHALLE", "#f1ece0", "#8a3a2c", None)], size=22)
    ga = D.glass_atlas_g(frame="#f2eee4", glass="#26323d", sky="#8fa9bb", cols=2, rows=3, seed=8, sign=sign, lit_p=0.35)
    mg = m.mat("glass", *ga, rough=0.35); mf = m.mat("flat", solid(W4))
    RED_C, SILO_C, CREAM, SLATE = hexl("#c4262c"), hexl("#a9a8a2"), hexl("#d9c9a4"), hexl("#4a4c52")
    hide = []

    def vols_of(p):
        return [(z - oz, localize(g, ox, oy)) for z, g in volumes(p)]

    def run(prefix, kind):
        t0 = m.tri_count()
        v = vols_of(prefix)
        for z0, z1, S, R in bands(v, -3.0):
            T = unary_union([g for z, g in v if z > z1 + 1e-6]) if any(z > z1 + 1e-6 for z, g in v) else None
            for S1 in polys_of(S):
                if S1.area < 3: continue
                if kind == "brick":
                    def hole(u0, u1, f0, f1, fi, L):
                        uc = (u0 + u1) / 2; w = 1.05; return D.arch_pts(uc - w / 2, f0 + 0.9, uc + w / 2, f0 + 2.3, n=3)
                    def egh(u0, u1, f0, f1, fi, L):
                        uc = (u0 + u1) / 2; w = 1.3; return D.arch_pts(uc - w / 2, f0 + 0.6, uc + w / 2, f0 + 2.9, n=3)
                    facade(m, (mw, mg, mf), S1, z0, z1, T, fh=4.1, bayw=3.7, hole=hole, depth=0.3, deep_z=5.0, wall_col=W4, reveal_col=hexl("#d8cdb6"), rng=rng,
                           wmod=(1.5, 1.2), eg_h=4.5 if z0 < 0.5 else None, eg_hole=egh, base=-3.0, cornice=(CREAM, 0.18, 0.45), wsill=0.05)
                    roofs(m, mf, S1.difference(T.buffer(0.05)) if T is not None else S1, z1, hexl("#7a7770"))
                elif kind == "red":
                    def hole(u0, u1, f0, f1, fi, L):
                        uc = (u0 + u1) / 2; w = min(1.9, u1 - u0 - 0.9); return D.rect_pts(uc - w / 2, f0 + 0.85, uc + w / 2, f0 + 2.55)
                    def egh(u0, u1, f0, f1, fi, L):
                        w = u1 - u0 - 0.3; return D.rect_pts(u0 + 0.15, f0 + 0.2, u0 + 0.15 + w, f0 + 3.6)
                    facade(m, (mf, mg, mf), S1, z0, z1, T, fh=3.7, bayw=3.3, hole=hole, depth=0.45, deep_z=6.0, wall_col=RED_C, reveal_col=hexl("#e9e5de"), rng=rng,
                           eg_h=4.4 if z0 < 0.5 else None, eg_hole=egh, base=-3.0, cornice=(hexl("#8f1c22"), 0.15, 0.4), wsill=0.12)
                    roofs(m, mf, S1.difference(T.buffer(0.05)) if T is not None else S1, z1, hexl("#8a8a86"))
                else:  # silo
                    def hole(u0, u1, f0, f1, fi, L):
                        if fi % 2: return None
                        uc = (u0 + u1) / 2; return D.rect_pts(uc - 0.55, f0 + 1.0, uc + 0.55, f0 + 2.4)
                    facade(m, (mf, mg, mf), S1, z0, z1, T, fh=3.4, bayw=4.5, hole=hole, depth=0.25, wall_col=SILO_C, reveal_col=hexl("#8a8984"), rng=rng,
                           base=-3.0, cornice=(hexl("#8f8e88"), 0.2, 0.5))
                    roofs(m, mf, S1.difference(T.buffer(0.05)) if T is not None else S1, z1, hexl("#7d7d79"))
        print(prefix, kind, m.tri_count() - t0)
        bb = bid(prefix); gs = bb["fp"].geoms if hasattr(bb["fp"], "geoms") else [bb["fp"]]
        hide.extend([[round(q.x, 1), round(q.y, 1)] for q in (g.representative_point() for g in gs)])

    for p in BRICK: run(p, "brick")
    run(RED, "red"); run(SILO, "silo")
    # hip roof on the tall brewery block
    v = vols_of(BRICK[0]); zt, gt = v[-1]
    big = max(polys_of(gt), key=lambda p: p.area) if False else None
    # silo stair/pipe details omitted; roof lights on red tower
    finish(m, "loewenbraeu", "Loewenbraeu-Areal", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
