"""Procedural tree GLBs (pure numpy, no Blender). Run: python3 pipeline/trees/gen_trees.py
Each GLB: 1 mesh, 2 primitives (0 bark opaque, 1 foliage alpha-MASK with atlas), normalised to
height 1, crown diameter 1, origin at trunk foot, Y up. License: own generation, WTFPL.
"""
import json, struct, math, io
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "web/public/models/trees"
ATLAS = OUT / "leaves.webp"
ZB = 0.0

# ---------------------------------------------------------------- class parameters
# env: crown envelope (z0 crown base, shape exponent), cards: count, size, tile(s), colours (tint rgb pairs)
C = dict
CLASSES = {
    "broadleaf": C(trunk=(.32, .26, .2), th=.34, tr=.028, nb=7, ztop=1.0, w=.5, shape=.65, cards=720, size=.15,
                   tiles=[0, 0, 1], col=[(.30, .46, .16), (.40, .56, .2), (.24, .38, .13)], bark=(.33, .27, .22), hole=.25),
    "cherry": C(trunk=(.3, .22, .2), th=.3, tr=.03, nb=8, ztop=.97, w=.5, shape=.55, cards=760, size=.13,
                tiles=[1, 1, 1, 0], col=[(.36, .5, .2), (.42, .54, .22), (.3, .42, .17)], bark=(.26, .18, .17), hole=.12),
    "whiteblossom": C(trunk=(.3, .25, .2), th=.3, tr=.026, nb=8, ztop=.95, w=.5, shape=.6, cards=740, size=.13,
                      tiles=[10, 1, 0], col=[(.36, .52, .2), (.42, .56, .22), (.3, .44, .16)], bark=(.3, .24, .2), hole=.15),
    "plane": C(trunk=(.55, .5, .4), th=.45, tr=.036, nb=7, ztop=1.0, w=.5, shape=.9, cards=700, size=.16,
               tiles=[2, 0, 0], col=[(.34, .5, .17), (.42, .58, .22), (.28, .42, .14)], bark=(.62, .6, .5), hole=.3, mottle=True),
    "linden": C(trunk=(.3, .26, .22), th=.22, tr=.03, nb=9, ztop=1.0, w=.5, shape=.5, cards=900, size=.12,
                tiles=[1, 1, 0], col=[(.26, .44, .14), (.34, .52, .18), (.22, .38, .12)], bark=(.3, .26, .22), hole=.05),
    "maple": C(trunk=(.34, .3, .26), th=.3, tr=.03, nb=8, ztop=1.0, w=.5, shape=.6, cards=780, size=.15,
               tiles=[2, 2, 2, 0], col=[(.28, .5, .15), (.4, .6, .18), (.5, .62, .2)], bark=(.36, .32, .28), hole=.15),
    "chestnut": C(trunk=(.3, .24, .2), th=.25, tr=.034, nb=8, ztop=1.0, w=.5, shape=.55, cards=560, size=.21,
                  tiles=[6, 6, 6], col=[(.2, .38, .12), (.26, .46, .15), (.17, .32, .1)], bark=(.3, .24, .2), hole=.1, candles=46),
    "birch": C(trunk=(.9, .9, .86), th=.35, tr=.018, nb=8, ztop=1.0, w=.5, shape=.8, cards=640, size=.12,
               tiles=[3, 3, 3], col=[(.4, .56, .2), (.5, .64, .24), (.34, .5, .16)], bark=(.88, .88, .84), hole=.5, weep=True, mottle="birch"),
    "conifer": C(trunk=(.28, .2, .15), th=.08, tr=.026, nb=0, ztop=1.0, w=.5, shape=1.0, cards=0, size=.3,
                 tiles=[5], col=[(.13, .27, .14), (.17, .33, .17), (.1, .22, .12)], bark=(.28, .2, .15), hole=0, cone=True),
    "robinia": C(trunk=(.3, .25, .2), th=.38, tr=.026, nb=8, ztop=1.0, w=.5, shape=.55, cards=430, size=.23,
                 tiles=[8, 8, 8], col=[(.44, .58, .22), (.5, .62, .26), (.38, .52, .2)], bark=(.27, .23, .2), hole=.4),
    "ash": C(trunk=(.4, .38, .33), th=.36, tr=.028, nb=8, ztop=1.0, w=.5, shape=.65, cards=430, size=.24,
             tiles=[8, 8], col=[(.3, .46, .17), (.37, .53, .2), (.26, .4, .15)], bark=(.46, .44, .4), hole=.3),
    "oak": C(trunk=(.28, .22, .18), th=.22, tr=.042, nb=10, ztop=1.0, w=.5, shape=.4, cards=640, size=.16,
             tiles=[9, 9, 0], col=[(.2, .36, .12), (.27, .44, .15), (.24, .4, .13)], bark=(.27, .22, .19), hole=.12),
    "beech": C(trunk=(.5, .48, .45), th=.28, tr=.036, nb=9, ztop=1.0, w=.5, shape=.6, cards=700, size=.15,
               tiles=[10, 10, 0], col=[(.24, .42, .14), (.32, .5, .18), (.2, .36, .12)], bark=(.56, .54, .5), hole=.1),
    "pine": C(trunk=(.4, .3, .25), th=.34, tr=.026, nb=7, ztop=1.0, w=.5, shape=.75, cards=480, size=.3,
              tiles=[12, 12], col=[(.14, .28, .15), (.18, .34, .17), (.12, .24, .13)], bark=(.34, .26, .22), hole=.05),
    "columnar": C(trunk=(.32, .26, .2), th=.18, tr=.024, nb=9, ztop=1.0, w=.5, shape=.45, cards=740, size=.12,
                  tiles=[0, 1], col=[(.28, .44, .15), (.36, .52, .18), (.22, .36, .12)], bark=(.32, .27, .22), hole=.1, narrow=True),
}


