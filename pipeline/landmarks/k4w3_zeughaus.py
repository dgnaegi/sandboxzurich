"""Zeughaeuser Kasernenareal (Zeughausstrasse): five long sandstone arsenal halls (1860s), 2-3 storeys, tall round-arched windows with stone surrounds and green
shutters, strong cornice, grey slate hip roofs. Photos: research/v3/zeughaeuser.md (Commons #1 #2 #3, Panoramax #9)"""
from k4w3_kit import *
from k45_volkshaus import plaster


def build():
    parts = ["ID_B5592320", "ID_DBED4C5B", "ID_DB1C5069", "ID_79896407", "ID_E4644D4E"]
    Bs, ox, oy, oz = setup(parts)
    rng = np.random.default_rng(41)
    m = Model("zeughaeuser")
    SAND = hexc("#dccb9c")
    mw = m.mat("wall", plaster(SAND, seed=7, stains=0.01))
    ga = D.glass_atlas_g(frame="#efe9d8", glass="#2c3640", sky="#8da3b3", cols=2, rows=3, seed=42, lit_p=0.2, curtains=True, curtain_cols=[(226, 222, 210), (200, 192, 176), (170, 176, 182)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W))
    run = make_run(m, mw, mg, mf, rng, W)
    STN, BAND, ROOF = hx("#c4b389"), hx("#cfc09a"), hx("#6b4a3f")
    def arch(w, lo, spring):
        def f(u0, u1, f0, f1, k, nb, L):
            uc = (u0 + u1) / 2; ww = min(w, (u1 - u0) - 0.9); return D.arch_pts(uc - ww / 2, f0 + lo, uc + ww / 2, f0 + spring, n=4)
        return f
    for B in Bs:
        gz = B["gz"] - oz; H = B["zmax"] - B["gz"]
        Pl = orient(localize(outline(B["fp"], 0.6), ox, oy), 1.0); r = list(Pl.exterior.coords)[:-1]
        nfl = 3 if H > 18 else 2; fh = (H - 5.0) / nfl if H > 11 else 5.5
        fh = max(4.6, min(6.2, fh)); g = gz + 0.3
        m.extrude(mf, mf, Pl, gz - 3, g, col=hx("#8d856f"), roof=False)
        zs = [g + k * fh for k in range(nfl + 1)]
        for i, a, b, L, t, n in edge_iter(r):
            if L < 3: m.wall(mw, a, b, g, zs[-1], (4, 4), W); continue
            for f in range(nfl):
                if f == 0:   # ground floor: tall arched doors/windows (alternating), rusticated base band
                    run(a, b, zs[0], fh, 4.6, lambda u0, u1, f0, f1, k, nb, L_: (arch(2.3, 0.0, fh - 1.1)(u0, u1, f0, f1, k, nb, L_) if k % 2 == 0 else arch(1.7, 0.9, fh - 1.4 - 0.85)(u0, u1, f0, f1, k, nb, L_)), 0.5, 0.28, 0.0, STN, STN)
                else:
                    run(a, b, zs[f], fh, 4.6, arch(1.7, 0.9, fh - 1.4 - 0.85), 0.5, 0.0, 0.0, STN, STN)
                if f: D.band(m, mf, a, b, zs[f] - 0.15, zs[f] + 0.12, 0.12, BAND)
            pilasters(m, mf, a, b, g, zs[-1], 9.2, 0.55, 0.16, BAND)
            D.band(m, mf, a, b, g, g + 1.0, 0.1, hx("#b5a67f"))
            D.band(m, mf, a, b, zs[-1] - 0.5, zs[-1] + 0.2, 0.4, BAND)
        slope_roof(m, mf, Pl.buffer(0.4, join_style=2), zs[-1] + 0.2, 3.6, 4.5, ROOF)
    info(m, "zeughaeuser")
    finish(m, "zeughaeuser", "Zeughaeuser Kasernenareal", ox, oy, oz, hide_union("Zeughaeuser Kasernenareal", hide_of(Bs)))


if __name__ == "__main__":
    build()
