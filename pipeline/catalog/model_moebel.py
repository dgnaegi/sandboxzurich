"""Street furniture: M1 lamp (mast with arm), M1b rope lamp (pendant), M2 kiosk, M3 VBZ poster stele."""
from model_core import Mesh


def lamp():
    m = Mesh("M1")
    m.lathe("steel_dark", [(0.14, 0.0), (0.14, 0.10), (0.08, 0.14), (0.06, 6.2), (0.05, 6.5)], 8)
    m.box("steel_dark", (0.45, 6.45, 0), (0.95, 0.06, 0.06))
    m.box("steel_dark", (0.95, 6.40, 0), (0.60, 0.12, 0.26))
    m.box("lampglass", (0.95, 6.33, 0), (0.54, 0.03, 0.22), top=False, bottom=True)
    return m


def rope_lamp():
    m = Mesh("M1b")
    m.box("steel_dark", (0, -0.02, 0), (1.6, 0.03, 0.03))
    m.box("steel_dark", (0, -0.17, 0), (0.02, 0.28, 0.02))
    m.lathe("steel_dark", [(0.04, -0.30), (0.04, -0.36), (0.28, -0.55), (0.30, -0.60)], 12)
    m.lathe("lampglass", [(0.30, -0.60), (0.20, -0.62), (0.0, -0.62)], 12)
    return m


def kiosk():
    m = Mesh("M2"); w, d, h = 2.6, 2.4, 2.65
    m.box("kiosk_body", (0, h / 2, 0), (w, h, d), front="kiosk_window")
    m.box("steel_dark", (0, h + 0.07, 0), (w + 0.25, 0.14, d + 0.25))
    m.box("steel_dark", (0, 0.04, 0), (w + 0.1, 0.08, d + 0.1))
    m.box("steel_grey", (0, 1.05, d / 2 + 0.12), (w - 0.2, 0.06, 0.28))
    for p in ([(-w / 2 - 0.1, 2.15, d / 2 + 0.05), (w / 2 + 0.1, 2.15, d / 2 + 0.05), (w / 2 + 0.1, 2.40, d / 2 + 0.85), (-w / 2 - 0.1, 2.40, d / 2 + 0.85)],):
        m.quad("awning", [p[3], p[2], p[1], p[0]], n=(0, 0.95, 0.3)); m.quad("awning", p, n=(0, -0.95, -0.3))
    m.box("poster_b", (w / 2 + 0.03, 1.6, -0.2), (0.04, 1.0, 0.7))
    return m


def poster_stele():
    m = Mesh("M3")
    m.box("steel_dark", (0, 0.06, 0), (1.3, 0.12, 0.45))
    m.box("steel_dark", (0, 1.15, 0), (1.2, 2.10, 0.18), front="poster_a", back="poster_b")
    m.box("steel_dark", (0, 2.25, 0), (1.30, 0.10, 0.28))
    return m


MOEBEL = {"M1": (lamp, "Mastleuchte"), "M1b": (rope_lamp, "Seilleuchte (Ursprung an Aufhaengung)"), "M2": (kiosk, "Kiosk"), "M3": (poster_stele, "Plakatstelle VBZ")}
