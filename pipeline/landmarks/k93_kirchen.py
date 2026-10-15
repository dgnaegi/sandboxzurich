"""Kirchen: Alte Kirche (Spitzhelm-Turm) + Kirche Altstetten (Moser 1941, Betonrasterturm), Dreifaltigkeitskirche Wiedikon.
Grundrisse/Hoehen aus swissBUILDINGS3D; Fassaden/Dach/Turm prozedural. -> k93_kirche_altstetten.glb, k93_dreifaltigkeit.glb"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, terrain, k93_kit as K
from k93_lib import hexc, shade
OUTD = F.ROOT + "/web/public/models/landmarks/"
WHITE = (255, 255, 255, 255)


def round_clock(size=192, face="#f4f0dc", ring="#c9a34a", ink="#22252c"):
    im = Image.new("RGB", (size, size), K.rgb("#d8d2bc")); d = ImageDraw.Draw(im); c = size / 2
    d.ellipse([2, 2, size - 3, size - 3], fill=K.rgb(ring)); d.ellipse([size * 0.07, size * 0.07, size * 0.93, size * 0.93], fill=K.rgb(face))
    for k in range(12):
        a = math.radians(k * 30 - 90); r0, r1 = size * (0.34 if k % 3 else 0.30), size * 0.42
        d.line([c + r0 * math.cos(a), c + r0 * math.sin(a), c + r1 * math.cos(a), c + r1 * math.sin(a)], fill=K.rgb(ink), width=3 if k % 3 == 0 else 2)
    d.line([c, c, c + size * 0.28 * math.cos(math.radians(-60)), c + size * 0.28 * math.sin(math.radians(-60))], fill=K.rgb(ink), width=3)
    d.line([c, c, c + size * 0.2 * math.cos(math.radians(40)), c + size * 0.2 * math.sin(math.radians(40))], fill=K.rgb(ink), width=5)
    return im


def tower_tex(w=7.0, h=45.0, ppm=14):
    """Concrete grid tower: pale concrete frame with rows of dark recessed slits, belfry zone at the top (module = whole tower face)."""
    W_, H_ = int(w * ppm), int(h * ppm); wc = K.rgb("#c6c0b0")
    im = K.noisy(Image.new("RGB", (W_, H_), wc), 5, 5, 0.5); d = ImageDraw.Draw(im); em = Image.new("RGB", (W_, H_), (0, 0, 0)); de = ImageDraw.Draw(em)
    px = lambda m: int(m * ppm)
    nx_ = 4; cw = w / nx_
    for r in range(0, int((h - 11) / 1.3)):
        y = px(2.0 + r * 1.3)
        for c in range(nx_):
            x = px(c * cw + cw * 0.3); d.rectangle([x, H_ - y - px(0.7), x + px(cw * 0.4), H_ - y], fill=K.mix(wc, (0, 0, 0), 0.7))
    # belfry: tall open arches
    for c in range(3):
        x = px(0.9 + c * 1.8); d.rectangle([x, px(2.0), x + px(1.3), px(7.3)], fill=(46, 48, 52)); d.pieslice([x, px(1.2), x + px(1.3), px(2.8)], 180, 360, fill=(46, 48, 52))
    d.rectangle([0, px(7.6), W_, px(8.0)], fill=K.mix(wc, (0, 0, 0), 0.2))
    return im, em


def church(M, M_, oid, p, eave, rise, ttop, spire, tw, style):
    o = [o for o in F.near(*p, 30) if o["id"][3:11] == oid][0]
    fp = F.footprint(o).simplify(0.4)
    z0 = float(H.at(*fp.centroid.coords[0]))
    r = list(fp.minimum_rotated_rectangle.exterior.coords)[:4]
    e1 = np.subtract(r[1], r[0]); e2 = np.subtract(r[2], r[1])
    if np.hypot(*e1) < np.hypot(*e2): e1, e2 = e2, e1
    ang = math.atan2(e1[1], e1[0]); Lg, Sh = np.hypot(*e1), np.hypot(*e2)
    ctr = np.array(fp.centroid.coords[0]); u = e1 / Lg
    roof = np.vstack([q for k, q in o["polys"] if k == 2]); top = roof[np.argmax(roof[:, 2])][:2]; sgn = 1 if np.dot(top - ctr, u) > 0 else -1
    base = z0 - 2.5
    pts = list(fp.exterior.coords)[:-1]
    n = np.array([-u[1], u[0]])
    old = style == "old"
    WALL, PLINTH, ROOF, TRIM, SPIRE, TOWER, CLK = M_
    K.wall_band(M, PLINTH, pts, base, z0 + 0.9, 3.0, 1.5)
    K.wall_band(M, WALL, pts, z0 + 0.9, z0 + eave, 4.4 if old else 4.0, eave - 0.9 if old else eave - 0.9, nx=4, ny=1)
    M.prism(TRIM, list(fp.buffer(0.2, join_style=2).exterior.coords)[:-1], z0 + eave - 0.5, z0 + eave + 0.05, hexc("#d9d2bf") if old else hexc("#b1aa9a"), top=False)
    K.pitched(M, ROOF, tuple(ctr), Lg, Sh, z0 + eave, rise, rot=ang, eave=0.5 if old else 0.9, tile=1.0, col=WHITE, gable_mat=TRIM, gable_col=hexc("#eee8d8") if old else hexc("#cbc3b0"), gable_tile=(4.0, 3.0))
    tc = ctr + u * sgn * (Lg / 2 - tw / 2 + 0.3)
    sq = [tc + (u * a + n * b) * tw / 2 for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    zb = z0 + ttop - spire
    if old:
        K.wall_band(M, WALL, [tuple(q) for q in sq], z0 + eave - 1.0, zb - 6.0, 4.4, 4.0, nx=4, ny=1)
        # belfry stage: arched louvre openings
        for sg in (-1, 1):
            for ax, ln_ in ((u, n), (n, u)):
                c = tc + ax * sg * (tw / 2 + 0.03)
                M.box(TRIM, (c[0], c[1], zb - 3.0), (0.1 if ax is u else 1.5, 1.5 if ax is u else 0.1, 3.0), hexc("#2b3036"), rot=ang)
        K.wall_band(M, WALL, [tuple(q) for q in sq], zb - 6.0, zb, 4.4, 6.0, nx=4, ny=1)
        for sg in (-1, 1):   # round clock faces on the four sides
            for ax in (u, n):
                c = tc + ax * sg * (tw / 2 + 0.05); cd = 1.9
                dirv = np.array([-ax[1], ax[0]]) * sg
                K.quad_tex(M, CLK, c - dirv * cd / 2, c + dirv * cd / 2, zb - 7.0, zb - 7.0 + cd)
        M.cap(TRIM, [tuple(q) for q in sq], zb, hexc("#444a50"))
        K.spire(M, SPIRE, tuple(tc), tw / 2 * 1.08, zb, z0 + ttop, n=4, rot=ang + math.pi / 4, col=WHITE, tile=1.0)
        M.box(TRIM, (tc[0], tc[1], z0 + ttop + 0.9), (0.12, 0.12, 1.8), hexc("#c8a64a"))
        M.box(TRIM, (tc[0], tc[1], z0 + ttop + 1.3), (0.7, 0.1, 0.1), hexc("#c8a64a"))
    else:
        # concrete grid tower, flat top with slender belfry slab, yellow clock faces below the top
        K.wall_band(M, TOWER, [tuple(q) for q in sq], z0 + eave - 4.0, z0 + ttop, tw, ttop - eave + 4.0, nx=1, ny=1)
        M.prism(TRIM, [tuple(tc + (u * a + n * b) * (tw / 2 + 0.3)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))], z0 + ttop - 0.5, z0 + ttop + 0.35, hexc("#b9b3a3"), top=True)
        for sg in (-1, 1):
            for ax in (u, n):
                c = tc + ax * sg * (tw / 2 + 0.06); cd = 3.0
                dirv = np.array([-ax[1], ax[0]]) * sg
                K.quad_tex(M, CLK, c - dirv * cd / 2, c + dirv * cd / 2, z0 + ttop - 11.0, z0 + ttop - 11.0 + cd)
    return z0


H = None
def build(name, items, origin_xy, outname, mats_fn):
    global H
    H = terrain.heights((origin_xy[0] - 80, origin_xy[1] - 80, origin_xy[0] + 80, origin_xy[1] + 80), 2.0, z_shift=-3.06)
    M = L.Model(origin=(origin_xy[0], origin_xy[1], float(H.at(*origin_xy))))
    mats = mats_fn(M)
    for it in items:
        key = it.pop("mats", None)
        church(M, mats[key] if key else mats, **it)
    M.write(OUTD + outname); print(name, "tris", M.tris(), "origin", origin_xy)


def mats_altstetten(M):
    clk = K.tile  # noqa
    old_win = K.tile(4, 1, 72, 96, K.window(wall="#eee8d8", frame="#f6f2e6", glass="#38424d", fw=0.30, fh=0.52, top=0.28, cols=2, rows=4, arch=True, surround="#e0d9c4", sill="#d4ccb8", noise=4, lit_col=(255, 214, 150)), seed=41, lit=0.0)
    def hall_mod(d, de, x, y, w, h, rng, on, ix, iy):
        wc = K.rgb("#cdc6b4"); d.rectangle([x, y, x + w - 1, y + h - 1], fill=tuple(int(v * (1 + (rng.random() - 0.5) * 0.04)) for v in wc))
        d.line([x, y, x, y + h], fill=K.mix(wc, (0, 0, 0), 0.18), width=2)
        gh = int(h * 0.30)                                              # glazed ground floor behind slim columns
        d.rectangle([x + 4, y + h - gh, x + w - 4, y + h - 3], fill=(44, 54, 62))
        for k in (0.5,): d.line([x + int(w * k), y + h - gh, x + int(w * k), y + h - 3], fill=(150, 146, 136), width=2)
        d.rectangle([x, y + h - gh - 4, x + w, y + h - gh], fill=K.mix(wc, (0, 0, 0), 0.25))
        for k in range(3):                                              # clerestory slits under the eaves
            sx = x + int(w * (0.12 + k * 0.30)); d.rectangle([sx, y + int(h * 0.12), sx + int(w * 0.2), y + int(h * 0.2)], fill=(52, 60, 68))
        if on:
            de.rectangle([x + 5, y + h - gh + 1, x + w - 5, y + h - 4], fill=(255, 214, 150))
            de.line([x + int(w * 0.5), y + h - gh, x + int(w * 0.5), y + h - 3], fill=(0, 0, 0), width=2)
    new_win = K.tile(4, 1, 80, 260, hall_mod, seed=42, lit=0.35)
    WO = M.mat("wall_old", rough=0.95, tex=old_win[0], emis=old_win[1], repeat=True)
    WN = M.mat("wall_new", rough=0.95, tex=new_win[0], emis=new_win[1], repeat=True)
    PL = M.mat("plinth", rough=0.95, tex=K.stone_tex("#8f8a7c", 0.25, seed=6, rustic=0.1), repeat=True)
    RO = M.mat("roof_old", rough=0.85, tex=K.tile_roof_tex("#8a6552", seed=7, var=0.22, moss=0.1), repeat=True)
    RN = M.mat("roof_new", rough=0.85, tex=K.tile_roof_tex("#7e463a", seed=8, var=0.2), repeat=True)
    SP = M.mat("spire", rough=0.7, tex=K.slate_tex("#3e4246", seed=9, rows=14), repeat=True)
    TW = tower_tex(7.0, 45.0); TOW = M.mat("tower", rough=0.9, tex=TW[0], emis=TW[1], repeat=False)
    ck = round_clock(); CKM = M.mat("clock", rough=0.5, tex=ck, emis=ck.point(lambda v: int(v * 0.55)), repeat=False)
    TR = M.mat("trim", rough=0.9)
    return {"old": (WO, PL, RO, TR, SP, TOW, CKM), "new": (WN, PL, RN, TR, SP, TOW, CKM)}


def mats_dreifaltigkeit(M):
    win = K.tile(4, 1, 72, 128, K.window(wall="#d9c9a6", frame="#efe6cf", glass="#363f48", fw=0.32, fh=0.6, top=0.18, cols=2, rows=5, arch=True, surround="#e6d9b8", sill="#cfc2a3", noise=5, lit_col=(255, 200, 130)), seed=43, lit=0.15)
    WL = M.mat("wall", rough=0.95, tex=win[0], emis=win[1], repeat=True)
    PL = M.mat("plinth", rough=0.95, tex=K.stone_tex("#8d8574", 0.25, seed=10, rustic=0.15), repeat=True)
    RO = M.mat("roof", rough=0.85, tex=K.tile_roof_tex("#774434", seed=11, var=0.2), repeat=True)
    SP = M.mat("spire", rough=0.6, tex=K.slate_tex("#5f8f7c", seed=12, rows=14), repeat=True)
    ck = round_clock(); CKM = M.mat("clock", rough=0.5, tex=ck, emis=ck.point(lambda v: int(v * 0.55)), repeat=False)
    TR = M.mat("trim", rough=0.9)
    return (WL, PL, RO, TR, SP, WL, CKM)


if __name__ == "__main__":
    os.makedirs(OUTD, exist_ok=True)
    build("Kirchen Altstetten", [
        dict(oid="96D18134", p=(-2388, 254), eave=7.5, rise=6.5, ttop=32.7, spire=11.0, tw=5.4, style="old", mats="old"),
        dict(oid="82C92B3A", p=(-2425, 245), eave=13.0, rise=1.6, ttop=45.7, spire=5.0, tw=6.0, style="new", mats="new"),
    ], (-2405.0, 250.0), "k93_kirche_altstetten.glb", mats_altstetten)
    build("Dreifaltigkeit", [dict(oid="756BF729", p=(457, -1185), eave=17.0, rise=6.0, ttop=32.5, spire=9.0, tw=5.8, style="old")], (457.0, -1185.0), "k93_dreifaltigkeit.glb", lambda M: mats_dreifaltigkeit(M))
