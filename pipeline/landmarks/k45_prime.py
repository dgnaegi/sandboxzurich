"""Prime Tower (Gigon/Guyer 2011, 126 m) with staggered massing, teal glass; plus Platform glass box."""
import math
from PIL import Image, ImageDraw, ImageFont
from common import *
from lm import *
import tex
from shapely.affinity import translate


def sign_tex():
    im = Image.new("RGBA", (1024, 128), hexc("#101214")); d = ImageDraw.Draw(im)
    f = None
    for p in ("/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf", "/System/Library/Fonts/Supplemental/Arial Italic.ttf", "/System/Library/Fonts/Helvetica.ttc"):
        try: f = ImageFont.truetype(p, 88); break
        except Exception: pass
    d.text((512, 66), "PRIME TOWER", font=f or ImageFont.load_default(), fill=hexc("#f2f2f0"), anchor="mm")
    return im


def build():
    T = bid("ID_85D5F868"); PL = bid("ID_6FB7219D")
    P = outline(T["fp"], 0.5); Q = outline(PL["fp"], 0.6)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl, Ql = localize(P, ox, oy), localize(Q, ox, oy)
    m = Model("prime")
    mg = m.mat("glass", *tile(4, 2, 64, 96, tex.curtain("#1d2a2b", "#4f9d92", "#7ac2b4", mull=1, spandrel=0.3, spandrel_col="#2f6f68", lit_col=(255, 232, 180)), 31, 0.22), rough=0.4)
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    ms = m.mat("sign", sign_tex(), None)
    H = T["zmax"] - ground(P.centroid.x, P.centroid.y)
    top = 126.0
    # plinth: recessed dark glazing, overhanging dark soffit band
    m.extrude(mf, mf, Pl.buffer(-2.5, join_style=2), -3, 7.0, col=hexc("#1b2224"), roof=False)
    ov = Pl.buffer(1.0, join_style=2)
    m.extrude(mf, mf, ov, 7.0, 8.6, col=hexc("#15191a"), rcol=hexc("#15191a"))
    # staggered shafts
    segs = [(8.6, 50.4, Pl), (50.4, 90.0, Pl.intersection(translate(Pl, 3.0, -2.5)).buffer(0)), (90.0, top, Pl.intersection(translate(Pl, -3.0, 2.5)).buffer(0))]
    for z0, z1, poly in segs:
        if poly.geom_type == "MultiPolygon": poly = max(poly.geoms, key=lambda g: g.area)
        m.extrude(mg, mf, poly, z0, z1, mod=(6.0, 7.2), rcol=hexc("#8a8c8a"), wallv0=0.0)
        # slab ledge at each shift
        m.extrude(mf, mf, poly.buffer(0.25, join_style=2), z0 - 0.3, z0 + 0.1, col=hexc("#c9cbc9"), roof=False)
    m.box(mf, 0, 0, 7, 7, top, top + 3.0, col=hexc("#2b2e2e"))
    # name plate on the plinth fascia: longest edge
    ring = list(orient(ov, 1.0).exterior.coords); best = max(zip(ring[:-1], ring[1:]), key=lambda ab: math.dist(*ab))
    a, b = best; L = math.dist(a, b); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; n = (uy, -ux)
    w = min(14.0, L * 0.8); mx, my = (a[0] + b[0]) / 2 + n[0] * 0.05, (a[1] + b[1]) / 2 + n[1] * 0.05
    p0 = (mx - ux * w / 2, my - uy * w / 2); p1 = (mx + ux * w / 2, my + uy * w / 2)
    m.quad(ms, [(p0[0], p0[1], 7.1), (p1[0], p1[1], 7.1), (p1[0], p1[1], 8.5), (p0[0], p0[1], 8.5)], [(0, 1), (1, 1), (1, 0), (0, 0)])
    # Platform: 29 m glass box, 7 floors
    HQ = 28.0
    m.extrude(mf, mf, Ql.buffer(-1.5, join_style=2), -3, 4.0, col=hexc("#222c30"), roof=False)
    m.extrude(mg, mf, Ql, 4.0, HQ, mod=(6.0, 7.2), col=(215, 228, 240, 255), rcol=hexc("#7d7f7e"), wallv0=0.0)
    hide = []
    for bb in (T, PL):
        fp = bb["fp"]; hide += [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    finish(m, "prime_tower", "Prime Tower + Platform", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
