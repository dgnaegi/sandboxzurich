"""Procedural ground layers (no photos): Zürich carriageway asphalt, sidewalk asphalt, Reihenpflaster, granite curb, gutter setts.

All layers tile seamlessly (FFT noise, periodic drawing). Each returns (albedo RGB, tint mask L, normal+roughness RGB):
R,G = tangent-space normal xy (v = image y), B = roughness. Used via LAYERS in gen_textures.py.
"""
import numpy as np
from PIL import Image

L = 512
_Y, _X = np.mgrid[0:L, 0:L].astype(np.float32)


def _rng(seed):
    return np.random.default_rng(seed)


def tnoise(rng, scale):
    """Seamless band-limited noise, feature size ~scale px, unit std."""
    w = rng.normal(0, 1, (L, L))
    f = np.fft.fftfreq(L)[:, None] ** 2 + np.fft.fftfreq(L)[None, :] ** 2
    k = np.fft.fft2(w) * np.exp(-f * (scale * 1.2) ** 2)
    n = np.real(np.fft.ifft2(k))
    return ((n - n.mean()) / (n.std() + 1e-9)).astype(np.float32)


def fbm(rng, scales, weights):
    return sum(w * tnoise(rng, s) for s, w in zip(scales, weights))


def pd(a, c):
    """Periodic signed distance on the tile."""
    return (a - c + L / 2) % L - L / 2


def blob(cx, cy, rx, ry, soft=1.0):
    d = np.sqrt((pd(_X, cx) / rx) ** 2 + (pd(_Y, cy) / ry) ** 2)
    return np.clip((1 - d) * soft, 0, 1)


def draw_walk(rng, x, y, ang, n, step, width, mask, wob=0.35, branch=0.0):
    """Crack: random walk drawn with periodic wrap. mask gets 1 along the path."""
    for i in range(n):
        ang += rng.normal(0, wob)
        x += np.cos(ang) * step
        y += np.sin(ang) * step
        d2 = pd(_X, x) ** 2 + pd(_Y, y) ** 2
        np.maximum(mask, np.clip(1 - d2 / (width * width), 0, 1), out=mask)
        if branch and rng.random() < branch:
            draw_walk(rng, x, y, ang + rng.choice([-1, 1]) * 0.9, n // 3, step, width * 0.7, mask, wob * 1.4)


def normal_rough(h, strength, rough):
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    nx, ny = -gx * strength, -gy * strength
    r = np.broadcast_to(rough, h.shape)
    im = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, r], -1)
    return Image.fromarray(np.clip(im * 255, 0, 255).astype(np.uint8))


def _img(rgb):
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


def _mask():
    return Image.new("L", (L, L), 255)


def asphalt():
    """Fahrbahn: dark fine-grained, aggregate speckle, sealed patches with tar seams, tar joint, cracks, oil spots."""
    r = _rng(11)
    macro = fbm(r, [90, 40], [0.7, 0.5])
    grain = r.normal(0, 1, (L, L)).astype(np.float32)
    fine = tnoise(r, 1.6)
    g = 108 + 5 * macro + 9 * fine + 5 * grain
    # aggregate: light stones and dark pits
    stones = (r.random((L, L)) > 0.972).astype(np.float32) * r.uniform(18, 46, (L, L)).astype(np.float32)
    pits = (r.random((L, L)) > 0.985).astype(np.float32) * 22
    g = g + stones - pits
    h = 0.5 * fine + 0.25 * grain + 0.6 * (stones > 0)
    warm = np.zeros((L, L), np.float32)
    # patches (Flickstellen): smoother, darker or blacker, with a tar seam around
    for cx, cy, w, hh, dv in [(150, 330, 190, 120, -13), (400, 90, 120, 150, +8), (60, 40, 80, 70, -9)]:
        sd = np.maximum(np.abs(pd(_X, cx)) - w / 2, np.abs(pd(_Y, cy)) - hh / 2)
        inside = (sd < 0).astype(np.float32)
        seam = np.clip(1 - np.abs(sd) / 2.2, 0, 1)
        g = np.where(inside > 0, g + dv - 2 * macro - 0.35 * (stones - pits), g)
        g = g - 24 * seam
        h = h - 0.7 * seam - 0.15 * inside
    # tar joint (Teerfuge), almost vertical, wavy; and a hairline crack network
    xl = 300 + 7 * np.sin(2 * np.pi * _Y / L * 2 + 1.1) + 3 * np.sin(2 * np.pi * _Y / L * 5)
    joint = np.clip(1 - np.abs(pd(_X, xl)) / 2.4, 0, 1)
    g -= 30 * joint
    h -= 0.9 * joint
    cr = np.zeros((L, L), np.float32)
    for _ in range(5):
        draw_walk(r, r.uniform(0, L), r.uniform(0, L), r.uniform(0, 6.28), 70, 4.5, 1.15, cr, branch=0.05)
    g -= 38 * cr
    h -= 0.8 * cr
    # oil spots (soft, dark, slightly warm, smoother)
    oil = np.zeros((L, L), np.float32)
    for cx, cy, rx, ry in [(210, 120, 26, 15), (450, 410, 18, 30), (95, 460, 20, 12)]:
        oil = np.maximum(oil, blob(cx, cy, rx, ry, 1.6) ** 1.5 * (0.6 + 0.4 * tnoise(r, 6)))
    g -= 22 * oil
    rgb = np.stack([g * 1.05, g * 1.0, g * 0.94], -1)  # warm neutral grey (fidelity S3: was bluish)
    rough = np.clip(0.93 - 0.18 * oil - 0.04 * (stones > 0) + 0.02 * macro, 0.4, 1.0)
    return _img(rgb), _mask(), normal_rough(h, 2.2, rough)


