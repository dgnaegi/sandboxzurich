"""Project LOD2 buildings into Mapillary images, sample facade pixels, store per-(image, building) Lab colours.
Cache: data/raw/autofacade/imgres/<id>.json  ->  {bldidx: {lab, n, inc, dist, spread}}
Usage: python extract.py [--debug id]"""
import json
import math
import pickle
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import pitch as pitch_mod
from common import CACHE, rgb2lab

RW = 512  # working width
CAMH = 1.7
G = None


def load_geom():
    global G
    if G is None:
        G = pickle.load(open(CACHE / "geom.pkl", "rb"))
        t = G["tris"]
        G["cen"] = t.mean(1)
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        ln = np.linalg.norm(n, axis=1, keepdims=True)
        G["nrm"] = n / np.maximum(ln, 1e-9)
        G["area"] = ln[:, 0] / 2
        from scipy.spatial import cKDTree
        G["kd"] = cKDTree(G["cen"][:, :2])
        cd = json.load(open(CACHE.parents[1] / "build" / "citydata_v3_-2849_-2069_1952_1454.json"))["trees"]
        G["tr"] = np.array([[t[0], t[1], float(t[3] or 8)] for t in cd])
        G["trkd"] = cKDTree(G["tr"][:, :2])
        G["NT"] = len(G["tris"])
    return G


def basis(hdg, pitch):
    h = math.radians(hdg)
    f0 = np.array([math.sin(h), math.cos(h), 0.0]); r0 = np.array([math.cos(h), -math.sin(h), 0.0]); u0 = np.array([0, 0, 1.0])
    fw = math.cos(pitch) * f0 + math.sin(pitch) * u0
    up = -math.sin(pitch) * f0 + math.cos(pitch) * u0
    return fw, r0, up


def render(cam, hdg, f, k1, k2, W, H, maxd=90.0, mx=0, my=0, pitch=0.0):
    """Painter's-algorithm ID map of triangles. Returns idmap (int32, -1 empty)."""
    g = load_geom()
    idx = np.array(g["kd"].query_ball_point(cam[:2], maxd), dtype=int)
    if len(idx) == 0:
        return np.full((H + 2 * my, W + 2 * mx), -1, np.int32), idx
    fw, rt, up = basis(hdg, pitch)
    T = g["tris"][idx].astype(np.float64) - cam
    xc, yc, zc = T @ rt, -(T @ up), T @ fw  # x right, y down, z forward
    P = np.stack([xc, yc, zc], -1)  # (n,3,3)
    keep = (P[:, :, 2].max(1) > 0.3)
    # drop tris fully outside a generous horizontal wedge
    ok = keep & ~((P[:, :, 0] > 3.0 * P[:, :, 2].clip(0.3)).all(1)) & ~((P[:, :, 0] < -3.0 * P[:, :, 2].clip(0.3)).all(1))
    idx, P = idx[ok], P[ok]
    pim = Image.new('I', (W + 2 * mx, H + 2 * my), 0)
    dr = ImageDraw.Draw(pim)
    depth = P[:, :, 2].mean(1)
    ti = np.array(g["trkd"].query_ball_point(cam[:2], 60.0), dtype=int)
    items = [(d, 0, o) for o, d in enumerate(depth)]
    for j in ti:
        tx, ty, th = g["tr"][j]
        v = np.array([tx, ty, cam[2] - CAMH + 0.55 * th]) - cam
        zc_ = v @ fw
        if zc_ > 1.0:
            items.append((zc_, 1, j))
    items.sort(key=lambda t: -t[0])
    order = items
    cx, cy = W / 2 + mx, H / 2 + my
    for dep, kind_, o in order:
        if kind_ == 1:
            tx, ty, th = g["tr"][o]
            v = np.array([tx, ty, cam[2] - CAMH + 0.55 * th]) - cam
            u_ = W / 2 + mx + f * (v @ rt) / dep
            v_ = H / 2 + my - f * (v @ up) / dep
            r_ = f * min(max(0.3 * th, 2.0), 6.0) / dep
            dr.ellipse([u_ - r_, v_ - r_ * 1.1, u_ + r_, v_ + r_ * 1.1], fill=g["NT"] + 1)
            continue
        poly = P[o]
        # clip to near plane z=0.3
        pts = []
        for a in range(3):
            p, q = poly[a], poly[(a + 1) % 3]
            if p[2] >= 0.3:
                pts.append(p)
            if (p[2] - 0.3) * (q[2] - 0.3) < 0:
                t = (0.3 - p[2]) / (q[2] - p[2])
                pts.append(p + t * (q - p))
        if len(pts) < 3:
            continue
        pts = np.array(pts)
        x, y = pts[:, 0] / pts[:, 2], pts[:, 1] / pts[:, 2]
        r2 = x * x + y * y
        s = 1 + k1 * r2 + k2 * r2 * r2
        u, v = cx + f * x * s, cy + f * y * s
        if u.max() < 0 or u.min() > W + 2 * mx or v.max() < 0 or v.min() > H + 2 * my:
            continue
        dr.polygon([(float(a), float(b)) for a, b in zip(u, v)], fill=int(idx[o]) + 1)
    return np.asarray(pim, np.int64).astype(np.int32) - 1, idx


