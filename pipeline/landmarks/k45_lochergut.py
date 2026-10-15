"""Lochergut (1966, Hans Hofmann / Hans Fischli): staggered slabs with ribbon floors, light concrete slab edges + brown/tan parapet panels,
end walls with punched windows, glazed 2-storey podium with ribbed grey fascia. Photos: research/v3/lochergut.md."""
import math
from PIL import Image, ImageDraw
from common import *
from lm import *
import detail as D
from shapely.geometry import Polygon

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


def build():
    bs = [bid(i) for i in IDS]; fps = [outline(b["fp"], 0.5) for b in bs]
    ox = round(float(np.mean([f.centroid.x for f in fps[1:]])), 1); oy = round(float(np.mean([f.centroid.y for f in fps[1:]])), 1); oz = ground(ox, oy)
    rng = np.random.default_rng(7)
    m = Model("lochergut")
    mw = m.mat("wall", panels(hexc("#e9e4d4"), joint=0.9))
    ga = D.glass_atlas_g(frame="#d9d4c6", glass="#2c353b", sky="#8aa0b0", cols=2, rows=1, seed=8, bar=2, lit_p=0.3, sign=D.letters_strip([(0, 1024, "ZENTRUM LOCHERGUT", "#52565a", "#d4d6d3", None)], size=26), curtain_cols=[(236, 228, 210), (214, 205, 185), (225, 225, 228), (190, 180, 160)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid((255, 255, 255, 255)))
    BR, SLAB, CONC, GREY = D.hexl("#c2b8a2"), D.hexl("#d3cdbd"), D.hexl("#a9a79f"), D.hexl("#c9cac7")
    W = (255, 255, 255, 255)
    lin = lambda v: (v / 255) ** 2.2
    def mul(target, base="#e9e4d4"):
        T, B_ = hexc(target), hexc(base); return tuple(int(min(255, 255 * lin(T[i]) / lin(B_[i]))) for i in range(3)) + (255,)
    TAN = mul("#b69b76")
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
                D.ribbon_floors(m, mw, mg, mf, a, b_, gz, 1, 4.3, 0.5, 3.2, 0.25, (255, 255, 255, 255), CONC, rng, wmod=(5, 4), seg=2.6, slab_out=0.0, pier=0.07)
                # ribbed fascia (storey 2), canopy lip
                m.wall(mf, a, b_, gz + 4.3, gz + h, (3, 3), GREY)
                D.band(m, mf, a, b_, gz + 4.1, gz + 4.5, 1.6, SLAB)
                D.band(m, mf, a, b_, gz + h - 0.4, gz + h + 0.2, 0.25, SLAB)
            m.flat(mf, P, gz + h + 0.2, D.hexl("#7c7e7d"))
            ea, eb = max(zip(ring, ring[1:] + ring[:1]), key=lambda e: math.dist(*e)); L, t, n = D.frame_of(ea, eb)
            u0, u1 = L * 0.3, L * 0.3 + 15.0; zz = gz + h + 0.2
            p0, p1 = D.P3(ea, t, n, u0, zz, -0.6), D.P3(ea, t, n, u1, zz, -0.6)
            D.band(m, mf, D.P3(ea, t, n, u0 - 0.2, 0, -0.5)[:2], D.P3(ea, t, n, u1 + 0.2, 0, -0.5)[:2], zz, zz + 1.7, 0.4, D.hexl("#d4d6d3"))
            m.quad(mg, [D.P3(ea, t, n, u0, zz + 0.25, -0.05), D.P3(ea, t, n, u1, zz + 0.25, -0.05), D.P3(ea, t, n, u1, zz + 1.45, -0.05), D.P3(ea, t, n, u0, zz + 1.45, -0.05)], [(0, 0), (1, 0), (1, 0.25), (0, 0.25)], n=(n[0], n[1], 0))
            continue
        FH = 2.9; n0 = int(round((H - 3.2) / FH)); top = 3.2 + n0 * FH
        m.extrude(mf, mf, P, gz - 3, gz + 3.2, col=CONC, roof=False)
        for i in range(ne):
            a, b_ = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b_)
            if L < 1.0: continue
            if L > 12:    # long facade: ribbon band with slab edges
                D.ribbon_floors(m, mw, mg, mf, a, b_, gz + 3.2, n0, FH, 1.0, 1.35, 0.2, mul('#e4dfd0'), SLAB, rng, wmod=(5.2, 2.9), seg=3.9, slab_out=0.35, slab_col=SLAB, pier=0.0)
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
    finish(m, "lochergut", "Lochergut", ox, oy, oz, hide_union("Lochergut", _hide(bs)))


def _hide(bs):
    out = []
    for b in bs:
        fp = b["fp"]; out += [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    return out


if __name__ == "__main__":
    build()