def trottoir():
    """Trottoir: lighter, finer grey asphalt; Leitungsgraben patches with seams; gum / dirt spots."""
    r = _rng(12)
    macro = fbm(r, [110, 45], [0.7, 0.5])
    grain = r.normal(0, 1, (L, L)).astype(np.float32)
    fine = tnoise(r, 1.4)
    stones = (r.random((L, L)) > 0.965).astype(np.float32) * r.uniform(14, 36, (L, L)).astype(np.float32)
    pits = (r.random((L, L)) > 0.98).astype(np.float32) * 16
    g = 110 + 4 * macro + 3 * fine + 2.5 * grain + 0.45 * (stones - pits)  # fidelity S2: darker, smoother
    h = 0.3 * fine + 0.1 * grain + 0.2 * (stones > 0)
    # trench patch (horizontal band, tiles trivially) + an inspection-cover patch
    for cy, wd, dv in [(170, 62, -14), (440, 30, +7)]:
        band = (np.abs(pd(_Y, cy)) < wd / 2).astype(np.float32)
        seam = np.clip(1 - (np.abs(np.abs(pd(_Y, cy)) - wd / 2)) / 1.8, 0, 1)
        g = np.where(band > 0, g + dv - 0.3 * (stones - pits), g) - 26 * seam
        h = h - 0.6 * seam - 0.12 * band
    cr = np.zeros((L, L), np.float32)
    for _ in range(3):
        draw_walk(r, r.uniform(0, L), r.uniform(0, L), r.uniform(0, 6.28), 55, 4.0, 1.0, cr, branch=0.04)
    g -= 34 * cr
    h -= 0.7 * cr
    spots = np.zeros((L, L), np.float32)
    for _ in range(26):  # gum, dirt
        spots = np.maximum(spots, blob(r.uniform(0, L), r.uniform(0, L), r.uniform(2, 5), r.uniform(2, 5), 2.0))
    g -= 30 * spots
    stain = np.clip(tnoise(r, 28) - 0.7, 0, 1.5) * 12
    g -= stain
    rgb = np.stack([g * 1.03, g * 0.995, g * 0.95], -1)
    rough = np.clip(0.92 - 0.03 * macro, 0.5, 1.0)
    return _img(rgb), _mask(), normal_rough(h, 2.0, rough)


def cobble():
    """Reihenpflaster (granite setts ~10 cm, 2.5 m per repeat): gently arced rows, rounded tops, sandy joints."""
    r = _rng(13)
    rows, per = 26, 24
    wob = 0.18 * np.sin(2 * np.pi * _X / L * 2 + 0.7) + 0.08 * np.sin(2 * np.pi * _X / L * 5)
    v = (_Y / L * rows + wob) % rows
    ri = np.floor(v).astype(int) % rows
    fv = v - np.floor(v)
    off = r.random(rows)[ri]
    u = (_X / L * per + off) % per
    ci = np.floor(u).astype(int) % per
    fu = u - np.floor(u)
    sid = ri * per + ci
    tone = r.normal(0, 1, rows * per)[sid].astype(np.float32)
    hue = r.random(rows * per)[sid]
    wj = r.uniform(0.05, 0.1, rows * per)[sid]
    d = np.minimum(np.minimum(fu, 1 - fu) * 1.0, np.minimum(fv, 1 - fv) * 0.95)
    dome = np.clip((d - wj) / 0.28, 0, 1)
    dome = dome * (2 - dome)
    stone = d > wj
    grain = r.normal(0, 1, (L, L)).astype(np.float32)
    mac = fbm(r, [70, 20], [0.7, 0.4])
    base = 128 + 15 * tone + 6 * mac + 5 * grain + 12 * (dome - 0.5)
    pink = (hue < 0.25)[..., None] * np.array([10, -2, -6]) + (hue > 0.78)[..., None] * np.array([-6, -1, 5])
    col = np.stack([base, base * 0.985, base * 0.96], -1) + pink
    joint = np.stack([np.full((L, L), 70.0), np.full((L, L), 66.0), np.full((L, L), 58.0)], -1) + 8 * grain[..., None]
    rgb = np.where(stone[..., None], col, joint) * (0.88 + 0.12 * dome[..., None])
    h = np.where(stone, 0.35 + 0.65 * dome, 0.0) + 0.04 * grain
    rough = np.where(stone, 0.78 - 0.1 * dome, 0.95).astype(np.float32)
    return _img(rgb), _mask(), normal_rough(h, 5.0, rough)


