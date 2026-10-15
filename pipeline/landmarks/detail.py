"""Geometry-detail helpers: recessed windows with reveals/sills, ribbon floors, slabs, glass atlas with curtains + night emissive.
Wall frame: origin org (x,y), unit tangent t, outward normal n (right of a->b on a CCW ring), u along t, z up."""
import math
import numpy as np
import shapely
from shapely.geometry import Polygon
from PIL import Image, ImageDraw
from lm import hexc, shade


def P3(org, t, n, u, z, d=0.0):
    return (org[0] + t[0] * u + n[0] * d, org[1] + t[1] * u + n[1] * d, z)


def frame_of(a, b):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    return L, t, (t[1], -t[0])


def _oriented(m, mat, pts, nrm, uv, col):
    p = np.array(pts, float); n = np.cross(p[1] - p[0], p[2] - p[0])
    if np.dot(n, nrm) < 0:
        pts = pts[::-1]; uv = uv[::-1]
    if len(pts) == 4: m.quad(mat, pts, uv, col, n=tuple(nrm))
    else: m.tri(mat, pts, uv, col)


def poly_wall(m, mat, poly_uz, org, t, n, d, col, uvf):
    """Triangulate a (u,z) polygon (holes ok) onto the wall plane at depth d. uvf(u,z)->(U,V)."""
    for g in shapely.constrained_delaunay_triangles(poly_uz).geoms:
        c = list(g.exterior.coords)[:3]
        if not poly_uz.buffer(1e-6).contains(g.representative_point()): continue
        pts = [P3(org, t, n, u, z, d) for u, z in c]
        _oriented(m, mat, pts, (n[0], n[1], 0), [uvf(u, z) for u, z in c], col)


def rect_pts(u0, z0, u1, z1):
    return [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]


def arch_pts(u0, z0, u1, zs, n=8):
    """Rect from z0 up to spring line zs with a semicircular head."""
    r = (u1 - u0) / 2; cx = (u0 + u1) / 2
    pts = [(u0, z0), (u1, z0), (u1, zs)]
    for i in range(1, n):
        a = math.pi * i / n; pts.append((cx + r * math.cos(a), zs + r * math.sin(a)))
    pts += [(u0, zs)]
    return pts


NV = 8


def bay(m, mw, mg, mf, org, t, n, u0, u1, z0, z1, hole, depth, k, wall_col, reveal_col, wmod=(4.0, 4.0), sill=None):
    """One wall bay [u0,u1]x[z0,z1] with an opening `hole` (list of (u,z) CCW) recessed by `depth`, glass variant k."""
    Hh = Polygon(hole)
    W = Polygon(rect_pts(u0, z0, u1, z1)).difference(Hh)
    poly_wall(m, mw, W, org, t, n, 0.0, wall_col, lambda u, z: (u / wmod[0], z / wmod[1]))
    h = list(hole)
    for i in range(len(h)):
        p, q = h[i], h[(i + 1) % len(h)]
        if math.hypot(q[0] - p[0], q[1] - p[1]) < 1e-4: continue
        # reveal faces into the opening: left of p->q in the (u,z) plane
        du, dz = q[0] - p[0], q[1] - p[1]; l = math.hypot(du, dz)
        nl = (t[0] * (-dz / l), t[1] * (-dz / l), du / l)
        pts = [P3(org, t, n, p[0], p[1], 0), P3(org, t, n, q[0], q[1], 0), P3(org, t, n, q[0], q[1], -depth), P3(org, t, n, p[0], p[1], -depth)]
        _oriented(m, mf, pts, nl, [(0, 0), (1, 0), (1, 1), (0, 1)], reveal_col)
    # glass pane at depth, uv into atlas cell k (windows occupy the top 3/4 of the atlas image)
    hz0 = min(p[1] for p in h); hz1 = max(p[1] for p in h); hu0 = min(p[0] for p in h); hu1 = max(p[0] for p in h)
    cu0, cu1 = k / NV, (k + 1) / NV
    guv = lambda u, z: (cu0 + (cu1 - cu0) * (u - hu0) / (hu1 - hu0), 0.25 + 0.75 * (z - hz0) / (hz1 - hz0))
    poly_wall(m, mg, Hh, org, t, n, -depth, (255, 255, 255, 255), guv)
    if sill:  # projecting sill below the opening
        su0, su1 = hu0 - 0.1, hu1 + 0.1; sz1 = hz0; sz0 = hz0 - 0.14; o = sill
        for pts, nn in (([P3(org, t, n, su0, sz1, o), P3(org, t, n, su1, sz1, o), P3(org, t, n, su1, sz1, 0), P3(org, t, n, su0, sz1, 0)], (0, 0, 1)),
                        ([P3(org, t, n, su0, sz0, o), P3(org, t, n, su1, sz0, o), P3(org, t, n, su1, sz1, o), P3(org, t, n, su0, sz1, o)], (n[0], n[1], 0))):
            _oriented(m, mf, pts, nn, [(0, 0), (1, 0), (1, 1), (0, 1)], reveal_col)


