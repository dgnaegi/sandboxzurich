"""Schiffbau (Escher Wyss ship hall 1892, now Schauspielhaus): brick hall with tall arched windows + octagonal brick chimney (45 m)."""
import math
from PIL import Image, ImageDraw
from common import *
from lm import *
from shapely.geometry import Polygon, Point
import detail as D

BR = hexc("#c2a05e")


PPM = 24   # px per metre in the hall bay texture (module = one 4.4 m window axis)


def brick_painter(d, de, x, y, w, h, rng, on, ix, iy):
    """One window axis of the hall (4.4 m x 14.2 m): grey plastered plinth, ochre brick with tone patches and courses, pilaster strips,
    tall slender round-arched steel window with square panes, stone surround, sill."""
    p = lambda m_: int(m_ * PPM)
    d.rectangle([x, y, x + w, y + h], fill=BR)
    for k in range(0, h, 5):
        d.line([x, y + k, x + w, y + k], fill=shade(BR, 0.86))
        off = 7 * ((k // 5) % 2)
        for j in range(0, w, 14): d.line([x + j + off, y + k, x + j + off, y + k + 5], fill=shade(BR, 0.9))
    for _ in range(70):   # brick tone patches (yellow-ochre, some brownish repairs)
        bx, by = x + int(rng.random() * w), y + int(rng.random() * h * 0.9); f = 0.82 + rng.random() * 0.36
        c = shade(BR, f) if rng.random() < 0.85 else shade((172, 120, 74, 255), f)
        d.rectangle([bx, by, bx + 12, by + 4], fill=c)
    pil = p(0.45)
    for xx in (x, x + w - pil):   # pilaster strips
        d.rectangle([xx, y + p(2.6), xx + pil, y + p(13.4)], fill=shade(BR, 0.8))
    ww = p(2.0); x0 = x + (w - ww) // 2
    sill_y = y + h - p(3.0); spring = y + h - p(9.7); top = spring - ww // 2
    # stone surround (arch + jambs)
    fb = p(0.22)
    d.pieslice([x0 - fb, top - fb, x0 + ww + fb, spring + ww // 2 + fb], 180, 360, fill=hexc("#cfc5a8"))
    d.rectangle([x0 - fb, spring, x0 + ww + fb, sill_y + p(0.15)], fill=hexc("#cfc5a8"))
    G = hexc("#3a4b55"); bar = hexc("#1d2226")
    d.pieslice([x0, top, x0 + ww, spring + ww // 2], 180, 360, fill=G)
    d.rectangle([x0, spring, x0 + ww, sill_y], fill=G)
    # square-pane steel grid + central mullion + transom
    pw = ww / 4.0; yy = sill_y
    while yy > top:
        d.line([x0, yy, x0 + ww, yy], fill=bar, width=1); yy -= p(0.5)
    for k in range(1, 4):
        xx = x0 + int(pw * k); d.line([xx, top + (ww // 2 - int(math.sqrt(max(0, (ww / 2) ** 2 - (xx - x0 - ww / 2) ** 2)))), xx, sill_y], fill=bar, width=2 if k == 2 else 1)
    d.line([x0, spring - p(3.0), x0 + ww, spring - p(3.0)], fill=bar, width=3)   # transom
    d.arc([x0, top, x0 + ww, spring + ww // 2], 180, 360, fill=bar, width=3)
    d.rectangle([x0 - fb - 3, sill_y + p(0.15), x0 + ww + fb + 3, sill_y + p(0.32)], fill=hexc("#bfb596"))   # sill
    # grey plastered plinth with joints, stained
    d.rectangle([x, y + h - p(2.6), x + w, y + h], fill=hexc("#aaa699"))
    for yy in range(y + h - p(2.6), y + h, p(0.55)): d.line([x, yy, x + w, yy], fill=hexc("#8f8b80"))
    for _ in range(14):
        bx, by = x + int(rng.random() * w), y + h - p(2.6) + int(rng.random() * p(2.4)); d.rectangle([bx, by, bx + p(0.6), by + p(0.3)], fill=shade(hexc("#aaa699"), 0.88 + rng.random() * 0.2))
    d.rectangle([x, y + h - p(2.66), x + w, y + h - p(2.5)], fill=hexc("#c6c1b2"))   # plinth cap
    d.rectangle([x, y, x + w, y + p(0.4)], fill=shade(BR, 1.12))                     # eaves course
    if on:
        de.pieslice([x0 + 2, top + 2, x0 + ww - 2, spring + ww // 2], 180, 360, fill=(255, 190, 110))
        de.rectangle([x0 + 2, spring, x0 + ww - 2, sill_y - 2], fill=(255, 185, 105))
        for k in range(1, 4): de.line([x0 + int(pw * k), top, x0 + int(pw * k), sill_y], fill=(0, 0, 0), width=2)
        yy = sill_y
        while yy > top:
            de.line([x0, yy, x0 + ww, yy], fill=(0, 0, 0), width=1); yy -= p(0.5)


def neubau(m, mg, mf, B, ox, oy, rng, stone, depth=0.35, upper_w=1.5, pitch=3.0, floors=None, eg_h=4.6, fh=3.55):
    """Stone-faced Neubau next to the hall (Schiffbau-Areal): arcade portals in the EG, slender deep-set windows above, parapet + roof plant."""
    P = orient(localize(outline(B["fp"], 0.6), ox, oy), 1.0)
    gz = ground(B["c"][0], B["c"][1]) - ground(ox, oy)
    H = B["zmax"] - ground(B["c"][0], B["c"][1]) + gz
    nf = max(2, int(round((H - eg_h - 0.6) / fh))); H = eg_h + nf * fh
    z0 = gz
    m.extrude(mf, mf, P, z0 - 3, z0, col=stone, roof=False)
    REV = D.hexl("#70675a"); DK = D.hexl("#8f8c84")
    ring = list(P.exterior.coords)[:-1]
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]; L, t, n = D.frame_of(a, b)
        if L < 2.0: m.wall(mf, a, b, z0, z0 + H, (4, 4), stone); continue
        D.wall_run(m, mf, mg, mf, a, b, z0, 1, eg_h, 6.0, lambda u0, u1, f0, f1, fl: D.rect_pts((u0 + u1) / 2 - 2.2, f0 + 0.2, (u0 + u1) / 2 + 2.2, f0 + 3.7), 0.5, stone, REV, rng, margin=0)
        D.wall_run(m, mf, mg, mf, a, b, z0 + eg_h, nf, fh, pitch, lambda u0, u1, f0, f1, fl: D.rect_pts((u0 + u1) / 2 - upper_w / 2, f0 + 0.55, (u0 + u1) / 2 + upper_w / 2, f0 + fh - 0.45), depth, stone, REV, rng, sill=0.1)
        D.band(m, mf, a, b, z0 + eg_h - 0.25, z0 + eg_h + 0.1, 0.12, DK)
        D.band(m, mf, a, b, z0 + H - 0.1, z0 + H + 0.9, 0.18, DK)
    m.flat(mf, P, z0 + H + 0.9, D.hexl("#6b6d6c"))
    for k in range(5):   # roof plant
        c = P.representative_point() if k == 0 else P.buffer(-8).representative_point() if not P.buffer(-8).is_empty else P.representative_point()
        px, py = c.x + rng.normal(0, P.length * 0.04), c.y + rng.normal(0, P.length * 0.04)
        if P.buffer(-3).contains(Point(px, py)): m.box(mf, px, py, 6 + k, 4, z0 + H + 0.9, z0 + H + 3.4, col=D.hexl("#9a9c9b"))
    return z0 + H


def build():
    A = bid("ID_ECC7D96E"); C = bid("ID_39E2287D")
    P = outline(A["fp"], 0.5)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = localize(P, ox, oy)
    m = Model("schiffbau")
    mb = m.mat("brick", *tile(4, 1, int(4.4 * PPM), int(14.2 * PPM), brick_painter, 5, 0.3))
    mg = m.mat("glass", *D.glass_atlas_g(frame="#6b5b3a", glass="#2d3d48", sky="#8fa9bb", cols=1, rows=3, seed=12, lit_p=0.3, cw=64), rough=0.3)
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    Hw = 14.2; HR = A["zmax"] - ground(P.centroid.x, P.centroid.y)
    m.extrude(mf, mf, Pl, -3, 0.0, col=D.hexl("#9d9a90"), roof=False)
    m.extrude(mb, mf, Pl, 0.0, Hw, mod=(17.6, Hw), roof=False, wallv0=0.0)
    rect = rect_of(Pl)
    rise = max(3.0, HR - Hw)
    gable_roof(m, mf, mb, rect, Hw, rise, D.hexl("#4f5a58"), (255, 255, 255, 255))
    # glazed monitor along the ridge
    (cx, cy), ux, uy, L, W = rect
    m.box(mf, cx, cy, L * 0.8, 2.2, Hw + rise, Hw + rise + 1.4, rot=math.atan2(uy, ux), col=D.hexl("#7f9aa5"))
    # chimney: octagonal brick shaft 45 m at the real location
    cxx, cyy = C["c"][0] - ox, C["c"][1] - oy
    gz = ground(C["c"][0], C["c"][1]) - oz
    HC = C["zmax"] - ground(*C["c"])
    for z0, z1, r0, r1, col in [(gz - 3, gz + 6, 2.4, 2.2, "#5e3226"), (gz + 6, HC - 9.0, 2.2, 1.5, "#6f3a2c")]:
        m.cylinder(mf, cxx, cyy, r0, z0, z1, n=16, col=D.hexl(col), r1=r1, smooth=True)
    zh = HC - 9.0
    m.cylinder(mf, cxx, cyy, 1.5, zh, zh + 1.4, n=16, col=D.hexl("#e6e2d6"), r1=1.9)                       # white head (cone out)
    m.cylinder(mf, cxx, cyy, 1.9, zh + 1.4, HC - 1.5, n=16, col=D.hexl("#ece8dc"), r1=1.3)               # white drum, tapering
    m.cylinder(mf, cxx, cyy, 1.3, HC - 1.5, HC, n=16, col=D.hexl("#ece8dc"), cap=mf, capcol=D.hexl("#303030"))
    for k in range(16):                                                                                # steel cage ring around the head
        aa = 2 * math.pi * k / 16; m.cylinder(mf, cxx + math.cos(aa) * 3.4, cyy + math.sin(aa) * 3.4, 0.07, zh + 1.2, zh + 5.2, n=4, col=D.hexl("#3a3d3f"))
    for zz in (zh + 1.2, zh + 5.1): m.cylinder(mf, cxx, cyy, 3.45, zz, zz + 0.12, n=16, col=D.hexl("#3a3d3f"), r1=3.45)
    rng = np.random.default_rng(21)
    N1, N2 = bid("ID_602FD2FE"), bid("ID_8701CE1D")
    neubau(m, mg, mf, N1, ox, oy, rng, D.hexl("#a8a69e"))
    neubau(m, mg, mf, N2, ox, oy, rng, D.hexl("#9d9b94"), upper_w=1.9, pitch=3.6)
    hide = []
    for b in (A, C, N1, N2):
        fp = b["fp"]; hide += [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    finish(m, "schiffbau", "Schiffbau", ox, oy, oz, hide_union("Schiffbau", hide))


if __name__ == "__main__":
    build()
