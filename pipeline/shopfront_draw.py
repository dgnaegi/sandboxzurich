"""Drawing primitives for procedural shopfront textures (metres -> supersampled pixels).

A Cv holds four aligned planes: albedo (RGB), emissive mask (L, 255 = lit at night), height (L, 128 = flat wall)
and roughness (L). Used by gen_shopfronts.py; no game data involved.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import ROOT

S = 170  # supersampled px per metre (final texture: 12 m x 4 m squeezed into 512 x 512)
FONT = ROOT / "web" / "public" / "fonts" / "BarlowCondensed-Bold.ttf"
_rng = np.random.default_rng(11)


def P(v):
    return int(round(v * S))


def font(size_m):
    return ImageFont.truetype(str(FONT), max(6, P(size_m)))


class Cv:
    def __init__(self, w, h, wall=(215, 210, 200), grain=14):
        self.w, self.h = w, h
        pw, ph = P(w), P(h)
        small = _rng.normal(0, 1, (max(2, ph // 24), max(2, pw // 24)))
        n = np.asarray(Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8)).resize((pw, ph), Image.BICUBIC), np.float32) / 255 - 0.5
        a = np.clip(np.array(wall, np.float32)[None, None] + n[..., None] * grain, 0, 255).astype(np.uint8)
        self.im = Image.fromarray(a)
        self.m = Image.new("L", (pw, ph), 0)
        self.hh = Image.new("L", (pw, ph), 128)
        self.ro = Image.new("L", (pw, ph), 210)
        self.d = [ImageDraw.Draw(x) for x in (self.im, self.m, self.hh, self.ro)]

    def _all(self, fn, col, m, h, ro):
        fn(self.d[0], col)
        if m is not None:
            fn(self.d[1], m)
        if h is not None:
            fn(self.d[2], h)
        if ro is not None:
            fn(self.d[3], ro)

    def r(self, x0, y0, x1, y1, col, m=None, h=None, ro=None):
        self._all(lambda d, c: d.rectangle([P(x0), P(y0), P(x1) - 1, P(y1) - 1], fill=c), col, m, h, ro)

    def e(self, x0, y0, x1, y1, col, m=None, h=None):
        self._all(lambda d, c: d.ellipse([P(x0), P(y0), P(x1), P(y1)], fill=c), col, m, h, None)

    def ring(self, cx, cy, rad, col, w=0.03, m=None, h=None):
        self._all(lambda d, c: d.ellipse([P(cx - rad), P(cy - rad), P(cx + rad), P(cy + rad)], outline=c, width=max(1, P(w))), col, m, h, None)

    def line(self, pts, col, w=0.03, m=None, h=None):
        pp = [(P(x), P(y)) for x, y in pts]
        self._all(lambda d, c: d.line(pp, fill=c, width=max(1, P(w)), joint="curve"), col, m, h, None)

    def poly(self, pts, col, m=None, h=None):
        pp = [(P(x), P(y)) for x, y in pts]
        self._all(lambda d, c: d.polygon(pp, fill=c), col, m, h, None)

    def text(self, x, y, s, size, col, m=None, anchor="mm"):
        f = font(size)
        self._all(lambda d, c: d.text((P(x), P(y)), s, font=f, fill=c, anchor=anchor), col, m, None, None)

    def glow(self, x0, y0, x1, y1, col, m=200, blur=0.12):
        """soft light spill: blurred mask + albedo, drawn as a rounded blob."""
        for plane, c in ((self.im, col), (self.m, m)):
            layer = Image.new("L", plane.size, 0)
            ImageDraw.Draw(layer).ellipse([P(x0), P(y0), P(x1), P(y1)], fill=255)
            layer = layer.filter(ImageFilter.GaussianBlur(P(blur)))
            solid = Image.new(plane.mode, plane.size, c)
            plane.paste(solid, mask=layer.point(lambda v: v * 0.7))

    def reflect(self, x0, y0, x1, y1, a=0.2):
        """sky reflection over glass (albedo only): diagonal gradient + two streaks."""
        w, h = P(x1) - P(x0), P(y1) - P(y0)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        g = np.clip(1.0 - yy / h * 1.2, 0, 1) * a
        for off, wd in ((0.25, 0.04), (0.55, 0.09)):
            g += np.clip(1 - np.abs((xx + yy * 0.7) / w - off) / wd, 0, 1) * a * 0.9
        reg = np.asarray(self.im.crop((P(x0), P(y0), P(x1), P(y1))), np.float32)
        sky = np.array([170, 195, 220], np.float32)
        out = reg * (1 - g[..., None]) + sky * g[..., None]
        self.im.paste(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), (P(x0), P(y0)))

    def paste(self, sub, x, y, h=100, ro=60):
        self.im.paste(sub.im, (P(x), P(y)))
        self.m.paste(sub.m, (P(x), P(y)))
        self.hh.paste(Image.new("L", sub.im.size, h), (P(x), P(y)))
        self.ro.paste(Image.new("L", sub.im.size, ro), (P(x), P(y)))

    def finish(self, size=512):
        """-> (rgb, mask, normal+roughness) at size x size."""
        rs = lambda im, f=Image.LANCZOS: im.resize((size, size), f)
        rgb = rs(self.im.filter(ImageFilter.GaussianBlur(0.5)))
        mask = rs(self.m.filter(ImageFilter.GaussianBlur(1.0)), Image.BILINEAR)
        hf = np.asarray(rs(self.hh.filter(ImageFilter.GaussianBlur(3)), Image.BILINEAR), np.float32) / 255
        gy, gx = np.gradient(hf)
        nx = np.clip(-gx * 28, -0.9, 0.9)
        ny = np.clip(gy * 28, -0.9, 0.9)  # image y points down; texture "up" = -y
        nrm = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, np.asarray(rs(self.ro, Image.BILINEAR), np.float32) / 255], -1)
        return rgb, mask, Image.fromarray((nrm * 255).astype(np.uint8))