def unit(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-9)


class Mesh:
    def __init__(self):
        self.p, self.n, self.c, self.uv, self.i = [], [], [], [], []
        self.nv = 0

    def add(self, p, n, c, uv, idx):
        self.p.append(p); self.n.append(n); self.c.append(c)
        self.uv.append(uv if uv is not None else np.zeros((len(p), 2)))
        self.i.append(np.asarray(idx, dtype=np.uint32) + self.nv)
        self.nv += len(p)

    def arrays(self):
        return (np.concatenate(self.p).astype(np.float32), np.concatenate(self.n).astype(np.float32),
                np.concatenate(self.c).astype(np.float32), np.concatenate(self.uv).astype(np.float32),
                np.concatenate(self.i).astype(np.uint32))


def tube(m, pts, radii, sides, color_fn):
    """Tapered tube along polyline pts (k,3) with radii (k,). Capped at the top by converging ring."""
    pts = np.asarray(pts, float); k = len(pts)
    P, N, Cc = [], [], []
    prev_u = None
    for j in range(k):
        d = pts[min(j + 1, k - 1)] - pts[max(j - 1, 0)]
        d = unit(d)
        a = np.array([1., 0, 0]) if abs(d[0]) < .9 else np.array([0, 0, 1.])
        u = unit(np.cross(d, a)); v = np.cross(d, u)
        for s in range(sides):
            t = 2 * math.pi * s / sides
            nrm = math.cos(t) * u + math.sin(t) * v
            P.append(pts[j] + nrm * radii[j]); N.append(nrm); Cc.append(color_fn(pts[j], s))
    idx = []
    for j in range(k - 1):
        for s in range(sides):
            a = j * sides + s; b = j * sides + (s + 1) % sides
            idx += [a, b, a + sides, b, b + sides, a + sides]
    m.add(np.array(P), np.array(N), np.array(Cc), None, idx)


def tile_uv(tile, inset=1.5 / 128):
    col, row = tile % 4, tile // 4
    u0, u1 = col / 4 + inset / 4, (col + 1) / 4 - inset / 4
    v0, v1 = row / 4 + inset / 4, (row + 1) / 4 - inset / 4
    return u0, u1, v0, v1


def cards(m, centers, normals_out, sizes, tiles, colors, rng, orient=None, aspect=None):
    """Add quads. orient: normal vectors of each card (random if None)."""
    n = len(centers)
    if orient is None:
        orient = unit(rng.normal(size=(n, 3)))
    ref = np.where(np.abs(orient[:, 1:2]) < .9, np.array([[0, 1., 0]]), np.array([[1., 0, 0]]))
    t1 = unit(np.cross(orient, ref))
    t2 = np.cross(orient, t1)
    rot = rng.uniform(0, 2 * math.pi, size=(n, 1))
    a = t1 * np.cos(rot) + t2 * np.sin(rot)
    b = -t1 * np.sin(rot) + t2 * np.cos(rot)
    if aspect is not None:
        b = b * aspect[:, None]
    h = sizes[:, None] * .5
    P = np.empty((n, 4, 3)); UV = np.empty((n, 4, 2))
    for q, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
        P[:, q] = centers + h * (sx * a + sy * b)
    for i in range(n):
        u0, u1, v0, v1 = tile_uv(tiles[i])
        UV[i] = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
    N = np.repeat(normals_out[:, None, :], 4, axis=1)
    Cc = np.repeat(colors[:, None, :], 4, axis=1)
    base = (np.arange(n) * 4)[:, None] + np.array([[0, 1, 2, 0, 2, 3]])
    m.add(P.reshape(-1, 3), N.reshape(-1, 3), Cc.reshape(-1, 3), UV.reshape(-1, 2), base.reshape(-1))


