"""Zuerich HB v3 underground (hb3_under.glb): Shopville gang + connector, stairs from the Querhalle and the Bahnhofplatz, Bahnhof Museumstrasse (Gleise 41-44)
and Bahnhof Loewenstrasse (Gleise 31-34) with platforms, tracks and ceilings. Walkable via hb3_decks.json (sub-surface decks, see bridges.ts // hb3).
Materials: hb3_pit (drawn first), hb3_lit (night glow), hb3_mask (stencil only: cuts the terrain over the two open stair wells). Neutral shopfronts, no logos/SBB clock."""
import sys
from hb_kit import *
import hb3_spec as S
common.OVR = ROOT / "pipeline" / "overrides" / "landmarks_hb3.json"   # own override file (merge.py globs landmarks_*.json)

P_, LIT, MASK = None, None, None
CONC, CONC_D, FLOOR_G, PLAT, TILE_W = hx("#b4b6b4"), hx("#7c7f80"), hx("#3e3f43"), hx("#d2d0c8"), hx("#c9c6bd")
DARK = hx("#4c4f53")
BALL, RAIL, YEL = hx("#3a3835"), hx("#7a7c80"), hx("#d8b830")
SHOPCOL = [hx(h) for h in ("#b4503c", "#3c6e9c", "#4a8a5c", "#c8a040", "#7c5aa0", "#c46a8c", "#4c9aa8", "#8a8a8a")]
CELLS = ["", "SHOPVILLE", "GLEISE 31-34", "GLEISE 41-44", "BAHNHOFPLATZ", "QUERHALLE", "LÖWENSTRASSE", "MUSEUMSTRASSE", "AUSGANG", "ZU DEN GLEISEN"]