def wall_run(m, mw, mg, mf, a, b, z0, nfloor, fh, bayw, hole_fn, depth, wall_col, reveal_col, rng, wmod=(4.0, 4.0), sill=None, margin=0.0):
    """Equal bays along edge a->b, nfloor floors; hole_fn(u0,u1,zf0,zf1,floor)->hole polygon or None."""
    L, t, n = frame_of(a, b)
    nb = max(1, int(round(L / bayw))); bw = L / nb
    for f in range(nfloor):
        for i in range(nb):
            u0, u1 = i * bw, (i + 1) * bw
            hole = hole_fn(u0, u1, z0 + f * fh, z0 + (f + 1) * fh, f)
            if hole is None:
                poly_wall(m, mw, Polygon(rect_pts(u0, z0 + f * fh, u1, z0 + (f + 1) * fh)), a, t, n, 0.0, wall_col, lambda u, z: (u / wmod[0], z / wmod[1]))
            else:
                bay(m, mw, mg, mf, a, t, n, u0, u1, z0 + f * fh, z0 + (f + 1) * fh, hole, depth, int(rng.integers(0, NV)), wall_col, reveal_col, wmod, sill)


def ribbon_floors(m, mw, mg, mf, a, b, z0, nfloor, fh, sp, wh, depth, wall_col, reveal_col, rng, wmod=(6.0, 6.0), seg=3.0, slab_out=0.0, slab_col=None, pier=0.0):
    """Floor-by-floor ribbon window: spandrel below, head above, recessed glass band (split into `seg` m panes)."""
    L, t, n = frame_of(a, b)
    nb = max(1, int(round(L / seg))); bw = L / nb
    for f in range(nfloor):
        zf = z0 + f * fh
        poly_wall(m, mw, Polygon(rect_pts(0, zf, L, zf + sp)), a, t, n, 0.0, wall_col, lambda u, z: (u / wmod[0], z / wmod[1]))
        poly_wall(m, mw, Polygon(rect_pts(0, zf + sp + wh, L, zf + fh)), a, t, n, 0.0, wall_col, lambda u, z: (u / wmod[0], z / wmod[1]))
        # sill plate (top of spandrel, recessed deck) and soffit
        _oriented(m, mf, [P3(a, t, n, 0, zf + sp, 0), P3(a, t, n, L, zf + sp, 0), P3(a, t, n, L, zf + sp, -depth), P3(a, t, n, 0, zf + sp, -depth)], (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)], reveal_col)
        _oriented(m, mf, [P3(a, t, n, 0, zf + sp + wh, 0), P3(a, t, n, L, zf + sp + wh, 0), P3(a, t, n, L, zf + sp + wh, -depth), P3(a, t, n, 0, zf + sp + wh, -depth)], (0, 0, -1), [(0, 0), (1, 0), (1, 1), (0, 1)], reveal_col)
        for i in range(nb):
            u0, u1 = i * bw, (i + 1) * bw
            k = int(rng.integers(0, NV)); cu0, cu1 = k / NV, (k + 1) / NV
            pts = [P3(a, t, n, u0 + pier, zf + sp, -depth), P3(a, t, n, u1 - pier, zf + sp, -depth), P3(a, t, n, u1 - pier, zf + sp + wh, -depth), P3(a, t, n, u0 + pier, zf + sp + wh, -depth)]
            m.quad(mg, pts, [(cu0, 0.25), (cu1, 0.25), (cu1, 1.0), (cu0, 1.0)], (255, 255, 255, 255), n=(n[0], n[1], 0))
            if pier > 0:   # mullion posts
                for uu in (u0, u1):
                    _oriented(m, mf, [P3(a, t, n, uu - pier, zf + sp, 0), P3(a, t, n, uu + pier, zf + sp, 0), P3(a, t, n, uu + pier, zf + sp + wh, 0), P3(a, t, n, uu - pier, zf + sp + wh, 0)], (n[0], n[1], 0), [(0, 0), (1, 0), (1, 1), (0, 1)], reveal_col)
        if slab_out > 0:
            sc = slab_col or reveal_col; zt, zb = zf + sp * 0.9, zf
            _oriented(m, mf, [P3(a, t, n, 0, zb, slab_out), P3(a, t, n, L, zb, slab_out), P3(a, t, n, L, zt, slab_out), P3(a, t, n, 0, zt, slab_out)], (n[0], n[1], 0), [(0, 0), (1, 0), (1, 1), (0, 1)], sc)
            _oriented(m, mf, [P3(a, t, n, 0, zt, slab_out), P3(a, t, n, L, zt, slab_out), P3(a, t, n, L, zt, 0), P3(a, t, n, 0, zt, 0)], (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)], shade(sc, 1.1))
            _oriented(m, mf, [P3(a, t, n, 0, zb, slab_out), P3(a, t, n, L, zb, slab_out), P3(a, t, n, L, zb, 0), P3(a, t, n, 0, zb, 0)], (0, 0, -1), [(0, 0), (1, 0), (1, 1), (0, 1)], shade(sc, 0.7))


