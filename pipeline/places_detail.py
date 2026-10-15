"""Detail layer for squares and parks (Röntgenplatz, Helvetiaplatz, ...): exact ground patterns and furniture.

Data: pipeline/overrides/places_detail.json (hand-authored from photos + orthophoto + OGD; coordinates are metres
relative to the place centre, x east, y north). Pipeline hooks (build_testarea.py):
    places_detail.ground(gm, tb, H)     ground patches (asphalt/pavers/gravel/lawn/concrete) draped on the tile
    places_detail.tile_meta(tb, H)      object rows for web/src/world/places_detail.ts  (meta["places"])
Tool:  .venv/bin/python pipeline/places_detail.py sheet <id> [window_m]   -> orthophoto + OGD + authored overlay (grid)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import shapely
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box

from config import ROOT
from mesh import drape
from styles import LAYER

OVR = ROOT / "pipeline" / "overrides" / "places_detail.json"
CURB = 0.12
# ground materials: (texture layer, colour multiplier, lift above the base surface)
MAT = {
    "asphalt": ("asphalt", (255, 255, 255)), "pave": ("cobble", (255, 255, 255)), "sidewalk": ("sidewalk", (255, 255, 255)),
    "grass": ("grass", (255, 255, 255)), "gravel": ("roof_flat", (225, 214, 190)), "mergel": ("roof_flat", (214, 190, 150)),
    "concrete": ("sidewalk", (214, 212, 206)), "granite": ("white", (150, 148, 144)), "plain": ("white", (200, 200, 200)),
}


def load():
    """places_detail.json plus places_detail_<id>.json (one file per place, same schema)."""
    out = []
    for f in sorted(OVR.parent.glob("places_detail*.json")):
        out += json.load(open(f)).get("places", [])
    return out


_OSM = None


def _osm():
    global _OSM
    if _OSM is None:
        import sources
        nodes, els = sources.osm()
        _OSM = (nodes, {e["id"]: e["nodes"] for e in els if e["type"] == "way" and "nodes" in e})
    return _OSM


def _shape(g, c, roads=None):
    """Authored shape -> shapely polygon in local metres. rect [dx,dy,w,h,rot_deg] | poly [[dx,dy]..] | circle [dx,dy,r]
    | line [[dx,dy]..] with width w."""
    cx, cy = c
    if "dots" in g:  # scattered round paint discs (Velostrasse markings); on_roads clips them to the carriageway
        import random
        dd = g["dots"]
        rnd = random.Random(dd.get("seed", 1))
        base = _shape(dd["within"], c)
        x0, y0, x1, y1 = base.bounds
        pts = []
        for i in range(int((x1 - x0) / dd["spacing"]) + 1):
            for j in range(int((y1 - y0) / dd["spacing"]) + 1):
                x = x0 + (i + rnd.random()) * dd["spacing"]
                y = y0 + (j + rnd.random()) * dd["spacing"]
                if rnd.random() < dd.get("p", 1.0) and base.contains(Point(x, y)):
                    pts.append(affinity.scale(Point(x, y).buffer(dd["r"], 8), 1.0, 0.8))
        u = shapely.union_all(pts) if pts else Polygon()
        if dd.get("on_roads") and roads is not None:
            u = u.intersection(roads.buffer(-0.7))
        return u
    if "rings" in g:  # concentric ring stripes: rings [dx, dy, r0, n, spacing, width, from_deg, to_deg]
        dx, dy, r0, n, sp, w, a0, a1 = g["rings"]
        out = []
        for i in range(n):
            r = r0 + i * sp
            ring = Point(cx + dx, cy + dy).buffer(r + w / 2, 32).difference(Point(cx + dx, cy + dy).buffer(r - w / 2, 32))
            wedge = Polygon([(cx + dx, cy + dy)] + [(cx + dx + 4 * (r0 + n * sp) * math.cos(math.radians(a)), cy + dy + 4 * (r0 + n * sp) * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 12)])
            out.append(ring.intersection(wedge))
        return shapely.union_all(out)
    if "pxpoly" in g:  # polygon read off an authoring sheet: pixels (1000 px = win metres, centre = place centre)
        k = 1000.0 / g.get("win", 100.0)
        return Polygon([(cx + (a - 500) / k, cy + (500 - b) / k) for a, b in g["pxpoly"]])
    if "grid" in g:  # bands of width w every spacing m, rotated by angle (deg), clipped to "within"
        gd = g["grid"]
        base = _shape(g["within"], c)
        x0, y0, x1, y1 = base.bounds
        n = int(max(x1 - x0, y1 - y0) / gd["spacing"]) + 2
        ox, oy = (x0 + x1) / 2 + gd.get("ox", 0), (y0 + y1) / 2 + gd.get("oy", 0)
        R = max(x1 - x0, y1 - y0)
        bands = [LineString([(ox + i * gd["spacing"], oy - R), (ox + i * gd["spacing"], oy + R)]).buffer(gd["w"] / 2, cap_style="flat") for i in range(-n, n + 1)]
        bands += [LineString([(ox - R, oy + i * gd["spacing"]), (ox + R, oy + i * gd["spacing"])]).buffer(gd["w"] / 2, cap_style="flat") for i in range(-n, n + 1)]
        u = shapely.union_all(bands)
        return affinity.rotate(u, gd.get("angle", 0), origin=(ox, oy)).intersection(base)
    if "osm" in g:  # OSM way polygon (area), optionally shrunk/grown by "buf"
        nodes, ways = _osm()
        p = Polygon([nodes[i] for i in ways[g["osm"]] if i in nodes])
        return p.buffer(g["buf"]) if g.get("buf") else p
    if "poly" in g:
        return Polygon([(cx + a, cy + b) for a, b in g["poly"]])
    if "rect" in g:
        dx, dy, w, h, *r = g["rect"]
        p = box(cx + dx - w / 2, cy + dy - h / 2, cx + dx + w / 2, cy + dy + h / 2)
        return affinity.rotate(p, r[0], origin=(cx + dx, cy + dy)) if r else p
    if "circle" in g:
        dx, dy, rad = g["circle"]
        return Point(cx + dx, cy + dy).buffer(rad, 24)
    if "line" in g:
        return LineString([(cx + a, cy + b) for a, b in g["line"]]).buffer(g.get("w", 1.0) / 2, cap_style="flat")
    raise ValueError(g)


def _ortho_patches(pl, og, tb, roads):
    """Ground classes measured from the SWISSIMAGE mosaic (0.5 m/px) inside og["within"] (minus roads):
    lawn (green), gravel/sand (warm light), everything else paved. Returns [(mat, geometry)]."""
    import streets_ortho as SO
    from PIL import Image, ImageFilter
    zone = _shape(og["within"], pl["center"]).intersection(tb)
    if roads is not None and not roads.is_empty:
        zone = zone.difference(roads.buffer(0.3))
    if zone.is_empty:
        return []
    m = SO._mosaic(*zone.bounds)
    if m is None:
        return []
    rgb, xs, ys = m
    X, Y = np.meshgrid(xs, ys)
    inz = shapely.contains_xy(zone, X, Y)
    a = rgb.astype(float)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.3 * R + 0.59 * G + 0.11 * B
    exg = G - 0.5 * (R + B)
    thr = og.get("exg", 7) - 4 * (1 - np.clip((lum - 70) / 40, 0, 1))  # shaded lawn is less green
    grass = inz & (exg > thr)
    gravel = inz & ~grass & (R - B > og.get("warm", 16)) & (lum > 95) if og.get("gravel", True) else np.zeros_like(grass)
    paved = inz & ~grass & ~gravel
    out = []
    for mat, mk, on in (("grass", grass, og.get("grass", True)), ("gravel", gravel, True), (og.get("paved", "concrete"), paved, og.get("paved", "concrete") is not None)):
        if not on or mk.sum() < 8:
            continue
        sm = np.asarray(Image.fromarray((mk * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5))) > 127
        r, c = np.nonzero(sm)
        if not len(r):
            continue
        px = shapely.box(xs[c] - 0.25, ys[r] - 0.25, xs[c] + 0.25, ys[r] + 0.25)
        u = shapely.union_all(px).buffer(0.3).buffer(-0.3).intersection(zone).simplify(0.2)
        parts = [g for g in shapely.get_parts(u) if g.geom_type == "Polygon" and g.area > 3.0]
        if parts:
            out.append((mat, shapely.union_all(parts)))
    return out


def ground(gm, tb, H, roads=None):
    """Draped patches. Order = file order (later on top, +0.002 per step)."""
    n = 0
    for pl in load():
        c = pl["center"]
        if not box(c[0] - 150, c[1] - 150, c[0] + 150, c[1] + 150).intersects(tb):
            continue
        og = pl.get("ortho_ground")
        if og:
            for mat, geom in _ortho_patches(pl, og, tb, roads):
                layer, col = MAT[mat]
                drape(gm, geom, H, og.get("lift", 0.0115), col, cell=10, layer=LAYER[layer], uv_scale=5.0 if mat == "grass" else 2.5)
                n += 1
        for i, g in enumerate(pl.get("ground", [])):
            geom = _shape(g, c, roads).intersection(tb)
            if geom.is_empty:
                continue
            layer, col = MAT[g["mat"]]
            col = tuple(g["color"]) if "color" in g else col
            drape(gm, geom, H, max(g.get("lift", 0.012), 0.013) + 0.002 * i, col, cell=10, layer=LAYER[layer], uv_scale=g.get("uv", 3.0))
            n += 1
    if n:
        print(f"  places_detail: {n} ground patches", flush=True)


FOOT = {  # collision footprint (w along x, d along y) of solid object types
    "basin": lambda o: (o.get("a") or 6, o.get("b") or 2.5), "kiosk": lambda o: (o.get("a") or 4, o.get("b") or 3),
    "stall": lambda o: (o.get("a") or 3, o.get("b") or 2), "rfount": lambda o: ((o.get("a") or 1.6) * 2,) * 2,
    "container": lambda o: (o.get("a") or 6, o.get("b") or 2.4), "cabinet": lambda o: (o.get("a") or 1.2, o.get("b") or 0.6),
    "sculpt": lambda o: (1.2, 1.2), "planter": lambda o: (o.get("a") or 3, o.get("b") or 1), "pingpong": lambda o: (2.8, 1.6),
    "pavilion": lambda o: (0.5, 0.5), "bin": lambda o: (0.45, 0.45), "pole": lambda o: (0.2, 0.2), "flag": lambda o: (0.2, 0.2),
    "arch": lambda o: (0.3, 0.3), "lamp": lambda o: (0.3, 0.3), "dfount": lambda o: (0.6, 0.6),
}


def _scatter(sc, c):
    """Points on a jittered grid inside a shape: [(dx, dy, heading_deg)]."""
    import random
    rnd = random.Random(sc.get("seed", 1))
    poly = _shape(sc["within"], c)
    x0, y0, x1, y1 = poly.bounds
    sp = sc.get("spacing", 3.0)
    out = []
    for i in range(int((x1 - x0) / sp) + 1):
        for j in range(int((y1 - y0) / sp) + 1):
            x = x0 + (i + 0.5) * sp + rnd.uniform(-1, 1) * sc.get("jitter", 0.3) * sp
            y = y0 + (j + 0.5) * sp + rnd.uniform(-1, 1) * sc.get("jitter", 0.3) * sp
            if poly.contains(Point(x, y)) and rnd.random() < sc.get("p", 1.0):
                h = sc.get("h", 0) + rnd.uniform(-1, 1) * sc.get("hj", 0)
                out.append((x - c[0], y - c[1], h))
    return out


def _objects(pl):
    """Authored objects plus scatter expansions: dicts with p (relative), t, h, a-d, col."""
    objs = list(pl.get("objs", []))
    for sc in pl.get("scatter", []):
        for dx, dy, h in _scatter(sc, pl["center"]):
            o = {k: v for k, v in sc.items() if k in ("t", "a", "b", "c", "d", "col", "lift", "sit")}
            objs.append({**o, "p": [dx, dy], "h": h})
    return objs


def convert_lights(P, tb, H):
    """OGD street furniture inside a place's zone becomes that place's own type (arch masts, mushroom lamps, dog fountain,
    green benches ...). Spec list "convert": [{layer: masts|fountains|benches|bins, within: shape, t: type, ...}];
    "lights" is the old single-spec form for masts. Matching rows are removed from P and returned as object rows."""
    rows = []
    for pl in load():
        specs = list(pl.get("convert", [])) + ([{**pl["lights"], "layer": "masts"}] if pl.get("lights") else [])
        for sp in specs:
            layer = sp["layer"]
            zone = _shape(sp["within"], pl["center"])
            keep = []
            for r in P.get(layer, []):
                if not zone.contains(Point(r[0], r[1])):
                    keep.append(r)
                    continue
                if layer == "masts":
                    hd = math.degrees(math.atan2(pl["center"][1] - r[1], pl["center"][0] - r[0])) if sp.get("face") == "centre" else sp.get("h", 0)
                elif layer in ("benches", "fountains"):
                    hd = 90 - math.degrees(r[3]) + sp.get("h", 0)
                else:
                    hd = sp.get("h", 0)
                rows.append({"t": sp["t"], "p": [r[0], r[1]], "h": hd, **{k: sp[k] for k in ("a", "b", "c", "d", "col", "sit") if k in sp}})
            if len(keep) != len(P.get(layer, [])):
                P[layer] = keep
    return rows


def tile_meta(tb, H, P=None):
    """Rows [type, x, y, z, heading_rad, a, b, c, d] and 'fences' polylines for the tile."""
    objs, lines, coll, benches, slabs = [], [], [], [], []
    extra = convert_lights(P, tb, H) if P is not None else []
    for pl in load() + ([{"center": [0, 0], "objs": extra}] if extra else []):
        c = pl["center"]
        for o in _objects(pl):
            x, y = c[0] + o["p"][0], c[1] + o["p"][1]
            if not tb.contains(Point(x, y)):
                continue
            lift = o.get("lift", 0.0)
            hd = math.radians(o.get("h", 0))
            if o["t"] in FOOT:  # solid objects block the player
                w, d = FOOT[o["t"]](o)
                fp = affinity.rotate(box(x - w / 2, y - d / 2, x + w / 2, y + d / 2), o.get("h", 0), origin=(x, y))
                coll.append([[round(a, 2), round(b, 2)] for a, b in list(fp.exterior.coords)[:-1]])
            if o["t"] in ("tbench", "bench") and o.get("sit", 1):  # seated people (pedspots): rows [x, y, z, heading]
                benches.append([round(x, 2), round(y, 2), round(float(H.at(x, y)), 2), round(math.pi / 2 - hd, 3)])
            objs.append([o["t"], round(x, 2), round(y, 2), round(float(H.at(x, y)) + lift, 2), round(math.radians(o.get("h", 0)), 3),
                         *[o.get(k, 0) for k in ("a", "b", "c", "d")], o.get("col", "")])
        for ln in pl.get("lines", []):
            pts = [(c[0] + a, c[1] + b) for a, b in ln["pts"]]
            ls = LineString(pts).intersection(tb)
            for seg in getattr(ls, "geoms", [ls]):
                if seg.geom_type != "LineString" or seg.is_empty:
                    continue
                lines.append({"t": ln["t"], "h": ln.get("hgt", 0), "col": ln.get("col", ""),
                              "pts": [[round(x, 2), round(y, 2), round(float(H.at(x, y)), 2)] for x, y in seg.coords]})
    for pl in load():  # roof slabs (canopies): extruded polygons with tree holes
        for sl in pl.get("slabs", []):
            shp = _shape(sl, pl["center"])
            if not tb.contains(shp.centroid):
                continue
            holes = [Point(pl["center"][0] + a, pl["center"][1] + b).buffer(r, 12) for a, b, r in sl.get("holes", [])]
            ring = lambda g: [[round(x, 2), round(y, 2)] for x, y in list(g.exterior.coords)[:-1]]
            slabs.append({"pts": ring(shp), "holes": [ring(h) for h in holes], "z": round(float(H.at(shp.centroid.x, shp.centroid.y)), 2),
                          "h": sl.get("h", 3.2), "t": sl.get("t", 0.25), "col": sl.get("col", "#b9b7af")})
    return {"objs": objs, "lines": lines, "slabs": slabs, "_colliders": coll, "seats": benches} if objs or lines or slabs else {}


# ------------------------------------------------------------------ authoring sheet
def sheet(pid, win=80.0):
    from PIL import Image, ImageDraw
    import sources
    pl = next(p for p in load() if p["id"] == pid) if any(p["id"] == pid for p in load()) else None
    cen = json.load(open(ROOT / "data/raw/ortho_places/centers.json"))
    c = pl["center"] if pl else cen[pid]
    im = Image.open(ROOT / f"data/raw/ortho_places/ortho_{pid}.jpg").convert("RGB")
    ox, oy = cen[pid]
    ppm = im.width / 140.0
    px = lambda x, y: ((x - ox) * ppm + im.width / 2, (oy - y) * ppm + im.height / 2)
    x0, y0 = px(c[0] - win / 2, c[1] + win / 2)
    out = im.crop((int(x0), int(y0), int(x0 + win * ppm), int(y0 + win * ppm))).resize((1000, 1000), Image.LANCZOS)
    k = 1000 / win
    d = ImageDraw.Draw(out)
    P = lambda x, y: ((x - (c[0] - win / 2)) * k, ((c[1] + win / 2) - y) * k)
    step = 10
    for v in range(-int(win / 2 // step) * step, int(win / 2) + 1, step):
        a = P(c[0] + v, c[1] - win / 2)[0]; b = P(c[0] - win / 2, c[1] + v)[1]
        d.line([(a, 0), (a, 1000)], fill=(255, 255, 255), width=1); d.line([(0, b), (1000, b)], fill=(255, 255, 255), width=1)
        d.text((a + 2, 2), str(v), fill=(255, 255, 0)); d.text((2, b + 2), str(v), fill=(255, 255, 0))
    C = json.load(open(next((ROOT / "data/build").glob("citydata_v2_-2849*.json"))))
    sty = {"trees": ((0, 200, 0), None), "benches": ((255, 140, 0), 4), "bins": ((255, 0, 255), 3), "fountains": ((0, 160, 255), 5),
           "lights": ((255, 255, 0), 3), "bikes": ((255, 80, 160), 3)}
    for layer, (col, r) in sty.items():
        for row in C.get(layer, []):
            if abs(row[0] - c[0]) < win / 2 and abs(row[1] - c[1]) < win / 2:
                X, Y = P(row[0], row[1])
                rr = (row[3] / 2 * k) if layer == "trees" else r
                d.ellipse([X - rr, Y - rr, X + rr, Y + rr], outline=col, width=2)
    if pl:
        for g in pl.get("ground", []):
            s = _shape(g, pl["center"])
            for p in getattr(s, "geoms", [s]):
                d.line([P(*q) for q in p.exterior.coords], fill=(0, 255, 255), width=2)
        for o in pl.get("objs", []):
            X, Y = P(c[0] + o["p"][0], c[1] + o["p"][1])
            d.rectangle([X - 4, Y - 4, X + 4, Y + 4], outline=(255, 60, 60), width=2); d.text((X + 6, Y - 5), o["t"], fill=(255, 60, 60))
    # reference photo positions (research/v3/photos.json): index + viewing direction
    try:
        from sources import geo
        for i, ph in enumerate(json.load(open(ROOT / "research/v3/photos.json")).get(pid, {}).get("photos", [])):
            if ph.get("lat") is None:
                continue
            x, y = geo.to_local(ph["lon"], ph["lat"])
            X, Y = P(float(x), float(y))
            if not (0 <= X < 1000 and 0 <= Y < 1000):
                continue
            hd = math.radians(ph.get("heading") or 0)
            d.line([(X, Y), (X + 40 * math.sin(hd), Y - 40 * math.cos(hd))], fill=(255, 0, 0), width=2)
            d.text((X + 3, Y + 3), f"#{i}", fill=(255, 120, 120))
    except Exception as e:
        print("photos", e)
    # OSM buildings
    try:
        for b in sources.buildings(margin=0, area=(c[0] - win, c[1] - win, c[0] + win, c[1] + win)):
            for kk, poly in b["polys"]:
                if kk == 0:
                    pts = [P(*q[:2]) for q in poly]
                    d.line(pts + pts[:1], fill=(120, 160, 255), width=1)
    except Exception as e:
        print("buildings", e)
    dst = sys.argv[4] if len(sys.argv) > 4 else str(ROOT / f"preview/sheet_{pid}.jpg")
    out.save(dst, quality=88)
    print(dst)


if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        sheet(sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 80.0)
