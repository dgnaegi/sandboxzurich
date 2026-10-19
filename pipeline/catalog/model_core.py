"""Mesh builder, shared texture atlas and GLB writer for the catalog models (no Blender). y up, metres, origin at footprint centre on the ground."""
import io, json, math, struct
import numpy as np
from PIL import Image, ImageDraw

ATLAS = 512
CELL = 64
NAMES = ["granite", "gneiss", "kalk", "sandstein", "concrete", "kunststein", "bronze", "bronze_hi", "wood", "wood_dark", "steel_dark",
         "steel_grey", "glass", "glass_green", "water", "jet", "roofglass", "poster_a", "poster_b", "screen", "fahne_tram", "fahne_bus",
         "kiosk_body", "awning", "lampglass", "iron", "ticket", "white", "yellow", "red", "bank_wood", "poster_blank", "kiosk_window", "asphalt_dark", "rubber", "kiosk_sign"]
BLEND = {"glass", "glass_green", "water", "jet", "roofglass"}
BASE = dict(granite="#7d7d78", gneiss="#5e5e5a", kalk="#cfc4ad", sandstein="#bdb5a0", concrete="#9a9a96", kunststein="#b8b2a6", bronze="#4a3d2c",
            bronze_hi="#8a6d45", wood="#7a5a3a", wood_dark="#4d3a28", steel_dark="#3a3f44", steel_grey="#767b80", iron="#3a3b3c", white="#e8e8e4",
            yellow="#e8b820", red="#b8322a", bank_wood="#b08a5a", kiosk_body="#5a4636", asphalt_dark="#2c2d2f", rubber="#2a2a2a")


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def cell_xy(name):
    i = NAMES.index(name)
    return (i % 8, i // 8)


def _noisy(rgb, amp, seed, a=255):
    r = np.random.default_rng(seed)
    arr = np.zeros((CELL, CELL, 4), np.float32); arr[..., :3] = rgb; arr[..., 3] = a
    n = r.normal(0, amp, (CELL, CELL, 1)); arr[..., :3] += n
    return arr


def paint(name, seed):
    if name in BASE:
        amp = 9 if name in ("granite", "gneiss", "kalk", "sandstein", "concrete", "kunststein") else 4
        arr = _noisy(hexc(BASE[name]), amp, seed)
        if name in ("granite", "gneiss", "sandstein", "kalk"):   # speckles
            r = np.random.default_rng(seed + 1)
            for _ in range(60):
                x, y = r.integers(0, CELL, 2); arr[y, x, :3] *= r.choice([0.7, 1.25])
        if name in ("bank_wood", "wood", "wood_dark"):            # grain lines
            for y in range(0, CELL, 8): arr[y, :, :3] *= 0.82
        if name == "concrete":
            arr[::32, :, :3] *= 0.85
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    im = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 255)); d = ImageDraw.Draw(im)
    if name == "bronze_hi":
        pass
    elif name == "steel_dark":
        pass
    elif name == "glass": im.paste((170, 195, 200, 70), (0, 0, CELL, CELL)); d.line([(0, CELL - 1), (CELL - 1, 0)], fill=(240, 245, 245, 110), width=3)
    elif name == "glass_green": im.paste((150, 195, 180, 90), (0, 0, CELL, CELL)); d.line([(0, CELL - 1), (CELL - 1, 0)], fill=(235, 245, 240, 120), width=3)
    elif name == "roofglass": im.paste((140, 185, 170, 130), (0, 0, CELL, CELL))
    elif name == "water": im.paste((70, 125, 150, 165), (0, 0, CELL, CELL)); [d.line([(0, y), (CELL, y + 4)], fill=(190, 225, 235, 190), width=1) for y in range(6, CELL, 14)]
    elif name == "jet": im.paste((225, 240, 245, 190), (0, 0, CELL, CELL))
    elif name in ("poster_a", "poster_b"):
        col = [(238, 232, 215), (35, 70, 120)] if name == "poster_a" else [(235, 235, 235), (200, 60, 50)]
        im.paste(col[0] + (255,), (0, 0, CELL, CELL)); d.rectangle([4, 4, 60, 34], fill=col[1] + (255,)); d.ellipse([34, 12, 54, 30], fill=(240, 200, 60, 255))
        d.rectangle([6, 40, 58, 44], fill=(40, 40, 40, 255)); d.rectangle([6, 50, 40, 53], fill=(90, 90, 90, 255))
    elif name == "poster_blank": im.paste((226, 224, 214, 255), (0, 0, CELL, CELL))
    elif name == "screen":
        im.paste((16, 18, 22, 255), (0, 0, CELL, CELL))
        for i, y in enumerate(range(8, 56, 12)): d.rectangle([5, y, 12, y + 5], fill=(240, 240, 240, 255)); d.rectangle([17, y, 40 - i * 3, y + 5], fill=(255, 150, 20, 255)); d.rectangle([48, y, 58, y + 5], fill=(255, 150, 20, 255))
    elif name in ("fahne_tram", "fahne_bus"):   # VBZ stop sign (photos Commons: blue field, white stop name; pictogram tram / bus; white line row)
        im.paste((252, 252, 250, 255), (0, 0, CELL, CELL)); d.rectangle([0, 0, CELL, 38], fill=(0, 66, 140, 255))
        d.rectangle([14, 6, 58, 12], fill=(255, 255, 255, 255)); d.rectangle([14, 17, 50, 22], fill=(220, 230, 245, 255)); d.rectangle([14, 27, 40, 31], fill=(190, 205, 230, 255))
        d.rounded_rectangle([2, 8, 11, 30], radius=2, fill=(255, 255, 255, 255))
        if name == "fahne_tram": d.line([(6, 3), (6, 8)], fill=(255, 255, 255, 255), width=1); d.rectangle([4, 12, 9, 17], fill=(0, 66, 140, 255)); d.rectangle([4, 21, 9, 26], fill=(0, 66, 140, 255))
        else: d.rectangle([4, 11, 9, 20], fill=(0, 66, 140, 255)); d.ellipse([3, 26, 6, 30], fill=(0, 66, 140, 255)); d.ellipse([7, 26, 10, 30], fill=(0, 66, 140, 255))
        for i, x in enumerate((4, 24, 44)): d.rounded_rectangle([x, 43, x + 16, 58], radius=3, fill=((0, 66, 140, 255) if name == "fahne_tram" else (30, 120, 70, 255))); d.rectangle([x + 4, 47, x + 12, 54], fill=(255, 255, 255, 255))
    elif name == "awning":
        for i in range(8): d.rectangle([i * 8, 0, i * 8 + 7, CELL], fill=((196, 50, 40, 255) if i % 2 == 0 else (240, 238, 232, 255)))
    elif name == "lampglass": im.paste((255, 235, 190, 255), (0, 0, CELL, CELL))
    elif name == "ticket":
        im.paste((78, 82, 88, 255), (0, 0, CELL, CELL)); d.rectangle([8, 6, 56, 30], fill=(25, 60, 110, 255)); d.rectangle([12, 10, 52, 14], fill=(235, 235, 235, 255))
        d.rectangle([10, 38, 30, 52], fill=(30, 30, 32, 255)); d.rectangle([38, 38, 54, 44], fill=(20, 20, 22, 255)); d.rectangle([38, 48, 54, 52], fill=(210, 190, 60, 255))
    elif name == "kiosk_sign":   # "k kiosk" fascia: dark field, white wordmark (Commons photos Zuerich Heimplatz/Paradeplatz)
        im.paste((36, 30, 28, 255), (0, 0, CELL, CELL)); d.rectangle([6, 22, 12, 42], fill=(255, 255, 255, 255)); d.rectangle([16, 22, 56, 42], outline=(255, 255, 255, 255), width=2)
        d.rectangle([22, 28, 50, 36], fill=(235, 235, 235, 255))
    elif name == "kiosk_window":
        im.paste((38, 44, 50, 255), (0, 0, CELL, CELL)); d.rectangle([4, 36, 60, 60], fill=(190, 150, 90, 255)); [d.rectangle([6 + i * 12, 40, 14 + i * 12, 56], fill=c) for i, c in enumerate([(200, 60, 50, 255), (60, 120, 200, 255), (230, 200, 60, 255), (80, 160, 90, 255), (220, 220, 220, 255)])]
    return im


