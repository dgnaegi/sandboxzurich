"""Tiny mesh toolkit + GLB writer for the bike models (pure numpy, own design, WTFPL).
Space = glTF space: x right (drive side +x), y up, front = -z. P(u, h, x): u = forward metres, h = height."""
import json, struct, io
import numpy as np
from PIL import Image

def P(u, h, x=0.0): return np.array([x, h, -u], float)
def nz(v): return v / (np.linalg.norm(v) + 1e-12)
def lin(h):
    c = np.array([(h >> 16) & 255, (h >> 8) & 255, h & 255]) / 255.0
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)

# ---- atlas layout (px in 1024x512): wheel disc | chainring | basket grid | solid block
AW, AH = 512, 256
REG = dict(wheel=(0, 0, 256, 256), ring=(256, 0, 320, 64), grid=(320, 0, 448, 128), solid=(496, 240, 512, 256))
def uvmap(name, s, t):
    x0, y0, x1, y1 = REG[name]; return ((x0 + s * (x1 - x0)) / AW, (y0 + t * (y1 - y0)) / AH)
SOLID = uvmap("solid", .5, .5)

class Mesh:
    def __init__(s): s.P = []; s.N = []; s.UV = []; s.C = []; s.A = []; s.T = []; s.n = 0
    def add(s, Pv, Nv, tris, col, paint=0.0, uv=None):
        Pv = np.asarray(Pv, float); Nv = np.asarray(Nv, float); n = len(Pv)
        for (a, b, c) in tris:                      # orient every tri to agree with the hint normals
            nn = np.cross(Pv[b] - Pv[a], Pv[c] - Pv[a])
            if np.dot(nn, Nv[a] + Nv[b] + Nv[c]) < 0: b, c = c, b
            s.T.append((s.n + a, s.n + b, s.n + c))
        s.P.append(Pv); s.N.append(Nv)
        s.UV.append(np.tile(SOLID, (n, 1)) if uv is None else np.asarray(uv, float))
        s.C.append(np.tile(np.asarray(col, float), (n, 1)) if np.ndim(col) == 1 else np.asarray(col)); s.A.append(np.full(n, paint)); s.n += n
    def transform(s, f_pos, f_dir):
        s.P = [f_pos(p) for p in s.P]; s.N = [f_dir(n) for n in s.N]

def grid(m, rings, hints, col, paint=0.0, closed=True, uv=None):
    R = len(rings); K = len(rings[0]); tris = []
    for r in range(R - 1):
        for k in range(K if closed else K - 1):
            k2 = (k + 1) % K; a, b, c, d = r * K + k, r * K + k2, (r + 1) * K + k2, (r + 1) * K + k
            tris += [(a, b, c), (a, c, d)]
    m.add(np.reshape(rings, (-1, 3)), np.reshape(hints, (-1, 3)), tris, col, paint, uv)

def frame_of(d):
    d = nz(d); ref = np.array([0, 1., 0]) if abs(d[1]) < .9 else np.array([1., 0, 0])
    e1 = nz(np.cross(d, ref)); e2 = nz(np.cross(d, e1)); return d, e1, e2

def tube(m, a, b, ra, rb=None, sides=5, col=(.5, .5, .5), paint=0.0, cap=False, sq=1.0):
    """Straight tube a->b. sq squashes the radius along e1 (oval tubes)."""
    rb = ra if rb is None else rb; d, e1, e2 = frame_of(np.asarray(b) - np.asarray(a))
    rings = []; hints = []
    for c, r in ((a, ra), (b, rb)):
        th = 2 * np.pi * np.arange(sides) / sides + np.pi / 2
        dirs = np.cos(th)[:, None] * e1 * sq + np.sin(th)[:, None] * e2
        rings.append(np.asarray(c) + r * dirs); hints.append(np.array([nz(v) for v in (np.cos(th)[:, None] * e1 / max(sq, 1e-3) + np.sin(th)[:, None] * e2)]))
    grid(m, rings, hints, col, paint)
    if cap:
        for c, rg, sgn in ((a, rings[0], -1), (b, rings[1], 1)):
            pts = np.vstack([rg, [c]]); nn = np.tile(sgn * d, (sides + 1, 1))
            m.add(pts, nn, [(k, (k + 1) % sides, sides) for k in range(sides)], col, paint)

