"""Textured LOD2 building meshes: facade bays/floors as UVs, shopfronts on street-facing ground floors."""
import mapbox_earcut as earcut
import json
import os
import numpy as np
from shapely.geometry import Polygon, box

from mesh import tri3d
import facade_trim
from styles import LAYER_NAME, h32, roof_override, BAY_W, FLOOR_H, LAYER, SHOP_H, building_style, shop_layer


ROOF_TINTS = [(255, 255, 255), (235, 205, 190), (205, 175, 160), (185, 170, 165), (150, 150, 155), (245, 225, 210)]


def nearest_poi(b, mid, r=9.0):
    """Closest POI (x, y, kind, notes) to this wall, from b["pois"] = [(x, y, kind[, photo notes])]; None if none within r."""
    best, bd = None, r
    for p in b.get("pois", []):
        d = float(np.hypot(p[0] - mid[0], p[1] - mid[1]))
        if d < bd:
            best, bd = p, d
    return best


def nearest_kind(b, mid, r=9.0):
    """POI kind (cafe, bar, kiosk …) closest to this wall."""
    p = nearest_poi(b, mid, r)
    return p[2] if p else None


# width (m) of the shopfront of a venue; the rest of the ground floor stays ordinary wall / house entrance
SHOP_W = {"restaurant": 7.0, "cafe": 5.5, "bar": 6.0, "pub": 7.0, "nightclub": 7.0, "biergarten": 7.0, "fast_food": 4.5, "kiosk": 3.6,
          "tobacco": 3.6, "newsagent": 3.6, "convenience": 5.0, "supermarket": 11.0, "bakery": 5.0, "pastry": 4.5, "ice_cream": 4.0,
          "clothes": 6.0, "shoes": 5.0, "pharmacy": 6.0, "bank": 8.0, "hairdresser": 4.5, "beauty": 4.5, "bicycle": 6.0, "greengrocer": 5.5}


def base_z(b):
    g = [p for k, p in b["polys"] if k == 0]
    return float(min(p[:, 2].min() for p in (g or [p for _, p in b["polys"]])))


def _tri2d(poly):
    rings = [np.asarray(poly.exterior.coords)[:-1]] + [np.asarray(r.coords)[:-1] for r in poly.interiors]
    xy = np.concatenate(rings)
    t = earcut.triangulate_float64(xy, np.cumsum([len(r) for r in rings]).astype(np.uint32)).reshape(-1, 3)
    return xy, t


def _wall(mesh, a, n, tint, layer, z0, shop, shop_lay, tile_h=FLOOR_H, shop_at=None):
    """Vertical wall: map to (u metres, z), split at the shop line, add with facade UVs."""
    nh = np.array([n[0], n[1]]) / np.hypot(n[0], n[1])
    t = np.array([-nh[1], nh[0]])  # right-hand direction when facing the wall
    d = float(np.mean(a[:, :2] @ nh))
    u = a[:, :2] @ t
    P = Polygon(np.column_stack([u, a[:, 2]])).buffer(0)
    if P.is_empty or P.area < 0.05:
        return None
    u0, _, u1, _ = P.bounds
    width = max(u1 - u0, 0.1)
    bays = max(1, round(width / 3.0))
    su = bays / 4.0 / width  # texture repeats per metre, integer number of bays
    nrm = np.array([nh[0], nh[1], 0.0])
    parts = []
    span = (u0, u1)
    if shop:
        low = P.intersection(box(u0 - 1, z0 - 50, u1 + 1, z0 + SHOP_H))
        # shopfront only over the venue's width (centred on its POI), the rest of the ground floor is ordinary wall
        ws = min(width, shop_at[2]) if shop_at else width
        if shop_at and width - ws >= 2.0:
            uc = float(np.dot([shop_at[0], shop_at[1]], t))
            span = (min(max(uc - ws / 2, u0), u1 - ws), 0.0)
            span = (span[0], span[0] + ws)
            sl = low.intersection(box(span[0], z0 - 50, span[1], z0 + SHOP_H))
            parts.append((sl, shop_lay, z0, SHOP_H, (255, 255, 255), span, shop_at[3]))
            parts.append((low.difference(sl), layer, z0, tile_h, tint))
        else:
            parts.append((low, shop_lay, z0, SHOP_H, (255, 255, 255)))
        parts.append((P.difference(low), layer, z0 + SHOP_H, tile_h, tint))
    else:
        # darker plinth zone (Sockel) like on real Zürich houses, same texture continues above
        plinth = P.intersection(box(u0 - 1, z0 - 50, u1 + 1, z0 + 0.7))
        parts.append((plinth, layer, z0, tile_h, tuple(np.array(tint) * 0.68)))
        parts.append((P.difference(plinth), layer, z0, tile_h, tint))
    for part in parts:
        geom, lay, zb, hv, col = part[:5]
        for poly in getattr(geom, "geoms", [geom]):
            if poly.geom_type != "Polygon" or poly.area < 0.05:
                continue
            uz, tri = _tri2d(poly)
            if len(tri) == 0:
                continue
            xy = np.outer(uz[:, 0], t) + d * nh
            pts = np.column_stack([xy, uz[:, 1]]).astype(np.float32)
            tri = tri.astype(np.uint32)
            cr = np.cross(pts[tri[:, 1]] - pts[tri[:, 0]], pts[tri[:, 2]] - pts[tri[:, 0]]) @ nrm
            tri[cr < 0] = tri[cr < 0][:, ::-1]
            if len(part) > 5:  # venue shopfront: its own bay count over its own width, optionally mirrored (door side)
                sa, sb = part[5]
                bs = max(1, round((sb - sa) / 3.0))
                uu = (uz[:, 0] - sa) * bs / 4.0 / (sb - sa)
                uu = bs / 4.0 - uu if part[6] else uu
                uv = np.column_stack([uu, -(uz[:, 1] - zb) / hv])
            else:
                uv = np.column_stack([(uz[:, 0] - u0) * su, -(uz[:, 1] - zb) / hv])
            mesh.add(pts, tri, nrm, col, uv=uv, layer=lay)
    return (u0, u1, t, nh, d, width, su, z0 + (SHOP_H if shop else 0.0), tile_h, span)