def make_tree(cls, variant, lod=0):
    p = dict(CLASSES[cls])
    p["cards"] = int(p["cards"] * 1.2)
    if lod:
        p["cards"] = int(p["cards"] * .3); p["size"] *= 1.75; p["nb"] = max(4, p["nb"] - 3); p["lod"] = 1
    rng = np.random.default_rng(hash((cls, variant)) % (2**32) if False else (sum(map(ord, cls)) * 131 + variant * 7919))
    bark, fol = Mesh(), Mesh()
    th, tr = p["th"] * rng.uniform(.9, 1.1), p["tr"] * .75 * rng.uniform(.9, 1.15)
    bc = np.array(p["bark"])
    mot = p.get("mottle")

    def bark_col(pt, s):
        v = rng.uniform(.85, 1.1)
        if mot is True:   # plane tree: cream / olive / grey patches
            patch = math.sin(pt[1] * 38 + s * 2.1) * math.sin(pt[1] * 17 - s * 3.3)
            c = np.array([.78, .74, .6]) if patch > .15 else (np.array([.45, .42, .3]) if patch < -.35 else bc)
            return c * v
        if mot == "birch":
            band = math.sin(pt[1] * 90 + s * 5.7) * math.sin(s * 3.1 + pt[1] * 21)
            return (np.array([.12, .11, .1]) if band > .6 else bc) * v
        return bc * v

    # trunk with slight lean
    lean = rng.normal(size=2) * .015
    k = 7
    ys = np.linspace(0, th, k)
    trunk_pts = np.stack([lean[0] * ys / th * 1.0 + np.sin(ys * 9 + variant) * .004, ys,
                          lean[1] * ys / th + np.cos(ys * 8) * .004], 1)
    flare = np.linspace(1.25, 1, k) ** 3
    tube(bark, trunk_pts, tr * .8 * flare * np.linspace(1, .75, k), 7, bark_col)
    top = trunk_pts[-1]
    global ZB
    ZB = th * .9 if not p.get('cone') else th

    if p.get("cone"):
        return make_conifer(p, rng, bark, fol, top, th, variant, bark_col)

    # crown envelope: ellipsoid-like in [th*.7 .. ztop]
    zb = th * (.9 if cls != "columnar" else .8)
    H = p["ztop"] - zb
    ctr = np.array([top[0], zb + H * .5, top[2]])
    R = .5 * (.5 if p.get("narrow") else 1.0)

    ph = rng.uniform(0, 6.28, size=4)

    def env_r(t, ang=0.0):  # t 0..1 along crown height; radius profile with angular lobes
        base = np.sin(np.pi * np.clip(t, 0, 1)) ** p["shape"]
        if p.get("narrow"):
            base = np.clip(np.sin(np.pi * np.clip(t, 0, 1)) ** .35, 0, 1) * (1 - .25 * t)
        lobe = 1 + .13 * math.sin(3 * ang + ph[0] + 4 * t) + .09 * math.sin(5 * ang + ph[1] - 3 * t) + .06 * math.sin(2 * t * 9 + ph[2])
        return R * base * lobe

    # cluster centres (foliage clumps), each carried by a branch from the trunk top
    ncl = p["nb"] * 2
    tg = []
    for b in range(ncl):
        ang = 2 * math.pi * (b + rng.uniform(-.3, .3)) / ncl
        t = rng.uniform(.2, .88)
        r = env_r(t, ang) * rng.uniform(.5, .85)
        tg.append([ctr[0] + r * math.cos(ang), zb + H * t, ctr[2] + r * math.sin(ang)])
    tg = np.array(tg)
    sig = p.get("sig", .12) * (.6 if p.get("narrow") else 1)
    for c in tg[::1]:
        s0 = np.array([trunk_pts[-1][0], th * rng.uniform(.8, 1.0) + .03 * rng.random(), trunk_pts[-1][2]])
        mid = (s0 + c) / 2 + np.array([0, .035, 0]) + rng.normal(size=3) * .015
        pts_ = np.array([s0, mid, c])
        rad = np.array([tr * .6, tr * .38, tr * .14]) * rng.uniform(.8, 1.1)
        tube(bark, pts_, rad, 4, lambda pt, s: bc * rng.uniform(.85, 1.05))

    n = p["cards"]
    pts = []
    while len(pts) < n:
        if rng.random() < .8:
            c = tg[rng.integers(len(tg))]
            pt = c + rng.normal(size=3) * sig * np.array([1, .8, 1])
        else:
            t = rng.uniform(.1, .95); ang = rng.uniform(0, 6.28); r = env_r(t, ang) * rng.uniform(.3, 1)
            pt = np.array([ctr[0] + r * math.cos(ang), zb + H * t, ctr[2] + r * math.sin(ang)])
        t = (pt[1] - zb) / H
        if t < .02 or t > 1:
            continue
        ang = math.atan2(pt[2] - ctr[2], pt[0] - ctr[0])
        if math.hypot(pt[0] - ctr[0], pt[2] - ctr[2]) > env_r(t, ang) * 1.04:
            continue
        pts.append(pt)
    pts = np.array(pts)
    if p.get("weep"):
        pts[:, 1] -= np.clip(np.linalg.norm(pts[:, [0, 2]] - ctr[[0, 2]], axis=1), 0, .5) * .35
        pts[:, 1] = np.maximum(pts[:, 1], th * .85)

    out = unit(pts - ctr * np.array([1, .9, 1]) + 1e-4)
    out[:, 1] = out[:, 1] * .8 + .1  # slightly upward for softer top lighting
    out = unit(out)
    sizes = p["size"] * rng.uniform(.75, 1.25, size=len(pts))
    tiles = rng.choice(p["tiles"], size=len(pts))
    pal = np.array(p["col"])
    cols = pal[rng.integers(0, len(pal), size=len(pts))] * rng.uniform(.82, 1.1, size=(len(pts), 1))
    # inner cards darker (self-shadow), top lighter
    depth = np.linalg.norm((pts - ctr) / np.array([R, H / 2, R]), axis=1)
    cols = cols * (.62 + .45 * np.clip(depth, 0, 1.1))[:, None] * (.9 + .15 * np.clip((pts[:, 1] - zb) / H, 0, 1))[:, None]
    orient = unit(rng.normal(size=(len(pts), 3)) * np.array([1, .8, 1]) + out * .6)
    aspect = None
    if p.get("weep"):
        aspect = np.full(len(pts), 1.5)
        orient = unit(rng.normal(size=(len(pts), 3)) * np.array([1, .2, 1]) + out * .3)
        # make b-axis (card long axis) hang down: rotate handled by randomness, acceptable
    cards(fol, pts, out, sizes, tiles, np.clip(cols, 0, 1), rng, orient, aspect)

    nc = p.get("candles", 0)
    if nc:
        idx = np.argsort(-pts[:, 1])[: nc * 3]
        idx = rng.choice(idx, nc, replace=False)
        cp = pts[idx] + np.array([0, .035, 0])
        cc = np.repeat(np.array([[1., .96, .92]]), nc, 0) * rng.uniform(.9, 1., size=(nc, 1))
        o = unit(rng.normal(size=(nc, 3)) * np.array([1, .1, 1]))
        cards(fol, cp, unit(out[idx] + [0, .6, 0]), np.full(nc, .13), np.full(nc, 7), cc, rng, o,
              aspect=np.full(nc, 1.4))
    return bark, fol


