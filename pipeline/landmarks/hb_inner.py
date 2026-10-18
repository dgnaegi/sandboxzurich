"""Zuerich HB walkable interior: Wannerhalle (Haupthalle, 133 x 42 m), portal tunnel from the Bahnhofplatz, Querhalle (cross hall at the platform heads).
Loaded only near the player (load_r). Colliders = thin wall rings (world metres), registered with walkable=true so the swissBUILDINGS3D footprints
are not solid. Textures painted procedurally; neutral lettering; clocks/boards are generic designs (no SBB logo, not the SBB station clock)."""
from hb_kit import *
import hb_geom as G
import hb_props as P
from shapely.ops import unary_union
from shapely.geometry import LineString

CREAM, STONE, STONE_D, TRIM = hx("#d9cfb8"), W, hx("#d8c9a8"), hx("#dccfae")
VAULT, STEEL, FLOORA, FLOORB = hx("#444a47"), hx("#5b4a3b"), hxw("#4a4a4a", (1.3, 1.0, 0.78)), hxw("#444444", (1.3, 1.0, 0.78))
SKY = hx("#ffffff"); FRIEZE = hx("#b4705e")
import hb3_spec
WELLS3 = [w for w in hb3_spec.WELLS if w[0] < 0 and w[3] < 0 and w[2] > -64]   # wells inside the Querhalle floor (hb3_spec.WELLS[0])
COLL = []   # collider walls: (a, b, thickness) in the model frame


def wallc(a, b, th=0.9):
    COLL.append((a, b, th))


