"""Zuerich HB surroundings + platform furniture (agent HBX). Two GLBs, registered in overrides/landmarks_hbx.json:
  hbx_perron  : sector signs A-F, neutral departure displays, ticket machines, bins on Perrons 3-18 (the roofs/benches/lines are in hb_perron.py)
  hbx_platz   : Bahnhofplatz - Alfred-Escher-Denkmal (Kissling 1889), bicycle parking at the Suedtrakt, tram-island kerbs are in stops_equip.
Frame/size as hb_kit (d along tracks, c across). Neutral lettering, no logos, no SBB clock."""
from hb_kit import *
import hb_geom as G
import hb_props as P
import json

D_HEAD, D_END = G.PLAT_HEAD_D, -470.0
TOP = 0.98
SECT = "ABCDEF"


def atlas():
    A = SignAtlas(512, 384)
    for i, s in enumerate(SECT):
        A.add("s" + s, 64, 64, sign_text(s, "#ffffff", "#1b2f55", glow=(180, 190, 220), size=48, frame="#ffffff"))
    A.add("tkt", 96, 96, sign_text("Billette", "#e8f0f8", "#12202e", glow=(150, 180, 210), size=20, frame="#5b6f82"))
    A.add("disp", 128, 192, sign_text("Abfahrt", "#ffd25a", "#101418", glow=(150, 120, 30), size=22, frame="#3a3f45"))
    return A


def panel(m, mat, d, c0, c1, z0, z1, rect, s):
    """Two-sided-ready quad in the c-z plane at d facing s (+1/-1 along d)."""
    a, b = (c0, c1) if s > 0 else (c1, c0)
    m.quad(mat, [(d, a, z0), (d, b, z0), (d, b, z1), (d, a, z1)], uvr(rect), W)


def perron():
    m = Model("hbx_perron"); A = atlas()
    ms = m.mat("sign", *A.images(), rough=0.8); mf = m.mat("flat", Image.new("RGBA", (8, 8), (255, 255, 255, 255)))
    DARK, MET, ORANGE = hx("#2b2e32"), hx("#8d9399"), hx("#c8461c")
    for ref, (cs, cn) in G.PLATFORMS.items():
        cm = (cs + cn) / 2
        # sector boards A-F hang between roof columns (columns at multiples of 17.5 from the head), 69 m apart, visible along the platform
        for k, s in enumerate(SECT):
            d = D_HEAD - 12.0 - 17.5 * 4 * k - 8.75
            if d < D_END + 10: break
            for sg in (-1, 1): panel(m, ms, d + 0.04 * sg, cm - 0.45, cm + 0.45, TOP + 5.6, TOP + 6.5, A.rects["s" + s], sg)
            for cc in (cm - 0.35, cm + 0.35): bx(m, mf, d - 0.02, d + 0.02, cc - 0.02, cc + 0.02, TOP + 6.5, TOP + 7.6, DARK, top=False)
        # neutral departure displays (double sided) on a post, every 70 m, between columns
        for k in range(6):
            d = D_HEAD - 26.0 - 70.0 * k
            if d < D_END + 15: break
            c = cm + (1.9 if k % 2 else -1.9)
            bx(m, mf, d - 0.05, d + 0.05, c - 0.05, c + 0.05, TOP, TOP + 2.2, DARK, top=False)
            bx(m, mf, d - 0.09, d + 0.09, c - 0.4, c + 0.4, TOP + 1.6, TOP + 2.7, DARK, top=True)
            for sg in (-1, 1): panel(m, ms, d + 0.1 * sg, c - 0.36, c + 0.36, TOP + 1.65, TOP + 2.65, A.rects["disp"], sg)
        # ticket machines (neutral), head, mid and tail; screen toward the platform axis
        for k, d in enumerate((D_HEAD - 22.0, D_HEAD - 170.0, D_HEAD - 330.0)):
            c = cs + 1.3 if k % 2 == 0 else cn - 1.3
            bx(m, mf, d - 0.3, d + 0.3, c - 0.28, c + 0.28, TOP, TOP + 1.75, MET, top=True)
            sgn = 1 if c < cm else -1
            a, b = (c + 0.2, c - 0.2) if sgn > 0 else (c - 0.2, c + 0.2)   # face toward the axis (c direction); quad in the d-z plane
            cf = c + 0.285 * sgn
            m.quad(ms, [(d - 0.22, cf, TOP + 0.95), (d + 0.22, cf, TOP + 0.95), (d + 0.22, cf, TOP + 1.55), (d - 0.22, cf, TOP + 1.55)] if sgn > 0 else
                   [(d + 0.22, cf, TOP + 0.95), (d - 0.22, cf, TOP + 0.95), (d - 0.22, cf, TOP + 1.55), (d + 0.22, cf, TOP + 1.55)], uvr(A.rects["tkt"]), W)
        # bins in pairs (waste / paper), next to the benches
        for d in np.arange(D_HEAD - 36.0, D_END + 25, -38.0):
            for off, col in ((0.0, hx("#3d4a3f")), (0.5, hx("#2f3d52"))):
                bx(m, mf, d + off - 0.22, d + off + 0.22, cm + 1.55 - 0.22, cm + 1.55 + 0.22, TOP, TOP + 0.95, col, top=True, colt=hx("#1d1f22"))
    info(m, "hbx_perron")
    return m


