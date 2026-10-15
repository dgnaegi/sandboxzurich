"""Fictional wild-posting flyers (concerts, parties, flea market, WG-Zimmer, lost cat …) for walls, boxes and
underpasses. All bands, venues and events are invented (except generic recurring things like 'Flohmarkt').
Output: web/public/tex/wildposters.webp (4x4 grid of 256x362 A-format sheets) + wildposters.json."""
import json
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import ROOT

OUT = ROOT / "web" / "public" / "tex"
F = ROOT / "web" / "public" / "fonts"
W, H = 256, 362
rnd = random.Random(5)
BANDS = ["DIE SIHLPIRATEN", "KALKBREITE KIDS", "NEBELHORN", "TRAMLINIE 8", "HARDBRÜCKE BLUES", "VELOKURIER", "BETONGOLD",
         "LIMMATMÖWEN", "SCHMIEDE SOUND", "ZWEITE MIETE", "FAHRLEITUNG", "LOCHERGUT ORCHESTRA"]
VENUES = ["Keller 4", "Halle Hard", "Bar Bäcki", "Werkhof 5", "Kulturraum Sihl", "Garage West", "Dachkantine"]


def font(name, size):
    return ImageFont.truetype(str(F / name), size)


def fit(d, text, fn, maxw, start):
    s = start
    while s > 10 and d.textlength(text, font=font(fn, s)) > maxw:
        s -= 2
    return font(fn, s)


def concert(i):
    bg = rnd.choice([(20, 20, 24), (240, 220, 40), (230, 60, 50), (40, 90, 200), (250, 245, 235), (30, 160, 110)])
    fg = (255, 255, 255) if sum(bg) < 400 else (15, 15, 15)
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    for _ in range(rnd.randint(2, 6)):  # bold shapes
        c = tuple(rnd.randint(0, 255) for _ in range(3))
        x, y, r = rnd.randint(0, W), rnd.randint(40, H - 120), rnd.randint(20, 90)
        (d.ellipse if rnd.random() < 0.5 else d.rectangle)([x - r, y - r, x + r, y + r], fill=c)
    band = rnd.choice(BANDS)
    words = band.split()
    y = 20
    for w in words:
        f = fit(d, w, "Anton-Regular.ttf", W - 24, 70)
        d.text((12, y), w, font=f, fill=fg, stroke_width=2, stroke_fill=bg)
        y += f.size + 4
    day = rnd.randint(1, 28)
    month = rnd.choice(["MÄRZ", "APRIL", "MAI", "JUNI", "SEPT", "OKT", "NOV"])
    d.text((12, H - 96), f"{day}. {month}", font=font("Anton-Regular.ttf", 34), fill=fg, stroke_width=2, stroke_fill=bg)
    d.text((12, H - 52), f"{rnd.choice(VENUES)} · Türöffnung 20 Uhr", font=font("BarlowCondensed-Bold.ttf", 22), fill=fg)
    return im


def party(i):
    im = Image.new("RGB", (W, H), (12, 10, 30))
    a = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    a[..., 0] += 120 * np.sin(xx / 40.0 + i) ** 2
    a[..., 2] += 160 * np.cos(yy / 50.0) ** 2
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    title = rnd.choice(["TECHNO IM KELLER", "QUEER RAVE", "80s NIGHT", "AFROBEATS", "DRUM & BASS", "SOLI-PARTY"])
    for k, w in enumerate(title.split()):
        f = fit(d, w, "Anton-Regular.ttf", W - 24, 64)
        d.text((12, 30 + k * (f.size + 6)), w, font=f, fill=(255, 255, 255))
    d.text((12, H - 60), f"SA {rnd.randint(1, 28)}.{rnd.randint(1, 12)}. · {rnd.choice(VENUES)}", font=font("BarlowCondensed-Bold.ttf", 24), fill=(255, 230, 120))
    return im


def text_flyer(title, lines, bg, tabs=False):
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    f = fit(d, title, "Anton-Regular.ttf", W - 24, 54)
    d.text((12, 16), title, font=f, fill=(20, 20, 20))
    y = 40 + f.size
    for ln in lines:
        d.text((14, y), ln, font=font("Barlow-Bold.ttf", 18), fill=(40, 40, 40))
        y += 26
    if tabs:  # tear-off strips
        for k in range(8):
            x = 8 + k * 30
            d.rectangle([x, H - 70, x + 26, H - 4], outline=(120, 120, 120))
            d.text((x + 8, H - 66), "079", font=font("BarlowCondensed-Bold.ttf", 12), fill=(60, 60, 60))
    return im


def main():
    sheets = [concert(i) for i in range(8)] + [party(i) for i in range(3)]
    sheets += [text_flyer("WG-ZIMMER GESUCHT", ["Studentin, 24, ruhig,", "zahle max. 900.-", "Kreis 3/4/5", "bitte melden!"], (250, 250, 245), True),
               text_flyer("FLOHMARKT", ["jeden Samstag", "Kanzleiareal", "ab 8 Uhr"], (255, 236, 150)),
               text_flyer("KATZE VERMISST", ["«Mimi», getigert", "seit Dienstag", "Nähe Bäckeranlage"], (245, 245, 245), True),
               text_flyer("CRITICAL MASS", ["letzter Freitag", "im Monat", "18:30 · mit Velo"], (180, 230, 140)),
               text_flyer("NACHHILFE", ["Mathe & Deutsch", "Sek / Gymi", "günstig"], (230, 240, 255), True)]
    grid = Image.new("RGB", (W * 4, H * 4), (200, 200, 200))
    for k, im in enumerate(sheets[:16]):
        im = im.rotate(rnd.uniform(-1.5, 1.5), resample=Image.BICUBIC, fillcolor=im.getpixel((2, 2))).filter(ImageFilter.GaussianBlur(0.4))
        grid.paste(im, ((k % 4) * W, (k // 4) * H))
    grid.save(OUT / "wildposters.webp", quality=85)
    json.dump({"cols": 4, "rows": 4, "count": len(sheets), "size_m": [0.42, 0.594]}, open(OUT / "wildposters.json", "w"))
    grid.resize((W * 2, H * 2)).save(ROOT / "preview" / "wildposters.png")
    print("wild posters", len(sheets))


if __name__ == "__main__":
    main()
