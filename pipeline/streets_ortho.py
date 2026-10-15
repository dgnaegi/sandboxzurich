"""Coloured road surfaces measured from the swisstopo SWISSIMAGE mosaic (0.5 m/px, data/raw/ortho_wms, see ortho_roofs.py).
red_surfaces(tb, roads) -> shapely geometry of red-coloured asphalt (Velofurten, Velostreifen) inside the road polygon.
Cars (small red blobs) and roofs (outside `roads`) are excluded. Source: swisstopo OGD (free use with credit)."""
import numpy as np
import shapely
from shapely.geometry import box

import ortho_roofs as OR

MIN_AREA = 9.0   # m2; a red car is ~8 m2 and compact
MIN_SIDE = 1.1   # m


def _mosaic(x0, y0, x1, y1):
    """RGB array (rows north->south) for the bbox at 0.5 m/px (None if tiles missing)."""
    step = 0.5
    xs, ys = np.arange(x0 + step / 2, x1, step), np.arange(y1 - step / 2, y0, -step)
    out = np.zeros((len(ys), len(xs), 3), np.uint8)
    ok = False
    for iy in range(int(np.floor(y0 / OR.TILE)), int(np.floor(y1 / OR.TILE)) + 1):
        for ix in range(int(np.floor(x0 / OR.TILE)), int(np.floor(x1 / OR.TILE)) + 1):
            im = OR._tile(ix, iy)
            if im is None:
                continue
            ci = np.where((xs >= ix * OR.TILE) & (xs < (ix + 1) * OR.TILE))[0]
            ri = np.where((ys >= iy * OR.TILE) & (ys < (iy + 1) * OR.TILE))[0]
            if not len(ci) or not len(ri):
                continue
            c = np.clip(((xs[ci] - ix * OR.TILE) * OR.PX / OR.TILE).astype(int), 0, OR.PX - 1)
            r = np.clip((((iy + 1) * OR.TILE - ys[ri]) * OR.PX / OR.TILE).astype(int), 0, OR.PX - 1)
            out[np.ix_(ri, ci)] = im[np.ix_(r, c)]
            ok = True
    return (out, xs, ys) if ok else None


def red_mask(rgb):
    a = rgb.astype(int)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    return (R > G + 32) & (R > B + 38) & (R > 105) & (G > 45) & (R < 235)


def red_surfaces(tb, roads, debug=None):
    x0, y0, x1, y1 = tb.bounds
    m = _mosaic(x0, y0, x1, y1)
    if m is None or roads.is_empty:
        return None
    rgb, xs, ys = m
    mk = red_mask(rgb)
    X, Y = np.meshgrid(xs, ys)
    mk &= shapely.contains_xy(roads.buffer(-0.2), X, Y)
    if debug:
        from PIL import Image
        im = rgb.copy(); im[mk] = (255, 0, 255); Image.fromarray(im).save(debug)
    if mk.sum() < 20:
        return None
    r, c = np.nonzero(mk)
    px = shapely.box(xs[c] - 0.25, ys[r] - 0.25, xs[c] + 0.25, ys[r] + 0.25)
    u = shapely.union_all(px).buffer(0.35).buffer(-0.3)  # close shadow gaps / jpeg noise
    keep = []
    for g in shapely.get_parts(u):
        if g.geom_type != "Polygon" or g.area < MIN_AREA:
            continue
        mrr = g.minimum_rotated_rectangle
        e = np.asarray(mrr.exterior.coords)
        sides = sorted([np.hypot(*(e[1] - e[0])), np.hypot(*(e[2] - e[1]))])
        if sides[0] < MIN_SIDE or (g.area < 14 and sides[1] < 6.5):
            continue
        keep.append(g.simplify(0.15))
    return shapely.union_all(keep).intersection(roads).intersection(tb) if keep else None
