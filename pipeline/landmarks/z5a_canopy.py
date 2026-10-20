"""Altstetterplatz (Bahnhof Altstetten Vorplatz): three bus-stop canopies of raw concrete with a planted (moss/grass) roof edge, square piers,
ad vitrines and a concrete bench underneath. Footprints from OSM building=roof / amenity=shelter (layer 1); look from Mapillary 2015 #9, #1, #2 and
Commons 'Z_rich_Altstetterplatz' (research/zones/z5/area_station.md). The generic stop shelter of the build is not added here."""
import math
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z5a.json"
# (cx, cy, length, width, angle deg) from the OSM roof rectangles
ROOFS = [(-2151.5, 755.3, 32.4, 4.6, 159.4), (-2150.0, 732.1, 13.3, 2.5, 159.6), (-2164.8, 747.3, 13.3, 2.5, 159.6)]
CONC, CONC2, GREEN = (88, 84, 76, 255), (62, 60, 56, 255), (54, 76, 36, 255)   # the game lighting roughly doubles vertex colours


def build():
    _k4.setup4(); common.OVR = OVRZ
    ox, oy = ROOFS[0][0], ROOFS[0][1]; oz = ground(ox, oy)
    m = Model4("z5a_bushof"); mf = m.mat("flat", solid(W4))
    for cx, cy, L, W, ang in ROOFS:
        a = math.radians(ang); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
        lx, ly = cx - ox, cy - oy; gz = ground(cx, cy) - oz
        z0, z1 = gz + 3.0, gz + 3.45
        m.box(mf, lx, ly, L, W, z0, z1, rot=a, col=CONC)
        m.box(mf, lx, ly, L - 0.5, W - 0.5, z1, z1 + 0.3, rot=a, col=GREEN)          # planted roof
        m.box(mf, lx, ly, L, W, z0 - 0.12, z0, rot=a, col=CONC2)                    # darker underside rib
        n = max(2, int(L // 6.5) + 1)
        for i in range(n):
            t = (i / (n - 1) - 0.5) * (L - 1.4)
            px, py = lx + ux * t, ly + uy * t
            m.box(mf, px, py, 0.45, 0.8, gz, z0, rot=a, col=CONC)                    # pier
            if i < n - 1 and L > 20:
                qx, qy = px + ux * (L - 1.4) / (n - 1) / 2 + nx * (W / 2 - 0.5), py + uy * (L - 1.4) / (n - 1) / 2 + ny * (W / 2 - 0.5)
                m.box(mf, qx, qy, 3.2, 0.12, gz + 0.1, gz + 2.3, rot=a, col=(128, 138, 142, 255))    # glass / vitrine screen on the back side
                m.box(mf, qx - nx * 0.5, qy - ny * 0.5, 2.8, 0.5, gz, gz + 0.5, rot=a, col=(74, 72, 68, 255))   # bench
    sinfo(m, "z5a_bushof")
    finish(m, "z5a_bushof", "Altstetterplatz Bushof-Dach", ox, oy, oz, [])


if __name__ == "__main__":
    build()
