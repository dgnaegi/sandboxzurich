"""Bike components. All take the geometry dict G (see build_bikes.py). Units: metres, P(u,h,x)."""
import numpy as np
from bikelib import *

BLACK = (.025, .025, .028); TIRE = (.02, .02, .02); CHROME = (.62, .62, .64); STEEL = (.30, .31, .33); WHITE = (1, 1, 1)
RED = (.55, .015, .015); LEATHER = lin(0x4a2c1a); GRIP = (.03, .03, .03)

def dirv(deg): a = np.deg2rad(deg); return np.array([np.cos(a), np.sin(a)])    # (u,h)
def uh(p, x=0.0): return P(p[0], p[1], x)

def wheel(m, u, R, tw, th, nseg=24, nmin=6, rim_clear=.85):
    torus_tire(m, u, R, R, tw, th, nseg, nmin, col=TIRE)
    disc(m, P(u, R, 0), R - th * rim_clear, nseg, WHITE, uvname="wheel")
    tube(m, P(u, R, -.052), P(u, R, .052), .011, sides=5, col=CHROME)

def fender(m, u, R, th, tw, a0, a1, col, nseg=9, lift=.014):
    """Fender arc from angle a0 to a1 (deg from top, positive = forward)."""
    rf = R + lift; w = tw * .5 + .012; rings = []; hints = []
    for k in range(nseg + 1):
        a = np.deg2rad(a0 + (a1 - a0) * k / nseg); rd = P(np.sin(a), np.cos(a), 0)
        rr = [rf - .010, rf, rf - .010]; xs = [-w, 0, w]
        rings.append([P(u, R, 0) + rd * r + np.array([x, 0, 0]) for r, x in zip(rr, xs)])
        hints.append([nz(rd + np.array([x * 3, 0, 0])) for x in xs])
    grid(m, rings, hints, col, closed=False)

def fork(m, G, susp=False, col_paint=1.0):
    hb = G["hbot"]; fu, R = G["fu"], G["Rf"]
    for s in (-1, 1):
        a = uh(hb, s * .045); b = P(fu, R, s * .052)
        if susp:
            mid = a + (b - a) * .5; tube(m, a, mid, .017, .017, 5, STEEL); tube(m, mid, b, .021, .015, 5, BLACK)
        else: tube(m, a, b, .0145, .0105, 5, col=(1, 1, 1), paint=col_paint)
    cuboid(m, P(hb[0], hb[1] + .004, 0), .02, .014, .055, (1, 1, 1) if not susp else BLACK, paint=0 if susp else col_paint)

def frame(m, G, style="diamond", tt_from=.93, dt_r=.02, tt_r=.0155, dt_sq=1.0, K=1.15):
    """Main triangle + rear triangle (paint=1)."""
    bb = G["bb"]; sd = np.array([-np.cos(np.deg2rad(G["sa"])), np.sin(np.deg2rad(G["sa"]))])
    st_top = bb + sd * G["sl"]; ht, hb = G["htop"], G["hbot"]; ru, R = G["ru"], G["Rr"]
    pk = dict(col=(1, 1, 1), paint=1.0); dt_r *= K; tt_r *= K
    tube(m, uh(ht + (hb - ht) * .08), uh(ht + (hb - ht) * .92), .02, .02, 6, **pk)                      # head tube
    tube(m, uh(bb), uh(st_top), tt_r, tt_r, 5, **pk)                                                    # seat tube
    if style == "step":                                                                                 # low-step: big swoosh + mixte tube
        tube(m, uh(hb + (ht - hb) * .15), uh(bb + np.array([.01, .005])), dt_r, dt_r, 6, sq=dt_sq, **pk)
        p2 = bb + sd * G["sl"] * .50
        tube(m, uh(ht + (hb - ht) * .35), uh(p2), tt_r * .9, tt_r * .9, 5, **pk)
        sp = p2 + (st_top - p2) * .5
    else:
        tube(m, uh(ht + (hb - ht) * .12), uh(bb + sd * G["sl"] * tt_from), tt_r, tt_r, 5, **pk)          # top tube
        tube(m, uh(hb + (ht - hb) * .12), uh(bb), dt_r, dt_r * .95, 6, sq=dt_sq, **pk)                   # down tube
        sp = bb + sd * G["sl"] * .90
    for s in (-1, 1):
        axl = P(ru, R, s * .062)
        tube(m, uh(sp, s * .028), axl, .0098, .0098, 5, **pk)                                            # seat stay
        tube(m, uh(bb + np.array([-.01, 0]), s * .03), axl, .0125, .0105, 5, **pk)                         # chain stay
    tube(m, uh(bb, -.05), uh(bb, .05), .019, .019, 6, col=STEEL)                                        # BB shell
    return st_top, sd

