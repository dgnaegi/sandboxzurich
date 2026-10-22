"""Limmatplatz tram stop: the round central pavilion (Rundkiosk / waiting room, OSM Limmatplatz 3, swissBUILDINGS3D ID_9182AA18, 10 m round).
Photos (research/zones/zone2_cam_photos.json: Mapillary 1494303894797579, 1318695799607049, 696920982278023, Commons Migros_Hochhaus 8510/8513, Panoramax a8247b07):
a low drum (~3 m) under the flat concrete canopy, dark steel frames, yellow-green glass panels, some dark doors/closed panels, concrete plinth.
The 3D-data volume is 6.6 m high (reaches through the canopy in the game), so it is hidden and replaced by a 3.0 m drum (R 3.4, moved 5 m east so it does not overlap the generic book-kiosk scene at (1117.1, 69.7), see ticket Z2c-1). Canopy slabs stay in
places_detail_limmatplatz.json. Registers into overrides/landmarks_z2c.json. Usage: python z2c_kiosk.py"""
import math
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRZ = ROOT / "pipeline" / "overrides" / "landmarks_z2c.json"
CX, CY = 1127.8, 65.6   # second (eastern) pavilion; the 9182AA footprint centre is (1122.9, 66.9), the generic book kiosk sits at (1117.1, 69.7)
R, H = 3.4, 3.05   # canopy underside in places_detail_limmatplatz is 3.4 - 0.3 = 3.1 m above the platform
CONC, DARK, GLASS, GLOW, DOOR, POST = (96, 94, 88, 255), (30, 32, 32, 255), (84, 90, 62, 255), (112, 118, 74, 255), (52, 56, 58, 255), (92, 66, 52, 255)


def build():
    _k4.OVR4 = OVRZ; _k4.setup4(); common.OVR = OVRZ
    name, title = "z2c_rundkiosk", "Limmatplatz Rundkiosk (Tramhaltestelle)"
    oz = ground(CX, CY)
    m = Model4(name); mf = m.mat("flat", solid(W4))
    N = 18
    def facet(i, z0, z1, col, r=R):
        a0, a1 = 2 * math.pi * i / N, 2 * math.pi * (i + 1) / N
        m.quad(mf, [(r * math.cos(a0), r * math.sin(a0), z0), (r * math.cos(a1), r * math.sin(a1), z0), (r * math.cos(a1), r * math.sin(a1), z1), (r * math.cos(a0), r * math.sin(a0), z1)], col=col)
    kinds = ["glass", "glass", "glass", "door", "glass", "glass", "post", "glass", "glass"] * 2   # waiting-room glass, door, kiosk panel
    for i in range(N):
        k = kinds[i]
        facet(i, 0.0, 0.45, CONC)                               # plinth
        facet(i, 0.45, 2.55, {"glass": GLASS, "door": DOOR, "post": POST}[k])
        if k == "glass":
            facet(i, 0.9, 2.3, GLOW, r=R + 0.02)                # lit glass pane inside the frame
        facet(i, 2.55, H, CONC)                                 # fascia
        a = 2 * math.pi * i / N                                 # dark frame post at each facet edge
        m.box(mf, (R + 0.03) * math.cos(a), (R + 0.03) * math.sin(a), 0.14, 0.14, 0.45, 2.55, rot=a, col=DARK)
    for i in range(N):
        a0, a1 = 2 * math.pi * i / N, 2 * math.pi * (i + 1) / N
        m.tri(mf, [(0, 0, H), (R * math.cos(a0), R * math.sin(a0), H), (R * math.cos(a1), R * math.sin(a1), H)], col=CONC)
    sinfo(m, name)
    hide = hide_points([bid("ID_9182AA18")["fp"]])
    finish(m, name, title, CX, CY, oz, hide)


if __name__ == "__main__":
    build()
