"""Before/after sheet of the lines from built tile meshes (ground layers only): top-down 50 m crop + low camera view along the street.
usage: .venv/bin/python pipeline/lines_cmp.py <dir_before> <dir_after> -> preview/lines_cmp.jpg  (dirs hold t_<ix>_<iy>.glb)"""
import sys, pickle, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_markings as AM

SPOTS = [("Badenerstrasse", 3, -6), ("Hardstrasse", 1, 2), ("Langstrasse", 4, -3), ("Birmensdorferstrasse", -1, -8)]
COL = {2: (240, 240, 235), 3: (246, 200, 30)}


def tris(d, ix, iy):
    g = AM.read_ground(d / f"t_{ix}_{iy}.glb")
    pos, col, lay, idx = g
    T = idx.reshape(-1, 3)
    P = np.stack([pos[:, 0], -pos[:, 2], pos[:, 1]], axis=1).astype(np.float64)   # x, y(north), z(up)
    out = []
    for t in T:
        L = int(lay[t[0]])
        if L == 34:
            out.append((0, (88, 88, 94), P[t]))
        elif L == 39:
            k = AM.CLS.get(tuple(int(v) for v in col[t[0], :3]))
            out.append((1, COL[k], P[t]) if k in COL else (0, (110, 110, 105), P[t]))
        else:
            out.append((-1, (128, 138, 118), P[t]))
    return out


def top(tr, cx, cy, half=25, px=8):
    n = int(2 * half * px); im = Image.new("RGB", (n, n), (60, 60, 60)); d = ImageDraw.Draw(im)
    for lay, c, p in sorted(tr, key=lambda a: a[0]):
        if abs(p[:, 0].mean() - cx) > half + 20 or abs(p[:, 1].mean() - cy) > half + 20:
            continue
        d.polygon([((x - cx + half) * px, (cy + half - y) * px) for x, y, z in p], fill=c)
    return im


def persp(tr, cx, cy, yaw, back=22, h=2.2, W=640, Hh=360, f=420):
    ex, ey = cx - math.sin(yaw) * back, cy - math.cos(yaw) * back
    ez = float(np.median([p[:, 2].mean() for l, c, p in tr if l == 0 and abs(p[:, 0].mean() - ex) < 15 and abs(p[:, 1].mean() - ey) < 15] or [0])) + h
    fx, fy = math.sin(yaw), math.cos(yaw); rx, ry = fy, -fx
    items = []
    for lay, c, p in tr:
        m = p.mean(axis=0)
        dx, dy = m[0] - ex, m[1] - ey
        fwd = dx * fx + dy * fy
        if fwd < 2 or fwd > 90 or abs(dx * rx + dy * ry) > fwd * 1.6 + 10:
            continue
        pts = []
        for x, y, z in p:
            dx, dy, dz = x - ex, y - ey, z - ez
            zf = dx * fx + dy * fy
            if zf < 0.3:
                pts = None; break
            pts.append((W / 2 + f * (dx * rx + dy * ry) / zf, Hh * 0.45 - f * dz / zf))
        if pts:
            items.append((lay, -fwd, c, pts))
    im = Image.new("RGB", (W, Hh), (170, 190, 215)); d = ImageDraw.Draw(im)
    for lay, nd, c, pts in sorted(items, key=lambda a: (a[0], a[1])):
        d.polygon(pts, fill=c)
    return im


def main():
    A, B = Path(sys.argv[1]), Path(sys.argv[2])
    S = pickle.load(open(R / "data/build/lines_S.pkl", "rb"))
    import streets
    streets.junction_gaps(S)
    rows = []
    for nm, ix, iy in SPOTS:
        best = None
        for w in S["ways"]:
            if w["name"] != nm or w["w"] < 5.5 or w["line"].length < 40:
                continue
            for s in np.arange(20, w["line"].length - 20, 10):
                p = w["line"].interpolate(s)
                if ix * 200 + 35 < p.x < (ix + 1) * 200 - 35 and iy * 200 + 35 < p.y < (iy + 1) * 200 - 35:
                    q = w["line"].interpolate(s + 5); yaw = math.atan2(q.x - p.x, q.y - p.y)
                    # prefer spots with long straight run (no junction gap) around
                    sc = -sum(1 for g0, g1 in w["gaps"] if abs((g0 + g1) / 2 - s) < 40)
                    if best is None or sc > best[0]:
                        best = (sc, p.x, p.y, yaw)
        if best is None:
            continue
        _, x, y, yaw = best
        ims = []
        for d in (A, B):
            tr = tris(d, ix, iy)
            ims.append((top(tr, x, y), persp(tr, x, y, yaw)))
        rows.append((nm, ims))
    W = 400 + 640 + 400 + 640
    sheet = Image.new("RGB", (400 * 2 + 640 * 2, 360 * len(rows)), (30, 30, 30))
    for r, (nm, ims) in enumerate(rows):
        x0 = 0
        for (t, p) in ims:
            sheet.paste(t.resize((400, 400)).crop((0, 20, 400, 380)), (x0, r * 360)); x0 += 400
            sheet.paste(p, (x0, r * 360)); x0 += 640
        ImageDraw.Draw(sheet).text((4, r * 360 + 4), nm + "  (links: vorher, rechts: nachher)", fill=(255, 255, 255))
    sheet.save(R / "preview/lines_cmp.jpg", quality=82)
    print("rows", [r[0] for r in rows])


main()
