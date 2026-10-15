"""Shared helpers for the wave-3 / Kreis 4 landmarks (k4w3_*.py). Style = k45 (lm.py + detail.py). Additive only.
Registers into pipeline/overrides/landmarks_k4w3.json (common.OVR is redirected on import)."""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import common
from common import *
from lm import *
import detail as D
import k93_kit as K
from shapely.geometry import Polygon, Point
from shapely.geometry.polygon import orient

common.OVR = ROOT / "pipeline" / "overrides" / "landmarks_k4w3.json"
FONTS = str(ROOT / "web" / "public" / "fonts") + "/"
W = (255, 255, 255, 255)
hx = D.hexl


def strip(regions, size=24, fnt="Barlow-Bold", W_=1024):
    """Sign painter for glass_atlas_g(sign=...): regions = [(x0, x1, text, fg, bg, glow|None)] written into the bottom 32 px strip with a free font."""
    def paint(d, de, x, y, w, hh):
        f = ImageFont.truetype(FONTS + fnt + ".ttf", size)
        for x0, x1, text, fg, bg, glow in regions:
            d.rectangle([x0, y, x1 - 1, y + hh], fill=hexc(bg))
            ws = [d.textlength(c, font=f) for c in text]; tot = sum(ws)
            gap = max(0, (0.88 * (x1 - x0) - tot) / max(1, len(text) - 1)); gap = min(gap, size * 0.35)
            cx = x0 + ((x1 - x0) - (tot + gap * (len(text) - 1))) / 2
            for c, wc in zip(text, ws):
                d.text((cx, y + hh / 2), c, font=f, fill=hexc(fg), anchor="lm")
                if glow: de.text((cx, y + hh / 2), c, font=f, fill=glow, anchor="lm")
                cx += wc + gap
    return paint


def txtq(m, mg, a, t, n, u0, u1, z0, h, x0, x1, off=0.07):
    """Lettering quad onto the glass-atlas sign strip region x0..x1 (px of 1024) on the wall frame (a, t, n)."""
    p0 = D.P3(a, t, n, u0, z0, off); p1 = D.P3(a, t, n, u1, z0, off)
    m.quad(mg, [p0, p1, (p1[0], p1[1], z0 + h), (p0[0], p0[1], z0 + h)],
           [(x0 / 1024, 0.0), (x1 / 1024, 0.0), (x1 / 1024, 0.25), (x0 / 1024, 0.25)], n=(n[0], n[1], 0))


_CACHE = ROOT / "data" / "build" / "landmarks" / "k4w3_bcache.json"


def _cget():
    import json
    try: return json.load(open(_CACHE))
    except Exception: return {}


def setup(parts, name_ids=None):
    """parts: list of swissBUILDINGS3D id prefixes. Returns (buildings, ox, oy, oz). Cached (the full building load is slow)."""
    import json
    from shapely import wkt
    c = _cget(); key = "|".join(parts)
    if key not in c:
        Bs = [bid(p) for p in parts]
        P = outline(Bs[0]["fp"], 0.5); cc = P.centroid
        ox, oy = round(cc.x, 1), round(cc.y, 1)
        c[key] = {"ox": ox, "oy": oy, "oz": ground(ox, oy), "b": [{"id": B["id"], "fp": B["fp"].wkt, "zmax": B["zmax"], "zmin": B["zmin"]} for B in Bs]}
        _CACHE.parent.mkdir(parents=True, exist_ok=True); json.dump(c, open(_CACHE, "w"))
    e = c[key]
    if len(e["b"]) > 1 and "gz" not in e["b"][0]:
        for b in e["b"]:
            cc = wkt.loads(b["fp"]).centroid; b["gz"] = ground(cc.x, cc.y)
        json.dump(c, open(_CACHE, "w"))
    Bs = [{"id": b["id"], "fp": wkt.loads(b["fp"]), "zmax": b["zmax"], "zmin": b["zmin"], "gz": b.get("gz", e["oz"])} for b in e["b"]]
    return Bs, e["ox"], e["oy"], e["oz"]


def ring_of(B, ox, oy, tol=0.5):
    return orient(localize(outline(B["fp"], tol), ox, oy), 1.0)


def hide_of(Bs):
    out = []
    for B in Bs:
        for g in (B["fp"].geoms if hasattr(B["fp"], "geoms") else [B["fp"]]):
            p = g.representative_point(); out.append([round(p.x, 1), round(p.y, 1)])
    return out


def make_run(m, mw, mg, mf, rng, wall_col=W, wmod=(4.0, 4.0)):
    """Window run along edge a->b (volkshaus pattern). fn(u0,u1,z0,z1,i,nb,L) -> hole polygon (u,z) or None."""
    def run(a, b, zb, fh, bayw, fn, depth, surr_w=0.0, sill=0.0, surr_col=None, reveal=None, wm=None):
        L, t, n = D.frame_of(a, b); nb = max(1, int(round(L / bayw))); bw = L / nb
        for i in range(nb):
            u0, u1 = i * bw, (i + 1) * bw
            hole = fn(u0, u1, zb, zb + fh, i, nb, L)
            if hole is None:
                D.poly_wall(m, mw, Polygon(D.rect_pts(u0, zb, u1, zb + fh)), a, t, n, 0.0, wall_col, lambda u, z: (u / wmod[0], z / wmod[1])); continue
            dep = depth(i, nb, L) if callable(depth) else depth
            D.bay(m, mw, mg, mf, a, t, n, u0, u1, zb, zb + fh, hole, dep, int(rng.integers(0, D.NV)), wall_col, reveal or surr_col or hx("#bdb09a"), wm or wmod, None)
            if surr_w and surr_col: D.surround(m, mf, a, t, n, hole, surr_w, surr_col, 0.05, sill)
    return run


