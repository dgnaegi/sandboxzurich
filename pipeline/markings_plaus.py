"""Visual plausibility sheets: game top-down (from built tile GLBs, ground layer asphalt 34 + markings 39 + decals) next to SWISSIMAGE 0.25 m (data/raw/ortho_025, swisstopo OGD)
for 60 x 60 m cells. Works per zone (pipeline/overrides/zones.json).
usage: .venv/bin/python pipeline/markings_plaus.py --zone 1 [--n 36] [--seed 1] [--tiles web/public/tiles] [--out research/markings_plaus/z1_before] [--cells x,y;x,y]
Writes <out>_<k>.jpg sheets (3x3 pairs, <=1600 px wide) and <out>_cells.tsv (cell centres, in order)."""
import sys, json, math, argparse, random, struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, Point
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_markings as AM
import markings_ortho25 as M25
from scipy import ndimage as ndi

CELL, PX = 60, 4
COL = {2: (245, 245, 240), 3: (255, 190, 0), 4: (60, 90, 230), 5: (200, 40, 30), 6: (40, 150, 60), 7: (40, 40, 44)}
DEC = {0: (255, 190, 0), 3: (255, 255, 255), 4: (255, 255, 255), 5: (255, 190, 0), 6: (255, 255, 255), 7: (255, 255, 255), 8: (255, 255, 255), 9: (255, 255, 255), 10: (255, 255, 255), 11: (255, 255, 255), 12: (255, 255, 255)}
_cache = {}


def zone_polys(zid):
    z = [q for q in json.load(open(R / "pipeline/overrides/zones.json"))["zones"] if q["id"] == zid][0]
    return [Polygon(p) for p in z["polys"]]


def tile(tdir, tx, ty):
    k = (str(tdir), tx, ty)
    if k not in _cache:
        f = Path(tdir) / f"t_{tx}_{ty}.glb"
        g = AM.read_ground(f) if f.exists() else None
        dec = []
        jf = R / "web/public/tiles" / f"t_{tx}_{ty}.json"
        if jf.exists():
            dec = json.load(open(jf)).get("decals", [])
        _cache[k] = (g, dec)
    return _cache[k]


def render_game(tdir, cx, cy, base=None):
    x0, y1 = cx - CELL / 2, cy + CELL / 2
    n = CELL * PX
    im = base if base is not None else Image.new("RGB", (n, n), (96, 112, 84)); d = ImageDraw.Draw(im)
    lay_items = {0: [], 1: [], 2: [], 3: []}
    for tx in range(math.floor((cx - CELL / 2) / 200), math.floor((cx + CELL / 2) / 200) + 1):
        for ty in range(math.floor((cy - CELL / 2) / 200), math.floor((cy + CELL / 2) / 200) + 1):
            g, dec = tile(tdir, tx, ty)
            if g is None:
                continue
            pos, col, lay, idx = g
            X, Y = (pos[:, 0] - x0) * PX, (y1 + pos[:, 2]) * PX
            T = idx.reshape(-1, 3)
            xs = X[T]; ys = Y[T]
            m = (xs.max(1) > -2) & (xs.min(1) < n + 2) & (ys.max(1) > -2) & (ys.min(1) < n + 2)
            for t in T[m]:
                L = int(lay[t[0]])
                poly = [(X[i], Y[i]) for i in t]
                if L == 34:
                    lay_items[0].append(((86, 86, 92), poly))
                elif L == 39:
                    k = AM.CLS.get(tuple(int(v) for v in col[t[0], :3]))
                    if k is None:
                        continue
                    lay_items[1].append((COL[k], poly) if k != 7 else ((50, 50, 56), poly))
                elif L == 33:
                    lay_items[3].append(((150, 146, 132), poly))
            for r in dec:
                x, y, z, h, kind = r[:5]
                if abs(x - cx) < CELL / 2 + 3 and abs(y - cy) < CELL / 2 + 3 and kind in DEC:
                    lay_items[2].append((DEC[kind], (kind, (x - x0) * PX, (y1 - y) * PX, h)))
    ov = ImageDraw.Draw(im, 'RGBA') if base is not None else None
    if base is None:
        for c, poly in lay_items[3] + lay_items[0]:
            d.polygon(poly, fill=c)
    for c, poly in lay_items[1]:
        if base is None:
            d.polygon(poly, fill=c)
        elif c != (50, 50, 56):
            ov.polygon(poly, fill=(255, 0, 255, 150) if c[2] > 200 else (255, 0, 0, 150))
    for c, (kind, px, py, h) in lay_items[2]:
        L = {4: 7, 7: 7, 8: 7, 9: 7, 10: 7, 5: 8, 0: 5, 3: 4, 6: 4, 11: 4, 12: 6}.get(kind, 5) * PX / 2 * 1.2
        w = 0.5 * PX
        ux, uy = math.sin(h), math.cos(h)   # heading -> screen (guess; north-up, y flipped)
        d.ellipse([px - w, py - w, px + w, py + w], outline=c, width=2)
        d.line([(px - ux * L, py + uy * L), (px + ux * L, py - uy * L)], fill=c, width=2)
        d.text((px + 4, py + 4), {0: "bike", 5: "BUS", 12: "STOP", 3: "30", 6: "30"}.get(kind, ""), fill=c)
    return im


