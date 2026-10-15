"""Facade texture painters for lm.tile(). Each factory returns painter(d, de, x, y, w, h, rng, on, ix, iy)."""
import numpy as np
from lm import hexc, shade


def punched(wall, glass="#2b3a46", fw=0.46, fh=0.58, top=0.18, frame="#e8e4da", arch=False, shutter=None, sill="#d8d2c4",
            plinth=0.0, cornice=0.0, lit_col=(255, 205, 130), noise=6, bands=None, dark_glass_top="#4a6272"):
    """Punched window per module (one window centred), optional round arch, shutters, sill, cornice at the module top."""
    W, G, F = hexc(wall), hexc(glass), hexc(frame)

    def p(d, de, x, y, w, h, rng, on, ix, iy):
        d.rectangle([x, y, x + w, y + h], fill=shade(W, 1 + (rng.random() - 0.5) * noise / 100))
        if bands:
            d.rectangle([x, y + int(h * (1 - bands)), x + w, y + h], fill=shade(W, 0.92))
        ww, wh = int(w * fw), int(h * fh)
        x0, y0 = x + (w - ww) // 2, y + int(h * top)
        if shutter:
            sw = max(3, int(ww * 0.45)); S = hexc(shutter)
            d.rectangle([x0 - sw - 2, y0, x0 - 2, y0 + wh], fill=S); d.rectangle([x0 + ww + 2, y0, x0 + ww + sw + 2, y0 + wh], fill=S)
            for k in range(y0 + 3, y0 + wh, 4):
                d.line([x0 - sw - 2, k, x0 - 2, k], fill=shade(S, 0.8)); d.line([x0 + ww + 2, k, x0 + ww + sw + 2, k], fill=shade(S, 0.8))
        d.rectangle([x0 - 2, y0 - 2, x0 + ww + 2, y0 + wh + 2], fill=F)
        if arch:
            d.pieslice([x0 - 2, y0 - ww // 2 - 2, x0 + ww + 2, y0 + ww // 2 + 2], 180, 360, fill=F)
            d.rectangle([x0, y0, x0 + ww, y0 + wh], fill=G)
            d.pieslice([x0, y0 - ww // 2, x0 + ww, y0 + ww // 2], 180, 360, fill=G)
        else:
            d.rectangle([x0, y0, x0 + ww, y0 + wh], fill=G)
            d.rectangle([x0, y0, x0 + ww, y0 + int(wh * 0.3)], fill=hexc(dark_glass_top))
        d.line([x0 + ww // 2, y0 - (ww // 2 if arch else 0), x0 + ww // 2, y0 + wh], fill=F, width=2)
        d.line([x0, y0 + int(wh * 0.38), x0 + ww, y0 + int(wh * 0.38)], fill=F, width=2)
        d.rectangle([x0 - 4, y0 + wh + 2, x0 + ww + 4, y0 + wh + 5], fill=hexc(sill))
        if cornice:
            d.rectangle([x, y, x + w, y + int(h * cornice)], fill=shade(F, 0.92))
        if on:
            top_ = y0 - (ww // 2 if arch else 0)
            de.rectangle([x0 + 1, y0 + int(wh * 0.3), x0 + ww - 1, y0 + wh - 1], fill=lit_col)
            de.line([x0 + ww // 2, y0 + int(wh * 0.3), x0 + ww // 2, y0 + wh], fill=(0, 0, 0), width=2)
    return p


def ribbon(wall, glass="#33444f", band=0.5, y0=0.2, mull=2, mull_col="#cfd2d1", lit_col=(255, 210, 140), noise=5, slab=0.12):
    W, G = hexc(wall), hexc(glass)

    def p(d, de, x, y, w, h, rng, on, ix, iy):
        d.rectangle([x, y, x + w, y + h], fill=shade(W, 1 + (rng.random() - 0.5) * noise / 100))
        wy0, wy1 = y + int(h * y0), y + int(h * (y0 + band))
        d.rectangle([x, wy0, x + w, wy1], fill=G)
        d.rectangle([x, wy0, x + w, wy0 + int((wy1 - wy0) * 0.22)], fill=shade(G, 1.45))
        d.rectangle([x, y + int(h * (1 - slab)), x + w, y + h], fill=shade(W, 0.85))
        for k in range(mull):
            xx = x + int(w * k / mull); d.line([xx, wy0, xx, wy1], fill=hexc(mull_col), width=2)
        if on:
            for k in range(mull):
                if rng.random() < 0.8:
                    de.rectangle([x + int(w * k / mull) + 3, wy0 + int((wy1 - wy0) * 0.3), x + int(w * (k + 1) / mull) - 2, wy1 - 1], fill=lit_col)
    return p


def curtain(frame, glass_a, glass_b, mull=2, spandrel=0.28, spandrel_col=None, lit_col=(255, 225, 170), noise=10):
    """Glass curtain wall: spandrel strip + vision glass with colour variation between panes."""
    Fr, A, B = hexc(frame), hexc(glass_a), hexc(glass_b)
    S = hexc(spandrel_col) if spandrel_col else shade(A, 0.7)

    def p(d, de, x, y, w, h, rng, on, ix, iy):
        d.rectangle([x, y, x + w, y + h], fill=Fr)
        pw = w // mull
        for k in range(mull):
            t = rng.random(); g = tuple(int(A[i] * (1 - t) + B[i] * t) for i in range(3)) + (255,)
            gx0, gx1 = x + k * pw + 1, x + (k + 1) * pw - 1
            d.rectangle([gx0, y + int(h * spandrel), gx1, y + h - 2], fill=g)
            d.rectangle([gx0, y + int(h * spandrel), gx1, y + int(h * spandrel) + int(h * 0.18)], fill=shade(g, 1.25))
            d.rectangle([gx0, y, gx1, y + int(h * spandrel) - 1], fill=S)
            if on and rng.random() < 0.7:
                de.rectangle([gx0 + 1, y + int(h * spandrel) + 3, gx1 - 1, y + h - 4], fill=lit_col)
    return p
