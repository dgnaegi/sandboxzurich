"""Shared helpers for wave-4 landmarks (k4w4_*.py). Additive: re-uses k5w3_kit (volumes/bands/facade) and detail.py; nothing there is changed.
- registers into pipeline/overrides/landmarks_k4w4.json (setup4())
- Model4: like lm.Model but up to 6 materials (wall, glass, flat + special textures)
- textures: graffiti/poster atlas, rust, sign boards (free fonts only), sloped polygon fill, sawtooth roofs
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import common
from k5w3_kit import *   # noqa: F401,F403  (Model, D, volumes, bands, facade, roofs, tex_*, text_painter, polys_of, finish helpers ...)
import lm as _lm
from shapely.geometry import LineString
import shapely

from k4w3_kit import slope_roof   # noqa: E402  (its import redirects OVR; setup4() resets)
OVR4 = ROOT / "pipeline" / "overrides" / "landmarks_k4w4.json"


def setup4():
    common.OVR = OVR4


class Model4(_lm.Model):
    def mat(self, key, tex=None, emis=None, rough=0.9):
        if key not in self.mats:
            assert len(self.mats) < 8, "max 7 materials"
            self.mats[key] = _lm.Mat(key, tex, emis, rough)
        return self.mats[key]


def sinfo(m, name):
    print(name, m.tri_count(), "tris;", ", ".join(f"{k}={v.tris()}" for k, v in m.mats.items()))


def local(poly, ox, oy):
    return localize(poly, ox, oy)


def frame_xy(cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (lambda u, v: (cx + u * c - v * s, cy + u * s + v * c))


# ---- textures ---------------------------------------------------------------
_FONT_CACHE = {}


def fnt(name, size):
    k = (name, size)
    if k not in _FONT_CACHE: _FONT_CACHE[k] = ImageFont.truetype(FONTS + name + ".ttf", size)
    return _FONT_CACHE[k]


def tex_graffiti(seed=11, size=1024, cells=4):
    """Atlas of cells x cells: cells 0..5 pink wall with posters, 6..11 multi-colour pieces/tags, 12..15 black&white poster walls.
    Pieces are random bubble letters/blobs (no real artworks)."""
    rng = np.random.default_rng(seed)
    cs = size // cells
    im = Image.new("RGB", (size, size), (200, 200, 200)); d = ImageDraw.Draw(im)
    pal = [(236, 120, 40), (245, 197, 24), (216, 74, 138), (44, 150, 190), (60, 170, 90), (230, 60, 50), (120, 80, 170), (250, 250, 240), (20, 20, 24)]
    words = ["ZW", "OMO", "BWR", "KRS", "FREE", "ZRH", "OKO", "ASK", "ROT", "ZUR", "WAESCH", "ART", "NIX", "ULI", "PIT", "LOVE"]
    for k in range(cells * cells):
        x0, y0 = (k % cells) * cs, (k // cells) * cs
        if k < 6:   # pink wall + posters
            d.rectangle([x0, y0, x0 + cs, y0 + cs], fill=(232, 162, 176))
            for _ in range(int(rng.integers(8, 14))):
                w, h = int(rng.integers(30, 80)), int(rng.integers(40, 110)); px, py = int(rng.integers(0, cs - w)), int(rng.integers(0, cs - h))
                c = pal[int(rng.integers(0, len(pal)))] if rng.random() < 0.55 else (235, 232, 224)
                d.rectangle([x0 + px, y0 + py, x0 + px + w, y0 + py + h], fill=c)
                for j in range(int(rng.integers(1, 4))):
                    d.rectangle([x0 + px + 4, y0 + py + 6 + j * h // 4, x0 + px + w - 4 - int(rng.integers(0, w // 2)), y0 + py + 10 + j * h // 4], fill=(30, 30, 34))
            for _ in range(3):
                d.text((x0 + int(rng.integers(0, cs - 60)), y0 + int(rng.integers(0, cs - 30))), words[int(rng.integers(0, len(words)))], font=fnt("PermanentMarker-Regular", int(rng.integers(26, 44))), fill=pal[int(rng.integers(0, 7))])
        elif k < 12:   # multi-colour pieces
            bg = [(235, 235, 228), (70, 150, 200), (30, 30, 36), (245, 197, 24), (200, 200, 196), (60, 170, 90)][k - 6]
            d.rectangle([x0, y0, x0 + cs, y0 + cs], fill=bg)
            for _ in range(5):
                cx, cy = x0 + int(rng.integers(10, cs - 10)), y0 + int(rng.integers(10, cs - 10)); r = int(rng.integers(8, 26))
                d.ellipse([cx - r, cy - int(r * 0.7), cx + r, cy + int(r * 0.7)], fill=pal[int(rng.integers(0, len(pal)))])
            for _ in range(3):
                t = words[int(rng.integers(0, len(words)))]; f = fnt("PermanentMarker-Regular", int(rng.integers(56, 96)))
                x, y = x0 + int(rng.integers(0, cs // 3)), y0 + int(rng.integers(0, cs - 70)); fg = pal[int(rng.integers(0, 8))]; ol = (20, 20, 24)
                for ddx, ddy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-3, -3), (3, 3)): d.text((x + ddx, y + ddy), t, font=f, fill=ol)
                d.text((x, y), t, font=f, fill=fg)
        else:   # black & white poster walls
            d.rectangle([x0, y0, x0 + cs, y0 + cs], fill=(214, 212, 206))
            for yy in range(0, cs, 64):
                for xx in range(0, cs, 64):
                    c = (30, 30, 34) if rng.random() < 0.45 else (240, 238, 232)
                    d.rectangle([x0 + xx + 2, y0 + yy + 2, x0 + xx + 62, y0 + yy + 62], fill=c)
                    if rng.random() < 0.5: d.rectangle([x0 + xx + 8, y0 + yy + 10, x0 + xx + 54, y0 + yy + 20], fill=(240, 238, 232) if c[0] < 100 else (30, 30, 34))
    return noisy(im, 5, seed)


def gcell(k, cells=4, pad=0.004):
    """uv rect (u0, v0, u1, v1) of cell k in the graffiti atlas (v up in model uv: atlas row 0 = top => v from 1)."""
    cx, cy = k % cells, k // cells; s = 1.0 / cells
    return (cx * s + pad, 1 - (cy + 1) * s + pad, (cx + 1) * s - pad, 1 - cy * s - pad)


def tex_rust(size=128, seed=3, col="#7a4a36"):
    rng = np.random.default_rng(seed); C = np.array(rgb(col), float)
    a = np.zeros((size, size, 3)); a[:] = C
    a *= (1 + rng.normal(0, 0.10, (size, size, 1)))
    for x in range(0, size, 16): a[:, x:x + 2] *= 0.8   # panel seams
    for y in range(0, size, 32): a[y:y + 2, :] *= 0.8
    for _ in range(40):
        x, y = rng.integers(0, size, 2); r = rng.integers(3, 12); a[max(0, y - r):y + r, max(0, x - 2):x + 2] *= rng.choice([0.7, 1.2])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def sign_board(lines, size=(512, 256), bg="#efede6", fg="#161616", fonts=None):
    """Sign texture: lines = [(text, font, px, fg, bg, height_frac)] stacked, each filling the width (letter-spaced if needed)."""
    im = Image.new("RGB", size, rgb(bg)); d = ImageDraw.Draw(im)
    y = 0
    for text, font_, px, fg_, bg_, hf in lines:
        h = int(size[1] * hf); d.rectangle([0, y, size[0], y + h], fill=rgb(bg_))
        f = fnt(font_, px); tw = d.textlength(text, font=f)
        d.text(((size[0] - tw) / 2, y + h / 2), text, font=f, fill=rgb(fg_), anchor="lm") if False else d.text((size[0] / 2, y + h / 2), text, font=f, fill=rgb(fg_), anchor="mm")
        y += h
    return im


def textquad(m, mat, org, tang, up, w, h, uv=(0, 0, 1, 1), col=(255, 255, 255, 255), nrm=None):
    """Quad centred on org spanned by tangent (unit, xy) and z-up, w x h metres, facing normal=(tang rotated -90deg)."""
    t = tang; n = (t[1], -t[0])
    p0 = (org[0] - t[0] * w / 2, org[1] - t[1] * w / 2, org[2]); p1 = (org[0] + t[0] * w / 2, org[1] + t[1] * w / 2, org[2])
    u0, v0, u1, v1 = uv
    m.quad(mat, [p0, p1, (p1[0], p1[1], org[2] + h), (p0[0], p0[1], org[2] + h)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], col, n=(n[0], n[1], 0))


# ---- geometry helpers ---------------------------------------------------------
def slope_fill(m, mat, poly, plane, col, uvscale=0.12):
    """Triangulate a horizontal-projection polygon with z = plane(x, y); triangles oriented upwards."""
    for g in shapely.constrained_delaunay_triangles(orient(poly, 1.0)).geoms:
        c = list(g.exterior.coords)[:3]
        if not poly.buffer(1e-6).contains(g.representative_point()): continue
        pts = [(x, y, plane(x, y)) for x, y in c]
        n = np.cross(np.array(pts[1]) - np.array(pts[0]), np.array(pts[2]) - np.array(pts[0]))
        if n[2] < 0: pts = pts[::-1]
        m.tri(mat, pts, [(p[0] * uvscale, p[1] * uvscale) for p in pts], col)


def sawtooth(m, mr, mg, mf, region, z0, rise, pitch, ang, roof_col, glass_cols=8, glass_uv=(0, 0.25, 1 / 8, 1.0), frame_col=None, glaze_h=None):
    """North-light sawtooth over `region`: strips of width `pitch` across axis v (perpendicular to ang), each sloping up by `rise` toward +v,
    with a vertical glazed riser (glass material) at the high edge facing +v. Returns number of strips."""
    c, s = math.cos(ang), math.sin(ang)
    to_uv = lambda x, y: (x * c + y * s, -x * s + y * c)
    pts = [to_uv(x, y) for g in polys_of(region) for x, y in g.exterior.coords]
    umin, umax = min(p[0] for p in pts) - 2, max(p[0] for p in pts) + 2; vmin, vmax = min(p[1] for p in pts), max(p[1] for p in pts)
    n = max(1, int(math.ceil((vmax - vmin) / pitch))); pv = (vmax - vmin) / n
    nrm = (-s, c)   # +v direction in xy
    ns = 0
    for k in range(n):
        va, vb = vmin + k * pv, vmin + (k + 1) * pv
        strip = Polygon([(umin * c - va * s, umin * s + va * c), (umax * c - va * s, umax * s + va * c), (umax * c - vb * s, umax * s + vb * c), (umin * c - vb * s, umin * s + vb * c)])
        Q = region.intersection(strip)
        for q in polys_of(Q):
            if q.area < 1.0: continue
            slope_fill(m, mr, q, lambda x, y, va=va: z0 + rise * (to_uv(x, y)[1] - va) / pv, roof_col)
        # glazed riser along v = vb (facing +v) over the part of that line inside the region
        ln = LineString([(umin * c - vb * s, umin * s + vb * c), (umax * c - vb * s, umax * s + vb * c)]).intersection(region.buffer(0.05))
        for seg in ([ln] if ln.geom_type == "LineString" else [g for g in getattr(ln, "geoms", []) if g.geom_type == "LineString"]):
            if seg.is_empty or len(seg.coords) < 2: continue
            (xa, ya), (xb, yb) = seg.coords[0], seg.coords[-1]
            if math.hypot(xb - xa, yb - ya) < 1.5: continue
            if to_uv(xa, ya)[0] > to_uv(xb, yb)[0]: xa, ya, xb, yb = xb, yb, xa, ya
            L = math.hypot(xb - xa, yb - ya); npn = max(1, int(round(L / 2.4)))
            for i in range(npn):
                f0, f1 = i / npn, (i + 1) / npn
                P0 = (xa + (xb - xa) * f0, ya + (yb - ya) * f0); P1 = (xa + (xb - xa) * f1, ya + (yb - ya) * f1)
                kk = (i + k * 3) % glass_cols
                u0, u1 = kk / glass_cols, (kk + 1) / glass_cols
                # facing +v: tangent = +u direction => right-hand normal of a->b with a->b = +u is (s... ) check: t=(c,s) -> n=(s,-c) = -v. so go reversed
                m.quad(mg, [(P1[0], P1[1], z0), (P0[0], P0[1], z0), (P0[0], P0[1], z0 + rise), (P1[0], P1[1], z0 + rise)], [(u1, 0.25), (u0, 0.25), (u0, 1.0), (u1, 1.0)], n=(nrm[0], nrm[1], 0))
        ns += 1
    return ns


def water_tower(m, mrust, mflat, cx, cy, z0, tank_r=3.4, tank_h=5.2, leg_h=10.0, col=(255, 255, 255, 255)):
    """Rusty cylindrical water tank with conical bottom on a steel lattice stilt (like the Zentralwaescherei yard tower)."""
    zc = z0 + leg_h
    m.cylinder(mrust, cx, cy, tank_r, zc, zc + tank_h, n=16, mod=(4.0, 2.0), col=col, cap=mrust, capcol=(110, 70, 52, 255))
    m.cylinder(mrust, cx, cy, 0.6, zc - 3.2, zc, n=16, mod=(4.0, 2.0), col=col, r1=tank_r)
    # roof cone
    for i in range(16):
        a0, a1 = 2 * math.pi * i / 16, 2 * math.pi * (i + 1) / 16
        m.tri(mrust, [(cx + tank_r * 1.05 * math.cos(a0), cy + tank_r * 1.05 * math.sin(a0), zc + tank_h), (cx + tank_r * 1.05 * math.cos(a1), cy + tank_r * 1.05 * math.sin(a1), zc + tank_h), (cx, cy, zc + tank_h + 1.2)], [(0, 0), (1, 0), (0.5, 1)], col)
    steel = (64, 66, 68, 255)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2; r = 3.0
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        m.box(mflat, px, py, 0.22, 0.22, z0 - 0.3, zc - 0.5, col=steel)
    for zz in (z0 + leg_h * 0.35, z0 + leg_h * 0.7):   # ring bracing
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2; b = a + math.pi / 2; r = 3.0
            xa, ya, xb, yb = cx + r * math.cos(a), cy + r * math.sin(a), cx + r * math.cos(b), cy + r * math.sin(b)
            m.box(mflat, (xa + xb) / 2, (ya + yb) / 2, math.hypot(xb - xa, yb - ya), 0.14, zz - 0.07, zz + 0.07, rot=math.atan2(yb - ya, xb - xa), col=steel)
    # ladder + balcony ring
    m.box(mflat, cx + tank_r + 0.1, cy, 0.1, 0.5, z0, zc + tank_h * 0.8, col=steel)


# ---- shared building blocks (wave 4) -------------------------------------------
def clock_paint(x0, face="#f4f0e2", ring="#c9a23a", dial="#27415f", hands="#e0b83c"):
    """Sign painter drawing a 30 px clock face (dark-blue dial, gold ring/hands) at x0 in the glass-atlas strip. Combine with both()."""
    def paint(d, de, x, y, w, hh):
        cx, cy = x0 + 16, y + 16
        d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=hexc(ring)); d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=hexc(dial))
        for k in range(12):
            a = k * math.pi / 6; d.line([cx + 10 * math.sin(a), cy - 10 * math.cos(a), cx + 12 * math.sin(a), cy - 12 * math.cos(a)], fill=hexc(hands), width=1)
        d.line([cx, cy, cx - 5, cy - 7], fill=hexc(hands), width=2); d.line([cx, cy, cx + 8, cy - 8], fill=hexc(hands), width=1)
        de.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(50, 56, 70))
    return paint


def both(*painters):
    def paint(d, de, x, y, w, hh):
        for p in painters: p(d, de, x, y, w, hh)
    return paint


def strip_quad(m, mg, c, t, w, h, z, x0, x1, off=0.0, W=1024):
    """Quad on the glass-atlas sign strip (px x0..x1 of 1024) centred at c=(x,y), tangent t=(tx,ty), size w x h, bottom at z. Faces right-hand normal (t[1], -t[0])."""
    n = (t[1], -t[0])
    p0 = (c[0] - t[0] * w / 2 + n[0] * off, c[1] - t[1] * w / 2 + n[1] * off, z); p1 = (c[0] + t[0] * w / 2 + n[0] * off, c[1] + t[1] * w / 2 + n[1] * off, z)
    m.quad(mg, [p0, p1, (p1[0], p1[1], z + h), (p0[0], p0[1], z + h)], [(x0 / W, 0.0), (x1 / W, 0.0), (x1 / W, 0.25), (x0 / W, 0.25)], n=(n[0], n[1], 0))


def rot_box(m, mat, cx, cy, w, d, z0, z1, ang, col, mod=(4.0, 4.0), mr=None, rcol=None):
    m.box(mat, cx, cy, w, d, z0, z1, rot=ang, col=col, mod=mod, mr=mr, rcol=rcol)


def cone8(m, mat, cx, cy, r0, r1, z0, z1, col, n=8, mod=(4.0, 4.0), rot=0.0):
    """Faceted cone/tapered spire (n sides), flat caps omitted."""
    for i in range(n):
        a0, a1 = rot + 2 * math.pi * i / n, rot + 2 * math.pi * (i + 1) / n
        P = [(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0), z0), (cx + r0 * math.cos(a1), cy + r0 * math.sin(a1), z0),
             (cx + r1 * math.cos(a1), cy + r1 * math.sin(a1), z1), (cx + r1 * math.cos(a0), cy + r1 * math.sin(a0), z1)]
        if r1 < 0.02: m.tri(mat, P[:3], [(0, 0), (1, 0), (0.5, 1)], col)
        else: m.quad(mat, P, [(0, 0), (1, 0), (1, 1), (0, 1)], col)


def pyramid_roof(m, mat, cx, cy, w, d, z0, rise, rot, col, eave=0.0):
    """Four-sided pyramid/hip over a rectangle w x d (rotated)."""
    c, s = math.cos(rot), math.sin(rot)
    P = lambda u, v, z: (cx + u * c - v * s, cy + u * s + v * c, z)
    hw, hd = w / 2 + eave, d / 2 + eave
    base = [P(-hw, -hd, z0), P(hw, -hd, z0), P(hw, hd, z0), P(-hw, hd, z0)]
    top = P(0, 0, z0 + rise)
    for i in range(4): m.tri(mat, [base[i], base[(i + 1) % 4], top], [(0, 0), (1, 0), (0.5, 1)], col)


def dome8(m, mat, cx, cy, r, z0, h, col, n=8, rings=((1.0, 0.0), (1.0, 0.18), (0.88, 0.45), (0.62, 0.75), (0.28, 0.95), (0.0, 1.0)), rot=0.0):
    """Faceted dome as stacked cone rings; rings = (radius factor, height factor)."""
    for (ra, ha), (rb, hb) in zip(rings[:-1], rings[1:]):
        cone8(m, mat, cx, cy, r * ra, r * rb, z0 + h * ha, z0 + h * hb, col, n=n, rot=rot)


# ---- generic block builder ------------------------------------------------------
def pick_edge(S, pref, minlen=6.0):
    """Edge (a, b, L, t, n) of polygon S whose outward normal is closest to pref=(dx,dy), weighted by length."""
    best = None
    for gp in polys_of(S):
        for a, b in edges_of(orient(gp, 1.0), minlen):
            L, t, n = D.frame_of(a, b); sc = (n[0] * pref[0] + n[1] * pref[1]) * min(L, 30) if pref else L
            if best is None or sc > best[0]: best = (sc, a, b, L, t, n)
    return best[1:] if best else None


def block_model(name, title, prefixes, *, wall="#d8cfae", wall_tex=None, frame="#f0ece0", glass="#2e3b46", sky="#8aa0ae", cols=2, rows=3,
                fh=3.2, bayw=2.6, win=(1.2, 1.6, 0.9), arch=False, depth=0.28, eg_h=4.4, eg_kind="shop", eg_col="#3a3d3f", base_col="#9a948a",
                cornice=("#cfc6b0", 0.3, 0.45), floor_bands=None, roof=("flat", "#8a8780"), eave_rise=0.0, parapet=0.4, seed=1, lit=0.4,
                signs=None, extra=None, min_area=14.0, simp=0.6, tol=0.5, deep_z=7.0, wmod=(4.0, 4.0), wall_stains=0.012, curtains=None,
                level_cols=None, surround=None, roof_d=5.0, ground_ref=None, awning=None, rooftop=None):
    """Generic multi-level block from swissBUILDINGS3D roof levels. signs = [dict(text, fg, bg, pref=(dx,dy), z=, h=, w=, font, size, u=)]. extra(m, ctx) hook."""
    from k45_volkshaus import plaster
    setup4()
    Bs = [bid(p) for p in prefixes]; U = unary_union([outline(b["fp"], tol) for b in Bs]); c = U.centroid
    ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(*(ground_ref or (ox, oy))) if False else ground(ox, oy)
    rng = np.random.default_rng(seed); m = Model4(name)
    mw = m.mat("wall", wall_tex if wall_tex is not None else plaster(hexc(wall), seed=seed + 3, stains=wall_stains), rough=0.95)
    sg = None
    if signs:
        regs = []; x = 0
        for s in signs:
            w = s.get("px", 1024 // len(signs)); regs.append((x, x + w, s["text"], s["fg"], s["bg"], s.get("glow"))); s["x0"], s["x1"] = x, x + w; x += w
        sg = text_painter(regs, size=signs[0].get("size", 24), fontname=signs[0].get("font", "Barlow-Bold"))
    ga = D.glass_atlas_g(frame=frame, glass=glass, sky=sky, cols=cols, rows=rows, seed=seed + 7, lit_p=lit, cw=128, ch=96, bar=3, sign=sg,
                         curtain_cols=curtains or [(226, 222, 212), (190, 190, 190), (150, 160, 168)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W4))
    WALL = hexl(wall); FR = hexl(frame)
    allS = []
    for bi, B in enumerate(Bs):
        P = orient(localize(outline(B["fp"], tol), ox, oy), 1.0)
        vols = [(z - oz, localize(g, ox, oy)) for z, g in volumes(prefixes[bi], min_area=min_area, simp=simp)]
        H = B["zmax"] - oz
        if roof[0] in ("hip", "gable") or not vols:
            top = max(2.5, H - (eave_rise if eave_rise else (roof_d * 0.55 if roof[0] != "flat" else 0.0)))
            vols = [(top, P)]
        print(name, prefixes[bi][3:11], 'levels', [round(v[0], 1) for v in vols], 'zmax-oz', round(H, 1), 'oz', round(oz, 1))
        for a, b in edges_of(P, 0.3): m.wall(mw, a, b, -3.0, 0.0, wmod, hexl(base_col))
        first = True
        for z0, z1, S, R in bands(vols, 0.0):
            col = hexl(level_cols[min(len(level_cols) - 1, bands_i)]) if False else WALL
            for S1 in polys_of(S):
                if S1.area < 3: continue
                nf = max(1, int(round((z1 - z0 - (eg_h if z0 < 0.5 and eg_h else 0)) / fh)))
                def hole(u0, u1, f0, f1, fi, L):
                    uc = (u0 + u1) / 2; w = min(win[0], u1 - u0 - 0.5)
                    if arch: return D.arch_pts(uc - w / 2, f0 + win[2], uc + w / 2, f0 + win[2] + win[1] - w / 2)
                    return D.rect_pts(uc - w / 2, f0 + win[2], uc + w / 2, f0 + win[2] + win[1])
                def egh(u0, u1, f0, f1, fi, L):
                    uc = (u0 + u1) / 2
                    if eg_kind == "shop":
                        w = u1 - u0 - 0.4; return D.rect_pts(u0 + 0.2, f0 + 0.25, u0 + 0.2 + w, f0 + eg_h - 0.7) if (int(u0 // bayw) % 4 != 3) else D.rect_pts(uc - 0.55, f0, uc + 0.55, f0 + 2.5)
                    if eg_kind == "arch": w = min(1.8, u1 - u0 - 0.6); return D.arch_pts(uc - w / 2, f0 + 0.5, uc + w / 2, f0 + eg_h - 1.6)
                    w = min(win[0], u1 - u0 - 0.5); return D.rect_pts(uc - w / 2, f0 + 0.9, uc + w / 2, f0 + 0.9 + win[1])
                facade(m, (mw, mg, mf), S1, z0, z1, None, fh=(z1 - z0 - (eg_h if z0 < 0.5 and eg_h else 0)) / nf, bayw=bayw, hole=hole, depth=depth, wall_col=W4, reveal_col=hexl(frame) if surround is None else hexl(surround),
                       rng=rng, wmod=wmod, eg_h=eg_h if z0 < 0.5 else None, eg_hole=egh if z0 < 0.5 else None, base=0.0,
                       cornice=(hexl(cornice[0]), cornice[1], cornice[2]) if cornice else None, wsill=0.07, floor_bands=(hexl(floor_bands[0]), floor_bands[1], floor_bands[2]) if floor_bands else None, deep_z=deep_z)
            if roof[0] == "flat" or z1 < vols[-1][0] - 0.01:
                for p in polys_of(R):
                    m.flat(mf, p, z1 + parapet, hexl(roof[1]))
                    if parapet > 0:
                        for a, b in edges_of(p, 0.4): m.wall(mf, a, b, z1, z1 + parapet, (4, 4), hexl(cornice[0]) if cornice else WALL)
            else:
                for p in polys_of(S):
                    if roof[0] == "hip" or p.area < 0.88 * p.minimum_rotated_rectangle.area:   # L/T/skew footprint: gable would grow wings, so hip
                        hip_roof(m, mf, orient(p.buffer(0.3, join_style=2).simplify(0.4), 1.0), z1 + 0.1, (roof[2] if roof[0] == "hip" and len(roof) > 2 else min(5.0, roof_d * 0.55)), roof_d, hexl(roof[1]))
                    else:
                        (cx_, cy_), ux, uy, L_, W_ = rect_of(p)
                        gable_roof(m, mf, mw, ((cx_, cy_), ux, uy, L_, W_), z1 + 0.1, roof[2] if len(roof) > 2 else W_ * 0.3, hexl(roof[1]), WALL, eave=0.4)
            allS.append((z1, S))
    if awning and allS:
        zS0, S0 = allS[0]
        for gp in polys_of(S0):
            for a, b in edges_of(orient(gp, 1.0), 3.0):
                D.band(m, mf, a, b, awning[1], awning[1] + 0.45, awning[2], hexl(awning[0]))
    if rooftop and allS:   # (col, w, d, h) plant box on the top roof
        zt, St = allS[-1]
        for gp in polys_of(St)[:1]:
            q = gp.representative_point(); m.box(mf, q.x, q.y, rooftop[1], rooftop[2], zt + parapet, zt + parapet + rooftop[3], col=hexl(rooftop[0]))
    ctx = dict(m=m, mw=mw, mg=mg, mf=mf, ox=ox, oy=oy, oz=oz, vols=vols, rng=rng, P=U, localize=lambda g: localize(g, ox, oy))
    if signs:
        S = allS[0][1]
        for s in signs:
            e = pick_edge(S, s.get("pref", (0, -1)), 5.0)
            if e:
                a, b, L, t, n = e; w = min(s.get("w", 8.0), L - 1.0)
                strip_quad(m, mg, ((a[0] + b[0]) / 2 + t[0] * s.get("du", 0.0), (a[1] + b[1]) / 2 + t[1] * s.get("du", 0.0)), t, w, s.get("h", 0.8), s.get("z", eg_h + 0.2), s["x0"], s["x1"], off=0.16)
    if extra: extra(m, ctx)
    sinfo(m, name)
    finish(m, name, title, ox, oy, oz, hide_pts(prefixes))
    return m


def hip_roof_v1(m, mr, P, z0, rise, d, col, cap=True):
    """(old, kept for regression comparison) Hip roof over a ring: vertex-paired frustum between P (z0) and its mitre-inset by d (z0+rise) when the vertex counts match
    (no 'fins' at concave corners); falls back to slope_roof otherwise."""
    P = orient(P, 1.0)
    for dd in (d, d * 0.8, d * 0.6, d * 0.4):
        Q = P.buffer(-dd, join_style=2, mitre_limit=8.0)
        if Q.geom_type == "Polygon" and not Q.is_empty and len(Q.exterior.coords) == len(P.exterior.coords):
            Q = orient(Q, 1.0); A = list(P.exterior.coords)[:-1]; B = list(Q.exterior.coords)[:-1]
            # align starting vertex of Q to P (nearest)
            k = min(range(len(B)), key=lambda i: (B[i][0] - A[0][0]) ** 2 + (B[i][1] - A[0][1]) ** 2); B = B[k:] + B[:k]
            ok = all(math.hypot(B[i][0] - A[i][0], B[i][1] - A[i][1]) < dd * 3.0 for i in range(len(A)))
            if ok:
                rz = rise * (dd / d)
                for i in range(len(A)):
                    j = (i + 1) % len(A)
                    p = [(A[i][0], A[i][1], z0), (A[j][0], A[j][1], z0), (B[j][0], B[j][1], z0 + rz), (B[i][0], B[i][1], z0 + rz)]
                    if math.hypot(B[j][0] - B[i][0], B[j][1] - B[i][1]) < 0.05: m.tri(mr, p[:3], col=col)
                    elif math.hypot(A[j][0] - A[i][0], A[j][1] - A[i][1]) > 0.02: m.quad(mr, p, col=col)
                if cap: m.flat(mr, Q, z0 + rz, col)
                return
    slope_roof(m, mr, P, z0, rise, d, col)


def hip_roof(m, mr, P, z0, rise, d, col, cap=True):
    """Hip roof over any ring (L, T, skew corners): eaves at P (z0), planar facets from the mitred inward offsets of P.
    Height = rise/d * distance to the eave, capped at rise; when the footprint is narrower than 2d the ridge stays lower (pitch kept).
    Each band between consecutive offsets is triangulated (constrained Delaunay) and vertex heights come from the distance field,
    so reflex corners give clean valleys and no spikes (straight-skeleton approximation)."""
    from shapely.geometry import Polygon, Point
    from shapely.geometry.polygon import orient as _or
    P = Polygon(_or(P, 1.0).exterior)
    if P.is_empty: return
    slope = rise / d
    def ring(dd):
        Q = P.buffer(-dd, join_style=2, mitre_limit=10.0)
        return Q if (not Q.is_empty and Q.area > 0.05) else None
    if ring(d) is not None: rmax = d
    else:
        lo, hi = 0.0, d
        for _ in range(12):
            mid = (lo + hi) / 2
            if ring(mid) is not None: lo = mid
            else: hi = mid
        rmax = lo * 0.97
    if rmax < 0.05: m.flat(mr, P, z0, col); return
    nsteps = 1 if len(P.simplify(0.05).exterior.coords) <= 5 else 3
    rings = [P] + [ring(rmax * k / nsteps) for k in range(1, nsteps + 1)]
    bnd = P.exterior
    def emit(poly):
        for g in shapely.constrained_delaunay_triangles(_or(poly, 1.0)).geoms:
            c = list(g.exterior.coords)[:3]; pts = [(x, y, z0 + min(rise, slope * bnd.distance(Point(x, y)))) for x, y in c]
            if not Polygon(c).exterior.is_ccw: pts = pts[::-1]
            m.tri(mr, pts, [(p[0] * 0.1, p[1] * 0.1) for p in pts], col)
    for A, B in zip(rings[:-1], rings[1:]):
        if A is None: continue
        for g in polys_of(A.difference(B) if B is not None else A):
            if g.area > 1e-3: emit(g)
    if rings[-1] is not None:
        for g in polys_of(rings[-1]):
            if g.area > 1e-3: emit(g)