def band(m, mat, a, b, z0, z1, out, col, uv=None):
    """Projecting band (cornice/slab edge) along a->b: front, top, bottom faces; thickness z1-z0, projection `out`."""
    L, t, n = frame_of(a, b); uv = uv or [(0, 0), (1, 0), (1, 1), (0, 1)]
    _oriented(m, mat, [P3(a, t, n, 0, z0, out), P3(a, t, n, L, z0, out), P3(a, t, n, L, z1, out), P3(a, t, n, 0, z1, out)], (n[0], n[1], 0), uv, col)
    _oriented(m, mat, [P3(a, t, n, 0, z1, out), P3(a, t, n, L, z1, out), P3(a, t, n, L, z1, 0), P3(a, t, n, 0, z1, 0)], (0, 0, 1), uv, shade(col, 1.1))
    _oriented(m, mat, [P3(a, t, n, 0, z0, out), P3(a, t, n, L, z0, out), P3(a, t, n, L, z0, 0), P3(a, t, n, 0, z0, 0)], (0, 0, -1), uv, shade(col, 0.7))


def pillar(m, mat, x, y, w, d, z0, z1, rot, col):
    m.box(mat, x, y, w, d, z0, z1, rot=rot, col=col)


# ---- glass atlas ---------------------------------------------------------------
def glass_atlas(frame="#e9e6dd", glass="#2b3a46", sky="#7fa3b8", tint=None, bars=True, seed=1, sign=None, cw=64, ch=96, lit_p=0.5, curtains=True):
    """8 window variants (top 96 px) + sign strip (bottom 32 px, full width). Returns (base RGBA, emissive RGB)."""
    rng = np.random.default_rng(seed)
    W, H = NV * cw, ch + 32
    base = Image.new("RGBA", (W, H), hexc(glass)); em = Image.new("RGB", (W, H), (0, 0, 0))
    d, de = ImageDraw.Draw(base), ImageDraw.Draw(em)
    G, S, F = hexc(glass), hexc(sky), hexc(frame)
    for k in range(NV):
        x0 = k * cw
        for y in range(ch):   # sky reflection gradient
            f = max(0.0, 1 - y / (ch * 0.9)) * 0.45
            c = tuple(int(G[i] * (1 - f) + S[i] * f) for i in range(3)) + (255,)
            d.line([x0, y, x0 + cw, y], fill=c)
        lit = rng.random() < lit_p
        cur = None
        if curtains and rng.random() < 0.7:
            cc = [(236, 228, 210), (214, 190, 150), (200, 120, 100), (150, 170, 190), (230, 230, 235), (120, 150, 110)][int(rng.integers(0, 6))]
            frac = rng.choice([0.35, 0.55, 0.8, 1.0]); side = rng.random() < 0.5
            cur = (cc, frac, side)
            cw_ = int((cw - 8) * frac)
            xa = x0 + 4 if side else x0 + cw - 4 - cw_
            d.rectangle([xa, 6, xa + cw_, ch - 6], fill=cc + (255,)); 
            for xx in range(xa, xa + cw_, 5): d.line([xx, 6, xx, ch - 6], fill=shade(cc + (255,), 0.9))
        if lit:
            warm = [(255, 214, 150), (255, 232, 190), (230, 235, 255), (255, 190, 120)][int(rng.integers(0, 4))]
            de.rectangle([x0 + 3, 4, x0 + cw - 3, ch - 4], fill=warm)
            if cur:
                cc, frac, side = cur; cw_ = int((cw - 8) * frac); xa = x0 + 4 if side else x0 + cw - 4 - cw_
                de.rectangle([xa, 6, xa + cw_, ch - 6], fill=tuple(int(v * 0.55) for v in cc))
        if bars:
            d.rectangle([x0 + cw // 2 - 1, 0, x0 + cw // 2 + 1, ch], fill=F)
            d.rectangle([x0, int(ch * 0.30) - 1, x0 + cw, int(ch * 0.30) + 1], fill=F)
            if lit: de.rectangle([x0 + cw // 2 - 1, 0, x0 + cw // 2 + 1, ch], fill=(0, 0, 0)); de.rectangle([x0, int(ch * 0.30) - 1, x0 + cw, int(ch * 0.30) + 1], fill=(0, 0, 0))
        d.rectangle([x0, 0, x0 + cw - 1, ch - 1], outline=F, width=3)
        if lit: de.rectangle([x0, 0, x0 + cw - 1, ch - 1], outline=(0, 0, 0), width=3)
    if sign:
        sign(d, de, 0, ch, W, 32)
    return base, em


def text_sign(text, bg="#14181b", fg="#f4f1e8", size=26, bold=True, glow=(255, 240, 200)):
    from PIL import ImageFont
    def paint(d, de, x, y, w, h):
        d.rectangle([x, y, x + w, y + h], fill=hexc(bg))
        f = None
        for p in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc"):
            try: f = ImageFont.truetype(p, size); break
            except Exception: pass
        d.text((x + w // 2, y + h // 2), text, font=f, fill=hexc(fg), anchor="mm")
        de.text((x + w // 2, y + h // 2), text, font=f, fill=glow, anchor="mm")
    return paint


SIGN_UV = lambda: [(0.0, 0.0), (1.0, 0.0), (1.0, 0.25), (0.0, 0.25)]   # bottom strip of the glass atlas