def saddle(m, G, st_top, sd, post=.12, kind="city", col=LEATHER):
    top = st_top + sd * post; tube(m, uh(st_top - sd * .03), uh(top), .0125, .0125, 5, col=CHROME)
    L, wr, wn, tr, tn = dict(city=(.28, .10, .02, .055, .028), road=(.27, .068, .014, .036, .020), mtb=(.27, .075, .016, .042, .024))[kind]
    ts = np.array([0, .12, .35, .65, .88, 1.0]); rings = []; hints = []
    for k, t in enumerate(ts):
        w = wn + (wr - wn) * t ** 1.4; u = top[0] - .02 + (.5 - t) * L; th = tn + (tr - tn) * t
        hh = top[1] + th * .5 + .004 + (.012 * t if kind == "city" else .006 * t) - (.02 if k == 0 else 0)
        ring = []; hint = []
        for j in range(6):
            a = 2 * np.pi * j / 6; x = w * np.cos(a); y = th * .5 * np.sin(a) * (1 if np.sin(a) > 0 else .7)
            ring.append(P(u, hh + y, x)); hint.append(nz(np.array([np.cos(a) * .6, np.sin(a), 0])))
        rings.append(ring); hints.append(hint)
    grid(m, rings, hints, col)
    for rg, sgn in ((rings[0], 1), (rings[-1], -1)):
        c = np.mean(rg, 0); m.add(np.vstack([rg, [c]]), np.tile([0, 0, -sgn * 1.0], (7, 1)), [(k, (k + 1) % 6, 6) for k in range(6)], col)
    cuboid(m, P(top[0] - .01, top[1] + .002, 0), .03, .008, .012, CHROME)

def crank(m, G, ring_r=.095, guard=False, cassette=False, ang=-25):
    bb = G["bb"]; a = np.deg2rad(ang); L = .17
    for s, aa in ((1, a), (-1, a + np.pi)):
        pu, ph = bb[0] + L * np.cos(aa), bb[1] + L * np.sin(aa)
        tube(m, P(bb[0], bb[1], s * .075), P(pu, ph, s * .082), .011, .009, 5, STEEL)
        cuboid(m, P(pu, ph, s * .12), .05, .010, .043, BLACK)
        tube(m, P(pu, ph, s * .075), P(pu, ph, s * .098), .006, .006, 4, CHROME)
    if guard:
        disc(m, P(bb[0], bb[1], .075), .108, 14, (.05, .05, .055))
        plate(m, P(bb[0] + .01, bb[1] + .09, .072), P(G["ru"] + .05, G["Rr"] + .045, .072), .06, (.04, .04, .045))
    else:
        disc(m, P(bb[0], bb[1], .058), ring_r, 14, (.12, .12, .13), uvname="ring")
    sp = .05 if not cassette else .062
    disc(m, P(G["ru"], G["Rr"], .045), sp, 10, (.30, .30, .32))
    if not guard:                                                                                       # chain strands
        for dy1, dy2 in ((ring_r, sp), (-ring_r, -sp)):
            obox(m, P(bb[0], bb[1] + dy1, .058), P(G["ru"], G["Rr"] + dy2, .045), .008, .012, (.035, .03, .02), up=(1., 0, 0))

def plate(m, a, b, h, col):
    """Thin vertical plate in the u/h plane (constant x) from a to b with height h."""
    d = nz(b - a); perp = nz(np.cross([1., 0, 0], d)); perp = perp if perp[1] > 0 else -perp
    q = [a - perp * h / 2, b - perp * h / 2, b + perp * h / 2, a + perp * h / 2]
    for sgn in (-1, 1): m.add(q, np.tile([sgn, 0, 0], (4, 1)), [(0, 1, 2), (0, 2, 3)], col)

def bars(m, G, kind="swept", width=.62, S=None, pk=None):
    """Handlebar; S = (u,h) of the stem top. kinds: swept (city), flat (mtb/trekking), drop (road)."""
    su, sh = S; ht = G["htop"]
    tube(m, uh(ht + np.array([0, -.03])), uh(np.array([su, sh])), .0115, .0115, 5, CHROME)               # steerer/stem
    for s in (-1, 1):
        if kind == "swept":
            pts = [P(su, sh, 0), P(su - .005, sh + .01, s * .12), P(su - .07, sh + .018, s * .28), P(su - .15, sh - .005, s * (width / 2 + .01))]
            ptube(m, pts, .0105, 5, CHROME, cap=False)
            tube(m, P(su - .085, sh + .012, s * .29), P(su - .15, sh - .005, s * (width / 2 + .01)), .0165, .0165, 6, GRIP, cap=True)
            tube(m, P(su - .04, sh + .01, s * .30), P(su + .06, sh - .03, s * .295), .005, .004, 4, CHROME)  # brake lever
        elif kind == "flat":
            pts = [P(su, sh, 0), P(su - .005, sh + .006, s * .15), P(su - .035, sh + .01, s * (width / 2 - .08)), P(su - .03, sh + .01, s * (width / 2))]
            ptube(m, pts, .0115, 5, BLACK, cap=False)
            tube(m, P(su - .03, sh + .01, s * (width / 2 - .11)), P(su - .03, sh + .01, s * (width / 2 + .005)), .0165, .0165, 6, GRIP, cap=True)
            tube(m, P(su - .01, sh + .005, s * (width / 2 - .09)), P(su + .075, sh - .03, s * (width / 2 - .095)), .005, .004, 4, BLACK)
        else:   # drop
            w = width / 2
            pts = [P(su, sh, 0), P(su, sh, s * w * .35), P(su + .005, sh, s * w), P(su + .075, sh - .015, s * (w + .005)), P(su + .125, sh - .065, s * (w + .008)),
                   P(su + .11, sh - .125, s * (w + .01)), P(su + .04, sh - .14, s * (w + .006))]
            ptube(m, pts, .0115, 5, BLACK, cap=True)
            cuboid(m, P(su + .04, sh - .008, s * w), .045, .024, .02, (.03, .03, .03), tu=.8, shift=.015)   # brake hood

