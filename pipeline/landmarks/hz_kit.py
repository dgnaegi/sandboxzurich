"""Shared helpers for the Hohlstrasse / Egli-Siedlung landmarks (hz_*.py). Style = k4w3 kit (lm.py + detail.py). Additive only.
Footprints come from OSM (the same polygons the game extrudes) because the 2022/23 Egli buildings are not in swissBUILDINGS3D.
Registers into pipeline/overrides/landmarks_hz.json (common.OVR is redirected after the k4w3 import)."""
from k4w3_kit import *
import common
from k45_volkshaus import plaster
from shapely.geometry import LineString

common.OVR = ROOT / "pipeline" / "overrides" / "landmarks_hz.json"


def osm_polys(keys, near_xy=(-420, -80), r=160):
    """keys: list of (street, nr) or ('@', x, y) -> [(label, global shapely polygon)]. '@' picks the OSM building containing the point."""
    allb = osm_named(near_xy[0], near_xy[1], r)
    out = []
    for k in keys:
        hit = None
        for t, g in allb:
            if k[0] == "@":
                if g.contains(Point(k[1], k[2])): hit = g
            elif t.get("addr:street") == k[0] and t.get("addr:housenumber") == k[1]:
                hit = g
        if hit is None:
            raise SystemExit(f"no OSM building for {k}")
        out.append((" ".join(str(x) for x in k), hit))
    return out


def centre_of(polys):
    from shapely.ops import unary_union
    c = unary_union([g for _, g in polys]).centroid
    return round(c.x, 1), round(c.y, 1)


def hide_pts(polys):
    return [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for _, g in polys]


def local_ring(g, ox, oy):
    P = orient(localize(g.simplify(0.15), ox, oy), 1.0)
    if P.geom_type == "MultiPolygon":
        P = max(P.geoms, key=lambda p: p.area)
    return P


def pv_panels(m, mf, Pl, z, rng, keep=1.7, rows_dir=None, col="#23282f", max_n=90):
    """Flat-roof PV: rows of dark panels (1.0 x 1.75 m, 0.18 m high) on a grid inside Pl.buffer(-keep)."""
    Q = Pl.buffer(-keep, join_style=2)
    if Q.is_empty: return 0
    (cx, cy), ux, uy, L, W = rect_of(Pl)
    vx, vy = -uy, ux; ang = math.atan2(uy, ux); n = 0
    pw, pd, gap = 1.05, 1.8, 0.35
    nu = int(L / (pw + gap)); nv = int(W / (pd + 1.0))
    for i in range(nu):
        for j in range(nv):
            a = -L / 2 + (i + 0.5) * (pw + gap); b = -W / 2 + (j + 0.5) * (pd + 1.0)
            x, y = cx + ux * a + vx * b, cy + uy * a + vy * b
            if not Q.contains(Point(x, y)): continue
            if rng.random() < 0.08: continue
            m.box(mf, x, y, pw, pd, z, z + 0.17, rot=ang, col=hx(col)); n += 1
            if n >= max_n: return n
    return n


def balcony(m, mf, a, t, n, u, z, w=2.5, d=1.45, slab_col="#ecebe6", rail_col="#cdd1d3", hrail=1.05):
    """Projecting balcony: slab + slatted/solid light balustrade on the front and both sides."""
    ang = math.atan2(t[1], t[0])
    c = D.P3(a, t, n, u, 0, d / 2 - 0.02)
    m.box(mf, c[0], c[1], w, d, z - 0.2, z, rot=ang, col=hx(slab_col))
    f = D.P3(a, t, n, u, 0, d - 0.05)
    m.box(mf, f[0], f[1], w, 0.06, z, z + hrail, rot=ang, col=hx(rail_col))
    for s in (-1, 1):
        sd = D.P3(a, t, n, u + s * (w / 2 - 0.03), 0, d / 2)
        m.box(mf, sd[0], sd[1], 0.06, d - 0.1, z, z + hrail, rot=ang, col=hx(rail_col))


def glazed_oriel(m, mf, mg, a, t, n, u, z0, h, k, w=2.7, d=0.95, post_col="#f1f1ee", spandrel_col="#e9e9e6", sp=0.9, nv=8):
    """Closed glazed bay (winter garden) projecting from the wall: spandrel panel, glass band (atlas cell k), flat top and sides."""
    ang = math.atan2(t[1], t[0]); cu0, cu1 = k / nv, (k + 1) / nv
    P = lambda uu, zz, dd: D.P3(a, t, n, uu, zz, dd)
    u0, u1 = u - w / 2, u + w / 2
    m.quad(mf, [P(u0, z0, d), P(u1, z0, d), P(u1, z0 + sp, d), P(u0, z0 + sp, d)], col=hx(spandrel_col), n=(n[0], n[1], 0))
    m.quad(mg, [P(u0, z0 + sp, d), P(u1, z0 + sp, d), P(u1, z0 + h - 0.15, d), P(u0, z0 + h - 0.15, d)], [(cu0, 0.25), (cu1, 0.25), (cu1, 1.0), (cu0, 1.0)], n=(n[0], n[1], 0))
    m.quad(mf, [P(u0, z0 + h - 0.15, d), P(u1, z0 + h - 0.15, d), P(u1, z0 + h, d), P(u0, z0 + h, d)], col=hx(post_col), n=(n[0], n[1], 0))
    for uu, s in ((u0, -1), (u1, 1)):   # side faces (closed) and posts
        q = [P(uu, z0, 0), P(uu, z0, d), P(uu, z0 + h, d), P(uu, z0 + h, 0)]
        m.quad(mf, q if s > 0 else q[::-1], col=hx(spandrel_col), n=(t[0] * s, t[1] * s, 0))
    m.quad(mf, [P(u0, z0 + h, d), P(u1, z0 + h, d), P(u1, z0 + h, 0), P(u0, z0 + h, 0)], col=hx("#d7d8d5"), n=(0, 0, 1))
    m.quad(mf, [P(u0, z0, 0), P(u1, z0, 0), P(u1, z0, d), P(u0, z0, d)], col=hx("#b9bbba"), n=(0, 0, -1))