def make_conifer(p, rng, bark, fol, top, th, variant, bark_col):
    # spruce/pine: trunk continues to the tip, whorls of drooping branches in a cone
    tip = 1.0
    ys = np.linspace(th, tip, 5)
    tube(bark, np.stack([np.zeros(5) + np.sin(ys * 7) * .004, ys, np.zeros(5)], 1),
         np.linspace(p["tr"] * .8, .004, 5), 6, bark_col)
    pal = np.array(p["col"])
    n_whorl = 7 if p.get('lod') else 13
    cs, nr, sz, ti, co, ori, asp = [], [], [], [], [], [], []
    for w in range(n_whorl):
        t = w / (n_whorl - 1)
        y = th + (tip - th - .03) * t
        R = .5 * (1 - t) ** .95 * (1.0 if t < .97 else .2)
        nb = int(round(6 + 5 * (1 - t))) + (variant % 2) - (3 if p.get('lod') else 0)
        phase = rng.uniform(0, 6.28)
        for b in range(nb):
            a = phase + 2 * math.pi * b / nb + rng.uniform(-.25, .25)
            d = np.array([math.cos(a), 0, math.sin(a)])
            L = max(R, .04)
            droop = .09 * (1 - t) + .02
            tube(bark, np.array([[0, y, 0], d * L * .8 + [0, y - droop * .8, 0]]),
                 np.array([.005, .0025]), 3, lambda pt, s: np.array(p["bark"]))
            # spray cards along branch: flat, slightly drooping, long axis = branch dir
            ncard = 2 if L > .2 else 1
            for q in range(ncard):
                f = (q + .6) / ncard
                c = d * L * f + [0, y - droop * f - .005, 0]
                cs.append(c); ori.append(unit(np.array([0, 1., 0]) + d * .0 + rng.normal(size=3) * .12))
                nr.append(unit(d + [0, .5, 0])); sz.append(max(.17, L * 1.15 / ncard * 1.5) * (1.5 if p.get('lod') else 1))
                ti.append(5); asp.append(1.0)
                co.append(pal[rng.integers(len(pal))] * rng.uniform(.8, 1.12) * (.7 + .4 * (1 - t) * 0 + .35 * f + .2 * t))
    cs, nr = np.array(cs), np.array(nr)
    # tile 5 spray runs along u from base(left) to tip (right); build orientation so a-axis follows branch dir
    for i in range(len(cs)):
        pass
    sizes = np.array(sz)
    ori = np.array(ori)
    # custom quad build so the spray's long axis follows the radial direction
    n = len(cs)
    dirs = unit(np.stack([cs[:, 0], np.zeros(n), cs[:, 2]], 1) + 1e-6)
    side = unit(np.cross(dirs, np.array([0, 1., 0])))
    P = np.empty((n * 2, 4, 3)); UV = np.empty((n * 2, 4, 2))
    u0, u1, v0, v1 = tile_uv(5)
    up = np.array([0, 1., 0])
    for i in range(n):
        L = sizes[i]
        c0 = cs[i] - dirs[i] * L * .5
        w = L * .42
        droop = np.array([0, -.03, 0])
        for q, ang in enumerate((.35, 1.15)):  # two crossed, tilted sprays
            sd = side[i] * math.cos(ang) + up * math.sin(ang) * (1 if q == 0 else 1)
            P[2 * i + q, 0] = c0 - sd * w; P[2 * i + q, 1] = c0 + dirs[i] * L - sd * w + droop
            P[2 * i + q, 2] = c0 + dirs[i] * L + sd * w + droop; P[2 * i + q, 3] = c0 + sd * w
            UV[2 * i + q] = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
    n2 = n * 2
    N = np.repeat(np.repeat(nr, 2, 0)[:, None, :], 4, 1)
    Cc = np.repeat(np.clip(np.repeat(np.array(co), 2, 0), 0, 1)[:, None, :], 4, 1)
    base = (np.arange(n2) * 4)[:, None] + np.array([[0, 1, 2, 0, 2, 3]])
    fol.add(P.reshape(-1, 3), N.reshape(-1, 3), Cc.reshape(-1, 3), UV.reshape(-1, 2), base.reshape(-1))
    # tip tuft cards
    return bark, fol