def add_building(mesh, b, street_dist, neighbour=lambda x, y: False):
    """street_dist(x, y) -> metres to the nearest main street; returns shop facade segments for signs."""
    zs = np.concatenate([p[:, 2] for _, p in b["polys"]])
    z0 = base_z(b)
    height = float(zs.max() - z0)
    osm = b.get("osm", {})
    layer, tint = building_style(b["id"], b["type"], height, osm)
    if os.environ.get("SBZ_STYLE_LOG"):  # debugging: which style did each building get?
        with open(os.environ["SBZ_STYLE_LOG"], "a") as f:
            f.write(json.dumps([b["id"], [round(float(v), 1) for v in b["center"][:2]], round(height, 1), layer, list(tint),
                                osm.get("_visual"), (osm.get("_gwr") or {}).get("period"), (osm.get("_gwr") or {}).get("class"),
                                osm.get("name")], default=str) + "\n")
    shop_ok = b.get("shops", False) and height > 6 and layer >= 0
    # storey height from the real eave height: windows line up with the roof instead of a fixed 3.2 m grid
    tops = [float(p[:, 2].max()) for k, p in b["polys"] if k == 1 and len(p) >= 3]
    eave = float(np.percentile(tops, 40)) if tops else z0 + height
    avail = max(2.6, eave - z0 - (SHOP_H if shop_ok else 0.0))
    floors = max(1, round(avail / 3.1))
    try:  # GWR floors (official) or OSM building:levels (above ground, incl. ground floor) beat guessing
        lv = int(float((osm.get("_gwr") or {}).get("floors") or osm.get("building:levels", "")))
        if 1 <= lv <= 40:
            floors = max(1, lv - (1 if shop_ok else 0))
    except ValueError:
        pass
    tile_h = 4 * avail / floors
    lname = LAYER_NAME.get(layer, "")
    trim = lname.startswith(("g3_", "k3_"))          # v3 Altbau: eave cornice (+ bay windows when the notes say so)
    want_erker = trim and "erker" in ((osm.get("_visual") or {}).get("v3") or {}).get("ext", [])
    n_erker = 0
    segs = []
    k = 0
    for kind, a in b["polys"]:
        if kind == 0:
            continue
        if np.allclose(a[0], a[-1]):
            a = a[:-1]
        if len(a) < 3:
            continue
        r = tri3d(a)
        if r is None:
            continue
        pts, tri, n = r
        if kind == 1 and abs(n[2]) < 0.3:
            mid = a[:, :2].mean(0)
            shop = shop_ok and street_dist(mid[0] + n[0] * 3, mid[1] + n[1] * 3) < 9 and a[:, 2].min() < z0 + 1.5
            # party wall: another building stands right in front → blank fire wall (Brandmauer), no windows
            party = not shop and neighbour(mid[0] + n[0] * 1.2, mid[1] + n[1] * 1.2)
            poi = nearest_poi(b, mid) if shop else None
            kind = poi[2] if poi else None
            nt = (poi[3] if len(poi) > 3 else None) or {} if poi else {}
            shop_at = None
            if shop:
                hh = h32(b["id"] + str(k))
                if poi:
                    wmax = SHOP_W.get(kind, 6.0)
                    px, py = poi[0], poi[1]
                else:  # no venue known: a small shop at a hashed place on the wall
                    wmax = 4.5 + hh % 4
                    px, py = mid[0] + (((hh >> 5) % 100) / 100 - 0.5) * 6 * -n[1], mid[1] + (((hh >> 5) % 100) / 100 - 0.5) * 6 * n[0]
                flip = nt.get("d") == "corner" and ((hh >> 3) & 1) or (nt.get("d") != "corner" and (hh >> 3) % 4 == 0)
                shop_at = (px, py, wmax, bool(flip))
            seg = _wall(mesh, a, n, tint, LAYER.get("brandmauer", layer) if party else layer, z0, shop, shop_layer(b["id"], k, kind, nt.get("w")), tile_h, shop_at)
            k += 1
            if trim and seg and not party and seg[5] > 3.0:
                facade_trim.cornice(mesh, seg, eave, tuple(min(255, c * 1.04) for c in tint))
                if want_erker and n_erker < 2 and floors >= 4 and street_dist(mid[0] + n[0] * 3, mid[1] + n[1] * 3) < 14:
                    z_lo = z0 + (SHOP_H if shop_ok else 3.2)
                    if facade_trim.erker(mesh, seg, z_lo, min(eave - 0.5, z_lo + 6.3), layer, tint, h32(b["id"]) + k):
                        n_erker += 1
            if not shop and seg and seg[5] > 3.2 and a[:, 2].min() < z0 + 1.5 \
                    and street_dist(mid[0] + n[0] * 3, mid[1] + n[1] * 3) < 7:
                u0, u1, t, nh, d, w = seg[:6]
                c = (u0 + u1) / 2 * t + d * nh
                segs.append({"x": float(c[0]), "y": float(c[1]), "z": z0 + 1.75, "tx": float(t[0]), "ty": float(t[1]),
                             "w": float(w), "bid": b["id"], "blank": True})
            if shop and seg and seg[5] > 3.5:
                u0, u1, t, nh, d, w = seg[:6]
                ua, ub = seg[9]
                c = (ua + ub) / 2 * t + d * nh
                segs.append({"x": float(c[0]), "y": float(c[1]), "z": z0 + 3.45, "tx": float(t[0]), "ty": float(t[1]),
                             "w": float(ub - ua), "bid": b["id"]})
            continue
        if kind == 2 or abs(n[2]) >= 0.3:
            sloped = abs(n[2]) < 0.94
            if sloped:
                th = np.array([-n[1], n[0], 0.0]) / max(np.hypot(n[0], n[1]), 1e-6)
                bt = np.cross(n, th)
                uv = np.column_stack([pts @ th, pts @ bt]) / 3.0
                seen = None if roof_override(osm) else ortho_tint(b.get("_roof_rgb"), "roof_tiles_grey")
                if seen:  # observed colour on SWISSIMAGE, neutral tile texture
                    mesh.add(pts, tri, n, seen, uv=uv, layer=LAYER["roof_tiles_grey"])
                else:
                    roof_tint = roof_override(osm) or ROOF_TINTS[h32(b["id"] + "r") % len(ROOF_TINTS)]  # tiles vary
                    mesh.add(pts, tri, n, roof_tint, uv=uv, layer=LAYER["roof_tiles"])
                roof_area = 0.5 * np.linalg.norm(np.cross(pts[tri[:, 1]] - pts[tri[:, 0]], pts[tri[:, 2]] - pts[tri[:, 0]]), axis=1).sum()
                if roof_area > 35 and (h32(b["id"]) + k) % 3 != 0:
                    chimney(mesh, pts, k + h32(b["id"]))
            else:
                mesh.add(pts, tri, n, ortho_tint(b.get("_roof_rgb"), "dach_kies") or (158, 155, 150), uv=pts[:, :2] / 3.0, layer=LAYER["dach_kies"])
                area = 0.5 * np.linalg.norm(np.cross(pts[tri[:, 1]] - pts[tri[:, 0]], pts[tri[:, 2]] - pts[tri[:, 0]]), axis=1).sum()
                if area > 60:
                    roof_units(mesh, pts, h32(b["id"]) + k)
        else:
            mesh.add(pts, tri, n, tint, uv=pts[:, :2] / 4.0, layer=layer)
    return segs


