"""Poster designs (own layouts, free fonts only): swiss typo grid, riso 2-colour, club neon, line-up list, theatre, flea market.
Every style: f(event, rnd, W, H) -> RGB image at design size (W x H, Weltformat ratio 89.5:128 ~ 1:1.43)."""
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import wildposter_data as D
from config import ROOT

FD = ROOT / "web" / "public" / "fonts"
_cache = {}


def font(name, size):
    k = (name, int(size))
    if k not in _cache:
        f = ImageFont.truetype(str(FD / name), int(size))
        if name == "Oswald-Var.ttf":
            f.set_variation_by_axes([700])
        _cache[k] = f
    return _cache[k]


def fit(d, text, name, maxw, start, lo=12):
    s = start
    while s > lo and d.textlength(text, font=font(name, s)) > maxw:
        s -= 2
    return font(name, s)


def wrap(d, text, name, size, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font(name, size)) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def title_block(d, text, name, x, y, maxw, size, fill, lead=1.0, upper=True, anchor="l"):
    """Stack of wrapped title lines, each shrunk to fit; returns bottom y."""
    text = text.upper() if upper else text
    for ln in wrap(d, text, name, size, maxw)[:4]:
        f = fit(d, ln, name, maxw, size)
        tw = d.textlength(ln, font=f)
        d.text((x + (maxw - tw) / 2 if anchor == "c" else x, y), ln, font=f, fill=fill)
        y += int(f.size * lead)
    return y


def info_lines(ev):
    wd, dm, yr = D.date_parts(ev)
    when = " ".join(x for x in (wd, dm + yr if yr else dm, ev.get("time", "")) if x)
    where = ", ".join(x for x in (ev.get("venue", ""), ev.get("address", "")) if x)
    return when, where, ev.get("price", ""), ev.get("organizer", "")


def grain(im, rnd, amt=10):
    a = np.asarray(im).astype(np.int16)
    n = np.random.default_rng(rnd.randint(0, 1 << 30)).normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + n, 0, 255).astype(np.uint8))


PAPER = [(244, 240, 228), (250, 246, 236), (238, 232, 214)]
SPOT = {"pink": (240, 80, 150), "blue": (30, 80, 200), "yellow": (250, 215, 40), "green": (40, 170, 120), "red": (225, 50, 40),
        "orange": (250, 130, 30), "teal": (30, 160, 170)}