def atlas():
    img = Image.new("RGBA", (512, 256), (255, 255, 255, 255)); em = Image.new("RGBA", (512, 256), (0, 0, 0, 255))
    d, de = ImageDraw.Draw(img), ImageDraw.Draw(em)
    d.rectangle([0, 0, 127, 63], fill=(255, 255, 255, 255)); de.rectangle([0, 0, 127, 63], fill=(255, 255, 255, 255))
    for i, t in enumerate(CELLS):
        if not t: continue
        x, y = (i % 4) * 128, (i // 4) * 64
        sign_text(t, "#ffffff", "#2a5a8c", glow=(255, 255, 255, 255), size=17 if len(t) > 11 else 22, frame="#ffffff")(d, de, x, y, 128, 64)
    return img, em


def cell_uv(name):
    i = CELLS.index(name); x, y = (i % 4) * 128, (i // 4) * 64
    return (x / 512, y / 256, (x + 128) / 512, (y + 64) / 256)


def wall2(*a, **k):
    wall(*a, double=True, **k)   # corridor/tunnel walls are seen from inside only; double-sided avoids winding mistakes


def sgn(name, a, b, z0, z1):
    """Sign quad from (d,c) a to b (facing right of a->b), on the lit material."""
    r = cell_uv(name); m_.quad(LIT, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], [(r[0], r[3]), (r[2], r[3]), (r[2], r[1]), (r[0], r[1])], W)


PU = [(0.02, 0.02), (0.1, 0.02), (0.1, 0.2), (0.02, 0.2)]   # plain white atlas cell


def panel(d0, d1, c0, c1, z):
    """Ceiling light panel (lit material, facing down)."""
    q(m_, LIT, [(d0, c0, z), (d1, c0, z), (d1, c1, z), (d0, c1, z)], hx("#fff6d8"), PU, (0, 0, -1))


def pl(col):    # plain white atlas cell -> vertex colour only
    return col


def box(d0, d1, c0, c1, z0, z1, col, top=True, mat=None, sides=(1, 1, 1, 1)):
    bx(m_, mat or P_, d0, d1, c0, c1, z0, z1, col, top=top, sides=sides)


def stair_pt(s, t):
    r = S.run(s); return (s[1][0] + s[2][0] * r * t, s[1][1] + s[2][1] * r * t, s[3] - (s[3] - s[4]) * t)


def lat(s):
    return (-s[2][1], s[2][0])   # unit lateral (d,c)


def stair(s):
    name, top, dr, zt, zb, w = s
    n = int(round((zt - zb) / 0.17)); L = lat(s); h = w / 2
    pt = lambda t, k: (top[0] + dr[0] * S.run(s) * t + L[0] * k, top[1] + dr[1] * S.run(s) * t + L[1] * k)
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n; z = zt - (zt - zb) * t1; zu = zt - (zt - zb) * t0
        a0, a1, b0, b1 = pt(t0, -h), pt(t1, -h), pt(t0, h), pt(t1, h)
        q(m_, P_, [(a1[0], a1[1], z), (b1[0], b1[1], z), (b0[0], b0[1], z), (a0[0], a0[1], z)], CONC, None, (0, 0, 1))                       # tread (z of this step)
        q(m_, P_, [(a0[0], a0[1], z), (b0[0], b0[1], z), (b0[0], b0[1], zu), (a0[0], a0[1], zu)], CONC_D, None, (-dr[0], -dr[1], 0))   # riser faces up the stair
    # side walls: top = min(surface + 3 m soffit, parapet 1 m) ; soffit slab follows the stair where it is below ground
    for k, sg in ((-h, 1), (h, -1)):
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n; a, b = pt(t0, k), pt(t1, k)
            za, zb_ = zt - (zt - zb) * t0, zt - (zt - zb) * t1
            ta, tb = min(za + 3.0, 1.0), min(zb_ + 3.0, 1.0)
            q(m_, P_, [(a[0], a[1], za), (b[0], b[1], zb_), (b[0], b[1], tb), (a[0], a[1], ta)], CONC, None, (-sg * L[0], -sg * L[1], 0))
    t_open = (zt - S.OPEN_Z) / (zt - zb)
    if t_open < 1.0:
        a, b = t_open, 1.0
        for sd in (-h, h):
            pass
        pa0, pa1, pb0, pb1 = pt(a, -h), pt(b, -h), pt(a, h), pt(b, h)
        za, zb_ = zt - (zt - zb) * a + 3.0, zt - (zt - zb) * b + 3.0
        q(m_, P_, [(pa0[0], pa0[1], za), (pa1[0], pa1[1], zb_), (pb1[0], pb1[1], zb_), (pb0[0], pb0[1], za)], CONC_D, None, (0, 0, -1))


def lights(d0, d1, c, z, step=9.0, w=1.2):
    d = d0 + step / 2
    while d < d1:
        panel(d - w, d + w, c - 0.25, c + 0.25, z - 0.03); d += step


def shops(side_c, d0, d1, z, inward, gaps, rng, depth=1.0):
    """Neutral shopfronts along a wall at c=side_c; inward = +1/-1 (direction into the gang)."""
    d = d0
    while d < d1 - 3:
        w = float(rng.choice([4.0, 5.0, 6.0, 7.0])); e = min(d + w, d1)
        if any(d < g1 and e > g0 for g0, g1 in gaps): d = e; continue
        col = SHOPCOL[int(rng.integers(len(SHOPCOL)))]
        c1 = side_c + inward * depth
        box(d + 0.3, e - 0.3, min(side_c, c1), max(side_c, c1), z, z + 0.9, CONC_D, top=True)                               # plinth
        box(d + 0.3, e - 0.3, min(side_c, c1 - inward * 0.2), max(side_c, c1 - inward * 0.2), z + 2.55, z + 3.15, col, top=False)   # fascia (no lettering: neutral)
        a, b = (d + 0.3, c1 - inward * 0.0), (e - 0.3, c1)      # window strip, lit
        zz0, zz1 = z + 0.9, z + 2.55
        if inward > 0: m_.quad(LIT, [(a[0], a[1], zz0), (b[0], b[1], zz0), (b[0], b[1], zz1), (a[0], a[1], zz1)], PU, hx("#e9e2c8"))
        else: m_.quad(LIT, [(b[0], b[1], zz0), (a[0], a[1], zz0), (a[0], a[1], zz1), (b[0], b[1], zz1)], PU, hx("#e9e2c8"))
        d = e


def tube(d0, d1, c0, c1, zf, h, gapsN=(), gapsS=(), floor=True, ceil_gaps=()):
    """Corridor shell: floor, ceiling (with gaps in d), walls with gaps."""
    if floor: slab(m_, P_, d0, d1, c0, c1, zf, FLOOR_G, True)
    ds = [d0] + sorted(v for g in ceil_gaps for v in g) + [d1]
    for k in range(0, len(ds), 2):
        if ds[k + 1] > ds[k]: slab(m_, P_, ds[k], ds[k + 1], c0, c1, zf + h, CONC, False)
    for cw, gaps, sg in ((c1, gapsN, -1), (c0, gapsS, 1)):
        pts = [d0] + sorted(v for g in gaps for v in g) + [d1]
        for k in range(0, len(pts), 2):
            if pts[k + 1] > pts[k]: wall2(m_, P_, (pts[k], cw), (pts[k + 1], cw), zf, zf + h, CONC) if sg > 0 else wall2(m_, P_, (pts[k + 1], cw), (pts[k], cw), zf, zf + h, CONC)


def station(kind):
    """Platform halls: 'L' along d (Loewenstrasse), 'M' along c (Museumstrasse). tracks + platforms + walls + ceiling."""
    rng = np.random.default_rng(4)
    if kind == "L":
        zp, a0, a1 = S.ZL, S.L_D0, S.L_D1; pcs, trs = S.L_P, S.L_TRACKS; lo, hi = -90.0, -60.8
        F = lambda x0, x1, y0, y1, z0, z1, col, **k: box(x0, x1, y0, y1, z0, z1, col, **k)
        cc = lambda a, b: (a, b)
    else:
        zp, a0, a1 = S.ZM, S.M_C0, S.M_C1; pcs, trs = S.M_P, S.M_TRACKS; lo, hi = 107.5, 136.7
        F = lambda x0, x1, y0, y1, z0, z1, col, **k: box(y0, y1, x0, x1, z0, z1, col, **k)   # swap (along, across) -> (d, c)
        cc = lambda a, b: (a, b)
    # F(along0, along1, across0, across1, ...)
    F(a0, a1, lo, hi, zp - 1.4, zp - 1.1, BALL, top=True)                       # ballast bed
    for c, w in pcs:
        F(a0, a1, c - w / 2, c + w / 2, zp - 1.1, zp, PLAT, top=True)
        F(a0, a1, c - w / 2, c - w / 2 + 0.4, zp, zp + 0.012, YEL, top=True, sides=(0, 0, 0, 0)); F(a0, a1, c + w / 2 - 0.4, c + w / 2, zp, zp + 0.012, YEL, top=True, sides=(0, 0, 0, 0))
    for t in trs:
        for dd in (-0.72, 0.72): F(a0, a1, t + dd - 0.04, t + dd + 0.04, zp - 1.1, zp - 0.95, RAIL, top=True, sides=(0, 0, 0, 0))
    # columns + lights along the platforms
    k = a0 + 6
    while k < a1 - 3:
        for c, w in pcs:
            F(k - 0.35, k + 0.35, c - 0.35, c + 0.35, zp, zp + 5.0, CONC_D, top=False)
        k += 12.0
    # walls + ceiling with gaps for the stairs
    gaps = [(66.0, 74.0)] if kind == "L" else []
    zc = zp + 5.0
    if kind == "L":
        ds = [a0] + [v for g in gaps for v in g] + [a1]
        for i in range(0, len(ds), 2): slab(m_, P_, ds[i], ds[i + 1], lo, hi, zc, CONC, False)
        for cw, sg in ((lo, 1), (hi, -1)):
            wall2(m_, P_, (a0, cw), (a1, cw), zp - 1.4, zc, DARK) if sg > 0 else wall2(m_, P_, (a1, cw), (a0, cw), zp - 1.4, zc, DARK)
        wall2(m_, P_, (a1, hi), (a1, lo), zp - 1.4, zc, DARK); wall2(m_, P_, (a0, lo), (a0, hi), zp - 1.4, zc, DARK)
        for c, w in pcs:
            lights(a0 + 4, a1 - 4, c, zc - 0.05, 6.0, 1.0)
        # column signs (square columns carry the platform label)
        k = a0 + 6
        while k < a1 - 3:
            for c, w in pcs:
                m_.quad(LIT, [(k + 0.35, c - 0.35, zp + 2.4), (k + 0.35, c + 0.35, zp + 2.4), (k + 0.35, c + 0.35, zp + 3.1), (k + 0.35, c - 0.35, zp + 3.1)], [(cell_uv("GLEISE 31-34")[0], cell_uv("GLEISE 31-34")[3]), (cell_uv("GLEISE 31-34")[2], cell_uv("GLEISE 31-34")[3]), (cell_uv("GLEISE 31-34")[2], cell_uv("GLEISE 31-34")[1]), (cell_uv("GLEISE 31-34")[0], cell_uv("GLEISE 31-34")[1])], W)
            k += 12.0
        # crossover over the tracks (Unterführung) at d=8
        slab(m_, P_, 7.0, 9.0, pcs[0][0], pcs[1][0], zp, PLAT, True)
    else:
        slab(m_, P_, lo, hi, -76.0, a1, zc, CONC, False)    # ceiling only north of the stair hole (c > -76); south: Shopville gang floor above
        slab(m_, P_, lo, hi, a0, -87.0, zc, CONC, False)
        slab(m_, P_, lo, 111.0, -87.0, -76.0, zc, CONC, False); slab(m_, P_, 119.0, hi, -87.0, -76.0, zc, CONC, False)
        for dw, sg in ((lo, 1), (hi, -1)):
            wall2(m_, P_, (dw, a1), (dw, a0), zp - 1.4, zc, DARK) if dw == lo else wall2(m_, P_, (dw, a0), (dw, a1), zp - 1.4, zc, DARK)
        wall2(m_, P_, (lo, a1), (hi, a1), zp - 1.4, zc, DARK)
        for c, w in pcs:
            for cc_ in np.arange(a0 + 4, a1 - 4, 6.0): panel(c - 0.25, c + 0.25, cc_ - 1.0, cc_ + 1.0, zc - 0.03)
        k = a0 + 6
        while k < a1 - 3:
            for c, w in pcs:
                r = cell_uv("GLEISE 41-44")
                m_.quad(LIT, [(c - 0.35, k + 0.35, zp + 2.4), (c + 0.35, k + 0.35, zp + 2.4), (c + 0.35, k + 0.35, zp + 3.1), (c - 0.35, k + 0.35, zp + 3.1)], [(r[0], r[3]), (r[2], r[3]), (r[2], r[1]), (r[0], r[1])], W)
            k += 12.0


def build():
    global m_, P_, LIT, MASK
    rng = np.random.default_rng(7)
    m_ = Model("hb3_under")
    img, em = atlas()
    P_ = m_.mat("hb3_pit", Image.new("RGBA", (4, 4), (255, 255, 255, 255)), None, 0.9); LIT = m_.mat("hb3_lit", img, em, 0.8); MASK = m_.mat("hb3_mask", Image.new("RGBA", (4, 4), (255, 255, 255, 255)))
    ZS, h = S.ZS, 3.8
    # --- Shopville gang (E-W under the Bahnhofplatz), openings for the connector, S2 landing and the two stairs on the north edge
    gN = [(S.CONN_D - 4.5, S.CONN_D + 4.5), (57.0, 63.0), (67.5, 72.5), (112.0, 117.6)]
    tube(S.GANG_D0, S.GANG_D1, S.GANG_C0, S.GANG_C1, ZS, h, gapsN=gN)
    wall2(m_, P_, (S.GANG_D1, S.GANG_C1), (S.GANG_D1, S.GANG_C0), ZS, ZS + h, CONC_D); wall2(m_, P_, (S.GANG_D0, S.GANG_C0), (S.GANG_D0, S.GANG_C1), ZS, ZS + h, CONC_D)
    shops(S.GANG_C0, S.GANG_D0 + 4, S.GANG_D1 - 2, ZS, 1, [], rng)
    shops(S.GANG_C1, S.GANG_D0 + 10, S.GANG_D1 - 2, ZS, -1, [(a - 0.5, b + 0.5) for a, b in gN], rng)
    lights(S.GANG_D0, S.GANG_D1, -92.0, ZS + h, 7.0)
    for i, d_ in enumerate(np.arange(S.GANG_D0 + 6, S.GANG_D1 - 4, 9.0)):   # coloured light columns (Shopville look, see research/hb/v3.md)
        if any(a - 1 < d_ < b + 1 for a, b in gN): continue
        column(m_, P_, d_, -92.0, 0.42, ZS, ZS + h, [hx("#3fa85a"), hx("#e8b030"), hx("#3c6cc8"), hx("#b0b4b8")][i % 4], 10)
    # signs on the south wall
    for d_ in (-10.0, 30.0, 85.0): sgn("SHOPVILLE", (d_ - 2.2, S.GANG_C0 + 0.02), (d_ + 2.2, S.GANG_C0 + 0.02), ZS + 3.0, ZS + 3.55)
    sgn("BAHNHOFPLATZ", (63.0, S.GANG_C1 - 0.03), (57.0, S.GANG_C1 - 0.03), ZS + 3.0, ZS + 3.6)
    # --- connector N-S under the Querhalle
    d0, d1 = S.CONN_D - S.CONN_W / 2, S.CONN_D + S.CONN_W / 2; c1 = -S.run(S.STAIRS[0]) - 4.0
    c0 = S.GANG_C1
    tube(d0, d1, c0, c1, ZS, h, floor=True)
    for dd, sg in ((d0, 1), (d1, -1)):
        pass
    # --- stairs
    for s in S.STAIRS: stair(s)
    # landing floor of the stairs S1 / SC / SL (stair foot meets the floor)
    # --- stations
    station("L"); station("M")
    # --- stencil masks over the two open wells
    for (a, b, c, d) in S.WELLS:
        m_.quad(MASK, [(a, c, 0.05), (b, c, 0.05), (b, d, 0.05), (a, d, 0.05)], None, W)
    # parapets are the stair side walls (top 1 m above the plateau); handrails are left out (budget)
    return m_


def decks():
    rows = []
    wp = lambda d, c, z: [*[round(v, 2) for v in to_world(d, c)], round(GZ + z, 2)]
    def row(name, pts, w):
        rows.append({"p": [wp(*p) for p in pts], "g": [round(GZ, 2)] * len(pts), "b": [round(GZ + p[2] - 0.4, 2) for p in pts], "w": w, "kind": "foot", "name": name, "sub": True})
    ZS = S.ZS
    row("HB Shopville", [(S.GANG_D0, -92.0, ZS), (S.GANG_D1, -92.0, ZS)], 9.8)
    cs = S.STAIRS[0]; cb = S.end(cs)[1]
    row("HB Shopville Zugang", [(S.CONN_D, cb, ZS), (S.CONN_D, -92.0, ZS)], S.CONN_W - 0.4)
    for s in S.STAIRS:
        (d, c), (e_d, e_c) = s[1], S.end(s)
        pts = [(d, c, s[3]), (e_d, e_c, s[4])]
        if s[0] in ("SC", "SL"): pts[0] = (d, c - 0.6, s[3])   # slope starts 0.6 m inside the gang so the gang parapet does not block the stair mouth
        row("HB Treppe " + s[0], pts, s[5] + 0.4)
    for c, w in S.L_P: row("HB Perron Loewenstrasse", [(S.L_D0, c, S.ZL), (S.L_D1, c, S.ZL)], w - 0.2)
    row("HB Perron Loewenstrasse Quergang", [(8.0, S.L_P[0][0], S.ZL), (8.0, S.L_P[1][0], S.ZL)], 2.0)
    for c, w in S.M_P: row("HB Perron Museumstrasse", [(c, S.M_C0, S.ZM), (c, S.M_C1, S.ZM)], w - 0.2)
    return {"decks": rows, "piers": []}


if __name__ == "__main__":
    m = build()
    register(m, "hb3_under", "Zürich Hauptbahnhof + Untergeschosse", [], hide_ids=(), walkable=True, colliders=None, load_r=250)
    json.dump(decks(), open(ROOT / "web/public/data/hb3_decks.json", "w"), separators=(",", ":"))
    print("hb3_decks.json:", len(decks()["decks"]), "decks")