_BASE = {}


def ortho_tint(rgb, layer):
    """Vertex tint that makes the (multiplied) texture layer show the roof colour seen on SWISSIMAGE."""
    if rgb is None:
        return None
    if layer not in _BASE:
        import json
        from PIL import Image
        from config import ROOT
        meta = json.load(open(ROOT / "web" / "public" / "tex" / "layers.json"))
        k, L, cols = meta["layers"].index(layer), meta["size"], meta["cols"]
        im = Image.open(ROOT / "web" / "public" / "tex" / "atlas.webp").convert("RGB")
        _BASE[layer] = np.asarray(im.crop(((k % cols) * L, (k // cols) * L, (k % cols + 1) * L, (k // cols + 1) * L))).reshape(-1, 3).mean(0)
    c = np.asarray(rgb, np.float32)
    c = c.mean() + (c - c.mean()) * 1.5  # orthophoto colours are hazy: restore saturation
    t = c * 0.95 / np.maximum(_BASE[layer], 30) * 255
    return tuple(int(v) for v in np.clip(t, 40, 255))


def chimney(mesh, pts, seed):
    """Brick/plaster chimney near the ridge of a pitched roof plane."""
    top = pts[np.argsort(pts[:, 2])[-2:]].mean(0)       # middle of the highest edge (ridge)
    c = pts.mean(0)
    p = c + (top - c) * (0.6 + (seed % 3) * 0.1)
    w = 0.55 + (seed % 4) * 0.08
    z0, z1 = p[2] - 0.8, top[2] + 0.9 + (seed % 5) * 0.12
    col = (150, 70, 52) if seed % 2 else (190, 182, 170)
    x, y = p[0], p[1]
    for nx, ny, a, b in ((1, 0, (x + w / 2, y - w / 2), (x + w / 2, y + w / 2)), (-1, 0, (x - w / 2, y + w / 2), (x - w / 2, y - w / 2)),
                         (0, 1, (x + w / 2, y + w / 2), (x - w / 2, y + w / 2)), (0, -1, (x - w / 2, y - w / 2), (x + w / 2, y - w / 2))):
        q = np.array([[a[0], a[1], z0], [b[0], b[1], z0], [b[0], b[1], z1], [a[0], a[1], z1]], np.float32)
        mesh.add(q, np.array([[0, 1, 2], [0, 2, 3]], np.uint32), np.array([nx, ny, 0.0]), col, uv=np.zeros((4, 2)), layer=LAYER["white"])
    capq = np.array([[x - w / 2 - 0.05, y - w / 2 - 0.05, z1], [x + w / 2 + 0.05, y - w / 2 - 0.05, z1],
                     [x + w / 2 + 0.05, y + w / 2 + 0.05, z1], [x - w / 2 - 0.05, y + w / 2 + 0.05, z1]], np.float32)
    mesh.add(capq, np.array([[0, 1, 2], [0, 2, 3]], np.uint32), np.array([0, 0, 1.0]), (70, 70, 72), uv=np.zeros((4, 2)), layer=LAYER["white"])


def _box(mesh, cx, cy, z0, w, d, h, col):
    """Axis-aligned box (rooftop equipment)."""
    x0, x1, y0, y1, z1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0 + h
    faces = [((1, 0, 0), [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]),
             ((-1, 0, 0), [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)]),
             ((0, 1, 0), [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)]),
             ((0, -1, 0), [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]),
             ((0, 0, 1), [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])]
    for nrm, q in faces:
        mesh.add(np.array(q, np.float32), np.array([[0, 1, 2], [0, 2, 3]], np.uint32), np.array(nrm, float), col,
                 uv=np.zeros((4, 2)), layer=LAYER["white"])


def roof_units(mesh, pts, seed):
    """Lift housing, ventilation boxes and a skylight on large flat roofs."""
    lo, hi = pts.min(0), pts.max(0)
    if min(hi[0] - lo[0], hi[1] - lo[1]) < 6:
        return
    z = float(pts[:, 2].max())
    rnd = np.random.default_rng(seed % (2 ** 31))
    for i in range(1 + seed % 3):
        cx, cy = rnd.uniform(lo[0] + 2, hi[0] - 2), rnd.uniform(lo[1] + 2, hi[1] - 2)
        if i == 0:
            _box(mesh, cx, cy, z, 2.4, 2.4, 2.2, (200, 196, 188))       # lift / stair housing
        else:
            _box(mesh, cx, cy, z, 1.4, 0.9, 0.9, (150, 154, 158))       # ventilation unit
