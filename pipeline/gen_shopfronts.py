"""Procedural shopfront textures v2 (12 m x 4 m ground floor, one layer per shop type/variant).

Layout (metres from the left/top of the texture, 3 m bays): fascia band y 0.25..1.15 stays blank (the name sign is a
runtime quad), glass y 1.5..3.55, stall riser below, door around x = 4.5 (so it is visible on walls >= 6 m).
Albedo = day look; emissive mask (alpha channel of atlas_mask) = what glows at night: lit interiors, neon tubes.
The shader multiplies albedo * mask, so interiors are painted in the colour they should glow.
Run via gen_textures.py (imports SHOP_LAYERS); standalone: prints a contact sheet to preview/shopfronts_tex.jpg.
"""
import random

from PIL import Image

from shopfront_draw import Cv, S, P

WARM = (255, 214, 150)


# ---------------------------------------------------------------- small furniture helpers
def person(c, x, fy, col=(28, 22, 26), s=1.0):
    c.e(x - 0.09 * s, fy - 1.72 * s, x + 0.09 * s, fy - 1.54 * s, col, 50)
    c.r(x - 0.17 * s, fy - 1.5 * s, x + 0.17 * s, fy - 0.8 * s, col, 50)
    c.r(x - 0.13 * s, fy - 0.8 * s, x + 0.13 * s, fy, col, 40)


def table(c, x, fy, w=0.7, col=(60, 44, 34), cloth=None):
    if cloth:
        c.r(x - w / 2, fy - 0.78, x + w / 2, fy - 0.45, cloth, 190)
    c.r(x - w / 2, fy - 0.78, x + w / 2, fy - 0.74, col, 60)
    c.r(x - 0.03, fy - 0.74, x + 0.03, fy, col, 40)


def chair(c, x, fy, col=(40, 30, 26)):
    c.r(x - 0.2, fy - 0.45, x + 0.2, fy - 0.41, col, 40)
    c.r(x - 0.2, fy - 0.9, x - 0.16, fy - 0.41, col, 40)
    c.r(x - 0.2, fy - 0.41, x - 0.16, fy, col, 40)
    c.r(x + 0.16, fy - 0.41, x + 0.2, fy, col, 40)


def pendant(c, x, y0, y1, col=WARM, r=0.13):
    c.r(x - 0.01, y0, x + 0.01, y1, (40, 40, 40), 30)
    c.e(x - r, y1 - r * 0.6, x + r, y1 + r * 0.9, col, 255)
    c.glow(x - 0.5, y1 - 0.3, x + 0.5, y1 + 0.6, col, 150, 0.2)


def shelves(c, x0, x1, ys, goods, rnd, w_rng=(0.1, 0.22), hmax=0.3):
    for y in ys:
        c.r(x0, y, x1, y + 0.025, (150, 150, 150), 120)
        x = x0 + 0.03
        while x < x1 - 0.1:
            w = rnd.uniform(*w_rng)
            hh = rnd.uniform(hmax * 0.6, hmax)
            c.r(x, y - hh, x + w, y, rnd.choice(goods), 230)
            x += w + 0.012


def bottles(c, x0, x1, ys, rnd):
    cols = [(170, 100, 30), (40, 120, 60), (50, 90, 170), (200, 60, 90), (230, 200, 80), (120, 40, 140), (210, 210, 210)]
    for y in ys:
        c.r(x0, y, x1, y + 0.03, (200, 200, 210), 255)
        x = x0 + 0.05
        while x < x1 - 0.08:
            hh = rnd.uniform(0.22, 0.34)
            col = rnd.choice(cols)
            c.r(x, y - hh, x + 0.07, y, col, 255)
            c.r(x + 0.025, y - hh - 0.07, x + 0.045, y - hh, col, 255)
            x += 0.11


def bike(c, x, fy, col, s=1.0):
    r = 0.34 * s
    for cx in (x - 0.5 * s, x + 0.5 * s):
        c.ring(cx, fy - r, r, (25, 25, 28), 0.03, 200)
    a, b, d, e = (x - 0.5 * s, fy - r), (x, fy - r - 0.25 * s), (x + 0.5 * s, fy - r), (x + 0.15 * s, fy - r - 0.5 * s)
    for p, q in ((a, b), (b, d), (a, e), (b, e), (e, d)):
        c.line([p, q], col, 0.035, 230)
    c.line([(x - 0.05 * s, fy - r - 0.58 * s), (x - 0.18 * s, fy - r - 0.58 * s)], (30, 30, 30), 0.04, 200)


