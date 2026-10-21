#!/usr/bin/env python3
"""Render the loading-screen intro video (GTA-style slideshow: Ken-Burns stills, hard cuts with flash,
chunky captions, vignette, grain, title card) from research/loading_stills/ (made by web/tests/loading_shots.mjs).
Outputs in web/public/loading/: intro.mp4/.webm (landscape 1280x720), intro_p.mp4/.webm (portrait 576x1024),
poster.jpg, poster_p.jpg.  Needs ffmpeg + Pillow + numpy.  Usage: python3 pipeline/loading_video.py"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'research/loading_stills'
OUT = ROOT / 'web/public/loading'
FONT = str(ROOT / 'web/public/fonts/Anton-Regular.ttf')
FPS, T_TITLE, T_SHOT = 24, 2.4, 3.0
PINK = (255, 25, 117)   # #FF1975 (User 2026-10-21)
FFMPEG = '/opt/homebrew/bin/ffmpeg'


def ease(u): return u * u * (3 - 2 * u)


def text_layer(W, H, lines, portrait):
    """RGBA layer with outlined caption lines. lines: [(text, size, fill)]"""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    y = H - (int(H * 0.17) if portrait else 190)
    scale = W / (576 if portrait else 1280)
    for text, size, fill in lines:
        size = int(size * scale)
        f = ImageFont.truetype(FONT, size)
        while d.textlength(text, font=f) > W * 0.9 and size > 20:
            size -= 2; f = ImageFont.truetype(FONT, size)
        w = d.textlength(text, font=f)
        x = (W - w) / 2 if portrait else 64 * scale
        d.text((x + 5, y + 6), text, font=f, fill=(0, 0, 0, 200), stroke_width=int(9 * scale), stroke_fill=(0, 0, 0, 200))
        d.text((x, y), text, font=f, fill=fill, stroke_width=int(7 * scale), stroke_fill=(0, 0, 0, 255))
        y += int(size * 1.12)
    return im


# title card words (colour per word); the internal project name is never shown (User 2026-10-21), the public name comes later
TITLE = [('ZÜRICH', PINK)]


def title_layer(W, H, portrait):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sc = W / (576 if portrait else 1280)
    f = ImageFont.truetype(FONT, int((120 if portrait else 150) * sc))
    parts = TITLE
    if portrait:
        ys = [H * 0.36 + i * 130 * sc for i in range(len(parts))]
        for (t, c), y in zip(parts, ys):
            w = d.textlength(t, font=f)
            d.text(((W - w) / 2 + 5, y + 6), t, font=f, fill=(0, 0, 0, 255), stroke_width=int(10 * sc), stroke_fill=(0, 0, 0, 255))
            d.text(((W - w) / 2, y), t, font=f, fill=c, stroke_width=int(7 * sc), stroke_fill=(0, 0, 0, 255))
    else:
        ws = [d.textlength(t + ' ', font=f) for t, _ in parts]
        x, y = (W - sum(ws) + d.textlength(' ', font=f)) / 2, H * 0.38
        for (t, c), w in zip(parts, ws):
            d.text((x + 5, y + 6), t, font=f, fill=(0, 0, 0, 255), stroke_width=10, stroke_fill=(0, 0, 0, 255))
            d.text((x, y), t, font=f, fill=c, stroke_width=7, stroke_fill=(0, 0, 0, 255))
            x += w
    return im


def vignette(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    return (1 - 0.38 * np.clip((r - 0.55) / 0.9, 0, 1) ** 1.6)[..., None]


def gradient_bg(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.clip(np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 1.6, 0, 1)[..., None]
    return (np.array([42, 32, 54], np.float32) * (1 - r) + np.array([18, 13, 24], np.float32) * r)


def paste(frame, layer, dx=0, alpha=1.0):
    im = Image.fromarray(frame.clip(0, 255).astype(np.uint8)).convert('RGBA')
    if alpha < 1: layer = layer.copy(); layer.putalpha(layer.getchannel('A').point(lambda a: int(a * alpha)))
    big = Image.new('RGBA', im.size, (0, 0, 0, 0)); big.paste(layer, (int(dx), 0))
    return np.asarray(Image.alpha_composite(im, big).convert('RGB')).astype(np.float32)


def render(portrait, shots):
    W, H = (576, 1024) if portrait else (1280, 720)
    sfx = '_p' if portrait else ''
    vig = vignette(W, H); rng = np.random.default_rng(7)
    grain = [(rng.normal(0, 2.2, (H, W, 1))).astype(np.float32) for _ in range(6)]
    cmd = [FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '29', '-pix_fmt', 'yuv420p', '-profile:v', 'main',
           '-movflags', '+faststart', '-an', str(OUT / f'intro{sfx}.mp4')]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = 0; poster = None
    def emit(fr):
        nonlocal n
        fr = fr * vig + grain[n % 6]
        enc.stdin.write(fr.clip(0, 255).astype(np.uint8).tobytes()); n += 1
    # title card
    bg, tl = gradient_bg(W, H), title_layer(W, H, portrait)
    for i in range(int(T_TITLE * FPS)):
        u = i / (T_TITLE * FPS)
        fr = paste(bg, tl, alpha=min(1, i / 6))
        if poster is None: poster = fr.copy()
        emit(fr * min(1, 0.4 + i / 8) if i < 8 else fr)
    for k, s in enumerate(shots):
        im = Image.open(SRC / f"{s['file']}.jpg").convert('RGB')
        sw, sh = im.size
        # base window: full image (landscape) or portrait-aspect strip centred on the focus point
        bw = sh * W / H if portrait else sw; bh = sh
        cx0 = min(max(s['fx'] * sw, bw / 2), sw - bw / 2) if portrait else sw / 2; cy0 = sh / 2
        zin = k % 2 == 0
        z0, z1 = (1.0, 1.16) if zin else (1.16, 1.0)
        tx = min(max(s['fx'] * sw, bw / 2), sw - bw / 2); ty = s['fy'] * sh
        lay = text_layer(W, H, [(s['caption'].split(' · ')[0], 92, (255, 255, 255)), (s['caption'].split(' · ')[1], 46, PINK)], portrait)
        N = int(T_SHOT * FPS)
        for i in range(N):
            u = ease(i / (N - 1)); z = z0 + (z1 - z0) * u
            w, h = bw / z, bh / z
            drift = u if zin else 1 - u
            cx = cx0 + (tx - cx0) * drift * 0.5; cy = cy0 + (ty - cy0) * drift * 0.5
            l = min(max(cx - w / 2, 0), sw - w); t = min(max(cy - h / 2, 0), sh - h)
            fr = np.asarray(im.resize((W, H), Image.BICUBIC, box=(l, t, l + w, t + h))).astype(np.float32)
            ci = (i - 8) / 6  # caption pops in after 8 frames
            if ci > 0: fr = paste(fr, lay, dx=-40 * (1 - ease(min(1, ci))), alpha=min(1, ci))
            if i < 3: fr = fr + (255 - fr) * (0.7, 0.4, 0.15)[i]  # cut flash
            emit(fr)
    enc.stdin.close(); enc.wait()
    Image.fromarray(poster.clip(0, 255).astype(np.uint8)).save(OUT / f'poster{sfx}.jpg', quality=70, optimize=True)
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', str(OUT / f'intro{sfx}.mp4'), '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '40',
                    '-row-mt', '1', '-deadline', 'good', '-cpu-used', '2', '-an', str(OUT / f'intro{sfx}.webm')], check=True)
    for ext in ('mp4', 'webm'): print(f'intro{sfx}.{ext}', (OUT / f'intro{sfx}.{ext}').stat().st_size // 1024, 'kB')


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    shots = json.load(open(SRC / 'manifest.json'))
    # note: stills are 1280x720 jpgs, name = file field
    shots = [{**s, 'file': s['file'].removesuffix('.jpg')} for s in shots]
    for p in (False, True): render(p, shots)
    import shutil; shutil.copy(OUT / 'intro.mp4', ROOT / 'preview/loading_intro.mp4')
