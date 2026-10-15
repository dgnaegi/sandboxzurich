"""Tiny procedural modelling kit for landmark GLBs (pure numpy, no Blender).
Model space: x east, y north, z up (metres), origin = landmark anchor at ground level.
Up to 3 materials; each has an optional colour texture and an optional emissive (night window) texture.
Geometry is written to glTF in three.js axes (x, z, -y)."""
import io, json, struct, math
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, MultiPolygon
from shapely.geometry.polygon import orient
import shapely


def hexc(h, a=255):
    h = h.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


class Mat:
    def __init__(self, name, tex=None, emis=None, rough=0.9):
        self.name, self.tex, self.emis, self.rough = name, tex, emis, rough
        self.pos, self.nrm, self.col, self.uv, self.idx = [], [], [], [], []
        self.n = 0

    def tris(self):
        return len(self.idx) // 3


class Model:
    def __init__(self, name):
        self.name = name
        self.mats = {}

    def mat(self, key, tex=None, emis=None, rough=0.9):
        if key not in self.mats:
            assert len(self.mats) < 3, "max 3 materials"
            self.mats[key] = Mat(key, tex, emis, rough)
        return self.mats[key]

    def tri_count(self):
        return sum(m.tris() for m in self.mats.values())

    # ---- primitives -------------------------------------------------
    def quad(self, m, p, uv=None, col=(255, 255, 255, 255), n=None):
        """p: 4 points CCW seen from the front."""
        p = np.array(p, float)
        if n is None:
            n = np.cross(p[1] - p[0], p[2] - p[0])
            l = np.linalg.norm(n)
            n = n / l if l > 0 else np.array([0, 0, 1.0])
        if uv is None:
            uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
        b = m.n
        for i in range(4):
            m.pos.append(p[i]); m.nrm.append(n); m.col.append(col); m.uv.append(uv[i])
        m.idx += [b, b + 1, b + 2, b, b + 2, b + 3]
        m.n += 4

    def tri(self, m, p, uv=None, col=(255, 255, 255, 255)):
        p = np.array(p, float)
        n = np.cross(p[1] - p[0], p[2] - p[0]); l = np.linalg.norm(n)
        n = n / l if l > 0 else np.array([0, 0, 1.0])
        uv = uv or [(0, 0), (1, 0), (0, 1)]
        b = m.n
        for i in range(3):
            m.pos.append(p[i]); m.nrm.append(n); m.col.append(col); m.uv.append(uv[i])
        m.idx += [b, b + 1, b + 2]
        m.n += 3

    def wall(self, m, a, b, z0, z1, mod=(3.0, 3.0), col=(255, 255, 255, 255), u0=0.0, v0=0.0, nt=(1, 1)):
        """Vertical quad from a=(x,y) to b=(x,y); facing = right-hand side of a->b (CCW ring => outward).
        mod = metres per texture repeat (u, v)."""
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-3 or z1 - z0 < 1e-3:
            return
        u1 = u0 + L / mod[0]; v1 = v0 + (z1 - z0) / mod[1]
        self.quad(m, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)],
                  [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], col)

    def flat(self, m, poly, z, col, up=True, uvscale=0.1):
        """Horizontal polygon (shapely) at height z, triangulated."""
        poly = orient(poly, 1.0)
        for g in shapely.constrained_delaunay_triangles(poly).geoms:
            c = list(g.exterior.coords)[:3]
            pts = [(x, y, z) for x, y in c]
            q = Polygon(c)
            if q.exterior.is_ccw != up:
                pts = pts[::-1]
            self.tri(m, pts, [(p[0] * uvscale, p[1] * uvscale) for p in pts], col)

    def extrude(self, mw, mr, poly, z0, z1, mod=(3.0, 3.0), col=(255, 255, 255, 255), rcol=(120, 120, 120, 255),
                roof=True, wallv0=0.0, skip=None):
        """Walls of a shapely polygon (holes allowed) from z0 to z1, flat roof in material mr.
        skip(i, a, b) -> True to omit an edge."""
        poly = orient(poly, 1.0)
        rings = [poly.exterior] + list(poly.interiors)
        k = 0
        for r in rings:
            c = list(r.coords)
            u = 0.0
            for a, b in zip(c[:-1], c[1:]):
                if not (skip and skip(k, a, b)):
                    self.wall(mw, a, b, z0, z1, mod, col, u0=u / mod[0], v0=wallv0)
                u += math.hypot(b[0] - a[0], b[1] - a[1]); k += 1
        if roof and mr is not None:
            self.flat(mr, poly, z1, rcol)

    def box(self, mw, cx, cy, w, d, z0, z1, rot=0.0, mod=(3.0, 3.0), col=(255, 255, 255, 255), mr=None, rcol=None, bottom=False):
        h = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
        cr, sr = math.cos(rot), math.sin(rot)
        pts = [(cx + x * cr - y * sr, cy + x * sr + y * cr) for x, y in h]
        self.extrude(mw, mr or mw, Polygon(pts), z0, z1, mod, col, rcol or col, roof=True)

    def cylinder(self, mw, cx, cy, r, z0, z1, n=16, mod=(3.0, 3.0), col=(255, 255, 255, 255), cap=None, capcol=None, r1=None, smooth=True, u_rep=None):
        r1 = r if r1 is None else r1
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            pa = (cx + r * math.cos(a0), cy + r * math.sin(a0)); pb = (cx + r * math.cos(a1), cy + r * math.sin(a1))
            qa = (cx + r1 * math.cos(a0), cy + r1 * math.sin(a0)); qb = (cx + r1 * math.cos(a1), cy + r1 * math.sin(a1))
            ur = u_rep or (2 * math.pi * r / mod[0])
            u0, u1 = ur * i / n, ur * (i + 1) / n
            p = [(pa[0], pa[1], z0), (pb[0], pb[1], z0), (qb[0], qb[1], z1), (qa[0], qa[1], z1)]
            nm = lambda t: np.array([math.cos(t), math.sin(t), 0.0])
            nn = [nm(a0), nm(a1), nm(a1), nm(a0)] if smooth else [nm((a0 + a1) / 2)] * 4
            b = mw.n
            for j in range(4):
                mw.pos.append(np.array(p[j], float)); mw.nrm.append(nn[j]); mw.col.append(col)
            mw.uv += [(u0, z0 / mod[1]), (u1, z0 / mod[1]), (u1, z1 / mod[1]), (u0, z1 / mod[1])]
            mw.idx += [b, b + 1, b + 2, b, b + 2, b + 3]; mw.n += 4
            if cap is not None:
                self.tri(cap, [(cx, cy, z1), (qa[0], qa[1], z1), (qb[0], qb[1], z1)], col=capcol or col)

    def hip(self, mr, pts, z, rise, col, ridge_frac=0.0):
        """Hipped roof over a convex quad pts (CCW); ridge_frac in 0..0.45: 0 = pyramid, else hip with ridge."""
        p = [np.array(q, float) for q in pts]
        c = sum(p) / 4
        if ridge_frac <= 0:
            top = [np.array([c[0], c[1], z + rise])] * 4
        else:
            e0, e1 = np.linalg.norm(p[1] - p[0]), np.linalg.norm(p[2] - p[1])
            if e0 >= e1:  # ridge parallel to p0->p1
                d = (p[1] - p[0]) / e0; s = e0 * ridge_frac
                top = [c - d * (e0 / 2 - s), c + d * (e0 / 2 - s)]
                T = [None] * 4
                T[0] = np.array([*(c - d * (e0 / 2 - s)), z + rise]); T[1] = np.array([*(c + d * (e0 / 2 - s)), z + rise])
                T[2] = T[1]; T[3] = T[0]
                top = T
            else:
                d = (p[2] - p[1]) / e1; s_ = e1 * ridge_frac
                a_ = np.array([*(c - d * (e1 / 2 - s_)), z + rise]); b_ = np.array([*(c + d * (e1 / 2 - s_)), z + rise])
                top = [a_, a_, b_, b_]
        P = [np.array([q[0], q[1], z]) for q in p]
        for i in range(4):
            j = (i + 1) % 4
            t0, t1 = top[i], top[j]
            if np.allclose(t0, t1):
                self.tri(mr, [P[i], P[j], t0], col=col)
            else:
                self.quad(mr, [P[i], P[j], t1, t0], col=col)

    # ---- output ------------------------------------------------------
    def write(self, path):
        bin_ = bytearray(); views = []; accs = []; imgs = []; texs = []; mats = []; prims = []

        def view(data, target=None):
            while len(bin_) % 4: bin_.append(0)
            d = {"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data)}
            if target: d["target"] = target
            views.append(d); bin_.extend(data); return len(views) - 1

        def acc(arr, comp, typ, target, norm=False, mm=False):
            v = view(arr.tobytes(), target)
            a = {"bufferView": v, "componentType": comp, "count": len(arr), "type": typ}
            if norm: a["normalized"] = True
            if mm: a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
            accs.append(a); return len(accs) - 1

        def image(im):
            b = io.BytesIO(); im.save(b, "PNG", optimize=True)
            imgs.append({"bufferView": view(b.getvalue()), "mimeType": "image/png"})
            texs.append({"source": len(imgs) - 1, "sampler": 0}); return len(texs) - 1

        for key, m in self.mats.items():
            if m.n == 0: continue
            pos = np.array(m.pos, np.float32); nrm = np.array(m.nrm, np.float32)
            pos = np.column_stack([pos[:, 0], pos[:, 2], -pos[:, 1]]); nrm = np.column_stack([nrm[:, 0], nrm[:, 2], -nrm[:, 1]])
            idx = np.array(m.idx, np.uint32)
            uv = np.array(m.uv, np.float32); uv[:, 1] = -uv[:, 1]  # glTF v points down
            attrs = {"POSITION": acc(pos, 5126, "VEC3", 34962, mm=True), "NORMAL": acc(nrm, 5126, "VEC3", 34962),
                     "COLOR_0": acc(np.array(m.col, np.uint8), 5121, "VEC4", 34962, norm=True),
                     "TEXCOORD_0": acc(uv, 5126, "VEC2", 34962)}
            ia = acc(idx, 5125, "SCALAR", 34963)
            pbr = {"metallicFactor": 0.0, "roughnessFactor": m.rough}
            gm = {"name": m.name, "pbrMetallicRoughness": pbr, "doubleSided": False}
            if m.tex is not None: pbr["baseColorTexture"] = {"index": image(m.tex)}
            if m.emis is not None:
                gm["emissiveTexture"] = {"index": image(m.emis)}; gm["emissiveFactor"] = [1, 1, 1]
            mats.append(gm)
            prims.append({"attributes": attrs, "indices": ia, "material": len(mats) - 1})
        gltf = {"asset": {"version": "2.0", "generator": "gtazurich-landmarks"}, "scene": 0, "scenes": [{"nodes": [0]}],
                "nodes": [{"name": self.name, "mesh": 0}], "meshes": [{"name": self.name, "primitives": prims}],
                "materials": mats, "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(bin_)}],
                "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]}
        if imgs: gltf["images"] = imgs; gltf["textures"] = texs
        js = json.dumps(gltf, separators=(",", ":")).encode(); js += b" " * (-len(js) % 4)
        bin_.extend(b"\0" * (-len(bin_) % 4))
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
            f.write(struct.pack("<II", len(bin_), 0x004E4942) + bytes(bin_))


# ---- textures -----------------------------------------------------------
def tile(nx, ny, mw, mh, painter, seed=1, lit=0.35):
    """Texture of nx*ny modules (mw x mh px each). painter(d, de, x, y, w, h, rng, on, ix, iy): draws onto base d and emissive de.
    Returns (base RGBA image, emissive RGB image)."""
    rng = np.random.default_rng(seed)
    base = Image.new("RGBA", (nx * mw, ny * mh), (255, 255, 255, 255)); em = Image.new("RGB", base.size, (0, 0, 0))
    d, de = ImageDraw.Draw(base), ImageDraw.Draw(em)
    for iy in range(ny):
        for ix in range(nx):
            painter(d, de, ix * mw, iy * mh, mw, mh, rng, rng.random() < lit, ix, iy)
    return base, em


def solid(color, size=8):
    return Image.new("RGBA", (size, size), color)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


def noise_overlay(im, amp=10, seed=5):
    a = np.asarray(im.convert("RGBA")).astype(np.int16)
    r = np.random.default_rng(seed).integers(-amp, amp + 1, a.shape[:2])[..., None]
    a[..., :3] += r
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def stack(*tiles):
    """Vertically stack (base, emissive) tiles of equal width -> (base, emissive), first = top of the image."""
    W = max(t[0].width for t in tiles); H = sum(t[0].height for t in tiles)
    b = Image.new("RGBA", (W, H)); e = Image.new("RGB", (W, H)); y = 0
    for tb, te in tiles:
        b.paste(tb, (0, y)); e.paste(te, (0, y)); y += tb.height
    return b, e


def _scaled(poly, s, cx, cy):
    from shapely.affinity import scale
    return scale(poly, s, s, origin=(cx, cy))


def taper(m, mr, poly, z0, z1, s, col, cap=True, center=None, mw_uv=None):
    """Sloped roof band: ring of `poly` at z0 -> ring of poly scaled by s about the centroid at z1 (same vertex order).
    Quad per edge, optional flat cap. For roughly star-shaped footprints (hips, mansards, spires)."""
    poly = orient(poly, 1.0)
    c = center or (poly.centroid.x, poly.centroid.y)
    q = orient(_scaled(poly, s, *c), 1.0)
    A = list(poly.exterior.coords)[:-1]; B = list(q.exterior.coords)[:-1]
    for i in range(len(A)):
        j = (i + 1) % len(A)
        P = [(A[i][0], A[i][1], z0), (A[j][0], A[j][1], z0), (B[j][0], B[j][1], z1), (B[i][0], B[i][1], z1)]
        if np.allclose(P[2], P[3]): m.tri(mr, P[:3], col=col)
        else: m.quad(mr, P, col=col)
    if cap and s > 0.02:
        m.flat(mr, q, z1, col)
    return q


def rect_of(poly, grow=0.0):
    """Minimum rotated rectangle as (centre, ux, uy, length, width) with the long axis first."""
    r = poly.minimum_rotated_rectangle; c = list(r.exterior.coords)[:4]
    e0 = (c[1][0] - c[0][0], c[1][1] - c[0][1]); e1 = (c[2][0] - c[1][0], c[2][1] - c[1][1])
    L0, L1 = math.hypot(*e0), math.hypot(*e1)
    if L0 >= L1: ux, uy, L, W = e0[0] / L0, e0[1] / L0, L0, L1
    else: ux, uy, L, W = e1[0] / L1, e1[1] / L1, L1, L0
    return (r.centroid.x, r.centroid.y), ux, uy, L + grow, W + grow


def gable_roof(m, mr, mw, rect, z, rise, col, gcol, eave=0.4, ridge_h_uv=None):
    """Gable roof over rect (centre, ux, uy, L, W): ridge along the long axis; gable triangles in material mw (uv 0..1)."""
    (cx, cy), ux, uy, L, W = rect
    vx, vy = -uy, ux
    hl, hw = L / 2 + eave, W / 2 + eave
    P = lambda a, b, zz: (cx + ux * a + vx * b, cy + uy * a + vy * b, zz)
    # two slopes (ccw seen from above/outside)
    m.quad(mr, [P(-hl, -hw, z), P(hl, -hw, z), P(hl, 0, z + rise), P(-hl, 0, z + rise)], col=col)
    m.quad(mr, [P(hl, hw, z), P(-hl, hw, z), P(-hl, 0, z + rise), P(hl, 0, z + rise)], col=col)
    # gable ends
    for s in (-1, 1):
        a = P(s * (L / 2), -W / 2, z); b = P(s * (L / 2), W / 2, z); t = P(s * (L / 2), 0, z + rise * (W / 2 / hw))
        pts = [a, b, t] if s > 0 else [b, a, t]
        m.tri(mw, pts, [(0, 0), (1, 0), (0.5, 0.35)], col=gcol)


def walls_by_edge(m, poly, z0, z1, chooser, floors=1):
    """Per-edge wall material: chooser(a, b, L) -> (mat, (mod_u, mod_v), colour, v0) ; floors>1 splits z0..z1 into equal floors (each repeating the texture)."""
    poly = orient(poly, 1.0)
    for ring in [poly.exterior] + list(poly.interiors):
        c = list(ring.coords)
        for a, b in zip(c[:-1], c[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 0.05: continue
            mat, mod, col, v0 = chooser(a, b, L)
            fh = (z1 - z0) / floors
            for k in range(floors):
                m.wall(mat, a, b, z0 + k * fh, z0 + (k + 1) * fh, mod, col, u0=0.0, v0=v0)
