"""Bullingerplatz Tellerbrunnen basin (Zone 3, Mapillary 2086251138419971, 1186383535673317, 1444815882778112, Commons 'Bullingerplatz Zuerich 2018'):
the generic `tellerbrunnen` in places_detail hides its water under a solid grey disc. This landmark draws the real basin on top: dark granite rim ring
(~0.5 m wide, 0.55 m high), shallow tan water/basin floor just above the generic disc, thin pale stone ring in the cobbles. Centre = generic fountain.
Registers into overrides/landmarks_z3b.json. Usage: python z3b_fountain.py"""
import math
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z3b.json"
CX, CY = -37.1, -497.2   # places_detail_bullingerplatz.json: centre (-41,-495.6) + tellerbrunnen offset (3.9,-1.6)


def build():
    _k4.OVR4 = OVRZ; _k4.setup4()
    name, title = "z3b_bullinger_brunnen", "Bullingerplatz Brunnenbecken"
    m = Model4(name); mf = m.mat("flat", solid(W4))
    oz = ground(CX, CY)
    R_OUT, R_IN = 6.55, 5.9
    def disc(r, z, col, n=64): 
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            m.tri(mf, [(0, 0, z), (r * math.cos(a0), r * math.sin(a0), z), (r * math.cos(a1), r * math.sin(a1), z)], col=col)
    def ring(r0, r1, z, col, n=64):
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            m.quad(mf, [(r0 * math.cos(a0), r0 * math.sin(a0), z), (r1 * math.cos(a0), r1 * math.sin(a0), z), (r1 * math.cos(a1), r1 * math.sin(a1), z), (r0 * math.cos(a1), r0 * math.sin(a1), z)], col=col)
    m.cylinder(mf, 0, 0, R_OUT, -0.1, 0.55, n=64, col=hexl("#4f4e4a")); ring(R_IN, R_OUT, 0.55, hexl("#5b5a56"))
    m.cylinder(mf, 0, 0, R_IN, 0.30, 0.44, n=64, col=hexl("#8f866f")); disc(R_IN, 0.44, hexl("#b3a88c"))
    # upper dish (generic one has a blue water top): pale stone plate, Ø ~5 m, rim 0.2 m, water just above the generic top (1.16)
    m.cylinder(mf, 0, 0, 2.65, 0.95, 1.25, n=40, col=hexl("#cbbf9f")); ring(2.25, 2.65, 1.25, hexl("#d6ccb0"), 40)
    m.cylinder(mf, 0, 0, 2.25, 1.0, 1.21, n=40, col=hexl("#cbbf9f")); disc(2.25, 1.21, hexl("#cfc8b4"), 40)
    # pale stone ring set into the cobbles (thin band, r 8.0-8.4)
    n = 64
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p = [(8.0 * math.cos(a0), 8.0 * math.sin(a0), 0.035), (8.4 * math.cos(a0), 8.4 * math.sin(a0), 0.035), (8.4 * math.cos(a1), 8.4 * math.sin(a1), 0.035), (8.0 * math.cos(a1), 8.0 * math.sin(a1), 0.035)]
        m.quad(mf, p, col=hexl("#a8a49c"))
    sinfo(m, name)
    finish(m, name, title, CX, CY, oz, [])


if __name__ == "__main__":
    build()
