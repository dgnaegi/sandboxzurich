"""Shared helpers for the Kreis 5 wave-3 landmarks (k5w3_*.py). Additive: nothing here changes lm.py/detail.py/common.py.
- registers into pipeline/overrides/landmarks_k5w3.json (set via setup())
- volumes(): flat-roof height levels of a game building (from the swissBUILDINGS3D roof polygons)
- bands(): stacked wall bands of those levels (walls only where exposed) + roof regions
- textures: brick, concrete (panel grid), corrugated metal, plaster; free fonts from web/public/fonts
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pickle, glob
import common
from common import *
from lm import *
import detail as D
from shapely.geometry import Polygon, MultiPolygon, box as sbox
from shapely.ops import unary_union

OVR5 = ROOT / "pipeline" / "overrides" / "landmarks_k5w3.json"
FONTS = str(ROOT / "web" / "public" / "fonts") + "/"
W4 = (255, 255, 255, 255)


def setup():
    common.OVR = OVR5


def font(name, size):
    return ImageFont.truetype(FONTS + name + ".ttf", size)


def rgb(h):
    return hexc(h)[:3]


def mixc(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def noisy(im, amp=6, seed=3):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    r = np.random.default_rng(seed).integers(-amp, amp + 1, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a + r, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


_pk = None


def raw_building(prefix):
    global _pk
    for f in sorted(glob.glob(str(ROOT / "data/build/bld/*.pkl"))):
        for b in pickle.load(open(f, "rb")):
            if b["id"].startswith(prefix):
                return b
    raise KeyError(prefix)


def volumes(prefix, tol=0.8, min_area=14.0, simp=0.6):
    """Flat-roof height levels of a building: list of (ztop, Polygon/MultiPolygon) sorted by z (absolute game z)."""
    b = raw_building(prefix)
    roofs = []
    for k, p in b["polys"]:
        if k == 2 and np.ptp(p[:, 2]) < 0.5:
            try:
                g = Polygon(p[:, :2]).buffer(0)
            except Exception:
                continue
            if g.area > 0.3: roofs.append((float(p[:, 2].mean()), g))
    roofs.sort(key=lambda t: t[0])
    out = []
    cl = []
    for z, g in roofs:
        for c in cl:
            if abs(c["z"] - z) < tol: c["g"].append(g); c["zs"].append(z); c["z"] = float(np.mean(c["zs"])); break
        else: cl.append({"z": z, "zs": [z], "g": [g]})
    for c in cl:
        u = unary_union(c["g"]).buffer(0.3, join_style=2).buffer(-0.3, join_style=2)
        u = u.simplify(simp)
        u = unary_union([Polygon(q.exterior, [i for i in q.interiors if Polygon(i).area > 60]) for q in polys_of(u)])
        if u.area >= min_area: out.append((max(c["zs"]), u))
    out.sort(key=lambda t: t[0])
    return out


def bands(vols, zbase):
    """vols: [(ztop, poly)] ascending. Returns [(z0, z1, S_poly, roof_poly)] : S_poly footprint of the band, roof_poly = part whose roof is at z1."""
    zs = [v[0] for v in vols]
    res = []; prev = zbase
    for j, z in enumerate(zs):
        S = unary_union([p for zz, p in vols if zz >= z - 1e-6])
        T = unary_union([p for zz, p in vols if zz > z + 1e-6]) if j + 1 < len(zs) else None
        R = S.difference(T.buffer(0.05)) if T is not None and not T.is_empty else S
        res.append((prev, z, S, R)); prev = z
    return res


def polys_of(g):
    if g.is_empty: return []
    return [g] if g.geom_type == "Polygon" else [p for p in g.geoms if p.geom_type == "Polygon"]


def rings_of(poly):
    poly = orient(poly, 1.0)
    return [list(poly.exterior.coords)[:-1]] + [list(i.coords)[:-1] for i in poly.interiors]


def edges_of(poly, minlen=0.6):
    for ring in rings_of(poly):
        n = len(ring)
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            if math.hypot(b[0] - a[0], b[1] - a[1]) >= minlen: yield a, b


def hide_pts(prefixes):
    out = []
    for p in prefixes:
        b = bid(p)
        gs = b["fp"].geoms if hasattr(b["fp"], "geoms") else [b["fp"]]
        out += [[round(q.x, 1), round(q.y, 1)] for q in (g.representative_point() for g in gs)]
    return out


def tex_brick(col="#9c4a36", mortar="#c9bfae", size=256, rows=16, seed=4, var=0.16):
    rng = np.random.default_rng(seed); C = rgb(col)
    im = Image.new("RGB", (size, size), rgb(mortar)); d = ImageDraw.Draw(im); rh = size / rows; bw = size / 6
    for r in range(rows):
        off = (bw / 2) if r % 2 else 0
        for c in range(-1, 7):
            t = 1 + (rng.random() - 0.5) * var * 2; cc = tuple(int(min(255, v * t)) for v in C)
            x0 = c * bw + off; d.rectangle([x0 + 1, r * rh + 1, x0 + bw - 2, (r + 1) * rh - 2], fill=cc)
    return noisy(im, 5, seed)


def tex_concrete(col="#a9a9a4", size=256, panel=(2, 1), seed=5, joint=0.15, ties=True):
    """Off-form concrete; panel joints at size/panel[0] x size/panel[1]."""
    C = rgb(col); im = Image.new("RGB", (size, size), C); d = ImageDraw.Draw(im); rng = np.random.default_rng(seed)
    for k in range(panel[0] + 1):
        x = int(k * size / panel[0]); d.line([x, 0, x, size], fill=mixc(C, (0, 0, 0), joint), width=2)
    for k in range(panel[1] + 1):
        y = int(k * size / panel[1]); d.line([0, y, size, y], fill=mixc(C, (0, 0, 0), joint), width=2)
    for _ in range(8):
        x, y = rng.integers(0, size, 2); d.rectangle([x, y, x + rng.integers(2, 8), y + rng.integers(16, 60)], fill=mixc(C, (0, 0, 0), 0.05))
    return noisy(im, 5, seed)


def tex_corrugated(col="#b9bcbd", size=256, n=32, seed=6, horizontal=False):
    C = rgb(col); im = Image.new("RGB", (size, size), C); d = ImageDraw.Draw(im); w = size / n
    for k in range(n):
        x = int(k * w)
        for j in range(int(w)):
            f = 0.12 * math.sin(math.pi * j / max(1, w))
            d.line([x + j, 0, x + j, size], fill=tuple(int(np.clip(v * (1 + 0.1 - f * 2.2), 0, 255)) for v in C))
    if horizontal: im = im.rotate(90)
    return noisy(im, 4, seed)


def tex_plain(col, seed=3, amp=5, size=64):
    return noisy(Image.new("RGB", (size, size), rgb(col)), amp, seed)


def text_painter(regions, size=26, fontname="Barlow-Bold", track=0.12):
    """Sign painter for glass_atlas_g(sign=...). regions: (x0, x1, text, fg, bg, glow|None). Uses a free font."""
    f = font(fontname, size)
    def paint(d, de, x, y, w, hh):
        for x0, x1, text, fg, bg, glow in regions:
            d.rectangle([x0, y, x1 - 1, y + hh], fill=hexc(bg))
            ws = [d.textlength(ch, font=f) for ch in text]; tot = sum(ws)
            gap = max(0, min(size * track, (0.9 * (x1 - x0) - tot) / max(1, len(text) - 1)))
            cx = x0 + ((x1 - x0) - (tot + gap * (len(text) - 1))) / 2
            for ch, wc in zip(text, ws):
                d.text((cx, y + hh / 2), ch, font=f, fill=hexc(fg), anchor="lm")
                if glow: de.text((cx, y + hh / 2), ch, font=f, fill=glow, anchor="lm")
                cx += wc + gap
    return paint


def sign_quad(m, mg, a, t, n, u0, u1, z0, z1, cx0, cx1, v0=0.0, v1=0.25, off=0.06, W=1024):
    """Quad of the atlas sign strip (u from cx0..cx1 px of the glass atlas, v 0..0.25) on a wall frame (a,t,n)."""
    p0 = D.P3(a, t, n, u0, z0, off); p1 = D.P3(a, t, n, u1, z0, off)
    m.quad(mg, [p0, p1, (p1[0], p1[1], z1), (p0[0], p0[1], z1)], [(cx0 / W, v0), (cx1 / W, v0), (cx1 / W, v1), (cx0 / W, v1)], n=(n[0], n[1], 0))


def punched(m, mw, mg, mf, a, b, z0, nfl, fh, bayw, ww, wh, sill, depth, wall_col, reveal_col, rng, wmod=(4.0, 4.0), arch=False, skip=None, wsill=None):
    """Storey-high rows of punched windows: width ww, height wh, sill height `sill` above floor."""
    def hole(u0, u1, f0, f1, f):
        if skip and skip(u0, u1, f): return None
        uc = (u0 + u1) / 2; w = min(ww, (u1 - u0) - 0.4)
        return D.rect_pts(uc - w / 2, f0 + sill, uc + w / 2, f0 + sill + wh)
    D.wall_run(m, mw, mg, mf, a, b, z0, nfl, fh, bayw, hole, depth, wall_col, reveal_col, rng, wmod, wsill)


def stair_run(m, mf, x0, y0, ang, length, width, z0, z1, col, steps=12):
    """Simple stepped stair rising along direction ang from (x0,y0) (steps as boxes)."""
    c, s = math.cos(ang), math.sin(ang); dl = length / steps
    for i in range(steps):
        cx = x0 + c * (i + 0.5) * dl; cy = y0 + s * (i + 0.5) * dl
        zt = z0 + (z1 - z0) * (i + 1) / steps
        m.box(mf, cx, cy, dl, width, zt - 0.15, zt, rot=ang, col=col)
    # stringers
    for sd in (-1, 1):
        px, py = x0 - s * sd * width / 2 + c * length / 2, y0 + c * sd * width / 2 + s * length / 2
        m.box(mf, px, py, length, 0.06, z0, z1 * 0.0 + (z0 + z1) / 2, rot=ang, col=col) if False else None


def gtex(key, m, im, em=None, rough=0.7):
    return m.mat(key, im, em, rough=rough)

hexl = D.hexl


def facade(m, mats, S, z0, z1, T=None, *, fh=3.5, bayw=3.0, hole=None, depth=0.3, wall_col=W4, reveal_col=None, rng=None, wmod=(4.0, 4.0),
           eg_h=None, eg_hole=None, base=None, cornice=None, minl=1.0, wsill=None, plain=None, floor_bands=None, deep_z=9.0):
    """Wall bands for the exposed edges of footprint S between z0..z1 (T = footprint of higher volumes: edges inside it are skipped).
    hole(u0,u1,f0,f1,fi,L) -> (u,z) opening polygon or None. eg_h/eg_hole: lower storey (only when z0 <= 0.5) ; base=(z_from) plinth wall below z0.
    cornice=(col, out, thick): projecting band at the top. plain(a,b)->True gives a blind wall. floor_bands=(col,out,thick): slab bands each floor."""
    mw, mg, mf = mats
    rng = rng or np.random.default_rng(1)
    reveal_col = reveal_col or hexl("#cfcac0")
    for a, b in edges_of(S, 0.15):
        L, t, n = D.frame_of(a, b)
        mid = ((a[0] + b[0]) / 2 + n[0] * 0.25, (a[1] + b[1]) / 2 + n[1] * 0.25)
        if base is not None and z0 > base + 0.01 and z0 <= 0.5:
            m.wall(mw, a, b, base, z0, wmod, wall_col)
        zs = z0
        if L < minl or (plain and plain(a, b)):
            m.wall(mw, a, b, zs, z1, wmod, wall_col); continue
        if eg_h and z0 <= 0.5:
            zt = zs + eg_h
            wall_run2(m, mw, mg, mf, a, b, zs, 1, eg_h, bayw, lambda u0, u1, f0, f1, f: eg_hole(u0, u1, f0, f1, 0, L), depth, wall_col, reveal_col, rng, wmod, wsill, deep_z)
            zs = zt
        nfl = max(1, int(round((z1 - zs) / fh))); h = (z1 - zs) / nfl
        if z1 - zs > 0.3:
            wall_run2(m, mw, mg, mf, a, b, zs, nfl, h, bayw, lambda u0, u1, f0, f1, f: hole(u0, u1, f0, f1, f, L), depth, wall_col, reveal_col, rng, wmod, wsill, deep_z)
        if floor_bands:
            for k in range(1, nfl):
                D.band(m, mf, a, b, zs + k * h - floor_bands[2] / 2, zs + k * h + floor_bands[2] / 2, floor_bands[1], floor_bands[0])
        if cornice: D.band(m, mf, a, b, z1 - cornice[2], z1, cornice[1], cornice[0])


def roofs(m, mf, R, z, col, parapet=0.0, pcol=None):
    for p in polys_of(R):
        m.flat(mf, p, z, col)


def hdz(x, y):
    """Ground height at game xy relative to model origin helper."""
    return ground(x, y)


def bay_lite(m, mw, mg, mf, org, t, n, u0, u1, z0, z1, hole, depth, k, wall_col, reveal_col, wmod=(4.0, 4.0), sill=None, nv=D.NV):
    """Like detail.bay but cheaper: reveal quads only for axis-aligned hole edges (arch segments get none); optional sill."""
    Hh = Polygon(hole)
    Wp = Polygon(D.rect_pts(u0, z0, u1, z1)).difference(Hh)
    D.poly_wall(m, mw, Wp, org, t, n, 0.0, wall_col, lambda u, z: (u / wmod[0], z / wmod[1]))
    h = list(hole)
    for i in range(len(h)):
        p, q = h[i], h[(i + 1) % len(h)]
        du, dz = q[0] - p[0], q[1] - p[1]; l = math.hypot(du, dz)
        if l < 0.12 or not (abs(du) < 1e-4 or abs(dz) < 1e-4): continue
        nl = (t[0] * (-dz / l), t[1] * (-dz / l), du / l)
        pts = [D.P3(org, t, n, p[0], p[1], 0), D.P3(org, t, n, q[0], q[1], 0), D.P3(org, t, n, q[0], q[1], -depth), D.P3(org, t, n, p[0], p[1], -depth)]
        D._oriented(m, mf, pts, nl, [(0, 0), (1, 0), (1, 1), (0, 1)], reveal_col)
    hz0 = min(p[1] for p in h); hz1 = max(p[1] for p in h); hu0 = min(p[0] for p in h); hu1 = max(p[0] for p in h)
    cu0, cu1 = k / nv, (k + 1) / nv
    guv = lambda u, z: (cu0 + (cu1 - cu0) * (u - hu0) / (hu1 - hu0), 0.25 + 0.75 * (z - hz0) / (hz1 - hz0))
    D.poly_wall(m, mg, Hh, org, t, n, -depth, (255, 255, 255, 255), guv)
    if sill:
        su0, su1 = hu0 - 0.08, hu1 + 0.08; o = sill
        D._oriented(m, mf, [D.P3(org, t, n, su0, hz0 - 0.12, o), D.P3(org, t, n, su1, hz0 - 0.12, o), D.P3(org, t, n, su1, hz0, o), D.P3(org, t, n, su0, hz0, o)],
                    (n[0], n[1], 0), [(0, 0), (1, 0), (1, 1), (0, 1)], reveal_col)
        D._oriented(m, mf, [D.P3(org, t, n, su0, hz0, o), D.P3(org, t, n, su1, hz0, o), D.P3(org, t, n, su1, hz0, 0), D.P3(org, t, n, su0, hz0, 0)],
                    (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)], reveal_col)


def bay_flat(m, mw, mg, mf, org, t, n, u0, u1, z0, z1, hole, k, wall_col, wmod, nv=D.NV, off=0.03):
    """Cheap bay: one wall quad + glass polygon painted on the wall plane (no recess). ~4-9 tris."""
    m.quad(mw, [D.P3(org, t, n, u0, z0), D.P3(org, t, n, u1, z0), D.P3(org, t, n, u1, z1), D.P3(org, t, n, u0, z1)],
           [(u0 / wmod[0], z0 / wmod[1]), (u1 / wmod[0], z0 / wmod[1]), (u1 / wmod[0], z1 / wmod[1]), (u0 / wmod[0], z1 / wmod[1])], wall_col, n=(n[0], n[1], 0))
    h = list(hole); hz0 = min(p[1] for p in h); hz1 = max(p[1] for p in h); hu0 = min(p[0] for p in h); hu1 = max(p[0] for p in h)
    cu0, cu1 = k / nv, (k + 1) / nv
    guv = lambda u, z: (cu0 + (cu1 - cu0) * (u - hu0) / (hu1 - hu0), 0.25 + 0.75 * (z - hz0) / (hz1 - hz0))
    D.poly_wall(m, mg, Polygon(hole), org, t, n, off, (255, 255, 255, 255), guv)


def wall_run2(m, mw, mg, mf, a, b, z0, nfloor, fh, bayw, hole_fn, depth, wall_col, reveal_col, rng, wmod=(4.0, 4.0), sill=None, deep_z=1e9):
    L, t, n = D.frame_of(a, b)
    nb = max(1, int(round(L / bayw))); bw = L / nb
    for f in range(nfloor):
        for i in range(nb):
            u0, u1 = i * bw, (i + 1) * bw
            hole = hole_fn(u0, u1, z0 + f * fh, z0 + (f + 1) * fh, f)
            if hole is None:
                D.poly_wall(m, mw, Polygon(D.rect_pts(u0, z0 + f * fh, u1, z0 + (f + 1) * fh)), a, t, n, 0.0, wall_col, lambda u, z: (u / wmod[0], z / wmod[1]))
            elif z0 + f * fh > deep_z:
                bay_flat(m, mw, mg, mf, a, t, n, u0, u1, z0 + f * fh, z0 + (f + 1) * fh, hole, int(rng.integers(0, D.NV)), wall_col, wmod)
            else:
                bay_lite(m, mw, mg, mf, a, t, n, u0, u1, z0 + f * fh, z0 + (f + 1) * fh, hole, depth, int(rng.integers(0, D.NV)), wall_col, reveal_col, wmod, sill)
