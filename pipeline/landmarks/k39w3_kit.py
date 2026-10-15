"""Kit for the Kreis 3/9 landmark wave 3 (k39w3_*.py): footprint prep, parametric window facades (lm.py/detail.py based),
free-font sign strips, roofs, registration in overrides/landmarks_k39w3.json. Additive: touches no other module."""
import math, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import *
from lm import *
import detail as D

hexl = D.hexl
W4 = (255, 255, 255, 255)
OVR39 = ROOT / "pipeline" / "overrides" / "landmarks_k39w3.json"
FONTS = ROOT / "web" / "public" / "fonts"


def plaster(color, seed=3, size=128, stains=0.04, amp=3):
    rng = np.random.default_rng(seed)
    a = np.full((size, size, 4), 255, np.uint8); a[..., :3] = color[:3]
    a[..., :3] = np.clip(a[..., :3] + rng.normal(0, amp, (size, size, 1)), 0, 255).astype(np.uint8)
    for _ in range(10):
        x, y, r = rng.integers(0, size), rng.integers(0, size), rng.integers(10, 30); f = 1 + rng.normal(0, stains)
        yy, xx = np.ogrid[:size, :size]; mk = ((xx - x) ** 2 + (yy - y) ** 2) < r * r
        a[mk, :3] = np.clip(a[mk, :3] * f, 0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def clinker(color, size=128, seed=3, rows=24):
    """Brick / clinker wall (running bond)."""
    rng = np.random.default_rng(seed); im = Image.new("RGBA", (size, size), shade(hexc("#c9c2b4"), 0.9)); d = ImageDraw.Draw(im)
    bh = size // rows; base = np.array(color[:3], float)
    for r in range(rows):
        off = (r % 2) * (size // 16)
        for x in range(-size // 8, size, size // 8):
            f = 1 + rng.normal(0, 0.06); c = tuple(int(np.clip(v * f, 0, 255)) for v in base) + (255,)
            d.rectangle([x + off + 1, r * bh + 1, x + off + size // 8 - 1, r * bh + bh - 1], fill=c)
    return im


def panels(color, size=128, nx=4, ny=4, seed=3, gap="#8a8d90", amp=2):
    """Flat cladding panels with thin joints."""
    rng = np.random.default_rng(seed); im = Image.new("RGBA", (size, size), hexc(color)); d = ImageDraw.Draw(im)
    for i in range(nx):
        for j in range(ny):
            f = 1 + rng.normal(0, 0.012); c = tuple(int(np.clip(v * f, 0, 255)) for v in hexc(color)[:3]) + (255,)
            d.rectangle([i * size // nx, j * size // ny, (i + 1) * size // nx, (j + 1) * size // ny], fill=c, outline=hexc(gap))
    return im


def tiles_roof(color="#8a3f2c", size=128, rows=12, cols=8, seed=4, var=0.12):
    rng = np.random.default_rng(seed); im = Image.new("RGBA", (size, size), shade(hexc(color), 0.7)); d = ImageDraw.Draw(im)
    h, w = size // rows, size // cols
    for r in range(rows):
        for c in range(-1, cols):
            f = 1 + rng.normal(0, var); col = tuple(int(np.clip(v * f, 0, 255)) for v in hexc(color)[:3]) + (255,)
            x = c * w + (w // 2 if r % 2 else 0)
            d.rectangle([x + 1, r * h, x + w - 1, r * h + h - 1], fill=col)
            d.line([x + 1, r * h + h - 1, x + w - 1, r * h + h - 1], fill=shade(hexc(color), 0.55))
    return im


def strip(regions, size=26, W=1024, h=32, font="Barlow-Bold", gap_max=3):
    """Sign painter for glass_atlas_g(sign=...): free font (Barlow). regions: (x0, x1, text, fg, bg, glow|None)."""
    def paint(d, de, x, y, w, hh):
        f = ImageFont.truetype(str(FONTS / (font + ".ttf")), size)
        for x0, x1, text, fg, bg, glow in regions:
            d.rectangle([x0, y, x1 - 1, y + hh], fill=hexc(bg))
            ws = [d.textlength(ch, font=f) for ch in text]; tot = sum(ws)
            gap = min(gap_max, max(0, (0.88 * (x1 - x0) - tot) / max(1, len(text) - 1)))
            cx = x0 + ((x1 - x0) - (tot + gap * (len(text) - 1))) / 2
            for ch, wc in zip(text, ws):
                d.text((cx, y + hh / 2), ch, font=f, fill=hexc(fg), anchor="lm")
                if glow: de.text((cx, y + hh / 2), ch, font=f, fill=glow, anchor="lm")
                cx += wc + gap
    return paint


class Ctx:
    pass


def prep(prefixes=None, tol=0.5, fp=None, orient_to=None, hide_extra=()):
    """prefixes: swissBUILDINGS3D ids ('ID_xxxxxxxx') whose footprints are unioned; or fp (shapely polygon in global metres)."""
    c = Ctx(); c.B = [bid(p) for p in (prefixes or [])]
    if fp is None: fp = unary_union([b["fp"] for b in c.B])
    c.G = outline(fp, tol)
    cc = c.G.centroid; c.ox, c.oy = round(cc.x, 1), round(cc.y, 1); c.oz = ground(c.ox, c.oy)
    c.P = orient(localize(c.G, c.ox, c.oy), 1.0); c.ring = list(c.P.exterior.coords)[:-1]
    c.hide = []
    for b in c.B:
        for g in (b["fp"].geoms if hasattr(b["fp"], "geoms") else [b["fp"]]):
            c.hide.append([round(g.representative_point().x, 1), round(g.representative_point().y, 1)])
    c.hide += [list(h) for h in hide_extra]
    return c


def hole_fn(kind, bw, fb, fh, ww=0.5, wh=0.62, so=0.2):
    """Opening polygon (u,z) centred in a bay [0,bw]: ww/wh as fractions or metres (>=1 -> metres)."""
    w = ww * bw if ww < 1 else ww; hgt = wh * fh if wh < 1.5 else wh; z0 = fb + (so if so >= 0.05 else so * fh)
    u0 = bw / 2 - w / 2
    if kind == "arch": return D.arch_pts(u0, z0, u0 + w, z0 + hgt - w / 2)
    if kind == "pointed": return D.pointed_pts(u0, z0, u0 + w, z0 + hgt - w * 0.8)
    return D.rect_pts(u0, z0, u0 + w, z0 + hgt)


def facade(m, mw, mg, mf, ring, z0, nf, fh, st, rng, wcol=W4, rev=None, minL=1.5):
    """Window facade over all ring edges. st: dict with bayw, kind, ww, wh, so, depth, surr(col|None), surr_w, sill, wmod, gf (override dict for floor 0),
    top (dict like st for the last floor, or None), edge(i, a, b, L) -> None | 'blind' | dict(override). Returns nothing."""
    rev = rev or hexl("#cfc9b8")
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]; L, t, n = D.frame_of(a, b)
        ov = st["edge"](i, a, b, L) if st.get("edge") else None
        s0 = dict(st)
        if isinstance(ov, dict): s0.update(ov)
        if L < minL or ov == "blind":
            m.wall(mw, a, b, z0, z0 + nf * fh, (4, 4), wcol); continue
        nb = max(1, int(round(L / s0["bayw"]))); bw = L / nb
        for f in range(nf):
            sp = dict(s0)
            if f == 0 and s0.get("gf"): sp.update(s0["gf"])
            if f == nf - 1 and s0.get("top"): sp.update(s0["top"])
            fb = z0 + f * fh
            for k in range(nb):
                u0, u1 = k * bw, (k + 1) * bw
                hl = hole_fn(sp["kind"], bw, fb, fh, sp.get("ww", .5), sp.get("wh", .62), sp.get("so", .2)) if not (sp.get("skip") and sp["skip"](k, nb, f)) else None
                if sp.get("hole_override"):
                    h2 = sp["hole_override"](k, nb, f, bw, fb, fh)
                    if h2 is not None: hl = h2
                if hl is None:
                    D.poly_wall(m, mw, Polygon(D.rect_pts(u0, fb, u1, fb + fh)), a, t, n, 0.0, wcol, lambda u, z: (u / 4, z / 4)); continue
                hl = [(u0 + p[0], p[1]) for p in hl]
                D.bay(m, mw, mg, mf, a, t, n, u0, u1, fb, fb + fh, hl, sp.get("depth", .25), int(rng.integers(0, D.NV)), wcol, rev, sp.get("wmod", (4, 4)), None)
                if sp.get("hook"): sp["hook"](m, a, t, n, u0, u1, hl, f, k)
                if sp.get("surr") is not None:
                    D.surround(m, mw, a, t, n, hl, sp.get("surr_w", .12), sp["surr"], 0.04, sill=0.1 if sp.get("sill", True) else 0)
        for band in st.get("bands", ()):   # (z, h, out, color)
            D.band(m, mw, a, b, band[0], band[0] + band[1], band[2], band[3])


def corner_pilasters(m, mw, ring, z0, z1, w, col):
    for i in range(len(ring)):
        p = ring[i]; q = ring[(i + 1) % len(ring)]
        m.box(mw, p[0], p[1], w, w, z0, z1, rot=math.atan2(q[1] - p[1], q[0] - p[0]), col=col)


def hip_roof(m, mf, P, eave_z, rise, col, grow=0.5, s=0.35):
    return taper(m, mf, P.buffer(grow, join_style=2), eave_z, eave_z + rise, s, col, cap=True)


def chimney(m, mf, x, y, z0, z1, col="#a87a62", w=1.1):
    m.box(mf, x, y, w, w, z0, z1, col=hexl(col)); m.box(mf, x, y, w + .3, w + .3, z1, z1 + .25, col=hexl("#5a5a58"))


def finish39(model, name, title, ox, oy, oz, hide):
    OUTDIR.mkdir(parents=True, exist_ok=True); RAWDIR.mkdir(parents=True, exist_ok=True)
    raw = RAWDIR / f"{name}.glb"; model.write(str(raw)); out = OUTDIR / f"{name}.glb"
    r = subprocess.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(out), "-cc", "-kn"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:])
    print(f"{name}: {model.tri_count()} tris, " + ", ".join(f"{k}={m.tris()}" for k, m in model.mats.items()) + f", glb {out.stat().st_size // 1024} kB, hide {len(hide)}")
    assert model.tri_count() <= 30000, "tri budget"
    d = json.load(open(OVR39)) if OVR39.exists() else {"landmarks": []}
    try: old = next(e["hide"] for e in d["landmarks"] if e["name"] == title)
    except StopIteration: old = []
    hh = [list(h) for h in old]
    for h in hide:
        if not any(abs(h[0] - o[0]) < 0.3 and abs(h[1] - o[1]) < 0.3 for o in hh): hh.append(list(h))
    d["landmarks"] = [e for e in d["landmarks"] if e["name"] != title]
    d["landmarks"].append({"name": title, "model": f"/models/landmarks/{name}.glb", "x": round(ox, 2), "y": round(oy, 2), "z": round(oz, 2), "heading": 0, "hide": hh})
    json.dump(d, open(OVR39, "w"), indent=1, ensure_ascii=False)
    import merge; merge.main()


def shutters(m, mat, a, t, n, hl, col, w=0.5, off=0.06):
    """Pair of louvre shutters either side of opening hl (u,z polygon) as thin slabs on the wall plane."""
    us = [p[0] for p in hl]; zs = [p[1] for p in hl]; u0, u1, z0, z1 = min(us), max(us), min(zs), max(zs)
    for (ua, ub) in ((u0 - w - 0.04, u0 - 0.04), (u1 + 0.04, u1 + w + 0.04)):
        D._oriented(m, mat, [D.P3(a, t, n, ua, z0, off), D.P3(a, t, n, ub, z0, off), D.P3(a, t, n, ub, z1, off), D.P3(a, t, n, ua, z1, off)], (n[0], n[1], 0),
                    [(0, 0), (1, 0), (1, 1), (0, 1)], col)


def roof_parts(prefix, ox, oy, oz, step=3.0, min_area=15.0, pitched_as_flat=True):
    """Height-class massing from the swissBUILDINGS3D roof faces: [(Polygon local, height_above_ground)] sorted low -> high.
    Roof polys of each class (height rounded to `step`) are unioned and slightly fused; small slivers dropped."""
    import pickle, glob
    from shapely.affinity import translate
    classes = {}
    for f in glob.glob(str(ROOT / "data/build/bld/*.pkl")):
        for o in pickle.load(open(f, "rb")):
            if o["id"][3:11] != prefix: continue
            for k, q in o["polys"]:
                if k != 2 or len(q) < 3: continue
                try: g = Polygon(q[:, :2]).buffer(0)
                except Exception: continue
                if g.area < 0.5: continue
                h = float(q[:, 2].max()) - oz; key = round(h / step) * step
                classes.setdefault(key, []).append(g)
    out = []
    for key, gs in sorted(classes.items()):
        u = unary_union([g.buffer(0.6, join_style=2) for g in gs]).buffer(-0.5, join_style=2)
        for g in ([u] if u.geom_type == "Polygon" else list(u.geoms)):
            if g.area >= min_area:
                g = g.simplify(0.8).buffer(0); out.append((orient(translate(g, -ox, -oy), 1.0), max(key, step)))
    return out