def atlas_image():
    im = Image.new("RGBA", (ATLAS, ATLAS), (255, 0, 255, 255))
    for i, n in enumerate(NAMES):
        im.paste(paint(n, 100 + i), ((i % 8) * CELL, (i // 8) * CELL))
    return im


def avg_color(name):
    a = np.array(paint(name, 100 + NAMES.index(name)), float).reshape(-1, 4).mean(0)
    return a


def uvc(name, s, t):
    """UV inside the cell: s right, t up, both 0..1."""
    cx, cy = cell_xy(name); m = 3
    return ((cx * CELL + m + s * (CELL - 2 * m)) / ATLAS, (cy * CELL + m + (1 - t) * (CELL - 2 * m)) / ATLAS)


class Mesh:
    def __init__(self, name):
        self.name = name
        self.g = {"o": dict(p=[], n=[], uv=[], i=[]), "b": dict(p=[], n=[], uv=[], i=[])}
        self.faces = []   # (group, tri vertices, cell) for the preview renderer

    def _grp(self, cell):
        return self.g["b" if cell in BLEND else "o"], ("b" if cell in BLEND else "o")

    def quad(self, cell, p, uvr=(0, 0, 1, 1), n=None, nn=None):
        """p: 4 points CCW seen from front: bottom-left, bottom-right, top-right, top-left."""
        g, k = self._grp(cell); p = np.array(p, float)
        if n is None:
            n = np.cross(p[1] - p[0], p[2] - p[0]); n = n / (np.linalg.norm(n) or 1)
        s0, t0, s1, t1 = uvr
        uv = [uvc(cell, s0, t0), uvc(cell, s1, t0), uvc(cell, s1, t1), uvc(cell, s0, t1)]
        b = len(g["p"])
        for i in range(4):
            g["p"].append(p[i]); g["n"].append(nn[i] if nn is not None else n); g["uv"].append(uv[i])
        g["i"] += [b, b + 1, b + 2, b, b + 2, b + 3]
        self.faces.append((k, p[[0, 1, 2]], cell)); self.faces.append((k, p[[0, 2, 3]], cell))

    def box(self, cell, c, s, ry=0.0, top=True, bottom=False, front=None, back=None):
        """c: centre (x,y,z), s: size (sx,sy,sz); local +z = front."""
        cx, cy, cz = c; hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
        co, si = math.cos(ry), math.sin(ry)
        def T(x, y, z): return (cx + x * co + z * si, cy + y, cz - x * si + z * co)
        f = front or cell; bk = back or cell
        self.quad(f, [T(-hx, -hy, hz), T(hx, -hy, hz), T(hx, hy, hz), T(-hx, hy, hz)])
        self.quad(bk, [T(hx, -hy, -hz), T(-hx, -hy, -hz), T(-hx, hy, -hz), T(hx, hy, -hz)])
        self.quad(cell, [T(hx, -hy, hz), T(hx, -hy, -hz), T(hx, hy, -hz), T(hx, hy, hz)])
        self.quad(cell, [T(-hx, -hy, -hz), T(-hx, -hy, hz), T(-hx, hy, hz), T(-hx, hy, -hz)])
        if top: self.quad(cell, [T(-hx, hy, hz), T(hx, hy, hz), T(hx, hy, -hz), T(-hx, hy, -hz)])
        if bottom: self.quad(cell, [T(-hx, -hy, -hz), T(hx, -hy, -hz), T(hx, -hy, hz), T(-hx, -hy, hz)])

    def lathe(self, cell, profile, seg=12, c=(0, 0, 0), smooth=True, closed=True, rot=0.0, turns=1.0):
        """profile: [(r, y)] bottom to top; faces point to the right of the walking direction (outwards when going up on the outside)."""
        g, k = self._grp(cell); prof = np.array(profile, float)
        for j in range(len(prof) - 1):
            (r0, y0), (r1, y1) = prof[j], prof[j + 1]
            if abs(r0) < 1e-6 and abs(r1) < 1e-6: continue
            dr, dy = r1 - r0, y1 - y0; L = math.hypot(dr, dy) or 1
            nr, ny = dy / L, -dr / L          # outward normal (radial, vertical)
            for a in range(seg):
                a0 = rot + 2 * math.pi * turns * a / seg; a1 = rot + 2 * math.pi * turns * (a + 1) / seg
                P = lambda r, y, an: (c[0] + r * math.cos(an), c[1] + y, c[2] - r * math.sin(an))
                pts = [P(r0, y0, a0), P(r0, y0, a1), P(r1, y1, a1), P(r1, y1, a0)]
                if smooth: nn = [(nr * math.cos(an), ny, -nr * math.sin(an)) for an in (a0, a1, a1, a0)]
                else:
                    am = (a0 + a1) / 2; nn = [(nr * math.cos(am), ny, -nr * math.sin(am))] * 4
                u0, u1 = a / seg, (a + 1) / seg; v0, v1 = j / (len(prof) - 1), (j + 1) / (len(prof) - 1)
                uvs = [uvc(cell, u0, v0), uvc(cell, u1, v0), uvc(cell, u1, v1), uvc(cell, u0, v1)]
                b = len(g["p"])
                for q in range(4): g["p"].append(np.array(pts[q])); g["n"].append(np.array(nn[q])); g["uv"].append(uvs[q])
                if r0 < 1e-6:      # apex at bottom: pts 0,1 coincide
                    g["i"] += [b, b + 2, b + 3]; self.faces.append((k, np.array([pts[0], pts[2], pts[3]]), cell))
                elif r1 < 1e-6:    # apex at top: pts 2,3 coincide
                    g["i"] += [b, b + 1, b + 2]; self.faces.append((k, np.array([pts[0], pts[1], pts[2]]), cell))
                else:
                    g["i"] += [b, b + 1, b + 2, b, b + 2, b + 3]
                    self.faces.append((k, np.array([pts[0], pts[1], pts[2]]), cell)); self.faces.append((k, np.array([pts[0], pts[2], pts[3]]), cell))

    def ribbon(self, cell, pts, w, twoplanes=True):
        """Thin ribbon along a polyline (water jets, cables), crossing planes."""
        pts = [np.array(p, float) for p in pts]
        for ang in ((0, math.pi / 2) if twoplanes else (0,)):
            off = np.array([math.cos(ang), 0, math.sin(ang)]) * w / 2
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                self.quad(cell, [a - off, b - off, b + off, a + off], n=(0, 1, 0))
                self.quad(cell, [a + off, b + off, b - off, a - off], n=(0, 1, 0))

    def tri_count(self):
        return sum(len(v["i"]) // 3 for v in self.g.values())

    def bounds(self):
        P = np.array([p for v in self.g.values() for p in v["p"]]); return P.min(0), P.max(0)


def write_glb(mesh, path, atlas, extras):
    png = io.BytesIO(); atlas.quantize(colors=128, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(png, "PNG", optimize=True); png = png.getvalue()
    bin_ = bytearray(); views = []; acc = []; prims = []
    def add(data, target=None):
        while len(bin_) % 4: bin_.append(0)
        views.append(dict(buffer=0, byteOffset=len(bin_), byteLength=len(data), **({"target": target} if target else {}))); bin_.extend(data); return len(views) - 1
    for k, mat in (("o", 0), ("b", 1)):
        g = mesh.g[k]
        if not g["i"]: continue
        P = np.array(g["p"], np.float32); N = np.array(g["n"], np.float32); UV = np.array(g["uv"], np.float32); I = np.array(g["i"], np.uint16)
        a = {}
        for nm, arr, ct, ty in (("POSITION", P, 5126, "VEC3"), ("NORMAL", N, 5126, "VEC3"), ("TEXCOORD_0", UV, 5126, "VEC2")):
            bv = add(arr.tobytes(), 34962); d = dict(bufferView=bv, componentType=ct, count=len(arr), type=ty)
            if nm == "POSITION": d["min"] = P.min(0).tolist(); d["max"] = P.max(0).tolist()
            acc.append(d); a[nm] = len(acc) - 1
        bv = add(I.tobytes(), 34963); acc.append(dict(bufferView=bv, componentType=5123, count=len(I), type="SCALAR"))
        prims.append(dict(attributes=a, indices=len(acc) - 1, material=mat))
    ibv = add(png)
    js = dict(asset=dict(version="2.0", generator="catalog/model_core.py"), scene=0, scenes=[dict(nodes=[0])], nodes=[dict(mesh=0, name=mesh.name)],
              meshes=[dict(primitives=prims, extras=extras)], buffers=[dict(byteLength=len(bin_))], bufferViews=views, accessors=acc,
              images=[dict(bufferView=ibv, mimeType="image/png")], samplers=[dict(magFilter=9729, minFilter=9987, wrapS=33071, wrapT=33071)], textures=[dict(source=0, sampler=0)],
              materials=[dict(name="atlas", pbrMetallicRoughness=dict(baseColorTexture=dict(index=0), metallicFactor=0.0, roughnessFactor=0.85)),
                         dict(name="atlas_blend", alphaMode="BLEND", doubleSided=True, pbrMetallicRoughness=dict(baseColorTexture=dict(index=0), metallicFactor=0.0, roughnessFactor=0.3))])
    j = json.dumps(js, separators=(",", ":")).encode(); j += b" " * (-len(j) % 4)
    while len(bin_) % 4: bin_.append(0)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(bin_)) + struct.pack("<II", len(j), 0x4E4F534A) + j + struct.pack("<II", len(bin_), 0x004E4942) + bytes(bin_)
    open(path, "wb").write(out)