def rack(m, G, h=.735, front=-.20, rear=-.52, wide=.12, col=STEEL):
    ru, R = G["ru"], G["Rr"]
    obox(m, P(front, h, 0), P(rear, h, 0), wide, .008, col)
    for s in (-1, 1):
        tube(m, P(front + .01, h - .004, s * .055), P(rear - .01, h - .004, s * .055), .0055, .0055, 4, col)
        tube(m, P(rear, h - .004, s * .055), P(ru, R, s * .066), .005, .005, 4, col)
        tube(m, P((front + rear) / 2, h - .004, s * .055), P(ru, R, s * .066), .005, .005, 4, col)
    cuboid(m, P(rear - .015, h - .01, 0), .014, .016, .03, RED)

def panniers(m, G, col, h=.73, u=-.37, hu=.14, hh=.15, hx=.065, gap=.075):
    for s in (-1, 1):
        cuboid(m, P(u, h - hh - .005, s * (gap + hx)), hu, hh, hx, col, tx=1.0, tu=.92)

def basket(m, G, u0=.40, u1=.68, h0=.74, h1=.96, hx0=.15, hx1=.17, sup=True):
    cs = {}
    def c(uu, hh, xx): return P(uu, hh, xx)
    quads = [([c(u0, h0, -hx0), c(u1, h0, -hx0), c(u1, h0, hx0), c(u0, h0, hx0)], (0, -1, 0)),
             ([c(u1, h0, -hx0), c(u1, h1, -hx1), c(u1, h1, hx1), c(u1, h0, hx0)], (0, 0, -1)),
             ([c(u0, h0, -hx0), c(u0, h1, -hx1), c(u0, h1, hx1), c(u0, h0, hx0)], (0, 0, 1)),
             ([c(u0, h0, -hx0), c(u1, h0, -hx0), c(u1, h1, -hx1), c(u0, h1, -hx1)], (-1, 0, 0)),
             ([c(u0, h0, hx0), c(u1, h0, hx0), c(u1, h1, hx1), c(u0, h1, hx1)], (1, 0, 0))]
    for q, nrm in quads:
        uvs = [uvmap("grid", 0, 1), uvmap("grid", 1, 1), uvmap("grid", 1, 0), uvmap("grid", 0, 0)]
        m.add(q, np.tile(nz(np.array(nrm, float)), (4, 1)), [(0, 1, 2), (0, 2, 3)], WHITE, 0.0, uvs)
    if sup:
        for s in (-1, 1):
            tube(m, P(u1 - .02, h0, s * .1), P(G["fu"], G["Rf"], s * .052), .005, .005, 4, STEEL)
            tube(m, P(u0 + .02, h0, s * .08), uh(G["hbot"], s * .04), .005, .005, 4, STEEL)

def lamp_front(m, G, h=.86, u=.50):
    tube(m, P(u, h, 0), P(u + .045, h, 0), .026, .03, 6, (.55, .55, .56), cap=True)

def kidseat(m, G, col, h=.745, u=-.37):
    cuboid(m, P(u, h + .03, 0), .15, .018, .125, col)
    cuboid(m, P(u - .17, h + .22, 0), .018, .19, .135, col, tu=1.0, shift=-.07)
    for s in (-1, 1):
        cuboid(m, P(u - .02, h + .10, s * .13), .13, .075, .012, col, tu=.8, shift=-.03)
        obox(m, P(u + .03, h + .02, s * .15), P(u + .12, h - .26, s * .165), .02, .035, (.1, .1, .1), up=(1., 0, 0))
        cuboid(m, P(u + .13, h - .27, s * .165), .05, .007, .032, col)
    tube(m, P(u + .13, h + .09, -.13), P(u + .13, h + .09, .13), .01, .01, 5, (.1, .1, .12))

def kickstand(m, G, x=-.07):
    ru = G["ru"]; tube(m, P(ru + .30, G["bb"][1] + .03, x), P(ru + .17, G["bb"][1] + .04, x), .008, .008, 4, STEEL)

def lean_stand(m, G, ang):
    """Kickstand extended to the ground for the *_lean variant (leans by ang degrees to the left)."""
    ru = G["ru"]; tube(m, P(ru + .30, G["bb"][1] + .03, -.07), P(ru + .36, .20 * np.tan(np.deg2rad(ang)), -.20), .009, .009, 4, STEEL)
