"""KVA Josefstrasse chimney (90 m, white concrete shaft with three red bands + crown). Overlays the swissBUILDINGS3D spike (no hide)."""
from common import *
from lm import *


def build():
    ox, oy = 433.5, 291.7; oz = ground(ox, oy)
    m = Model("kva"); mf = m.mat("flat", solid((255, 255, 255, 255)))
    W, R, G = hexc("#ecebe6"), hexc("#c4322a"), hexc("#d7d5cf")
    z, H = -6.0, 90.5
    r_at = lambda zz: 3.9 - 1.2 * (zz + 6) / 96.5   # slight taper
    segs = [(-6, 20, W), (20, 62, W), (62, 66, R), (66, 70, W), (70, 74, R), (74, 78, W), (78, 82, R), (82, 87, W)]
    for z0, z1, c in segs:
        m.cylinder(mf, 0, 0, r_at(z0) + (0.04 if c == R else 0.0), z0, z1, n=14, col=c, r1=r_at(z1) + (0.04 if c == R else 0.0))
    # darker soot streaks via a thin pale/dark ring pattern low on the shaft
    m.cylinder(mf, 0, 0, r_at(30) + 0.02, 30, 34, n=14, col=hexc("#e0dfd9"))
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