def render_ortho(cx, cy):
    TILE = 250.0
    n = CELL * PX
    out = Image.new("RGB", (n, n), (0, 0, 0))
    x0, y1 = cx - CELL / 2, cy + CELL / 2
    for ix in range(math.floor(x0 / TILE), math.floor((x0 + CELL) / TILE) + 1):
        for iy in range(math.floor((y1 - CELL) / TILE), math.floor(y1 / TILE) + 1):
            f = AM.R / "data/raw/ortho_025" / f"o_{ix}_{iy}.jpg"
            if not f.exists():
                continue
            im = Image.open(f).convert("RGB")
            s = im.size[0] / TILE
            bx0, by1 = ix * TILE, (iy + 1) * TILE
            wx0, wx1 = max(x0, bx0), min(x0 + CELL, bx0 + TILE)      # intersection of cell and box (local m)
            wy1, wy0 = min(y1, by1), max(y1 - CELL, by1 - TILE)
            if wx1 <= wx0 or wy1 <= wy0:
                continue
            crop = (round((wx0 - bx0) * s), round((by1 - wy1) * s), round((wx1 - bx0) * s), round((by1 - wy0) * s))
            c = im.crop(crop).resize((round((wx1 - wx0) * PX), round((wy1 - wy0) * PX)), Image.BILINEAR)
            out.paste(c, (round((wx0 - x0) * PX), round((y1 - wy1) * PX)))
    return out


def analyze(game, ortho):
    """ortho paint detection vs game paint. game/ortho: PIL (n,n) from render_game (plain) / render_ortho. Returns metrics dict + diff image.
    white = thin bright ridge on road (0.25 m px, 1 px = 0.25 m); yellow = M25.yellow mask. Both restricted to the game carriageway dilated 1.2 m."""
    G = np.asarray(game).astype(int); O = np.asarray(ortho).astype(float)
    near = lambda c, t=14: (np.abs(G - c).sum(2) < t)
    gw, gy = near((245, 245, 240)), near((255, 190, 0))
    road = near((86, 86, 92)) | gw | gy | near((50, 50, 56)) | near((60, 90, 230))
    road = ndi.binary_dilation(road, iterations=5)
    gray = O.mean(2)
    ridge = ndi.gaussian_filter(gray, 0.8) - ndi.gaussian_filter(gray, 4)
    yb = (O[..., 0] + O[..., 1]) / 2 - O[..., 2]
    ym, _, _ = M25.yellow(O)
    ym = ndi.binary_opening(ym, np.ones((2, 2)))
    wm = (ridge > 20) & (gray > 105) & (yb < 22) & road & ~ndi.binary_dilation(ym, iterations=2)
    wm &= ~ndi.binary_opening(wm, np.ones((4, 4)))             # thin only: drops cars / roofs / zebras / blobs
    wm = ndi.binary_opening(wm, np.ones((1, 1)))
    lab, k = ndi.label(ndi.binary_closing(wm, np.ones((3, 3))))
    if k:
        sz = ndi.sum(wm, lab, range(1, k + 1)); keep = np.isin(lab, 1 + np.nonzero(sz >= 14)[0]); wm &= keep
    dg = ndi.distance_transform_edt(~gw)                       # px distance to game white
    do = ndi.distance_transform_edt(~wm)
    dgy = ndi.distance_transform_edt(~gy)
    oy = ym & road
    doy = ndi.distance_transform_edt(~oy)
    m = dict(o_white=int(wm.sum()), g_white=int(gw.sum()), o_white_unexpl=int((wm & (dg > 3)).sum()), g_white_unsup=int((gw & (do > 3)).sum()),
             o_yel=int(oy.sum()), g_yel=int(gy.sum()), o_yel_unexpl=int((oy & (dgy > 5)).sum()), g_yel_unsup=int((gy & (doy > 5)).sum()))
    img = Image.fromarray((O * 0.55).astype(np.uint8)); a = np.asarray(img).copy()
    a[wm & (dg <= 3)] = (0, 255, 255); a[wm & (dg > 3)] = (0, 255, 0)
    a[oy & (dgy <= 5)] = (0, 200, 255); a[oy & (dgy > 5)] = (160, 255, 0)
    a[gw & (do > 3)] = (255, 0, 255); a[gy & (doy > 5)] = (255, 0, 0)
    return m, Image.fromarray(a)