def bike(m, mf, d, c, ang_d=True, col=None):
    """Low-poly parked bicycle (frame along c): two wheels as thin boxes, frame, saddle, handlebar."""
    col = col or hx("#3b4a63")
    w = hx("#18191b")
    for dd in (-0.55, 0.55): bx(m, mf, d - 0.02, d + 0.02, c + dd - 0.33, c + dd + 0.33, 0.0, 0.66, w, top=False, sides=(1, 0, 1, 0))
    bx(m, mf, d - 0.02, d + 0.02, c - 0.5, c + 0.5, 0.35, 0.40, col, top=True)
    bx(m, mf, d - 0.02, d + 0.02, c - 0.52, c - 0.46, 0.35, 0.95, col, top=False)
    bx(m, mf, d - 0.06, d + 0.06, c + 0.5, c + 0.7, 0.93, 0.97, w, top=True)
    bx(m, mf, d - 0.15, d + 0.15, c - 0.62, c - 0.42, 0.95, 0.99, w, top=True)


def platz():
    m = Model("hbx_platz"); mf = m.mat("flat", Image.new("RGBA", (8, 8), (255, 255, 255, 255)))
    STONE, STONE2, BRONZE, RACK = hx("#a39e92"), hx("#8b867b"), hx("#4a4338"), hx("#6c7075")
    # Alfred-Escher-Brunnen (Richard Kissling, 1889; refs Commons "Alfred Escher Brunnen", "Zuerich Alfred Escher Denkmal"): round low basin r 5.5 with water,
    # reddish granite pedestal ~4.6 m, patinated bronze group (allegories) at 2.9 m, standing figure on top, two side bowls on stems.
    GREEN, GRAN, GRAN2, WATER = hx("#4d7565"), hx("#8c6f66"), hx("#a8a39a"), hx("#6f8f9a")
    d0, c0 = 48.0, -78.0
    n = 20
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0 = (d0 + 5.5 * math.cos(a0), c0 + 5.5 * math.sin(a0)); p1 = (d0 + 5.5 * math.cos(a1), c0 + 5.5 * math.sin(a1))
        q0 = (d0 + 5.1 * math.cos(a0), c0 + 5.1 * math.sin(a0)); q1 = (d0 + 5.1 * math.cos(a1), c0 + 5.1 * math.sin(a1))
        wall(m, mf, p1, p0, 0.0, 0.45, GRAN2, double=False); wall(m, mf, q0, q1, 0.1, 0.45, GRAN2)
        q(m, mf, [(p0[0], p0[1], 0.45), (p1[0], p1[1], 0.45), (q1[0], q1[1], 0.45), (q0[0], q0[1], 0.45)], GRAN2, None, (0, 0, 1))
    m.cylinder(mf, d0, c0, 5.1, 0.0, 0.3, n=20, col=WATER, cap=mf, capcol=WATER)
    bx(m, mf, d0 - 1.9, d0 + 1.9, c0 - 1.9, c0 + 1.9, 0.0, 1.0, GRAN, top=True)
    bx(m, mf, d0 - 1.3, d0 + 1.3, c0 - 1.3, c0 + 1.3, 1.0, 2.6, GRAN, top=True, colt=GRAN2)
    bx(m, mf, d0 - 1.0, d0 + 1.0, c0 - 1.0, c0 + 1.0, 2.6, 5.0, GRAN, top=True, colt=GRAN2)
    bx(m, mf, d0 - 1.15, d0 + 1.15, c0 - 1.15, c0 + 1.15, 5.0, 5.25, GRAN2, top=True)
    for k in range(4):      # bronze allegory group around the pedestal waist
        a = math.pi / 4 + k * math.pi / 2
        m.cylinder(mf, d0 + 1.15 * math.cos(a), c0 + 1.15 * math.sin(a), 0.38, 2.7, 3.8, n=8, col=GREEN, r1=0.55)
        m.cylinder(mf, d0 + 1.2 * math.cos(a), c0 + 1.2 * math.sin(a), 0.2, 3.8, 4.3, n=8, col=GREEN, r1=0.3)
    for sg in (-1, 1):      # side bowls on stems
        cc = c0 + sg * 3.3
        m.cylinder(mf, d0, cc, 0.25, 0.3, 1.1, n=8, col=GRAN)
        m.cylinder(mf, d0, cc, 1.15, 1.1, 1.3, n=14, col=GRAN2, r1=0.5)
    m.cylinder(mf, d0, c0, 0.45, 5.25, 6.4, n=10, col=GREEN, r1=0.38)
    m.cylinder(mf, d0, c0, 0.38, 6.4, 7.2, n=10, col=GREEN, r1=0.47)
    m.cylinder(mf, d0, c0, 0.2, 7.2, 7.65, n=8, col=GREEN, r1=0.14)
    bx(m, mf, d0 + 0.3, d0 + 0.5, c0 - 0.55, c0 - 0.1, 6.5, 6.8, GREEN, top=True)
    # bicycle parking in front of the Suedtrakt (facade face c ~ -62 at d 60..90)
    cols = [hx("#3b4a63"), hx("#7a2f2f"), hx("#44604a"), hx("#6b6b6e"), hx("#a58a3a")]
    n = 0
    for d in np.arange(62.0, 89.0, 1.0):
        c = -66.2
        bx(m, mf, d - 0.02, d + 0.02, c - 0.9, c + 0.9, 0.0, 0.03, RACK, top=True)
        if n % 3 != 2: bike(m, mf, d, c, col=cols[n % 5])
        n += 1
    bx(m, mf, 61.5, 89.5, -67.2, -67.1, 0.0, 0.9, RACK, top=False, sides=(0, 0, 0, 0))
    info(m, "hbx_platz")
    return m


