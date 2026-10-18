"""Stop equipment H1-H7 plus masts. Local frame: shelter long axis = x, open side faces +z. Sizes: research/catalog/haltestellen.md + stops_equip.json."""
import math
from model_core import Mesh


def two_sided(m, cell, p):
    m.quad(cell, p); m.quad(cell, [p[1], p[0], p[3], p[2]])


def shelter_new(L=7.0, D=1.6):
    """H1: VBZ glass shelter. Dark steel posts, glass back + side wall, lightly sloped roof of tinted glass in steel frame, advert case at one end."""
    m = Mesh("H1"); H0, H1 = 2.55, 2.40; n = max(2, int(round(L / 2.3))); st = "steel_dark"
    pz = -D / 2 + 0.05; x0 = -L / 2
    for i in range(n + 1):
        x = x0 + 0.05 + i * (L - 0.10) / n
        m.box(st, (x, H0 / 2, pz), (0.08, H0, 0.08))
        if i in (0, n): m.box(st, (x, (H1 - 0.1) / 2, D / 2 - 0.05), (0.07, H1 - 0.1, 0.07))
    two_sided(m, "roofglass", [(-L / 2, H1, D / 2 + 0.15), (L / 2, H1, D / 2 + 0.15), (L / 2, H0 + 0.05, -D / 2), (-L / 2, H0 + 0.05, -D / 2)])
    m.box(st, (0, H0 + 0.04, -D / 2), (L, 0.10, 0.08))
    m.box(st, (0, H1 - 0.04, D / 2 + 0.15), (L, 0.08, 0.06))
    for x in (-L / 2 + 0.02, L / 2 - 0.02):
        m.box(st, (x, (H0 + H1) / 2 + 0.02, 0.05), (0.06, 0.08, D + 0.2))
    gw = L - (1.4 if L > 4 else 0.0)
    two_sided(m, "glass_green", [(x0, 0.25, pz), (x0 + gw, 0.25, pz), (x0 + gw, 2.25, pz), (x0, 2.25, pz)])
    m.box(st, (x0 + gw / 2, 0.20, pz), (gw, 0.10, 0.06)); m.box(st, (x0 + gw / 2, 2.30, pz), (gw, 0.08, 0.06))
    for k in range(1, int(gw / 1.15) + 1): m.box(st, (x0 + k * 1.15, 1.25, pz), (0.04, 2.0, 0.04))
    if L > 4:
        cx = L / 2 - 0.70
        m.box(st, (cx, 1.25, pz + 0.04), (1.20, 2.20, 0.12), front="poster_a", back="poster_b")
    two_sided(m, "glass_green", [(x0 + 0.01, 0.25, D / 2 - 0.05), (x0 + 0.01, 0.25, pz), (x0 + 0.01, 2.25, pz), (x0 + 0.01, 2.25, D / 2 - 0.05)])
    m.box("steel_grey", (0, 0.02, 0), (L, 0.04, D))
    return m


def shelter_old(L=6.0, D=1.5):
    """H2: older shelter: flat grey roof with fascia, clear glass, steel-grey frame, side panels."""
    m = Mesh("H2"); H = 2.45; st = "steel_grey"; pz = -D / 2 + 0.05
    m.box("concrete", (0, H, 0.05), (L + 0.2, 0.14, D + 0.5))
    m.box(st, (0, H - 0.12, 0.05), (L + 0.1, 0.06, D + 0.4))
    n = max(2, int(round(L / 2.0)))
    for i in range(n + 1):
        x = -L / 2 + i * L / n
        m.box(st, (x, H / 2, pz), (0.09, H, 0.09))
        if i in (0, n): m.box(st, (x, H / 2, D / 2 - 0.05), (0.09, H, 0.09))
    two_sided(m, "glass", [(-L / 2, 0.30, pz), (L / 2, 0.30, pz), (L / 2, H - 0.1, pz), (-L / 2, H - 0.1, pz)])
    m.box(st, (0, 0.26, pz), (L, 0.10, 0.08))
    for sx in (-L / 2, L / 2):
        two_sided(m, "glass", [(sx, 0.30, pz), (sx, 0.30, D / 2 - 0.05), (sx, H - 0.1, D / 2 - 0.05), (sx, H - 0.1, pz)])
    m.box(st, (-L / 2 + 0.9, 1.30, pz + 0.06), (1.0, 1.7, 0.06), front="poster_b", back="steel_dark")
    return m


def ticket():
    m = Mesh("H3")
    m.box("steel_dark", (0, 0.04, 0), (0.50, 0.08, 0.40))
    m.box("steel_dark", (0, 0.70, 0), (0.46, 1.25, 0.34), front="ticket")
    m.quad("steel_dark", [(-0.23, 1.325, 0.17), (0.23, 1.325, 0.17), (0.23, 1.40, -0.12), (-0.23, 1.40, -0.12)])
    m.box("yellow", (0, 1.34, 0.18), (0.40, 0.03, 0.02))
    return m


def screen_wall():
    m = Mesh("H4"); m.box("steel_dark", (0, 0, 0), (0.64, 0.44, 0.10), front="screen"); return m


def screen_ceiling():
    m = Mesh("H5")
    m.box("steel_dark", (0, -0.05, 0), (0.30, 0.04, 0.10))
    m.box("steel_dark", (-0.22, -0.20, 0), (0.025, 0.30, 0.025)); m.box("steel_dark", (0.22, -0.20, 0), (0.025, 0.30, 0.025))
    m.box("steel_dark", (0, -0.55, 0), (0.64, 0.44, 0.10), front="screen", back="screen")
    return m


def bench(L, name):
    m = Mesh(name); d = 0.42
    for sx in (-L / 2 + 0.15, L / 2 - 0.15):
        m.box("steel_dark", (sx, 0.22, 0), (0.05, 0.44, d)); m.box("steel_dark", (sx, 0.04, 0), (0.05, 0.05, d + 0.1))
    for k in range(3):
        m.box("bank_wood", (0, 0.45, -d / 2 + 0.07 + k * 0.14), (L, 0.045, 0.11))
    return m


def mast(kind):
    """Stop mast with VBZ flag, origin at foot, flag faces +z and -z."""
    m = Mesh("mast_" + kind); cell = "fahne_" + kind
    m.lathe("steel_dark", [(0.18, 0.0), (0.18, 0.06), (0.05, 0.08), (0.05, 3.55), (0.0, 3.58)], 8)
    m.box("steel_dark", (0.12, 3.20, 0.0), (0.24, 0.03, 0.04))
    m.box("white", (0.30, 2.85, 0.0), (0.46, 0.80, 0.025), front=cell, back=cell)
    return m


STOPS = {"H1": (lambda: shelter_new(7.0, 1.6), "VBZ-Glaswartehalle Standard 7 m"),
         "H2": (lambda: shelter_old(6.0, 1.5), "aeltere Wartehalle 6 m"),
         "H3": (ticket, "Ticketautomat Typ 20"), "H4": (screen_wall, "Anzeige Wand"), "H5": (screen_ceiling, "Anzeige Decke (Ursprung oben)"),
         "H6": (lambda: bench(1.8, "H6"), "Bank kurz 1.8 m"), "H7": (lambda: bench(3.6, "H7"), "Bank lang 3.6 m"),
         "mast_tram": (lambda: mast("tram"), "Haltestellenmast Tram"), "mast_bus": (lambda: mast("bus"), "Haltestellenmast Bus")}
