"""Hotel 25hours Langstrasse (Pfingstweidstrasse/Langstrasse underpass edge), ~2018: nine-storey block; dark anthracite lower floors with staggered wide
dark-framed windows, lighter grey upper floors with tall narrow windows, set-back top storeys, ground-floor glazing with coloured word signs
(hotel / smile / bar / spotlight / quirky / pocket universe / noise today). Photos: research/v3/hotel_25hours.md (Mapillary #5 #11 #1 #4)"""
from k4w3_kit import *
from k45_volkshaus import plaster


def build():
    Bs, ox, oy, oz = setup(["ID_C04BED14"])
    B = Bs[0]; H = B["zmax"] - oz
    rng = np.random.default_rng(51)
    Pl = orient(localize(outline(B["fp"], 0.5), ox, oy), 1.0); r = list(Pl.exterior.coords)[:-1]
    m = Model("hotel25")
    mw = m.mat("wall", plaster(hexc("#c3c5c4"), seed=11, stains=0.01))
    words = [(0, 170, "hotel", "#f2f2ee", "#26282a", (200, 200, 190)), (170, 340, "smile", "#f5d33a", "#26282a", (200, 170, 40)), (340, 420, "bar", "#d9453a", "#26282a", (200, 60, 50)),
             (420, 600, "spotlight", "#7fc6a0", "#26282a", (80, 160, 120)), (600, 740, "quirky", "#f5d33a", "#26282a", (200, 170, 40)), (740, 1024, "pocket universe", "#f2f2ee", "#26282a", (200, 200, 190))]
    ga = D.glass_atlas_g(frame="#3f4447", glass="#46525a", sky="#7f93a1", cols=1, rows=1, seed=52, lit_p=0.45, sign=strip(words, size=24, fnt="BarlowCondensed-Bold"), cw=128, ch=96, bar=4,
                         curtain_cols=[(226, 222, 212), (190, 190, 190), (150, 160, 168)])
    mg = m.mat("glass", *ga, rough=0.25); mf = m.mat("flat", solid(W))
    run = make_run(m, mw, mg, mf, rng, W)
    DARK, LIGHT, BAND = hx("#323436"), hx("#b9bcbc"), hx("#8d9092")
    # dark plaster for lower floors is a vertex colour tint on the same wall texture (grey plaster x dark tint)
    TINT = (70, 72, 74, 255)
    g = 0.3; e0 = 4.6; fh = 3.1; nf = max(6, int(round((H - e0 - 0.5) / fh))); zs = [g + e0 + k * fh for k in range(nf + 1)]
    dark_n = 3
    m.extrude(mf, mf, Pl, -3.5, g, col=hx("#78787a"), roof=False)
    for i, a, b, L, t, n in edge_iter(r):
        if L < 3: m.wall(mw, a, b, g, zs[-1], (4, 4), TINT); continue
        # ground floor: dark shopfront glazing + sign band
        runc = make_run(m, mw, mg, mf, rng, TINT)
        runc(a, b, g, e0, 4.4, rect_hole(3.7, 3.0, 0.5), 0.15, 0.0, 0.0, DARK, reveal=DARK)
        D.band(m, mf, a, b, g + e0 - 1.0, g + e0, 0.15, DARK)
        txtq(m, mg, a, t, n, 1.2, min(L - 1.2, 26.0), g + e0 - 0.95, 0.8, 0, 1024, off=0.19)
        for f in range(nf):
            zf = zs[f]
            if f < dark_n:   # dark floors: wide, staggered windows
                def fn(u0, u1, f0, f1, k, nb, L_, f=f):
                    uc = (u0 + u1) / 2 + (0.45 if (k + f) % 2 else -0.35); return D.rect_pts(uc - 1.05, f0 + 0.85, uc + 1.05, f0 + 2.35)
                runc(a, b, zf, fh, 2.7, fn, 0.22, 0.0, 0.0, DARK, reveal=DARK)
            else:
                run(a, b, zf, fh, 2.25, rect_hole(1.25, 1.95, 0.7), 0.2, 0.0, 0.0, LIGHT, reveal=hx("#9a9d9e"))
        D.band(m, mf, a, b, zs[dark_n] - 0.15, zs[dark_n] + 0.1, 0.12, BAND)
        D.band(m, mf, a, b, zs[-1] - 0.1, zs[-1] + 0.5, 0.2, hx("#7b7e80"))
    m.flat(mf, Pl, zs[-1] + 0.5, hx("#6e7072"))
    # rooftop plant box
    c = Pl.centroid; m.box(mf, c.x, c.y, 8.0, 6.0, zs[-1] + 0.5, zs[-1] + 3.2, col=hx("#8c8f90"), rot=math.atan2(r[1][1] - r[0][1], r[1][0] - r[0][0]))
    info(m, "hotel25")
    finish(m, "hotel25", "Hotel 25hours Langstrasse", ox, oy, oz, hide_union("Hotel 25hours Langstrasse", hide_of(Bs)))


if __name__ == "__main__":
    build()
