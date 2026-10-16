"""Kit for the Zuerich HB models (hb_*.py). Modelling frame: x = d (along the tracks toward the head end, i.e. ESE), y = c (across, NNE), z up,
origin ORG at ground level; the entries are registered with heading -21 deg so the model frame lines up with the real building axes.
All heights are metres above the local terrain (swissBUILDINGS3D z + 2.9).
Textures are painted procedurally (no photos, no SBB logos). Registers into pipeline/overrides/landmarks_hb.json."""
import math, json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import common
from common import *
from lm import *
import detail as D
from shapely.geometry import Polygon, Point, box as sbox
from shapely.geometry.polygon import orient

common.OVR = ROOT / "pipeline" / "overrides" / "landmarks_hb.json"
FONTS = str(ROOT / "web" / "public" / "fonts") + "/"
ORG = (1760.0, -650.0)
ANG = -21.0
GZ = -2.9            # terrain height at ORG (model z=0)
W = (255, 255, 255, 255)
hx = D.hexl


def to_world(d, c):
    a = math.radians(ANG)
    return ORG[0] + d * math.cos(a) - c * math.sin(a), ORG[1] + d * math.sin(a) + c * math.cos(a)


def from_world(x, y):
    a = math.radians(ANG); dx, dy = x - ORG[0], y - ORG[1]
    return dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)


def font(name, size):
    return ImageFont.truetype(FONTS + name + ".ttf", size)


# ------------------------------------------------------------------ primitives (model frame)
def q(m, mat, pts, col=W, uv=None, up=None):
    """Quad; `up` = desired normal (flips the winding if needed)."""
    p = np.array(pts, float); n = np.cross(p[1] - p[0], p[2] - p[0])
    if up is not None and np.dot(n, up) < 0: pts = pts[::-1]; uv = uv[::-1] if uv else None
    m.quad(mat, pts, uv, col)


def tri(m, mat, pts, col=W, uv=None, up=None):
    p = np.array(pts, float); n = np.cross(p[1] - p[0], p[2] - p[0])
    if up is not None and np.dot(n, up) < 0: pts = pts[::-1]; uv = uv[::-1] if uv else None
    m.tri(mat, pts, uv, col)


def slab(m, mat, d0, d1, c0, c1, z, col, up=True, uvs=0.0):
    """Horizontal rectangle (facing up or down)."""
    uv = [(d0 * uvs, c0 * uvs), (d1 * uvs, c0 * uvs), (d1 * uvs, c1 * uvs), (d0 * uvs, c1 * uvs)] if uvs else None
    q(m, mat, [(d0, c0, z), (d1, c0, z), (d1, c1, z), (d0, c1, z)], col, uv, (0, 0, 1 if up else -1))


def bx(m, mat, d0, d1, c0, c1, z0, z1, col, top=True, bottom=False, mod=None, colt=None, sides=(1, 1, 1, 1)):
    """Axis-aligned box in the model frame. mod=(mu,mv): texture repeat in metres."""
    def uvq(w, h): return [(0, 0), (w / mod[0], 0), (w / mod[0], h / mod[1]), (0, h / mod[1])] if mod else None
    h = z1 - z0
    if sides[0]: q(m, mat, [(d0, c0, z0), (d1, c0, z0), (d1, c0, z1), (d0, c0, z1)], col, uvq(d1 - d0, h), (0, -1, 0))
    if sides[1]: q(m, mat, [(d1, c0, z0), (d1, c1, z0), (d1, c1, z1), (d1, c0, z1)], col, uvq(c1 - c0, h), (1, 0, 0))
    if sides[2]: q(m, mat, [(d1, c1, z0), (d0, c1, z0), (d0, c1, z1), (d1, c1, z1)], col, uvq(d1 - d0, h), (0, 1, 0))
    if sides[3]: q(m, mat, [(d0, c1, z0), (d0, c0, z0), (d0, c0, z1), (d0, c1, z1)], col, uvq(c1 - c0, h), (-1, 0, 0))
    if top: slab(m, mat, d0, d1, c0, c1, z1, colt or col, True)
    if bottom: slab(m, mat, d0, d1, c0, c1, z0, col, False)


