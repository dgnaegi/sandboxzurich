"""Bahnhof Wiedikon (Reiterbahnhof 1927, H. Herter) + Loewenbrunnen Schmiede Wiedikon.
-> k93_wiedikon.glb, k93_schmiede.glb"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import k93_lib as L, k93_find as F, terrain
from k93_lib import hexc, shade
OUTD = F.ROOT + "/web/public/models/landmarks/"
WHITE = (255, 255, 255, 255)

def bay_tex():
    im = Image.new("RGB", (64, 64), (205, 198, 178)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 63, 5], fill=(190, 183, 163))
    d.rectangle([18, 22, 46, 60], fill=(54, 62, 74)); d.ellipse([18, 10, 46, 34], fill=(54, 62, 74))
    d.rectangle([14, 60, 50, 63], fill=(170, 164, 146)); d.line([32, 10, 32, 60], fill=(190, 186, 170), width=2)
    return im

def sign_tex():
    im = Image.new("RGB", (512, 64), (214, 208, 190)); d = ImageDraw.Draw(im)
    try: f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 46)
    except Exception: f = ImageFont.load_default()
    w = d.textlength("WIEDIKON", font=f); d.text(((512 - w) / 2, 6), "WIEDIKON", font=f, fill=(32, 92, 196))
    return im

def station():
    oid, p = "BE5BEAB6", (544, -1403)
    o = [o for o in F.near(*p, 30) if o["id"][3:11] == oid][0]; fp = F.footprint(o).simplify(0.4)
    c = np.array(fp.centroid.coords[0]); H = terrain.heights((c[0] - 60, c[1] - 60, c[0] + 60, c[1] + 60), 2.0, z_shift=-3.06)
    z0 = float(H.at(*c)); M = L.Model(origin=(c[0], c[1], 0.0))
    mw = M.mat("walls", rough=0.95, tex=bay_tex(), repeat=True); ms = M.mat("sign", rough=0.6, tex=sign_tex(), repeat=False); mr = M.mat("roof", rough=0.85)
    r = list(fp.minimum_rotated_rectangle.exterior.coords)[:4]; e1 = np.subtract(r[1], r[0]); e2 = np.subtract(r[2], r[1])
    if np.hypot(*e1) < np.hypot(*e2): e1, e2 = e2, e1
    Lg, Sh = np.hypot(*e1), np.hypot(*e2); u = e1 / Lg; ang = math.atan2(u[1], u[0]); n = np.array([-u[1], u[0]])
    if np.dot(n, np.array([500, -1360]) - c) < 0: n = -n
    eave = 12.6
    up = np.array([math.cos(math.radians(-135.3)), math.sin(math.radians(-135.3))])
    if np.dot(u, up) < 0: u = -u; n = -n; ang = math.atan2(u[1], u[0])
    if np.dot(n, np.array([500, -1360]) - c) < 0: n = -n  # n -> NW (open cutting side)
    from shapely.geometry import Polygon as _P, box as _box
    from shapely import affinity
    S0, S1, ZB, ZR = -3.0, 15.0, -1.5, -7.8   # opening across the cutting (s along u), bridge soffit, rail level (rel. to street)
    w2l = lambda pts: [(float(np.dot(np.array(p) - c, u)), float(np.dot(np.array(p) - c, n))) for p in pts]
    l2w = lambda pts: [tuple(c + u * s_ + n * k_) for s_, k_ in pts]
    fl = _P(w2l(fp.exterior.coords))
    for lo, hi, base in ((-99, S0, -9.0), (S0, S1, ZB), (S1, 99, -9.0)):
        part = fl.intersection(_box(lo, -99, hi, 99))
        for g in ([part] if part.geom_type == "Polygon" else list(getattr(part, "geoms", []))):
            if g.area < 1: continue
            pts = l2w(list(g.exterior.coords)[:-1])
            M.prism(mw, pts, base, eave, WHITE, tile=(3.4, 4.2), top=False)
            if base == ZB: M.cap(mr, pts, ZB, hexc("#4a4c4e"), flip=True)   # soffit of the bridge
    # cutting retaining walls and portal wing walls (stone), open towards the north-west
    for sw in (S0, S1):
        for k0, k1 in ((-11.5, -26.0),):
            a_ = c + u * sw + n * k0; b_ = c + u * sw + n * k1; m_ = (a_ + b_) / 2
            M.box(mr, (m_[0], m_[1], (ZR + 0.6) / 2), (0.7, abs(k1 - k0), 0.6 - ZR), hexc("#8d877a"), rot=ang + math.pi / 2)
            M.box(mr, (m_[0], m_[1], 0.9), (1.0, abs(k1 - k0), 0.35), hexc("#a7a291"), rot=ang + math.pi / 2)
    # platform edge and ballast floor strip (rails come from railways.py)
    M.gable(mr, tuple(c), Lg, Sh, eave, 7.0, hexc("#5a5f64"), rot=ang, eave=0.8, hip=1.0)
    for k in (-1, 0, 1):
        q = c + u * (k * 8 - 0.0) + n * (-(Sh / 2 - 3) if k % 2 == 0 else (Sh / 2 - 3))
        M.box(mr, (q[0], q[1], eave + 2.2), (2.2, 2.2, 2.4), hexc("#c9c2ad"), rot=ang)
        M.gable(mr, tuple(q), 2.6, 2.6, eave + 3.4, 1.2, hexc("#5a5f64"), rot=ang + math.pi / 2)
    # string course + arch portals on the wings, sign and clock above the bridge opening on both long faces
    for sg, face in ((-1, 11.5), (1, 10.5)):
        for sc_, wd in ((-9.5, 5.0),):
            q = c + u * sc_ + n * sg * (face + 0.35)
            M.box(mr, (q[0], q[1], 3.0), (wd, 0.7, 6.0), hexc("#bdb7a2"), rot=ang)
            M.box(mr, (*(c + u * sc_ + n * sg * (face + 0.75)), 2.4), (3.2, 0.2, 4.6), hexc("#232831"), rot=ang)
        sc2 = c + u * 6.0 + n * sg * (face + 0.1)
        a = sc2 - u * 5.0; b = sc2 + u * 5.0; za, zb_ = 6.2, 7.6
        if sg > 0: a, b = b, a
        M.quad(ms, (*a, za), (*b, za), (*b, zb_), (*a, zb_), WHITE, [(0, 1), (1, 1), (1, 0), (0, 0)])
        q = c + u * 6.0 + n * sg * (face + 0.15)
        M.box(mr, (q[0], q[1], 9.8), (2.4, 0.25, 2.4), hexc("#f2eee0"), rot=ang)
        M.box(mr, (*(q + n * sg * 0.16), 9.8), (0.12, 0.08, 1.0), hexc("#20242a"), rot=ang)
    return M, c, z0

def fountain():
    x, y = 314.2, -1561.5
    H = terrain.heights((x - 30, y - 30, x + 30, y + 30), 2.0, z_shift=-3.06); z0 = float(H.at(x, y))
    M = L.Model(origin=(x, y, 0.0)); m = M.mat("stone", rough=0.9)
    G = hexc("#9d9b95"); W_ = hexc("#6fa3b8")
    M.cyl(m, (x, y), 2.5, 0, 0.95, G, n=20); M.cyl(m, (x, y), 2.1, 0.7, 0.72, W_, n=20)
    M.cyl(m, (x, y), 0.55, 0.7, 3.0, shade(G, 1.05), n=10); M.cyl(m, (x, y), 0.8, 3.0, 3.3, G, n=10)
    # stylised lion: body, head, mane, tail
    LC = hexc("#8a8678")
    M.box(m, (x, y, 3.85), (1.5, 0.55, 0.6), LC); M.box(m, (x + 0.85, y, 4.2), (0.45, 0.5, 0.45), LC)
    M.dome(m, (x + 0.85, y), 0.42, 4.0, shade(LC, 0.85), n=8, rings=2); M.box(m, (x - 0.85, y, 3.8), (0.5, 0.12, 0.12), LC, rot=0.2)
    for sx in (-0.5, 0.5): 
        for sy in (-0.2, 0.2): M.box(m, (x + sx, y + sy, 3.5), (0.16, 0.16, 0.5), LC)
    return M

if __name__ == "__main__":
    M, c, z0 = station(); M.write(OUTD + "k93_wiedikon.glb"); print("wiedikon tris", M.tris(), "origin", c.round(1).tolist(), round(z0, 2))
    Mf = fountain(); Mf.write(OUTD + "k93_schmiede.glb"); print("schmiede tris", Mf.tris())
