"""Zuerich HB Hauptgebaeude, outer shell (Wanner 1871 Neorenaissance): Suedtrakt facade to the Bahnhofplatz with triumphal-arch portal,
Wannerhalle (Haupthalle) barrel roof with 7 skylight ridges, Nordtrakt barrel roof, Querhalle barrel vault, east gable to the Bahnhofquai.
Sources/dimensions: hb_geom.py, research/hb/README.md. No photos as textures, no logos."""
import sys
from hb_kit import *
import hb_geom as G
from k45_volkshaus import plaster

SAND = hexl = None


def stone_tex(col=(198, 190, 172, 255)):
    a = D.ashlar(col, size=128, rows=8, seed=5, rough=0.05, joint=0.84)
    return a


def build():
    rng = np.random.default_rng(71)
    m = Model("hb_shell")
    SAND_C, SAND_D, TRIM, SLATE, ROOF_Z, STEEL = W, hx("#e4ddcb"), hx("#e9e2cf"), hx("#5d6268"), hx("#7c8a86"), hx("#4b4f52")
    mw = m.mat("wall", stone_tex())
    def sign(d, de, x, y, w, h):   # neutral clock dial (Arabic numerals) for the portal attic; strip px x 256..288
        cx, cy = x + 272, y + 16
        d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=(40, 40, 42)); d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(238, 234, 222))
        d.line([cx, cy, cx - 6, cy - 8], fill=(30, 30, 30), width=2); d.line([cx, cy, cx + 8, cy - 9], fill=(30, 30, 30), width=1)
        de.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(60, 56, 40))
    base, em = D.glass_atlas_g(frame="#e6dcc4", glass="#2a3641", sky="#8aa3b6", cols=2, rows=4, seed=9, lit_p=0.55, cw=64, ch=96, curtains=False, sign=sign)
    mg = m.mat("glass", base, em, rough=0.3)
    mf = m.mat("flat", Image.new("RGBA", (8, 8), (255, 255, 255, 255)))

    def run(a, b, zb, fh, bayw, hole_fn, depth=0.45, wall_col=W, reveal=None, surr=None, surr_w=0.35, sill=0.0, wmod=(4.0, 4.0)):
        L, t, n = D.frame_of(a, b); nb = max(1, int(round(L / bayw))); bw = L / nb
        for i in range(nb):
            u0, u1 = i * bw, (i + 1) * bw
            hole = hole_fn(u0, u1, zb, zb + fh, i, nb, L)
            if hole is None:
                D.poly_wall(m, mw, Polygon(D.rect_pts(u0, zb, u1, zb + fh)), a, t, n, 0.0, wall_col, lambda u, z: (u / wmod[0], z / wmod[1])); continue
            D.bay(m, mw, mg, mf, a, t, n, u0, u1, zb, zb + fh, hole, depth, int(rng.integers(0, D.NV)), wall_col, reveal or SAND_D, wmod, None)
            if surr: D.surround(m, mf, a, t, n, hole, surr_w, surr, 0.06, sill)

    def arch(w, lo, hs, hh):
        def f(u0, u1, z0, z1, i, nb, L):
            uc = (u0 + u1) / 2; ww = min(w, (u1 - u0) - 0.8); return D.arch_pts(uc - ww / 2, z0 + lo, uc + ww / 2, z0 + hs)
        return f

    def rect(w, lo, hh):
        def f(u0, u1, z0, z1, i, nb, L):
            uc = (u0 + u1) / 2; ww = min(w, (u1 - u0) - 0.8); return D.rect_pts(uc - ww / 2, z0 + lo, uc + ww / 2, z0 + lo + hh)
        return f

    def cornice(a, b, z, h=0.6, out=0.55, col=TRIM):
        D.band(m, mf, a, b, z, z + h, out, col)

    # ------------------------------------------------------------------ Suedtrakt facade (south, towards the Bahnhofplatz)
    # real outline (swissBUILDINGS3D footprint): projecting end pavilions, recessed wings, central risalit with the triumphal-arch portal
    cb = G.S_C1                                   # back of the facade block (c -45)
    pd0, pd1 = G.PORTAL_D - 7.5, G.PORTAL_D + 7.5
    pieces = []                                   # (d0, d1, c_face, eave, floor heights)
    for (f0, f1, cf, ev) in G.FACADE:
        if f0 == 36.0:    # risalit: pylons either side of the portal opening
            pieces += [(f0, pd0, cf, ev), (pd1, f1, cf, ev)]
        else:
            pieces.append((f0, f1, cf, ev))
    for (a_d, b_d, cf, ev) in pieces:
        fh1, fh2 = 6.5, 5.5 if ev > 16 else 5.0
        fh3 = ev - fh1 - fh2
        a, b = (a_d, cf), (b_d, cf)
        run(a, b, 0.0, fh1, 4.6, arch(3.1, 0.0, 4.5, 4.6), 0.5, SAND_D, SAND_D, TRIM, 0.3)                      # rusticated ground floor, arched openings
        run(a, b, fh1, fh2, 4.6, arch(2.4, 0.9, 4.8, 4.1), 0.4, SAND_C, SAND_D, TRIM, 0.3, 0.35)                # piano nobile
        run(a, b, fh1 + fh2, fh3, 4.6, rect(2.0, 0.8, fh3 - 1.7), 0.35, SAND_C, SAND_D, TRIM, 0.22)              # upper floor
        cornice(a, b, fh1 - 0.2, 0.35, 0.3); cornice(a, b, fh1 + fh2 - 0.2, 0.4, 0.35); cornice(a, b, ev, 0.7, 0.8)
    # returns between the facade planes (and the side faces at the ends)
    for (d_, c_a, c_b, e_) in ((-8.0, -47.0, -67.0, 17.5), (6.0, -67.0, -63.0, 17.5), (36.0, -63.0, -68.0, 18.5), (60.0, -68.0, -62.0, 18.5), (90.0, -62.0, -66.0, 17.5), (105.0, -66.0, -45.0, 17.5)):
        if d_ in (-8.0, 105.0):
            a, b = ((d_, c_a), (d_, c_b)) if d_ == 105.0 else ((d_, c_b), (d_, c_a))
            run(a, b, 0.0, 6.5, 5.5, arch(2.6, 0.6, 5.0, 4.4), 0.45, SAND_D, SAND_D, TRIM, 0.3)
            run(a, b, 6.5, 5.5, 5.5, arch(2.2, 0.9, 4.8, 4.0), 0.4, SAND_C, SAND_D, TRIM, 0.3)
            run(a, b, 12.0, e_ - 12.0, 5.5, rect(1.9, 0.8, e_ - 13.7), 0.35, SAND_C, SAND_D, TRIM, 0.22)
        else:
            wall(m, mw, (d_, c_a), (d_, c_b), 0, e_, SAND_C, mod=(4, 4), double=True)
    # portal: triumphal arch (pylon crowns, attic over the opening)
    cf = -68.0
    m.box(mw, G.PORTAL_D, cf - 0.3, 17.0, 1.8, 15.8, 19.7, col=SAND_C, mod=(3, 3), mr=mf, rcol=TRIM)       # attic over the arch
    m.box(mf, G.PORTAL_D, cf - 0.3, 18.4, 2.1, 19.7, 20.8, col=TRIM)
    for xc in (pd0 - 1.6, pd0 + 1.4, pd1 - 1.4, pd1 + 1.6):   # paired columns flanking the arch (photos Exterior #396 #397)
        m.cylinder(mw, xc, cf - 1.0, 0.6, 0, 13.0, n=10, col=SAND_C, mod=(3, 3))
        bx(m, mf, xc - 0.8, xc + 0.8, cf - 1.8, cf - 0.2, 13.0, 13.8, TRIM, top=True); bx(m, mf, xc - 0.8, xc + 0.8, cf - 1.8, cf - 0.2, 0, 0.5, TRIM, top=True)
    bx(m, mf, pd0 - 2.6, pd1 + 2.6, cf - 1.9, cf - 0.1, 13.8, 15.0, TRIM, top=True)                      # entablature over the columns
    for xs in (pd0 - 1.0, pd1 + 1.0):   # sculpture plinths with figures (stylised)
        bx(m, mf, xs - 0.9, xs + 0.9, cf - 1.4, cf - 0.4, 19.7, 21.0, SAND_D, top=True); m.cylinder(mf, xs, cf - 0.9, 0.45, 21.0, 24.0, n=6, col=hx("#8b8577"), r1=0.25)
    pc = (G.PORTAL_D, cf - 1.22)
    m.quad(mg, [(pc[0] - 1.6, pc[1], 16.4), (pc[0] + 1.6, pc[1], 16.4), (pc[0] + 1.6, pc[1], 19.6), (pc[0] - 1.6, pc[1], 19.6)], [(256 / 512, 0.0), (288 / 512, 0.0), (288 / 512, 0.25), (256 / 512, 0.25)], W)
    a, b = (pd0, cf), (pd1, cf); L, t, n = D.frame_of(a, b)
    D.poly_wall(m, mw, Polygon(D.rect_pts(0, 0, L, 18.5)).difference(Polygon(D.arch_pts(0.0, 0, L, 9.5))), a, t, n, 0.0, SAND_C, lambda u, z: (u / 4, z / 4))
    # roofs: mansard slate with a flat cap per facade piece
    for (a_d, b_d, cf_, ev) in G.FACADE:
        zE = ev + 0.7; cap_z = ev + 3.2
        ring = [(a_d, cf_), (b_d, cf_), (b_d, cb), (a_d, cb)]
        for i in range(4):
            p, q_ = ring[i], ring[(i + 1) % 4]; L, t, n = D.frame_of(p, q_)
            ins = (-n[0] * 3.0, -n[1] * 3.0)
            m.quad(mf, [(p[0], p[1], zE), (q_[0], q_[1], zE), (q_[0] + ins[0], q_[1] + ins[1], cap_z), (p[0] + ins[0], p[1] + ins[1], cap_z)], col=SLATE)
        m.flat(mf, Polygon([(a_d + 3, cf_ + 3 if cf_ < cb else cf_ - 3), (b_d - 3, cf_ + 3), (b_d - 3, cb - 3), (a_d + 3, cb - 3)]), cap_z, ROOF_Z)
    # inner low part of the Suedtrakt (c -45..-25), flat 11 m
    bx(m, mw, G.HALL_D0, G.HALL_D1 + 1, G.S_C1, G.HALL_C0, 0, G.WING_LOW, SAND_D, top=True, colt=ROOF_Z, mod=(4, 4), sides=(0, 1, 0, 1))
    # ------------------------------------------------------------------ Wannerhalle: clerestory walls above the wings + barrel roof + skylights
    z0, z1 = G.WING_LOW, G.HALL_EAVE
    for cc, sgn in ((G.HALL_C0, 1), (G.HALL_C1, -1)):
        a, b = ((G.HALL_D0, cc), (G.HALL_D1, cc)) if sgn > 0 else ((G.HALL_D1, cc), (G.HALL_D0, cc))
        run(a, b, z0, z1 - z0, 9.1, arch(3.4, 1.2, 7.2, 8.0), 0.5, SAND_C, SAND_D, TRIM, 0.3)
        cornice(a, b, z1, 0.7, 0.9)
    # east gable towards the Bahnhofquai: arcade of 7 doors, two big arched windows + small ones (photos Haupthalle #24 #25 #38)
    a, b = (G.HALL_D1, G.HALL_C0), (G.HALL_D1, G.HALL_C1)
    L, t, n = D.frame_of(a, b)
    lows = [3.0 + 6.0 * k for k in range(7)]; ups = [(10.5, 9.6, 9.8, 14.8), (31.5, 9.6, 9.8, 14.8), (21.0, 2.6, 11.0, 15.4), (2.2, 2.0, 11.0, 15.0), (39.8, 2.0, 11.0, 15.0)]
    holes = [D.arch_pts(u - 1.8, 0, u + 1.8, 4.0) for u in lows] + [D.arch_pts(u - w / 2, z0_, u + w / 2, hs) for u, w, z0_, hs in ups]
    poly = Polygon(D.rect_pts(0, 0, L, z1))
    for h in holes: poly = poly.difference(Polygon(h))
    D.poly_wall(m, mw, poly, a, t, n, 0.0, SAND_C, lambda u, z: (u / 4, z / 4))
    for h in holes:
        pts = [D.P3(a, t, n, u, z, -0.5) for u, z in h]
        for k in range(1, len(pts) - 1): m.tri(mg, [pts[0], pts[k], pts[k + 1]], [(0.06, 0.6)] * 3, W)
    cornice(a, b, 6.2, 0.35, 0.3); cornice(a, b, 9.4, 0.4, 0.4)
    cap_arch(m, mw, 'd', G.HALL_D1, (G.HALL_C0 + G.HALL_C1) / 2, 21.0, z1, G.HALL_CROWN - z1, SAND_C, 10, 1, z0=z1)
    barrel(m, mf, 'd', G.HALL_D0, G.HALL_D1, (G.HALL_C0 + G.HALL_C1) / 2, 21.0, z1, G.HALL_CROWN - z1, ROOF_Z, n=8, inside=False)
    # west gable above the Querhalle roof: big glazed grid window
    a, b = (G.HALL_D0, G.HALL_C1), (G.HALL_D0, G.HALL_C0)
    L, t, n = D.frame_of(a, b)
    D.poly_wall(m, mw, Polygon(D.rect_pts(0, 11.0, L, z1)).difference(Polygon(D.rect_pts(3.0, 11.8, 39.0, 19.6))), a, t, n, 0.0, SAND_C, lambda u, z: (u / 4, z / 4))
    q(m, mg, [D.P3(a, t, n, 3.0, 11.8, -0.4), D.P3(a, t, n, 39.0, 11.8, -0.4), D.P3(a, t, n, 39.0, 19.6, -0.4), D.P3(a, t, n, 3.0, 19.6, -0.4)], W, [(0.0, 0.25), (1 / 8, 0.25), (1 / 8, 1.0), (0.0, 1.0)], (n[0], n[1], 0))
    cornice(a, b, z1, 0.7, 0.9)
    cap_arch(m, mw, 'd', G.HALL_D0, (G.HALL_C0 + G.HALL_C1) / 2, 21.0, z1, G.HALL_CROWN - z1, SAND_C, 10, -1, z0=z1)
    # skylight ridges (transverse prisms with glass)
    for xd in G.LANT_X:
        cm = (G.HALL_C0 + G.HALL_C1) / 2; hw = 15.75; zb = G.HALL_CROWN - 0.4
        for s in (-1, 1):
            q(m, mg, [(xd - 6.0 * s, cm - hw, zb - 0.6), (xd - 6.0 * s, cm + hw, zb - 0.6), (xd - 1.6 * s, cm + hw, G.HALL_LANT), (xd - 1.6 * s, cm - hw, G.HALL_LANT)],
              W, [(0, 0.5), (0.5, 0.5), (0.5, 1.0), (0, 1.0)], (-s * 0.5, 0, 1))
        q(m, mf, [(xd - 1.6, cm - hw, G.HALL_LANT), (xd + 1.6, cm - hw, G.HALL_LANT), (xd + 1.6, cm + hw, G.HALL_LANT), (xd - 1.6, cm + hw, G.HALL_LANT)], hx("#8d9aa0"), None, (0, 0, 1))
        for s in (-1, 1):   # end gables of the skylight
            tri(m, mf, [(xd - 6.0, cm + s * hw, zb - 0.6), (xd + 6.0, cm + s * hw, zb - 0.6), (xd, cm + s * hw, G.HALL_LANT)], hx("#8d9aa0"), None, (0, s, 0))
    # ------------------------------------------------------------------ Nordtrakt
    d0n, d1n, c0n, c1n = G.N_D0, G.N_D1, G.N_C0, G.N_C1
    a, b = (d1n, c1n), (d0n, c1n)
    run(a, b, 0.0, 6.0, 5.0, arch(2.6, 0.6, 5.0, 4.4), 0.45, SAND_D, SAND_D, TRIM, 0.3)
    run(a, b, 6.0, 5.0, 5.0, arch(2.2, 0.8, 4.6, 3.8), 0.4, SAND_C, SAND_D, TRIM, 0.3)
    run(a, b, 11.0, 4.0, 5.0, rect(1.9, 0.6, 2.8), 0.35, SAND_C, SAND_D, TRIM, 0.22)
    cornice(a, b, G.N_EAVE - 0.4, 0.6, 0.7)
    for a, b in (((d1n, c0n), (d1n, c1n)), ((d0n, c1n), (d0n, c0n))):
        run(a, b, 0.0, 6.0, 5.5, arch(2.4, 0.6, 5.0, 4.4), 0.45, SAND_D, SAND_D, TRIM, 0.3)
        run(a, b, 6.0, 5.0, 5.5, arch(2.0, 0.8, 4.6, 3.8), 0.4, SAND_C, SAND_D, TRIM, 0.3)
        run(a, b, 11.0, 4.0, 5.5, rect(1.8, 0.6, 2.8), 0.35, SAND_C, SAND_D, TRIM, 0.22)
    a, b = (d0n, c0n), (d1n, c0n)   # wall towards the hall (c = 17): low part only (above 15 m the hall wall rises)
    # (no wall here: the hall side is drawn by hb_inner, the outside is the Nordtrakt facade)
    barrel(m, mf, 'd', d0n, d1n, (c0n + c1n) / 2, 20.0, G.N_EAVE, G.N_CROWN - G.N_EAVE, SLATE, n=6, inside=False)
    cap_arch(m, mw, 'd', d1n, (c0n + c1n) / 2, 20.0, G.N_EAVE, G.N_CROWN - G.N_EAVE, SAND_C, 6, 1)
    cap_arch(m, mw, 'd', d0n, (c0n + c1n) / 2, 20.0, G.N_EAVE, G.N_CROWN - G.N_EAVE, SAND_C, 6, -1)
    # ------------------------------------------------------------------ Querhalle (barrel along c); the platform side (d = -45) stays open
    qd0, qd1, qc0, qc1 = G.Q_D0, G.Q_D1, G.Q_C0, G.Q_C1; qm = (qd0 + qd1) / 2
    barrel(m, mf, 'c', qc0, qc1, qm, 12.5, G.Q_EAVE, G.Q_CROWN - G.Q_EAVE, hx("#8da3ae"), n=10, inside=False)
    for cc, face in ((qc0, -1), (qc1, 1)):   # end gables with a big arched window
        cap_arch(m, mw, 'c', cc, qm, 12.5, G.Q_EAVE, G.Q_CROWN - G.Q_EAVE, SAND_C, 8, face, z0=0)
    # glazed arch in the south end gable
    m.quad(mg, [(qd0 + 3.5, qc0 - 0.25, 3), (qd1 - 3.5, qc0 - 0.25, 3), (qd1 - 3.5, qc0 - 0.25, 12), (qd0 + 3.5, qc0 - 0.25, 12)], [(0, .25), (3 / 8, .25), (3 / 8, 1), (0, 1)], W)
    info(m, "hb_shell")
    return m


if __name__ == "__main__":
    m = build()
    register(m, "hb_shell", "Zürich Hauptbahnhof", [], hide_ids=[])
