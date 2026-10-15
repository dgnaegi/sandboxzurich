"""KVA Josefstrasse chimney (90 m, white concrete shaft with three red bands + crown). Overlays the swissBUILDINGS3D spike (no hide)."""
from common import *
from lm import *


def build():
    ox, oy = 433.5, 291.7; oz = ground(ox, oy)
    m = Model("kva"); mf = m.mat("flat", solid((255, 255, 255, 255)))
    W, R, G = hexc("#ecebe6"), hexc("#c4322a"), hexc("#d7d5cf")
    z, H = -6.0, 90.5
    r_at = lambda zz: 3.9 - 1.2 * (zz + 6) / 96.5   # slight taper
    segs = [(-6, 20, hexc("#dcdcd6")), (20, 45, W), (45, 62, hexc("#f1f1ed")), (62, 87, hexc("#f4f4f1"))]
    for z0, z1, c in segs:
        m.cylinder(mf, 0, 0, r_at(z0) + (0.04 if c == R else 0.0), z0, z1, n=14, col=c, r1=r_at(z1) + (0.04 if c == R else 0.0))
    # darker soot streaks via a thin pale/dark ring pattern low on the shaft
    m.cylinder(mf, 0, 0, r_at(30) + 0.02, 30, 34, n=14, col=hexc("#e0dfd9"))
    # form-work joints (slight tone rings every ~6 m) and service platforms
    for zz in range(14, 86, 6): m.cylinder(mf, 0, 0, r_at(zz) + 0.03, zz, zz + 0.25, n=14, col=hexc("#d4d3cc"), r1=r_at(zz) + 0.03)
    for zz in (40, 64): m.cylinder(mf, 0, 0, r_at(zz) + 0.9, zz, zz + 0.12, n=14, col=hexc("#4a4d4f"), r1=r_at(zz) + 0.9)
    # crown: widened ring, platform, rail
    m.cylinder(mf, 0, 0, 3.15, 87, 88.6, n=14, col=G, r1=3.45)
    m.cylinder(mf, 0, 0, 3.45, 88.6, 90.5, n=14, col=G, cap=mf, capcol=hexc("#8c8a85"))
    m.cylinder(mf, 0, 0, 2.5, 90.5, 91.2, n=14, col=hexc("#3a3a3a"), cap=mf, capcol=hexc("#222222"))
    # peregrine falcon nest box + service ladder strip
    m.box(mf, 3.5, 0, 1.0, 1.2, 80, 81.2, col=hexc("#8a6a3d"))
    m.quad(mf, [(r_at(10), -0.3, 0), (r_at(10) + 0.12, -0.3, 0), (r_at(10) + 0.12, -0.3, 82), (r_at(10), -0.3, 82)][::1], col=hexc("#4b4b4b")) if False else None
    finish(m, "kva_chimney", "KVA-Kamin Josefstrasse", ox, oy, oz, [])


if __name__ == "__main__":
    build()
