"""Prime Tower (Gigon/Guyer 2011, 126 m): five stacked, slightly twisted/offset glass volumes with vertical-emphasis curtain wall
(1.35 m axis, 3.7 m floors, dark teal), recessed plinth with overhang + lit PRIME TOWER lettering; Platform glass block."""
import math
from PIL import Image, ImageDraw, ImageFont
from common import *
from lm import *
import detail as D
from shapely.affinity import translate, rotate, scale


def sign_tex():
    im = Image.new("RGBA", (1024, 128), hexc("#101214")); em = Image.new("RGB", (1024, 128), (0, 0, 0))
    f = None
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf", "/System/Library/Fonts/Supplemental/Arial Italic.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try: f = ImageFont.truetype(p, 88); break
        except Exception: pass
    for img, col in ((im, hexc("#f4f4f2")), (em, (255, 255, 255))):
        ImageDraw.Draw(img).text((512, 66), "PRIME TOWER", font=f or ImageFont.load_default(), fill=col, anchor="mm")
    return im, em


def curtain_painter(glass_hi="#52b0ac", glass_lo="#1f6470", mull="#26363c", spand="#1d4a52", lit=(255, 232, 182), lit_p=0.42):
    GH, GL, MU, SP = hexc(glass_hi), hexc(glass_lo), hexc(mull), hexc(spand)
    def p(d, de, x, y, w, h, rng, on, ix, iy):
        d.rectangle([x, y, x + w, y + h], fill=MU)
        sp0 = y + int(h * 0.72); gx0, gx1 = x + 3, x + w - 3
        t0 = rng.random() * 0.5
        for yy in range(y + 2, sp0):                                  # vision glass: sky reflection fades downward
            f = ((yy - y) / (sp0 - y)); k = min(1.0, 0.25 + 0.75 * f + t0 * 0.2)
            c = tuple(int(GH[i] * (1 - k) + GL[i] * k) for i in range(3)) + (255,)
            d.line([gx0, yy, gx1, yy], fill=c)
        d.rectangle([gx0, sp0 + 1, gx1, y + h - 4], fill=SP)           # spandrel panel
        d.line([x, y + h - 2, x + w, y + h - 2], fill=shade(MU, 1.6), width=2)    # slab edge
        if rng.random() < lit_p:
            k = rng.random()
            de.rectangle([gx0 + 1, y + 4, gx1 - 1, sp0 - 1], fill=tuple(int(v * (0.5 + 0.5 * k)) for v in lit))
    return p


def build():
    T = bid("ID_85D5F868"); PL = bid("ID_6FB7219D")
    P = outline(T["fp"], 0.5); Q = outline(PL["fp"], 0.6)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl, Ql = localize(P, ox, oy), localize(Q, ox, oy)
    m = Model("prime")
    mg = m.mat("glass", *tile(4, 2, 80, 112, curtain_painter(), 31, 1.0), rough=0.35)
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    ms = m.mat("sign", *sign_tex())
    MOD = (5.4, 7.4)
    top = 126.0
    # plinth: recessed dark glazing, overhanging dark soffit band
    m.extrude(mf, mf, Pl.buffer(-2.5, join_style=2), -3, 7.0, col=D.hexl("#1b2a2e"), roof=False)
    ov = Pl.buffer(1.0, join_style=2)
    m.extrude(mf, mf, ov, 7.0, 8.6, col=D.hexl("#15191a"), rcol=D.hexl("#15191a"))
    # five volumes, each shifted/twisted/shrunk a little (no right angle in the silhouette)
    vols = [(8.6, 36.0, 0.0, 0, 0.0, 0.0), (36.0, 62.0, 2.0, 1.0, -1.0, 0.8), (62.0, 88.0, -1.5, 2.0, 1.0, -1.0), (88.0, 108.0, 2.5, 3.0, -1.5, 1.2), (108.0, top, -1.5, 4.0, 0.8, -0.8)]
    c = Pl.centroid
    for z0, z1, rot, shr, dx, dy in vols:
        poly = rotate(Pl, rot, origin=(c.x, c.y)); poly = translate(poly, dx, dy)
        poly = poly.buffer(-shr * 0.25, join_style=2)
        if poly.geom_type == "MultiPolygon": poly = max(poly.geoms, key=lambda g: g.area)
        poly = orient(poly.simplify(0.2), 1.0)
        ring = list(poly.exterior.coords)[:-1]
        for i in range(len(ring)):
            a, b = ring[i], ring[(i + 1) % len(ring)]
            if math.dist(a, b) < 0.3: continue
            m.wall(mg, a, b, z0, z1, MOD, (255, 255, 255, 255), u0=(i * 0.37) % 1, v0=0.0)
        m.flat(mf, poly, z1, D.hexl("#2e3234")); m.flat(mf, poly, z0, D.hexl("#1b2224"), up=False)
        D.band(m, mf, ring[0], ring[0], 0, 0, 0, (0, 0, 0, 0)) if False else None
        m.extrude(mf, mf, poly.buffer(0.2, join_style=2), z1 - 0.9, z1 - 0.2, col=D.hexl("#c9cbc9"), roof=False)    # slab ledge/parapet band
    m.box(mf, 0, 0, 6, 6, top, top + 3.0, col=D.hexl("#2b2e2e")); m.cylinder(mf, 3, 1, 0.12, top + 3, top + 12, n=6, col=D.hexl("#aaaaaa"))
    # name plate on the plinth fascia: longest edge
    ring = list(orient(ov, 1.0).exterior.coords); best = max(zip(ring[:-1], ring[1:]), key=lambda ab: math.dist(*ab))
    a, b = best; L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; n = (uy, -ux)
    w = min(16.0, L * 0.8); mx, my = (a[0] + b[0]) / 2 + n[0] * 0.05, (a[1] + b[1]) / 2 + n[1] * 0.05
    p0 = (mx - ux * w / 2, my - uy * w / 2); p1 = (mx + ux * w / 2, my + uy * w / 2)
    m.quad(ms, [(p0[0], p0[1], 7.1), (p1[0], p1[1], 7.1), (p1[0], p1[1], 8.5), (p0[0], p0[1], 8.5)], [(0, 1), (1, 1), (1, 0), (0, 0)], n=(n[0], n[1], 0))
    # Platform: glass block, 7 floors
    HQ = 27.0
    m.extrude(mf, mf, Ql.buffer(-1.5, join_style=2), -3, 4.0, col=D.hexl("#222c30"), roof=False)
    ringq = list(orient(Ql, 1.0).exterior.coords)[:-1]
    for i in range(len(ringq)):
        a, b = ringq[i], ringq[(i + 1) % len(ringq)]
        if math.dist(a, b) < 0.3: continue
        m.wall(mg, a, b, 4.0, HQ, MOD, (255, 255, 255, 255), u0=(i * 0.21) % 1)
    m.flat(mf, orient(Ql, 1.0), HQ, D.hexl("#7d7f7e")); m.extrude(mf, mf, Ql.buffer(0.15, join_style=2), HQ - 0.6, HQ + 0.5, col=D.hexl("#b9bbb9"), roof=False)
    hide = []
    for bb in (T, PL):
        fp = bb["fp"]; hide += [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    finish(m, "prime_tower", "Prime Tower + Platform", ox, oy, oz, hide_union("Prime Tower + Platform", hide))


if __name__ == "__main__":
    build()
