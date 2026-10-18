"""Textures for the Letzipark landmark: window/shopfront/entrance decals (alpha cut-out) and a sign atlas (roof letters, Einkaufszentrum text,
shop name plates with the real tenant names from research/pois_kreis9_notes.md). Free font Barlow only; the plates are plain text (no logo copies)."""
import math
import numpy as np
from PIL import Image, ImageDraw
from schlachthof_tex import font

PLATES = [("coop", (255, 255, 255), (241, 90, 34)), ("MANOR", (20, 20, 20), (240, 240, 236)), ("Vögele", (255, 255, 255), (30, 30, 34)), ("bau+hobby", (255, 255, 255), (20, 150, 160)),
          ("Decathlon", (255, 255, 255), (0, 112, 190)), ("H&M", (255, 255, 255), (214, 30, 40)), ("Orell Füssli", (255, 255, 255), (40, 90, 150)), ("Dosenbach", (20, 20, 20), (250, 220, 40)),
          ("Gidor", (255, 255, 255), (60, 60, 64)), ("C&A", (255, 255, 255), (30, 60, 140)), ("Ochsner Sport", (255, 255, 255), (200, 30, 40)), ("Mobilezone", (255, 255, 255), (230, 80, 20))]
DR = {"ribbon": (0, 0, 512, 128), "shop": (0, 128, 512, 418), "door": (0, 418, 320, 768)}
SR = {"letters": (0, 0, 1024, 256), "ekz": (0, 256, 1024, 384), "hours": (0, 384, 512, 640)}
for i in range(12): SR[f"plate{i}"] = ((i % 2) * 512, 640 + (i // 2) * 64, (i % 2) * 512 + 512, 640 + (i // 2) * 64 + 64)


def uvr(rects, name, W, H):
    x0, y0, x1, y1 = rects[name]
    return [(x0 / W, 1 - y1 / H), (x1 / W, 1 - y1 / H), (x1 / W, 1 - y0 / H), (x0 / W, 1 - y0 / H)]


def decals():
    W, H = 512, 768
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); em = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im); de = ImageDraw.Draw(em)
    rng = np.random.default_rng(4)
    # ribbon window band 8 m x 2 m: dark reflective glass, 6 bays, slim grey mullions
    x0, y0, x1, y1 = DR["ribbon"]
    for y in range(y0 + 4, y1 - 4):
        f = (y - y0) / 124; c = (int(52 + 40 * (1 - f)), int(66 + 44 * (1 - f)), int(78 + 46 * (1 - f)), 255); d.line([x0 + 2, y, x1 - 2, y], fill=c)
    d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(150, 156, 160, 255), width=4)
    for k in range(1, 6): d.line([x0 + k * 512 / 6, y0, x0 + k * 512 / 6, y1], fill=(150, 156, 160, 255), width=3)
    for k in range(6):
        if rng.random() < 0.5: de.rectangle([x0 + k * 512 / 6 + 4, y0 + 6, x0 + (k + 1) * 512 / 6 - 4, y1 - 6], fill=(150, 130, 84))
    # shopfront 6 m x 3.4 m: dark frame, big glass with warm lit interior, 3 bays
    x0, y0, x1, y1 = DR["shop"]
    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=(64, 68, 72, 255))
    for k in range(3):
        a = x0 + 8 + k * 166; d.rectangle([a, y0 + 14, a + 160, y1 - 20], fill=(92, 110, 120, 255))
        de.rectangle([a, y0 + 14, a + 160, y1 - 20], fill=(150, 126, 84))
        d.rectangle([a, y0 + 14, a + 160, y0 + 60], fill=(130, 150, 160, 255))
        for s in range(4): d.rectangle([a + 14 + s * 38, y1 - 100, a + 40 + s * 38, y1 - 22], fill=(210, 200, 180, 255))    # goods
    # entrance 4.6 m x 5.0 m: glazed sliding doors, light frame, lit
    x0, y0, x1, y1 = DR["door"]
    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=(190, 194, 198, 255)); d.rectangle([x0 + 14, y0 + 30, x1 - 14, y1 - 6], fill=(96, 118, 128, 255))
    de.rectangle([x0 + 14, y0 + 30, x1 - 14, y1 - 6], fill=(170, 150, 100))
    for xx in (x0 + 14, (x0 + x1) // 2, x1 - 18): d.rectangle([xx, y0 + 30, xx + 4, y1 - 6], fill=(190, 194, 198, 255))
    d.rectangle([x0 + 14, y0 + 150, x1 - 14, y0 + 156], fill=(190, 194, 198, 255))
    return im, em


def signs():
    W, H = 1024, 1024
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); em = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im); de = ImageDraw.Draw(em)
    # roof letters LETZIPARK, blue, with green palm above "ZI"
    x0, y0, x1, y1 = SR["letters"]; f = font(168, "Barlow-Bold"); cx = (x0 + x1) / 2
    d.text((cx, y1 - 18), "LETZIPARK", font=f, fill=(46, 124, 230, 255), anchor="ms", stroke_width=4, stroke_fill=(235, 244, 255, 255))
    de.text((cx, y1 - 18), "LETZIPARK", font=f, fill=(60, 150, 255), anchor="ms", stroke_width=3)
    px, py = cx - 10, y0 + 70
    for ang, ln in ((-70, 60), (-35, 70), (0, 74), (35, 70), (70, 60), (-100, 40), (100, 40)):
        a = math.radians(ang - 90); ex, ey = px + ln * math.cos(a) * 0.9, py - ln * math.sin(a) * 0.0 + ln * math.sin(a) * 0.9 + 30
        d.line([px, py + 30, ex, ey], fill=(40, 180, 70, 255), width=14); de.line([px, py + 30, ex, ey], fill=(30, 130, 50), width=10)
    # EINKAUFSZENTRUM line on the dark/blue cube (pale, slightly lit)
    x0, y0, x1, y1 = SR["ekz"]; f = font(110, "Barlow-Bold")
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), "EINKAUFSZENTRUM", font=f, fill=(176, 206, 240, 255), anchor="mm"); de.text(((x0 + x1) / 2, (y0 + y1) / 2), "EINKAUFSZENTRUM", font=f, fill=(60, 80, 110), anchor="mm")
    # hours panel
    x0, y0, x1, y1 = SR["hours"]; f1 = font(64, "Barlow-Bold"); f2 = font(50, "Barlow-Bold")
    for i, (txt, ff) in enumerate((("66 Geschäfte", f1), ("Montag–Samstag", f2), ("9–20 Uhr", f2))):
        d.text((x0 + 20, y0 + 40 + i * 82), txt, font=ff, fill=(214, 234, 255, 255), anchor="lm")
    # shop name plates (plain text on coloured board)
    for i, (txt, fg, bg) in enumerate(PLATES):
        x0, y0, x1, y1 = SR[f"plate{i}"]; d.rectangle([x0 + 2, y0 + 4, x1 - 3, y1 - 5], fill=bg + (255,)); ff = font(44, "Barlow-Bold")
        d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 2), txt, font=ff, fill=fg + (255,), anchor="mm"); de.rectangle([x0 + 2, y0 + 4, x1 - 3, y1 - 5], fill=tuple(int(v * 0.45) for v in bg))
    return im, em


