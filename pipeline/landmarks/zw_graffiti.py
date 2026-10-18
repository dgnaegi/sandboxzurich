"""Zentralwaescherei wall paintings: procedural redraw (own drawings, no photo pixels) after photo reference.
Reads pipeline/overrides/zw_graffiti.json -> atlas 2048x1024. `python zw_graffiti.py` writes web/public/tex/zw_graffiti.webp (+ _half.webp).
Used by k4w4_zentralwaescherei.py via atlas() and uv(name, u0, u1) (u0/u1 = fractions along the wall)."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONTS = os.path.join(ROOT, "web", "public", "fonts") + "/"
CFG = json.load(open(os.path.join(ROOT, "pipeline", "overrides", "zw_graffiti.json")))
SS = 2   # supersampling


def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def font(n, s): return ImageFont.truetype(FONTS + n + ".ttf", int(s))
def mix(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def rnd(rng, seq): return seq[int(rng.integers(0, len(seq)))]


def word_mask(word, h, rng, fname, wild):
    """Mask of a word; wild=True: each letter rotated/jittered with overlapping tracking (interlocking wildstyle look)."""
    fn = font(fname, h); tmp = ImageDraw.Draw(Image.new("L", (1, 1))); track = -0.07 * h if wild else 0.0
    ws = [tmp.textlength(ch, font=fn) for ch in word]; tw = int(sum(ws) + track * len(word) + h * 0.9)
    m = Image.new("L", (tw, int(h * 1.9)), 0); x = h * 0.45
    for ch, w in zip(word, ws):
        l = Image.new("L", (int(h * 1.4), int(h * 1.9)), 0); ImageDraw.Draw(l).text((h * 0.7, h * 0.95), ch, font=fn, fill=255, anchor="mm")
        if wild: l = l.rotate(rng.uniform(-9, 9), resample=Image.BICUBIC, center=(h * 0.7, h * 0.95))
        dy = int(rng.uniform(-0.1, 0.1) * h) if wild else 0
        m.paste(255, (int(x - h * 0.7 + w / 2), dy), l) if False else m.paste(Image.new("L", l.size, 255), (int(x - h * 0.7 + w / 2), dy), l)
        x += w + track
    return m


def piece(im, cx, cy, word, h, c1, c2, rng, kind="wild", accent=(255, 255, 255), tilt=0.0):
    """kind: wild (3D wildstyle: thick outline, extrusion, gradient, highlight, stars) | chrome (bubble throw-up, silver gradient)"""
    chrome = kind == "chrome"; m = word_mask(word, h, rng, "ArchivoBlack-Regular" if chrome else "Anton-Regular", not chrome)
    if chrome: m = m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(h * 0.02)).point(lambda v: 255 if v > 90 else 0)
    W_, H_ = m.size; pad = int(h * 0.25); lay = Image.new("RGBA", (W_ + pad * 2, H_ + pad * 2), (0, 0, 0, 0)); M = Image.new("L", lay.size, 0); M.paste(m, (pad, pad))
    ol = max(3, int(h * 0.09)); O = M.filter(ImageFilter.MaxFilter(ol * 2 + 1))
    d = ImageDraw.Draw(lay)
    if not chrome:   # background cloud + stars
        cl = Image.new("L", lay.size, 0); ImageDraw.Draw(cl).ellipse([pad * 0.2, H_ * 0.15, lay.size[0] - pad * 0.2, lay.size[1] - H_ * 0.1], fill=150)
        lay.paste(Image.new("RGBA", lay.size, accent + (255,)), (0, 0), cl.filter(ImageFilter.GaussianBlur(h * 0.18)))
    dep = int(h * (0.12 if chrome else 0.2)); dark = mix(c1, (10, 10, 20), 0.75)
    for k in range(dep, 0, -2):   # 3D block
        sh = O.transform(O.size, Image.AFFINE, (1, 0, -k, 0, 1, -k)); lay.paste(Image.new("RGBA", lay.size, dark + (255,)), (0, 0), sh)
    lay.paste(Image.new("RGBA", lay.size, (12, 12, 16, 255)), (0, 0), O)
    gr = np.zeros((lay.size[1], lay.size[0], 3), float); t = np.linspace(0, 1, lay.size[1])[:, None]
    if chrome:
        band = np.interp(t, [0, 0.42, 0.5, 0.6, 1], [235, 150, 60, 190, 245]); gr[:] = band[:, :, None] * np.array([0.93, 0.97, 1.0])
    else:
        gr[:] = (np.array(c1) * (1 - t) + np.array(c2) * t)[:, None, :] if False else (np.array(c1)[None, None, :] * (1 - t)[:, :, None] + np.array(c2)[None, None, :] * t[:, :, None])
    lay.paste(Image.fromarray(np.clip(gr, 0, 255).astype(np.uint8), "RGB").convert("RGBA"), (0, 0), M)
    ln = M.transform(M.size, Image.AFFINE, (1, 0, -ol * 0.9, 0, 1, -ol * 0.9)); rim = Image.composite(M, Image.new("L", M.size, 0), ImageChops.invert(ln)) if False else ImageChops.subtract(M, ln)
    lay.paste(Image.new("RGBA", lay.size, (255, 255, 255, 255)), (0, 0), rim.point(lambda v: 230 if v > 60 else 0))
    if not chrome:
        for _ in range(4):
            sx, sy = rng.uniform(pad, lay.size[0] - pad), rng.uniform(0.1, 0.9) * lay.size[1]; r = h * rng.uniform(0.07, 0.14)
            d.polygon([(sx, sy - r * 2), (sx + r * .5, sy - r * .5), (sx + r * 2, sy), (sx + r * .5, sy + r * .5), (sx, sy + r * 2), (sx - r * .5, sy + r * .5), (sx - r * 2, sy), (sx - r * .5, sy - r * .5)], fill=(255, 255, 255, 255), outline=(12, 12, 16, 255))
    if tilt: lay = lay.rotate(tilt, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(lay, (int(cx - lay.size[0] / 2), int(cy - lay.size[1] / 2)))


def tag(im, x, y, s, col, rng):
    """Marker tag: smooth looping stroke (round caps), crown/underline, a few drips."""
    d = ImageDraw.Draw(im); w = max(2, int(s * 0.1)); n = int(rng.integers(4, 8)); t = np.linspace(0, n * 1.7, n * 14)
    ph = rng.uniform(0, 6); xs = x + t * s * 0.22 + np.sin(t * 2.3 + ph) * s * 0.18; ys = y + np.cos(t * 1.7 + ph) * s * 0.4 - t * rng.uniform(-0.03, 0.03) * s
    pts = list(zip(xs, ys)); d.line(pts, fill=col, width=w, joint="curve")
    for px, py in pts[::7]: d.ellipse([px - w / 2, py - w / 2, px + w / 2, py + w / 2], fill=col)
    d.line([(xs[0], ys[0] + s * .6), (xs[-1] + s * .3, ys[-1] + s * .55)], fill=col, width=max(2, w - 1))
    for _ in range(int(rng.integers(0, 3))):
        k = int(rng.integers(0, len(pts))); px, py = pts[k]; L = rng.uniform(0.4, 1.4) * s; d.line([(px, py), (px, py + L)], fill=col, width=max(1, w // 2)); d.ellipse([px - w / 3, py + L - w / 3, px + w / 3, py + L + w / 3], fill=col)


def sticker(im, x, y, s, rng, pal):
    d = ImageDraw.Draw(im); c = rgb(rnd(rng, pal)); k = int(rng.integers(0, 3))
    if k == 0: d.rounded_rectangle([x, y, x + s * 1.4, y + s], radius=s * .2, fill=(245, 244, 238), outline=(20, 20, 24), width=max(1, int(s * .06))); d.rectangle([x + s * .12, y + s * .12, x + s * 1.28, y + s * .5], fill=c); d.rectangle([x + s * .12, y + s * .62, x + s * .9, y + s * .75], fill=(20, 20, 24))
    elif k == 1: d.ellipse([x, y, x + s, y + s], fill=c, outline=(250, 250, 245), width=max(2, int(s * .1))); d.ellipse([x + s * .3, y + s * .3, x + s * .7, y + s * .7], fill=(20, 20, 24))
    else: d.polygon([(x + s * .5, y), (x + s, y + s * .4), (x + s * .8, y + s), (x + s * .2, y + s), (x, y + s * .4)], fill=c, outline=(20, 20, 24)); d.rectangle([x + s * .3, y + s * .4, x + s * .7, y + s * .55], fill=(250, 250, 245))


HEAD = ["LIVE", "NIGHT", "KULTUR", "BAR", "DISCO", "FEST", "KINO", "JAZZ", "ZW", "PARTY", "SOUND", "OPEN"]


def poster(im, x, y, w, h, rng, pal):
    """Paste-up: light paper sheet (never dark), print-like content: headline type, flat-colour 'photo' shapes, bars; torn corner, soft shadow."""
    paper = rnd(rng, [(246, 244, 236), (238, 236, 226), (250, 232, 120), (250, 214, 222), (214, 236, 246), (252, 252, 250)])
    lay = Image.new("RGBA", (int(w) + 8, int(h) + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); W_, H_ = int(w), int(h)
    d.rectangle([0, 0, W_, H_], fill=paper + (255,))
    ink = (22, 22, 26) if sum(paper) > 560 else (200, 30, 40)
    acc = rgb(rnd(rng, pal)) if rng.random() < .7 else (230, 60, 50)
    k = int(rng.integers(0, 3))
    if k == 0:   # photo block (flat-colour face shapes) + headline
        d.rectangle([W_ * .08, H_ * .08, W_ * .92, H_ * .6], fill=acc); cx = W_ * .5
        for i in range(int(rng.integers(1, 4))):
            ox = (i - 0.5) * W_ * .25; d.ellipse([cx + ox - W_ * .09, H_ * .2, cx + ox + W_ * .09, H_ * .38], fill=(235, 190, 160)); d.rectangle([cx + ox - W_ * .12, H_ * .38, cx + ox + W_ * .12, H_ * .6], fill=ink)
        d.text((W_ / 2, H_ * .75), rnd(rng, HEAD), font=font("Anton-Regular", max(8, H_ * .2)), fill=ink, anchor="mm")
    elif k == 1:   # big type block
        d.text((W_ / 2, H_ * .35), rnd(rng, HEAD), font=font("Anton-Regular", max(8, min(H_ * .4, W_ * .5))), fill=acc if sum(acc) < 600 else ink, anchor="mm")
        d.rectangle([W_ * .08, H_ * .62, W_ * .92, H_ * .72], fill=ink)
        for j in range(3): d.rectangle([W_ * .08, H_ * (.78 + j * .06), W_ * (.5 + .4 * rng.random()), H_ * (.8 + j * .06)], fill=ink)
    else:   # abstract bars + circle
        d.ellipse([W_ * .15, H_ * .1, W_ * .85, H_ * .1 + W_ * .7], fill=acc)
        for j in range(5): d.rectangle([0, H_ * (.62 + j * .07), W_ * (.4 + .6 * rng.random()), H_ * (.65 + j * .07)], fill=ink)
    m = Image.new("L", lay.size, 255)   # torn corner / edge
    if rng.random() < .8:
        cx, cy = rnd(rng, [0, W_]), rnd(rng, [0, H_]); r = rng.uniform(.15, .4) * min(W_, H_); pts = [(cx + math.cos(a) * r * rng.uniform(.6, 1.1), cy + math.sin(a) * r * rng.uniform(.6, 1.1)) for a in np.linspace(0, 6.28, 9)]
        ImageDraw.Draw(m).polygon(pts, fill=0)
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), m))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 70), (3, 3), lay.getchannel("A")); im.alpha_composite(sh, (int(x), int(y))); im.alpha_composite(lay, (int(x), int(y)))


def paint(name, c):
    x, y, w, h = c["rect"]; W, H = w * SS, h * SS; rng = np.random.default_rng(c["seed"]); base = rgb(c["base"]); pal = c["palette"]; pl = [rgb(q) for q in pal]; mx = c["mix"]
    a = np.zeros((H, W, 3)); a[:] = base; a *= (1 + rng.normal(0, 0.025, (H, W, 1)))
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA"); d = ImageDraw.Draw(im)
    bright = [q for q in pl if sum(q) > 200 and q != (250, 250, 240)] or pl
    for _ in range(mx["fields"]):   # large colour fields (sprayed clouds)
        bx, by = rng.uniform(0, W), rng.uniform(0.1, .9) * H; rx, ry = rng.uniform(.5, 1.2) * W / max(4, mx["fields"] * .8), rng.uniform(.5, .9) * H / 2
        f = Image.new("L", im.size, 0); ImageDraw.Draw(f).ellipse([bx - rx, by - ry, bx + rx, by + ry], fill=255); im.paste(Image.new("RGBA", im.size, rnd(rng, bright) + (255,)), (0, 0), f.filter(ImageFilter.GaussianBlur(H * .03)))
    cw = W / max(1, mx["pieces"])
    for i in range(mx["pieces"]):
        word = rnd(rng, c["words"]); hh = H * rng.uniform(.5, .75); fn = font("Anton-Regular", hh); tw = ImageDraw.Draw(Image.new("L", (1, 1))).textlength(word, font=fn)
        if tw > cw * 1.1: hh *= cw * 1.1 / tw
        c1, c2, ac = [rnd(rng, bright) for _ in range(3)]
        piece(im, (i + .5) * cw + rng.uniform(-.05, .05) * cw, H * rng.uniform(.38, .62), word, hh * .75, c1, c2, rng, "wild", ac, rng.uniform(-3, 3))
    for i in range(mx["throw"]):
        word = rnd(rng, c["words"]); hh = H * rng.uniform(.3, .45); piece(im, rng.uniform(.1, .9) * W, H * rng.uniform(.55, .8), word, hh, (200, 200, 205), (200, 200, 205), rng, "chrome", tilt=rng.uniform(-4, 4))
    for _ in range(mx["posters"]):
        pw = rng.uniform(.07, .14) * W * (3 if W < 900 and H > 400 else 1) / (1.0 if mx["posters"] > 20 else 0.7); ph = min(pw * rng.uniform(1.2, 1.7), H * .6); poster(im, rng.uniform(-.02, 1) * (W - pw), rng.uniform(0, 1) * (H - ph), pw, ph, rng, pal)
    for _ in range(mx["stickers"]): sticker(im, rng.uniform(0, W), rng.uniform(0, H * .95), H * rng.uniform(.04, .08), rng, pal)
    for i in range(mx["tags"]):
        col = rnd(rng, [(18, 18, 22), (18, 18, 22), (200, 30, 36), (30, 60, 190), (18, 18, 22)]); tag(im, rng.uniform(0, W * .95), rng.uniform(.08, .9) * H, H * rng.uniform(.1, .22), col, rng)
    a = np.asarray(im.convert("RGB"), float); yy = np.linspace(0, 1, H)[:, None, None]; a *= 1 - 0.22 * np.clip((yy - 0.85) / 0.15, 0, 1)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(0.5))
    return im.resize((w, h), Image.LANCZOS)


def atlas():
    AW, AH = CFG["atlas"]; A = Image.new("RGB", (AW, AH), (200, 200, 200))
    for n, c in CFG["walls"].items(): A.paste(paint(n, c), tuple(c["rect"][:2]))
    return A


def uv(name, u0=0.0, u1=1.0, v0=0.0, v1=1.0, pad=0.002):
    """uv rect (u0, v0, u1, v1) of (a fraction of) a wall in glTF/model uv (v up)."""
    AW, AH = CFG["atlas"]; x, y, w, h = CFG["walls"][name]["rect"]
    return ((x + w * u0) / AW + pad * 0.5, 1 - (y + h * v1) / AH + pad, (x + w * u1) / AW - pad * 0.5, 1 - (y + h * v0) / AH - pad)


if __name__ == "__main__":
    A = atlas(); out = os.path.join(ROOT, "web", "public", "tex"); os.makedirs(out, exist_ok=True)
    A.save(out + "/zw_graffiti.webp", quality=82); A.resize((1024, 512), Image.LANCZOS).save(out + "/zw_graffiti_half.webp", quality=80)
    print("atlas", A.size, [os.path.getsize(out + f"/zw_graffiti{s}.webp") // 1024 for s in ("", "_half")], "KB")