def ptube(m, pts, radii, sides=5, col=(.5, .5, .5), paint=0.0, cap=True):
    """Tube through a polyline with shared joint rings (handlebars, curved stays)."""
    pts = [np.asarray(p, float) for p in pts]; n = len(pts)
    tans = [nz(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]) for i in range(n)]
    _, e1, _ = frame_of(tans[0]); rings = []; hints = []
    for i in range(n):
        d = tans[i]; e1 = nz(e1 - d * np.dot(e1, d)); e2 = np.cross(d, e1)
        th = 2 * np.pi * np.arange(sides) / sides; dirs = np.cos(th)[:, None] * e1 + np.sin(th)[:, None] * e2
        r = radii[i] if hasattr(radii, "__len__") else radii
        rings.append(pts[i] + r * dirs); hints.append(dirs)
    grid(m, rings, hints, col, paint)
    if cap:
        for i, sgn in ((0, -1), (n - 1, 1)):
            m.add(np.vstack([rings[i], [pts[i]]]), np.tile(sgn * tans[i], (sides + 1, 1)), [(k, (k + 1) % sides, sides) for k in range(sides)], col, paint)

def cuboid(m, c, hu, hh, hx, col, paint=0.0, tu=1.0, tx=1.0, shift=0.0, uv=None):
    """Box centred at c=(u,h,x) with half sizes; top face scaled (tu,tx) and shifted forward by `shift`. Flat shaded."""
    u, h, x = -c[2], c[1], c[0]; cs = []
    for sh in (-1, 1):
        for su in (-1, 1):
            for sx in (-1, 1):
                k = 1.0 if sh < 0 else None
                uu = u + su * hu * (1 if sh < 0 else tu) + (shift if sh > 0 else 0); xx = x + sx * hx * (1 if sh < 0 else tx)
                cs.append(P(uu, h + sh * hh, xx))
    # corner index = sh*4 + su*2 + sx  with (-1->0, 1->1)
    def ci(sh, su, sx): return ((sh > 0) * 4) + ((su > 0) * 2) + (sx > 0)
    faces = [((1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1)), ((-1, -1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)),
             ((-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)), ((-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1)),
             ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)), ((-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1))]
    ctr = np.mean(cs, 0)
    for f in faces:
        q = [cs[ci(*(((s[0]), s[1], s[2])))] for s in [(a, b, d) for (a, b, d) in f]]
        nn = nz(np.cross(q[1] - q[0], q[2] - q[0]))
        if np.dot(nn, np.mean(q, 0) - ctr) < 0: nn = -nn
        m.add(q, np.tile(nn, (4, 1)), [(0, 1, 2), (0, 2, 3)], col, paint, uv)

def obox(m, a, b, w, h, col, paint=0.0, up=(0, 1., 0), wb=None, hb=None):
    """Oriented slab from a to b (w = lateral size, h = size along 'up' perpendicular)."""
    a = np.asarray(a); b = np.asarray(b); d = nz(b - a); e1 = nz(np.cross(d, up)); e2 = nz(np.cross(e1, d))
    wb = w if wb is None else wb; hb = h if hb is None else hb; cs = []
    for c, ww, hh in ((a, w, h), (b, wb, hb)):
        for s1, s2 in ((-1, -1), (1, -1), (1, 1), (-1, 1)): cs.append(c + s1 * ww / 2 * e1 + s2 * hh / 2 * e2)
    ctr = np.mean(cs, 0)
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        q = [cs[i] for i in f]; nn = nz(np.cross(q[1] - q[0], q[2] - q[0]))
        if np.dot(nn, np.mean(q, 0) - ctr) < 0: nn = -nn
        m.add(q, np.tile(nn, (4, 1)), [(0, 1, 2), (0, 2, 3)], col, paint)

def disc(m, c, r, nseg, col, paint=0.0, uvname=None, x_normal=1.0, cut=None):
    """Disc in the vertical plane (normal +-x) at centre c=(u,h,x). With uvname the polygon is textured (circle inscribed)."""
    pts = [np.asarray(c)]; uvs = [uvmap(uvname, .5, .5)] if uvname else None
    for k in range(nseg):
        a = 2 * np.pi * k / nseg; pts.append(np.asarray(c) + P(r * np.cos(a), r * np.sin(a), 0))
        if uvname: uvs.append(uvmap(uvname, .5 + .5 * np.cos(a), .5 - .5 * np.sin(a)))
    n = np.tile([x_normal, 0, 0], (nseg + 1, 1))
    m.add(pts, n, [(0, 1 + k, 1 + (k + 1) % nseg) for k in range(nseg)], col, paint, uvs)

