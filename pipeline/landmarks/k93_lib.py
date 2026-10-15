"""Tiny mesh builder + GLB writer for the Kreis 9/3 landmark models.
Build in local metres (x east, y north, z up) relative to a model origin; export converts to three axes
(x, z, -y). Flat-shaded quads with vertex colours; optional texture per material (uv, clamp or repeat)."""
import io, json, struct, math
import numpy as np

UP = np.array([0.0, 0.0, 1.0])


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def shade(c, f):
    return (int(min(255, c[0] * f)), int(min(255, c[1] * f)), int(min(255, c[2] * f)), c[3] if len(c) > 3 else 255)


class Mat:
    def __init__(self, name, rough=0.9, metal=0.0, tex=None, repeat=True, base=(1, 1, 1, 1), emissive=None, double=False, emis=None):
        self.name, self.rough, self.metal, self.tex, self.repeat, self.base = name, rough, metal, tex, repeat, base
        self.emissive, self.double, self.emis = emissive, double, emis
        self.pos, self.nrm, self.col, self.uv, self.idx = [], [], [], [], []
        self.n = 0


class Model:
    def __init__(self, origin=(0.0, 0.0, 0.0)):
        self.ox, self.oy, self.oz = origin
        self.mats = []

    def mat(self, *a, **k):
        m = Mat(*a, **k); self.mats.append(m); return m

    # ---- primitives -------------------------------------------------------------------------------------------
    def quad(self, m, p0, p1, p2, p3, col, uv=None, flip=False):
        p = np.array([p0, p1, p2, p3], float)
        n = np.cross(p[1] - p[0], p[3] - p[0])
        if np.linalg.norm(n) < 1e-9: n = np.cross(p[2] - p[0], p[3] - p[0])
        l = np.linalg.norm(n)
        if l < 1e-9: return
        n = n / l
        if flip: n = -n
        c = col if isinstance(col[0], (int, float)) else col
        m.pos.extend(p.tolist()); m.nrm.extend([n.tolist()] * 4); m.col.extend([c] * 4)
        m.uv.extend(uv if uv is not None else [(0, 0), (1, 0), (1, 1), (0, 1)])
        b = m.n
        m.idx.extend([b, b + 1, b + 2, b, b + 2, b + 3] if not flip else [b, b + 2, b + 1, b, b + 3, b + 2])
        m.n += 4

    def tri(self, m, p0, p1, p2, col, uv=None):
        p = np.array([p0, p1, p2], float)
        n = np.cross(p[1] - p[0], p[2] - p[0]); l = np.linalg.norm(n)
        if l < 1e-9: return
        n = n / l
        m.pos.extend(p.tolist()); m.nrm.extend([n.tolist()] * 3); m.col.extend([col] * 3)
        m.uv.extend(uv if uv is not None else [(0, 0), (1, 0), (0, 1)])
        m.idx.extend([m.n, m.n + 1, m.n + 2]); m.n += 3

    def box(self, m, c, s, col, rot=0.0, top=None, uvs=None, bottom=False):
        """Box centred at c=(x,y,zc), size s=(sx,sy,sz), yaw rot (rad). Optional different top colour."""
        cx, cy, cz = c; sx, sy, sz = s[0] / 2, s[1] / 2, s[2] / 2
        co, si = math.cos(rot), math.sin(rot)

        def P(dx, dy, dz): return (cx + dx * co - dy * si, cy + dx * si + dy * co, cz + dz)
        a, b, cc, d = P(-sx, -sy, -sz), P(sx, -sy, -sz), P(sx, sy, -sz), P(-sx, sy, -sz)
        e, f, g, h = P(-sx, -sy, sz), P(sx, -sy, sz), P(sx, sy, sz), P(-sx, sy, sz)
        u = lambda w, hh: [(0, 0), (w, 0), (w, hh), (0, hh)]
        self.quad(m, a, b, f, e, shade(col, .88), u(s[0], s[2]) if uvs else None)
        self.quad(m, b, cc, g, f, shade(col, .78), u(s[1], s[2]) if uvs else None)
        self.quad(m, cc, d, h, g, shade(col, .88), u(s[0], s[2]) if uvs else None)
        self.quad(m, d, a, e, h, shade(col, .78), u(s[1], s[2]) if uvs else None)
        self.quad(m, e, f, g, h, top or col, u(s[0], s[1]) if uvs else None)
        if bottom: self.quad(m, d, cc, b, a, shade(col, .6))

    def prism(self, m, poly, z0, z1, col, topcol=None, uvs=True, tile=(4.0, 3.0), top=True, shade_sides=True):
        """Extrude xy polygon (any winding) z0->z1. Walls get uv (len/tile.x, height/tile.y)."""
        pts = [tuple(p[:2]) for p in poly]
        if pts[0] == pts[-1]: pts = pts[:-1]
        if signed_area(pts) < 0: pts = pts[::-1]
        L = 0.0
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            d = math.hypot(b[0] - a[0], b[1] - a[1])
            nx = (b[1] - a[1]) / (d or 1)
            f = 1.0 if not shade_sides else 0.8 + 0.2 * abs(nx)
            self.quad(m, (*a, z0), (*b, z0), (*b, z1), (*a, z1), shade(col, f),
                      [(L / tile[0], 0.0), ((L + d) / tile[0], 0.0), ((L + d) / tile[0], (z1 - z0) / tile[1]), (L / tile[0], (z1 - z0) / tile[1])])
            L += d
        if top: self.cap(m, pts, z1, topcol or col)

    def cap(self, m, pts, z, col, flip=False):
        """Horizontal polygon face by ear clipping (handles concave)."""
        pts = list(pts)
        if signed_area(pts) < 0: pts = pts[::-1]
        for t in triangulate(pts):
            a, b, c = [pts[i] for i in t]
            if flip: b, c = c, b
            self.tri(m, (*a, z), (*b, z), (*c, z), col, [(a[0], a[1]), (b[0], b[1]), (c[0], c[1])])

    def gable(self, m, c, w, d, z0, rise, col, rot=0.0, ridge_len=None, hip=0.0, eave=0.0, gablecol=None):
        """Gable (hip=0) or hip roof over a w x d rectangle (ridge along local x). z0=eave height."""
        cx, cy = c; co, si = math.cos(rot), math.sin(rot)
        hw, hd = w / 2 + eave, d / 2 + eave
        def P(x, y, z): return (cx + x * co - y * si, cy + x * si + y * co, z)
        rl = hw - hip * (hd)  # ridge half length
        rl = max(0.0, rl)
        zt = z0 + rise
        A, B, C, D = P(-hw, -hd, z0), P(hw, -hd, z0), P(hw, hd, z0), P(-hw, hd, z0)
        R1, R2 = P(-rl, 0, zt), P(rl, 0, zt)
        self.quad(m, A, B, R2, R1, shade(col, 1.0))
        self.quad(m, C, D, R1, R2, shade(col, .82))
        gc = gablecol or col
        if rl < hw - 1e-6:
            self.tri(m, B, C, R2, shade(col, .9)); self.tri(m, D, A, R1, shade(col, .9))
        else:
            self.tri(m, B, C, R2, shade(gc, .95)); self.tri(m, D, A, R1, shade(gc, .95))

    def cyl(self, m, c, r, z0, z1, col, n=12, r1=None, cap=True, tile=(4, 3), smooth=False):
        r1 = r if r1 is None else r1
        cx, cy = c
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0)); p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
            q0 = (cx + r1 * math.cos(a0), cy + r1 * math.sin(a0)); q1 = (cx + r1 * math.cos(a1), cy + r1 * math.sin(a1))
            f = 0.82 + 0.18 * math.cos((a0 + a1) / 2 - 0.9)
            L = r * (a1 - a0)
            self.quad(m, (*p0, z0), (*p1, z0), (*q1, z1), (*q0, z1), shade(col, f),
                      [(i * L / tile[0], z0 / tile[1]), ((i + 1) * L / tile[0], z0 / tile[1]), ((i + 1) * L / tile[0], z1 / tile[1]), (i * L / tile[0], z1 / tile[1])])
            if cap and r1 > 0.02:
                self.tri(m, (cx, cy, z1), (*q0, z1), (*q1, z1), col)  # wrong winding fixed below
        # note: tri above has CW winding for top -> flip handled in tri() by normal; ensure up
    def cone(self, m, c, r, z0, z1, col, n=12):
        cx, cy = c
        for i in range(n):
            a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            self.tri(m, (cx + r * math.cos(a0), cy + r * math.sin(a0), z0), (cx + r * math.cos(a1), cy + r * math.sin(a1), z0), (cx, cy, z1),
                     shade(col, 0.8 + 0.2 * math.cos((a0 + a1) / 2 - 0.9)))

    def dome(self, m, c, r, z0, col, n=16, rings=4, sq=1.0):
        cx, cy = c
        prev = [(r, z0)] * 1
        pr = [(r * math.cos(math.pi / 2 * k / rings), z0 + sq * r * math.sin(math.pi / 2 * k / rings)) for k in range(rings + 1)]
        for k in range(rings):
            r0, h0 = pr[k]; r1_, h1 = pr[k + 1]
            for i in range(n):
                a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
                p = lambda rr, a, h: (cx + rr * math.cos(a), cy + rr * math.sin(a), h)
                f = 0.8 + 0.2 * math.cos((a0 + a1) / 2 - 0.9) * (1 - k / rings * 0.5)
                if k == rings - 1:
                    self.tri(m, p(r0, a0, h0), p(r0, a1, h0), p(0, 0, h1), shade(col, f))
                else:
                    self.quad(m, p(r0, a0, h0), p(r0, a1, h0), p(r1_, a1, h1), p(r1_, a0, h1), shade(col, f))

    # ---- export -----------------------------------------------------------------------------------------------
    def tris(self):
        return sum(len(m.idx) // 3 for m in self.mats)

    def write(self, path):
        bin_ = bytearray(); views, accs, meshes, nodes, mats, imgs, texs, samplers = [], [], [], [], [], [], [], []

        def add(arr, comp, typ, target, norm=False, mm=False):
            while len(bin_) % 4: bin_.append(0)
            data = arr.tobytes()
            views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data), "target": target}); bin_.extend(data)
            a = {"bufferView": len(views) - 1, "componentType": comp, "count": len(arr), "type": typ}
            if norm: a["normalized"] = True
            if mm: a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
            accs.append(a); return len(accs) - 1

        for m in self.mats:
            if not m.idx: continue
            pos = np.array(m.pos, np.float32) - np.array([self.ox, self.oy, self.oz], np.float32)
            nrm = np.array(m.nrm, np.float32)
            T = lambda a: np.column_stack([a[:, 0], a[:, 2], -a[:, 1]]).astype(np.float32)
            col = np.array([c if len(c) == 4 else (*c, 255) for c in m.col], np.uint8)
            attrs = {"POSITION": add(T(pos), 5126, "VEC3", 34962, mm=True), "NORMAL": add(T(nrm), 5126, "VEC3", 34962),
                     "COLOR_0": add(col, 5121, "VEC4", 34962, norm=True)}
            mt = {"name": m.name, "pbrMetallicRoughnessFactor": None}
            pbr = {"baseColorFactor": list(m.base), "metallicFactor": m.metal, "roughnessFactor": m.rough}
            if m.tex is not None:
                attrs["TEXCOORD_0"] = add(np.array(m.uv, np.float32), 5126, "VEC2", 34962)
                buf = io.BytesIO(); m.tex.save(buf, "PNG"); data = buf.getvalue()
                while len(bin_) % 4: bin_.append(0)
                views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data)}); bin_.extend(data)
                imgs.append({"bufferView": len(views) - 1, "mimeType": "image/png"})
                w = 10497 if m.repeat else 33071
                samplers.append({"magFilter": 9729, "minFilter": 9987, "wrapS": w, "wrapT": w})
                texs.append({"source": len(imgs) - 1, "sampler": len(samplers) - 1}); pbr["baseColorTexture"] = {"index": len(texs) - 1}
            mdef = {"name": m.name, "pbrMetallicRoughness": pbr}
            if m.emis is not None:  # night texture (runtime scales it by the night factor); needs uv
                buf = io.BytesIO(); m.emis.convert("RGB").save(buf, "PNG"); data = buf.getvalue()
                while len(bin_) % 4: bin_.append(0)
                views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data)}); bin_.extend(data)
                imgs.append({"bufferView": len(views) - 1, "mimeType": "image/png"})
                w = 10497 if m.repeat else 33071
                samplers.append({"magFilter": 9729, "minFilter": 9987, "wrapS": w, "wrapT": w})
                texs.append({"source": len(imgs) - 1, "sampler": len(samplers) - 1})
                mdef["emissiveTexture"] = {"index": len(texs) - 1}; mdef["emissiveFactor"] = [1, 1, 1]
                if "TEXCOORD_0" not in attrs: attrs["TEXCOORD_0"] = add(np.array(m.uv, np.float32), 5126, "VEC2", 34962)
            elif m.emissive: mdef["emissiveFactor"] = list(m.emissive)
            if m.double: mdef["doubleSided"] = True
            mats.append(mdef)
            ia = add(np.array(m.idx, np.uint32), 5125, "SCALAR", 34963)
            meshes.append({"name": m.name, "primitives": [{"attributes": attrs, "indices": ia, "material": len(mats) - 1}]})
        nodes = [{"name": "landmark", "children": list(range(1, 1 + len(meshes)))}] + [{"name": mm["name"], "mesh": i} for i, mm in enumerate(meshes)]
        g = {"asset": {"version": "2.0", "generator": "sandboxzurich k93"}, "scene": 0, "scenes": [{"nodes": [0]}], "nodes": nodes, "meshes": meshes,
             "materials": mats, "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(bin_)}]}
        if imgs: g.update(images=imgs, textures=texs, samplers=samplers)
        js = json.dumps(g, separators=(",", ":")).encode(); js += b" " * (-len(js) % 4); bin_.extend(b"\0" * (-len(bin_) % 4))
        with open(path, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
            f.write(struct.pack("<II", len(js), 0x4E4F534A) + js); f.write(struct.pack("<II", len(bin_), 0x004E4942) + bytes(bin_))


def signed_area(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def triangulate(pts):
    """Ear clipping for CCW simple polygon -> index triples."""
    idx = list(range(len(pts))); out = []
    def inside(p, a, b, c):
        d1 = (p[0] - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (p[1] - b[1])
        d2 = (p[0] - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (p[1] - c[1])
        d3 = (p[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (p[1] - a[1])
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1; ok = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = pts[i0], pts[i1], pts[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-9: continue
            if any(inside(pts[j], a, b, c) for j in idx if j not in (i0, i1, i2)): continue
            out.append((i0, i1, i2)); idx.pop(k); ok = True; break
        if not ok: idx.pop(0)
    if len(idx) == 3: out.append(tuple(idx))
    return out