def rect_hole(w, h, lo=0.8):
    def f(u0, u1, f0, f1, i, nb, L):
        uc = (u0 + u1) / 2; ww = min(w, (u1 - u0) - 0.7)
        return D.rect_pts(uc - ww / 2, f0 + lo, uc + ww / 2, f0 + lo + h)
    return f


def arch_hole(w, lo, hs, h_spring):
    def f(u0, u1, f0, f1, i, nb, L):
        uc = (u0 + u1) / 2; ww = min(w, (u1 - u0) - 0.7)
        return D.arch_pts(uc - ww / 2, f0 + lo, uc + ww / 2, f0 + h_spring)
    return f


def edge_iter(ring):
    ne = len(ring)
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; L, t, n = D.frame_of(a, b)
        yield i, a, b, L, t, n


def pilasters(m, mf, a, b, z0, z1, pitch, w, d, col, skip_end=0.0):
    L, t, n = D.frame_of(a, b); nb = max(1, int(round(L / pitch))); ang = math.atan2(t[1], t[0])
    for i in range(nb + 1):
        u = i * L / nb
        if skip_end and (u < skip_end or u > L - skip_end): continue
        p = D.P3(a, t, n, u, 0, d / 2 - 0.02)
        m.box(mf, p[0], p[1], w, d, z0, z1, rot=ang, col=col)


def gable_run(m, mr, mg, pts, z, rise, col, gcol=None):
    """Plain gable roof over an oriented rect from lm.rect_of; kept for convenience."""
    gable_roof(m, mr, mg, pts, z, rise, col, gcol or col)


def info(m, name):
    print(name, m.tri_count(), "tris;", ", ".join(f"{k}={v.tris()}" for k, v in m.mats.items()))


def slope_roof(m, mr, Pl, z0, rise, d, col, cap=True):
    """Hip-like sloped roof over an arbitrary ring (shapely Polygon): one sloped quad per edge going inward by d, corner fill triangles at
    convex corners, flat cap over Pl.buffer(-d). Works for L/U shapes where lm.taper (scale about centroid) does not."""
    Pl = orient(Pl, 1.0); ring = list(Pl.exterior.coords)[:-1]; ne = len(ring)
    nr = [D.frame_of(ring[i], ring[(i + 1) % ne])[2] for i in range(ne)]
    for i in range(ne):
        a, b = ring[i], ring[(i + 1) % ne]; n = nr[i]
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1e-3: continue
        m.quad(mr, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0] - n[0] * d, b[1] - n[1] * d, z0 + rise), (a[0] - n[0] * d, a[1] - n[1] * d, z0 + rise)], col=col)
    for i in range(ne):
        v = ring[(i + 1) % ne]; n1, n2 = nr[i], nr[(i + 1) % ne]
        cr = n1[0] * n2[1] - n1[1] * n2[0]
        if cr < -1e-3:   # convex (CCW ring, outward normals turn clockwise)
            p = [(v[0], v[1], z0), (v[0] - n1[0] * d, v[1] - n1[1] * d, z0 + rise), (v[0] - n2[0] * d, v[1] - n2[1] * d, z0 + rise)]
            nn = np.cross(np.array(p[1]) - np.array(p[0]), np.array(p[2]) - np.array(p[0]))
            if nn[2] < 0: p = [p[0], p[2], p[1]]
            m.tri(mr, p, col=col)
    if cap:
        Q = Pl.buffer(-d, join_style=2)
        for g in ([Q] if Q.geom_type == "Polygon" else list(Q.geoms)):
            if g.area > 0.5: m.flat(mr, g, z0 + rise, col)


def crenels(m, mf, a, b, z, pitch, w, h, d, col, off=0.0):
    L, t, n = D.frame_of(a, b); nb = max(1, int(L / pitch)); ang = math.atan2(t[1], t[0])
    for i in range(nb):
        p = D.P3(a, t, n, (i + 0.5) * L / nb, 0, off - d / 2)
        m.box(mf, p[0], p[1], w, d, z, z + h, rot=ang, col=col)


def clock_painter(x0, face="#f1efe6", ring="#2a2a2a", hands="#222"):
    """Sign painter drawing a 30 px clock face at x0 in the glass-atlas strip (use txtq with x0..x0+32)."""
    def paint(d, de, x, y, w, hh):
        cx, cy = x0 + 16, y + 16
        d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=hexc(ring)); d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=hexc(face))
        d.line([cx, cy, cx - 6, cy - 8], fill=hexc(hands), width=2); d.line([cx, cy, cx + 8, cy - 9], fill=hexc(hands), width=1)
        de.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(60, 56, 40))
    return paint


def both(*painters):
    def paint(d, de, x, y, w, hh):
        for p in painters: p(d, de, x, y, w, hh)
    return paint


def clock_quad(m, mg, a, t, n, u, z, size, x0, off=0.08):
    p0 = D.P3(a, t, n, u - size / 2, z - size / 2, off); p1 = D.P3(a, t, n, u + size / 2, z - size / 2, off)
    m.quad(mg, [p0, p1, (p1[0], p1[1], z + size / 2), (p0[0], p0[1], z + size / 2)],
           [(x0 / 1024, 0.0), ((x0 + 32) / 1024, 0.0), ((x0 + 32) / 1024, 0.25), (x0 / 1024, 0.25)], n=(n[0], n[1], 0))