def normalise(bark, fol):
    bp = bark.arrays(); fp = fol.arrays()
    allp = np.concatenate([bp[0], fp[0]])
    lo, hi = allp.min(0), allp.max(0)
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    # crown diameter = max extent over x and z
    dia = max(hi[0] - lo[0], hi[2] - lo[2])
    sx = 1 / dia; sy = 1 / (hi[1] - lo[1])
    out = []
    for a in (bp, fp):
        P = a[0].copy()
        P[:, 0] = (P[:, 0] - cx) * sx; P[:, 2] = (P[:, 2] - cz) * sx; P[:, 1] = (P[:, 1] - lo[1]) * sy
        cc = a[2] if a is fp else np.clip(a[2], 0, 1) ** 2.2
        N = a[1].copy(); N[:, 1] /= sy / sx; N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
        out.append((P, N, cc, a[3], a[4]))
    out.append(((ZB - lo[1]) * sy))
    return out


def pad4(b):
    return b + b"\x00" * ((4 - len(b) % 4) % 4)


def write_glb(path, prims, name):
    buf = bytearray(); views = []; accs = []

    def view(data, target=None):
        while len(buf) % 4: buf.append(0)
        v = {"buffer": 0, "byteOffset": len(buf), "byteLength": len(data)}
        if target: v["target"] = target
        buf.extend(data); views.append(v); return len(views) - 1

    gprims = []
    for k, (P, N, Cc, UV, I) in enumerate(prims):
        attrs = {}
        def acc(arr, typ, ctype, target, minmax=False, norm=False, stride=None, count=None):
            vi = view(arr.tobytes(), target)
            if stride: views[vi]["byteStride"] = stride
            a = {"bufferView": vi, "componentType": ctype, "count": count or len(arr), "type": typ}
            if norm: a["normalized"] = True
            if minmax: a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
            accs.append(a); return len(accs) - 1
        attrs["POSITION"] = acc(P.astype("<f4"), "VEC3", 5126, 34962, True)
        n8 = np.zeros((len(N), 4), np.int8); n8[:, :3] = np.round(np.clip(N, -1, 1) * 127)
        attrs["NORMAL"] = acc(n8, "VEC3", 5120, 34962, norm=True, stride=4, count=len(N))
        c8 = np.full((len(Cc), 4), 255, np.uint8); c8[:, :3] = np.round(np.clip(Cc, 0, 1) * 255)
        attrs["COLOR_0"] = acc(c8, "VEC4", 5121, 34962, norm=True)
        if k == 1: attrs["TEXCOORD_0"] = acc(np.round(np.clip(UV, 0, 1) * 65535).astype("<u2"), "VEC2", 5123, 34962, norm=True)
        ind = acc(I.astype("<u2"), "SCALAR", 5123, 34963)
        gprims.append({"attributes": attrs, "indices": ind, "material": k, "mode": 4})
    gltf = {
        "asset": {"version": "2.0", "generator": "sandboxzurich pipeline/trees/gen_trees.py (WTFPL)"},
        "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0, "name": name}],
        "meshes": [{"name": name, "primitives": gprims}],
        "materials": [{"name": "bark", "pbrMetallicRoughness": {"metallicFactor": 0, "roughnessFactor": 1}},
                      {"name": "foliage", "alphaMode": "MASK", "doubleSided": True, "pbrMetallicRoughness": {"metallicFactor": 0, "roughnessFactor": 1}}],
        "bufferViews": views, "accessors": accs, "buffers": [{"byteLength": len(buf)}],
    }
    js = pad4(json.dumps(gltf, separators=(",", ":")).encode()).replace(b"\x00", b" ") if False else json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    bn = bytes(buf) + b"\x00" * ((4 - len(buf) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(bn)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack("<II", len(bn), 0x004E4942)); f.write(bn)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []; rows = []
    for cls in CLASSES:
        for v, lod in ((0, 0), (1, 0), (0, 1)):
            bark, fol = make_tree(cls, v, lod)
            *prims, zb = normalise(bark, fol)
            f = f"{cls}_{v}.glb" if not lod else f"{cls}_lod1.glb"
            write_glb(OUT / f, prims, f.replace(".glb", ""))
            tris = sum(len(p[4]) // 3 for p in prims)
            kb = (OUT / f).stat().st_size / 1024
            manifest.append({"cls": cls, "file": f, "variant": v, "lod": lod, "zb": round(float(zb), 3), "tris": tris})
            rows.append((f, tris, kb))
            print(f"{f:20s} tris={tris:5d} kb={kb:6.1f} zb={zb:.2f}")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    lines = ["# Baummodelle (pipeline/trees)", "",
             "Erzeugt per `python3 pipeline/trees/atlas.py && python3 pipeline/trees/gen_trees.py` (numpy/PIL, reproduzierbar, seeded).",
             "Pro GLB: 1 Mesh, 2 Primitives (Rinde, Laub). Der Blattatlas `leaves.webp` (4x4 Kacheln) wird einmal separat geladen. `_lod1` = vereinfachte Mittel-LOD.",
             "Normiert: Höhe 1, Kronendurchmesser 1, Ursprung Stammfuss, Y oben.", "",
             "| Datei | Tris | KB | Lizenz |", "|---|---|---|---|"]
    lines += [f"| {f} | {t} | {k:.0f} | eigene Erzeugung, WTFPL |" for f, t, k in rows]
    (ROOT / "research/trees.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