def build():
    rng = np.random.default_rng(5)
    m = Model("hb_inner")
    A = P.make_atlas()
    from hb_shell import stone_tex
    mw = m.mat("wall", stone_tex((176, 158, 130, 255))); ms = m.mat("sign", *A.images(), rough=0.8); mf = m.mat("flat", Image.new("RGBA", (8, 8), (255, 255, 255, 255)))
    HM = (G.HALL_C0 + G.HALL_C1) / 2            # -4
    d0, d1, c0, c1 = G.HALL_D0, G.HALL_D1, G.HALL_C0, G.HALL_C1

    # ---------------------------------------------------------------- floors (3 m tiles, small tint variation)
    LIGHT = hxw("#8e8e8e", (1.25, 1.0, 0.8))
    def floor(x0, x1, y0, y1, z=G.FLOOR, ts=2.5, bands=True, light_all=False):
        nx, ny = max(1, int(round((x1 - x0) / ts))), max(1, int(round((y1 - y0) / ts)))
        for i in range(nx):
            for j in range(ny):
                xa, xb = x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx; ya, yb = y0 + (y1 - y0) * j / ny, y0 + (y1 - y0) * (j + 1) / ny
                xc, yc = (xa + xb) / 2, (ya + yb) / 2
                lit = light_all or (bands and (abs(yc - HM) < 2.6 or any(abs(xc - bd) < 2.6 for bd in (8.0, 47.0, 86.0))))
                base = LIGHT if lit else (FLOORA if (i + j) % 2 else FLOORB)
                t = 0.95 + 0.07 * rng.random()
                col_ = tuple(int(v * t) for v in base[:3]) + (255,)
                hole = next((h_ for h_ in WELLS3 if xa < h_[1] and xb > h_[0] and ya < h_[3] and yb > h_[2]), None)   # hb3: stair well in the floor
                if hole is None: slab(m, mf, xa, xb, ya, yb, z, col_); continue
                for r_ in ((xa, hole[0], ya, yb), (hole[1], xb, ya, yb), (max(xa, hole[0]), min(xb, hole[1]), ya, hole[2]), (max(xa, hole[0]), min(xb, hole[1]), hole[3], yb)):
                    if r_[1] - r_[0] > 0.01 and r_[3] - r_[2] > 0.01: slab(m, mf, r_[0], r_[1], r_[2], r_[3], z, col_)
    floor(d0 - 1, d1 + 1, c0, c1)
    floor(G.Q_D0, G.Q_D1 + 1, G.Q_C0, G.Q_C1, bands=False, light_all=True)
    floor(40.5, 55.5, -68.0, c0 + 0.1, bands=False, light_all=True)
    # ---------------------------------------------------------------- openings (arch recesses with shops, clerestory windows)
    def poly_in(a, b, poly, col, wmod=(4.0, 4.0)):
        L, t, n = D.frame_of(a, b)
        D.poly_wall(m, mw, poly, a, t, n, 0.0, col, lambda u, z: (u / wmod[0], z / wmod[1]))

    def reveal(a, t, n, hole, depth, col):
        h = list(hole)
        for i in range(len(h)):
            p, q_ = h[i], h[(i + 1) % len(h)]
            if math.hypot(q_[0] - p[0], q_[1] - p[1]) < 1e-4: continue
            du, dz = q_[0] - p[0], q_[1] - p[1]; l = math.hypot(du, dz); nl = (t[0] * (-dz / l), t[1] * (-dz / l), du / l)
            D._oriented(m, mf, [D.P3(a, t, n, p[0], p[1], 0), D.P3(a, t, n, q_[0], q_[1], 0), D.P3(a, t, n, q_[0], q_[1], -depth), D.P3(a, t, n, p[0], p[1], -depth)], nl, [(0, 0), (1, 0), (1, 1), (0, 1)], col)

    def wall_with_holes(a, b, z0, z1, holes, col, wmod=(4.0, 4.0), depth=0.6, rcol=STONE_D):
        L, t, n = D.frame_of(a, b)
        poly = Polygon(D.rect_pts(0, z0, L, z1))
        for h in holes: poly = poly.difference(Polygon(h))
        poly_in(a, b, poly, col, wmod)
        for h in holes: reveal(a, t, n, h, depth, rcol)
        return L, t, n

    def shop_recess(a, t, n, u0, u1, zt, depth, idx):
        """Shop behind an arch opening (u0..u1 on the wall frame a/t/n, pointing away from the room by -n): back wall, sides, ceiling, floor, sign."""
        bc = [hx("#e9d9b8"), hx("#dfe6e0"), hx("#f0d6c4"), hx("#d6dce8")][idx % 4]
        zA = zt
        for (ua, ub, col, nn, zz0, zz1) in ((u0, u1, bc, None, 0, zA),):
            p0, p1 = D.P3(a, t, n, ua, zz0, -depth), D.P3(a, t, n, ub, zz0, -depth)
            q(m, mf, [p0, p1, (p1[0], p1[1], zz1), (p0[0], p0[1], zz1)], col, None, (n[0], n[1], 0))
        for ua, sg in ((u0, 1), (u1, -1)):   # side walls
            p0, p1 = D.P3(a, t, n, ua, 0, 0), D.P3(a, t, n, ua, 0, -depth)
            q(m, mf, [p0, p1, (p1[0], p1[1], zA), (p0[0], p0[1], zA)], hx("#cdbf9f"), None, (t[0] * sg, t[1] * sg, 0))
        p0, p1, p2, p3 = D.P3(a, t, n, u0, 0, 0), D.P3(a, t, n, u1, 0, 0), D.P3(a, t, n, u1, 0, -depth), D.P3(a, t, n, u0, 0, -depth)
        q(m, mf, [p0, p1, p2, p3], hx("#8f6f4d"), None, (0, 0, 1))
        for (zz, col, nn) in ((zA - 0.4, hx("#f4efe4"), (0, 0, -1)),):
            q(m, mf, [D.P3(a, t, n, u0, zz, 0), D.P3(a, t, n, u1, zz, 0), D.P3(a, t, n, u1, zz, -depth), D.P3(a, t, n, u0, zz, -depth)], col, None, nn)
        # counter + shelf block and an emissive lamp
        uc = (u0 + u1) / 2; pc = D.P3(a, t, n, uc, 0, -depth * 0.45)
        bx(m, mf, pc[0] - 0.3, pc[0] + 0.3, pc[1] - 0.3, pc[1] + 0.3, 0, 1.0, hx("#6e5a42"), top=True) if abs(n[0]) < 0.5 else bx(m, mf, pc[0] - 0.3, pc[0] + 0.3, pc[1] - 0.3, pc[1] + 0.3, 0, 1.0, hx("#6e5a42"), top=True)
        lp = D.P3(a, t, n, uc, zA - 0.45, -depth * 0.5)
        P.box_uv(m, ms, lp[0] - 0.4, lp[0] + 0.4, lp[1] - 0.4, lp[1] + 0.4, lp[2] - 0.05, lp[2] + 0.05, A.rects["lamp"])

    def arcade_wall(a, b, u_of, gap=None, sign_off=0):
        """Hall long wall seen from inside (photos Haupthalle #26 #33 #38): lower arcade of 3.2 m arches (shops/doors) to 6.2 m, stone band + frieze,
        above it per 18.2 m bay one big arched window (7.4 m) flanked by two small ones; cornice at the eaves. u_of(d) -> position on the wall."""
        L, t, n = D.frame_of(a, b)
        holes, lows, ups = [], [], []
        pitch = 4.75
        for i in range(int(L // pitch)):
            uc = (i + 0.5) * pitch + (L - int(L // pitch) * pitch) / 2
            if gap and gap[0] - 2.0 < uc < gap[1] + 2.0: continue
            lows.append(uc); holes.append(D.arch_pts(uc - 1.6, 0.0, uc + 1.6, 4.6))
        for xd in G.LANT_X:
            for off, w, z0_, hs in ((0.0, 7.2, 9.0, 15.2), (-6.0, 2.8, 10.0, 15.8), (6.0, 2.8, 10.0, 15.8)):
                uc = u_of(xd + (off if u_of(1) > u_of(0) else -off))
                if uc < 2 or uc > L - 2 or (gap and gap[0] - 4.2 < uc < gap[1] + 4.2): continue
                ups.append((uc, w, z0_, hs)); holes.append(D.arch_pts(uc - w / 2, z0_, uc + w / 2, hs))
        if gap: holes.append(D.arch_pts(gap[0], 0.0, gap[1], 9.5))
        wall_with_holes(a, b, 0.0, 21.0, holes, STONE, depth=0.7)
        for k, uc in enumerate(lows):
            shop_recess(a, t, n, uc - 1.6, uc + 1.6, 4.6, 5.0, k)
            R = A.rects[f"shop{(k + sign_off) % len(P.SHOPS)}"]
            p0, p1 = D.P3(a, t, n, uc - 1.4, 5.0, 0.06), D.P3(a, t, n, uc + 1.4, 5.0, 0.06)
            m.quad(ms, [p0, p1, (p1[0], p1[1], 5.9), (p0[0], p0[1], 5.9)], uvr(R), W)
        for uc, w, z0_, hs in ups:
            hh = D.arch_pts(uc - w / 2, z0_, uc + w / 2, hs); pts = [D.P3(a, t, n, u, z, -0.7) for u, z in hh]
            for k in range(1, len(pts) - 1): D._oriented(m, mf, [pts[0], pts[k], pts[k + 1]], (n[0], n[1], 0), [(0, 0), (1, 0), (1, 1)], SKY)
            if w > 5:   # tracery: mullions + transom
                for fr in (0.25, 0.5, 0.75):
                    p0, p1 = D.P3(a, t, n, uc - w / 2 + w * fr, z0_, -0.65), D.P3(a, t, n, uc - w / 2 + w * fr, hs + 2.0, -0.65)
                    bx(m, mf, min(p0[0], p1[0]) - 0.06, max(p0[0], p1[0]) + 0.06, min(p0[1], p1[1]) - 0.06, max(p0[1], p1[1]) + 0.06, z0_, hs + 0.2, STONE_D, top=False)
        D.band(m, mf, a, b, 6.4, 6.9, 0.35, TRIM)
        D.poly_wall(m, mf, Polygon(D.rect_pts(0, 7.0, L, 9.4)), a, t, n, 0.1, FRIEZE, lambda u, z: (0, 0))   # rosy frieze band
        D.band(m, mf, a, b, 9.4, 9.8, 0.45, TRIM)
        D.band(m, mf, a, b, 20.4, 21.0, 0.6, TRIM)
        for xd in G.LANT_X + [G.LANT_X[-1] + 18.2, G.LANT_X[0] - 18.2]:   # pilasters at the bay boundaries
            u = u_of(xd - 9.1)
            if 0.5 < u < L - 0.5:
                p = D.P3(a, t, n, u, 0, 0.2); m.box(mw, p[0], p[1], 1.0, 0.4, 0, 21.0, rot=math.atan2(t[1], t[0]), col=STONE, mod=(2, 4), mr=mf, rcol=STONE)

    # hall long walls: south (c0, faces +c, walked from d1 to d0) with the portal opening; north (c1, faces -c)
    arcade_wall((d1, c0), (d0, c0), lambda d: d1 - d, gap=(d1 - 55.5, d1 - 40.5), sign_off=0)
    arcade_wall((d0, c1), (d1, c1), lambda d: d - d0, sign_off=5)
    # portal arch frame (south)
    # hall east end (d1): faces -d; photos Haupthalle #24 #25 #38: arcade of green doors, two big arched windows, small arches between
    a, b = (d1, c1), (d1, c0)
    L, t, n = D.frame_of(a, b)
    lows = [3.0 + 6.0 * k for k in range(7)]
    ups = [(10.5, 9.6, 9.8, 14.8), (31.5, 9.6, 9.8, 14.8), (21.0, 2.6, 11.0, 15.4), (2.2, 2.0, 11.0, 15.0), (39.8, 2.0, 11.0, 15.0)]
    holes = [D.arch_pts(u - 1.8, 0, u + 1.8, 4.0) for u in lows] + [D.arch_pts(u - w / 2, z0_, u + w / 2, hs) for u, w, z0_, hs in ups]
    wall_with_holes(a, b, 0, 21.0, holes, STONE, depth=0.8)
    for u in lows:
        hh = D.arch_pts(u - 1.8, 0, u + 1.8, 4.0); pts = [D.P3(a, t, n, uu, z, -0.7) for uu, z in hh]
        for k in range(1, len(pts) - 1): D._oriented(m, mf, [pts[0], pts[k], pts[k + 1]], (n[0], n[1], 0), [(0, 0), (1, 0), (1, 1)], hx("#2f5a55"))
    for u, w, z0_, hs in ups:
        hh = D.arch_pts(u - w / 2, z0_, u + w / 2, hs); pts = [D.P3(a, t, n, uu, z, -0.7) for uu, z in hh]
        for k in range(1, len(pts) - 1): D._oriented(m, mf, [pts[0], pts[k], pts[k + 1]], (n[0], n[1], 0), [(0, 0), (1, 0), (1, 1)], SKY)
    D.band(m, mf, a, b, 6.4, 6.9, 0.35, TRIM); D.band(m, mf, a, b, 9.4, 9.8, 0.45, TRIM); D.band(m, mf, a, b, 20.4, 21.0, 0.6, TRIM)
    cap_arch(m, mw, 'd', d1 - 0.02, HM, 21.0, 21.0, 4.0, STONE, 10, -1, z0=21.0)
    # hall west end (d0): faces +d; three arches towards the Querhalle and above them the big glazed grid window (photos Haupthalle #7 #20 #33)
    a, b = (d0, c0), (d0, c1)
    L, t, n = D.frame_of(a, b)
    holes = [D.arch_pts(1.5 + k * 13.4, 0, 1.5 + k * 13.4 + 12.0, 4.5) for k in range(3)]
    win = D.rect_pts(3.0, 11.8, 39.0, 19.6)
    wall_with_holes(a, b, 0, 21.0, holes + [win], STONE, depth=1.0)
    q(m, mf, [D.P3(a, t, n, 3.0, 11.8, -0.9), D.P3(a, t, n, 39.0, 11.8, -0.9), D.P3(a, t, n, 39.0, 19.6, -0.9), D.P3(a, t, n, 3.0, 19.6, -0.9)], SKY, None, (n[0], n[1], 0))
    for k in range(1, 12):
        p0 = D.P3(a, t, n, 3.0 + 3.0 * k, 11.8, -0.8); bx(m, mf, p0[0] - 0.05, p0[0] + 0.05, p0[1] - 0.05, p0[1] + 0.05, 11.8, 19.6, STEEL, top=False)
    for z_ in (14.4, 17.0):
        p0, p1 = D.P3(a, t, n, 3.0, z_, -0.8), D.P3(a, t, n, 39.0, z_, -0.8)
        bx(m, mf, min(p0[0], p1[0]) - 0.05, max(p0[0], p1[0]) + 0.05, min(p0[1], p1[1]), max(p0[1], p1[1]), z_, z_ + 0.1, STEEL, top=False)
    cap_arch(m, mw, 'd', d0 + 0.02, HM, 21.0, 21.0, 4.0, STONE, 10, 1, z0=21.0)
    # ---------------------------------------------------------------- hall roof (inside): vault strips between the 7 skylights, ribs, ties
    R_ = (21.0 ** 2 + 4.0 ** 2) / (2 * 4.0); zc = 21.0 + 4.0 - R_
    nseg = 8
    prof = [(-21.0 + 42.0 * i / nseg, zc + math.sqrt(R_ ** 2 - (-21.0 + 42.0 * i / nseg) ** 2)) for i in range(nseg + 1)]

    def vault(da, db, segs):
        for i in segs:
            (x0, h0), (x1, h1) = prof[i], prof[i + 1]
            q(m, mf, [(da, HM + x0, h0), (db, HM + x0, h0), (db, HM + x1, h1), (da, HM + x1, h1)], VAULT, None, (0, -(x0 + x1) / 2 / 21, -1))
    lanterns = [(x - 6.0, x + 6.0) for x in G.LANT_X]
    edges = [d0] + [v for ab in lanterns for v in ab] + [d1]
    for k in range(0, len(edges), 2):
        vault(edges[k], edges[k + 1], range(nseg))
    for (la, lb) in lanterns:
        vault(la, lb, (0, nseg - 1))
        xm = (la + lb) / 2; zb = 24.55
        for s, (xa, xb) in ((1, (la, xm - 1.6)), (-1, (lb, xm + 1.6))):   # sloped glass, seen from below
            q(m, mf, [(xa, HM - 15.75, zb), (xb, HM - 15.75, G.HALL_LANT), (xb, HM + 15.75, G.HALL_LANT), (xa, HM + 15.75, zb)], SKY, None, (0, 0, -1))
        q(m, mf, [(xm - 1.6, HM - 15.75, G.HALL_LANT), (xm + 1.6, HM - 15.75, G.HALL_LANT), (xm + 1.6, HM + 15.75, G.HALL_LANT), (xm - 1.6, HM + 15.75, G.HALL_LANT)], SKY, None, (0, 0, -1))
        for cc, sg in ((HM - 15.75, 1), (HM + 15.75, -1)):   # gable ends of the skylight
            tri(m, mf, [(la, cc, zb), (lb, cc, zb), (xm, cc, G.HALL_LANT)], hx("#e8e6df"), None, (0, sg, 0))
            for dd in (la, lb):
                pa = [(dd, cc, prof[1][1] if sg > 0 else prof[nseg - 1][1]), (dd, cc + sg * 0.01, zb)]
        for dd, sg in ((la, 1), (lb, -1)):   # curbs along the skylight sides
            for i in range(1, nseg - 1):
                (x0, h0), (x1, h1) = prof[i], prof[i + 1]
                q(m, mf, [(dd, HM + x0, h0), (dd, HM + x1, h1), (dd, HM + x1, zb), (dd, HM + x0, zb)], VAULT, None, (sg, 0, 0))
        # steel ribs
        for dd in (la, lb, xm):
            for i in range(nseg):
                (x0, h0), (x1, h1) = prof[i], prof[i + 1]
                if abs(dd - xm) < 0.1: continue
                q(m, mf, [(dd - 0.25, HM + x0, h0 - 0.02), (dd + 0.25, HM + x0, h0 - 0.02), (dd + 0.25, HM + x1, h1 - 0.02), (dd - 0.25, HM + x1, h1 - 0.02)], STEEL, None, (0, 0, -1))
    # tie rods and lamps
    for k, x in enumerate(G.LANT_X + [G.LANT_X[-1] + 18.2]):
        xx = x - 9.1
        if d0 < xx < d1:
            bx(m, mf, xx - 0.08, xx + 0.08, c0, c1, 17.6, 17.76, STEEL, top=False)
            for cc in (HM - 9, HM, HM + 9): P.lamp(m, ms, A, xx, cc, 17.3, 17.6)
    # ---------------------------------------------------------------- portal tunnel (c -67 .. -25, d 40.5 .. 55.5), barrel along c
    tw, tm = 7.5, 48.0
    # part 1: through the facade block (c -68 .. -45), semicircular arch of the portal (spring 9.5, crown 17)
    wall(m, mw, (40.5, -68.0), (40.5, -45.0), 0, 9.5, STONE, mod=(4, 4))
    wall(m, mw, (55.5, -45.0), (55.5, -68.0), 0, 9.5, STONE, mod=(4, 4))
    barrel(m, mf, 'c', -68.0, -45.0, tm, tw, 9.5, 7.5, hx('#6a4a3e'), n=10, outside=False)   # painted coffered ceiling (photos Interior #267 #270)
    # part 2: under the low wing (c -45 .. -25), flatter vault (spring 7, crown 10.4) with a transition wall at c=-45
    wall(m, mw, (40.5, -45.0), (40.5, c0), 0, 7.0, STONE, mod=(4, 4))
    wall(m, mw, (55.5, c0), (55.5, -45.0), 0, 7.0, STONE, mod=(4, 4))
    pr2 = barrel(m, mf, 'c', -45.0, c0, tm, tw, 7.0, 3.4, hx('#6a4a3e'), n=8, outside=False)
    a_, b_ = (40.5, -45.0), (55.5, -45.0); L_, t_, n_ = D.frame_of(a_, b_)
    hole = [(0.0, 0.0), (15.0, 0.0), (15.0, 7.0)] + [(7.5 + x, h) for x, h in reversed(pr2)][1:-1] + [(0.0, 7.0)]
    D.poly_wall(m, mw, Polygon(D.rect_pts(0, 0, 15.0, 17.5)).difference(Polygon(hole)), a_, t_, n_, 0.0, STONE, lambda u, z: (u / 4, z / 4))
    for cc in np.arange(-66.0, c0, 7.0):
        for dd in (40.5 + 0.2, 55.5 - 0.2):
            bx(m, mw, dd - 0.35, dd + 0.35, cc - 0.4, cc + 0.4, 0, 9.5 if cc < -45 else 7.0, STONE, top=False, mod=(2, 4))
        P.lamp(m, ms, A, tm, cc, 15.0 if cc < -45 else 9.9, 15.3 if cc < -45 else 10.3)
    wallc((40.5, -68.0), (40.5, c0), 0.9); wallc((55.5, -68.0), (55.5, c0), 0.9)
    # ---------------------------------------------------------------- Querhalle (inside): vault along c, ribs, east wall, end walls, open west side with columns
    qd0, qd1, qc0, qc1 = G.Q_D0, G.Q_D1, G.Q_C0, G.Q_C1; qm = (qd0 + qd1) / 2
    barrel(m, mf, 'c', qc0, qc1, qm, 12.5, G.Q_EAVE, G.Q_CROWN - G.Q_EAVE, hxw('#d8d8d4'), n=10, outside=False)
    for cc in np.arange(qc0 + 2, qc1, 3.5):   # ribs (steel arches, black lattice) and lamps
        RR = (12.5 ** 2 + (G.Q_CROWN - G.Q_EAVE) ** 2) / (2 * (G.Q_CROWN - G.Q_EAVE)); zcq = G.Q_CROWN - RR
        for i in range(10):
            x0, x1 = -12.5 + 25.0 * i / 10, -12.5 + 25.0 * (i + 1) / 10
            h0 = zcq + math.sqrt(RR ** 2 - x0 ** 2); h1 = zcq + math.sqrt(RR ** 2 - x1 ** 2)
            q(m, mf, [(qm + x0, cc - 0.18, h0 - 0.02), (qm + x0, cc + 0.18, h0 - 0.02), (qm + x1, cc + 0.18, h1 - 0.02), (qm + x1, cc - 0.18, h1 - 0.02)], hx('#6a3e32'), None, (0, 0, -1))
        if int((cc - qc0) / 3.5) % 2 == 0: P.lamp(m, ms, A, qm, cc, 16.0, 17.0)
    # Querhalle east wall (= hall west wall seen from the west), faces -d
    a, b = (qd1, qc1), (qd1, qc0)
    L, t, n = D.frame_of(a, b)
    holes = [D.arch_pts(qc1 - ch, 0, qc1 - cl, 4.5) for cl, ch in ((-23.5, -11.5), (-10.1, 1.9), (3.3, 15.3))]
    wall_with_holes(a, b, 0, G.Q_EAVE, holes, STONE, depth=1.0)
    # end walls
    for (aa, bb) in (((qd1, qc0), (qd0, qc0)), ((qd0, qc1), (qd1, qc1))):
        L, t, n = D.frame_of(aa, bb)
        poly_in(aa, bb, Polygon(D.rect_pts(0, 0, L, G.Q_EAVE)).difference(Polygon(D.arch_pts(5, 2.5, L - 5, 8.5))), STONE)
        pts = [D.P3(aa, t, n, u, z, -0.3) for u, z in D.arch_pts(5, 2.5, L - 5, 8.5)]
        for k in range(1, len(pts) - 1): D._oriented(m, mf, [pts[0], pts[k], pts[k + 1]], (n[0], n[1], 0), [(0, 0), (1, 0), (1, 1)], SKY)
        cap_arch(m, mw, 'c', (qc0 + 0.02) if aa[1] == qc0 else (qc1 - 0.02), qm, 12.5, G.Q_EAVE, G.Q_CROWN - G.Q_EAVE, STONE, 8, 1 if aa[1] == qc0 else -1, z0=G.Q_EAVE)
    # open west side: steel columns every 8.5 m + a deep beam
    for cc in np.arange(qc0 + 3, qc1, 8.5):
        column(m, mf, qd0 + 0.6, cc, 0.35, 0, 9.0, STEEL, 8)
    bx(m, mf, qd0 + 0.2, qd0 + 1.0, qc0, qc1, 9.0, 10.2, STEEL, top=True)
    # ---------------------------------------------------------------- props
    P.board_pair(m, ms, mf, A, -3.0, HM, 12.0, 6.4, 4.6, hang=17.0)
    P.board_pair(m, ms, mf, A, 90.0, HM, 12.0, 6.4, 4.6, hang=17.5)
    P.clock_pair(m, ms, mf, A, -33.0, HM, 6.8, 1.2, hang=14.5)
    P.angel(m, mf, 52.0, HM, 13.5)
    P.xmas_tree(m, mf, 104.0, HM + 0.0, 13.0, 3.4); wallc((102.5, HM), (105.5, HM), 3.0)
    for dd in (51.2, 52.8):
        bx(m, mf, dd - 0.03, dd + 0.03, HM - 0.03, HM + 0.03, 15.0, 24.6, hx("#303338"), top=False)
    ks = [(18.0, HM - 6.0, 4.2, 2.4, 3.0, 0), (30.0, HM + 15.75, 3.6, 2.2, 3.0, 1), (78.0, HM - 8.0, 4.4, 2.4, 3.0, 3), (96.0, HM + 15.75, 3.6, 2.2, 3.0, 4)]
    for (kd, kc, kw, kdp, kh, si) in ks:
        P.kiosk(m, ms, mf, A, kd, kc, kw, kdp, kh, si); wallc((kd - kw / 2, kc), (kd + kw / 2, kc), kdp)
    for i, sd in enumerate([58.0, 69.0, 80.0, 91.0, 102.0]):   # market huts: two rows with a free aisle in the middle
        for cc, sg in ((HM - 12.0, 0), (HM + 6.0, 1)):
            P.stall(m, ms, mf, A, sd, cc, 3.2, 2.2, 2.3, seed=i * 2 + sg); wallc((sd - 1.6, cc), (sd + 1.6, cc), 2.2)
    for bd in (8.0, 22.0, 36.0, 62.0, 74.0, 98.0):
        P.bench(m, mf, bd, HM + 2.5); P.bench(m, mf, bd, HM - 7.5)
    # stair wells to the Shopville (dark void, railings, hanging sign; visual, solid)
    for (sd, sc, sw, sl) in ((27.0, -16.0, 6.0, 3.2), (86.0, 8.0, 6.0, 3.2), (-35.0, -40.0, 4.0, 3.0), (-35.0, 28.0, 4.0, 3.0)):
        slab(m, mf, sd - sw / 2, sd + sw / 2, sc - sl / 2, sc + sl / 2, G.FLOOR + 0.02, hx("#08090a"))
        for k in range(6):   # visible steps going down into the dark
            zz = -0.0
        for (xa, ya, xb, yb) in ((sd - sw / 2, sc - sl / 2, sd + sw / 2, sc - sl / 2), (sd - sw / 2, sc + sl / 2, sd + sw / 2, sc + sl / 2), (sd - sw / 2, sc - sl / 2, sd - sw / 2, sc + sl / 2), (sd + sw / 2, sc - sl / 2, sd + sw / 2, sc + sl / 2)):
            bx(m, mf, min(xa, xb) - 0.04, max(xa, xb) + 0.04, min(ya, yb) - 0.04, max(ya, yb) + 0.04, 0, 1.0, hx("#9aa0a4"), top=True)
        wallc((sd - sw / 2, sc), (sd + sw / 2, sc), sl)
        R = A.rects["shopville"]
        zz = 9.5 if abs(sd) < 60 and sd > 0 else 7.0
        if sd > 0:
            for dd, sg in ((sd - 0.1, -1), (sd + 0.1, 1)):
                a_, b_ = (sc - 2.2, sc + 2.2) if sg > 0 else (sc + 2.2, sc - 2.2)
                m.quad(ms, [(dd, a_, zz), (dd, b_, zz), (dd, b_, zz + 1.0), (dd, a_, zz + 1.0)], uvr(R), W)
            bx(m, mf, sd - 0.03, sd + 0.03, sc - 0.03, sc + 0.03, zz + 1.0, 17.0, hx("#303338"), top=False)
    # signs to the platforms
    Rg = A.rects["gleise"]
    for dd, sg in ((-23.0, -1), (-23.0, 1)):
        a_, b_ = (HM - 2.2, HM + 2.2) if sg > 0 else (HM + 2.2, HM - 2.2)
        m.quad(ms, [(dd + 0.05 * sg, a_, 8.6), (dd + 0.05 * sg, b_, 8.6), (dd + 0.05 * sg, b_, 9.6), (dd + 0.05 * sg, a_, 9.6)], uvr(Rg), W)
    bx(m, mf, -23.03, -22.97, HM - 0.03, HM + 0.03, 9.6, 11.0, hx("#303338"), top=False)
    info(m, "hb_inner")
    return m


def colliders():
    """Wall rings in local metres: hall + Querhalle shells, thin walls with the openings left out."""
    rings = []
    d0, d1, c0, c1 = G.HALL_D0, G.HALL_D1, G.HALL_C0, G.HALL_C1
    segs = [  # (a, b) in the model frame; thickness 0.9
        ((d0, c0), (40.5, c0)), ((55.5, c0), (d1, c0)),                          # south wall, portal gap 40.5..55.5
        ((d0, c1), (d1, c1)),                                                    # north wall (shops, solid)
        ((d1, c0), (d1, -9.0)), ((d1, 3.0), (d1, c1)),                           # east end, exit gap c -9..3
        ((G.Q_D1, G.Q_C0), (G.Q_D1, c0 - 0.0)), ((G.Q_D1, c1), (G.Q_D1, G.Q_C1)),   # Querhalle east wall outside the hall mouth
        ((G.Q_D0, G.Q_C0), (G.Q_D1, G.Q_C0)), ((G.Q_D0, G.Q_C1), (G.Q_D1, G.Q_C1)),  # Querhalle end walls
        ((-8.0, -47.0), (-8.0, -67.0)), ((-8.0, -67.0), (6.0, -67.0)), ((6.0, -67.0), (6.0, -63.0)), ((6.0, -63.0), (36.0, -63.0)), ((36.0, -63.0), (36.0, -68.0)),
        ((36.0, -68.0), (40.5, -68.0)), ((55.5, -68.0), (60.0, -68.0)), ((60.0, -68.0), (60.0, -62.0)), ((60.0, -62.0), (90.0, -62.0)), ((90.0, -62.0), (90.0, -66.0)),
        ((90.0, -66.0), (105.0, -66.0)), ((105.0, -66.0), (105.0, -45.0)),                                   # facade polyline (swiss footprint), portal gap 40.5..55.5
        ((d0, c0), (d0, -47.0)), ((d0, -47.0), (G.S_D0, -47.0)),                   # Suedtrakt west annex (swiss footprint: west edge d=-20 for c -47..-25)
        ((G.S_D1, -45.0), (114.0, -45.0)), ((114.0, -45.0), (114.0, c0)), ((114.0, c0), (d1, c0)),   # low part east of the facade block
        ((G.N_D0, c1), (G.N_D0, G.N_C1)), ((G.N_D0, G.N_C1), (G.N_D1, G.N_C1)), ((G.N_D1, G.N_C1), (G.N_D1, c1)),   # Nordtrakt
        ((G.N_D1, c1), (d1, c1)),
    ]
    for a, b in segs + [(c[0], c[1]) for c in COLL]:
        pass
    allw = [(a, b, 0.9) for a, b in segs] + COLL
    for a, b, th in allw:
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 0.05: continue
        t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L); n = (-t[1], t[0]); h = th / 2
        pts = [(a[0] + n[0] * h, a[1] + n[1] * h), (b[0] + n[0] * h, b[1] + n[1] * h), (b[0] - n[0] * h, b[1] - n[1] * h), (a[0] - n[0] * h, a[1] - n[1] * h)]
        rings.append([[round(v, 2) for v in to_world(*p)] for p in pts])
    return rings


if __name__ == "__main__":
    m = build()
    H = json.load(open(ROOT / "research/hb/hide.json"))
    register(m, "hb_inner", "Zürich Hauptbahnhof + Innenraum", H["osm_points"]["haupt"], hide_ids=H["swiss"]["haupt"], walkable=True, colliders=colliders(), load_r=260)