def swiss(ev, rnd, W=500, H=714):
    bg = rnd.choice([(244, 240, 228), (235, 235, 235), (250, 215, 40), (225, 50, 40), (30, 80, 200)])
    dark = sum(bg) < 480
    fg = (250, 248, 240) if dark else (15, 15, 15)
    acc = rnd.choice([c for c in SPOT.values() if c != bg])
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    m = 28
    d.rectangle([m, m, W - m, m + 4], fill=fg)  # top rule
    # grid shape
    r = rnd.choice([150, 190, 230])
    cx, cy = rnd.choice([W - m - r // 2, m + r // 2 + 150]), 420
    if rnd.random() < 0.5:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=acc)
    else:
        d.rectangle([cx - r, cy - r // 2, cx + r // 2, cy + r], fill=acc)
    when, where, price, org = info_lines(ev)
    d.text((m, m + 14), when, font=font("SpaceMono-Bold.ttf", 22), fill=fg)
    y = title_block(d, ev["title"], rnd.choice(["Oswald-Var.ttf", "ArchivoBlack-Regular.ttf", "Anton-Regular.ttf"]), m, m + 60, W - 2 * m, 110, fg, 0.92)
    if ev.get("subtitle"):
        y = title_block(d, ev["subtitle"], "Barlow-Bold.ttf", m, y + 10, W - 2 * m - 80, 30, fg, 1.1, upper=False)
    # info columns at the bottom on a 2-col grid
    by = H - 150
    d.rectangle([m, by - 10, W - m, by - 8], fill=fg)
    fs = font("SpaceMono-Bold.ttf", 17)
    for i, ln in enumerate(wrap(d, where, "SpaceMono-Bold.ttf", 17, W / 2 - m)[:4]):
        d.text((m, by + i * 22), ln, font=fs, fill=fg)
    col = [t for t in (ev.get("lineup", [])[:4] + [price]) if t]
    for i, t in enumerate(col[:6]):
        d.text((W / 2 + 10, by + i * 22), t[:26], font=fs, fill=fg)
    if org:
        d.text((m, H - 36), org[:44], font=font("SpaceMono-Bold.ttf", 14), fill=fg)
    return im


def riso(ev, rnd, W=500, H=714):
    paper = rnd.choice(PAPER)
    c1, c2 = rnd.sample(list(SPOT.values()), 2)
    layers = []
    when, where, price, org = info_lines(ev)
    for li, col in enumerate((c1, c2)):
        m = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(m)
        if li == 0:  # halftone blob
            cx, cy, R = rnd.randint(150, 350), rnd.randint(380, 520), rnd.randint(130, 200)
            for gy in range(0, H, 14):
                for gx in range(0, W, 14):
                    dist = np.hypot(gx - cx, gy - cy) / R
                    if dist < 1.2:
                        rr = 7 * max(0.0, 1.15 - dist)
                        d.ellipse([gx - rr, gy - rr, gx + rr, gy + rr], fill=255)
            title_block(d, ev["title"], "Anton-Regular.ttf", 26, 30, W - 52, 120, 255, 0.95)
        else:
            d.rectangle([26, H - 190, W - 26, H - 188], fill=255)
            d.text((26, H - 175), when, font=font("Oswald-Var.ttf", 44), fill=255)
            for i, ln in enumerate(wrap(d, where, "Barlow-Bold.ttf", 24, W - 52)[:3]):
                d.text((26, H - 120 + i * 28), ln, font=font("Barlow-Bold.ttf", 24), fill=255)
            if ev.get("lineup"):
                d.text((26, 390), " / ".join(ev["lineup"][:4])[:70], font=font("BarlowCondensed-Bold.ttf", 28), fill=255)
            if price:
                d.text((W - 160, 30), price[:12], font=font("Anton-Regular.ttf", 30), fill=255)
            d.rectangle([26, 32 + 130 * 2, 36, 40 + 130 * 2], fill=255)
        layers.append((m.filter(ImageFilter.GaussianBlur(0.6)).point(lambda v: 255 if v > 110 else 0), col))
    base = np.asarray(Image.new("RGB", (W, H), paper)).astype(np.float32)
    for i, (m, col) in enumerate(layers):
        off = (rnd.randint(-5, 5), rnd.randint(-5, 5)) if i else (0, 0)  # misregistration
        m = ImageChops.offset(m, *off)
        a = np.asarray(m).astype(np.float32)[..., None] / 255
        base = base * (1 - a) + base * (np.array(col) / 255) * a  # multiply blend
    return grain(Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)), rnd, 7)


def neon(ev, rnd, W=500, H=714):
    bg = (10, 8, 22)
    im = Image.new("RGB", (W, H), bg)
    a = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    hue = rnd.choice([(255, 40, 160), (40, 220, 255), (180, 255, 60), (255, 120, 40)])
    a += (np.array(hue) * 0.28)[None, None] * np.exp(-((yy - H * 0.55) / 260.0) ** 2)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    sharp = Image.new("RGB", (W, H), (0, 0, 0))
    when, where, price, org = info_lines(ev)
    for lay, fill in ((ImageDraw.Draw(glow), hue), (ImageDraw.Draw(sharp), (255, 255, 255))):
        y = title_block(lay, ev["title"], "BebasNeue-Regular.ttf", 28, 60, W - 56, 190, fill, 0.9, anchor="c")
        lay.rounded_rectangle([40, y + 20, W - 40, y + 130], radius=18, outline=fill, width=5)
        lay.text((W / 2, y + 75), when, font=fit(lay, when, "BebasNeue-Regular.ttf", W - 110, 70), fill=fill, anchor="mm")
        for i, t in enumerate(ev.get("lineup", [])[:5]):
            lay.text((W / 2, y + 190 + i * 40), t.upper()[:30], font=font("BebasNeue-Regular.ttf", 34), fill=fill, anchor="mm")
        lay.text((W / 2, H - 70), where.upper()[:46], font=fit(lay, where.upper(), "BarlowCondensed-Bold.ttf", W - 60, 28), fill=fill, anchor="mm")
        if price:
            lay.text((W / 2, H - 36), price.upper()[:30], font=font("BarlowCondensed-Bold.ttf", 24), fill=fill, anchor="mm")
    g1, g2 = glow.filter(ImageFilter.GaussianBlur(14)), glow.filter(ImageFilter.GaussianBlur(4))
    out = ImageChops.add(ImageChops.add(im, g1), ImageChops.add(g2, sharp))
    return grain(out, rnd, 6)


def lineup(ev, rnd, W=500, H=714):
    bg = rnd.choice([(250, 215, 40), (240, 235, 220), (225, 50, 40), (40, 170, 120), (245, 150, 190)])
    fg = (15, 15, 15)
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    when, where, price, org = info_lines(ev)
    d.rectangle([0, 0, W, 78], fill=fg)
    d.text((W / 2, 40), when, font=fit(d, when, "Anton-Regular.ttf", W - 40, 46), fill=bg, anchor="mm")
    y = title_block(d, ev["title"], "Anton-Regular.ttf", 24, 100, W - 48, 105, fg, 0.95)
    y += 14
    names = ev.get("lineup", []) or ([ev["subtitle"]] if ev.get("subtitle") else [])
    for i, n in enumerate(names[:9]):
        sz = max(30, 72 - i * 9)
        f = fit(d, n.upper(), "BarlowCondensed-Bold.ttf", W - 48, sz)
        d.text((24, y), n.upper(), font=f, fill=fg)
        y += int(f.size * 1.02)
        if i % 2 == 1:
            d.rectangle([24, y + 2, W - 24, y + 4], fill=fg)
            y += 10
    d.rectangle([0, H - 110, W, H], fill=fg)
    for i, ln in enumerate(wrap(d, where, "Barlow-Bold.ttf", 26, W - 48)[:2]):
        d.text((24, H - 100 + i * 30), ln, font=font("Barlow-Bold.ttf", 26), fill=bg)
    d.text((24, H - 38), " · ".join(t for t in (price, org) if t)[:50], font=font("SpaceMono-Bold.ttf", 17), fill=bg)
    return grain(im, rnd, 6)


def theater(ev, rnd, W=500, H=714):
    bg = rnd.choice([(238, 228, 205), (28, 36, 60), (120, 30, 40), (30, 60, 50)])
    fg = (30, 25, 20) if sum(bg) > 500 else (240, 228, 200)
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([20, 20, W - 20, H - 20], outline=fg, width=3)
    d.rectangle([30, 30, W - 30, H - 30], outline=fg, width=1)
    when, where, price, org = info_lines(ev)
    d.text((W / 2, 80), (ev.get("kind") or "").upper()[:30], font=font("SpaceMono-Bold.ttf", 18), fill=fg, anchor="mm")
    y = title_block(d, ev["title"], "DMSerifDisplay-Regular.ttf", 50, 130, W - 100, 90, fg, 1.02, upper=False, anchor="c")
    d.line([W / 2 - 60, y + 20, W / 2 + 60, y + 20], fill=fg, width=2)
    d.ellipse([W / 2 - 6, y + 14, W / 2 + 6, y + 26], fill=fg)
    y += 50
    if ev.get("subtitle"):
        y = title_block(d, ev["subtitle"], "DMSerifDisplay-Regular.ttf", 60, y, W - 120, 30, fg, 1.15, upper=False, anchor="c")
    y += 30
    for t in ev.get("lineup", [])[:5]:
        d.text((W / 2, y), t, font=font("DMSerifDisplay-Regular.ttf", 24), fill=fg, anchor="mt")
        y += 32
    d.text((W / 2, H - 175), when, font=fit(d, when, "Oswald-Var.ttf", W - 100, 44), fill=fg, anchor="mt")
    for i, ln in enumerate(wrap(d, where, "Barlow-Bold.ttf", 22, W - 100)[:2]):
        d.text((W / 2, H - 120 + i * 28), ln, font=font("Barlow-Bold.ttf", 22), fill=fg, anchor="mt")
    d.text((W / 2, H - 58), " · ".join(t for t in (price, org) if t)[:46], font=font("SpaceMono-Bold.ttf", 15), fill=fg, anchor="mt")
    return grain(im, rnd, 6)


def flohmarkt(ev, rnd, W=500, H=714):
    bg = rnd.choice([(255, 236, 120), (255, 160, 190), (170, 225, 140), (255, 190, 90)])
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    when, where, price, org = info_lines(ev)
    y = title_block(d, ev["title"], "Anton-Regular.ttf", 24, 30, W - 48, 150, (20, 20, 20), 0.95)
    if ev.get("subtitle"):
        d.text((24, y + 10), ev["subtitle"], font=fit(d, ev["subtitle"], "PermanentMarker-Regular.ttf", W - 48, 38), fill=(200, 30, 40))
    d.rounded_rectangle([24, 380, W - 24, 540], radius=14, outline=(20, 20, 20), width=5)
    d.text((W / 2, 435), when, font=fit(d, when, "Anton-Regular.ttf", W - 80, 56), fill=(20, 20, 20), anchor="mm")
    d.text((W / 2, 500), where[:40], font=fit(d, where[:40], "Barlow-Bold.ttf", W - 80, 28), fill=(20, 20, 20), anchor="mm")
    d.polygon([(W - 90, 580), (W - 40, 620), (W - 90, 660), (W - 90, 635), (W - 170, 635), (W - 170, 605), (W - 90, 605)], fill=(20, 20, 20))
    d.text((24, H - 80), " · ".join(t for t in (price, org) if t)[:36] or "Kommt vorbei!", font=font("PermanentMarker-Regular.ttf", 30), fill=(20, 20, 20))
    return grain(im, rnd, 7)


STYLES = {"swiss": swiss, "riso": riso, "neon": neon, "lineup": lineup, "theater": theater, "flohmarkt": flohmarkt}


def render(ev, rnd, W=500, H=714):
    k = D.kind_of(ev)
    if k in ("swiss", "lineup") and rnd.random() < 0.4:
        k = rnd.choice(["riso", "swiss"])
    return STYLES[k](ev, rnd, W, H)