def curb():
    """Granite Randstein face. Used with u = metres, v = metres (only v 0..0.12 visible, bottom of the texture):
    stone joints every 1 m at u=0, dirt at the foot, worn lighter top edge, scuffs, tar/wheel marks."""
    r = _rng(14)
    mac = fbm(r, [120, 30], [0.7, 0.5])
    grain = r.normal(0, 1, (L, L)).astype(np.float32)
    speck = tnoise(r, 1.5)
    g = 176 + 7 * mac + 7 * grain + 7 * speck
    dark = (r.random((L, L)) > 0.93) * r.uniform(15, 45, (L, L))   # biotite flecks
    g -= dark
    vy = _Y / L                                    # metres from the foot of the curb
    foot = np.exp(-vy / 0.018)                     # dirt/road grime at the bottom
    g -= 48 * foot * (0.6 + 0.4 * tnoise(r, 16))
    top = np.exp(-np.abs(vy - 0.118) / 0.006)      # worn arris
    g += 14 * top
    scuff = np.clip(tnoise(r, 8) - 1.1, 0, 2) * np.exp(-vy / 0.05) * 38  # tyre / wheel abrasion
    g -= scuff
    # joint at u = 0 (dark thin seam), and a rare chipped one at 0.5
    j = np.clip(1 - np.abs(pd(_X, 0)) / 1.6, 0, 1)
    g -= 62 * j
    h = 0.4 * speck + 0.2 * grain - 0.9 * j - 0.4 * (foot > 0.5)
    # tone per stone is constant over the whole 1 m: add a little low-frequency tone
    rgb = np.stack([g, g * 0.985, g * 0.96], -1)
    rough = np.clip(0.78 + 0.15 * foot, 0.5, 1.0)
    return _img(rgb), _mask(), normal_rough(h, 2.0, rough)


def gutter():
    """Rinnstein: three rows of granite setts running along u (the curb direction), darker, dirty, sandy joints.
    v spans 0..0.3 m across the strip; 1 m per repeat in u."""
    r = _rng(15)
    rows, per = 12, 8                              # 12 rows over 1 m of v; only v 0..0.3 (3 rows of setts) is visible
    ri = np.floor(_Y / L * rows).astype(int)
    fv = _Y / L * rows - ri
    off = r.random(rows)[ri]
    u = (_X / L * per + off) % per
    ci = np.floor(u).astype(int) % per
    fu = u - np.floor(u)
    sid = ri * per + ci
    tone = r.normal(0, 1, rows * per)[sid].astype(np.float32)
    d = np.minimum(np.minimum(fu, 1 - fu) * 0.7, np.minimum(fv, 1 - fv))
    wj = 0.08
    dome = np.clip((d - wj) / 0.25, 0, 1)
    dome = dome * (2 - dome)
    stone = d > wj
    grain = r.normal(0, 1, (L, L)).astype(np.float32)
    mac = fbm(r, [60, 18], [0.7, 0.5])
    base = 112 + 7 * tone + 4 * mac + 3 * grain + 5 * (dome - 0.5) - 8 * np.clip(tnoise(r, 10) - 0.4, 0, 2)  # S4: calmer, closer to kerb tone
    col = np.stack([base, base * 0.985, base * 0.955], -1)
    joint = np.stack([np.full((L, L), 78.0), np.full((L, L), 74.0), np.full((L, L), 68.0)], -1) + 4 * grain[..., None]
    rgb = np.where(stone[..., None], col, joint)
    h = np.where(stone, 0.3 + 0.7 * dome, 0.0) + 0.04 * grain
    rough = np.where(stone, 0.8, 0.95).astype(np.float32)
    return _img(rgb), _mask(), normal_rough(h, 2.2, rough)
