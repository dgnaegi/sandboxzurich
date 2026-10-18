"""Fountain variants V1-V6, V8, V9 (V7/V10 fall back to V2). Proportions from research/catalog/brunnen.md and Zurich street knowledge."""
import math
from model_core import Mesh


def trough(m, cell, r_out, r_in, h, seg, floor=0.0, water=True, base=None, rimcell=None):
    fl = floor or h * 0.35
    prof = [(r_out, 0.0), (r_out, h)]
    m.lathe(cell, prof, seg, smooth=False)
    m.lathe(rimcell or cell, [(r_out, h), (r_in, h)], seg, smooth=False)
    m.lathe(cell, [(r_in, h), (r_in, fl), (0.01, fl)], seg, smooth=False)
    if water: m.lathe("water", [(r_in * 0.98, h - 0.07), (0.0, h - 0.07)], seg, smooth=False)


def jet(m, x, y0, z, height, reach, n_arcs=4, cell="jet", w=0.03, steps=5):
    for a in range(n_arcs):
        ang = a * 2 * math.pi / n_arcs
        pts = []
        for i in range(steps + 1):
            t = i / steps; r = reach * t
            pts.append((x + r * math.cos(ang), y0 + height * (1 - (2 * t - 1) ** 2) * 1.0 - 0.0 * t, z - r * math.sin(ang)))
        m.ribbon(cell, pts, w, twoplanes=False)


def v1():  # Saeulenbrunnen: octagonal granite trough, column with capital, spouts into trough
    m = Mesh("V1")
    trough(m, "granite", 0.95, 0.80, 0.80, 8, floor=0.30, rimcell="kalk")
    m.lathe("granite", [(0.55, 0.0), (0.55, 0.14), (0.22, 0.14)], 8, smooth=False)         # plinth inside the trough
    m.lathe("sandstein", [(0.20, 0.14), (0.17, 0.30), (0.17, 1.30), (0.24, 1.36), (0.24, 1.50), (0.15, 1.56), (0.0, 1.78)], 8, smooth=False)  # column + capital + cap
    for a in range(4):
        an = a * math.pi / 2 + math.pi / 4; m.box("bronze", (0.22 * math.cos(an), 1.05, -0.22 * math.sin(an)), (0.05, 0.05, 0.14), ry=an + math.pi / 2)
    jet(m, 0, 1.0, 0, 0.12, 0.42, 4, w=0.025, steps=4)
    return m


def v2():  # round granite trough, short pipe, jet (also fallback for V7/V10)
    m = Mesh("V2")
    trough(m, "granite", 1.05, 0.88, 0.55, 16, floor=0.20)
    m.box("granite", (0, 0.65, -0.72), (0.30, 1.10, 0.30))            # rear stele (Brunnenstock) with pipe
    m.box("granite", (0, 1.24, -0.72), (0.40, 0.10, 0.40))
    m.box("bronze", (0, 0.92, -0.55), (0.06, 0.06, 0.18))
    jet(m, 0, 0.9, -0.45, 0.10, 0.35, 1, w=0.04, steps=4)
    m.ribbon("jet", [(0, 0.90, -0.46), (0, 0.80, -0.30), (0, 0.55, -0.22)], 0.04, False)
    return m


def v3():  # Bronze bowl on stem
    m = Mesh("V3")
    m.lathe("granite", [(0.50, 0.0), (0.50, 0.10), (0.25, 0.10), (0.25, 0.14)], 12)
    m.lathe("bronze", [(0.12, 0.14), (0.09, 0.30), (0.09, 0.55), (0.20, 0.62), (0.55, 0.78), (0.62, 0.92), (0.58, 0.92), (0.50, 0.80), (0.0, 0.70)], 14)
    m.lathe("bronze_hi", [(0.62, 0.92), (0.58, 0.92)], 14)
    m.lathe("water", [(0.52, 0.84), (0.0, 0.84)], 14)
    m.lathe("bronze", [(0.05, 0.70), (0.05, 1.10), (0.0, 1.16)], 8)
    jet(m, 0, 1.05, 0, 0.10, 0.30, 4, w=0.025, steps=4)
    return m


def v4():  # Concrete basin with central fountain
    m = Mesh("V4")
    trough(m, "concrete", 1.70, 1.50, 0.42, 20, floor=0.12)
    m.lathe("concrete", [(0.35, 0.12), (0.30, 0.30), (0.30, 0.55), (0.0, 0.55)], 10)
    m.lathe("water", [(0.30, 0.55), (0.0, 0.55)], 10)
    jet(m, 0, 0.55, 0, 0.55, 0.9, 6, w=0.04, steps=6)
    m.lathe("jet", [(0.03, 0.55), (0.03, 1.1), (0.0, 1.2)], 5)
    return m