def poster(c, x, y, w, h, col, label=None, lc=(255, 255, 255)):
    c.r(x, y, x + w, y + h, col, 255)
    if label:
        c.text(x + w / 2, y + h / 2, label, min(h * 0.45, w * 0.28), lc, 255)


def back_wall(c, col, m):
    c.r(0, 0, c.w, c.h, col, m)


# ---------------------------------------------------------------- interiors: fn(cv, rnd) draws into the glass area
def in_cafe(c, rnd):
    back_wall(c, (176, 128, 84), 235)
    c.r(0, c.h - 0.18, c.w, c.h, (110, 80, 52), 120)
    for i in range(int(c.w // 1.4)):
        pendant(c, 0.6 + i * 1.4 + rnd.uniform(-.1, .1), 0, 0.45 + rnd.uniform(0, .2))
    c.r(c.w * 0.62, c.h - 0.95, c.w - 0.1, c.h, (70, 50, 38), 60)  # counter
    c.r(c.w * 0.68, c.h - 1.25, c.w * 0.68 + 0.4, c.h - 0.95, (170, 170, 175), 160)  # machine
    shelves(c, c.w * 0.6, c.w - 0.1, [0.75], [(230, 220, 200), (120, 60, 40), (40, 80, 60)], rnd)
    for i in range(2):
        x = 0.55 + i * 1.35
        table(c, x, c.h + 0.02, 0.6)
        chair(c, x - 0.5, c.h)
        chair(c, x + 0.5, c.h)
    if rnd.random() < 0.7:
        person(c, rnd.uniform(0.6, 2.2), c.h + 0.1)


def in_restaurant(c, rnd):
    back_wall(c, (150, 104, 70), 215)
    c.r(0, c.h - 0.15, c.w, c.h, (70, 40, 30), 90)
    for i in range(int(c.w // 1.2)):
        x = 0.5 + i * 1.2
        table(c, x, c.h + 0.05, 0.75, cloth=(235, 228, 215))
        c.e(x - 0.03, c.h - 0.9, x + 0.03, c.h - 0.84, (255, 220, 120), 255)  # candle
        chair(c, x - 0.52, c.h + 0.05, (50, 30, 24))
        chair(c, x + 0.52, c.h + 0.05, (50, 30, 24))
        if rnd.random() < 0.45:
            person(c, x + rnd.choice((-.45, .45)), c.h + 0.0, s=0.95)
    for i in range(3):
        pendant(c, 0.9 + i * c.w / 3, 0, 0.35, (255, 190, 110), 0.1)
    poster(c, 0.12, 0.35, 0.42, 0.62, (240, 232, 205), "MENÜ", (60, 40, 30))


def in_bar(c, rnd):
    back_wall(c, (36, 18, 42), 150)
    bottles(c, 0.2, c.w - 0.2, [0.55, 0.95], rnd)
    c.r(0.1, c.h - 0.9, c.w - 0.1, c.h, (30, 20, 28), 70)  # bar counter
    c.r(0.1, c.h - 0.92, c.w - 0.1, c.h - 0.88, (230, 90, 170), 255)  # lit edge
    for i in range(int(c.w // 0.9)):
        x = 0.5 + i * 0.9
        if rnd.random() < 0.55:
            person(c, x, c.h - 0.1)
        c.r(x - 0.02, c.h - 0.55, x + 0.02, c.h, (20, 20, 20), 40)
    col = rnd.choice([(255, 60, 170), (40, 230, 220)])
    cx, cy = c.w * 0.5, 0.25
    c.line([(cx - 0.18, cy - 0.12), (cx + 0.18, cy - 0.12), (cx, cy + 0.1), (cx - 0.18, cy - 0.12)], col, 0.03, 255)  # neon cocktail glass
    c.line([(cx, cy + 0.1), (cx, cy + 0.28)], col, 0.03, 255)
    c.text(c.w * 0.82, 0.3, rnd.choice(["BAR", "OPEN", "COCKTAILS"]), 0.26, (40, 230, 220) if col[0] > 200 else (255, 60, 170), 255)


def in_club(c, rnd):
    back_wall(c, (30, 10, 40), 200)
    for i in range(4):
        col = rnd.choice([(255, 40, 160), (60, 80, 255), (40, 240, 220), (255, 200, 40)])
        c.glow(rnd.uniform(0, c.w * .8), rnd.uniform(0, c.h * .5), c.w, c.h, col, 255, 0.15)


def in_kebab(c, rnd):
    back_wall(c, (238, 226, 190), 255)
    c.r(0, 0, c.w, 0.05, (255, 255, 255), 255)
    c.r(0.1, c.h - 0.85, c.w - 0.1, c.h, (170, 172, 175), 150)  # steel counter
    sx = c.w * 0.72
    c.poly([(sx - 0.15, c.h - 0.9), (sx + 0.15, c.h - 0.9), (sx + 0.1, c.h - 1.6), (sx - 0.1, c.h - 1.6)], (150, 85, 45), 160)  # döner spit
    c.line([(sx, c.h - 1.7), (sx, c.h - 0.9)], (200, 200, 200), 0.02, 200)
    for i in range(3):  # backlit menu panels with picture blocks
        x = 0.15 + i * 0.7
        c.r(x, 0.15, x + 0.62, 0.72, (200, 30, 30), 255)
        c.r(x + 0.04, 0.2, x + 0.58, 0.5, rnd.choice([(250, 190, 40), (120, 170, 60), (230, 130, 50)]), 255)
        c.r(x + 0.06, 0.55, x + 0.5, 0.65, (255, 240, 210), 255)
    person(c, c.w * 0.45, c.h + 0.05) if rnd.random() < 0.5 else None


def in_kiosk(c, rnd):
    back_wall(c, (214, 205, 175), 220)
    shelves(c, 0.1, c.w - 0.1, [0.95, 1.4], [(220, 40, 40), (250, 200, 30), (40, 100, 200), (240, 240, 240), (50, 50, 50)], rnd, (0.12, 0.3), 0.32)
    x = 0.12
    cols = [((250, 205, 30), "LOTTO"), ((50, 130, 220), "GLACE"), ((30, 30, 30), "TABAK"), ((220, 50, 50), "ZEITUNGEN"), ((60, 160, 90), "GETRÄNKE")]
    rnd.shuffle(cols)
    for col, lab in cols[:int(c.w // 0.75)]:
        poster(c, x, 0.12, 0.66, 0.5, col, lab, (20, 20, 20) if col[0] > 240 else (255, 255, 255))
        x += 0.72
    c.r(0.05, c.h - 0.55, c.w - 0.05, c.h, (60, 60, 64), 60)  # counter


def in_spaeti(c, rnd):
    back_wall(c, (230, 232, 228), 255)
    shelves(c, 0.1, c.w * 0.62, [0.5, 0.95, 1.4], [(220, 40, 40), (250, 200, 30), (40, 150, 90), (40, 100, 200), (240, 130, 30), (240, 240, 240)], rnd)
    cx0 = c.w * 0.66  # cooler with beer
    c.r(cx0, 0.25, c.w - 0.1, c.h, (170, 215, 240), 255)
    for y in (0.55, 0.9, 1.25, 1.6):
        bottles(c, cx0 + 0.05, c.w - 0.15, [y], rnd)
    c.text(0.6, 0.2, "OFFEN", 0.2, (255, 70, 60), 255)


def in_baeckerei(c, rnd):
    back_wall(c, (240, 224, 190), 255)
    shelves(c, 0.1, c.w - 0.1, [0.65, 1.05], [(176, 112, 56), (200, 140, 70), (150, 90, 45), (225, 180, 110)], rnd, (0.14, 0.3), 0.28)
    c.r(0.05, c.h - 0.7, c.w - 0.05, c.h, (245, 245, 240), 220)  # display counter
    for i in range(int(c.w / 0.18)):
        c.e(0.12 + i * 0.18, c.h - 0.78, 0.26 + i * 0.18, c.h - 0.7, rnd.choice([(230, 160, 170), (250, 220, 120), (150, 90, 50)]), 240)
    for i in range(3):
        pendant(c, 0.7 + i * c.w / 3, 0, 0.3, (255, 235, 190), 0.1)


def in_coiffeur(c, rnd):
    back_wall(c, (216, 220, 224), 255)
    for i in range(int(c.w // 1.1)):
        x = 0.35 + i * 1.1
        c.r(x, 0.2, x + 0.8, 1.05, (60, 60, 64), 255)
        c.r(x + 0.04, 0.24, x + 0.76, 1.01, (190, 215, 235), 255)  # lit mirror
        c.r(x + 0.25, c.h - 0.9, x + 0.55, c.h - 0.45, (25, 25, 28), 70)  # chair
        c.r(x + 0.38, c.h - 0.45, x + 0.42, c.h, (60, 60, 60), 60)
        if rnd.random() < 0.55:
            person(c, x + 0.4, c.h - 0.2, (40, 30, 35), 0.8)
    for i in range(2):
        pendant(c, 0.9 + i * c.w * 0.5, 0, 0.3, (255, 250, 235), 0.09)


def in_velo(c, rnd):
    back_wall(c, (232, 230, 224), 245)
    c.r(0.1, 0.35, c.w * 0.35, 1.1, (80, 76, 70), 150)  # tool wall
    for k in range(7):
        c.line([(0.2 + k * 0.1, 0.45), (0.2 + k * 0.1, 0.95)], (210, 210, 210), 0.02, 200)
    cols = [(210, 40, 40), (30, 90, 190), (240, 170, 30), (30, 140, 90), (30, 30, 30)]
    for i in range(int((c.w - 1.0) // 1.4)):
        bike(c, c.w * 0.4 + 0.8 + i * 1.4, c.h + 0.02, rnd.choice(cols))


def in_super(c, rnd):
    back_wall(c, (240, 242, 238), 255)
    c.r(0, 0, c.w, 0.06, (255, 255, 255), 255)
    goods = [(220, 40, 40), (250, 200, 30), (40, 150, 90), (40, 100, 200), (240, 130, 30), (240, 240, 240), (150, 60, 140)]
    shelves(c, 0.1, c.w - 0.1, [0.7, 1.15, 1.6], goods, rnd, (0.1, 0.2), 0.34)
    for i in range(int(c.w // 1.1)):
        poster(c, 0.2 + i * 1.1, 0.1, 0.5, 0.28, rnd.choice([(220, 30, 30), (250, 210, 30)]), rnd.choice(["-30%", "NEU", "ANGEBOT", "2 FÜR 1"]), (255, 255, 255))


def in_gemuese(c, rnd):
    back_wall(c, (60, 80, 50), 150)
    for row in range(2):
        y = c.h - 0.55 - row * 0.5
        c.r(0.05, y, c.w - 0.05, y + 0.45, (150, 105, 60), 100)
        x = 0.12
        while x < c.w - 0.3:
            col = rnd.choice([(210, 40, 30), (240, 150, 30), (110, 160, 50), (245, 215, 60), (120, 40, 100), (60, 130, 50)])
            c.e(x, y - 0.12, x + 0.2, y + 0.06, col, 235)
            x += 0.17
    c.text(c.w / 2, 0.3, rnd.choice(["FRISCH", "BIO", "REGIONAL"]), 0.28, (255, 240, 170), 230)


def in_buero(c, rnd):
    back_wall(c, (170, 176, 178), 80)
    for i in range(int(c.h / 0.07)):
        c.r(0, i * 0.07, c.w, i * 0.07 + 0.05, (205, 208, 206), 90)
    c.r(0, 0, c.w, rnd.uniform(0.3, 0.9), (185, 188, 186), 60)


def in_leer(c, rnd):
    back_wall(c, (222, 219, 205), 0)
    c.r(0, c.h - 0.2, c.w, c.h, (150, 148, 135), 0)
    poster(c, c.w * 0.3, 0.35, 0.6, 0.85, (250, 250, 245), None)
    c.text(c.w * 0.3 + 0.3, 0.6, "ZU", 0.16, (200, 40, 40), 0)
    c.text(c.w * 0.3 + 0.3, 0.82, "VERMIETEN", 0.11, (200, 40, 40), 0)
    c.line([(0.2, 1.4), (0.6, 1.0), (0.9, 1.45)], (40, 40, 40), 0.03, 0)


def in_laden(c, rnd):
    back_wall(c, (232, 228, 222), 255)
    for i in range(int(c.w // 0.9)):
        x = 0.45 + i * 0.9
        col = rnd.choice([(190, 40, 60), (40, 70, 130), (230, 190, 60), (30, 30, 34), (60, 130, 100)])
        c.e(x - 0.07, c.h - 1.75, x + 0.07, c.h - 1.6, (200, 180, 160), 220)  # mannequin head
        c.poly([(x - 0.22, c.h - 1.58), (x + 0.22, c.h - 1.58), (x + 0.14, c.h - 0.7), (x - 0.14, c.h - 0.7)], col, 250)
        c.r(x - 0.02, c.h - 0.7, x + 0.02, c.h, (60, 60, 60), 60)
    poster(c, c.w - 0.75, 0.1, 0.6, 0.35, (220, 30, 40), "SALE")
    for i in range(3):
        c.glow(0.5 + i * c.w / 3, 0, 1.0 + i * c.w / 3, 0.5, (255, 245, 225), 255, 0.1)


def in_apotheke(c, rnd):
    back_wall(c, (238, 242, 240), 255)
    shelves(c, 0.1, c.w - 0.1, [0.6, 1.0, 1.4], [(255, 255, 255), (60, 170, 110), (220, 235, 240), (200, 220, 200)], rnd)
    cx = c.w * 0.5
    c.r(cx - 0.07, 0.05, cx + 0.07, 0.4, (40, 200, 110), 255)  # green cross
    c.r(cx - 0.18, 0.16, cx + 0.18, 0.29, (40, 200, 110), 255)


def in_bank(c, rnd):
    back_wall(c, (168, 188, 198), 120)  # frosted film
    c.r(0, c.h * 0.4, c.w, c.h * 0.46, (240, 240, 240), 160)
    c.r(0, 0, c.w, c.h, (178, 196, 206), 90)


# ---------------------------------------------------------------- shopfront assembly
def make(spec, seed):
    rnd = random.Random(seed)
    sp = dict(spec)
    c = Cv(12, 4, sp["wall"])
    # fascia band (name sign is a runtime quad on top) + plinth/riser
    c.r(0, 0.25, 12, 1.2, sp["fascia"], 0, 140)
    c.r(0, 0.22, 12, 0.27, (60, 60, 60), 0, 160)
    c.r(0, 3.55, 12, 4.0, sp["riser"], 0, 150)
    c.r(0, 3.55, 12, 3.6, (35, 35, 38), 0, 165)
    for x in (0, 3, 6, 9):  # pilaster-ish shading at the bays
        c.r(x, 1.2, x + 0.12, 3.55, tuple(max(0, v - 25) for v in sp["wall"]), 0, 150)
    dx = sp.get("door_x", 4.5)
    dw = 1.15
    glass_span = [(0.2, dx - 0.12), (dx + dw + 0.12, 11.8)]
    if sp.get("no_windows"):
        glass_span = [(0.3, 1.6), (9.6, 11.7)] if sp["no_windows"] == 2 else []
    for x0, x1 in glass_span:
        if x1 - x0 < 0.5:
            continue
        y0, y1 = (1.5, 3.55) if not sp.get("no_windows") else (1.9, 2.7)
        c.r(x0, y0, x1, y1, sp["frame"], 0, 165)
        sub = Cv(x1 - x0 - 0.14, y1 - y0 - 0.14, (30, 30, 30))
        sub.m.paste(Image.new("L", sub.m.size, 0))
        sp["interior"](sub, random.Random(seed + int(x0 * 10)))
        c.paste(sub, x0 + 0.07, y0 + 0.07)
        c.reflect(x0 + 0.07, y0 + 0.07, x1 - 0.07, y1 - 0.07, 0.2)
        for mx in (3, 6, 9):  # mullions at the bay edges
            if x0 + 0.3 < mx < x1 - 0.3:
                c.r(mx - 0.035, y0, mx + 0.035, y1, sp["frame"], 0, 170)
    # door
    kind = sp.get("door", "glass")
    c.r(dx, 1.4, dx + dw, 3.97, sp["frame"], 0, 168)
    if kind == "glass":
        sub = Cv(dw - 0.2, 1.75, (30, 30, 30))
        sp["interior"](sub, random.Random(seed + 99))
        c.paste(sub, dx + 0.1, 1.55)
        c.reflect(dx + 0.1, 1.55, dx + dw - 0.1, 3.3, 0.22)
        c.r(dx + 0.1, 3.4, dx + dw - 0.1, 3.9, sp["frame"], 0, 160)
    else:
        col = sp.get("door_col", (30, 30, 34))
        c.r(dx + 0.08, 1.48, dx + dw - 0.08, 3.95, col, 0, 160)
        if kind == "porthole":
            c.e(dx + 0.3, 1.9, dx + dw - 0.3, 2.45, (50, 40, 60), sp.get("lit", 150), 120)
        if kind == "club":
            c.line([(dx + 0.05, 3.95), (dx + 0.05, 1.45), (dx + dw - 0.05, 1.45), (dx + dw - 0.05, 3.95)], sp["neon"], 0.05, 255)
    c.r(dx + dw - 0.22, 2.55, dx + dw - 0.19, 3.15, (200, 200, 205), 0, 175)  # pull handle
    c.r(dx - 0.05, 3.94, dx + dw + 0.05, 4.0, (120, 118, 112), 0, 130)
    c.r(dx + 0.15, 1.6 if kind != "glass" else 3.2, dx + 0.45, 1.75 if kind != "glass" else 3.35, (255, 255, 255), 255 if sp.get("open_sign") else 0)
    if sp.get("neon"):  # neon tube under the fascia + lit edge for the sign
        col = sp["neon"]
        c.line([(0.3, 1.27), (11.7, 1.27)], col, 0.035, 255)
        c.line([(0.3, 0.18), (11.7, 0.18)], col, 0.02, 200)
    if sp.get("stripe"):  # painted accent line (e.g. fascia trim)
        c.r(0, 1.2, 12, 1.26, sp["stripe"], 0, 160)
    if sp.get("extra"):
        sp["extra"](c, rnd)
    return c.finish()


def paint_tag(c, rnd):
    c.line([(0.5, 3.7), (1.2, 3.4), (1.9, 3.8), (2.4, 3.45)], rnd.choice([(230, 40, 120), (40, 200, 220), (240, 220, 40)]), 0.08, 0)


GREY = (205, 202, 195)
SPECS = {
    "cafe_a": dict(wall=(222, 214, 196), fascia=(70, 100, 78), riser=(60, 56, 50), frame=(36, 48, 40), interior=in_cafe, open_sign=1),
    "cafe_b": dict(wall=(228, 220, 205), fascia=(150, 50, 40), riser=(80, 62, 50), frame=(60, 36, 30), interior=in_cafe, door_x=4.9),
    "restaurant_a": dict(wall=(218, 206, 186), fascia=(110, 28, 40), riser=(50, 44, 42), frame=(40, 30, 30), interior=in_restaurant, stripe=(200, 170, 90)),
    "restaurant_b": dict(wall=(232, 226, 214), fascia=(30, 34, 40), riser=(70, 70, 72), frame=(26, 26, 28), interior=in_restaurant, door_x=4.9, stripe=(190, 150, 60)),
    "bar_a": dict(wall=(70, 62, 74), fascia=(24, 18, 30), riser=(30, 26, 32), frame=(18, 14, 20), interior=in_bar, door="porthole", door_col=(36, 22, 44), neon=(255, 60, 170), lit=170, extra=paint_tag),
    "bar_b": dict(wall=(54, 58, 66), fascia=(16, 20, 28), riser=(28, 30, 34), frame=(14, 16, 20), interior=in_bar, door="porthole", door_col=(30, 30, 40), neon=(40, 230, 220), lit=170, door_x=4.9),
    "club": dict(wall=(34, 30, 38), fascia=(14, 10, 18), riser=(24, 20, 26), frame=(12, 10, 14), interior=in_club, door="club", neon=(255, 40, 160), no_windows=2, door_x=4.5),
    "kebab_a": dict(wall=(232, 224, 200), fascia=(190, 30, 30), riser=(150, 40, 30), frame=(60, 20, 20), interior=in_kebab, open_sign=1),
    "kebab_b": dict(wall=(238, 232, 216), fascia=(40, 120, 60), riser=(60, 70, 60), frame=(30, 50, 36), interior=in_kebab, door_x=4.9, open_sign=1),
    "kiosk": dict(wall=(206, 204, 196), fascia=(220, 190, 40), riser=(60, 60, 64), frame=(40, 40, 44), interior=in_kiosk, open_sign=1),
    "spaeti": dict(wall=(200, 206, 204), fascia=(30, 80, 160), riser=(60, 66, 70), frame=(40, 44, 50), interior=in_spaeti, open_sign=1, extra=paint_tag),
    "baeckerei": dict(wall=(236, 226, 206), fascia=(160, 110, 60), riser=(110, 76, 50), frame=(90, 62, 40), interior=in_baeckerei, open_sign=1),
    "coiffeur": dict(wall=(230, 230, 232), fascia=(24, 24, 28), riser=(40, 40, 44), frame=(24, 24, 28), interior=in_coiffeur, stripe=(230, 230, 230)),
    "velo": dict(wall=(220, 218, 210), fascia=(230, 120, 30), riser=(70, 70, 70), frame=(50, 50, 52), interior=in_velo),
    "super": dict(wall=(232, 232, 226), fascia=(220, 40, 40), riser=(150, 150, 150), frame=(70, 70, 76), interior=in_super, open_sign=1),
    "gemuese": dict(wall=(222, 214, 192), fascia=(50, 110, 60), riser=(100, 80, 56), frame=(48, 40, 30), interior=in_gemuese),
    "laden_a": dict(wall=(226, 222, 214), fascia=(36, 36, 40), riser=(60, 60, 64), frame=(20, 20, 24), interior=in_laden),
    "laden_b": dict(wall=(215, 205, 192), fascia=(120, 90, 60), riser=(70, 56, 46), frame=(50, 38, 30), interior=in_laden, door_x=4.9),
    "buero": dict(wall=(196, 198, 196), fascia=(150, 154, 158), riser=(100, 104, 108), frame=(70, 74, 78), interior=in_buero),
    "leer": dict(wall=(190, 184, 170), fascia=(150, 146, 134), riser=(110, 104, 96), frame=(80, 76, 70), interior=in_leer, extra=paint_tag),
    "apotheke": dict(wall=(230, 232, 230), fascia=(40, 150, 100), riser=(120, 130, 126), frame=(60, 76, 70), interior=in_apotheke),
    "bank": dict(wall=(206, 208, 210), fascia=(60, 70, 90), riser=(90, 96, 104), frame=(50, 56, 66), interior=in_bank),
}
SHOP_LAYERS = {f"shop_{k}": (lambda s=s, i=i: make(s, 100 + i)) for i, (k, s) in enumerate(SPECS.items())}
BASE = {}  # base type -> layer names (variants)
for _n in SHOP_LAYERS:
    BASE.setdefault(_n[5:].rsplit("_", 1)[0] if _n[-2:] in ("_a", "_b") else _n[5:], []).append(_n)

if __name__ == "__main__":
    import numpy as np
    from config import ROOT
    names = list(SHOP_LAYERS)
    sheet = Image.new("RGB", (4 * 640, ((len(names) + 1) // 2) * 213))
    for i, n in enumerate(names):
        rgb, mask, _ = SHOP_LAYERS[n]()
        a, m = np.asarray(rgb, np.float32), np.asarray(mask, np.float32)[..., None] / 255
        night = Image.fromarray(np.clip(a * m * 1.3 + a * 0.04, 0, 255).astype(np.uint8))
        for j, im in enumerate((rgb, night)):
            sheet.paste(im.resize((640, 213)), (((i % 2) * 2 + j) * 640, (i // 2) * 213))
    sheet.resize((sheet.width // 2, sheet.height // 2)).save(ROOT / "preview" / "shopfronts_tex.jpg", quality=85)
    print(len(names), "layers")