def sky_mask(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    sk = ((b < -3) & (L > 45)) | ((L > 78) & (np.hypot(a, b) < 7))
    im = Image.fromarray((sk * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(7))
    sk = np.asarray(im) > 127
    return np.cumprod(sk, axis=0).astype(bool)  # sky connected to the top edge


def align(lab, big, W, H, mx, my):
    """Skyline alignment: shift (dx ~ yaw, dy ~ pitch) so that the first rendered building row per column matches the first non-sky row."""
    sk = sky_mask(lab)
    if sk.mean() < 0.04 or sk.mean() > 0.9:
        return None
    q = 4
    # first non-sky row per image column (sky connected to the top)
    ys = (~sk).argmax(0)
    ys = np.where(sk.all(0), H, ys)[::q].astype(float)
    cols = np.arange(0, W, q)
    bm = big >= 0
    top = np.where(bm.any(0), bm.argmax(0), 10 ** 6).astype(float)  # in canvas coords
    best = None
    for dy in range(-int(H * 0.08), int(H * 0.08) + 1, 2):
        for dx in range(-int(W * 0.05), int(W * 0.05) + 1, 4):
            ci = cols - dx + mx
            ok = (ci >= 0) & (ci < big.shape[1])
            if ok.sum() < 20:
                continue
            tr = top[ci[ok]] + dy - my  # rendered skyline in image coords
            d = np.abs(tr - ys[ok])
            use = ys[ok] < H - 6  # image has non-sky below sky in this column
            if use.sum() < 15:
                continue
            c = np.minimum(d[use], 40)
            cost = np.mean(c)
            if best is None or cost < best[0]:
                best = (cost, dx, dy)
    if best is None:
        return None
    return best[1], best[2], 1 - best[0] / 40


def process(iid, pose, dbg=False):
    g = load_geom()
    fimg = CACHE / "img" / f"{iid}.jpg"
    im = Image.open(fimg).convert("RGB")
    w0, h0 = im.size
    ow, oh = pose["width"], pose["height"]
    if abs(w0 / h0 - ow / oh) > 0.05:
        return None
    s = RW / w0
    W, H = RW, round(h0 * s)
    im = im.resize((W, H), Image.LANCZOS)
    rgb = np.asarray(im, np.float64)
    from common import ll2xy
    lon, lat = pose["computed_geometry"]["coordinates"]
    cx_, cy_ = ll2xy(lon, lat)
    hdg = pose["computed_compass_angle"]
    f0, k1, k2 = (pose["camera_parameters"] + [0, 0])[:3]
    f = f0 * max(W, H)
    # ground reference: median ground z of buildings within 25 m
    nb = np.unique(g["tb"][g["kd"].query_ball_point([cx_, cy_], 25)])
    if len(nb) == 0:
        return None
    gz = float(np.median([G["b"][b]["gz"] for b in nb]))
    cam = np.array([cx_, cy_, gz + CAMH])
    lab = rgb2lab(rgb)
    if rgb.mean() < 45:
        return {}
    pe = pitch_mod.estimate(lab[..., 0], f)
    if pe is None or pe[2] < 0.5 or abs(pe[1]) > 0.12 or abs(pe[0]) > 1.0:
        return {}
    if abs(pe[1]) > 0.012:
        im = im.rotate(math.degrees(pe[1]))
        rgb = np.asarray(im, np.float64)
        lab = rgb2lab(rgb)
    pit = math.atan(pe[0])
    mx, my = W // 8, H // 4
    big, _ = render(cam, hdg, f, k1, k2, W, H, mx=mx, my=my, pitch=pit)
    al = align(lab, big, W, H, mx, my)
    dx, dy, score = al if al is not None else (0, 0, 0.0)
    idm = big[my - dy: my - dy + H, mx - dx: mx - dx + W]
    # pixel rays
    vv, uu = np.mgrid[0:H, 0:W]
    xn, yn = (uu - dx - W / 2) / f, (vv - dy - H / 2) / f
    # (distortion ignored for ray directions: sampling error small near centre)
    fw, rt, upv = basis(hdg, pit)
    ray = xn[..., None] * rt + (-yn)[..., None] * upv + fw
    tri = idm
    valid = (tri >= 0) & (tri < g["NT"])
    tk = np.where(valid, g["tk"][np.where(valid, tri, 0)], 0)
    tbm = np.where(valid, g["tb"][np.where(valid, tri, 0)], -1)
    # erode: pixel must have same building in 4-neighbourhood
    same = np.ones_like(valid)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh = np.roll(np.roll(tbm, dy, 0), dx, 1)
        same &= sh == tbm
    wallpx = valid & (tk == 1) & same
    ys, xs = np.nonzero(wallpx)
    if len(ys) == 0:
        return {}
    ti = tri[ys, xs]
    n = g["nrm"][ti]
    d = ray[ys, xs]
    dn = np.einsum("ij,ij->i", n, d)
    v0 = g["tris"][ti, 0]
    t = np.einsum("ij,ij->i", n, v0 - cam) / np.where(np.abs(dn) < 1e-6, 1e-6, dn)
    hit = cam + d * t[:, None]
    bi = g["tb"][ti]
    gzb = np.array([G["b"][b]["gz"] for b in np.unique(bi)])
    gmap = dict(zip(np.unique(bi), gzb))
    gzp = np.array([gmap[b] for b in bi])
    ev = {b: G["b"][b]["eave"] for b in np.unique(bi)}
    ep = np.array([ev[b] for b in bi])
    hh = hit[:, 2] - gzp
    inc = np.abs(dn) / np.linalg.norm(d, axis=1)
    sel = (hh > 3.0) & (hh < ep - gzp - 0.6) & (inc > 0.3) & (t > 0)
    res = {}
    for b in np.unique(bi[sel]):
        m = sel & (bi == b)
        if m.sum() < 120:
            continue
        px = lab[ys[m], xs[m]]
        dist = float(np.median(t[m] * np.linalg.norm(d[m], axis=1)))
        res[int(b)] = dict(px=px, inc=float(inc[m].mean()), dist=dist, al=float(score))
    if dbg:
        return res, rgb, idm, (xs, ys, sel, bi)
    return res


def robust(px):
    """Lab median of facade-like pixels: drop sky, vegetation, darkest 20% (windows/shadow), brightest 3%."""
    L, a, b = px[:, 0], px[:, 1], px[:, 2]
    sky = (b < -6) & (L > 30)
    veg = (a < -8) & (b > 8)
    m = ~(sky | veg)
    if m.sum() < 80:
        return None
    px = px[m]
    lo, hi = np.percentile(px[:, 0], [20, 97])
    px = px[(px[:, 0] >= lo) & (px[:, 0] <= hi)]
    med = np.median(px, 0)
    # outliers by chroma distance
    dd = np.linalg.norm(px[:, 1:] - med[1:], axis=1)
    px2 = px[dd < max(10, np.percentile(dd, 70))]
    med = np.median(px2, 0)
    spread = float(np.linalg.norm(px2.std(0)))
    return dict(lab=[float(x) for x in med], n=int(len(px2)), spread=spread)


def main():
    pose = json.load(open(CACHE / "imgs_pose.json"))
    d = CACHE / "imgres"
    d.mkdir(exist_ok=True)
    todo = [i for i in pose if (CACHE / "img" / f"{i}.jpg").exists() and not (d / f"{i}.json").exists()]
    only = set(json.load(open(sys.argv[1]))) if len(sys.argv) > 1 else None
    if only:
        todo = [i for i in todo if i in only]
    print("todo", len(todo), flush=True)
    for n, i in enumerate(todo):
        try:
            r = process(i, pose[i])
        except Exception as e:
            print("err", i, repr(e)[:100], flush=True)
            r = None
        out = {}
        for b, v in (r or {}).items():
            rb = robust(v["px"])
            if rb:
                rb.update(inc=v["inc"], dist=v["dist"], al=v["al"])
                out[str(b)] = rb
        json.dump(out if r is not None else {"_skip": 1}, open(d / f"{i}.json", "w"))
        if n % 200 == 0:
            print(n, len(todo), flush=True)


if __name__ == "__main__":
    main()
