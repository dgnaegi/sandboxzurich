"""Rooftop furniture per building: dormers, roof windows, solar panels, lift/vent boxes, terraces, antennas, green roofs.

Sources (see research/rooftops.md):
  * swissBUILDINGS3D roof planes (slope, azimuth, height) -> dormers / roof windows on steep planes, terraces on lower flat planes
  * nDSM (swissSURFACE3D minus swissALTI3D, 1 m, data/build/ndsm) -> structures > 0.8 m above the flat-roof level
  * SWISSIMAGE (data/raw/ortho_wms, 0.5 m) -> green roof (green), photovoltaics (dark blue), tree overhang (ignored)
analyse(b) -> rows [t, x, y, z, w, d, h, azimuth, slope, colour] (t 0 box, 1 gable prism), flags for facade.py.
Runtime: web/src/world/rooftops.ts. Origin of an instance: bottom centre; azimuth = downslope direction (rad, map frame),
slope = tilt (rad). Everything deterministic (hash of the building id).
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np
import shapely
from scipy import ndimage
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ortho_roofs  # noqa: E402
from config import ROOT  # noqa: E402
E0, N0 = 2681400.0, 1248700.0

# colour palette index -> runtime table in rooftops.ts
PV, GLASS, CONC, METAL, DWALL, ZINC, RED, RAIL, PLANT, MAST, WOOD, DWALL2 = range(12)
MAX_ROWS = 60  # per building

def _h(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


_dsm = {}


def _dsm_tile(e, n):
    k = (e, n)
    if k not in _dsm:
        import tifffile
        f = next((ROOT / "data/raw/surface3d").glob(f"swisssurface3d-raster_*_{e}-{n}_*.tif"), None)
        _dsm[k] = tifffile.imread(f).astype(np.float32) if f else None
    return _dsm[k]


def ndsm_at(xs, ys):
    """swissSURFACE3D height (0.5 m raster) in local z (m above 408) at local points; NaN where missing.
    Building footprints are NaN in data/build/ndsm, so the raw DSM is read and compared with the sb3d roof plane."""
    E, N = xs + E0, ys + N0
    out = np.full(len(xs), np.nan, np.float32)
    te, tn = np.floor(E / 1000).astype(int), np.floor(N / 1000).astype(int)
    for k in set(zip(te.tolist(), tn.tolist())):
        a = _dsm_tile(*k)
        if a is None:
            continue
        m = (te == k[0]) & (tn == k[1])
        c = np.clip(((E[m] - k[0] * 1000) * 2).astype(int), 0, a.shape[1] - 1)
        r = np.clip(((k[1] * 1000 + 1000 - N[m]) * 2).astype(int), 0, a.shape[0] - 1)
        v = a[r, c] - 408.0
        v[(v < -50) | (v > 600)] = np.nan
        out[m] = v
    return out


def ortho_at(xs, ys):
    """RGB (float32 Nx3) from SWISSIMAGE at local points; NaN outside the mosaic."""
    T, PXn = ortho_roofs.TILE, ortho_roofs.PX
    ix, iy = np.floor(xs / T).astype(int), np.floor(ys / T).astype(int)
    out = np.full((len(xs), 3), np.nan, np.float32)
    for k in set(zip(ix.tolist(), iy.tolist())):
        im = ortho_roofs._tile(*k)
        if im is None:
            continue
        m = (ix == k[0]) & (iy == k[1])
        c = np.clip(((xs[m] - k[0] * T) * PXn / T).astype(int), 0, PXn - 1)
        r = np.clip((((k[1] + 1) * T - ys[m]) * PXn / T).astype(int), 0, PXn - 1)
        out[m] = im[r, c]
    return out


def classify(rgb):
    """-> (green, pv, dark) boolean masks for SWISSIMAGE pixels (calibrated on Zuerich roofs, research/rooftops.md)."""
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    lum = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    green = (g > r + 8) & (g > b + 16) & (lum > 45)  # vegetation (teal/blue-green paint excluded)
    pv = (b > r + 12) & (b >= g - 2) & (lum < 105) & ~green
    return green, pv, lum < 70


def plane_info(pts):
    """pts Nx3 ring -> (poly, normal up, slope rad, downslope azimuth rad, true area) or None."""
    if len(pts) < 3:
        return None
    if np.allclose(pts[0], pts[-1]):
        pts = pts[:-1]
    xy = pts[:, :2].astype(float)
    poly = Polygon(xy)
    if not poly.is_valid:
        poly = poly.buffer(0)
    if poly.is_empty or poly.geom_type != "Polygon" or poly.area < 4:
        return None
    n = np.zeros(3)
    for i in range(len(pts)):  # Newell
        p, q = pts[i].astype(float), pts[(i + 1) % len(pts)].astype(float)
        n += [(p[1] - q[1]) * (p[2] + q[2]), (p[2] - q[2]) * (p[0] + q[0]), (p[0] - q[0]) * (p[1] + q[1])]
    L = np.linalg.norm(n)
    if L < 1e-6:
        return None
    n /= L
    if n[2] < 0:
        n = -n
    s = math.acos(min(1.0, n[2]))
    az = math.atan2(-n[1], -n[0]) if s > 0.02 else 0.0
    return poly, n, pts.astype(float), s, az, poly.area / max(n[2], 0.2)


def _z_at(n, c, x, y):
    return c[2] - (n[0] * (x - c[0]) + n[1] * (y - c[1])) / max(n[2], 1e-3)


def _grid(poly, step, shrink):
    g = poly.buffer(-shrink)
    if g.is_empty:
        return None, None, None
    x0, y0, x1, y1 = g.bounds
    xs, ys = np.meshgrid(np.arange(x0 + step / 2, x1, step), np.arange(y0 + step / 2, y1, step))
    inside = shapely.contains_xy(g, xs.ravel(), ys.ravel())
    return xs, ys, inside.reshape(xs.shape)


def analyse(b):
    """b: building dict (polys local metres). -> (rows, flags). flags: real_units (nDSM-derived units placed),
    green (flat roof mostly vegetated)."""
    planes = []
    for kind, a in b["polys"]:
        if kind == 2:
            p = plane_info(np.asarray(a))
            if p:
                planes.append(p)
    if not planes:
        return [], {}
    bid = b["id"]
    zmax = max(p[2][:, 2].max() for p in planes)
    rows, flags = [], {"real_units": False, "green": False}
    flat_area = green_area = 0.0
    n_term = 0
    for pi, (poly, n, pts, s, az, area) in enumerate(planes):
        if len(rows) >= MAX_ROWS:
            break
        seed = _h(f"{bid}/{pi}")
        c = pts.mean(0)
        zc = float(pts[:, 2].mean())
        if s < 0.35:  # flat (< 20 deg)
            _flat(poly, n, c, bid, seed, zmax, zc, area, rows, flags, n_term)
            flat_area += poly.area
            flags["_ga"] = flags.get("_ga", 0.0) + flags.pop("_g", 0.0)
        elif s > 0.45 and poly.area > 12:
            _pitched(poly, n, c, s, az, seed, area, rows)
    ga = flags.pop("_ga", 0.0)
    if flat_area > 40 and ga / flat_area > 0.45:
        flags["green"] = True
    return rows, flags


def _frame_angle(poly):
    """Dominant building axis (rad) from the minimum rotated rectangle."""
    r = shapely.minimum_rotated_rectangle(poly)
    if r.geom_type != "Polygon":
        return 0.0
    cs = np.asarray(r.exterior.coords)
    e = cs[1] - cs[0]
    if np.hypot(*e) < np.hypot(*(cs[2] - cs[1])):
        e = cs[2] - cs[1]
    return math.atan2(e[1], e[0])


def _flat(poly, n, c, bid, seed, zmax, zc, area, rows, flags, n_term):
    xs, ys, ins = _grid(poly, 1.0, 1.0)
    if xs is None or ins.sum() < 6:
        return
    px, py = xs[ins], ys[ins]
    nd = ndsm_at(px, py) - np.array([_z_at(n, c, x, y) for x, y in zip(px, py)], np.float32)  # DSM minus sb3d roof plane
    ok = np.isfinite(nd)
    # ortho-based classes on a 0.5 m grid
    ox, oy, oins = _grid(poly, 0.5, 0.4)
    rgb = ortho_at(ox[oins], oy[oins]) if ox is not None and oins.sum() else np.zeros((0, 3), np.float32)
    good = np.isfinite(rgb[:, 0]) if len(rgb) else np.zeros(0, bool)
    green = pv = None
    if good.sum() > 8:
        gm, pm, _ = classify(rgb[good])
        green, pv = gm, pm
    base = float(np.median(nd[ok])) if ok.sum() >= 6 else None
    spread = float(np.percentile(nd[ok], 85) - base) if base is not None else 9.0
    # green roof: vegetated and flat on the nDSM (trees overhanging a roof stand much higher)
    if green is not None and green.mean() > 0.55 and spread < 0.9 and poly.area > 25:
        flags["_g"] = poly.area
    ang = _frame_angle(poly)
    ca, sa = math.cos(ang), math.sin(ang)
    # structures: nDSM clusters well above the roof level
    if base is not None and ok.sum() >= 12 and flags.get("_g") is None and poly.area > 40:
        grid = np.full(xs.shape, np.nan, np.float32)
        grid[ins] = np.where(ok, nd - base, np.nan)
        m = np.nan_to_num(grid, nan=0) > 0.8
        lab, k = ndimage.label(m, structure=np.ones((3, 3)))
        placed = 0
        for i in range(1, k + 1):
            if placed >= 8:
                break
            sel = lab == i
            cnt = int(sel.sum())
            if cnt > 70:
                continue
            cx, cy = xs[sel], ys[sel]
            # not a tree crown: skip clusters mostly green on the orthophoto
            if green is not None:
                gg, _, _ = classify(ortho_at(cx, cy))
                if gg.mean() > 0.5:
                    continue
            hh = float(np.percentile(grid[sel], 90))
            if hh < 0.8 or hh > 9:
                continue
            u = (cx - cx.mean()) * ca + (cy - cy.mean()) * sa
            v = -(cx - cx.mean()) * sa + (cy - cy.mean()) * ca
            w, d = float(u.max() - u.min()) + 1.0, float(v.max() - v.min()) + 1.0
            mx, my = float(cx.mean()), float(cy.mean())
            z = _z_at(n, c, mx, my)
            if cnt <= 2 and hh > 2.2:  # thin spike: mast
                rows.append([0, mx, my, z, 0.12, 0.12, min(hh, 7.0), ang, 0.0, MAST])
            elif hh > 2.1 and cnt >= 4:  # stair / lift tower
                rows.append([0, mx, my, z, min(w, 8), min(d, 8), min(hh, 4.0), ang, 0.0, CONC])
                rows.append([0, mx, my, z + min(hh, 4.0), min(w, 8) + 0.2, min(d, 8) + 0.2, 0.15, ang, 0.0, METAL])  # parapet cap
            else:  # ventilation / HVAC box
                rows.append([0, mx, my, z, min(w, 6), min(d, 6), min(hh, 2.0), ang, 0.0, METAL if (seed + i) % 3 else CONC])
            placed += 1
            n_term += 1
        if placed:
            flags["real_units"] = True
    # photovoltaics on the flat roof: tilted south-facing rows
    if pv is not None and 0.12 < pv.mean() < 0.85 and poly.area > 30 and flags.get("_g") is None:
        _pv_flat(ox[oins][good][pv], oy[oins][good][pv], n, c, ang, rows)
    # roof terrace: lower flat part of a taller building, only some of them
    if (zmax - zc > 2.8 and 25 < poly.area < 160 and flags.get("_g") is None and seed % 5 < 2 and (pv is None or pv.mean() < 0.1)):
        _terrace(poly, n, c, seed, rows)
    # parapet-less far flat roofs get a lone antenna now and then
    if zmax - zc < 0.5 and zc > 14 and poly.area > 120 and seed % 23 == 0 and len(rows) < MAX_ROWS:
        q = poly.representative_point()
        rows.append([0, q.x, q.y, _z_at(n, c, q.x, q.y), 0.1, 0.1, 4 + seed % 4, ang, 0.0, MAST])


def _pv_flat(px, py, n, c, ang, rows):
    if len(px) < 12:
        return
    ca, sa = math.cos(ang), math.sin(ang)
    u, v = px * ca + py * sa, -px * sa + py * ca
    # connected blobs on a 1 m grid in the building frame
    iu, iv = np.floor(u - u.min()).astype(int), np.floor(v - v.min()).astype(int)
    img = np.zeros((iu.max() + 2, iv.max() + 2), bool)
    img[iu, iv] = True
    img = ndimage.binary_closing(img, iterations=1)
    lab, k = ndimage.label(img)
    south = -math.pi / 2  # panels face south: downslope azimuth = south
    for i in range(1, k + 1):
        sel = np.argwhere(lab == i)
        if len(sel) < 8:
            continue
        u0, u1 = sel[:, 0].min() + u.min(), sel[:, 0].max() + 1 + u.min()
        v0, v1 = sel[:, 1].min() + v.min(), sel[:, 1].max() + 1 + v.min()
        # rows run along the building axis whose "south" side is closer to south
        along_u = abs(math.cos(ang + south)) < 0.707  # contour direction is u when downslope is ~ +-v
        steps = np.arange((v0 if along_u else u0) + 0.9, (v1 if along_u else u1) - 0.9, 2.3)
        for s0 in steps[:14]:
            if along_u:
                cu, cv, w = (u0 + u1) / 2, s0, u1 - u0
            else:
                cu, cv, w = s0, (v0 + v1) / 2, v1 - v0
            x, y = cu * ca - cv * sa, cu * sa + cv * ca
            rows.append([0, x, y, _z_at(n, c, x, y) + 0.25, max(1.0, w - 0.4), 1.5, 0.05, south, 0.2, PV])
            if len(rows) >= MAX_ROWS:
                return


def _terrace(poly, n, c, seed, rows):
    g = poly.buffer(-0.12)
    if g.is_empty or g.geom_type != "Polygon":
        return
    co = np.asarray(g.exterior.coords)
    for a, bb in zip(co[:-1], co[1:]):
        L = float(np.hypot(*(bb - a)))
        if L < 1.5:
            continue
        mx, my = (a + bb) / 2
        rows.append([0, mx, my, _z_at(n, c, mx, my), L, 0.06, 1.0, math.atan2(bb[1] - a[1], bb[0] - a[0]) - math.pi / 2, 0.0, RAIL])
    ang = _frame_angle(poly)
    q = g.representative_point()
    z = _z_at(n, c, q.x, q.y)
    rows.append([0, q.x, q.y, z, min(4.0, math.sqrt(g.area) * 0.6), min(3.0, math.sqrt(g.area) * 0.45), 0.04, ang, 0.0, WOOD])
    for i in range(1 + seed % 3):  # planters
        p = g.buffer(-0.5).representative_point() if i == 0 else shapely.Point(q.x + (i * 1.7 - 2), q.y + 1.5 + i)
        if g.contains(p):
            rows.append([0, p.x, p.y, z, 0.9, 0.5, 0.55, ang, 0.0, PLANT])


def _pitched(poly, n, c, s, az, seed, area, rows):
    dv = np.array([math.cos(az), math.sin(az)])  # downslope
    tv = np.array([-dv[1], dv[0]])               # contour
    pts = np.asarray(poly.exterior.coords)[:-1]
    uu, vv = pts @ tv, pts @ dv
    width, depth = float(uu.max() - uu.min()), float(vv.max() - vv.min())
    if width < 5 or depth < 2.5:
        return
    inner = poly.buffer(-0.9)
    if inner.is_empty:
        return
    ts = math.tan(s)
    # dormers on steep, big planes: along the contour at 35 % up the slope
    ndorm = 0
    if s > 0.6 and area > 45 and width > 8 and seed % 4 != 0:
        k = min(3, int(width // 5))
        for i in range(k):
            u = uu.min() + width * (i + 0.5) / k + ((seed >> (3 * i)) % 5 - 2) * 0.25
            for f in (0.35, 0.5, 0.65):
                v = vv.min() + depth * f
                cx, cy = u * tv + v * dv
                dw, dd = 1.5, 1.6
                box_ = shapely.box(-dw / 2, -dd / 2, dw / 2, dd / 2)
                corners = np.array([[cx, cy]]) + np.array([[a_ * tv + b_ * dv] for a_, b_ in
                                                           ((-dw / 2, -dd / 2), (dw / 2, -dd / 2), (dw / 2, dd / 2), (-dw / 2, dd / 2))]).reshape(4, 2)
                if inner.contains(Polygon(corners)):
                    break
            else:
                continue
            zf = _z_at(n, c, *(np.array([cx, cy]) + dv * dd / 2)) - 0.1  # plane height at the dormer front
            hbox = 1.25 + dd * ts + 0.1
            wall = DWALL if (seed + i) % 3 else DWALL2
            rows.append([0, cx, cy, zf, dw, dd, hbox, az, 0.0, wall])
            fx, fy = np.array([cx, cy]) + dv * (dd / 2 + 0.03)
            rows.append([0, fx, fy, zf + 0.35, 0.7, 0.05, 0.75, az, 0.0, GLASS])
            rows.append([1, cx, cy, zf + hbox, dw + 0.3, dd + 0.4, 0.55, az, 0.0, RED if (seed >> 4) % 3 == 0 else ZINC])
            ndorm += 1
    # roof windows (Velux-like): 1-3 flush glazed panels on the plane
    if s > 0.4 and area > 30 and (ndorm == 0 or seed % 2):
        for i in range(1 + seed % 3):
            u = uu.min() + width * (0.2 + 0.6 * ((seed >> (2 * i)) % 7) / 6)
            v = vv.min() + depth * (0.3 + 0.1 * (i % 3))
            cx, cy = u * tv + v * dv
            ww, dd = 0.8, 1.2
            corners = np.array([cx, cy]) + np.array([a_ * tv + b_ * dv for a_, b_ in
                                                      ((-ww / 2, -dd / 2), (ww / 2, -dd / 2), (ww / 2, dd / 2), (-ww / 2, dd / 2))])
            if inner.contains(Polygon(corners)):
                rows.append([0, cx, cy, _z_at(n, c, cx, cy) + 0.02, ww, dd / math.cos(s), 0.08, az, s, GLASS])
    # photovoltaics on the pitched plane: from SWISSIMAGE
    _pv_pitched(poly, n, c, s, az, tv, dv, rows)


def _pv_pitched(poly, n, c, s, az, tv, dv, rows):
    if poly.area < 20:
        return
    ox, oy, oins = _grid(poly, 0.5, 0.3)
    if ox is None or oins.sum() < 40:
        return
    rgb = ortho_at(ox[oins], oy[oins])
    good = np.isfinite(rgb[:, 0])
    if good.sum() < 40:
        return
    _, pv, _ = classify(rgb[good])
    if pv.mean() < 0.15 or pv.mean() > 0.85:  # > 85 %: shaded dark roof, not panels
        return
    px, py = ox[oins][good][pv], oy[oins][good][pv]
    u, v = px * tv[0] + py * tv[1], px * dv[0] + py * dv[1]
    iu, iv = np.floor((u - u.min()) / 0.5).astype(int), np.floor((v - v.min()) / 0.5).astype(int)
    img = np.zeros((iu.max() + 2, iv.max() + 2), bool)
    img[iu, iv] = True
    img = ndimage.binary_closing(img, iterations=2)
    lab, k = ndimage.label(img)
    for i in range(1, k + 1):
        sel = np.argwhere(lab == i)
        if len(sel) < 16:  # < 4 m2
            continue
        u0, u1 = u.min() + sel[:, 0].min() * 0.5, u.min() + (sel[:, 0].max() + 1) * 0.5
        v0, v1 = v.min() + sel[:, 1].min() * 0.5, v.min() + (sel[:, 1].max() + 1) * 0.5
        cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
        cx, cy = cu * tv + cv * dv
        rows.append([0, cx, cy, _z_at(n, c, cx, cy) + 0.03, u1 - u0 - 0.2, (v1 - v0 - 0.2) / math.cos(s), 0.07, az, s, PV])
        if len(rows) >= MAX_ROWS:
            return


def pack(rows):
    """Compact JSON rows: rounded numbers."""
    return [[int(r[0]), round(r[1], 1), round(r[2], 1), round(r[3], 1), round(r[4], 2), round(r[5], 2), round(r[6], 2),
             round(r[7], 2), round(r[8], 2), int(r[9])] for r in rows]
