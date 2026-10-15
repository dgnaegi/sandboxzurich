"""Poster-wall pieces: overlapping pasted sheets (old ones faded below), torn corners, wheat-paste sheen, folds,
stickers and marker tags on top. piece(...) -> RGBA PIL image (PX x PX, 1.5 x 1.5 m)."""
import math

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

import wildposter_styles as S

PX = 1024            # working size of one piece; atlas cell is PX/2
PXM = PX / 1.5       # px per metre
FORMATS = {"F4": (0.895, 1.28), "A1": (0.594, 0.841), "A2": (0.42, 0.594)}
TAGS = ["WAVE", "ZUPA", "MOKA", "SKYR", "NIRO", "PLOP", "HEI", "ZH", "BOLA", "KIWI"]
INK = [(15, 15, 15), (230, 40, 40), (30, 90, 220), (240, 230, 240), (250, 200, 30)]


def lowfreq(rnd, w, h, sigma, amp):
    n = np.random.default_rng(rnd.randint(0, 1 << 30)).normal(0, 1, (h, w)).astype(np.float32)
    im = Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
    a = (np.asarray(im).astype(np.float32) - 128)
    return a / (np.abs(a).max() + 1e-6) * amp


def age_sheet(im, rnd, age, fresh):
    """im RGBA -> faded, crumpled, folded, with sheen and torn corners."""
    w, h = im.size
    a = np.asarray(im).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    lum = rgb.mean(axis=2, keepdims=True)
    rgb = lum + (rgb - lum) * (1 - 0.6 * age)                      # desaturate
    paper = np.array([228, 222, 205], np.float32)
    rgb = rgb * (1 - 0.45 * age) + paper * (0.45 * age)             # sun-fade toward paper
    rgb *= (1 + lowfreq(rnd, w, h, 14, 0.07) + lowfreq(rnd, w, h, 4, 0.04))[..., None]   # crumple shading
    # folds: 1-2 thin lines
    for _ in range(rnd.randint(1, 2)):
        if rnd.random() < 0.5:
            y = rnd.randint(h // 4, 3 * h // 4)
            rgb[y:y + 2] *= 0.82
            rgb[y + 2:y + 4] *= 1.08
        else:
            x = rnd.randint(w // 4, 3 * w // 4)
            rgb[:, x:x + 2] *= 0.82
            rgb[:, x + 2:x + 4] *= 1.08
    if fresh:  # wet wheat paste: horizontal brush sheen + bubbles
        st = lowfreq(rnd, w, h, 3, 1.0)
        st = np.asarray(Image.fromarray(((st + 1) * 127).astype(np.uint8)).resize((w // 12, h)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 127 - 1
        rgb += np.clip(st, 0, 1)[..., None] * 38
    rgb = np.clip(rgb, 0, 255)
    # torn corners / edges
    m = Image.fromarray(al.astype(np.uint8))
    d = ImageDraw.Draw(m)
    for _ in range(rnd.choice([0, 1, 1, 2]) + (1 if age > 0.5 else 0)):
        cx, cy = rnd.choice([0, w]), rnd.choice([0, h])
        r = rnd.randint(int(0.06 * w), int(0.2 * w))
        pts = []
        for k in range(9):
            ang = (k / 8) * math.pi / 2 + (0 if cx == 0 else math.pi / 2) + (0 if cy == 0 else math.pi)
            rr = r * rnd.uniform(0.55, 1.1)
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        d.polygon([(cx, cy)] + pts, fill=0)
    # ragged edge: tiny noise on alpha border
    ed = np.asarray(m).astype(np.float32)
    band = ed - np.asarray(m.filter(ImageFilter.MinFilter(9))).astype(np.float32)   # border band only
    ed = np.where((band > 0) & (lowfreq(rnd, w, h, 1.5, 1) < -0.35), 0, ed)
    m2 = Image.fromarray(ed.astype(np.uint8))
    inner = m2.filter(ImageFilter.MinFilter(5))
    rim = (np.asarray(m2).astype(np.float32) - np.asarray(inner).astype(np.float32)) / 255   # torn paper white rim
    rgb = rgb * (1 - rim[..., None]) + np.array([240, 236, 226], np.float32) * rim[..., None]
    out = np.dstack([rgb, np.asarray(m2)]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def sticker(d, rnd, x, y):
    r = rnd.randint(34, 60)
    kind = rnd.choice(["round", "tag", "stripe"])
    if kind == "round":
        c = rnd.choice(list(S.SPOT.values()))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c, outline=(250, 250, 250), width=4)
        d.ellipse([x - r // 2, y - r // 2, x + r // 2, y + r // 2], fill=(250, 250, 250))
    elif kind == "tag":
        d.rounded_rectangle([x - r * 1.5, y - r, x + r * 1.5, y + r], radius=8, fill=(250, 250, 250), outline=(200, 40, 40), width=5)
        d.rectangle([x - r * 1.5 + 5, y - r + 5, x + r * 1.5 - 5, y - r // 3], fill=(200, 40, 40))
        d.text((x, y + r // 3), rnd.choice(["Mimi", "Nino", "Lea", "Sam"]), font=S.font("PermanentMarker-Regular.ttf", r // 2 + 4), fill=(20, 20, 120), anchor="mm")
    else:
        c = rnd.choice(list(S.SPOT.values()))
        d.rounded_rectangle([x - r * 1.6, y - r // 2, x + r * 1.6, y + r // 2], radius=6, fill=c)
        for k in range(-3, 4):
            d.line([x + k * r // 2, y - r // 2, x + k * r // 2 + r // 3, y + r // 2], fill=(250, 250, 250), width=5)


def tag(layer, rnd):
    d = ImageDraw.Draw(layer)
    col = rnd.choice(INK)
    txt = rnd.choice(TAGS)
    f = S.font("PermanentMarker-Regular.ttf", rnd.randint(70, 150))
    t = Image.new("RGBA", (int(d.textlength(txt, font=f)) + 40, f.size + 60), (0, 0, 0, 0))
    td = ImageDraw.Draw(t)
    td.text((20, 14), txt, font=f, fill=col + (235,))
    td.line([(14, f.size + 30), (t.width - 20, f.size + 18 + rnd.randint(-8, 8))], fill=col + (235,), width=rnd.randint(4, 8))
    t = t.rotate(rnd.uniform(-14, 14), expand=True, resample=Image.BICUBIC)
    layer.alpha_composite(t, (rnd.randint(0, max(1, PX - t.width)), rnd.randint(PX // 3, max(PX // 3 + 1, PX - t.height))))


def piece(events, rnd, rendered):
    """events: ordered old -> new (last is on top); rendered: dict id -> RGB at design size."""
    canvas = Image.new("RGBA", (PX, PX), (0, 0, 0, 0))
    n = len(events)
    for i, ev in enumerate(events):
        top = i == n - 1
        fmt = rnd.choices(list(FORMATS), [3, 2, 2])[0] if not top else rnd.choice(["F4", "F4", "A1"])
        mw, mh = FORMATS[fmt]
        w, h = int(mw * PXM), int(mh * PXM)
        h = min(h, PX - 16)
        w = int(h * mw / mh)
        src = rendered[ev["id"]].resize((w, h), Image.LANCZOS).convert("RGBA")
        age = 0.0 if top else rnd.uniform(0.35, 0.95) * (1 - 0.5 * i / max(1, n))
        sh = age_sheet(src, rnd, age, fresh=top or age < 0.3)
        sh = sh.rotate(rnd.uniform(-2.5, 2.5), expand=True, resample=Image.BICUBIC)
        # spread layers across the cell: left/centre/right with overlap
        slot = (i / max(1, n - 1)) if n > 1 else 0.5
        x = int((PX - sh.width) * np.clip(slot + rnd.uniform(-0.25, 0.25), 0, 1))
        y = int((PX - sh.height) * np.clip(rnd.uniform(0, 1) if sh.height < PX - 40 else 0.5, 0, 1))
        # soft shadow under the new sheet edge
        shadow = Image.new("RGBA", sh.size, (0, 0, 0, 0))
        shadow.putalpha(sh.getchannel("A").point(lambda v: int(v * 0.35)))
        canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(3)), (x + 2, y + 3))
        canvas.alpha_composite(sh, (x, y))
    for _ in range(rnd.randint(0, 2)):
        tag(canvas, rnd)
    st = Image.new("RGBA", (PX, PX), (0, 0, 0, 0))
    for _ in range(rnd.choice([0, 1, 1, 2, 3])):
        sticker(ImageDraw.Draw(st), rnd, rnd.randint(80, PX - 80), rnd.randint(80, PX - 80))
    canvas.alpha_composite(st)
    # transparent pixels keep a neutral colour (no dark mip halos)
    a = np.asarray(canvas).copy()
    a[a[..., 3] == 0, :3] = (150, 145, 135)
    return Image.fromarray(a, "RGBA")