def europa():
    """Velostation Europaplatz surface items (OSM nodes: Zueri-rollt rental -265/-117, Ticketautomat -341/-120, charging station -249/-135 in the HB frame).
    The OSM polygon (way 526215141, d -341..-243, c -143..-105) is the underground station: only racks, a kiosk-like entrance canopy and a ticket machine are modelled."""
    m = Model("hbx_europa"); A = SignAtlas(256, 128)
    A.add("tkt", 96, 96, sign_text("Billette", "#e8f0f8", "#12202e", glow=(150, 180, 210), size=20, frame="#5b6f82"))
    ms = m.mat("sign", *A.images(), rough=0.8); mf = m.mat("flat", Image.new("RGBA", (8, 8), (255, 255, 255, 255)))
    DARK, MET = hx("#2b2e32"), hx("#8d9399"); cols = [hx("#3b4a63"), hx("#7a2f2f"), hx("#44604a"), hx("#6b6b6e"), hx("#a58a3a")]
    # rental racks (Zueri rollt): 2 rows of 8 bikes
    for r in range(2):
        for i in range(8):
            d, c = -265.0 + i * 0.9 - 3.6, -116.7 + r * 2.4
            bx(m, mf, d - 0.02, d + 0.02, c - 0.9, c + 0.9, 0.0, 0.03, MET, top=True)
            bike(m, mf, d, c, col=cols[(i + r) % 5])
    # entrance canopy at the charging station: 7 x 3.2 m, 2.6 m high, open front
    d, c = -249.3, -135.2
    bx(m, mf, d - 3.5, d + 3.5, c - 1.6, c + 1.6, 2.5, 2.7, DARK, top=True, bottom=True)
    for dd in (-3.3, 3.3):
        for cc in (-1.4, 1.4): bx(m, mf, d + dd - 0.06, d + dd + 0.06, c + cc - 0.06, c + cc + 0.06, 0.0, 2.5, DARK, top=False)
    bx(m, mf, d - 3.5, d + 3.5, c + 1.5, c + 1.6, 0.0, 2.5, hx("#5d6a72"), top=False, sides=(0, 0, 1, 0))
    for k in range(4): bx(m, mf, d - 3.0 + k * 1.7, d - 2.6 + k * 1.7, c - 0.6, c - 0.3, 0.0, 1.1, hx("#2f6f4d"), top=True)   # charging posts
    # ticket machine
    d, c = -340.6, -119.7
    bx(m, mf, d - 0.3, d + 0.3, c - 0.28, c + 0.28, 0.0, 1.75, MET, top=True)
    cf = c + 0.285
    m.quad(ms, [(d - 0.22, cf, 0.95), (d + 0.22, cf, 0.95), (d + 0.22, cf, 1.55), (d - 0.22, cf, 1.55)], uvr(A.rects["tkt"]), W)
    info(m, "hbx_europa")
    return m


def reg(m, name, title, hide, load_r, colliders=None):
    common.OVR = ROOT / "pipeline" / "overrides" / "landmarks_hbx.json"
    register(m, name, title, hide, load_r=load_r, colliders=colliders)


if __name__ == "__main__":
    import sys, merge
    if sys.argv[1:] == ["europa"]:
        merge.main = lambda: None     # no merge while a full build runs
        reg(europa(), "hbx_europa", "Zürich Europaplatz Velostation (Oberfläche)", [], 260); sys.exit()
    reg(perron(), "hbx_perron", "Zürich Hauptbahnhof Perron-Ausstattung", [], 330)
    # monument + parked bikes: solid footprint of the pedestal
    reg(platz(), "hbx_platz", "Zürich Bahnhofplatz Escher-Denkmal und Velostand", [], 220,
        colliders=[rect_ring(48 - 2.1, 48 + 2.1, -78 - 2.1, -78 + 2.1)])