def huge():
    """Giant facade lettering L E T Z + palm-I (photos: dark Baslerstrasse facade). 1024 x 256 RGBA cut-out, 60 m x 15 m on the wall; palm is big and green."""
    W, H = 1024, 256
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); em = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im); de = ImageDraw.Draw(em)
    f = font(210, "Barlow-Bold"); BL = (52, 128, 232, 255); LI = (170, 214, 255, 255)
    pitch = 190.0
    for i, ch in enumerate("LETZ"):
        cx = 40 + pitch * (i + 0.5)
        d.text((cx, H - 8), ch, font=f, fill=BL, anchor="ms", stroke_width=5, stroke_fill=LI); de.text((cx, H - 8), ch, font=f, fill=(40, 90, 170), anchor="ms", stroke_width=3)
    cx = 40 + pitch * 4 + 70; top = 112                                       # the I is a palm: blue trunk, big green fronds
    d.rectangle([cx - 17, top, cx + 17, H - 8], fill=BL, outline=LI, width=4); de.rectangle([cx - 17, top, cx + 17, H - 8], fill=(40, 90, 170))
    for ang, ln in ((-85, 150), (-55, 168), (-25, 160), (0, 120), (25, 160), (55, 168), (85, 150), (-115, 90), (115, 90)):
        a = math.radians(ang); ex, ey = cx + ln * math.sin(a) * 0.95, top - ln * math.cos(a) * 0.7 + ln * 0.35 * abs(math.sin(a)) + 10
        d.line([cx, top, ex, ey], fill=(34, 190, 70, 255), width=30); d.line([cx, top, ex, ey], fill=(140, 238, 140, 255), width=7)
        de.line([cx, top, ex, ey], fill=(30, 110, 50), width=20)
    return im, em