def v5():  # flat Kunststein dish with spout at the rim
    m = Mesh("V5")
    trough(m, "kunststein", 0.70, 0.58, 0.32, 14, floor=0.12)
    m.box("kunststein", (0, 0.5, -0.62), (0.30, 1.0, 0.30))
    m.box("bronze", (0, 0.78, -0.43), (0.05, 0.05, 0.16))
    m.ribbon("jet", [(0, 0.78, -0.40), (0, 0.55, -0.30), (0, 0.22, -0.18)], 0.035, False)
    return m


def v6():  # Figurenbrunnen: bronze figure on sandstone plinth over a trough
    m = Mesh("V6")
    trough(m, "granite", 1.10, 0.95, 0.55, 12, floor=0.20)
    m.box("sandstein", (0, 0.70, 0), (0.60, 1.40, 0.60))
    m.box("sandstein", (0, 1.45, 0), (0.78, 0.10, 0.78))
    m.lathe("bronze", [(0.18, 1.50), (0.20, 1.80), (0.14, 2.30), (0.17, 2.55), (0.10, 2.62), (0.0, 2.62)], 10)       # body
    m.lathe("bronze", [(0.0, 2.58), (0.10, 2.66), (0.12, 2.78), (0.08, 2.92), (0.0, 2.97)], 8)          # head
    m.box("bronze", (0.24, 2.35, 0.0), (0.10, 0.60, 0.10), ry=0.0)  # raised arm
    m.box("bronze", (-0.20, 2.10, 0.12), (0.09, 0.50, 0.09))
    m.box("bronze_hi", (0, 0.95, 0.31), (0.06, 0.06, 0.10))
    m.ribbon("jet", [(0, 0.95, 0.34), (0, 0.80, 0.50), (0, 0.50, 0.62)], 0.04, False)
    return m


def v8():  # Notwasserbrunnen: cast-iron column with open bowl and pump lever
    m = Mesh("V8")
    m.lathe("iron", [(0.30, 0.0), (0.30, 0.10), (0.18, 0.16), (0.12, 0.30), (0.12, 0.95), (0.16, 1.02), (0.16, 1.10), (0.12, 1.14), (0.0, 1.30)], 10)
    m.lathe("iron", [(0.34, 0.45), (0.38, 0.62), (0.34, 0.64), (0.28, 0.50)], 10)       # shallow bowl at mid height
    m.lathe("water", [(0.30, 0.60), (0.0, 0.60)], 10)
    m.box("iron", (0.0, 0.92, 0.17), (0.05, 0.05, 0.22))
    m.box("iron", (0.0, 1.10, 0.0), (0.05, 0.05, 0.60), ry=0.0)       # pump lever
    m.box("bronze_hi", (0, 0.80, 0.14), (0.14, 0.10, 0.04))
    return m


def v9():  # wooden trough: staved barrel-like tub, iron bands, pipe
    m = Mesh("V9")
    m.lathe("wood", [(0.50, 0.0), (0.52, 0.30), (0.50, 0.58), (0.0, 0.58)][:3], 12, smooth=False)
    m.lathe("wood_dark", [(0.50, 0.58), (0.42, 0.58), (0.42, 0.14), (0.0, 0.14)], 12, smooth=False)
    m.lathe("water", [(0.42, 0.50), (0.0, 0.50)], 12)
    for y in (0.12, 0.46): m.lathe("iron", [(0.505 + 0.01 * (y < 0.3), y - 0.02), (0.515, y + 0.02)], 12)
    m.box("wood", (0, 0.50, -0.62), (0.18, 1.00, 0.18))
    m.box("bronze", (0, 0.88, -0.48), (0.05, 0.05, 0.16))
    m.ribbon("jet", [(0, 0.88, -0.42), (0, 0.78, -0.30), (0, 0.50, -0.22)], 0.035, False)
    return m


BRUNNEN = {"V1": (v1, "Saeulenbrunnen (Granittrog achteckig, Saeule)"), "V2": (v2, "Trogbrunnen Stein"), "V3": (v3, "Bronzeguss-Schale"),
           "V4": (v4, "Betonbassin mit Fontaene"), "V5": (v5, "Kunststein-Schale"), "V6": (v6, "Figurenbrunnen"), "V8": (v8, "Notwasserbrunnen"), "V9": (v9, "Holztrog")}
