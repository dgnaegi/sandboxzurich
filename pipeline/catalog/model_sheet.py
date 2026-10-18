"""Software preview (PIL painter's algorithm) -> contact sheet of all catalog models."""
import math
import numpy as np
from PIL import Image, ImageDraw
from model_core import avg_color

TILE = 240


def render(mesh, size=TILE, az=0.62, el=0.42, ss=2):
    S = size * ss
    P = np.array([f[1] for f in mesh.faces]); lo, hi = mesh.bounds()
    c = (lo + hi) / 2
    ca, sa, ce, se = math.cos(az), math.sin(az), math.cos(el), math.sin(el)
    def proj(p):
        x, y, z = p[..., 0] - c[0], p[..., 1] - c[1], p[..., 2] - c[2]
        x1 = x * ca + z * sa; z1 = -x * sa + z * ca               # yaw
        y2 = y * ce - z1 * se; z2 = y * se + z1 * ce              # pitch (camera looks along -z2 -> larger z2 is closer)
        return x1, y2, z2
    X, Y, Z = proj(P)
    sc = 0.86 * S / max(X.max() - X.min(), Y.max() - Y.min())
    im = Image.new("RGB", (S, S), (226, 230, 232)); d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, int(S * 0.9), S, S], fill=(170, 172, 168))
    L = np.array([0.4, 0.8, 0.45]); L /= np.linalg.norm(L)
    order = sorted(range(len(P)), key=lambda i: (mesh.faces[i][0] == "b", Z[i].mean()))
    cx0 = (X.max() + X.min()) / 2; cy0 = (Y.max() + Y.min()) / 2
    for i in order:
        k, tri, cell = mesh.faces[i]
        n = np.cross(tri[1] - tri[0], tri[2] - tri[0]); ln = np.linalg.norm(n)
        if ln < 1e-9: continue
        n /= ln
        vz = n[0] * (-sa) * 0 + 0  # placeholder
        # camera-space normal z (closer = +z2)
        nx1 = n[0] * ca + n[2] * sa; nz1 = -n[0] * sa + n[2] * ca; nz2 = n[1] * se + nz1 * ce
        if k == "o" and nz2 < 0: continue
        sh = 0.55 + 0.45 * max(0.0, float(n @ L)); col = avg_color(cell)
        rgb = tuple(int(min(255, col[j] * sh)) for j in range(3)); al = int(col[3]) if k == "b" else 255
        pts = [(S / 2 + (X[i][j] - cx0) * sc, S * 0.5 - (Y[i][j] - cy0) * sc - S * 0.02) for j in range(3)]
        d.polygon(pts, fill=rgb + (al,))
    return im.resize((size, size), Image.LANCZOS), sc / ss


def sheet(entries, path, cols=6):
    """entries: [(key, mesh)]"""
    rows = math.ceil(len(entries) / cols); W = cols * TILE; H = rows * (TILE + 18)
    out = Image.new("RGB", (W, H), (40, 40, 44)); dr = ImageDraw.Draw(out)
    for n, (key, m) in enumerate(entries):
        r, c = divmod(n, cols); im, _ = render(m)
        out.paste(im, (c * TILE, r * (TILE + 18)))
        lo, hi = m.bounds(); sz = hi - lo
        dr.text((c * TILE + 4, r * (TILE + 18) + TILE + 3), f"{key} {m.tri_count()}t {sz[0]:.1f}x{sz[2]:.1f}x{sz[1]:.1f}m", fill=(235, 235, 235))
    out.save(path, quality=85)
