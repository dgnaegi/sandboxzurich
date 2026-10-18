"""v2: shop signs (Coop, Apotheke, Café, Blumen) at OSM positions, green-roof discs + skylights, cream end walls. Writes the same GLB as k45_lochergut.
Lochergut (1966, Hans Hofmann / Hans Fischli): staggered slabs with ribbon floors, light concrete slab edges + brown/tan parapet panels,
end walls with punched windows, glazed 2-storey podium with ribbed grey fascia. Photos: research/v3/lochergut.md."""
import math
from PIL import Image, ImageDraw
from common import *
from lm import *
import detail as D
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

SIGNS = [(0, 448, "ZENTRUM LOCHERGUT", "#52565a", "#d4d6d3", (255, 190, 235)), (448, 704, "coop", "#e4571e", "#f4f3ef", (255, 170, 110)),
         (704, 832, "GRAND CAFE", "#f3e6c8", "#3a2a22", (255, 220, 150)), (832, 960, "BLUMEN", "#fbf3f0", "#8a3d54", (255, 210, 230))]
SIGN_V = (0.0, 0.25)
# shop signs on the south front (OSM shop positions, local m): (strip x0, strip x1, x, y, sign width m)
SHOPS = [(448, 704, 58.0, -927.0, 8.4), (704, 832, 36.0, -925.0, 4.6), (832, 960, 49.0, -921.0, 4.6)]
IDS = ["ID_1EB1BB89", "ID_6E312FD7", "ID_C1E18200", "ID_F93C1762", "ID_1D02EC7C"]