def torus_tire(m, cu, ch, R, tw, th, nseg=24, nmin=6, x=0.0, col=(.02, .02, .02)):
    """Tyre: outer radius R, width tw, section height th, axis along x."""
    Rm = R - th / 2; rings = []; hints = []
    for k in range(nseg):
        a = 2 * np.pi * k / nseg; rd = P(np.cos(a), np.sin(a), 0)
        ring = []; hint = []
        for j in range(nmin):
            t = 2 * np.pi * j / nmin + np.pi / nmin * 0   # tip at outer
            off = np.array([np.sin(t) * tw / 2, 0, 0]); rr = Rm + np.cos(t) * th / 2
            ring.append(P(cu, ch, x) + rd * rr + off)
            hint.append(nz(rd * np.cos(t) / (th / 2) + np.array([np.sin(t) / (tw / 2), 0, 0])))
        rings.append(ring); hints.append(hint)
    rings.append(rings[0]); hints.append(hints[0])
    # wrap rings: last duplicates first -> close by index reuse
    grid(m, rings, hints, col)

# ---- texture atlas
def make_atlas():
    SS = 3
    def L(w, h): return Image.new("LA", (w * SS, h * SS), (0, 0))
    from PIL import ImageDraw
    # wheel 512x512
    im = L(512, 512); d = ImageDraw.Draw(im); c = 256 * SS; R = 254 * SS
    d.ellipse((c - R, c - R, c + R, c + R), fill=(170, 255))                       # rim band
    d.ellipse((c - R * .935, c - R * .935, c + R * .935, c + R * .935), fill=(0, 0))      # cut inside rim
    rf = R * .09; ro = R * .94
    for i in range(36):
        a = 2 * np.pi * i / 36; sgn = 1 if (i // 1) % 2 == 0 else -1
        fx, fy = c + rf * np.cos(a), c + rf * np.sin(a)
        b = a + sgn * np.deg2rad(62) * (1 if i % 4 < 2 else -1)
        d.line((fx, fy, c + ro * np.cos(b), c + ro * np.sin(b)), fill=(185, 255), width=int(2.2 * SS))
    d.ellipse((c - R * .11, c - R * .11, c + R * .11, c + R * .11), fill=(95, 255))        # hub flange
    d.ellipse((c - R * .055, c - R * .055, c + R * .055, c + R * .055), fill=(200, 255))
    d.ellipse((c - R, c - R, c + R, c + R), outline=(160, 255), width=2 * SS)
    wheel = im.resize((512, 512), Image.LANCZOS)
    # chainring 128
    im = L(128, 128); d = ImageDraw.Draw(im); c = 64 * SS; R = 63 * SS
    d.ellipse((c - R, c - R, c + R, c + R), fill=(80, 255)); d.ellipse((c - R * .80, c - R * .80, c + R * .80, c + R * .80), fill=(0, 0))
    for i in range(5):
        a = 2 * np.pi * i / 5 + .3; d.line((c, c, c + R * .85 * np.cos(a), c + R * .85 * np.sin(a)), fill=(80, 255), width=9 * SS)
    d.ellipse((c - R * .22, c - R * .22, c + R * .22, c + R * .22), fill=(80, 255))
    ring = im.resize((128, 128), Image.LANCZOS)
    # basket grid 256
    im = L(256, 256); d = ImageDraw.Draw(im); g = (60, 255)
    for i in range(12): x = (6 + i * 22) * SS; d.line((x, 0, x, 256 * SS), fill=g, width=int(5 * SS))
    for j in range(5): y = (10 + j * 58) * SS; d.line((0, y, 256 * SS, y), fill=g, width=int(6 * SS))
    d.rectangle((0, 0, 256 * SS, 12 * SS), fill=g); d.rectangle((0, 244 * SS, 256 * SS, 256 * SS), fill=g)
    grid_ = im.resize((256, 256), Image.LANCZOS)
    A = Image.new("LA", (1024, 512), (0, 0))
    A.paste(wheel, (0, 0)); A.paste(ring, (512, 0)); A.paste(grid_, (640, 0)); A.paste(Image.new("LA", (32, 32), (255, 255)), (992, 480))
    A = A.resize((AW, AH), Image.LANCZOS)
    g, a = A.split(); g = g.point(lambda v: v // 8 * 8 + 4); a = a.point(lambda v: min(255, (v + 8) // 16 * 16))
    A = Image.merge("LA", (g, a))
    b = io.BytesIO(); A.save(b, "PNG", optimize=True)
    return b.getvalue()

# ---- GLB writer
def write_glb(m, path, png, lean_deg=0.0):
    Pv = np.vstack(m.P).astype(np.float32); Nv = np.vstack(m.N); Nv = (Nv / (np.linalg.norm(Nv, axis=1, keepdims=True) + 1e-12))
    UV = np.vstack(m.UV); C = np.vstack(m.C); A = np.concatenate(m.A).astype(np.float32); T = np.array(m.T, np.uint32)
    # drop degenerate tris
    keep = [i for i, t in enumerate(T) if len({*t}) == 3]; T = T[keep].astype(np.uint16)
    n8 = np.clip(np.round(Nv * 127), -127, 127).astype(np.int8); n8 = np.hstack([n8, np.zeros((len(n8), 1), np.int8)])
    uv16 = np.clip(np.round(UV * 65535), 0, 65535).astype(np.uint16)
    c8 = np.clip(np.round(np.hstack([np.clip(C, 0, 1), np.ones((len(C), 1))]) * 255), 0, 255).astype(np.uint8)
    buf = bytearray(); views = []; acc = []
    def push(arr, target, **kw):
        while len(buf) % 4: buf.append(0)
        views.append(dict(buffer=0, byteOffset=len(buf), byteLength=arr.nbytes, target=target)); buf.extend(arr.tobytes()); return len(views) - 1
    def accessor(bv, ct, cnt, typ, **kw): acc.append(dict(bufferView=bv, componentType=ct, count=cnt, type=typ, **kw)); return len(acc) - 1
    n = len(Pv)
    iP = accessor(push(Pv, 34962), 5126, n, "VEC3", min=Pv.min(0).tolist(), max=Pv.max(0).tolist())
    while len(buf) % 4: buf.append(0)
    views.append(dict(buffer=0, byteOffset=len(buf), byteLength=n8.nbytes, byteStride=4, target=34962)); buf.extend(n8.tobytes())
    iN = accessor(len(views) - 1, 5120, n, "VEC3", normalized=True)
    iU = accessor(push(uv16, 34962), 5123, n, "VEC2", normalized=True)
    iC = accessor(push(c8, 34962), 5121, n, "VEC4", normalized=True)
    iA = accessor(push(A, 34962), 5126, n, "SCALAR")
    iI = accessor(push(T.reshape(-1), 34963), 5123, T.size, "SCALAR")
    while len(buf) % 4: buf.append(0)
    views.append(dict(buffer=0, byteOffset=len(buf), byteLength=len(png))); buf.extend(png); imv = len(views) - 1
    j = dict(asset=dict(version="2.0", generator="sandboxzurich pipeline/bikes"), scene=0, scenes=[dict(nodes=[0])], nodes=[dict(mesh=0, name="bike")],
             meshes=[dict(name="bike", primitives=[dict(attributes=dict(POSITION=iP, NORMAL=iN, TEXCOORD_0=iU, COLOR_0=iC, _PAINT=iA), indices=iI, material=0, mode=4)])],
             materials=[dict(name="bike", doubleSided=True, alphaMode="MASK", alphaCutoff=0.3, pbrMetallicRoughness=dict(baseColorTexture=dict(index=0), metallicFactor=0.1, roughnessFactor=0.55))],
             textures=[dict(source=0, sampler=0)], samplers=[dict(magFilter=9729, minFilter=9987, wrapS=33071, wrapT=33071)], images=[dict(bufferView=imv, mimeType="image/png")],
             accessors=acc, bufferViews=views, buffers=[dict(byteLength=len(buf))])
    js = json.dumps(j, separators=(",", ":")).encode(); js += b" " * (-len(js) % 4)
    while len(buf) % 4: buf.append(0)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(buf)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(buf), 0x004E4942) + bytes(buf)
    open(path, "wb").write(out); return len(T), len(out), Pv