def wall(m, mat, a, b, z0, z1, col=W, mod=(4.0, 4.0), double=False, v0=0.0):
    """Vertical wall a->b ((d,c) points), facing = right-hand side. double=True adds the back face."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L < 1e-3 or z1 - z0 < 1e-3: return
    uv = [(0, v0), (L / mod[0], v0), (L / mod[0], v0 + (z1 - z0) / mod[1]), (0, v0 + (z1 - z0) / mod[1])]
    m.quad(mat, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], uv, col)
    if double:
        m.quad(mat, [(b[0], b[1], z0), (a[0], a[1], z0), (a[0], a[1], z1), (b[0], b[1], z1)], uv[::-1], col)


def column(m, mat, d, c, r, z0, z1, col, n=8):
    m.cylinder(mat, d, c, r, z0, z1, n=n, col=col, mod=(4, 4))


def barrel(m, mat, axis, a0, a1, mid, hw, zs, rise, col, n=10, inside=True, outside=True, thick=0.0, colin=None, mod=(4, 4)):
    """Circular-segment barrel vault. axis 'd': runs along d from a0 to a1, cross-section centred on c=mid, half width hw, spring height zs, rise.
    axis 'c': runs along c, centred on d=mid. Outer surface facing out, inner surface facing in."""
    R = (hw * hw + rise * rise) / (2 * rise); zc = zs + rise - R
    prof = []
    for i in range(n + 1):
        x = -hw + 2 * hw * i / n; prof.append((x, zc + math.sqrt(max(R * R - x * x, 0))))
    colin = colin or col
    for i in range(n):
        (x0, h0), (x1, h1) = prof[i], prof[i + 1]
        if axis == 'd': P = lambda a, x, h: (a, mid + x, h)
        else: P = lambda a, x, h: (mid + x, a, h)
        pts = [P(a0, x0, h0), P(a1, x0, h0), P(a1, x1, h1), P(a0, x1, h1)]
        L = a1 - a0; ws = math.hypot(x1 - x0, h1 - h0)
        uv = [(0, i * ws / mod[1]), (L / mod[0], i * ws / mod[1]), (L / mod[0], (i + 1) * ws / mod[1]), (0, (i + 1) * ws / mod[1])]
        out_n = (0, (x0 + x1) / 2, 1) if axis == 'd' else ((x0 + x1) / 2, 0, 1)
        if outside: q(m, mat, pts, col, uv, out_n)
        if inside: q(m, mat, pts, colin, uv, tuple(-v for v in out_n))
    return prof


def cap_arch(m, mat, axis, a, mid, hw, zs, rise, col, n=10, face=1, z0=None):
    """Gable (arch-segment) infill at position a, from z0 (default spring) up to the arch, facing +/- along the run axis."""
    R = (hw * hw + rise * rise) / (2 * rise); zc = zs + rise - R
    z0 = zs if z0 is None else z0
    for i in range(n):
        x0, x1 = -hw + 2 * hw * i / n, -hw + 2 * hw * (i + 1) / n
        h0 = zc + math.sqrt(max(R * R - x0 * x0, 0)); h1 = zc + math.sqrt(max(R * R - x1 * x1, 0))
        if axis == 'd': pts = [(a, mid + x0, z0), (a, mid + x1, z0), (a, mid + x1, h1), (a, mid + x0, h0)]; nn = (face, 0, 0)
        else: pts = [(mid + x0, a, z0), (mid + x1, a, z0), (mid + x1, a, h1), (mid + x0, a, h0)]; nn = (0, face, 0)
        q(m, mat, pts, col, None, nn)


# ------------------------------------------------------------------ sign atlas (neutral lettering, no logos)
class SignAtlas:
    """Shelf-packed painted atlas (RGBA + emissive). add() returns the uv rect (u0, v0, u1, v1) with v pointing UP the image like lm.py expects."""
    def __init__(self, W_=2048, H_=1024):
        self.W, self.H = W_, H_
        self.base = Image.new("RGBA", (W_, H_), (40, 40, 44, 255)); self.em = Image.new("RGB", (W_, H_), (0, 0, 0))
        self.d, self.de = ImageDraw.Draw(self.base), ImageDraw.Draw(self.em)
        self.x = self.y = self.rowh = 0; self.rects = {}

    def add(self, name, w, h, painter):
        if self.x + w > self.W: self.x = 0; self.y += self.rowh + 2; self.rowh = 0
        assert self.y + h <= self.H, "sign atlas full"
        painter(self.d, self.de, self.x, self.y, w, h)
        r = (self.x / self.W, 1 - (self.y + h) / self.H, (self.x + w) / self.W, 1 - self.y / self.H)
        self.rects[name] = r; self.x += w + 2; self.rowh = max(self.rowh, h); return r

    def add_scaled(self, name, w, h, painter, w0, h0):
        """Paint at (w0, h0) on scratch images, then resize into the atlas cell (smaller texture for phones, same layout code)."""
        b0 = Image.new("RGBA", (w0, h0), (0, 0, 0, 255)); e0 = Image.new("RGB", (w0, h0), (0, 0, 0))
        painter(ImageDraw.Draw(b0), ImageDraw.Draw(e0), 0, 0, w0, h0)
        return self.add(name, w, h, lambda d, de, x, y, ww, hh: (self.base.paste(b0.resize((w, h), Image.LANCZOS), (x, y)), self.em.paste(e0.resize((w, h), Image.LANCZOS), (x, y))))

    def images(self): return self.base, self.em


def sign_text(text, fg, bg, glow=None, fnt="Barlow-Bold", size=40, anchor="mm", pad=0.0, frame=None):
    def paint(d, de, x, y, w, h):
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=hexc(bg))
        if frame: d.rectangle([x, y, x + w - 1, y + h - 1], outline=hexc(frame), width=3)
        f = font(fnt, size)
        d.text((x + w / 2, y + h / 2), text, font=f, fill=hexc(fg), anchor=anchor)
        if glow: de.text((x + w / 2, y + h / 2), text, font=f, fill=glow, anchor=anchor)
    return paint


def uvr(r, flip=False):
    u0, v0, u1, v1 = r
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def sign_q(m, mat, p0, p1, z0, z1, rect, col=W, nrm=None):
    """Textured sign quad from (d,c) p0 to p1 between z0 and z1 (facing = right of p0->p1), uv = atlas rect."""
    m.quad(mat, [(p0[0], p0[1], z0), (p1[0], p1[1], z0), (p1[0], p1[1], z1), (p0[0], p0[1], z1)], uvr(rect), col)


def info(m, name):
    print(name, m.tri_count(), "tris;", ", ".join(f"{k}={v.tris()}" for k, v in m.mats.items()))


# ------------------------------------------------------------------ registration with colliders / walkable flag
def register(m, name, title, hide, hide_ids=(), walkable=False, colliders=None, load_r=None, z=GZ, extra=None):
    """Write GLB (gltfpack) and register in landmarks_hb.json. colliders: list of rings [[x, y], ...] in LOCAL METRES (world)."""
    OUTDIR.mkdir(parents=True, exist_ok=True); RAWDIR.mkdir(parents=True, exist_ok=True)
    raw = RAWDIR / f"{name}.glb"; m.write(str(raw)); out = OUTDIR / f"{name}.glb"
    r = common._sp.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(out), "-cc", "-kn"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:])
    print(f"{name}: {m.tri_count()} tris, " + ", ".join(f"{k}={mm.tris()}" for k, mm in m.mats.items()) + f", glb {out.stat().st_size // 1024} kB")
    d = json.load(open(common.OVR)) if common.OVR.exists() else {"landmarks": []}
    d["landmarks"] = [e for e in d["landmarks"] if e["name"] != title]
    e = {"name": title, "model": f"/models/landmarks/{name}.glb", "x": ORG[0], "y": ORG[1], "z": z, "heading": math.radians(ANG), "hide": hide}
    if hide_ids: e["hide_ids"] = list(hide_ids)
    if walkable: e["walkable"] = True
    if colliders is not None: e["colliders"] = colliders
    if load_r: e["load_r"] = load_r
    if extra: e.update(extra)
    d["landmarks"].append(e)
    json.dump(d, open(common.OVR, "w"), indent=1)
    import merge; merge.main()


def ring_world(pts_dc):
    """[(d,c), ...] -> [[x, y], ...] local metres, rounded."""
    return [[round(v, 2) for v in to_world(d, c)] for d, c in pts_dc]


def rect_ring(d0, d1, c0, c1):
    return ring_world([(d0, c0), (d1, c0), (d1, c1), (d0, c1)])
