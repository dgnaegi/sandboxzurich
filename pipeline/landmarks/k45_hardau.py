"""Hardau II (Bullingerstrasse/Norastrasse), 1978: four residential towers 70-97 m with projecting balcony slabs + coloured fronts,
corner fins, glazed lobby, and the 3-storey podium (Sockelbau) around three of them."""
import math
from PIL import Image
from common import *
from lm import *
import detail as D
from k45_volkshaus import plaster

IDS = ["ID_26259A5A", "ID_EEB23F5F", "ID_78594C63", "ID_0E0A8569"]
POD = "ID_616085CB"
ACC = ["#c49a72"] * 4


def fp_ground(fp, oz):
    """(base, lowest) model-space z of the terrain along a footprint outline: tower stands on the highest point, skirt reaches the lowest."""
    ext = fp.exterior; gs = [ground(*ext.interpolate(t).coords[0]) for t in np.linspace(0, ext.length, 48)]
    return max(gs) - oz, min(gs) - oz


def edges(P):
    r = list(orient(P, 1.0).exterior.coords)[:-1]; return [(r[i], r[(i + 1) % len(r)]) for i in range(len(r))]


def build():
    bs = [bid(i) for i in IDS]; pod = bid(POD)
    fps = [outline(b["fp"], 0.4) for b in bs]; pfp = outline(pod["fp"], 0.6)
    ox = round(float(np.mean([f.centroid.x for f in fps])), 1); oy = round(float(np.mean([f.centroid.y for f in fps])), 1)
    oz = float(np.mean([ground(f.centroid.x, f.centroid.y) for f in fps]))
    rng = np.random.default_rng(8)
    m = Model("hardau")
    mw = m.mat("wall", plaster(hexc("#c9a074"), seed=4, stains=0.03))
    mg = m.mat("glass", *D.glass_atlas_g(frame="#5a4535", glass="#2a3338", sky="#a8bfcc", cols=2, rows=1, seed=14, lit_p=0.4, curtains=True, curtain_cols=[(236, 228, 210), (214, 200, 175), (225, 225, 225), (190, 175, 150)]), rough=0.35)
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    W = (255, 255, 255, 255); CONC = D.hexl("#cfa77c"); REV = D.hexl("#8a5a3a")
    # ---- podium (Sockelbau)
    Pp = orient(localize(pfp, ox, oy), 1.0); gzp, gzp_lo = fp_ground(pfp, oz)   # base = highest terrain on the footprint, skirt down to the lowest
    m.extrude(mf, mf, Pp, gzp_lo - 0.6, gzp, col=D.hexl("#8f8780"), roof=False)
    GFH, FH2 = 4.5, 3.4
    for a, b in edges(Pp):
        L, t, n = D.frame_of(a, b)
        if L < 2: m.wall(mw, a, b, gzp, gzp + 11.3, (4, 4), W); continue
        D.wall_run(m, mf, mg, mf, a, b, gzp, 1, GFH, 5.0, lambda u0, u1, f0, f1, fl: D.rect_pts(u0 + 0.5, f0 + 0.3, u1 - 0.5, f1 - 0.6), 0.5, D.hexl("#b9ab98"), REV, rng)
        D.ribbon_floors(m, mw, mg, mf, a, b, gzp + GFH, 2, FH2, 0.95, 1.6, 0.3, W, REV, rng, wmod=(4, 4), seg=4.0, slab_out=0.6, slab_col=CONC)
        D.band(m, mf, a, b, gzp + 11.0, gzp + 11.45, 0.35, CONC)
    m.flat(mf, Pp, gzp + 11.3, hexc("#6f7a6a"))
    # ---- towers
    for i, (b, fp) in enumerate(zip(bs, fps)):
        P = orient(localize(fp, ox, oy), 1.0)
        gz, gz_lo = fp_ground(fp, oz); g0 = gz + oz; H = b["zmax"] - g0
        m.extrude(mf, mf, P, gz_lo - 0.6, gz, col=D.hexl("#8f8780"), roof=False)   # foundation skirt: terraced terrain (-2..+2 m) must not bury the tower
        n_fl = int(round((H - 4.0) / 3.0)); top = 4.0 + n_fl * 3.0
        acc = D.hexl(ACC[i])
        for a, b2 in edges(P):
            L, t, n = D.frame_of(a, b2)
            if L < 1.0: continue
            D.wall_run(m, mf, mg, mf, a, b2, gz, 1, 4.0, max(L, 2.0), lambda u0, u1, f0, f1, fl: D.rect_pts(u0 + 1.2, f0 + 0.2, u1 - 1.2, f1 - 0.5), 0.6, D.hexl("#b9ab98"), REV, rng) if L > 6 else m.wall(mf, a, b2, gz, gz + 4.0, (2, 2), D.hexl("#b9ab98"))
            for f in range(n_fl):
                zf = gz + 4.0 + f * 3.0
                accent = (f % 3 == 1)
                D.ribbon_floors(m, mw, mg, mf, a, b2, zf, 1, 3.0, 0.95, 1.55, 0.25, W, REV, rng, wmod=(4, 4), seg=max(5.0, L / 2), slab_out=0.9 if L > 8 else 0.0, slab_col=acc if accent else CONC)
        m.flat(mf, P, gz + top, hexc("#6d6f6e"))
        c = P.centroid; rc = list(P.minimum_rotated_rectangle.exterior.coords); ang = math.atan2(rc[1][1] - rc[0][1], rc[1][0] - rc[0][0])
        m.box(mf, c.x, c.y, 9, 6.5, gz + top, gz + top + 3.4, rot=ang, col=hexc("#a9a9a5"))
        m.box(mf, c.x + 5 * math.cos(ang), c.y + 5 * math.sin(ang), 2.2, 2.2, gz + top, gz + top + 5.5, rot=ang, col=hexc("#8a8a88"))
        for a, b2 in edges(P):
            L, t, n = D.frame_of(a, b2)
            if L > 0.5: D.band(m, mf, a, b2, gz + top, gz + top + 0.9, 0.0, hexc("#c8c6c0"))
        # corner fins
        for a, b2 in edges(P):
            L, t, n = D.frame_of(a, b2)
            if L < 8: continue
            for u0 in (0.0, L - 1.8):
                p0 = D.P3(a, t, n, u0, gz + 4.0, 0.95); p1 = D.P3(a, t, n, u0 + 1.8, gz + 4.0, 0.95)
                m.quad(mf, [p0, p1, (p1[0], p1[1], gz + top), (p0[0], p0[1], gz + top)], col=acc, n=(n[0], n[1], 0))
    hide = []
    for bb in bs + [pod]:
        fp = bb["fp"]; hide += [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    finish(m, "hardau_towers", "Hardau II (4 Wohntuerme)", ox, oy, oz, hide_union("Hardau II (4 Wohntuerme)", hide))


if __name__ == "__main__":
    build()
