"""Zentralwaescherei (Kulturhaus, Neue Hard 12, Kreis 5). Former municipal central laundry: long hall with north-light sawtooth roofs (NE), taller office/plant
blocks (SW end 25 m + stair tower), pink poster/graffiti kiosk at the street corner with the white 'Zentral waescherei / BAR I KULTUR / CAFE | RESTAURANT' sign,
white tower with 'ZW' lettering and a yellow tank on top, rusty water tower in the yard. Footprints/heights from swissBUILDINGS3D, aerial (SWISSIMAGE) for the layout.
Photos: research/v3/zentralwaescherei.md (Commons 'Zentralwaescherei, Zuerich', Panoramax #108, Mapillary #78 #90 #79 #123 #132)"""
from k4w4_kit import *
from k45_volkshaus import plaster

MAIN, KIOSK, TOWER = "ID_6DCCD334", "ID_24EA961E", "ID_61417FF4"


def build():
    setup4()
    Pm = outline(bid(MAIN)["fp"], 0.5); c = Pm.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    rng = np.random.default_rng(41)
    m = Model4("zentralwaescherei")
    WALL = hexc("#cfcabd")
    mw = m.mat("wall", plaster(WALL, seed=21, stains=0.008), rough=0.95)
    ga = D.glass_atlas_g(frame="#2f3335", glass="#2e3b46", sky="#8aa0ae", cols=3, rows=2, seed=23, lit_p=0.4, cw=128, ch=96, bar=4,
                         curtain_cols=[(226, 222, 212), (190, 190, 190), (200, 170, 150)])
    mg = m.mat("glass", *ga, rough=0.3)
    mf = m.mat("flat", solid(W4))
    mgr = m.mat("graf", tex_graffiti(31), rough=0.9)
    mru = m.mat("rust", tex_rust(128, 5), rough=0.8)
    # sign / lettering sheet: [0..0.375] shop sign, [0.375..0.69] HC BR lettering, [0.69..1] ZW lettering
    S_W, S_H = 1024, 640
    sg = Image.new("RGB", (S_W, S_H), (239, 237, 230)); d = ImageDraw.Draw(sg)
    d.rectangle([0, 0, S_W, 150], fill=(239, 237, 230))
    f1, f2 = fnt("Barlow-Bold", 104), fnt("Barlow-Bold", 104); w1, w2 = d.textlength("Zentral", font=f1), d.textlength("wäscherei", font=f2); x0_ = (S_W - (w1 + w2 + 22)) / 2
    d.text((x0_, 80), "Zentral", font=f1, fill=(20, 20, 20), anchor="lm"); d.text((x0_ + w1 + 22, 80), "wäscherei", font=f2, fill=(20, 20, 20), anchor="lm")
    d.rectangle([0, 150, S_W, 240], fill=(120, 120, 118))
    d.text((60, 196), "BAR  |  KULTUR", font=fnt("BarlowCondensed-Bold", 60), fill=(245, 245, 240), anchor="lm"); d.text((S_W - 60, 196), "CAFE  |  RESTAURANT", font=fnt("BarlowCondensed-Bold", 60), fill=(245, 245, 240), anchor="rm")
    d.rectangle([0, 241, S_W, 400], fill=(244, 243, 238))
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4)): d.text((512 + dx, 320 + dy), "HC BR", font=fnt("PermanentMarker-Regular", 150), fill=(20, 40, 20), anchor="mm")
    d.text((512, 320), "HC BR", font=fnt("PermanentMarker-Regular", 150), fill=(150, 220, 60), anchor="mm")
    d.rectangle([0, 401, S_W, S_H], fill=(244, 243, 238))
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4)): d.text((512 + dx, 520 + dy), "ZW", font=fnt("PermanentMarker-Regular", 210), fill=(20, 20, 20), anchor="mm")
    d.text((512, 520), "ZW", font=fnt("PermanentMarker-Regular", 210), fill=(40, 120, 60), anchor="mm")
    msn = m.mat("sign", noisy(sg, 2, 4), rough=0.7)
    UV_SIGN = (0.0, 1 - 240 / S_H, 1.0, 1.0); UV_HC = (0.0, 1 - 400 / S_H, 1.0, 1 - 241 / S_H); UV_ZW = (0.0, 0.0, 1.0, 1 - 401 / S_H); UV_WHITE = (0.002, 0.985, 0.02, 0.995)

    # ---- main building: base block + stacked volumes + sawtooth hall ----
    Pl = orient(localize(Pm, ox, oy), 1.0)
    EZ = 9.3
    vols = [(z - oz, localize(g, ox, oy)) for z, g in volumes(MAIN) if z - oz > 10.5]
    LC = {}
    for z, g in vols: LC[round(z, 1)] = None
    cols = ["#cdc8ba", "#dcd8cc", "#c7c2b4", "#d9d5c8", "#b9b4a8", "#cdc8ba"]

    def hole_hall(u0, u1, f0, f1, fi, L):
        uc = (u0 + u1) / 2; w = min(2.3, u1 - u0 - 0.8); return D.rect_pts(uc - w / 2, f0 + 1.0, uc + w / 2, f0 + 3.0)

    def eg_hall(u0, u1, f0, f1, fi, L):
        uc = (u0 + u1) / 2; k = int(u0 // 3)
        if k % 5 == 2: w = min(3.0, u1 - u0 - 0.4); return D.rect_pts(uc - w / 2, f0, uc + w / 2, f0 + 3.4)   # roller-door size opening
        w = min(2.0, u1 - u0 - 0.9); return D.rect_pts(uc - w / 2, f0 + 1.2, uc + w / 2, f0 + 3.0)

    for a, b in edges_of(Pl, 0.3): m.wall(mw, a, b, -3.0, 0.0, (4, 4), (150, 146, 138, 255))
    facade(m, (mw, mg, mf), Pl, 0.0, EZ, None, fh=4.5, bayw=3.0, hole=hole_hall, depth=0.28, wall_col=W4, reveal_col=hexl("#6c6f70"), rng=rng, wmod=(4.0, 4.0),
           eg_h=4.8, eg_hole=eg_hall, base=0.0, cornice=(hexl("#a8a398"), 0.14, 0.45), wsill=0.07, deep_z=6.0)
    BANDS = bands(vols, EZ)
    print('bands', [(round(z0, 1), round(z1, 1), round(S.area)) for z0, z1, S, R in BANDS], 'oz', round(oz, 2))
    for z0, z1, S, R in BANDS:
        col = hexl(cols[min(len(cols) - 1, int(round(z1 / 4.5)) % len(cols))])
        for S1 in polys_of(S):
            if S1.area < 4: continue
            def hole(u0, u1, f0, f1, fi, L):
                uc = (u0 + u1) / 2; w = min(2.6, u1 - u0 - 0.5); return D.rect_pts(uc - w / 2, f0 + 0.95, uc + w / 2, f0 + 2.55)
            facade(m, (mw, mg, mf), S1, z0, z1, None, fh=max(3.2, (z1 - z0) / max(1, round((z1 - z0) / 3.6))), bayw=2.9, hole=hole, depth=0.2, wall_col=col, reveal_col=hexl("#d9d5ca"), rng=rng,
                   wmod=(4.0, 4.0), cornice=(hexl("#aaa59a"), 0.12, 0.35), wsill=0.05, deep_z=12.0)
        roofs(m, mf, R, z1 + 0.35, hexl("#8f8c85"))
        for p in polys_of(R):   # parapet ring
            for a, b in edges_of(p, 0.5): m.wall(mf, a, b, z1, z1 + 0.35, (4, 4), hexl("#bfbaae"))
    Rh = Pl.difference(unary_union([g for z, g in vols]).buffer(0.1)).buffer(-0.25)
    ns = sawtooth(m, mf, mg, mf, Rh, EZ, 2.4, 8.4, math.radians(55), hexl("#8d8a84"))
    print("sawtooth strips", ns)

    # ---- tower lettering + yellow tank on the SW block ----
    sw = [(z1, S) for z0, z1, S, R in BANDS if abs(z1 - (14.8 - oz)) < 0.7]
    sw2 = [(z, g) for z, g in vols if abs(z - (17.7 - oz)) < 0.6]
    if sw:
        zS, gS = sw[0]
        zTop = sw2[0][0] if sw2 else zS
        best = None
        for gp in polys_of(gS):
            for a, b in edges_of(orient(gp, 1.0), 6.0):
                L_, t_, n_ = D.frame_of(a, b); sc = n_[0] * -0.95 + n_[1] * -0.3
                if best is None or sc * L_ > best[0]: best = (sc * L_, a, b, L_, t_, n_)
        if best:
            _, a, b, L_, t_, n_ = best
            print('tower edge', [round(v,1) for v in a], [round(v,1) for v in b], 'n', [round(v,2) for v in n_], 'zS', round(zS,1))
            mid = ((a[0] + b[0]) / 2 + n_[0] * 0.08, (a[1] + b[1]) / 2 + n_[1] * 0.08)
            textquad(m, msn, (mid[0] + t_[0] * 3.2, mid[1] + t_[1] * 3.2, zS - 3.6), t_, 1, min(8.0, L_ - 6), 3.0, UV_HC)
            textquad(m, msn, (mid[0] - t_[0] * min(4.5, L_ / 2 - 3.5), mid[1] - t_[1] * min(4.5, L_ / 2 - 3.5), zS - 3.7), t_, 1, 4.2, 3.2, UV_ZW)
            cc = sw2[0][1].representative_point() if sw2 else gS.representative_point()
            m.cylinder(mf, cc.x - 2, cc.y, 1.35, zTop + 0.35, zTop + 4.2, n=14, col=(232, 190, 40, 255), cap=mf, capcol=(210, 170, 30, 255))

    # ---- kiosk with sign ----
    kb = bid(KIOSK); gk = ground(*kb["c"]) - oz
    Pk = orient(localize(outline(kb["fp"], 0.3), ox, oy), 1.0)
    HK = 3.4
    m.extrude(mw, mf, Pk, gk - 1.0, gk + HK, mod=(4, 4), col=(236, 168, 184, 255), rcol=hexl("#8b8884"))
    cells = [0, 1, 2, 3, 4, 5, 0, 2, 4, 6, 1, 3, 5, 12]
    ci = 0
    edge_info = []
    for a, b in edges_of(Pk, 1.2):
        L_, t_, n_ = D.frame_of(a, b)
        if L_ < 1.6: continue
        edge_info.append((a, b, L_, t_, n_))
        nseg = max(1, int(round(L_ / 3.2)))
        for i in range(nseg):
            f0, f1 = i / nseg, (i + 1) / nseg
            k = cells[ci % len(cells)]; ci += 1
            u0, v0, u1, v1 = gcell(k)
            p0 = (a[0] + (b[0] - a[0]) * f0 + n_[0] * 0.05, a[1] + (b[1] - a[1]) * f0 + n_[1] * 0.05); p1 = (a[0] + (b[0] - a[0]) * f1 + n_[0] * 0.05, a[1] + (b[1] - a[1]) * f1 + n_[1] * 0.05)
            m.quad(mgr, [(p0[0], p0[1], gk), (p1[0], p1[1], gk), (p1[0], p1[1], gk + HK), (p0[0], p0[1], gk + HK)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], n=(n_[0], n_[1], 0))
    # sign on the roof, facing the street (south-west-ish): pick the edge with normal closest to (-0.2,-1)
    if edge_info:
        a, b, L_, t_, n_ = max(edge_info, key=lambda e: (e[4][0] * -0.2 + e[4][1] * -1.0) * min(e[2], 8))
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2); sw_ = min(7.4, L_ - 0.4); sh_ = sw_ * 240 / 1024 * 1.0
        zb = gk + HK + 0.35
        cx_, cy_ = mid[0] + n_[0] * 0.2, mid[1] + n_[1] * 0.2
        m.box(mf, cx_ - n_[0] * 0.15, cy_ - n_[1] * 0.15, sw_, 0.55, zb, zb + sh_ + 0.1, rot=math.atan2(t_[1], t_[0]), col=(236, 234, 228, 255))
        textquad(m, msn, (cx_ + n_[0] * 0.17, cy_ + n_[1] * 0.17, zb + 0.05), t_, 1, sw_ - 0.15, sh_, UV_SIGN)
        bt = (-t_[0], -t_[1])
        textquad(m, msn, (cx_ - n_[0] * 0.5, cy_ - n_[1] * 0.5, zb + 0.05), bt, 1, sw_ - 0.15, sh_, UV_WHITE)
        # pergola + plants on the kiosk roof
        for i in range(5):
            px_, py_ = mid[0] - n_[0] * 1.8 + t_[0] * (-3 + i * 1.5), mid[1] - n_[1] * 1.8 + t_[1] * (-3 + i * 1.5)
            m.box(mf, px_, py_, 0.14, 0.14, gk + HK, gk + HK + 2.5, col=(120, 86, 58, 255))
        for i in range(10):
            px_, py_ = mid[0] - n_[0] * (0.8 + 1.4 * rng.random()) + t_[0] * (-3.4 + i * 0.75), mid[1] - n_[1] * (0.8 + 1.4 * rng.random()) + t_[1] * (-3.4 + i * 0.75)
            s_ = 0.5 + 0.7 * rng.random(); m.box(mf, px_, py_, s_, s_, gk + HK, gk + HK + 0.5 + 1.2 * rng.random(), col=(70 + int(rng.integers(0, 40)), 120 + int(rng.integers(0, 40)), 62, 255))
    # graffiti wall continuing along the kiosk's long edge on both sides
    if edge_info:
        a, b, L_, t_, n_ = max(edge_info, key=lambda e: e[2])
        for sgn, ext in ((1, 13.0), (-1, 9.0)):
            end = b if sgn > 0 else a
            st = (end[0] + t_[0] * sgn * 0.0, end[1] + t_[1] * sgn * 0.0)
            e2 = (st[0] + t_[0] * sgn * ext, st[1] + t_[1] * sgn * ext)
            gz = gk
            seg = max(1, int(round(ext / 3.5)))
            for i in range(seg):
                f0, f1 = i / seg, (i + 1) / seg
                q0 = (st[0] + (e2[0] - st[0]) * f0, st[1] + (e2[1] - st[1]) * f0); q1 = (st[0] + (e2[0] - st[0]) * f1, st[1] + (e2[1] - st[1]) * f1)
                k = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15][(i * 3 + (0 if sgn > 0 else 5)) % 10]; u0, v0, u1, v1 = gcell(k)
                if sgn > 0: pa, pb = q0, q1
                else: pa, pb = q1, q0
                nn = (n_[0], n_[1])
                m.quad(mgr, [(pa[0] + nn[0] * 0.2, pa[1] + nn[1] * 0.2, gz), (pb[0] + nn[0] * 0.2, pb[1] + nn[1] * 0.2, gz), (pb[0] + nn[0] * 0.2, pb[1] + nn[1] * 0.2, gz + 2.5), (pa[0] + nn[0] * 0.2, pa[1] + nn[1] * 0.2, gz + 2.5)],
                       [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], n=(nn[0], nn[1], 0))
            # wall body (thin box) behind the quads
            m.box(mw, (st[0] + e2[0]) / 2, (st[1] + e2[1]) / 2, ext, 0.3, gz - 0.5, gz + 2.5, rot=math.atan2(t_[1], t_[0]), col=(190, 188, 182, 255), mr=mf, rcol=(150, 148, 142, 255))

    # ---- water tower in the yard ----
    wb = bid(TOWER); wc = wb["c"]; gz = ground(*wc) - oz
    water_tower(m, mru, mf, wc[0] - ox, wc[1] - oy, gz, col=(255, 255, 255, 255))

    sinfo(m, "zentralwaescherei")
    finish(m, "zentralwaescherei", "Zentralwaescherei (Kulturhaus Neue Hard)", ox, oy, oz, hide_pts([MAIN, KIOSK, TOWER]))


if __name__ == "__main__":
    build()