def candidates(zid, tdir):
    pl = zone_polys(zid)
    xs = [p.bounds for p in pl]
    res = []
    for p in pl:
        b = p.bounds
        for i in range(int(b[0] // CELL), int(b[2] // CELL) + 1):
            for j in range(int(b[1] // CELL), int(b[3] // CELL) + 1):
                cx, cy = i * CELL + CELL / 2, j * CELL + CELL / 2
                if p.contains(Point(cx, cy)):
                    res.append((cx, cy))
    out = []
    for cx, cy in res:
        im = render_game(tdir, cx, cy)
        a = np.asarray(im).astype(int)
        road = ((np.abs(a - (86, 86, 92)).sum(2) < 12).mean() + (a[..., 0] > 200).mean())
        if road > 0.18 and (np.asarray(render_ortho(cx, cy)).sum(2) == 0).mean() < 0.02:
            out.append((cx, cy, road))
    return out


def sheet_big(tdir, cells, out, per=4):
    """pairs game | ortho with game paint outlined over the ortho, 8 px/m (60 m = 480 px), 2 cells per row"""
    global PX
    PX = 8
    paths = []; n = CELL * PX
    for k in range(0, len(cells), per):
        chunk = cells[k:k + per]
        S = Image.new("RGB", (2 * (2 * n + 6) + 6, math.ceil(len(chunk) / 2) * (n + 14)), (255, 255, 255)); d = ImageDraw.Draw(S)
        for q, (cx, cy) in enumerate(chunk):
            r, c = divmod(q, 2); ox, oy = c * (2 * n + 6) + 4, r * (n + 14)
            S.paste(render_game(tdir, cx, cy), (ox, oy + 14)); S.paste(render_ortho(cx, cy), (ox + n, oy + 14))
            for gx in range(10, CELL, 10):
                for gy in range(10, CELL, 10):
                    for off in (0, n):
                        d.point([(ox + off + gx * PX + i, oy + 14 + gy * PX) for i in (-1, 0, 1)] + [(ox + off + gx * PX, oy + 14 + gy * PX + i) for i in (-1, 1)], fill=(255, 0, 255))
            d.text((ox, oy), f"#{k + q} {cx:.0f},{cy:.0f}  game | ortho (N up, 60 m, dots every 10 m)", fill=(0, 0, 0))
        S = S.resize((1600, int(S.height * 1600 / S.width))); p = f"{out}_{k // per}.jpg"; S.save(p, quality=88); paths.append(p)
    PX = 4
    return paths


def sheet(tdir, cells, out, per=9):
    """2-panel sheets (game | ortho with the game paint filled over it), 4 px/m, 3 cells per row; metrics from analyze() go to <out>_metrics.tsv"""
    paths, rows_m = [], []
    n = CELL * PX
    for k in range(0, len(cells), per):
        chunk = cells[k:k + per]
        S = Image.new("RGB", (3 * (2 * n + 4) + 8, math.ceil(len(chunk) / 3) * (n + 14)), (255, 255, 255)); d = ImageDraw.Draw(S)
        for q, (cx, cy) in enumerate(chunk):
            r, c = divmod(q, 3)
            ox, oy = c * (2 * n + 4) + 4, r * (n + 14)
            gi, orx = render_game(tdir, cx, cy), render_ortho(cx, cy)
            rows_m.append((k + q, cx, cy, analyze(gi, orx)[0]))
            S.paste(gi, (ox, oy + 14)); S.paste(render_game(tdir, cx, cy, base=orx.copy()), (ox + n, oy + 14))
            d.text((ox, oy), f"#{k + q} {cx:.0f},{cy:.0f}  game | ortho + game paint (N up, 60 m)", fill=(0, 0, 0))
        S = S.resize((min(S.width, 1600), int(S.height * min(S.width, 1600) / S.width)))
        p = f"{out}_{k // per}.jpg"; S.save(p, quality=88); paths.append(p)
    with open(out + "_metrics.tsv", "w") as f:
        f.write("idx\tx\ty\t" + "\t".join(rows_m[0][3].keys()) + "\n")
        for i, x, y, m in rows_m:
            f.write(f"{i}\t{x:.0f}\t{y:.0f}\t" + "\t".join(str(v) for v in m.values()) + "\n")
    return paths


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--zone", type=int, required=True); ap.add_argument("--n", type=int, default=36); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tiles", default=str(R / "data/build/tiles_raw")); ap.add_argument("--out", default=None); ap.add_argument("--cells", default=None); ap.add_argument("--big", action="store_true")
    a = ap.parse_args()
    out = a.out or str(R / f"research/markings_plaus/z{a.zone}_before")
    if a.cells:
        cells = [tuple(map(float, c.split(","))) for c in a.cells.split(";")]
    else:
        cand = candidates(a.zone, a.tiles); print(len(cand), "candidate cells")
        random.Random(a.seed).shuffle(cand)
        cells = [(c[0], c[1]) for c in cand[:a.n]]
    open(out + "_cells.tsv", "w").write("\n".join(f"{i}\t{c[0]:.0f}\t{c[1]:.0f}" for i, c in enumerate(cells)) + "\n")
    print((sheet_big if a.big else sheet)(a.tiles, cells, out))
