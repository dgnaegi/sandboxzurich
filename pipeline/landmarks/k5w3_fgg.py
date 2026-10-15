"""Frau Gerolds Garten (Geroldstrasse 23): dark container-clad bar/kitchen blocks (3 levels), glazed ground floors, string lights and
bunting across the gravel yard. Photos: research/v3/frau_gerolds_garten.md."""
import math
from k5w3_kit import *
import k5w3_towers as T


def extra(m, mw, mg, mf, ox, oy, oz, ids):
    # string lights (emissive atlas strip: warm yellow) and bunting triangles between posts across the yard
    lines = [((190 - ox, 144 - oy, 5.2), (240 - ox, 152 - oy, 5.0)), ((196 - ox, 166 - oy, 4.6), (236 - ox, 160 - oy, 4.8)),
             ((194 - ox, 154 - oy, 5.6), (238 - ox, 156 - oy, 5.4))]
    cols = ["#d9362c", "#f0c02a", "#2f7fb8", "#3f9a4e", "#e8e4da", "#d4772a"]
    for li, (a, b) in enumerate(lines):
        N = 24
        for i in range(N):
            f = i / N; f2 = (i + 1) / N
            def P(ff):
                sag = 1.2 * 4 * ff * (1 - ff)
                return (a[0] + (b[0] - a[0]) * ff, a[1] + (b[1] - a[1]) * ff, a[2] + (b[2] - a[2]) * ff - sag)
            p0, p1 = P(f), P(f2)
            if li < 2:   # bulbs
                m.box(mf, p0[0], p0[1], 0.16, 0.16, p0[2] - 0.08, p0[2] + 0.08, col=hexl("#ffe9b0"))
            else:        # bunting flags hanging
                mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
                m.tri(mf, [p0, p1, (mid[0], mid[1], p0[2] - 0.55)], col=hexl(cols[i % 6]))
                m.tri(mf, [p1, p0, (mid[0], mid[1], p0[2] - 0.55)], col=hexl(cols[i % 6]))
    for px, py in [(190, 144), (240, 152), (196, 166), (236, 160), (194, 154), (238, 156)]:
        m.box(mf, px - ox, py - oy, 0.14, 0.14, 0, 5.4, col=hexl("#5a4a3a"))
    # wooden terrace deck
    m.box(mf, 214 - ox, 156 - oy, 14, 8, 0.0, 0.25, col=hexl("#8a6a48"))


def build():
    sign = text_painter([(0, 1024, "BAR", "#2a1c10", "#f2c97a", (255, 210, 130))], size=26)
    T.block("frau_gerolds_garten", "Frau Gerolds Garten", ["ID_6999753E", "ID_38727667", "ID_B9E3EE20"], wall="#3a3d3f", wall_tex=tex_corrugated("#3d4042", n=20), frame="#222426",
            glass="#3a4048", cols=2, rows=2, bay=3.0, hole_w=2.0, hole_h=1.6, sill=0.8, fh=2.9, eg_h=3.0, tol=2.0, minA=20, corn="#6b4a30", roof="#5a5c5e", sign=sign, deep_z=4.0,
            extra=extra, seed=22, lit=0.55)


if __name__ == "__main__":
    build()
