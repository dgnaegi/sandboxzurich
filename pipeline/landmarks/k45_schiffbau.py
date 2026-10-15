"""Schiffbau (Escher Wyss ship hall 1892, now Schauspielhaus): brick hall with tall arched windows + octagonal brick chimney (45 m)."""
import math
from PIL import Image, ImageDraw
from common import *
from lm import *
from shapely.geometry import Polygon

BR = hexc("#c2a05e")


def brick_painter(d, de, x, y, w, h, rng, on, ix, iy):
    d.rectangle([x, y, x + w, y + h], fill=BR)
    for k in range(0, h, 5):  # brick courses
        d.line([x, y + k, x + w, y + k], fill=shade(BR, 0.84))
        if k % 10 == 0:
            for j in range(0, w, 14): d.line([x + j + 7 * ((k // 5) % 2), y + k, x + j + 7 * ((k // 5) % 2), y + k + 5], fill=shade(BR, 0.88))
    for _ in range(40):  # brick tone noise
        bx, by = x + int(rng.random() * w), y + int(rng.random() * h); f = 0.85 + rng.random() * 0.3
        d.rectangle([bx, by, bx + 12, by + 4], fill=shade(BR, f))
    pil = int(w * 0.09)
    d.rectangle([x, y, x + pil, y + h], fill=shade(BR, 0.75)); d.rectangle([x + w - pil, y, x + w, y + h], fill=shade(BR, 0.75))
    ww = int(w * 0.62); x0 = x + (w - ww) // 2; spring = y + int(h * 0.34)
    # tall arched steel window with glazing bars
    d.pieslice([x0 - 5, spring - ww // 2 - 5, x0 + ww + 5, spring + ww // 2 + 5], 180, 360, fill=hexc("#d9c9a6"))
    d.rectangle([x0 - 5, spring, x0 + ww + 5, y + int(h * 0.84)], fill=hexc("#e4dcc4"))
    G = hexc("#33454f")
    d.pieslice([x0, spring - ww // 2, x0 + ww, spring + ww // 2], 180, 360, fill=G)
    d.rectangle([x0, spring, x0 + ww, y + int(h * 0.82)], fill=G)
    bar = hexc("#1b2024")
    for k in range(1, 4): d.line([x0 + ww * k // 4, spring - ww // 2 + (6 if k != 2 else 0), x0 + ww * k // 4, y + int(h * 0.82)], fill=bar, width=2)
    for yy in range(spring - ww // 4, y + int(h * 0.82), int(h * 0.09)): d.line([x0, yy, x0 + ww, yy], fill=bar, width=2)
    d.arc([x0, spring - ww // 2, x0 + ww, spring + ww // 2], 180, 360, fill=bar, width=3)
    d.rectangle([x, y + int(h * 0.84), x + w, y + h], fill=hexc("#9d9a90"))
    for yy in range(y + int(h * 0.84), y + h, 9): d.line([x, yy, x + w, yy], fill=hexc("#85827a"))
    d.rectangle([x, y + int(h * 0.835), x + w, y + int(h * 0.85)], fill=hexc("#c9c4b4"))   # plinth + sill band
    d.rectangle([x, y, x + w, y + int(h * 0.025)], fill=shade(BR, 1.12))
    if on:
        de.pieslice([x0 + 2, spring - ww // 2 + 2, x0 + ww - 2, spring + ww // 2], 180, 360, fill=(255, 190, 110))
        de.rectangle([x0 + 2, spring, x0 + ww - 2, y + int(h * 0.82) - 2], fill=(255, 185, 105))
        for k in range(1, 4): de.line([x0 + ww * k // 4, spring - ww // 2, x0 + ww * k // 4, y + int(h * 0.82)], fill=(0, 0, 0), width=2)


def build():
    A = bid("ID_ECC7D96E"); C = bid("ID_39E2287D")
    P = outline(A["fp"], 0.5)
    ox, oy = round(P.centroid.x, 1), round(P.centroid.y, 1); oz = ground(ox, oy)
    Pl = localize(P, ox, oy)
    m = Model("schiffbau")
    mb = m.mat("brick", *tile(4, 1, 112, 320, brick_painter, 5, 0.3))
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    Hw = 14.2; HR = A["zmax"] - ground(P.centroid.x, P.centroid.y)
    m.extrude(mf, mf, Pl, -3, 0.0, col=hexc("#9d9a90"), roof=False)
    m.extrude(mb, mf, Pl, 0.0, Hw, mod=(20.0, Hw), roof=False, wallv0=0.0)
    rect = rect_of(Pl)
    rise = max(3.0, HR - Hw)
    gable_roof(m, mf, mb, rect, Hw, rise, hexc("#4f5a58"), (255, 255, 255, 255))
    # glazed monitor along the ridge
    (cx, cy), ux, uy, L, W = rect
    m.box(mf, cx, cy, L * 0.8, 2.2, Hw + rise, Hw + rise + 1.4, rot=math.atan2(uy, ux), col=hexc("#7f9aa5"))
    # chimney: octagonal brick shaft 45 m at the real location
    cxx, cyy = C["c"][0] - ox, C["c"][1] - oy
    gz = ground(C["c"][0], C["c"][1]) - oz
    HC = C["zmax"] - ground(*C["c"])
    for z0, z1, r0, r1, col in [(gz - 3, gz + 6, 2.4, 2.2, "#5e3226"), (gz + 6, HC - 9.0, 2.2, 1.5, "#6f3a2c")]:
        m.cylinder(mf, cxx, cyy, r0, z0, z1, n=16, col=hexc(col), r1=r1, smooth=True)
    zh = HC - 9.0
    m.cylinder(mf, cxx, cyy, 1.5, zh, zh + 1.4, n=16, col=hexc("#e6e2d6"), r1=1.9)                       # white head (cone out)
    m.cylinder(mf, cxx, cyy, 1.9, zh + 1.4, HC - 1.5, n=16, col=hexc("#ece8dc"), r1=1.3)               # white drum, tapering
    m.cylinder(mf, cxx, cyy, 1.3, HC - 1.5, HC, n=16, col=hexc("#ece8dc"), cap=mf, capcol=hexc("#303030"))
    for k in range(16):                                                                                # steel cage ring around the head
        aa = 2 * math.pi * k / 16; m.cylinder(mf, cxx + math.cos(aa) * 3.4, cyy + math.sin(aa) * 3.4, 0.07, zh + 1.2, zh + 5.2, n=4, col=hexc("#3a3d3f"))
    for zz in (zh + 1.2, zh + 5.1): m.cylinder(mf, cxx, cyy, 3.45, zz, zz + 0.12, n=16, col=hexc("#3a3d3f"), r1=3.45)
    hide = []
    for b in (A, C):
        fp = b["fp"]; hide += [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    finish(m, "schiffbau", "Schiffbau", ox, oy, oz, hide_union("Schiffbau", hide))


if __name__ == "__main__":
    build()
