"""Toni-Areal (ZHdK), Pfingstweidstrasse 94/96: converted dairy (170 x 80 m, 34 m) + 76 m tower, expanded-metal skin,
exposed-concrete ground floor with glazing, ribbon windows, truck ramp along the long facade, roof plant, entrance + lettering."""
import math
from PIL import Image, ImageDraw
from common import *
from lm import *
import detail as D
import osmq
from shapely.geometry import Polygon, MultiLineString, LineString, Point

METAL = hexc("#7a766c"); CONC = D.hexl("#a9a69e")


def metal_tex(seed=2):
    """Expanded-metal screen: vertical bronze fins (0.5 m pitch at 4 m/tile -> 8 fins), lit/shaded flanks, fine mesh rows, panel seams."""
    S = 128; rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (S, S), METAL); d = ImageDraw.Draw(im)
    for k in range(S):
        ph = (k % 16) / 16.0
        f = 1.12 if ph < 0.18 else (0.62 if ph < 0.4 else 0.9 - 0.12 * ph) + rng.normal(0, 0.012)
        d.line([k, 0, k, S], fill=shade(METAL, f))
    for y in range(0, S, 4):
        d.line([0, y, S, y], fill=shade(METAL, 0.9))
    d.rectangle([0, 0, S, 2], fill=shade(METAL, 0.6)); d.rectangle([S // 2 - 1, 0, S // 2, S], fill=shade(METAL, 0.7))
    return im


def finned(ga, cw=64, ch=96, pitch=8):
    """Overlay vertical metal fins (the screen in front of the ribbon windows) on the glass atlas cells."""
    base, em = ga; d, de = ImageDraw.Draw(base), ImageDraw.Draw(em)
    for k in range(8):
        for x in range(k * cw + 2, (k + 1) * cw, pitch):
            d.rectangle([x, 0, x + 2, ch - 1], fill=hexc("#575349")); de.rectangle([x, 0, x + 2, ch - 1], fill=(0, 0, 0))
    return base, em


def build():
    A = bid("ID_5CEB50B3"); B = bid("ID_195ECD88")
    P1, P2 = outline(A["fp"], 0.5), outline(B["fp"], 0.5)
    c = P1.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    P1l, P2l = orient(localize(P1, ox, oy), 1.0), orient(localize(P2, ox, oy), 1.0)
    rng = np.random.default_rng(4)
    m = Model("toni")
    mm = m.mat("metal", metal_tex())
    mg = m.mat("glass", *finned(D.glass_atlas(frame="#6f7374", glass="#2f4352", sky="#a9c3d4", seed=9, curtains=True, lit_p=0.4,
               sign=D.letters_strip([(0, 640, "TONI-AREAL", "#f2f0ea", "#1b1f22", None), (640, 1024, "BISTRO", "#e6e3da", "#7c7e7b", None)], size=26))), rough=0.3)
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    W = (255, 255, 255, 255); REV = D.hexl("#6e7476"); GRC = D.hexl("#c9c6bd")
    H1, FH, GF = 33.8, 3.6, 5.0
    nf1 = int(round((H1 - GF) / FH)); H1 = GF + nf1 * FH
    HT = 76.0; nf2 = int(round((HT - GF) / FH)); HT = GF + nf2 * FH
    # entrance side = edge of the body nearest Pfingstweidstrasse
    streets = [LineString([(x - ox, y - oy) for x, y in pts]) for t, pts in osmq.rows if t.get("name") == "Pfingstweidstrasse" and "building" not in t]
    street = MultiLineString(streets)

    def edges(P):
        r = list(P.exterior.coords)[:-1]; return [(r[i], r[(i + 1) % len(r)]) for i in range(len(r))]

    def tower_like(P, H, nf, seg):
        for a, b in edges(P):
            L, t, n = D.frame_of(a, b)
            if L < 1.2: m.wall(mm, a, b, 0, H, (4, 4), W); continue
            # ground floor: concrete piers with glazing
            nb = max(1, int(round(L / 6.0)))
            D.wall_run(m, mf, mg, mf, a, b, 0.0, 1, GF, 6.0, lambda u0, u1, f0, f1, fl: D.rect_pts(u0 + 0.8, f0 + 0.15, u1 - 0.8, f1 - 0.75), 0.9, CONC, D.hexl("#8b8880"), rng)
            D.band(m, mf, a, b, GF - 0.75, GF + 0.0, 0.5, GRC)
            D.ribbon_floors(m, mm, mg, mf, a, b, GF, nf, FH, 1.15, 2.0, 0.45, W, REV, rng, wmod=(4.0, 4.0), seg=seg, slab_out=0.0)
            D.band(m, mf, a, b, GF + 0.0, GF + 0.01, 0.0, GRC) if False else None
    m.extrude(mf, mf, P1l.buffer(0.01), -4, 0.0, col=D.hexl("#8b8880"), roof=False)
    tower_like(P1l, H1, nf1, 6.0)
    m.extrude(mf, mf, P2l.buffer(0.01), -4, 0.0, col=D.hexl("#8b8880"), roof=False)
    tower_like(P2l, HT, nf2, 4.5)
    # parapets + roofs
    for P, H in ((P1l, H1), (P2l, HT)):
        m.flat(mf, P, H, D.hexl("#5a5d5e"))
        for a, b in edges(P):
            L, t, n = D.frame_of(a, b)
            if L < 0.5: continue
            m.wall(mf, a, b, H, H + 0.8, (2, 2), D.hexl("#b3b7b8"))
            D.band(m, mf, a, b, H + 0.8, H + 1.0, 0.18, GRC)
    # ---- roof plant on the body
    rect = P1l.minimum_rotated_rectangle; rc = list(rect.exterior.coords)
    e0 = (rc[1][0] - rc[0][0], rc[1][1] - rc[0][1]); ang = math.atan2(e0[1], e0[0])
    if math.hypot(*e0) < math.hypot(rc[2][0] - rc[1][0], rc[2][1] - rc[1][1]): ang += math.pi / 2
    ux, uy = math.cos(ang), math.sin(ang); vx, vy = -uy, ux; cx0, cy0 = rect.centroid.x, rect.centroid.y
    inner = P1l.buffer(-5)
    for (a_, b_, w_, d_, h_, col) in [(-70, 5, 16, 9, 3.2, "#8d8f8e"), (-45, -18, 24, 6, 2.4, "#9a9c9b"), (-20, 14, 12, 12, 3.8, "#7f8281"), (10, -8, 30, 9, 2.8, "#8d8f8e"),
                                      (40, 12, 22, 8, 2.6, "#9a9c9b"), (62, -14, 10, 10, 4.2, "#7f8281"), (-5, 30, 36, 4, 1.4, "#6f93a0"), (20, -30, 44, 4, 1.4, "#6f93a0"), (-60, -28, 18, 5, 2.0, "#b0b3b2")]:
        px, py = cx0 + ux * a_ + vx * b_, cy0 + uy * a_ + vy * b_
        if inner.contains(Point(px, py)):
            m.box(mf, px, py, w_, d_, H1 + 1.0, H1 + 1.0 + h_, rot=ang, col=D.hexl(col))
            m.box(mf, px, py, w_ * 0.5, d_ * 0.5, H1 + 1.0 + h_, H1 + 1.4 + h_, rot=ang, col=D.hexl("#4e5253"))
            for k in range(-1, 2): m.cylinder(mf, px + ux * k * w_ * 0.28, py + uy * k * w_ * 0.28, 0.9, H1 + 1.0 + h_, H1 + 2.2 + h_, n=8, col=D.hexl("#c9ccca"), cap=mf, capcol=D.hexl("#7d8080"))
    # ---- tower crown: glazed lantern, mast, lift core
    t = P2l.centroid; r2 = P2l.minimum_rotated_rectangle; rc2 = list(r2.exterior.coords)
    e2 = (rc2[1][0] - rc2[0][0], rc2[1][1] - rc2[0][1]); a2 = math.atan2(e2[1], e2[0])
    m.box(mf, t.x, t.y, 12, 9, HT + 1.0, HT + 4.5, rot=a2, col=D.hexl("#aeb2b3"))
    m.box(mf, t.x + 5, t.y, 3, 3, HT + 4.5, HT + 6.0, rot=a2, col=D.hexl("#555a5c"))
    m.cylinder(mf, t.x - 3, t.y + 2, 0.18, HT + 4.5, HT + 16.0, n=6, col=D.hexl("#d0d3d2"), cap=mf, capcol=D.hexl("#d33"))
    # ---- entrance + lettering on the edge of the body nearest the street
    best = min(edges(P1l), key=lambda ab: street.distance(Point((ab[0][0] + ab[1][0]) / 2, (ab[0][1] + ab[1][1]) / 2)) if not street.is_empty else 0)
    a, b = best; L, t_, n_ = D.frame_of(a, b); u = L * 0.35; ang_e = math.atan2(t_[1], t_[0])
    cw, cd = 18.0, 7.0
    cp = D.P3(a, t_, n_, u, 0, cd / 2)
    m.box(mf, cp[0], cp[1], cw, cd, GF + 0.2, GF + 0.7, rot=ang_e, col=D.hexl("#d6d3ca"))
    for s in (-1, 1, -0.33, 0.33):
        q = D.P3(a, t_, n_, u + s * (cw / 2 - 1.2), 0, cd - 1.0); m.cylinder(mf, q[0], q[1], 0.35, 0.0, GF + 0.2, n=10, col=D.hexl("#d6d3ca"))
    for k in range(4):   # wide steps
        sp = D.P3(a, t_, n_, u, 0, 0.5 + (3 - k) * 0.5 + cd * 0.0)
        m.box(mf, sp[0], sp[1], 12, 0.5 * (4 - k) + 0.4, -0.5 - 0.1 * k, 0.12 * (4 - k) - 0.3 + 0.1, rot=ang_e, col=D.hexl("#b4b1a8"))
    w, h, zz = 24.0, 2.6, H1 - 5.5
    p0 = D.P3(a, t_, n_, u - w / 2, zz, 0.55); p1 = D.P3(a, t_, n_, u + w / 2, zz, 0.55)
    D.band(m, mf, D.P3(a, t_, n_, u - w / 2 - 0.3, 0, 0)[:2], D.P3(a, t_, n_, u + w / 2 + 0.3, 0, 0)[:2], zz - 0.25, zz + h + 0.25, 0.5, D.hexl("#2a2e30"))
    m.quad(mg, [p0, p1, (p1[0], p1[1], zz + h), (p0[0], p0[1], zz + h)], [(0.0, 0.0), (0.625, 0.0), (0.625, 0.25), (0.0, 0.25)], n=(n_[0], n_[1], 0))
    bu = u + cw / 2 + 9.0; q0, q1 = D.P3(a, t_, n_, bu, GF - 1.5, 0.06), D.P3(a, t_, n_, bu + 5.0, GF - 1.5, 0.06)   # BISTRO lettering on the concrete base
    m.quad(mg, [q0, q1, (q1[0], q1[1], GF - 0.95), (q0[0], q0[1], GF - 0.95)], [(0.625, 0.0), (1.0, 0.0), (1.0, 0.25), (0.625, 0.25)], n=(n_[0], n_[1], 0))
    # ---- truck ramp along the opposite long edge
    others = [e for e in edges(P1l) if math.dist(*e) > 40 and e != best]
    if others:
        a2_, b2_ = max(others, key=lambda ab: street.distance(Point((ab[0][0] + ab[1][0]) / 2, (ab[0][1] + ab[1][1]) / 2)) if not street.is_empty else math.dist(*ab))
        L2, t2, n2 = D.frame_of(a2_, b2_); us, ue = 8.0, min(L2 - 8.0, 118.0); RH = 14.0
        d0, d1 = 1.2, 7.4
        def Q(u, d, z): return D.P3(a2_, t2, n2, u, z, d)
        zs = lambda u: RH * (u - us) / (ue - us)
        top = [Q(us, d0, 0.0), Q(ue, d0, RH), Q(ue, d1, RH), Q(us, d1, 0.0)]
        m.quad(mf, top[::-1] if False else [top[0], top[3], top[2], top[1]], col=D.hexl("#4a4d4f"), n=(0, 0, 1)); m.quad(mf, top, col=D.hexl("#4a4d4f"), n=(0, 0, 1))
        # slab thickness + outer face + parapets
        for (da, zoff, col) in ((d1, -0.8, "#bdbab1"),):
            f = [Q(us, da, 0.0 + zoff), Q(ue, da, RH + zoff), Q(ue, da, RH + 1.0), Q(us, da, 1.0)]
            m.quad(mf, f, col=D.hexl(col), n=(n2[0], n2[1], 0)); m.quad(mf, f[::-1], col=D.hexl(col), n=(n2[0], n2[1], 0))
        for da in (d0, d1):
            f = [Q(us, da, 0.0), Q(ue, da, RH), Q(ue, da, RH + 1.0), Q(us, da, 1.0)]
            m.quad(mf, f, col=D.hexl("#c3c0b7")); m.quad(mf, f[::-1], col=D.hexl("#c3c0b7"))
        # columns every 11 m
        for uu in np.arange(us + 4, ue, 11.0):
            q = Q(uu, (d0 + d1) / 2, 0)
            m.box(mf, q[0], q[1], 0.9, 3.0, -1.0, zs(uu) - 0.4, rot=ang_e, col=D.hexl("#b4b1a8"))
        # truck-height dock gate openings (dark) on the facade under the ramp
        for uu in np.arange(us + 6, ue - 6, 14.0):
            q0, q1 = Q(uu, 0.02, 0.2), Q(uu + 5.0, 0.02, 0.2)
            hh = 4.2
            m.quad(mf, [q0, q1, (q1[0], q1[1], hh), (q0[0], q0[1], hh)], col=D.hexl("#1d2225"), n=(n2[0], n2[1], 0))
    hide = [[round(p.x, 1), round(p.y, 1)] for fp in (A["fp"], B["fp"]) for p in (g.representative_point() for g in (fp.geoms if hasattr(fp, "geoms") else [fp]))]
    finish(m, "toni_areal", "Toni-Areal", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
