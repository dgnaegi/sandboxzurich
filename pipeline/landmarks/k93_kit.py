"""Detail kit for the Kreis 9/3 landmarks: procedural textures (windows with reveal/sill/muntins, stone, plaster, tiles, slats,
lettering with free fonts) and geometry helpers (wall bands with real bay spacing, gable/hip roofs with tile UVs, spires,
lettering quads, gates). Textures are painted (no photos). Emissive textures give the night look (runtime scales by night)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import k93_lib as L
from k93_lib import hexc, shade, signed_area

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONTS = ROOT + "/web/public/fonts/"
WHITE = (255, 255, 255, 255)


def font(name, size):
    return ImageFont.truetype(FONTS + name + ".ttf", size)


def rgb(h):
    return hexc(h)[:3]


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def noisy(im, amp=8, seed=3, blur=0.0):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    r = np.random.default_rng(seed).integers(-amp, amp + 1, a.shape[:2])[..., None]
    out = Image.fromarray(np.clip(a + r, 0, 255).astype(np.uint8), "RGB")
    return out.filter(ImageFilter.GaussianBlur(blur)) if blur else out


# ------------------------------------------------------------------------------------------------ window tiles
def tile(nx, ny, mw, mh, painter, seed=1, lit=0.35):
    """nx*ny modules of mw x mh px. painter(d, de, x, y, w, h, rng, on, ix, iy) draws base d and emissive de."""
    rng = np.random.default_rng(seed)
    base = Image.new("RGB", (nx * mw, ny * mh), (255, 255, 255)); em = Image.new("RGB", base.size, (0, 0, 0))
    d, de = ImageDraw.Draw(base), ImageDraw.Draw(em)
    for iy in range(ny):
        for ix in range(nx):
            painter(d, de, ix * mw, iy * mh, mw, mh, rng, bool(rng.random() < lit), ix, iy)
    return base, em


def window(wall="#d9d2c0", frame="#f0ede2", glass="#34414d", fw=0.5, fh=0.55, top=0.2, cols=2, rows=3, arch=False, sill="#cfc8b6",
           surround=None, lintel=None, shutter=None, curtain=True, lit_col=(255, 214, 150), noise=5, plinth=0.0, shade_wall=1.0, mun=2):
    """Punched window in a module: opening (reveal shadow left/top, light right/bottom), frame, muntins, glass with sky gradient,
    optional stone surround / lintel / sill / shutters / round arch. Returns a tile painter."""
    W, F, G = rgb(wall), rgb(frame), rgb(glass)
    S = rgb(surround) if surround else None; LT = rgb(lintel) if lintel else None; SI = rgb(sill)

    def p(d, de, x, y, w, h, rng, on, ix, iy):
        wc = tuple(int(c * shade_wall * (1 + (rng.random() - 0.5) * noise / 100)) for c in W)
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=wc)
        if plinth: d.rectangle([x, y + int(h * (1 - plinth)), x + w - 1, y + h - 1], fill=mix(W, (0, 0, 0), 0.12))
        ww, wh = int(w * fw), int(h * fh)
        x0, y0 = x + (w - ww) // 2, y + int(h * top)
        if S:  # stone surround (Gewaende)
            b = max(3, int(w * 0.055))
            d.rectangle([x0 - b, y0 - b - (ww // 2 if arch else 0), x0 + ww + b, y0 + wh + b], fill=S)
            if arch: d.pieslice([x0 - b, y0 - ww // 2 - b, x0 + ww + b, y0 + ww // 2 + b], 180, 360, fill=S)
        if LT:
            d.rectangle([x0 - 5, y0 - 8, x0 + ww + 5, y0 - 2], fill=LT)
        if shutter:
            sw = max(3, ww // 2 - 1); SH = rgb(shutter)
            for sx in (x0 - sw - 3, x0 + ww + 3):
                d.rectangle([sx, y0, sx + sw, y0 + wh], fill=SH)
                for k in range(y0 + 3, y0 + wh, 4): d.line([sx + 1, k, sx + sw - 1, k], fill=mix(SH, (0, 0, 0), 0.25))
        # opening: dark reveal
        d.rectangle([x0 - 2, y0 - 2 - (ww // 2 if arch else 0), x0 + ww + 2, y0 + wh + 2], fill=mix(W, (0, 0, 0), 0.55))
        if arch: d.pieslice([x0 - 2, y0 - ww // 2 - 2, x0 + ww + 2, y0 + ww // 2 + 2], 180, 360, fill=mix(W, (0, 0, 0), 0.55))
        # frame
        d.rectangle([x0, y0, x0 + ww, y0 + wh], fill=F)
        if arch: d.pieslice([x0, y0 - ww // 2, x0 + ww, y0 + ww // 2], 180, 360, fill=F)
        fb = 2
        gx0, gy0, gx1, gy1 = x0 + fb, y0 + fb, x0 + ww - fb, y0 + wh - fb
        # glass with diagonal sky reflection
        t = 0.55 + 0.35 * rng.random()
        for k in range(gy0, gy1 + 1):
            g = mix(G, (150, 175, 195), 0.28 * (1 - (k - gy0) / max(1, gy1 - gy0)) * t)
            d.line([gx0, k, gx1, k], fill=g)
        if arch:
            d.pieslice([gx0, y0 - ww // 2 + fb, gx1, y0 + ww // 2 - fb], 180, 360, fill=mix(G, (150, 175, 195), 0.3))
        # muntins
        for c in range(1, cols):
            xx = gx0 + (gx1 - gx0) * c // cols; d.line([xx, gy0 - (ww // 2 if arch else 0), xx, gy1], fill=F, width=mun)
        for r in range(1, rows):
            yy = gy0 + (gy1 - gy0) * r // rows; d.line([gx0, yy, gx1, yy], fill=F, width=mun)
        # reveal shading: light line right/bottom of the frame
        d.line([x0 + ww + 1, y0, x0 + ww + 1, y0 + wh], fill=mix(W, (255, 255, 255), 0.3))
        # sill + shadow
        d.rectangle([x0 - 4, y0 + wh + 2, x0 + ww + 4, y0 + wh + 5], fill=SI)
        d.line([x0 - 4, y0 + wh + 6, x0 + ww + 4, y0 + wh + 6], fill=mix(W, (0, 0, 0), 0.35))
        if on:
            cl = lit_col if rng.random() < 0.8 else (200, 225, 255)
            if curtain and rng.random() < 0.35: cl = mix(cl, (255, 150, 90), 0.4)
            de.rectangle([gx0, gy0, gx1, gy1], fill=cl)
            if arch: de.pieslice([gx0, y0 - ww // 2 + fb, gx1, y0 + ww // 2 - fb], 180, 360, fill=cl)
            for c in range(1, cols):
                xx = gx0 + (gx1 - gx0) * c // cols; de.line([xx, gy0, xx, gy1], fill=(0, 0, 0), width=mun)
            for r in range(1, rows):
                yy = gy0 + (gy1 - gy0) * r // rows; de.line([gx0, yy, gx1, yy], fill=(0, 0, 0), width=mun)
    return p


def plain(wall, noise=6):
    W = rgb(wall)
    def p(d, de, x, y, w, h, rng, on, ix, iy):
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=tuple(int(c * (1 + (rng.random() - 0.5) * noise / 100)) for c in W))
    return p


# ------------------------------------------------------------------------------------------------ material textures
def stone_tex(col="#a39f94", course=0.28, w=2.0, size=256, seed=2, rustic=0.0, joint=0.7):
    """Ashlar masonry: courses of height `course` (fraction of tile height per course), blocks vary in colour."""
    rng = np.random.default_rng(seed); C = rgb(col)
    im = Image.new("RGB", (size, size), mix(C, (0, 0, 0), 0.4)); d = ImageDraw.Draw(im)
    n = max(2, int(1 / course)); ch = size / n
    for r in range(n):
        x = -rng.integers(0, int(size * 0.3)); y0 = int(r * ch)
        while x < size:
            bw = int(size * (0.28 + 0.3 * rng.random()))
            t = 1 + (rng.random() - 0.5) * (0.22 + rustic)
            c = tuple(int(v * t) for v in C)
            d.rectangle([x + 1, y0 + 1, x + bw - 1, int(y0 + ch) - 1], fill=c)
            if rustic:  # chiselled face: lighter top/left, dark bottom
                d.line([x + 1, y0 + 1, x + bw - 1, y0 + 1], fill=mix(c, (255, 255, 255), 0.25)); d.line([x + 1, int(y0 + ch) - 1, x + bw - 1, int(y0 + ch) - 1], fill=mix(c, (0, 0, 0), 0.35))
            x += bw
    return noisy(im, 7, seed, 0.4)


def plaster_tex(col="#c9c0ac", size=128, seed=4, amp=7):
    return noisy(Image.new("RGB", (size, size), rgb(col)), amp, seed, 0.6)


def concrete_tex(col="#a8a7a1", size=256, seed=5, panel=(2.0, 1.0), board=True):
    """Off-form concrete: panel joints + tie holes + subtle board texture + stains."""
    C = rgb(col); im = Image.new("RGB", (size, size), C); d = ImageDraw.Draw(im); rng = np.random.default_rng(seed)
    for k in range(0, size, size // 8):
        d.line([0, k, size, k], fill=mix(C, (0, 0, 0), 0.07))
    for k in range(0, size, size // 2):
        d.line([k, 0, k, size], fill=mix(C, (0, 0, 0), 0.22), width=2)
    for yy in (size // 4, 3 * size // 4):
        for xx in (size // 4, 3 * size // 4): d.ellipse([xx - 2, yy - 2, xx + 2, yy + 2], fill=mix(C, (0, 0, 0), 0.3))
    for _ in range(6):  # stains
        x, y = rng.integers(0, size, 2); d.rectangle([x, y, x + rng.integers(3, 10), y + rng.integers(20, 70)], fill=mix(C, (0, 0, 0), 0.06))
    return noisy(im, 6, seed, 0.5)


def tile_roof_tex(col="#9a4a36", size=128, rows=8, cols=6, seed=6, var=0.2, moss=0.0):
    """Biberschwanz-style clay tiles; one texture covers 1 m x 1 m (cols x rows)."""
    C = rgb(col); rng = np.random.default_rng(seed)
    im = Image.new("RGB", (size, size), mix(C, (0, 0, 0), 0.5)); d = ImageDraw.Draw(im)
    ch, cw = size / rows, size / cols
    for r in range(rows):
        for c in range(-1, cols + 1):
            x = c * cw + (cw / 2 if r % 2 else 0); t = 1 + (rng.random() - 0.5) * var
            cc = tuple(int(min(255, v * t)) for v in C)
            if moss and rng.random() < moss: cc = mix(cc, (70, 90, 60), 0.5)
            d.rounded_rectangle([x + 1, r * ch, x + cw - 1, r * ch + ch * 1.6], 3, fill=cc)
            d.line([x + 1, r * ch + 1, x + cw - 1, r * ch + 1], fill=mix(cc, (0, 0, 0), 0.4))
    return noisy(im, 5, seed, 0.3)


def slate_tex(col="#4f5358", size=128, seed=7, rows=10):
    C = rgb(col); rng = np.random.default_rng(seed)
    im = Image.new("RGB", (size, size), mix(C, (0, 0, 0), 0.4)); d = ImageDraw.Draw(im)
    ch = size / rows
    for r in range(rows):
        x = -rng.integers(0, 12)
        while x < size:
            w = int(size * 0.12); t = 1 + (rng.random() - 0.5) * 0.22
            d.rectangle([x + 1, r * ch, x + w - 1, r * ch + ch * 1.4], fill=tuple(int(v * t) for v in C)); x += w
    return noisy(im, 4, seed, 0.3)


def slat_tex(col="#7a3f2e", size=256, n=16, seed=8, gap=0.25):
    """Timber slats (vertical lines) with grain, as on the Letzigrund roof underside."""
    C = rgb(col); rng = np.random.default_rng(seed)
    im = Image.new("RGB", (size, size), mix(C, (0, 0, 0), 0.6)); d = ImageDraw.Draw(im)
    w = size / n
    for k in range(n):
        t = 1 + (rng.random() - 0.5) * 0.25
        d.rectangle([int(k * w + w * gap / 2), 0, int((k + 1) * w - w * gap / 2), size], fill=tuple(int(v * t) for v in C))
    for _ in range(40):
        x = rng.integers(0, size); d.line([x, 0, x, size], fill=mix(C, (0, 0, 0), 0.12))
    for yy in (0, size // 2):
        d.line([0, yy, size, yy], fill=mix(C, (0, 0, 0), 0.5), width=2)
    return noisy(im, 5, seed, 0.3)


def metal_panel_tex(col="#3b3a39", size=256, n=8, seed=9, rust=0.0, rib=True):
    C = rgb(col); rng = np.random.default_rng(seed)
    im = Image.new("RGB", (size, size), C); d = ImageDraw.Draw(im); w = size / n
    for k in range(n):
        t = 1 + (rng.random() - 0.5) * 0.12
        d.rectangle([int(k * w), 0, int((k + 1) * w) - 1, size], fill=tuple(int(v * t) for v in C))
        d.line([int(k * w), 0, int(k * w), size], fill=mix(C, (255, 255, 255), 0.18))
        d.line([int((k + 1) * w) - 1, 0, int((k + 1) * w) - 1, size], fill=mix(C, (0, 0, 0), 0.35))
    if rust:
        for _ in range(60):
            x = rng.integers(0, size); y = rng.integers(0, size); d.rectangle([x, y, x + 2, y + rng.integers(8, 50)], fill=mix(C, (140, 70, 40), rust))
    return noisy(im, 4, seed, 0.2)


def text_tex(text, fnt="Barlow-Bold", fg="#2b2b2b", bg=None, h=64, pad=0.25, spacing=0.0, width=None):
    """Lettering image (RGBA, transparent when bg is None) and its aspect ratio w/h."""
    f = font(fnt, h)
    if spacing:
        ws = [f.getlength(ch) for ch in text]; tw = int(sum(ws) + spacing * h * (len(text) - 1))
    else:
        tw = int(f.getlength(text))
    W = tw + int(h * pad * 2); Hh = int(h * (1 + pad))
    im = Image.new("RGBA", (W, Hh), rgb(bg) + (255,) if bg else (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if spacing:
        x = h * pad
        for ch, w_ in zip(text, ws): d.text((x, h * pad * 0.4), ch, font=f, fill=fg); x += w_ + spacing * h
    else:
        d.text((h * pad, h * pad * 0.4), text, font=f, fill=fg)
    return im, W / Hh


def lamp_mat(M, name="lamps", col="#fff0c4", level=255, emcol=None):
    """Emissive material (glows at night); emcol = emission colour, default warm white."""
    base = Image.new("RGB", (4, 4), rgb(col)); em = Image.new("RGB", (4, 4), emcol or (level, int(level * 0.92), int(level * 0.75)))
    return M.mat(name, rough=0.6, tex=base, emis=em, repeat=True)


# ------------------------------------------------------------------------------------------------ geometry helpers
def edges(pts):
    pts = [tuple(p[:2]) for p in pts]
    if pts[0] == pts[-1]: pts = pts[:-1]
    if signed_area(pts) < 0: pts = pts[::-1]
    return pts


def wall_band(M, mat, poly, z0, z1, bw, sh, nx=1, ny=1, col=WHITE, skip=None, flat=0.0, vrows=None):
    """Walls of polygon `poly` between z0 and z1 with UVs so that `bw` x `sh` metre bays map to one module of an nx x ny tile.
    Bay count per edge is rounded so windows never get cut at corners. skip(i, len) -> True to leave out an edge.
    Returns list of (a, b, L, nrm) edge info."""
    pts = edges(poly); info = []
    nr = max(1, round((z1 - z0) / sh)); vv = nr / ny
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]; Ld = math.hypot(b[0] - a[0], b[1] - a[1])
        if Ld < 0.05: continue
        nxn = (b[1] - a[1]) / Ld; nyn = -(b[0] - a[0]) / Ld
        info.append((a, b, Ld, (nxn, nyn)))
        if skip and skip(i, Ld): continue
        nb = max(1, round(Ld / bw)); uu = nb / nx
        f = 0.82 + 0.18 * abs(nxn) if not flat else 1.0
        M.quad(mat, (*a, z0), (*b, z0), (*b, z1), (*a, z1), shade(col, f), [(0, vv), (uu, vv), (uu, 0), (0, 0)])
    return info


def quad_tex(M, mat, a, b, z0, z1, uv=(0, 0, 1, 1), col=WHITE):
    """Vertical quad from a to b (xy) between z0..z1; uv=(u0,v0,u1,v1) with v0 at the top of the image."""
    u0, v0, u1, v1 = uv
    M.quad(mat, (*a, z0), (*b, z0), (*b, z1), (*a, z1), col, [(u0, v1), (u1, v1), (u1, v0), (u0, v0)])


def lettering(M, mat, c, ang, w, h, z, off=0.0, flip=False):
    """Text plane (full-image uv) centred at c=(x,y) facing local +normal (ang = wall direction), bottom at z."""
    ux, uy = math.cos(ang), math.sin(ang); nx, ny = uy, -ux
    cx, cy = c[0] + nx * off, c[1] + ny * off
    a = (cx - ux * w / 2, cy - uy * w / 2); b = (cx + ux * w / 2, cy + uy * w / 2)
    quad_tex(M, mat, a, b, z, z + h)


def pitched(M, mat, ctr, w, d, z0, rise, rot=0.0, eave=0.4, hip=0.0, tile=1.0, col=WHITE, gable_mat=None, gable_col=None, gable_tile=(4.0, 3.0), base_z=None):
    """Gable (hip=0) or hip roof over a w x d rectangle, ridge along local x, with 1-metre tile UVs. Gable triangles use gable_mat
    (wall texture) when given."""
    cx, cy = ctr; co, si = math.cos(rot), math.sin(rot)
    hw, hd = w / 2 + eave, d / 2 + eave
    def P(x, y, z): return (cx + x * co - y * si, cy + x * si + y * co, z)
    rl = max(0.0, hw - hip * hd); zt = z0 + rise
    A, B, C, D = P(-hw, -hd, z0), P(hw, -hd, z0), P(hw, hd, z0), P(-hw, hd, z0)
    R1, R2 = P(-rl, 0, zt), P(rl, 0, zt)
    sl = math.hypot(hd, rise)
    M.quad(mat, A, B, R2, R1, col, [(0, 0), (2 * hw / tile, 0), ((hw + rl) / tile, sl / tile), ((hw - rl) / tile, sl / tile)])
    M.quad(mat, C, D, R1, R2, shade(col, 0.82), [(0, 0), (2 * hw / tile, 0), ((hw + rl) / tile, sl / tile), ((hw - rl) / tile, sl / tile)])
    if rl < hw - 1e-6:   # hip ends
        se = math.hypot(hw - rl, rise)
        M.tri(mat, B, C, R2, shade(col, .9), [(0, 0), (2 * hd / tile, 0), (hd / tile, se / tile)])
        M.tri(mat, D, A, R1, shade(col, .9), [(0, 0), (2 * hd / tile, 0), (hd / tile, se / tile)])
    elif gable_mat is not None:
        gc = gable_col or WHITE
        M.tri(gable_mat, B, C, R2, gc, [(0, 1), (d / gable_tile[0], 1), (d / 2 / gable_tile[0], 0.2)])
        M.tri(gable_mat, D, A, R1, gc, [(0, 1), (d / gable_tile[0], 1), (d / 2 / gable_tile[0], 0.2)])
    return P


def spire(M, mat, c, r, z0, z1, n=4, rot=0.0, col=WHITE, tile=1.0, r_top=0.0, tex_scale=1.0):
    """n-sided pyramid/frustum with UVs (metres/tile)."""
    cx, cy = c
    for i in range(n):
        a0, a1 = rot + 2 * math.pi * i / n, rot + 2 * math.pi * (i + 1) / n
        p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0)); p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        q0 = (cx + r_top * math.cos(a0), cy + r_top * math.sin(a0)); q1 = (cx + r_top * math.cos(a1), cy + r_top * math.sin(a1))
        sl = math.hypot(r - r_top, z1 - z0); wd = 2 * r * math.sin(math.pi / n)
        f = 0.78 + 0.22 * math.cos((a0 + a1) / 2 - 0.9)
        if r_top < 0.02:
            M.tri(mat, (*p0, z0), (*p1, z0), (cx, cy, z1), shade(col, f), [(0, 0), (wd / tile, 0), (wd / 2 / tile, sl / tile)])
        else:
            wt = 2 * r_top * math.sin(math.pi / n); o = (wd - wt) / 2
            M.quad(mat, (*p0, z0), (*p1, z0), (*q1, z1), (*q0, z1), shade(col, f), [(0, 0), (wd / tile, 0), ((o + wt) / tile, sl / tile), (o / tile, sl / tile)])


def box_tex(M, mat, c, s, rot=0.0, col=WHITE, tile=(2.0, 2.0), top=None):
    """Axis box with metre-based UV on the sides (for textured masonry/plaster)."""
    cx, cy, cz = c; sx, sy, sz = s[0] / 2, s[1] / 2, s[2] / 2; co, si = math.cos(rot), math.sin(rot)
    P = lambda dx, dy, dz: (cx + dx * co - dy * si, cy + dx * si + dy * co, cz + dz)
    pts = [P(-sx, -sy, 0), P(sx, -sy, 0), P(sx, sy, 0), P(-sx, sy, 0)]
    for i, (w_, f) in enumerate(((s[0], .88), (s[1], .78), (s[0], .88), (s[1], .78))):
        a, b = pts[i], pts[(i + 1) % 4]
        M.quad(mat, (a[0], a[1], cz - sz), (b[0], b[1], cz - sz), (b[0], b[1], cz + sz), (a[0], a[1], cz + sz), shade(col, f),
               [(0, s[2] / tile[1]), (w_ / tile[0], s[2] / tile[1]), (w_ / tile[0], 0), (0, 0)])
    M.quad(mat, P(-sx, -sy, sz), P(sx, -sy, sz), P(sx, sy, sz), P(-sx, sy, sz), top or col, [(0, 0), (s[0] / tile[0], 0), (s[0] / tile[0], s[1] / tile[1]), (0, s[1] / tile[1])])


def rect_pts(c, w, d, rot):
    co, si = math.cos(rot), math.sin(rot)
    return [(c[0] + x * co - y * si, c[1] + x * si + y * co) for x, y in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]


def tube(M, mat, a, b, r, col, n=6):
    """Thin cylinder between 3D points a and b (steel mast, cable, rail)."""
    a = np.array(a, float); b = np.array(b, float); v = b - a; Ln = np.linalg.norm(v)
    if Ln < 1e-6: return
    v = v / Ln; t = np.cross(v, [0, 0, 1.0]) if abs(v[2]) < 0.99 else np.array([1.0, 0, 0]); t = t / np.linalg.norm(t); s = np.cross(v, t)
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        o0 = (t * math.cos(a0) + s * math.sin(a0)) * r; o1 = (t * math.cos(a1) + s * math.sin(a1)) * r
        M.quad(mat, tuple(a + o0), tuple(a + o1), tuple(b + o1), tuple(b + o0), shade(col, 0.8 + 0.2 * math.cos((a0 + a1) / 2)), [(0, 0), (1, 0), (1, 1), (0, 1)])


def fence_line(M, mat, pts, h, col, post=2.5, r=0.03, bars=0.12):
    """Iron railing along a polyline (posts + top/bottom rail + pickets, thin boxes)."""
    for a, b in zip(pts[:-1], pts[1:]):
        Ld = math.hypot(b[0] - a[0], b[1] - a[1]); ang = math.atan2(b[1] - a[1], b[0] - a[0]); n = max(1, int(Ld / bars))
        for z in (0.12, h - 0.06):
            M.box(mat, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z), (Ld, 0.05, 0.05), col, rot=ang)
        for k in range(n + 1):
            t = k / n; M.box(mat, (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, h / 2), (0.025, 0.025, h), col, rot=ang)


def wall_aligned(M, mat, poly, z0, z1, bw, sh, c, u, s0, nx=1, ny=1, col=WHITE, flat=0.0, skip=None):
    """Like wall_band, but edges roughly parallel to direction u get texture modules aligned to a global grid:
    module boundaries at s = s0 + k*bw (s = dot(p - c, u)). Other edges round the bay count. Returns edge infos."""
    pts = edges(poly); info = []
    nr = max(1, round((z1 - z0) / sh)); vv = (z1 - z0) / sh / ny
    c = np.array(c, float); u = np.array(u, float)
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]; Ld = math.hypot(b[0] - a[0], b[1] - a[1])
        if Ld < 0.05: continue
        d = ((b[0] - a[0]) / Ld, (b[1] - a[1]) / Ld); nxn, nyn = d[1], -d[0]
        info.append((a, b, Ld, (nxn, nyn)))
        if skip and skip(i, Ld): continue
        f = 0.82 + 0.18 * abs(nxn) if not flat else 1.0
        if abs(d[0] * u[0] + d[1] * u[1]) > 0.9:
            sa = float(np.dot(np.array(a) - c, u)); sb = float(np.dot(np.array(b) - c, u))
            ua, ub = (sa - s0) / bw / nx, (sb - s0) / bw / nx
        else:
            ua, ub = 0.0, max(1, round(Ld / bw)) / nx
        M.quad(mat, (*a, z0), (*b, z0), (*b, z1), (*a, z1), shade(col, f), [(ua, vv), (ub, vv), (ub, 0), (ua, 0)])
    return info


def clock_tex(size=256, roman=True, face="#f1efe6", ink="#262a3a", ring="#c9c4b2", red="#b83a4a"):
    """Square station clock: roman numerals, red 13-24 inner numbers, hands at 10:10."""
    im = Image.new("RGB", (size, size), rgb(ring)); d = ImageDraw.Draw(im)
    m = size * 0.06; d.rectangle([m, m, size - m, size - m], fill=rgb(face))
    cx = cy = size / 2
    rn = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    f = font("Barlow-Bold", int(size * 0.11)); f2 = font("Barlow-Bold", int(size * 0.07))
    for k in range(12):
        a = math.radians(k * 30 - 90); r_ = size * 0.37
        t = rn[k]; w = f.getlength(t)
        d.text((cx + r_ * math.cos(a) - w / 2, cy + r_ * math.sin(a) - size * 0.07), t, font=f, fill=rgb(ink))
        t2 = str(k + 12 if k else 24); w2 = f2.getlength(t2); r2 = size * 0.24
        d.text((cx + r2 * math.cos(a) - w2 / 2, cy + r2 * math.sin(a) - size * 0.045), t2, font=f2, fill=rgb(red))
    for ang, ln, wd in ((math.radians(10 * 6 - 90 + 0), 0.30, 6), (math.radians(-60 - 30 + 0), 0.22, 9)):
        pass
    d.line([cx, cy, cx + size * 0.32 * math.cos(math.radians(-60)), cy + size * 0.32 * math.sin(math.radians(-60))], fill=rgb(ink), width=max(2, size // 40))
    d.line([cx, cy, cx + size * 0.22 * math.cos(math.radians(-150)), cy + size * 0.22 * math.sin(math.radians(-150))], fill=rgb(ink), width=max(3, size // 28))
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=rgb(ink))
    return im


def ribbon(wall="#b8bcb6", glass="#4d6a72", band=0.62, y0=0.18, mull="#d5d9d6", lit_col=(255, 226, 170), noise=4, slab="#a7aca7", sky=0.35, lit_p=0.8):
    """Office ribbon window module: spandrel panel + horizontal glass band with a mullion at the module edge and a thin slab edge."""
    W, G, ML, SL = rgb(wall), rgb(glass), rgb(mull), rgb(slab)

    def p(d, de, x, y, w, h, rng, on, ix, iy):
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=tuple(int(c * (1 + (rng.random() - 0.5) * noise / 100)) for c in W))
        wy0, wy1 = y + int(h * y0), y + int(h * (y0 + band))
        t = rng.random()
        for k in range(wy0, wy1):
            f = (k - wy0) / max(1, wy1 - wy0)
            d.line([x + 2, k, x + w - 3, k], fill=mix(G, (170, 200, 215), sky * (1 - f) * (0.6 + 0.4 * t)))
        d.line([x, wy0 - 1, x + w, wy0 - 1], fill=mix(W, (0, 0, 0), 0.35)); d.rectangle([x, wy1, x + w, wy1 + 2], fill=SL)
        d.rectangle([x, wy0, x + 2, wy1], fill=ML); d.rectangle([x + w // 2, wy0, x + w // 2 + 1, wy1], fill=mix(ML, G, 0.4))
        d.rectangle([x, y + h - 3, x + w, y + h - 1], fill=SL)
        if on:
            cl = lit_col if rng.random() < 0.85 else (205, 228, 255)
            de.rectangle([x + 3, wy0 + 1, x + w - 3, wy1 - 1], fill=cl)
            de.rectangle([x + w // 2, wy0, x + w // 2 + 1, wy1], fill=(40, 40, 40))
    return p


def sphere(M, mat, c, r, col, n=10, rings=5, z=None):
    """UV sphere (flat shaded) centred at c=(x, y), centre height z."""
    cx, cy = c
    P = lambda th, a: (cx + r * math.cos(th) * math.cos(a), cy + r * math.cos(th) * math.sin(a), z + r * math.sin(th))
    for k in range(rings):
        t0 = -math.pi / 2 + math.pi * k / rings; t1 = -math.pi / 2 + math.pi * (k + 1) / rings
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            f = 0.78 + 0.22 * math.cos((a0 + a1) / 2 - 0.9) * (0.6 + 0.4 * math.cos((t0 + t1) / 2))
            if k == 0: M.tri(mat, P(t0, a0), P(t1, a1), P(t1, a0), shade(col, f))
            elif k == rings - 1: M.tri(mat, P(t0, a0), P(t0, a1), P(t1, a0), shade(col, f))
            else: M.quad(mat, P(t0, a0), P(t0, a1), P(t1, a1), P(t1, a0), shade(col, f))
