"""Procedural PBR facade layers (albedo, mask, normal, rough), 1024^2 each, fully own generation.

Facade layer = 12 m x 12.8 m (4 axes x 4 floors a 3.2 m), tileable in x and y.
Shop layer   = 12 m x 4 m ground floor, tileable in x, painted on a square canvas (3x vertical stretch).
Output: data/build/facades/<name>_{albedo,mask,normal,rough}.png + layers.json,
preview/facades_sheet.jpg.  Usage: .venv/bin/python pipeline/gen_facades.py [name ...]
Mask: 255 = plaster that the game tints per house; glass, shutters, stone, wood, brick = 0.
Normal: tangent space, OpenGL (+Y up).  Height is modelled in metres, so relief is physically scaled.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "build" / "facades"  # sources only; gen_textures.py packs them into the atlas
S = 1024
F32 = np.float32
STONE = np.array([0.70, 0.67, 0.62], F32)
NK = 0.6  # normal strength


# ---------------------------------------------------------------- noise / math
def fblur(a, sx, sy=None):
    """Gaussian blur with wrap-around (tileable); sigma in pixels."""
    sy = sx if sy is None else sy
    if a.ndim == 3:
        return np.stack([fblur(a[..., i], sx, sy) for i in range(a.shape[2])], -1)
    ky = np.fft.fftfreq(a.shape[0])[:, None]
    kx = np.fft.rfftfreq(a.shape[1])[None, :]
    g = np.exp(-2 * np.pi ** 2 * ((kx * sx) ** 2 + (ky * sy) ** 2))
    return np.fft.irfft2(np.fft.rfft2(a) * g, s=a.shape).astype(F32)


def noise(rng, sx, sy=None):
    a = fblur(rng.standard_normal((S, S)).astype(F32), sx, sy)
    return ((a - a.mean()) / (a.std() + 1e-9)).astype(F32)


def sstep(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return np.asarray(a, F32) * (1 - t) + np.asarray(b, F32) * t


def cells(rng, n, jit=0.35, rmin=0.38, rmax=0.5):
    """Jittered-grid domes (pebbles) tileable; returns (dome 0..1, random id)."""
    g = S / n
    cx = (np.arange(n)[None, :] + .5 + rng.uniform(-jit, jit, (n, n))) * g
    cy = (np.arange(n)[:, None] + .5 + rng.uniform(-jit, jit, (n, n))) * g
    rad = rng.uniform(rmin, rmax, (n, n)) * g
    ids = rng.random((n, n))
    py, px = np.mgrid[0:S, 0:S] + .5
    pi, pj = (py // g).astype(int), (px // g).astype(int)
    best = np.zeros((S, S), F32)
    bid = np.zeros((S, S), F32)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ii, jj = (pi + di) % n, (pj + dj) % n
            cxu = cx[ii, jj] + ((pj + dj) // n) * S
            cyu = cy[ii, jj] + ((pi + di) // n) * S
            d = np.hypot(px - cxu, py - cyu) / rad[ii, jj]
            dome = np.sqrt(np.clip(1 - d * d, 0, 1)).astype(F32)
            up = dome > best
            best = np.where(up, dome, best)
            bid = np.where(up, ids[ii, jj], bid)
    return best, bid


# ---------------------------------------------------------------- canvas
class C:
    def __init__(s, wm, hm, seed):
        s.wm, s.hm, s.px, s.py = wm, hm, S / wm, S / hm
        s.k = (s.px + s.py) / 2
        s.rng = r = np.random.default_rng(seed)
        s.n1, s.n2, s.n3 = noise(r, .8), noise(r, 3), noise(r, 30)
        s.stk = noise(r, 1.2, 50)
        s.alb = np.full((S, S, 3), .5, F32)
        s.h = np.zeros((S, S), F32)
        s.m = np.zeros((S, S), F32)
        s.r = np.full((S, S), .8, F32)
        s.dirt = np.zeros((S, S), F32)
        s.plaster = np.array([.8, .78, .72], F32)

    # patch in metres, wrapped
    def grid(s, x0, y0, x1, y1):
        c0, c1 = int(np.floor(x0 * s.px)), int(np.ceil(x1 * s.px))
        r0, r1 = int(np.floor(y0 * s.py)), int(np.ceil(y1 * s.py))
        ri, ci = np.arange(r0, r1), np.arange(c0, c1)
        Y, X = np.meshgrid((ri + .5) / s.py, (ci + .5) / s.px, indexing="ij")
        return np.ix_(ri % S, ci % S), X.astype(F32), Y.astype(F32)

    def aa(s, d):
        return np.clip(d * s.k + .5, 0, 1).astype(F32)

    def paint(s, ix, a, col=None, h=None, hadd=None, m=None, r=None, dirt=None, g=0.0, keep=False):
        a = np.asarray(a, F32)
        if col is not None:
            col = np.asarray(col, F32)
            if g:
                col = col * (1 + g * s.n1[ix][..., None] + .6 * g * s.n2[ix][..., None])
            s.alb[ix] = s.alb[ix] * (1 - a[..., None]) + col * a[..., None]
            if not keep:
                s.dirt[ix] *= 1 - .85 * a
        if h is not None:
            s.h[ix] = s.h[ix] * (1 - a) + h * a
        if hadd is not None:
            s.h[ix] += hadd * a
        if m is not None:
            s.m[ix] = s.m[ix] * (1 - a) + m * a
        if r is not None:
            s.r[ix] = s.r[ix] * (1 - a) + r * a
        if dirt is not None:
            s.dirt[ix] = np.clip(s.dirt[ix] + dirt * a, 0, 1)

    def box(s, x0, y0, x1, y1, **kw):
        ix, X, Y = s.grid(x0 - .02, y0 - .02, x1 + .02, y1 + .02)
        a = np.minimum(s.aa(np.minimum(X - x0, x1 - X)), s.aa(np.minimum(Y - y0, y1 - Y)))
        s.paint(ix, a, **kw)
        return ix, X, Y, a


def seg(X, Y, a, b, t):
    """Alpha of a thick line segment."""
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    u = np.clip(((X - ax) * dx + (Y - ay) * dy) / (dx * dx + dy * dy + 1e-9), 0, 1)
    d = np.hypot(X - ax - u * dx, Y - ay - u * dy)
    return np.clip((t / 2 - d) / .008 + .5, 0, 1).astype(F32)


def disc(X, Y, cx, cy, r):
    return np.clip((r - np.hypot(X - cx, Y - cy)) / .008 + .5, 0, 1).astype(F32)


def rectm(X, Y, x0, y0, x1, y1):
    e = .006
    return (np.clip((np.minimum(X - x0, x1 - X)) / e + .5, 0, 1) *
            np.clip((np.minimum(Y - y0, y1 - Y)) / e + .5, 0, 1)).astype(F32)


def over(img, mask, col, a=1.0):
    mk = (mask * a)[..., None]
    img[:] = img * (1 - mk) + np.asarray(col, F32) * mk


# ---------------------------------------------------------------- wall materials
def wall_plaster(c, col, rough=1.0, blot=1.0):
    col = np.asarray(col, F32)
    c.plaster = col
    n = c.n1 * .02 + c.n2 * .018 + c.n3 * .022 * blot
    c.alb[:] = col * (1 + n[..., None]) + c.n3[..., None] * np.array([.006, .004, -.004], F32)
    c.h[:] = (c.n1 * .0018 + c.n2 * .0030 + c.n3 * .004) * rough
    c.m[:] = 1
    c.r[:] = .86 + .05 * c.n1
    c.dirt[:] = .02 + .014 * np.clip(c.n3, 0, 2) + .035 * np.clip(c.stk - .8, 0, 2)


def wall_brick(c, cols, mortar=(.62, .6, .56), bw=.25, ch=.0752, aged=1.0):
    nc = int(round(c.hm / ch))
    nb = int(round(c.wm / bw))
    yy = (np.arange(S)[:, None] + .5) / S * nc
    course = np.floor(yy).astype(int)
    fy = yy - course
    xx = ((np.arange(S)[None, :] + .5) / S * nb + .5 * (course % 2)) % nb
    bi = np.floor(xx).astype(int) % nb
    fx = xx - np.floor(xx)
    r1 = c.rng.random((nc, nb)).astype(F32)
    r2 = c.rng.random((nc, nb)).astype(F32)
    t = r1[course % nc, bi]
    tone = lerp(cols[0], cols[1], t[..., None])
    dark = (r2[course % nc, bi] > .93)[..., None]
    tone = np.where(dark, np.asarray(cols[2], F32) * (.9 + .2 * t[..., None]), tone)
    tone = tone * (1 + .05 * c.n1[..., None] + .06 * c.n2[..., None])
    joint = ((fy < .16) | (fx < .045) | (fx > .985)).astype(F32)
    joint = fblur(joint, .6)
    mort = np.asarray(mortar, F32) * (1 + .1 * c.n2[..., None])
    c.alb[:] = tone * (1 - joint[..., None]) + mort * joint[..., None]
    c.h[:] = -.006 * joint + c.n1 * .0012 + c.n2 * .0012 + (t - .5) * .002
    c.m[:] = 0
    c.r[:] = .9 - .1 * joint
    c.dirt[:] = (.05 + .06 * np.clip(c.n3, 0, 2) + .1 * np.clip(c.stk - .6, 0, 2)) * aged
    c.plaster = np.asarray(cols[0], F32)


def wall_pebble(c, base, tones, n=128, grout=.9):
    dome, ids = cells(c.rng, n, .4, .36, .5)
    tone = np.zeros((S, S, 3), F32)
    ti = np.minimum((ids * len(tones)).astype(int), len(tones) - 1)
    tt = np.asarray(tones, F32)[ti]
    cem = np.asarray(base, F32) * (1 + .07 * c.n1[..., None] + .05 * c.n2[..., None])
    a = sstep(dome * 3.2)[..., None]
    tone = cem * (1 - a) + tt * (.85 + .3 * (dome[..., None])) * a
    c.alb[:] = tone
    c.h[:] = dome * .012 + c.n1 * .0006
    c.m[:] = 0
    c.r[:] = .93 - .08 * dome
    c.dirt[:] = .08 + .06 * np.clip(c.n3, 0, 2) + .12 * np.clip(c.stk - .6, 0, 2)
    c.plaster = np.asarray(base, F32)


def wall_panel(c, cols, pw=1.2, ph=.6, jw=.012, mask=0):
    nx, ny = int(round(c.wm / pw)), int(round(c.hm / ph))
    gx = (np.arange(S)[None, :] + .5) / S * nx
    gy = (np.arange(S)[:, None] + .5) / S * ny
    ix, iy = np.floor(gx).astype(int) % nx, np.floor(gy).astype(int) % ny
    rr = c.rng.random((ny, nx)).astype(F32)
    ci = (c.rng.random((ny, nx)) * len(cols)).astype(int)
    tone = np.asarray(cols, F32)[ci[iy, ix]] * (.93 + .1 * rr[iy, ix])[..., None]
    jx = np.minimum(gx - np.floor(gx), 1 - (gx - np.floor(gx))) * pw
    jy = np.minimum(gy - np.floor(gy), 1 - (gy - np.floor(gy))) * ph
    j = fblur(((jx < jw / 2) | (jy < jw / 2)).astype(F32), .7)
    c.alb[:] = (tone * (1 + .025 * c.n2[..., None] + .02 * c.n1[..., None])) * (1 - .55 * j[..., None])
    c.h[:] = -.008 * j + c.n1 * .0008
    c.m[:] = mask
    c.r[:] = .7 + .1 * c.n1 - .1 * j
    c.dirt[:] = .03 + .04 * np.clip(c.n3, 0, 2) + .1 * np.clip(c.stk - .6, 0, 2)
    c.plaster = np.asarray(cols[0], F32)


def wall_wood(c, col, bw=.14, x0=0, x1=None, y0=0, y1=None):
    """Vertical boards, painted into a region (default full)."""
    x1 = c.wm if x1 is None else x1
    y1 = c.hm if y1 is None else y1
    ix, X, Y = c.grid(x0, y0, x1, y1)
    f = (X / bw) % 1
    bi = np.floor(X / bw).astype(int) % 997
    rr = (np.sin(bi * 12.9898) * 43758.5453) % 1
    jt = np.minimum(f, 1 - f) * bw
    j = np.clip(1 - jt / .007, 0, 1)
    grain = c.stk[ix] * .045 + c.n1[ix] * .02
    tone = np.asarray(col, F32) * (.88 + .22 * rr[..., None]) * (1 + grain[..., None])
    a = np.ones(X.shape, F32)
    c.paint(ix, a, col=tone * (1 - .6 * j[..., None]), h=-.012 * j + c.stk[ix] * .0008, m=0, r=.75)


# ---------------------------------------------------------------- building elements
def band(c, yc, th, prot, col, m=0, shade=.12, y_off=0.0):
    """Horizontal full-width cornice / sill band, profile stepped; wrap-safe."""
    ix, X, Y = c.grid(0, yc - th / 2 - .35, c.wm, yc + th / 2 + .35)
    t = (Y - (yc - th / 2)) / th
    inb = ((t >= 0) & (t <= 1)).astype(F32)
    a = fblur(inb, .6, .6) if False else inb
    prof = np.where(t < .2, t / .2 * .35, np.where(t < .65, .35 + (t - .2) / .45 * .15, .5 + .5 * np.sin(np.clip((t - .65) / .35, 0, 1) * np.pi / 2)))
    shd = np.clip((Y - (yc + th / 2)) / .22, 0, 1)
    c.paint(ix, a, col=np.asarray(col, F32), hadd=prot * prof, m=m, r=.75, g=.03)
    c.paint(ix, np.exp(-shd * 3) * (Y > yc + th / 2) * c.aa(.4 - np.abs(Y - yc)) * 1.0, dirt=shade)
    c.paint(ix, (t < 0) * np.exp(np.clip(t, -1, 0) * th / .05) * .3, dirt=.05)


def ornament(c, yc, bh, col, accent=None, p=.5, prot=.022):
    """Jugendstil ribbon: wavy double ribbon with discs, framed by thin lines."""
    ix, X, Y = c.grid(0, yc - bh / 2 - .05, c.wm, yc + bh / 2 + .05)
    ph = 2 * np.pi * X / p
    amp = bh * .26
    w1 = yc + amp * np.sin(ph)
    w2 = yc - amp * np.sin(ph)
    rib = np.exp(-((Y - w1) / .02) ** 2) + np.exp(-((Y - w2) / .02) ** 2)
    dx = ((X + p / 2) % p) - p / 2
    dsc = np.clip(1 - np.hypot(dx, Y - yc) / (bh * .2), 0, 1)
    lines = np.exp(-((Y - (yc - bh / 2)) / .012) ** 2) + np.exp(-((Y - (yc + bh / 2)) / .012) ** 2)
    leaf = np.exp(-(((np.abs(dx) - p * .25) / .045) ** 2) - ((Y - yc - np.sign(dx) * amp * .0) / (bh * .12)) ** 2)
    hgt = rib * .012 + dsc ** .6 * .02 + lines * .014 + leaf * .014
    inb = (np.abs(Y - yc) < bh / 2 + .02).astype(F32)
    c.paint(ix, inb * .35, col=np.asarray(accent if accent is not None else c.plaster * .93, F32), m=1)
    shape = np.clip(rib + dsc * 1.4 + lines + leaf, 0, 1)
    c.paint(ix, shape * inb, col=np.asarray(col, F32), hadd=hgt * inb, m=1, g=.03)


def interior(c, X, Y, cx, y0, y1, w, kind):
    rng = c.rng
    t = np.clip((Y - y0) / (y1 - y0), 0, 1)[..., None]
    bases = [(.10, .10, .12), (.15, .12, .10), (.20, .18, .15), (.08, .10, .13), (.24, .22, .20)]
    base = np.asarray(bases[rng.integers(len(bases))], F32)
    img = base * (1.3 - .6 * t) * np.ones(X.shape + (3,), F32)
    hw = w / 2
    if kind == "lamp":
        g = np.exp(-(((X - cx) / (hw * .9)) ** 2) - (((Y - y0) / (y1 - y0) - .3) / .5) ** 2)[..., None]
        img = img * .5 + np.array([.62, .46, .26], F32) * g * (.7 + rng.random() * .4)
    elif kind in ("curtain", "veil"):
        f = 1.0 if kind == "veil" else rng.uniform(.25, .75)
        col = np.asarray([(.82, .80, .74), (.72, .74, .62), (.62, .40, .34), (.88, .88, .86), (.45, .5, .6)][rng.integers(5)], F32)
        fold = .82 + .18 * np.sin((X - cx) * 2 * np.pi / rng.uniform(.07, .12) + rng.random() * 6)
        side = np.abs(X - cx) > hw * (1 - f)
        # gathered curtain hangs slightly shorter at one side
        cover = side * (Y < y1 - (0 if kind == "veil" else rng.uniform(0, .5)))
        a = (.95 if kind != "veil" else .55) * cover
        img = img * (1 - a[..., None]) + col * fold[..., None] * a[..., None]
    elif kind == "blind":
        lo = rng.uniform(.25, .95)
        slat = .8 + .12 * np.sin((Y - y0) * 2 * np.pi / .03)
        cov = (((Y - y0) / (y1 - y0)) < lo).astype(F32)[..., None]
        col = np.asarray([(.78, .78, .74), (.62, .6, .55), (.85, .84, .8)][rng.integers(3)], F32)
        img = img * (1 - cov) + col * slat[..., None] * cov
    elif kind == "plant":
        for _ in range(3):
            px_, py_ = cx + rng.uniform(-hw * .7, hw * .7), y1 - rng.uniform(.0, .25)
            blob = np.exp(-(((X - px_) / .13) ** 2) - (((Y - py_) / .28) ** 2))[..., None]
            img = img * (1 - blob) + np.array([.12, .26, .1], F32) * (1 + .5 * c.rng.random()) * blob
    return img


def reflection(X, Y, rng, x0, y0, y1):
    t = np.clip((Y - y0) / (y1 - y0), 0, 1)[..., None]
    top = np.array([.44, .60, .80], F32) * rng.uniform(.9, 1.15)
    bot = np.array([.82, .86, .88], F32)
    sky = top * (1 - t) + bot * t
    u = (X - x0) * .9 + (Y - y0) * .7 + rng.uniform(0, 2)
    streak = np.exp(-(((u % 1.4) - .5) / .12) ** 2)[..., None]
    sky = sky + .22 * streak
    # opposite buildings / trees low in the pane
    for _ in range(2):
        bx, bw = x0 + rng.uniform(0, 1.2), rng.uniform(.2, .6)
        top_y = y0 + (y1 - y0) * rng.uniform(.55, .9)
        m = rectm(X, Y, bx, top_y, bx + bw, y1 + .1)[..., None]
        sky = sky * (1 - m * .55) + np.array([.25, .27, .28], F32) * m * .55
    return sky


def window(c, cx, y1, w, hh, **o):
    P = dict(arch=0, cols=1, rows=2, bar=.026, frame=(.9, .9, .87), fw=.06, d=.16, rw=.07, sur=0.0,
             surc=None, surm=1, sill=True, shut=None, closed=False, dirt=.24, flowers=0, cap=None,
             content=None, refl=.34, pane=None, sillcol=None)
    P.update(o)
    rng = c.rng
    y0 = y1 - hh
    sur = P["sur"]
    mx = (w / 2 + sur + .1) if P["shut"] else sur + .35
    ix, X, Y = c.grid(cx - w / 2 - mx - .1, y0 - sur - .45 - (.7 if P["cap"] else 0), cx + w / 2 + mx + .1, y1 + 1.5)
    arch = P["arch"]
    # surround (Fasche)
    if sur > 0:
        top = sur
        ds = sdr(X, Y, cx, y0 - top, y1 + (0 if P["sill"] else sur), w + 2 * sur, arch)
        sc = P["surc"] if P["surc"] is not None else np.clip(c.plaster * 1.07, 0, 1)
        c.paint(ix, c.aa(ds), col=sc, hadd=.02, m=P["surm"], g=.02)
    # cap / Verdachung
    if P["cap"]:
        ww = w / 2 + sur + .1
        yb = y0 - sur
        if P["cap"] == "flat":
            c.box(cx - ww, yb - .2, cx + ww, yb - .02, col=STONE * 1.02, hadd=.05, m=0, g=.03)
        else:
            tri = np.clip((yb - .02 - Y) / .0001, 0, 1) * 0
            hgt_ = .28
            inside = (Y < yb - .02) & (Y > yb - .02 - hgt_ * (1 - np.abs(X - cx) / ww))
            c.paint(ix, c.aa(np.minimum(hgt_ * (1 - np.abs(X - cx) / ww) - (yb - .02 - Y), yb - .02 - Y)) * (np.abs(X - cx) < ww),
                    col=STONE * 1.03, hadd=.05, m=0, g=.03)
    # opening + reveal ramp
    d = sdr(X, Y, cx, y0, y1, w, arch)
    ao = c.aa(d)
    t = sstep(d / P["rw"])
    ramp = -P["d"] * t
    c.paint(ix, ao, hadd=ramp)
    ring = ao * (1 - sstep((d - P["rw"] * .3) / P["rw"]))
    c.alb[ix] *= (1 - .3 * ring[..., None])
    c.alb[ix] = np.where((ao > .5)[..., None] & (t[..., None] < 1), c.alb[ix] * .82, c.alb[ix])
    c.dirt[ix] *= 1 - ao * .9
    # frame + glass
    fo = P["rw"]
    af = c.aa(d - fo)
    ag = c.aa(d - fo - P["fw"])
    fcol = np.asarray(P["frame"], F32)
    c.paint(ix, af, col=fcol * (1 + .03 * c.n1[ix][..., None]), h=-P["d"] + .015, m=0, r=.45)
    kind = P["content"] or ["dark", "curtain", "blind", "lamp", "plant", "veil"][int(rng.choice(6, p=[.3, .22, .15, .1, .08, .15]))]
    room = interior(c, X, Y, cx, y0, y1, w, kind)
    ref = reflection(X, Y, rng, cx - w / 2, y0, y1)
    ra = P["refl"] * (.8 + .5 * (1 - np.clip((Y - y0) / (y1 - y0), 0, 1)))[..., None]
    glass = room * (1 - ra) + ref * ra
    c.paint(ix, ag, col=glass, h=-P["d"] - .01, m=0, r=.06)
    # bars
    gx0, gx1 = cx - w / 2 + fo + P["fw"], cx + w / 2 - fo - P["fw"]
    gy0, gy1 = y0 + fo + P["fw"], y1 - fo - P["fw"]
    bar = np.zeros_like(X)
    for i in range(1, P["cols"]):
        bar = np.maximum(bar, np.clip((P["bar"] / 2 - np.abs(X - (gx0 + (gx1 - gx0) * i / P["cols"]))) / .006 + .5, 0, 1))
    for i in range(1, P["rows"]):
        bar = np.maximum(bar, np.clip((P["bar"] / 2 - np.abs(Y - (gy0 + (gy1 - gy0) * i / P["rows"]))) / .006 + .5, 0, 1))
    c.paint(ix, bar * ag, col=fcol, h=-P["d"] + .012, r=.45)
    # sill + drip stain
    if P["sill"]:
        sw = w / 2 + sur + .05
        sc = P["sillcol"] if P["sillcol"] is not None else STONE * rng.uniform(.95, 1.04)
        c.paint(ix, rectm(X, Y, cx - sw, y1 + sur * 0 - .005, cx + sw, y1 + .075), col=sc, hadd=.06, m=0, r=.7, g=.03)
        below = np.clip((Y - (y1 + .075)) / 1.3, 0, 1)
        streak = np.clip(.45 + .5 * c.stk[ix], 0, 1.2) ** 1.4
        fade = c.aa(w / 2 + sur - np.abs(X - cx)) * (Y > y1 + .075)
        c.paint(ix, fade * (np.exp(-below * 2.8) * (.35 + .65 * streak)), dirt=P["dirt"])
        c.paint(ix, fade * np.exp(-(Y - y1 - .075) / .05) * (Y > y1 + .075), dirt=.14)
    # shutters
    if P["shut"]:
        scol = np.asarray(P["shut"], F32)
        lw = w / 2 + (sur if P["closed"] else 0) - (.0 if P["closed"] else 0)
        for sgn in (-1, 1):
            if P["closed"]:
                xa, xb = (cx - w / 2 - sur, cx - .01) if sgn < 0 else (cx + .01, cx + w / 2 + sur)
            else:
                xa, xb = (cx - w / 2 - sur - lw * .98, cx - w / 2 - sur) if sgn < 0 else (cx + w / 2 + sur, cx + w / 2 + sur + lw * .98)
            a = rectm(X, Y, xa, y0 - .02, xb, y1 + .02)
            sl = ((Y - y0) / .036) % 1
            slat = np.sin(sl * np.pi)
            edge = np.minimum(np.minimum(X - xa, xb - X), np.minimum(Y - y0, y1 - Y))
            frame_ = (edge < .045)
            tone = scol * (.8 + .22 * slat[..., None] * (~frame_[..., None]) + .1 * frame_[..., None]) * (1 + .05 * c.n1[ix][..., None])
            gap = P["closed"] * (sl < .18) * ~frame_
            tone = tone * np.where(gap[..., None], .35, 1)
            c.paint(ix, a, col=tone, hadd=.035 + .005 * slat * (~frame_), m=0, r=.6, keep=True)
            c.paint(ix, a * 0 + c.aa(.04 - np.abs(X - (xa if sgn > 0 else xb))) * a, dirt=0)
            # shadow below / beside
        c.paint(ix, fade_shadow(X, Y, cx, w, sur, y0, y1, lw), dirt=.1)
    # flowers
    if P["flowers"]:
        bx0, bx1 = cx - w / 2 - .02, cx + w / 2 + .02
        c.box(bx0, y1 - .17, bx1, y1 + .0, col=(.55, .3, .2), hadd=.1, m=0)
        n = int(w * 14)
        for _ in range(n):
            px_ = rng.uniform(bx0, bx1)
            py_ = y1 - .17 - rng.uniform(0, .17)
            r_ = rng.uniform(.05, .09)
            g = disc(X, Y, px_, py_, r_)
            col = np.array([.13, .3, .1], F32) * rng.uniform(.7, 1.3)
            c.paint(ix, g, col=col, hadd=.06, m=0, r=.9, keep=True)
            if rng.random() < .55:
                fc = [(.8, .1, .12), (.9, .5, .6), (.95, .9, .9), (.9, .75, .2), (.55, .2, .6)][rng.integers(5)]
                c.paint(ix, disc(X, Y, px_ + rng.uniform(-.03, .03), py_ + rng.uniform(-.03, .03), rng.uniform(.018, .03)), col=fc, hadd=.02, keep=True)


def fade_shadow(X, Y, cx, w, sur, y0, y1, lw):
    return (np.exp(-np.maximum(0, np.abs(X - cx) - w / 2 - sur - lw) / .05) * 0).astype(F32)


def sdr(X, Y, cx, y0, y1, w, arch):
    hw = w / 2
    d = np.minimum(hw - np.abs(X - cx), y1 - Y)
    if arch:
        cya = y0 + hw
        d = np.minimum(d, np.where(Y < cya, hw - np.hypot(X - cx, Y - cya), Y - y0))
    else:
        d = np.minimum(d, Y - y0)
    return d


def balcony(c, cx, yf, w, kind, col=None, rail=(.16, .17, .18), flowers=False):
    """Slab at floor line yf, railing above it."""
    col = STONE * .96 if col is None else np.asarray(col, F32)
    x0, x1 = cx - w / 2, cx + w / 2
    # shade on wall behind and below
    ix, X, Y = c.grid(x0 - .1, yf - 1.2, x1 + .1, yf + .9)
    c.paint(ix, c.aa(np.minimum(X - x0 + .05, x1 + .05 - X)) * np.exp(-np.clip(Y - yf - .22, 0, 5) / .22) * (Y > yf), dirt=.3)
    c.box(x0, yf - .02, x1, yf + .2, col=col, hadd=.16, m=0, r=.8, g=.03)
    c.paint(ix, rectm(X, Y, x0, yf + .17, x1, yf + .2), dirt=.0)
    top = yf - 1.0
    if kind == "bars":
        ix2, X2, Y2 = c.grid(x0, top, x1, yf)
        pitch = .115
        a = np.clip((.009 - np.abs(((X2 - x0) % pitch) - pitch / 2 + 0.0 * 1) + 0.0) / .006 + .5, 0, 1)
        a = np.clip((.009 - np.abs(((X2 - x0) % pitch) - pitch / 2)) / .006 + .5, 0, 1) * (Y2 > top)
        c.paint(ix2, c.aa(.05 - 0) * 0 + a * (Y2 < yf), col=rail, hadd=.12, m=0, r=.5)
        # dark backing (view into balcony)
        c.paint(ix2, np.minimum(c.aa(np.minimum(X2 - x0, x1 - X2)), 1) * .18 * (Y2 < yf), dirt=.0)
        c.alb[ix2] *= 1 - .12 * (Y2 < yf)[..., None]
        c.box(x0, top - .02, x1, top + .035, col=rail, hadd=.14, m=0, r=.5)
        c.box(x0, yf - .1, x1, yf - .06, col=rail, hadd=.12, m=0, r=.5)
        c.box(x0, top, x0 + .035, yf, col=rail, hadd=.13, m=0)
        c.box(x1 - .035, top, x1, yf, col=rail, hadd=.13, m=0)
    elif kind == "solid":
        c.box(x0, yf - .95, x1, yf - .02, col=col * 1.04, hadd=.13, m=0, r=.85, g=.04)
        c.box(x0 - .02, yf - 1.0, x1 + .02, yf - .93, col=col * .98, hadd=.15, m=0)
    elif kind == "glass":
        ix2, X2, Y2 = c.grid(x0, top, x1, yf)
        refl = reflection(X2, Y2, c.rng, x0, top, yf)
        a = rectm(X2, Y2, x0, top, x1, yf - .03) * .55
        c.paint(ix2, a, col=refl * .8 + np.array([.1, .16, .15], F32) * .3, hadd=.1, m=0, r=.08, keep=True)
        c.box(x0, top - .03, x1, top + .02, col=(.55, .56, .58), hadd=.13, m=0, r=.3)
        for i in range(0, int(w / .9) + 1):
            c.box(x0 + i * w / max(1, int(w / .9)) - .015, top, x0 + i * w / max(1, int(w / .9)) + .015, yf, col=(.5, .5, .52), hadd=.12, m=0, r=.3)
    if flowers:
        for _ in range(int(w * 9)):
            px_, py_ = c.rng.uniform(x0, x1), top - c.rng.uniform(0, .17)
            ixf, Xf, Yf = c.grid(px_ - .15, py_ - .15, px_ + .15, py_ + .15)
            c.paint(ixf, disc(Xf, Yf, px_, py_, c.rng.uniform(.05, .09)), col=np.array([.13, .3, .1], F32) * c.rng.uniform(.7, 1.3), hadd=.06, m=0, r=.9, keep=True)
            if c.rng.random() < .5:
                fc = [(.8, .1, .12), (.9, .5, .6), (.95, .9, .9), (.9, .5, .2)][c.rng.integers(4)]
                c.paint(ixf, disc(Xf, Yf, px_, py_, .025), col=fc, hadd=.02, keep=True)


# ---------------------------------------------------------------- finishing
def finish(c, name, ao_s=1.0, nk=NK):
    h = fblur(c.h, .5)
    d1 = np.clip(fblur(h, c.k * .04) - h, 0, None)
    d2 = np.clip(fblur(h, c.k * .22) - h, 0, None)
    A = np.clip(.55 * np.clip(d1 / .045, 0, 1) + .4 * np.clip(d2 / .10, 0, 1), 0, .85) * ao_s
    alb = c.alb * (1 - .75 * A[..., None])
    D = np.clip(c.dirt, 0, .8)[..., None]
    alb = alb * (1 - .62 * D) + np.array([.17, .15, .13], F32) * .62 * D * .5
    alb = np.clip(alb, 0, 1)
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2 * c.px
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2 * c.py
    n = np.stack([-gx * nk, gy * nk, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    rough = np.clip(c.r * (1 - .25 * D[..., 0]) + .05 * D[..., 0], .03, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    sv = lambda a, mode, suf: Image.fromarray(a, mode).save(OUT / f"{name}_{suf}.png", compress_level=6)
    sv((alb * 255 + .5).astype(np.uint8), "RGB", "albedo")
    sv((np.clip(c.m, 0, 1) * 255 + .5).astype(np.uint8), "L", "mask")
    sv(((n * .5 + .5) * 255 + .5).astype(np.uint8), "RGB", "normal")
    sv((rough * 255 + .5).astype(np.uint8), "L", "rough")


# ---------------------------------------------------------------- facade builders
def parapet(c, fl_lines, col, y_from=.95, y_to=.05):
    for Lf in fl_lines:
        c.box(0, Lf - y_from, c.wm, Lf + y_to, col=col, hadd=.025, m=0, g=.03, r=.8)


def standard(name, seed, P):
    c = C(12, 12.8, seed)
    rng = c.rng
    P["wall"](c)
    lines = [(i + 1) * 3.2 for i in range(4)]
    if P.get("parapet"):
        parapet(c, lines, **P["parapet"])
    gs = P.get("gs")
    if gs:
        for Lf in lines:
            band(c, Lf, gs["th"], gs["prot"], gs["col"], m=gs.get("m", 0))
    if P.get("orn"):
        for Lf in lines:
            ornament(c, Lf - 2.88, .24, **P["orn"])
    for jx in P.get("joints", []):
        for xx in jx:
            c.box(xx - .01, 0, xx + .01, c.hm, col=(.25, .25, .24), hadd=-.012, m=0, keep=True)
    bal = P.get("bal")
    W = P["win"]
    for fl in range(4):
        Lf = lines[fl]
        for ax in range(4):
            cx = (ax + .5) * 3 + P.get("shift", 0) * (fl % 2)
            isbal = bal and fl in bal["floors"] and ax in bal["axes"]
            kw = dict(W)
            kw.pop("w"), kw.pop("h")
            if P.get("shut") and rng.random() < P["shut"].get("p", .7):
                kw["shut"] = P["shut"]["col"]
                kw["closed"] = bool(rng.random() < P["shut"].get("closed", .1))
            if kw.get("flowers") is not None:
                kw["flowers"] = int(rng.random() < kw["flowers"])
            if P.get("altwin") and (fl + ax) % P["altwin"].get("mod", 2) == P["altwin"].get("eq", 0):
                kw2 = {"w": W["w"], "h": W["h"], **P["altwin"]["kw"]}
                window(c, cx, Lf - P.get("sillh", .9), kw2.pop("w"), kw2.pop("h"), **{**kw, **kw2})
                continue
            if isbal:
                dw = bal.get("dw", 1.0)
                dk = {**kw, "shut": None, "flowers": 0, "sill": False, "content": rng.choice(["veil", "curtain", "dark"])}
                dk.update(bal.get("dkw", {}))
                window(c, cx, Lf - .03, dw, bal.get("dh", 2.15), **dk)
                if bal.get("side"):  # window beside door
                    pass
                balcony(c, cx, Lf, bal["w"], bal["kind"], col=bal.get("col"), rail=bal.get("rail", (.16, .17, .18)),
                        flowers=bool(rng.random() < bal.get("flowers", .5)))
            elif P.get("twin"):
                for sg in (-1, 1):
                    window(c, cx + sg * P["twin"], Lf - P.get("sillh", .9), W["w"], W["h"], **kw)
            else:
                window(c, cx, Lf - P.get("sillh", .9), W["w"], W["h"], **kw)
    return c


def curtain(name, seed, tint, spandrel, mull, nx=8, fins=0, louvres=False, hband=False):
    c = C(12, 12.8, seed)
    rng = c.rng
    X, Y = np.meshgrid((np.arange(S) + .5) / c.px, (np.arange(S) + .5) / c.py)
    X, Y = X.astype(F32), Y.astype(F32)
    cloud = noise(rng, 80, 18)
    t = .5 + .5 * np.cos(2 * np.pi * (Y / 12.8 + .08))
    top, bot = np.array([.40, .55, .74], F32), np.array([.74, .80, .84], F32)
    sky = top * (1 - t[..., None]) + bot * t[..., None]
    sky = sky + np.clip(cloud - .5, 0, 1)[..., None] * .14
    sk = np.zeros((S, S), F32)  # opposite skyline: rectangular blocks, tileable
    xs = 0.0
    while xs < 12:
        bw_ = rng.uniform(.8, 2.6)
        bh_ = rng.uniform(.8, 3.4)
        for oy in (3.2, 9.6):
            sk = np.maximum(sk, rectm(X, Y, xs, oy - bh_, min(xs + bw_, 12), oy + .05))
        xs += bw_ + rng.uniform(0, .4)
    sk = sk * (.5 + .08 * noise(rng, 40, 40))
    sky = sky * (1 - sk[..., None] * .8) + np.array([.17, .2, .22], F32) * sk[..., None] * .8
    tt = np.asarray(tint, F32)
    sky = sky * (tt / tt.mean()) ** .6 * .85
    c.alb[:] = sky
    c.r[:] = .06
    c.m[:] = 0
    gw = 12 / nx
    for fl in range(4):
        Lf = (fl + 1) * 3.2
        for ax in range(nx):
            x0 = ax * gw
            ix, Xp, Yp = c.grid(x0, Lf - 3.2, x0 + gw, Lf)
            # inside blinds in some panes
            if rng.random() < .35:
                inner = interior(c, Xp, Yp, x0 + gw / 2, Lf - 3.2, Lf - 1.0, gw, rng.choice(["blind", "blind", "lamp"]))
                a = rectm(Xp, Yp, x0 + .06, Lf - 3.2 + .1, x0 + gw - .06, Lf - 1.05) * .55
                c.paint(ix, a, col=inner * .6 + c.alb[ix] * .4, keep=True)
            v = rng.uniform(.9, 1.1)
            c.alb[ix] *= np.where(((Yp > Lf - 3.2 + .1) & (Yp < Lf - 1.05))[..., None], v, 1)
        # spandrel
        c.box(0, Lf - 1.0, 12, Lf + .08, col=spandrel, h=-.02, m=0, r=.2)
        # transoms and slab edge
        c.box(0, Lf - 1.04, 12, Lf - .98, col=mull, hadd=.06, m=0, r=.35)
        c.box(0, Lf + .08, 12, Lf + .13, col=mull, hadd=.06, m=0, r=.35)
        c.box(0, Lf - 3.2 + .1, 12, Lf - 3.2 + .14, col=mull, hadd=.06, m=0, r=.35)
        if louvres:
            for k in range(7):
                yy = Lf - 3.2 + .35 + k * .12
                c.box(0, yy, 12, yy + .03, col=np.asarray(mull) * .7, hadd=.12, m=0, r=.4, keep=True)
    for ax in range(nx):
        c.box(ax * gw - .03, 0, ax * gw + .03, 12.8, col=mull, hadd=.08, m=0, r=.35)
    if fins:
        for ax in range(nx):
            c.box(ax * gw - .05, 0, ax * gw + .05, 12.8, col=np.asarray(mull) * .5, hadd=fins, m=0, r=.5, keep=True)
    c.dirt[:] = .02 + .03 * np.clip(c.stk, 0, 2)
    c.h += c.n1 * .0003
    return c


def hband(name, seed, wall, glass_tint, pier):
    """Concrete precast office: horizontal ribbon windows between white bands."""
    c = C(12, 12.8, seed)
    wall_panel(c, wall, pw=1.5, ph=1.6, jw=.014)
    rng = c.rng
    for fl in range(4):
        Lf = (fl + 1) * 3.2
        y1, y0 = Lf - .9, Lf - 2.4
        ix, X, Y = c.grid(0, y0 - .3, 12, y1 + 1.4)
        d = np.minimum(Y - y0, y1 - Y)
        ao = c.aa(d)
        c.paint(ix, ao, hadd=-.2 * sstep(d / .08))
        c.alb[ix] *= 1 - .3 * (ao * (1 - sstep(d / .1)))[..., None]
        ref = reflection(X, Y, rng, 0, y0, y1)
        ref = ref * np.asarray(glass_tint, F32) * 1.7
        ag = c.aa(d - .1)
        c.paint(ix, ag, col=ref * .6 + np.array([.05, .06, .07], F32) * .4, h=-.22, r=.05)
        for k in range(8):  # slim mullions
            c.box(k * 1.5 - .02, y0, k * 1.5 + .02, y1, col=(.3, .31, .32), h=-.17, m=0, r=.4)
        c.box(0, y1, 12, y1 + .06, col=STONE * 1.05, hadd=.04, m=0)
        c.paint(ix, c.aa(.4 - np.abs(X - 6) + 6) * 0, dirt=0)
    for k in range(4):  # piers
        c.box(k * 3 - pier / 2, 0, k * 3 + pier / 2, 12.8, col=np.asarray(wall[0], F32) * 1.04, hadd=.05, m=0, g=.02)
    return c


def rolltor(c, cx, yb, w, h, col):
    y0 = yb - h
    c.box(cx - w / 2 - .12, y0 - .12, cx + w / 2 + .12, yb, col=STONE * .85, hadd=.03, m=0, g=.03)
    ix, X, Y = c.grid(cx - w / 2, y0, cx + w / 2, yb)
    a = np.ones(X.shape, F32)
    rib = np.sin((Y - y0) / .06 * 2 * np.pi)
    tone = np.asarray(col, F32) * (.92 + .08 * rib[..., None]) * (1 + .05 * c.n2[ix][..., None])
    sc = np.clip(1 - (yb - Y) / 1.4, 0, 1)
    tone = tone * (1 - .2 * sc[..., None])
    c.paint(ix, a, col=tone, h=-.08 + rib * .008, m=0, r=.55 + .15 * c.n2[ix])
    c.paint(ix, a * np.exp(-(yb - Y) / .5), dirt=.28)
    c.box(cx - w / 2, y0 - .0, cx + w / 2, y0 + .28, col=np.asarray(col) * .7, hadd=.04, m=0)
    c.box(cx - .08, yb - .32, cx + .08, yb - .27, col=(.2, .2, .2), hadd=.05, m=0)
    c.paint(ix, rectm(X, Y, cx - w / 2 + .1, y0 + .4, cx - w / 2 + .5, y0 + .95) * .35 * (c.n3[ix] > 0), col=(.12, .12, .13), keep=True)  # tag


def roof_tiles(seed):
    c = C(12, 12.8, seed)
    rng = c.rng
    nc, nt = 40, 60
    yy = (np.arange(S)[:, None] + .5) / S * nc
    row = np.floor(yy).astype(int)
    fy = yy - row
    xx = ((np.arange(S)[None, :] + .5) / S * nt + .5 * (row % 2)) % nt
    ti = np.floor(xx).astype(int) % nt
    fx = xx - np.floor(xx)
    rr = rng.random((nc, nt)).astype(F32)
    r = rr[row % nc, ti]
    base = lerp((.50, .22, .15), (.62, .30, .20), r[..., None])
    base = np.where((rng.random((nc, nt))[row % nc, ti] > .94)[..., None], np.array([.33, .17, .13], F32), base)
    moss = np.clip(c.n3 * .5 + c.n2 * .25 - .8, 0, 1)[..., None]
    base = base * (1 - moss * .7) + np.array([.22, .28, .13], F32) * moss * .7
    prof = .016 * np.cos(2 * np.pi * (fx - .5)) + .035 * fy ** 1.6
    shade = 1 - .45 * sstep((fy - .72) / .28) + .12 * sstep((.3 - fy) / .3) * 0
    shade = shade * (.88 + .12 * np.cos(2 * np.pi * (fx - .5)))
    c.alb[:] = base * shade[..., None] * (1 + .06 * c.n1[..., None])
    c.h[:] = prof + c.n1 * .0008
    c.m[:] = 0
    c.r[:] = .78 + .08 * c.n2
    c.dirt[:] = .05 + .08 * np.clip(c.n3, 0, 2) + .15 * np.clip(c.stk - .5, 0, 2)
    return c


def roof_gravel(seed):
    c = C(12, 12.8, seed)
    rng = c.rng
    dome, ids = cells(rng, 128, .45, .34, .52)
    tones = np.array([(.62, .6, .56), (.5, .49, .47), (.7, .66, .6), (.57, .53, .48), (.42, .42, .42)], F32)
    tone = tones[np.minimum((ids * 5).astype(int), 4)] * (.8 + .35 * dome[..., None])
    bit = np.array([.14, .14, .15], F32) * (1 + .1 * c.n2[..., None])
    a = sstep(dome * 2.4)[..., None]
    c.alb[:] = bit * (1 - a) + tone * a
    # bare / moss patches and Bahnen seams
    bare = sstep((c.n3 - 1.1) * 2)[..., None]
    c.alb[:] = c.alb * (1 - bare * .8) + np.array([.18, .18, .19], F32) * bare * .8
    moss = sstep((c.n2 * .5 + c.n3 * .7 - 1.2) * 3)[..., None]
    c.alb[:] = c.alb * (1 - moss * .5) + np.array([.22, .27, .12], F32) * moss * .5
    c.h[:] = dome * .015 * (1 - bare[..., 0] * .8)
    for k in range(13):
        c.box(k * 1.0 - .008, 0, k * 1.0 + .008, 12.8, col=(.1, .1, .1), hadd=.006, keep=True)
    c.m[:] = 0
    c.r[:] = .85 - .1 * dome
    c.dirt[:] = .04 + .05 * np.clip(c.n3, 0, 2)
    return c


def brandmauer(seed):
    c = C(12, 12.8, seed)
    rng = c.rng
    wall_plaster(c, (.74, .70, .62), rough=2.2, blot=1.8)
    Y = (np.arange(S)[:, None] + .5) / c.py
    wv = sstep(((.5 + .5 * np.cos(2 * np.pi * (Y - 2.0) / 12.8)) + c.n3 * .12 - .45) * 4)  # weathered zone
    fresh = np.array([.84, .82, .76], F32)
    c.alb[:] = c.alb * wv[..., None] + c.alb * (fresh / c.plaster) * (1 - wv[..., None]) * .98
    c.dirt[:] = c.dirt + wv * (.1 + .09 * np.clip(c.stk - .4, 0, 2) + .1 * np.clip(c.n2, 0, 2)) + (1 - wv) * .02
    # flaking: dark exposed patches
    fl = sstep((c.n3 * .7 + c.n2 * .6 - 1.5) * 3) * wv
    c.alb[:] = c.alb * (1 - fl[..., None] * .6) + np.array([.55, .38, .3], F32) * fl[..., None] * .6
    c.h[:] -= fl * .01
    # walled-up window outlines (new plaster, slightly different)
    for cx, y in ((3.0, 5.1), (9.0, 8.4)):
        ix, X, Y2 = c.grid(cx - .7, y - 1.6, cx + .7, y)
        a = rectm(X, Y2, cx - .55, y - 1.4, cx + .55, y - .1)
        c.paint(ix, a * .6, col=c.plaster * 1.08, hadd=.004, keep=True)
        c.paint(ix, c.aa(.012 - np.abs(np.minimum(np.minimum(X - cx + .55, cx + .55 - X), np.minimum(Y2 - y + 1.4, y - .1 - Y2)))) * .5, dirt=.25)
    # wall anchors (Maueranker), chimney trace, cracks
    for Lf in (3.2, 6.4, 9.6, 12.8):
        for xx in (1.5, 4.5, 7.5, 10.5):
            c.box(xx - .1, Lf - .04, xx + .1, Lf + .04, col=(.18, .13, .1), hadd=.015, m=0, r=.5)
            c.box(xx - .04, Lf - .1, xx + .04, Lf + .1, col=(.18, .13, .1), hadd=.015, m=0, r=.5)
            ix, X, Yg = c.grid(xx - .3, Lf, xx + .3, Lf + 1.5)
            c.paint(ix, np.exp(-(Yg - Lf) / .6) * c.aa(.1 - np.abs(X - xx)), dirt=.2)
    ix, X, Yg = c.grid(7.2, 0, 8.4, 12.8)
    c.paint(ix, rectm(X, Yg, 7.4, -1, 8.2, 14) * .0 + .0, keep=True)
    for _ in range(6):  # hairline cracks
        x, y = rng.uniform(0, 12), rng.uniform(0, 12.8)
        for _ in range(14):
            nx_, ny_ = x + rng.uniform(-.2, .2), y + rng.uniform(.05, .3)
            ixs, X, Yg = c.grid(min(x, nx_) - .05, min(y, ny_) - .05, max(x, nx_) + .05, max(y, ny_) + .05)
            a = seg(X, Yg, (x, y), (nx_, ny_), .012)
            c.paint(ixs, a * .8, dirt=.35, hadd=-.004)
            x, y = nx_, ny_
    c.r[:] = .92
    return c


# ---------------------------------------------------------------- facade catalogue
GREEN, GREY, BLUE = (.27, .42, .30), (.58, .6, .6), (.34, .42, .52)
WHITE, ANTH = (.92, .92, .89), (.2, .21, .22)


def pl(col, rough=1.0, blot=1.0):
    return lambda c: wall_plaster(c, col, rough, blot)


FACADES = {
    "gruender_a": ("1870-1914", lambda: standard("gruender_a", 11, dict(
        wall=pl((.88, .8, .6)), gs=dict(th=.26, prot=.1, col=STONE),
        win=dict(w=1.15, h=2.0, cols=2, rows=3, sur=.13, flowers=.35, bar=.03),
        shut=dict(col=GREEN, p=.75, closed=.12), sillh=.85,
        bal=dict(floors=[1, 2], axes=[1, 2], w=2.7, kind="bars", dw=1.05, dh=2.2, flowers=.7)))),
    "gruender_b": ("1870-1914", lambda: standard("gruender_b", 12, dict(
        wall=pl((.80, .81, .76)), gs=dict(th=.22, prot=.08, col=STONE * 1.02),
        win=dict(w=1.1, h=2.05, cols=2, rows=3, sur=.12, cap="tri", flowers=.2, arch=0),
        shut=dict(col=(.52, .56, .58), p=.55, closed=.08), sillh=.85,
        altwin=dict(mod=4, eq=1, kw=dict(w=1.2, h=2.1, arch=1, cap=None)),
        bal=dict(floors=[2], axes=[1, 2], w=3.0, kind="bars", dw=1.05, dh=2.2, rail=(.1, .13, .12))))),
    "gruender_c": ("1870-1914", lambda: standard("gruender_c", 13, dict(
        wall=pl((.86, .72, .64), 1.2), gs=dict(th=.2, prot=.07, col=STONE),
        win=dict(w=1.15, h=1.95, cols=2, rows=3, sur=.1, flowers=.15),
        sillh=.85, bal=dict(floors=[0, 2], axes=[0, 3], w=2.2, kind="bars", dw=1.0, dh=2.15, flowers=.8)))),
    "jugend_a": ("1900-1914", lambda: standard("jugend_a", 21, dict(
        wall=pl((.88, .84, .66)), gs=dict(th=.14, prot=.05, col=STONE * 1.05),
        orn=dict(col=(.8, .76, .6), accent=(.5, .62, .5)),
        win=dict(w=1.2, h=1.9, cols=2, rows=3, arch=1, sur=.11, flowers=.2),
        sillh=.8, bal=dict(floors=[1, 3], axes=[1, 2], w=2.7, kind="bars", dw=1.05, dh=2.2, rail=(.1, .22, .16))))),
    "jugend_b": ("1900-1914", lambda: standard("jugend_b", 22, dict(
        wall=pl((.74, .8, .72)), gs=dict(th=.12, prot=.04, col=STONE),
        orn=dict(col=(.88, .85, .74), accent=(.45, .58, .5), p=.6),
        win=dict(w=.82, h=1.75, cols=1, rows=3, sur=.09, flowers=.25),
        shut=dict(col=(.45, .22, .16), p=.3, closed=0), sillh=.85,
        twin=.56,
        bal=dict(floors=[], axes=[], w=1)))),
    "genoss_a": ("1920-1939", lambda: standard("genoss_a", 31, dict(
        wall=pl((.91, .88, .79)), gs=dict(th=.08, prot=.015, col=(.88, .85, .76), m=1),
        win=dict(w=1.2, h=1.45, cols=2, rows=3, bar=.022, flowers=.25),
        shut=dict(col=GREEN, p=.85, closed=.05), sillh=.95,
        bal=dict(floors=[1, 3], axes=[0, 2], w=1.7, kind="bars", dw=.95, dh=2.1, flowers=.7)))),
    "genoss_b": ("1920-1939", lambda: standard("genoss_b", 32, dict(
        wall=pl((.9, .8, .6)), gs=dict(th=.08, prot=.015, col=(.88, .78, .58), m=1),
        win=dict(w=1.25, h=1.5, cols=2, rows=3, bar=.022, flowers=.2),
        shut=dict(col=(.5, .2, .15), p=.8, closed=.05), sillh=.95,
        bal=dict(floors=[0, 2], axes=[1, 3], w=1.8, kind="bars", dw=.95, dh=2.1, rail=(.14, .14, .14))))),
    "genoss_c": ("1920-1939", lambda: standard("genoss_c", 33, dict(
        wall=pl((.8, .84, .78)), gs=dict(th=.07, prot=.012, col=(.78, .82, .76), m=1),
        win=dict(w=1.15, h=1.5, cols=2, rows=3, bar=.022, sur=.06, surc=(.9, .9, .86)),
        shut=dict(col=BLUE, p=.7, closed=.05), sillh=.95, shift=.0,
        bal=dict(floors=[1, 2, 3], axes=[2], w=1.7, kind="solid", col=(.82, .83, .78), dw=.95, dh=2.1)))),
    "block50_a": ("1950-1969", lambda: standard("block50_a", 41, dict(
        wall=pl((.82, .8, .73), .8), gs=dict(th=.1, prot=.02, col=(.7, .7, .68)),
        win=dict(w=1.35, h=1.4, cols=2, rows=2, bar=.04, frame=WHITE, d=.1, flowers=.15, sillcol=(.62, .62, .6)),
        sillh=.9, bal=dict(floors=[0, 1, 2, 3], axes=[0, 2], w=2.0, kind="solid", col=(.78, .78, .74), dw=1.0, dh=2.1, flowers=.4)))),
    "block50_b": ("1950-1969", lambda: standard("block50_b", 42, dict(
        wall=pl((.87, .83, .7), .8), gs=dict(th=.08, prot=.015, col=(.72, .7, .66)),
        win=dict(w=1.2, h=1.35, cols=2, rows=2, bar=.04, frame=(.55, .38, .26), d=.1, sillcol=(.66, .64, .6)),
        sillh=.95, parapet=dict(col=(.62, .36, .3), y_from=.95, y_to=0.0),
        bal=dict(floors=[1, 3], axes=[1, 3], w=1.9, kind="bars", dw=1.0, dh=2.1, rail=(.3, .3, .3))))),
    "block60_a": ("1960-1975", lambda: standard("block60_a", 43, dict(
        wall=pl((.85, .85, .82), .7), parapet=dict(col=(.58, .6, .6), y_from=1.0, y_to=.14),
        win=dict(w=2.7, h=1.3, cols=3, rows=1, bar=.05, frame=(.75, .75, .73), d=.1, sillcol=(.6, .6, .58), sill=False),
        sillh=1.0, bal=dict(floors=[], axes=[], w=1)))),
    "waschbeton_a": ("1970-1985", lambda: standard("waschbeton_a", 51, dict(
        wall=lambda c: wall_pebble(c, (.55, .53, .5), [(.62, .6, .56), (.45, .44, .42), (.7, .65, .55), (.52, .5, .46)]),
        joints=[[0, 3, 6, 9]], gs=dict(th=.05, prot=-.01, col=(.3, .3, .3)),
        win=dict(w=1.35, h=1.25, cols=2, rows=1, bar=.05, frame=(.34, .26, .2), d=.2, sillcol=(.42, .4, .38)),
        sillh=.95, bal=dict(floors=[1, 2, 3], axes=[0, 2], w=2.1, kind="solid", col=(.5, .48, .45), dw=1.0, dh=2.1, flowers=.5)))),
    "waschbeton_b": ("1970-1985", lambda: standard("waschbeton_b", 52, dict(
        wall=lambda c: wall_pebble(c, (.62, .58, .52), [(.72, .66, .55), (.55, .5, .44), (.8, .74, .62), (.5, .48, .45)]),
        parapet=dict(col=(.5, .46, .4), y_from=1.0, y_to=.1),
        win=dict(w=2.4, h=1.25, cols=3, rows=1, bar=.05, frame=(.3, .3, .3), d=.18, sillcol=(.45, .43, .4)),
        sillh=1.0, bal=dict(floors=[], axes=[], w=1)))),
    "neubau_a": ("2005-", lambda: standard("neubau_a", 61, dict(
        wall=pl((.93, .93, .9), .5), win=dict(w=1.3, h=1.45, cols=1, rows=1, bar=.03, frame=ANTH, fw=.05, d=.22, sill=False, refl=.4),
        altwin=dict(mod=2, eq=0, kw=dict(w=1.9, h=2.15, cols=2, rows=1, sill=False)), sillh=.95, shift=.0,
        bal=dict(floors=[0, 1, 2, 3], axes=[1, 3], w=2.6, kind="glass", dw=1.9, dh=2.15,
                 dkw=dict(cols=2, rows=1, frame=ANTH, fw=.05, d=.22, refl=.4), flowers=.0)))),
    "neubau_b": ("2005-", lambda: standard("neubau_b", 62, dict(
        wall=lambda c: wall_panel(c, [(.9, .9, .88), (.82, .83, .81), (.95, .95, .92), (.86, .87, .84)], 1.2, .6, .014, mask=1),  # tintable (was fixed grey = 'grey window grid')
        win=dict(w=1.4, h=2.1, cols=1, rows=1, bar=.03, frame=ANTH, fw=.05, d=.24, sill=False, refl=.42),
        sillh=.2, shift=1.2, bal=dict(floors=[], axes=[], w=1)))),
    "neubau_c": ("2005-", lambda: standard("neubau_c", 63, dict(
        wall=lambda c: (wall_plaster(c, (.84, .84, .81), .5), [wall_wood(c, (.52, .46, .4), .13, ax * 3 + .02, ax * 3 + 2.98, fl * 3.2 + .1, fl * 3.2 + 3.1)
                                                     for fl in range(4) for ax in range(4) if (fl + ax) % 2 == 1]),
        win=dict(w=1.2, h=1.5, cols=1, rows=1, bar=.03, frame=ANTH, fw=.05, d=.22, sill=False, refl=.4),
        altwin=dict(mod=2, eq=0, kw=dict(w=1.0, h=2.1)), sillh=.95,
        bal=dict(floors=[], axes=[], w=1)))),
    "gewerbe_a": ("1900-1960", lambda: gewerbe("gewerbe_a", 71, ((.55, .24, .17), (.46, .2, .15), (.3, .15, .12)), (.22, .24, .24), 0)),
    "gewerbe_b": ("1880-1930", lambda: gewerbe("gewerbe_b", 72, ((.7, .56, .36), (.6, .46, .3), (.4, .28, .2)), (.2, .3, .25), 1)),
    "gewerbe_c": ("1950-1990", lambda: gewerbe("gewerbe_c", 73, None, (.7, .72, .72), 2)),
    "buero_a": ("1990-", lambda: curtain("buero_a", 81, (.55, .78, .78), (.1, .14, .16), (.62, .64, .66))),
    "buero_b": ("1960-1985", lambda: hband("buero_b", 82, [(.78, .78, .75), (.74, .74, .72)], (.5, .7, .85), .9)),
    "buero_c": ("2000-", lambda: curtain("buero_c", 83, (.75, .72, .62), (.3, .27, .22), (.3, .3, .32), nx=8, fins=.16, louvres=True)),
}


def gewerbe(name, seed, brick, frame, kind):
    c = C(12, 12.8, seed)
    rng = c.rng
    if kind == 2:
        wall_ribbed(c, (.6, .66, .64))
    else:
        wall_brick(c, brick)
    for Lf in (3.2, 6.4, 9.6, 12.8):
        band(c, Lf, .16, .03, (.55, .54, .52), m=0)
    gate_col = (.28, .45, .36) if kind == 1 else (.5, .53, .55)
    for fl in range(4):
        Lf = (fl + 1) * 3.2
        for ax in range(4):
            cx = (ax + .5) * 3
            if fl == 3 and ax in (0, 2):
                rolltor(c, cx, Lf - .3, 2.6, 2.6, gate_col)
                continue
            if kind == 2:
                if fl in (1, 2):
                    window(c, cx, Lf - 1.2, 2.5, 1.0, cols=5, rows=1, frame=(.7, .72, .72), fw=.05, d=.12, bar=.05, sillcol=(.55, .55, .55))
                continue
            if kind == 1:
                window(c, cx, Lf - .75, 1.4, 2.3, arch=1, cols=3, rows=5, frame=frame, fw=.035, bar=.025, d=.2,
                       sur=.1, surc=brick[0], surm=0, content=str(rng.choice(["dark", "dark", "lamp", "blind"])), sillcol=(.55, .54, .52))
                continue
            window(c, cx, Lf - .8, 2.2, 1.6, cols=6, rows=4, frame=frame, fw=.03, bar=.02, d=.14,
                   content=str(rng.choice(["dark", "dark", "lamp", "blind", "veil"])), refl=.3, sillcol=(.55, .54, .52))
    c.dirt[:] += .05
    return c


def wall_ribbed(c, col):
    p = .1
    X = (np.arange(S)[None, :] + .5) / c.px
    ph = (X / p) % 1
    prof = np.sin(ph * 2 * np.pi)
    c.alb[:] = np.asarray(col, F32) * (1 + .06 * prof[..., None]) * (1 + .04 * c.n2[..., None]) * np.ones((S, 1, 1), F32)
    c.h[:] = prof * .012 + c.n1 * .0008
    c.m[:] = 0
    c.r[:] = .55 + .1 * c.n2
    c.dirt[:] = .06 + .1 * np.clip(c.stk - .3, 0, 2) + .05 * np.clip(c.n3, 0, 2)
    c.plaster = np.asarray(col, F32)


# ---------------------------------------------------------------- shop fronts (12 x 4 m)
def shop_room(kind, X, Y, x0, x1, y0, y1, rng):
    """Interior seen through the shop glass; floor line at y1."""
    img = np.zeros(X.shape + (3,), F32)
    R = lambda a, b: rng.uniform(min(a, b), max(a, b))
    flr = y1 - .45
    if kind == "cafe":
        img[:] = np.array([.30, .20, .13], F32) * (1.15 - .5 * np.clip((Y - y0) / (y1 - y0), 0, 1))[..., None]
        over(img, rectm(X, Y, x0, flr, x1, y1), (.12, .08, .06))
        over(img, rectm(X, Y, x0, y0 + .9, x1, y0 + .96), (.5, .36, .2), .8)
        for i in range(int((x1 - x0) / .45)):  # shelf bottles
            bx = x0 + .2 + i * .45 + R(0, .2)
            over(img, rectm(X, Y, bx, y0 + .62, bx + .07, y0 + .9), [(.5, .35, .15), (.2, .35, .2), (.6, .25, .15)][rng.integers(3)], .8)
        tx = x0 + .5
        while tx < x1 - .5:
            over(img, rectm(X, Y, tx - .32, y1 - 1.0, tx + .32, y1 - .95), (.2, .13, .08))
            over(img, rectm(X, Y, tx - .02, y1 - .95, tx + .02, y1 - .15), (.1, .08, .06))
            for sd in (-1, 1):
                over(img, rectm(X, Y, tx + sd * .5 - .05, y1 - 1.15, tx + sd * .5 + .05, y1 - .1), (.1, .07, .05))
                over(img, rectm(X, Y, tx + sd * .5 - .22 * (sd < 0) , y1 - .5, tx + sd * .5 + .22 * (sd > 0), y1 - .45), (.12, .08, .06))
            lx = tx + R(-.2, .2)
            over(img, seg(X, Y, (lx, y0), (lx, y0 + .55), .01), (.1, .1, .1))
            g = np.exp(-(((X - lx) / .5) ** 2) - (((Y - y0 - .6) / .45) ** 2))
            img += g[..., None] * np.array([.55, .38, .18], F32)
            over(img, disc(X, Y, lx, y0 + .6, .11), (1, .85, .55))
            tx += R(1.0, 1.5)
        if rng.random() < .8:
            px_ = R(x0 + .6, x1 - .6)
            over(img, disc(X, Y, px_, y1 - 1.55, .1), (.35, .25, .2))
            over(img, rectm(X, Y, px_ - .17, y1 - 1.42, px_ + .17, y1 - .55), (.22, .2, .25))
    elif kind == "kiosk":
        img[:] = np.array([.72, .70, .64], F32) * (1.1 - .3 * np.clip((Y - y0) / (y1 - y0), 0, 1))[..., None]
        for sy in (y0 + .55, y0 + 1.05, y0 + 1.55):
            over(img, rectm(X, Y, x0, sy, x1, sy + .03), (.3, .3, .3))
            xx = x0 + .05
            while xx < x1 - .1:
                w_, h_ = R(.05, .14), R(.12, .36)
                hue = np.array([R(.15, .95), R(.1, .9), R(.1, .9)], F32)
                over(img, rectm(X, Y, xx, sy - h_, xx + w_, sy), hue)
                xx += w_ + R(0, .03)
        over(img, rectm(X, Y, x0, flr + .1, x1, y1), (.3, .28, .26))
    elif kind == "bar":
        img[:] = np.array([.05, .035, .045], F32) * np.ones(X.shape + (1,), F32)
        ny = R(.2, .5)
        col = [(1, .15, .35), (.2, .5, 1), (1, .4, .1)][rng.integers(3)]
        ly = y0 + .35
        img += (np.exp(-((Y - ly) / .12) ** 2) * .5)[..., None] * np.array(col, F32)
        over(img, rectm(X, Y, x0 + .3, ly - .015, x1 - .3, ly + .015), col)
        for i in range(int((x1 - x0) / .3)):
            bx = x0 + .2 + i * .3
            over(img, rectm(X, Y, bx, y0 + 1.05, bx + .08, y0 + 1.35), [(.6, .35, .1), (.15, .4, .2), (.5, .1, .1)][rng.integers(3)], .7)
        over(img, rectm(X, Y, x0, y0 + 1.4, x1, y0 + 1.43), (.55, .35, .15))
        over(img, rectm(X, Y, x0, flr, x1, y1), (.02, .02, .02))
    elif kind == "kebab":
        img[:] = np.array([.78, .74, .6], F32) * np.ones(X.shape + (1,), F32)
        over(img, rectm(X, Y, x0, y0 + 1.0, x1, y1), (.5, .3, .2), .85)
        for bx in np.arange(x0 + .1, x1 - .7, .85):
            over(img, rectm(X, Y, bx, y0 + .1, bx + .75, y0 + .75), (.1, .1, .1))
            for k in range(3):
                over(img, rectm(X, Y, bx + .05 + k * .24, y0 + .15, bx + .26 + k * .24, y0 + .45), [(.8, .15, .1), (.9, .7, .1), (.3, .55, .2)][rng.integers(3)])
                over(img, rectm(X, Y, bx + .05 + k * .24, y0 + .5, bx + .26 + k * .24, y0 + .52), (.9, .9, .9))
        sx = R(x0 + .5, x1 - .5)
        over(img, rectm(X, Y, sx - .12, y0 + 1.05, sx + .12, y0 + 1.9), (.55, .3, .15))
        over(img, rectm(X, Y, x0, y1 - .75, x1, y1), (.62, .64, .66))
        over(img, rectm(X, Y, x0, y1 - .78, x1, y1 - .74), (.85, .86, .88))
    elif kind == "coiffeur":
        img[:] = np.array([.84, .84, .85], F32) * (1.05 - .15 * np.clip((Y - y0) / (y1 - y0), 0, 1))[..., None]
        mx = x0 + .35
        while mx < x1 - .9:
            over(img, rectm(X, Y, mx - .03, y0 + .35, mx + .83, y0 + 1.5), (.08, .08, .09))
            sky = np.array([.7, .78, .85], F32) * (1.1 - .3 * np.clip((Y - y0) / 1.5, 0, 1))[..., None]
            over(img, rectm(X, Y, mx, y0 + .38, mx + .8, y0 + 1.47), 0, 0)
            img[:] = np.where((rectm(X, Y, mx, y0 + .38, mx + .8, y0 + 1.47) > .5)[..., None], sky, img)
            cx_ = mx + .4
            over(img, rectm(X, Y, cx_ - .25, y1 - .75, cx_ + .25, y1 - .6), (.05, .05, .06))
            over(img, rectm(X, Y, cx_ - .22, y1 - 1.3, cx_ + .22, y1 - .75), (.08, .08, .09))
            over(img, rectm(X, Y, cx_ - .03, y1 - .6, cx_ + .03, y1 - .1), (.5, .5, .5))
            mx += R(1.1, 1.5)
        over(img, rectm(X, Y, x0, y1 - .85, x1, y1 - .8), (.95, .95, .95))
    elif kind == "velo":
        img[:] = np.array([.74, .73, .68], F32) * (1.05 - .2 * np.clip((Y - y0) / (y1 - y0), 0, 1))[..., None]
        over(img, rectm(X, Y, x0, flr + .1, x1, y1), (.3, .3, .3))
        over(img, rectm(X, Y, x0, y0 + .7, x1, y0 + .75), (.3, .3, .3))
        bx = x0 + .7
        while bx < x1 - .7:
            col = [(.1, .1, .12), (.7, .12, .1), (.1, .3, .6), (.85, .75, .1), (.1, .45, .3)][rng.integers(5)]
            yw = y1 - .45
            for wx in (bx - .55, bx + .55):
                ring = np.clip(1 - np.abs(np.hypot(X - wx, Y - yw) - .33) / .018, 0, 1)
                over(img, ring, (.08, .08, .08))
            pts = [(bx - .55, yw), (bx - .12, yw - .45), (bx + .32, yw - .45), (bx + .55, yw), (bx, yw), (bx - .12, yw - .45), (bx + .32, yw - .45), (bx + .5, yw - .75), (bx + .6, yw - .75)]
            for a_, b_ in zip(pts[:-1], pts[1:]):
                over(img, seg(X, Y, a_, b_, .035), col)
            over(img, seg(X, Y, (bx - .15, yw - .52), (bx - .2, yw - .6), .05), (.1, .1, .1))
            bx += R(1.45, 1.9)
    elif kind == "leer":
        img[:] = np.array([.88, .87, .82], F32) * (.95 + .03 * rng.random())
        for _ in range(int((x1 - x0) * 2.2)):
            px_, py_ = R(x0, x1), R(y0, y1 - .5)
            col = [(.9, .2, .15), (.2, .4, .8), (.95, .85, .2), (.15, .15, .15), (.85, .85, .85), (.3, .6, .4)][rng.integers(6)]
            w_, h_ = R(.2, .55), R(.3, .8)
            over(img, rectm(X, Y, px_, py_, px_ + w_, py_ + h_), col, .95)
            for k in range(int(R(2, 5))):
                yy = py_ + h_ * (.45 + .1 * k)
                over(img, rectm(X, Y, px_ + .04, yy, px_ + w_ * R(.4, .9), yy + .015), (.15, .15, .15), .6)
        px_ = R(x0 + .3, x1 - .8)
        over(img, rectm(X, Y, px_, y0 + .2, px_ + .5, y0 + .8), (.97, .97, .95))
        over(img, rectm(X, Y, px_, y0 + .2, px_ + .5, y0 + .32), (.85, .1, .1))
        over(img, rectm(X, Y, x0, y1 - .35, x1, y1), (.35, .33, .3), .6)
    elif kind == "baeckerei":
        img[:] = np.array([.78, .58, .36], F32) * (1.1 - .3 * np.clip((Y - y0) / (y1 - y0), 0, 1))[..., None]
        for sy in (y0 + .65, y0 + 1.2, y0 + 1.75):
            over(img, rectm(X, Y, x0, sy, x1, sy + .04), (.45, .3, .15))
            xx = x0 + .08
            while xx < x1 - .2:
                r_ = R(.07, .13)
                col = [(.62, .38, .18), (.76, .5, .25), (.5, .3, .14), (.82, .62, .35)][rng.integers(4)]
                img[:] = np.where((disc(X, Y, xx + r_, sy - r_ * .7, r_)[..., None] * (Y < sy)[..., None] > .5), np.asarray(col, F32) * (1.15 - .4 * (Y - sy + r_ * 1.4)[..., None] / r_ / 2), img)
                xx += r_ * 2 + R(.0, .05)
        over(img, rectm(X, Y, x0, y1 - .8, x1, y1), (.9, .88, .84))
        for xx in np.arange(x0 + .1, x1 - .3, .3):
            over(img, rectm(X, Y, xx, y1 - .75, xx + .24, y1 - .55), [(.9, .7, .8), (.5, .3, .2), (.95, .9, .6)][rng.integers(3)])
    return img


def shop_pane(c, x0, y0, x1, y1, kind, frame, fw=.05, refl=.17, d=.12):
    ix, X, Y = c.grid(x0, y0, x1, y1)
    c.paint(ix, rectm(X, Y, x0, y0, x1, y1), col=frame, h=-d + .01, m=0, r=.4)
    room = shop_room(kind, X, Y, x0, x1, y0, y1, c.rng)
    ref = reflection(X, Y, c.rng, x0, y0, y1 - .5)
    ra = refl * (.4 + 1.2 * (1 - np.clip((Y - y0) / (y1 - y0) * 1.6, 0, 1)))[..., None]
    glass = room * (1 - ra) + ref * ra
    dust = (.04 * np.clip(c.n3[ix], -1, 2))[..., None]
    c.paint(ix, rectm(X, Y, x0 + fw, y0 + fw, x1 - fw, y1 - fw), col=np.clip(glass + dust, 0, 1), h=-d - .012, m=0, r=.05)


def awning(c, x0, x1, y0, y1, cols, w=.16):
    ix, X, Y = c.grid(x0, y0 - .05, x1, y1 + .5)
    st = (np.floor((X - x0) / w).astype(int) % 2)[..., None]
    col = np.asarray(cols[0], F32) * (1 - st) + np.asarray(cols[1], F32) * st
    t = np.clip((Y - y0) / (y1 - y0), 0, 1)
    edge = y1 + .05 * np.sin((X - x0) / w * np.pi)
    a = (np.clip((edge - Y) * c.k + .5, 0, 1) * np.clip((Y - y0) * c.k + .5, 0, 1)).astype(F32)
    shade = (1.05 - .3 * t - .25 * sstep((Y - (y1 - .16)) / .1))[..., None]
    folds = (1 + .05 * np.sin((X - x0) / w * np.pi))[..., None]
    c.paint(ix, a, col=col * shade * folds * (1 + .04 * c.n1[ix][..., None]), h=.1 + .25 * t - .05 * (Y > y1 - .16), m=0, r=.85)
    below = np.clip((Y - edge) / .35, 0, 1)
    c.alb[ix] *= (1 - .35 * (np.exp(-below * 3) * (Y > edge) * c.aa(x1 - X) * c.aa(X - x0)))[..., None]


def shopfront(name, seed, K):
    c = C(12, 4, seed)
    rng = c.rng
    wall_plaster(c, K.get("wall", (.82, .8, .74)), .8)
    sc = np.asarray(K["sign"], F32)
    c.box(0, .3, 12, 1.12, col=sc, hadd=.07, m=0, g=.03, r=K.get("signr", .45))
    c.box(0, .3, 12, .35, col=sc * .65, hadd=.1, m=0)
    c.box(0, 1.07, 12, 1.12, col=sc * .65, hadd=.1, m=0)
    if K.get("lit"):
        ix, X, Y = c.grid(0, .3, 12, 1.12)
        c.alb[ix] = np.clip(c.alb[ix] * (1.0 + .35 * np.exp(-((Y - .7) / .25) ** 2)[..., None]), 0, 1)
    ix, X, Y = c.grid(0, 1.12, 12, 1.6)
    c.paint(ix, np.exp(-(Y - 1.12) / .12) * (Y > 1.12), dirt=.28)
    pw = .48
    door_ax = K.get("door", 1)
    frame = np.asarray(K.get("frame", (.2, .21, .22)), F32)
    top, bot = 1.3, 3.5
    for ax in range(4):
        bx0, bx1 = ax * 3 + pw / 2, ax * 3 + 3 - pw / 2
        kind = K["room"]
        if ax == door_ax:
            dx0, dx1 = (bx0 + bx1) / 2 - .6, (bx0 + bx1) / 2 + .6
            shop_pane(c, bx0, top, dx0, bot, kind, frame, refl=.17)
            shop_pane(c, dx1, top, bx1, bot, kind, frame, refl=.17)
            shop_pane(c, dx0, top, dx1, bot, kind, frame, fw=.08, refl=.16)
            c.box(dx1 - .14, 2.3, dx1 - .11, 3.0, col=(.7, .72, .74), hadd=.05, m=0, r=.3)
            c.box(dx0, 3.2, dx1, 3.5, col=frame * 1.3, hadd=.0, m=0, r=.4, keep=True)
        else:
            mid = (bx0 + bx1) / 2
            shop_pane(c, bx0, top, mid, bot, kind, frame, refl=.17)
            shop_pane(c, mid, top, bx1, bot, kind, frame, refl=.17)
            if K.get("transom"):
                c.box(bx0, 2.75, bx1, 2.8, col=frame, hadd=-.07, m=0, r=.4)
    for k in range(4):  # piers
        pc = K.get("pier")
        if pc is None:
            c.box(k * 3 - pw / 2, 1.2, k * 3 + pw / 2, 3.55, col=c.plaster * 1.0, hadd=.04, m=1, g=.03)
        else:
            c.box(k * 3 - pw / 2, 1.2, k * 3 + pw / 2, 3.55, col=pc, hadd=.05, m=0, g=.04, r=.7)
    sk = np.asarray(K.get("sockel", (.35, .35, .36)), F32)
    ix, X, Y = c.grid(0, 3.5, 12, 4.0)
    tile = K.get("tile")
    col = sk * np.ones(X.shape + (1,), F32)
    hh = np.full(X.shape, .03, F32)
    if tile:
        g = np.minimum(((X / .15) % 1), ((Y / .15) % 1))
        j = (g < .05)
        col = col * np.where(j[..., None], .6, 1.0)
        hh = hh - .006 * j
    c.paint(ix, np.ones(X.shape, F32), col=col, h=hh, m=0, r=.7 if tile else .85, g=.05)
    c.paint(ix, sstep((Y - 3.55) / .45), dirt=.2)
    if K.get("awning"):
        for ax in K.get("awn_ax", range(4)):
            awning(c, ax * 3 + .3, ax * 3 + 2.7 + .3, 1.12, 1.95, K["awning"])
    if K.get("shutter"):  # roller shutter partly down on one bay
        ax = K["shutter"]
        x0, x1 = ax * 3 + pw / 2, ax * 3 + 3 - pw / 2
        low = K.get("shut_low", 2.3)
        ix, X, Y = c.grid(x0, top, x1, low)
        a = np.ones(X.shape, F32)
        rib = np.sin((Y - top) / .045 * 2 * np.pi)
        tone = np.array([.56, .58, .58], F32) * (.9 + .1 * rib[..., None]) * (1 + .06 * c.n2[ix][..., None])
        c.paint(ix, a, col=tone, h=-.02 + rib * .006, m=0, r=.5)
        for _ in range(5):  # graffiti tags
            gx, gy = rng.uniform(x0 + .1, x1 - .6), rng.uniform(top + .3, low - .3)
            gc = [(.9, .2, .5), (.2, .6, .9), (.95, .85, .1), (.1, .1, .1), (.9, .9, .9)][rng.integers(5)]
            p0 = (gx, gy)
            for _ in range(5):
                p1 = (p0[0] + rng.uniform(-.08, .22), p0[1] + rng.uniform(-.2, .2))
                c.paint(ix, seg(X, Y, p0, p1, .035) * .85, col=gc, keep=True)
                p0 = p1
        c.box(x0, low - .06, x1, low, col=(.3, .3, .3), hadd=.04, m=0)
        c.paint(ix, a * np.exp(-(Y - top) / .3), dirt=.2)
    for ix_ in K.get("posters", []):  # posters on piers
        px_ = ix_ * 3
        for _ in range(3):
            y = rng.uniform(1.6, 3.0)
            h_ = rng.uniform(.35, .7)
            col = np.array([rng.uniform(.1, 1), rng.uniform(.1, .95), rng.uniform(.1, .9)], F32)
            c.box(px_ - .2, y, px_ + .2, y + h_, col=col, hadd=.006, m=0, r=.6)
    c.dirt[:] += .03
    return c


SHOPS = {
    "shop_cafe": ("generic", dict(room="cafe", sign=(.17, .3, .23), awning=[(.16, .3, .22), (.9, .87, .78)], awn_ax=[0, 1, 2], door=2, frame=(.12, .15, .13), wall=(.86, .83, .74), sockel=(.24, .26, .25))),
    "shop_kiosk": ("generic", dict(room="kiosk", sign=(.95, .75, .1), lit=True, door=0, frame=(.45, .46, .48), pier=(.55, .55, .56), posters=[1, 2, 3], sockel=(.45, .44, .42), transom=True)),
    "shop_bar": ("generic", dict(room="bar", sign=(.09, .08, .1), door=3, frame=(.07, .07, .08), wall=(.7, .66, .62), pier=(.2, .18, .18), sockel=(.1, .1, .11), posters=[2])),
    "shop_kebab": ("generic", dict(room="kebab", sign=(.78, .12, .1), lit=True, door=1, frame=(.7, .7, .72), wall=(.86, .85, .8), sockel=(.55, .35, .25), tile=True, signr=.3)),
    "shop_coiffeur": ("generic", dict(room="coiffeur", sign=(.12, .12, .13), door=2, frame=(.85, .85, .86), wall=(.9, .88, .86), sockel=(.2, .2, .22), signr=.25)),
    "shop_velo": ("generic", dict(room="velo", sign=(.85, .42, .1), door=1, frame=(.15, .16, .17), wall=(.8, .78, .72), sockel=(.3, .3, .3), pier=(.45, .43, .4))),
    "shop_leer": ("generic", dict(room="leer", sign=(.5, .5, .48), door=2, frame=(.3, .3, .3), wall=(.78, .75, .7), sockel=(.3, .3, .3), shutter=0, shut_low=2.9, posters=[1, 3], signr=.9)),
    "shop_baeckerei": ("generic", dict(room="baeckerei", sign=(.84, .76, .58), awning=[(.6, .18, .15), (.9, .86, .78)], awn_ax=[1], door=0, frame=(.38, .24, .14), wall=(.88, .84, .72), sockel=(.4, .3, .22), signr=.5)),
}
ERA_SHOP = "1900-"


def build(name):
    if name in FACADES:
        c = FACADES[name][1]()
        finish(c, name)
    elif name in SHOPS:
        c = shopfront(name, 100 + list(SHOPS).index(name), SHOPS[name][1])
        finish(c, name, nk=.5)
    elif name == "dach_ziegel":
        finish(roof_tiles(91), name)
    elif name == "dach_kies":
        finish(roof_gravel(92), name)
    elif name == "brandmauer":
        finish(brandmauer(93), name)


def catalogue():
    L = [dict(name=n, kind="facade", era=e) for n, (e, _) in FACADES.items()]
    L += [dict(name=n, kind="shop", era=ERA_SHOP) for n in SHOPS]
    L += [dict(name="dach_ziegel", kind="roof", era="1850-"), dict(name="dach_kies", kind="roof", era="1960-"),
          dict(name="brandmauer", kind="wall", era="1850-")]
    return L


def sheet():
    L = catalogue()
    W = 256
    face = [l for l in L if l["kind"] != "shop"]
    shops = [l for l in L if l["kind"] == "shop"]
    cols = 6
    rows = (len(face) + cols - 1) // cols
    img = Image.new("RGB", (cols * W, rows * W + 2 * 128), (30, 30, 30))
    for i, l in enumerate(face):
        a = Image.open(OUT / f"{l['name']}_albedo.png").resize((W, W), Image.LANCZOS)
        img.paste(a, ((i % cols) * W, (i // cols) * W))
    for i, l in enumerate(shops):
        a = Image.open(OUT / f"{l['name']}_albedo.png").resize((384, 128), Image.LANCZOS)
        img.paste(a, ((i % 4) * 384, rows * W + (i // 4) * 128))
    p = ROOT / "preview"
    p.mkdir(exist_ok=True)
    img.save(p / "facades_sheet.jpg", quality=88)


if __name__ == "__main__":
    names = sys.argv[1:] or [l["name"] for l in catalogue()]
    for n in names:
        build(n)
        print("ok", n, flush=True)
    if not sys.argv[1:]:
        (OUT / "layers.json").write_text(json.dumps(catalogue(), indent=1))
    sheet()