def shutter_quad(m, mf, a, t, n, u, z0, z1, w, col="#c8773a", off=0.06):
    p0 = D.P3(a, t, n, u - w / 2, z0, off); p1 = D.P3(a, t, n, u + w / 2, z0, off)
    m.quad(mf, [p0, p1, (p1[0], p1[1], z1), (p0[0], p0[1], z1)], col=hx(col), n=(n[0], n[1], 0))


def facade_building(m, mw, mg, mf, rng, Pl, g, floors, fh0, fh, *, wall, bay=3.2, ww=1.25, wh=1.75, sill=0.9, wmod=(4.0, 4.0),
                    reveal="#d9d6cf", frame_sp="#ecebe6", cornice=None, balc_pred=None, oriel_pred=None, shutter_p=0.0,
                    ground_open=None, nv=8, cornice_out=0.12, z_top=None):
    """Walls with window bays on every edge of Pl (CCW). Returns z of the eave (top of the last floor).
    balc_pred(i, a, b, n, mid) -> bool: edge gets balconies (every 3rd bay, floors >= 1). oriel_pred likewise (2-storey glazed bays, every 3rd bay).
    ground_open(i, a, b, n, mid) -> dict(w, h, lo) for taller ground-floor openings (shopfront/entrance) or None."""
    z1 = g + fh0
    zt = z_top if z_top is not None else z1 + (floors - 1) * fh
    for i, a, b, L, t, n in edge_iter(list(Pl.exterior.coords)[:-1]):
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if L < 1.2:
            m.wall(mw, a, b, g, zt, wmod, wall); continue
        nb = max(1, int(round(L / bay))); bw = L / nb
        go = ground_open(i, a, b, n, mid) if ground_open else None
        bal = balc_pred(i, a, b, n, mid) if balc_pred else False
        ori = oriel_pred(i, a, b, n, mid) if oriel_pred else False
        for f in range(floors):
            zf0 = g if f == 0 else z1 + (f - 1) * fh
            zf1 = z1 if f == 0 else z1 + f * fh
            hf = zf1 - zf0
            for k in range(nb):
                u0, u1 = k * bw, (k + 1) * bw; uc = (u0 + u1) / 2
                if bw < 1.5 or L < 2.2:
                    D.poly_wall(m, mw, Polygon(D.rect_pts(u0, zf0, u1, zf1)), a, t, n, 0.0, wall, lambda u, z: (u / wmod[0], z / wmod[1])); continue
                if f == 0:
                    o = go if go else dict(w=ww + 0.1, h=wh + 0.35, lo=sill - 0.1)
                    w_, h_, lo = min(o["w"], bw - 0.7), o["h"], o["lo"]
                    if go and go.get("door") and k == nb // 2: lo = 0.0
                else:
                    w_, h_, lo = ww, wh, sill
                    if ori and 1 <= f <= 4 and k % 3 == 1:     # two-storey glazed bay replaces the plain window
                        D.poly_wall(m, mw, Polygon(D.rect_pts(u0, zf0, u1, zf1)), a, t, n, 0.0, wall, lambda u, z: (u / wmod[0], z / wmod[1]))
                        if f % 2 == 1 and f + 1 < floors:
                            glazed_oriel(m, mf, mg, a, t, n, uc, zf0 + 0.35, 2 * fh - 0.7, int(rng.integers(0, nv)), w=min(2.7, bw - 0.5), nv=nv)
                        continue
                    if bal and k % 3 == 1:                 # French window onto a balcony
                        w_, h_, lo = 1.15, 2.2, 0.15
                hole = D.rect_pts(uc - w_ / 2, zf0 + lo, uc + w_ / 2, zf0 + lo + h_)
                D.bay(m, mw, mg, mf, a, t, n, u0, u1, zf0, zf1, hole, 0.14, int(rng.integers(0, nv)), wall, hx(reveal), wmod, 0.07 if f > 0 and not (bal and k % 3 == 1) else None)
                if f >= 1 and bal and k % 3 == 1:
                    balcony(m, mf, a, t, n, uc, zf0)
                elif f >= 1 and shutter_p and rng.random() < shutter_p:
                    shutter_quad(m, mf, a, t, n, uc - w_ / 2 - 0.35, zf0 + lo, zf0 + lo + h_, 0.5)
        if cornice:
            D.band(m, mf, a, b, zt - 0.25, zt + 0.1, cornice_out, hx(cornice))
    return zt


def pavilion_hex(m, mw, mg, mf, rng, Pl, g, nf, fh, wall, roof_col, rise=3.6, nv=8):
    """Small hexagonal 3-storey pavilion with a hip roof (Egli-Siedlung courtyard houses)."""
    zt = facade_building(m, mw, mg, mf, rng, Pl, g, nf, fh, fh, wall=wall, bay=3.0, ww=1.1, wh=1.7, sill=0.95, shutter_p=0.25, nv=nv, cornice="#e4e2dc", cornice_out=0.25)
    taper(m, mf, Pl.buffer(0.45, join_style=2), zt - 0.1, zt - 0.1 + rise, 0.04, hx(roof_col))
    return zt