def panels(color, joint=0.88, seed=4, size=128):
    rng = np.random.default_rng(seed)
    a = np.full((size, size, 4), 255, np.uint8); a[..., :3] = color[:3]
    n = rng.normal(0, 4, (size, size, 1)); a[..., :3] = np.clip(a[..., :3] + n, 0, 255).astype(np.uint8)
    for i in range(0, size, size // 4):   # panel joints 4x4 per texture tile
        a[i, :, :3] = (a[i, :, :3] * joint).astype(np.uint8); a[:, i, :3] = (a[:, i, :3] * joint).astype(np.uint8)
    for _ in range(18):    # individual panel tone variation
        x, y = rng.integers(0, 4) * (size // 4), rng.integers(0, 4) * (size // 4); f = 1 + rng.normal(0, 0.05)
        a[y:y + size // 4, x:x + size // 4, :3] = np.clip(a[y:y + size // 4, x:x + size // 4, :3] * f, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def ribbed(color, size=64):
    a = np.full((size, size, 4), 255, np.uint8); a[..., :3] = color[:3]
    for y in range(0, size, 4): a[y, :, :3] = (a[y, :, :3] * 0.8).astype(np.uint8); a[y + 1, :, :3] = (a[y + 1, :, :3] * 1.06).clip(0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def neon_tex():
    """Light-box face 512x64: dark panel, big white blocky «LOCHERGUT» letters. Emissive = letters only (tinted at runtime), so the letters glow on an unlit box."""
    from PIL import ImageFont
    im = Image.new("RGBA", (512, 64), (52, 54, 58, 255)); em = Image.new("RGB", (512, 64), (0, 0, 0)); d = ImageDraw.Draw(im); de = ImageDraw.Draw(em)
    f = None
    for p in ("/System/Library/Fonts/Supplemental/Arial Black.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        try: f = ImageFont.truetype(p, 60); break
        except Exception: pass
    txt = "LOCHERGUT"; ws = [d.textlength(c, font=f) for c in txt]; gap = (496 - sum(ws)) / (len(txt) - 1); x = 8
    for c, w in zip(txt, ws):
        d.text((x, 33), c, font=f, fill=(70, 70, 74, 255), anchor="lm"); de.text((x, 33), c, font=f, fill=(255, 255, 255), anchor="lm"); x += w + gap
    return im, em


def build():
    bs = [bid(i) for i in IDS]; fps = [outline(b["fp"], 0.5) for b in bs]
    ox = round(float(np.mean([f.centroid.x for f in fps[1:]])), 1); oy = round(float(np.mean([f.centroid.y for f in fps[1:]])), 1); oz = ground(ox, oy)
    rng = np.random.default_rng(7)
    m = Model("lochergut"); m.max_mats = 4
    mw = m.mat("wall", panels(hexc("#e9e4d4"), joint=0.9))
    ga = D.glass_atlas_g(frame="#d9d4c6", glass="#2c353b", sky="#8aa0b0", cols=2, rows=1, seed=8, bar=2, lit_p=0.3, sign=D.letters_strip(SIGNS, size=26), curtain_cols=[(236, 228, 210), (214, 205, 185), (225, 225, 228), (190, 180, 160)])
    _d, _de = ImageDraw.Draw(ga[0]), ImageDraw.Draw(ga[1]); _d.rectangle([970, 100, 1020, 124], fill=(250, 232, 190, 255)); _de.rectangle([970, 100, 1020, 124], fill=(255, 225, 160))   # warm shop-light cell
    mg = m.mat("glass", *ga, rough=0.3)
    mn = m.mat("lochergut_neon", *neon_tex()); mf = m.mat("flat", solid((255, 255, 255, 255)))
    BR, SLAB, CONC, GREY = D.hexl("#c2b8a2"), D.hexl("#d3cdbd"), D.hexl("#a9a79f"), D.hexl("#c9cac7")
    W = (255, 255, 255, 255)
    lin = lambda v: (v / 255) ** 2.2
    def mul(target, base="#e9e4d4"):
        T, B_ = hexc(target), hexc(base); return tuple(int(min(255, 255 * lin(T[i]) / lin(B_[i]))) for i in range(3)) + (255,)
    TAN = mul("#cdbb8c")
    sign = D.letters_strip([(0, 1024, "ZENTRUM LOCHERGUT", "#52565a", "#d4d6d3", None)], size=26)
    for k, (b, fp) in enumerate(zip(bs, fps)):
        P = orient(localize(fp, ox, oy), 1.0); c = fp.centroid; g0 = ground(c.x, c.y); gz = g0 - oz
        H = b["zmax"] - g0; ring = list(P.exterior.coords)[:-1]; ne = len(ring)
        if k == 0:      # podium: 2 storeys, glazed ground floor + ribbed fascia
            h = H - 0.6
            m.extrude(mf, mf, P, gz - 3, gz, col=CONC, roof=False)
            for i in range(ne):
                a, b_ = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b_)
                if L < 2.5: m.wall(mf, a, b_, gz, gz + h, (3, 3), CONC); continue
                a = (a[0], a[1]); 
                D.ribbon_floors(m, mw, mg, mf, a, b_, gz, 1, 4.3, 0.5, 3.2, 0.25, (255, 255, 255, 255), CONC, rng, wmod=(5, 4), seg=2.6, slab_out=0.0, pier=0.07, lite=True)
                # ribbed fascia (storey 2), canopy lip
                m.wall(mf, a, b_, gz + 4.3, gz + h, (3, 3), GREY)
                for zz_ in np.arange(gz + 4.95, gz + h - 0.9, 0.8): D._oriented(m, mf, [D.P3(a, t, n, 0, zz_, 0.05), D.P3(a, t, n, L, zz_, 0.05), D.P3(a, t, n, L, zz_ + 0.1, 0.05), D.P3(a, t, n, 0, zz_ + 0.1, 0.05)], (n[0], n[1], 0), [(0, 0), (1, 0), (1, 1), (0, 1)], D.hexl('#a3a7a8'))
                D.band(m, mf, a, b_, gz + 4.1, gz + 4.5, 1.6, SLAB)
                m.quad(mg, [D.P3(a, t, n, 0.15, gz + 2.7, -0.2), D.P3(a, t, n, L - 0.15, gz + 2.7, -0.2), D.P3(a, t, n, L - 0.15, gz + 3.0, -0.2), D.P3(a, t, n, 0.15, gz + 3.0, -0.2)],
                       [(985 / 1024, 0.05), (1005 / 1024, 0.05), (1005 / 1024, 0.15), (985 / 1024, 0.15)], n=(n[0], n[1], 0))   # night light cove under the sign band
                D.band(m, mf, a, b_, gz + h - 0.4, gz + h + 0.2, 0.25, SLAB)
            m.flat(mf, P, gz + h + 0.2, D.hexl("#7c7e7d"))
            # --- shop signs on the south front (positions from OSM shops, projected on the long south edge)
            south = [(ring[i], ring[(i + 1) % ne]) for i in range(ne)]
            south = [(a_, b_) for a_, b_ in south if math.dist(a_, b_) > 10 and D.frame_of(a_, b_)[2][1] < -0.3]
            for s0, s1, sx, sy, wd in SHOPS:
                px, py = sx - ox, sy - oy
                best = None
                for a_, b_ in south:
                    L_, t_, n_ = D.frame_of(a_, b_); u = (px - a_[0]) * t_[0] + (py - a_[1]) * t_[1]; dn = (px - a_[0]) * n_[0] + (py - a_[1]) * n_[1]
                    if 1.5 < u < L_ - 1.5 and (best is None or abs(dn) < best[0]): best = (abs(dn), a_, b_, L_, t_, n_, u)
                if best is None: continue
                _, a_, b_, L_, t_, n_, u = best
                u0 = min(max(u - wd / 2, 0.3), L_ - wd - 0.3)
                U0, U1 = s0 / 1024, s1 / 1024
                pts = [D.P3(a_, t_, n_, u0, gz + 3.0, 0.04), D.P3(a_, t_, n_, u0 + wd, gz + 3.0, 0.04), D.P3(a_, t_, n_, u0 + wd, gz + 4.05, 0.04), D.P3(a_, t_, n_, u0, gz + 4.05, 0.04)]
                m.quad(mg, pts, [(U0, SIGN_V[0]), (U1, SIGN_V[0]), (U1, SIGN_V[1]), (U0, SIGN_V[1])], n=(n_[0], n_[1], 0))
            # --- green roof: discs + skylights on the podium roof (SWISSIMAGE)
            zr = gz + h + 0.2; rc = list(P.minimum_rotated_rectangle.exterior.coords)[:4]
            ei = max(range(4), key=lambda q: math.dist(rc[q], rc[(q + 1) % 4])); a0, b0 = rc[ei], rc[(ei + 1) % 4]; el, tl, _ = D.frame_of(a0, b0)
            nl = (-tl[1], tl[0]); cen = P.centroid
            if (cen.x - a0[0]) * nl[0] + (cen.y - a0[1]) * nl[1] < 0: nl = (-nl[0], -nl[1])
            towers = unary_union([localize(f, ox, oy).buffer(1.5) for f in fps[1:]]); inner = P.buffer(-2.6).difference(towers); k = 0
            for iu in range(0, int(el / 5.4)):
                for iv in range(0, 6):
                    uu = 3.0 + iu * 5.4 + (2.7 if iv % 2 else 0); vv = 3.2 + iv * 5.0
                    x_ = a0[0] + tl[0] * uu + nl[0] * vv; y_ = a0[1] + tl[1] * uu + nl[1] * vv
                    if not inner.contains(Point(x_, y_)): continue
                    k += 1
                    m.cylinder(mf, x_, y_, 1.7, zr, zr + 0.07, n=6, col=D.hexl("#847f6c"), cap=mf, capcol=D.hexl("#847f6c"))
                    if k % 2 == 0: m.box(mf, x_, y_, 2.1, 1.3, zr + 0.07, zr + 0.55, rot=math.atan2(tl[1], tl[0]), col=D.hexl("#c6cbcc"))
            ea, eb = max(zip(ring, ring[1:] + ring[:1]), key=lambda e: math.dist(*e)); L, t, n = D.frame_of(ea, eb)
            u0, u1 = L * 0.3, L * 0.3 + 16.0; zz = gz + h + 0.2
            # rooftop light-box lettering «LOCHERGUT» (photos 52, 75): white box on legs, glows magenta/pink at night, colour animated at runtime (material lochergut_neon)
            zb, zt_, dep = zz + 1.0, zz + 3.5, 0.9
            for uu in np.linspace(u0 + 0.6, u1 - 0.6, 9): m.box(mf, *[(D.P3(ea, t, n, uu, 0, -0.5)[q]) for q in (0, 1)], 0.25, 0.25, zz, zb, rot=math.atan2(t[1], t[0]), col=D.hexl("#3b3f42"))
            P_ = lambda u, z, d_: D.P3(ea, t, n, u, z, d_)
            m.quad(mn, [P_(u0, zb, 0.0), P_(u1, zb, 0.0), P_(u1, zt_, 0.0), P_(u0, zt_, 0.0)], [(0, 0), (1, 0), (1, 1), (0, 1)], n=(n[0], n[1], 0))
            for a_, b_, nn in ((P_(u0, zb, -dep), P_(u1, zb, -dep), (-n[0], -n[1], 0)),):
                m.quad(mn, [P_(u1, zb, -dep), P_(u0, zb, -dep), P_(u0, zt_, -dep), P_(u1, zt_, -dep)], [(0, 0), (1, 0), (1, 1), (0, 1)], n=nn)
            m.quad(mn, [P_(u0, zt_, 0.0), P_(u1, zt_, 0.0), P_(u1, zt_, -dep), P_(u0, zt_, -dep)], [(0, 0.9), (1, 0.9), (1, 1), (0, 1)], n=(0, 0, 1))
            for uu, nn in ((u0, (-t[0], -t[1], 0)), (u1, (t[0], t[1], 0))):
                m.quad(mn, [P_(uu, zb, 0.0), P_(uu, zb, -dep), P_(uu, zt_, -dep), P_(uu, zt_, 0.0)], [(0, 0.5), (0.01, 0.5), (0.01, 0.6), (0, 0.6)], n=nn)
            continue
        FH = 2.9; n0 = int(round((H - 3.2) / FH)); top = 3.2 + n0 * FH
        m.extrude(mf, mf, P, gz - 3, gz + 3.2, col=CONC, roof=False)
        for i in range(ne):
            a, b_ = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b_)
            if L < 1.0: continue
            if L > 12:    # long facade: ribbon band with slab edges
                D.ribbon_floors(m, mw, mg, mf, a, b_, gz + 3.2, n0, FH, 1.0, 1.35, 0.2, mul('#e4dfd0'), SLAB, rng, wmod=(5.2, 2.9), seg=7.8, slab_out=0.35, slab_col=SLAB, pier=0.0, lite=True)
            else:         # end / narrow wall: brown panel with punched windows
                def hole(u0, u1, f0, f1, fl):
                    if (u1 - u0) < 1.4: return None
                    uc = (u0 + u1) / 2; return D.rect_pts(uc - 0.55, f0 + 0.9, uc + 0.55, f0 + 2.3)
                D.wall_run(m, mw, mg, mf, a, b_, gz + 3.2, n0, FH, 2.6, hole, 0.15, TAN, SLAB, rng, wmod=(5.2, 2.9))
            D.band(m, mf, a, b_, gz + top - 0.1, gz + top + 0.9, 0.12, SLAB)       # parapet / roof edge
        m.flat(mf, P, gz + top + 0.9, D.hexl("#6f7274"))
        cc = P.centroid; m.box(mf, cc.x, cc.y, 7, 5, gz + top + 0.9, gz + top + 3.8, col=D.hexl("#9b9992"))        # lift/stair head
        m.box(mf, cc.x + 5, cc.y - 3, 2, 2, gz + top + 0.9, gz + top + 2.0, col=D.hexl("#8d8b85"))
        if k == 2: m.cylinder(mf, cc.x - 4, cc.y, 0.12, gz + top + 3.8, gz + top + 13, n=6, col=D.hexl("#b8b8b8"))       # antenna mast
    finish(m, "lochergut", "Lochergut", ox, oy, oz, hide_union("Lochergut", _hide(bs)), reg=False)


def _hide(bs):
    out = []
    for b in bs:
        fp = b["fp"]; out += [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    return out


if __name__ == "__main__":
    build()
