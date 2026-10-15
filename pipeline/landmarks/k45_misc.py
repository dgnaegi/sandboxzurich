"""Lochergut, Kalkbreite, Kirche St. Jakob, Bullingerkirche, Kanzlei-Schulhaus."""
import math, sys
from PIL import Image, ImageDraw
from common import *
from lm import *
import tex
from shapely.geometry import Polygon, box as sbox
from shapely.affinity import rotate


def hide_of(bs):
    out = []
    for b in bs:
        fp = b["fp"]; out += [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    return out


def lochergut():
    ids = ["ID_1EB1BB89", "ID_6E312FD7", "ID_C1E18200", "ID_F93C1762", "ID_1D02EC7C"]
    bs = [bid(i) for i in ids]; fps = [outline(b["fp"], 0.5) for b in bs]
    ox = round(float(np.mean([f.centroid.x for f in fps[1:]])), 1); oy = round(float(np.mean([f.centroid.y for f in fps[1:]])), 1); oz = ground(ox, oy)
    m = Model("lochergut")
    mw = m.mat("wall", *tile(4, 1, 96, 96, tex.ribbon("#b6a37a", glass="#2e3439", band=0.46, y0=0.14, slab=0.32, mull=1, mull_col="#6d655a"), 41, 0.25))
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    YEL = hexc("#cbb67c")
    for k, (b, fp) in enumerate(zip(bs, fps)):
        P = localize(fp, ox, oy); c = fp.centroid; g0 = ground(c.x, c.y)
        H = b["zmax"] - g0; gz = g0 - oz
        if k == 0:  # podium: concrete with glazed ground floor, canopy
            h = 11.0
            m.extrude(mf, mf, P, gz - 3, gz + 4.2, col=hexc("#a9a7a0"), roof=False)
            walls_by_edge(m, P, gz + 4.2, gz + h, lambda a, b_, L: (mw, (12.0, 3.0), (225, 228, 232, 255), 0.0), floors=2)
            m.flat(mf, P, gz + h, hexc("#77797a"))
            m.extrude(mf, mf, P.buffer(1.8, join_style=2), gz + 4.0, gz + 4.5, col=hexc("#d0cec7"), rcol=hexc("#d0cec7"))
            continue
        n = int(round((H - 3.0) / 2.9)); top = 3.0 + n * 2.9
        m.extrude(mf, mf, P, gz - 3, gz + 3.0, col=hexc("#b3b0a8"), roof=False)
        def ch(a, b_, L):
            return (mw, (12.0, 2.9), (255, 255, 255, 255), 0.0) if L > 15 else (mf, (3, 3), YEL, 0.0)
        walls_by_edge(m, P, gz + 3.0, gz + top, ch, floors=n)
        m.flat(mf, P, gz + top, hexc("#6f7274"))
        c2 = P.centroid; m.box(mf, c2.x, c2.y, 6, 5, gz + top, gz + top + 3, col=hexc("#9b9992"))
    finish(m, "lochergut", "Lochergut", ox, oy, oz, hide_of(bs))


def kalkbreite():
    B = bid("ID_E2807877"); P = outline(B["fp"], 0.6)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = localize(P, ox, oy); H = B["zmax"] - ground(P.centroid.x, P.centroid.y)
    m = Model("kalkbreite")
    mw = m.mat("wall", *tile(4, 1, 96, 96, tex.ribbon("#d8d6cf", glass="#3b4a52", band=0.5, y0=0.15, slab=0.2, mull=2, mull_col="#b9b3a6"), 51, 0.3))
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    m.extrude(mf, mf, Pl, -3, 7.0, col=hexc("#7e7f7c"), roof=False)
    FL = 3.0; n = int(round((H - 7.0) / FL)); top = 7.0 + n * FL
    walls_by_edge(m, Pl, 7.0, top, lambda a, b, L: (mw, (12.0, FL), (255, 255, 255, 255), 0.0), floors=n)
    m.flat(mf, Pl, top, hexc("#6b6e6c"))
    # tram portals: dark arches along the ground floor of the long street edge
    ring = list(orient(Pl, 1.0).exterior.coords)
    a, b = max(zip(ring[:-1], ring[1:]), key=lambda ab: math.dist(*ab)); L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx_, ny_ = uy, -ux
    for t in np.arange(8, L - 8, 14):
        p0 = (a[0] + ux * t + nx_ * 0.08, a[1] + uy * t + ny_ * 0.08); p1 = (a[0] + ux * (t + 7) + nx_ * 0.08, a[1] + uy * (t + 7) + ny_ * 0.08)
        m.quad(mf, [(p0[0], p0[1], 0), (p1[0], p1[1], 0), (p1[0], p1[1], 5.2), (p0[0], p0[1], 5.2)], col=hexc("#232b30"))
    # rooftop garden + pavilion
    m.box(mf, 0, 0, 14, 8, top, top + 3.2, col=hexc("#b8b4a8"), rot=0.5)
    finish(m, "kalkbreite", "Kalkbreite", ox, oy, oz, hide_of([B]))


def church(bid_, name, title, tower_pt, tower_h, spire_h, nave_h, body_col, roofcol, painter, tile_args, spire_col, tower_w=7.5, lancet=True):
    B = bid(bid_); P = outline(B["fp"], 0.5)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = localize(P, ox, oy)
    m = Model(name)
    mw = m.mat("wall", *tile(*tile_args, painter, 61, 0.2)); mf = m.mat("flat", solid((255, 255, 255, 255)))
    m.extrude(mf, mf, Pl, -3, 0.0, col=body_col, roof=False)
    walls_by_edge(m, Pl, 0.0, nave_h, lambda a, b, L: (mw, (tile_args[0] * 4.0, nave_h), (255, 255, 255, 255), 0.0))
    rect = rect_of(Pl); (cx, cy), ux, uy, L, W = rect
    gable_roof(m, mf, mw, rect, nave_h, min(9.0, W * 0.42), roofcol, body_col)
    # tower at the long-axis end nearest tower_pt
    tx, ty = tower_pt[0] - ox, tower_pt[1] - oy
    s = 1 if ((tx - cx) * ux + (ty - cy) * uy) > 0 else -1
    tc = (cx + ux * s * (L / 2 - tower_w / 2 - 0.3), cy + uy * s * (L / 2 - tower_w / 2 - 0.3))
    ang = math.atan2(uy, ux)
    m.box(mw, tc[0], tc[1], tower_w, tower_w, 0.0, tower_h, rot=ang, mod=(tile_args[0] * 4.0, tower_h))
    # spire: octagonal pyramid (or flat cap for Bullingerkirche)
    if spire_h > 0:
        m.cylinder(mf, tc[0], tc[1], tower_w * 0.62, tower_h, tower_h + spire_h, n=8, col=spire_col, r1=0.15, smooth=False)
        for k in range(4):   # dormer gablets
            a = ang + math.pi / 4 + k * math.pi / 2
            m.box(mf, tc[0] + math.cos(a) * tower_w * 0.5, tc[1] + math.sin(a) * tower_w * 0.5, 1.6, 1.6, tower_h, tower_h + 3.5, rot=a, col=body_col)
    else:
        m.box(mf, tc[0], tc[1], tower_w + 0.8, tower_w + 0.8, tower_h, tower_h + 0.8, rot=ang, col=hexc("#e6e0d0"))
        # clock faces (blue) on four sides
        for k in range(4):
            a = ang + k * math.pi / 2; r = tower_w / 2 + 0.06
            nx_, ny_ = math.cos(a), math.sin(a); tx_, ty_ = -ny_, nx_
            p0 = (tc[0] + nx_ * r - tx_ * 1.4, tc[1] + ny_ * r - ty_ * 1.4); p1 = (tc[0] + nx_ * r + tx_ * 1.4, tc[1] + ny_ * r + ty_ * 1.4)
            z0 = tower_h - 5.0
            m.quad(mf, [(p0[0], p0[1], z0), (p1[0], p1[1], z0), (p1[0], p1[1], z0 + 2.8), (p0[0], p0[1], z0 + 2.8)], col=hexc("#2a5fa8"))
    finish(m, name, title, ox, oy, oz, hide_of([B]))


def stone_lancet(d, de, x, y, w, h, rng, on, ix, iy):
    S = hexc("#a8977c")
    d.rectangle([x, y, x + w, y + h], fill=S)
    for k in range(0, h, 7):
        d.line([x, y + k, x + w, y + k], fill=shade(S, 0.82))
        for j in range(((k // 7) % 2) * 9, w, 18): d.line([x + j, y + k, x + j, y + k + 7], fill=shade(S, 0.86))
    for _ in range(30):
        bx, by = x + int(rng.random() * w), y + int(rng.random() * h); d.rectangle([bx, by, bx + 14, by + 6], fill=shade(S, 0.9 + rng.random() * 0.2))
    d.rectangle([x, y, x + int(w * 0.1), y + h], fill=shade(S, 0.78)); d.rectangle([x + w - int(w * 0.1), y, x + w, y + h], fill=shade(S, 0.78))   # buttress strips
    ww = int(w * 0.34); x0 = x + (w - ww) // 2; y1 = y + int(h * 0.82); y0 = y + int(h * 0.30)
    for (a_, col) in ((4, hexc("#d8ccb0")), (0, hexc("#27384a"))):
        d.rectangle([x0 - a_, y0, x0 + ww + a_, y1], fill=col)
        d.polygon([(x0 - a_, y0), (x0 + ww + a_, y0), (x0 + ww // 2, y0 - ww - a_ * 2)], fill=col)
    d.line([x0 + ww // 2, y0 - ww, x0 + ww // 2, y1], fill=hexc("#16181a"), width=2)
    d.line([x0, y0 + 14, x0 + ww, y0 + 14], fill=hexc("#16181a"), width=2)
    d.rectangle([x, y + int(h * 0.94), x + w, y + h], fill=shade(S, 0.65))
    if on:
        d.rectangle([0, 0, 0, 0], fill=None) if False else None
        de.rectangle([x0 + 2, y0, x0 + ww - 2, y1 - 2], fill=(255, 150, 100))
        de.polygon([(x0 + 2, y0), (x0 + ww - 2, y0), (x0 + ww // 2, y0 - ww + 4)], fill=(255, 150, 100))


def stucco_church(d, de, x, y, w, h, rng, on, ix, iy):
    S = hexc("#ddd2b6")
    d.rectangle([x, y, x + w, y + h], fill=shade(S, 0.97 + rng.random() * 0.06))
    ww = int(w * 0.30); x0 = x + (w - ww) // 2; y0 = y + int(h * 0.28); y1 = y + int(h * 0.80)
    d.rectangle([x0 - 4, y0 - 4, x0 + ww + 4, y1 + 4], fill=hexc("#f1ebd9"))
    d.pieslice([x0 - 4, y0 - ww // 2 - 4, x0 + ww + 4, y0 + ww // 2 + 4], 180, 360, fill=hexc("#f1ebd9"))
    d.rectangle([x0, y0, x0 + ww, y1], fill=hexc("#2c3e52")); d.pieslice([x0, y0 - ww // 2, x0 + ww, y0 + ww // 2], 180, 360, fill=hexc("#2c3e52"))
    d.line([x0 + ww // 2, y0 - ww // 2, x0 + ww // 2, y1], fill=hexc("#e8e2d0"), width=2)
    d.rectangle([x, y + int(h * 0.94), x + w, y + h], fill=shade(S, 0.78))
    if on:
        de.rectangle([x0 + 2, y0, x0 + ww - 2, y1 - 2], fill=(255, 190, 120)); de.pieslice([x0 + 2, y0 - ww // 2 + 2, x0 + ww - 2, y0 + ww // 2], 180, 360, fill=(255, 190, 120))


def kanzlei():
    B = bid("ID_3822D538"); P = outline(B["fp"], 0.5)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = localize(P, ox, oy); H = B["zmax"] - ground(P.centroid.x, P.centroid.y)
    m = Model("kanzlei")
    g = tile(4, 1, 90, 96, tex.punched("#d3c3a0", glass="#2c3a45", fw=0.42, fh=0.62, top=0.2, frame="#efe8d6", arch=True, sill="#cbbd9b", noise=8), 71, 0.1)
    mw = m.mat("wall", *g); mf = m.mat("flat", solid((255, 255, 255, 255)))
    FL = 4.0; n = 4; eave = n * FL + 0.6
    m.extrude(mf, mf, Pl, -3, 0.9, col=hexc("#9a9484"), roof=False)
    walls_by_edge(m, Pl, 0.9, 0.9 + n * FL, lambda a, b, L: (mw, (14.4, FL), (255, 255, 255, 255), 0.0), floors=n)
    cor = Pl.buffer(0.5, join_style=2)
    m.extrude(mf, mf, cor, eave - 0.6, eave + 0.2, col=hexc("#e4dac1"), roof=False)
    q1 = taper(m, mf, Pl.buffer(0.4, join_style=2), eave + 0.2, eave + H * 0.0 + 6.5, 0.55, hexc("#8a3f32"), cap=True)
    m.box(mf, q1.centroid.x, q1.centroid.y, 1.3, 1.3, eave + 5, eave + 9, col=hexc("#a05a45"))
    finish(m, "kanzlei_schulhaus", "Kanzlei-Schulhaus", ox, oy, oz, hide_of([B]))


if __name__ == "__main__":
    which = sys.argv[1:] or ["lochergut", "kalkbreite", "jakob", "bullinger", "kanzlei"]
    if "lochergut" in which: lochergut()
    if "kalkbreite" in which: kalkbreite()
    if "jakob" in which:
        church("ID_B0FF1289", "st_jakob", "Kirche St. Jakob", (949, -1219), 40.0, 36.0, 13.0, hexc("#a8977c"), hexc("#4c5560"), stone_lancet, (4, 1, 96, 224), hexc("#6f9a98"), 8.0)
    if "bullinger" in which:
        church("ID_7B3577FB", "bullingerkirche", "Bullingerkirche", (-41, -496), 32.0, 0.0, 11.5, hexc("#ddd2b6"), hexc("#8c4a3a"), stucco_church, (4, 1, 96, 224), hexc("#999"), 6.5)
    if "kanzlei" in which: kanzlei()
