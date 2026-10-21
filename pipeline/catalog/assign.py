"""Catalog assignment (Auftrag K3): variants for every fountain and stop object in the play area
-> web/public/data/catalog.json.

Fountains: data/raw/stadtzh*/geo_brunnen__wvz_brunnen.geojson inside data/build/playarea.json (+50 m); variant from the
data rules in variants.py (research/catalog/brunnen.md), then research/catalog/assign_hints.json (photo-confirmed), then
pipeline/overrides/catalog_assign.json. V7/V10 fall back to V2 (index.json). Heading = nearest road direction
(web/public/data/roads.json) so the long axis of a trough follows the street.
Stops: web/public/data/stops_equip.json (shelters H1/H2 by installation year, ticket machines H3, displays H4/H5,
benches H6/H7); positions and facing are taken over 1:1, so only objects that stops_equip draws today appear.

Row format "o": [variant, x, y, yaw, sx, dy, kind]; yaw = rotation about three.js Y (front = +z); sx = x scale (shelters);
dy = height offset above ground; kind 0 fountain, 1 stop object, 2 kiosk (collider), 3 kiosk replacing a tile kiosk (z from the stop platform at runtime). Ground z is not stored:
the runtime asks Tiles.ground() (kerb-lowered terrain), the same function the other props use.
Usage: python3 pipeline/catalog/assign.py"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from shapely.geometry import Point, Polygon  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402
from shapely.geometry import LineString  # noqa: E402
from variants import brunnen_variant  # noqa: E402

ROOT = HERE.parents[1]
WEB = ROOT / "web" / "public" / "data"
RAW_ALL = ROOT / "data" / "raw" / "stadtzh_all"
CODE = {"V1_saeule_trog": "V1", "V2_stein_trog": "V2", "V3_bronze_trog": "V3", "V4_beton": "V4", "V5_kunststein": "V5",
        "V6_figur": "V6", "V7_wandbrunnen": "V7", "V8_notwasser": "V8", "V9_holz": "V9", "V10_ohne_angabe": "V2"}
OVR = ROOT / "pipeline" / "overrides" / "catalog_assign.json"


def yaw_of(az_deg, side):
    a = math.radians(az_deg)
    return math.atan2(math.cos(a) * side, math.sin(a) * side)   # same frame as frame() in stops_equip.ts


def road_lines():
    d = json.load(open(WEB / "roads.json"))
    ls = []
    for r in d["cars"] + d["bikes"]:
        p = r["p"]
        pts = list(zip(p[0::2], p[1::2]))
        if len(pts) > 1:
            ls.append(LineString(pts))
    return ls, STRtree(ls)


def feats(path):
    return json.load(open(path))["features"]


def main():
    pa = json.load(open(ROOT / "data" / "build" / "playarea.json"))
    area = Polygon(pa["polygon"]).buffer(50)
    ovr = json.load(open(OVR))
    hints = json.load(open(ROOT / "research" / "catalog" / "assign_hints.json"))
    lines, tree = road_lines()
    out_o, cnt = [], Counter()

    # --- fountains
    src = next((ROOT / "data" / "raw").glob("stadtzh*/geo_brunnen__wvz_brunnen.geojson"))
    n_in = 0
    for f in feats(src):
        p = f["properties"]
        if p.get("hkoord") is None:
            continue
        x, y = p["hkoord"] - 2681400.0, p["vkoord"] - 1248700.0
        if not area.contains(Point(x, y)):
            continue
        bid = f"BR-{p['objectid']}"
        if bid in ovr.get("exclude", []):
            continue
        n_in += 1
        v = CODE[hints.get(bid) or brunnen_variant(p)]
        v = ovr.get("brunnen", {}).get(bid, v)
        if bid in ovr.get("rot", {}):
            yaw = ovr["rot"][bid]
        else:
            i = int(tree.nearest(Point(x, y)))
            ln = lines[i]
            s = ln.project(Point(x, y))
            a, b = ln.interpolate(max(0, s - 1)), ln.interpolate(min(ln.length, s + 1))
            yaw = math.pi / 2 - math.atan2(b.x - a.x, b.y - a.y)   # model +x along the street
        sys.path.insert(0, str(ROOT / "pipeline"))
        import props_road   # fountains stand on the pavement, not the carriageway (cache: pipeline/props_road.py)
        props_road.load_cached()
        q = props_road.snap(x, y)
        if q is None:
            continue
        x, y = q
        out_o.append([v, round(x, 2), round(y, 2), round(yaw, 3), 1, 0, 0])
        cnt[v] += 1

    # --- stops
    eq = json.load(open(WEB / "stops_equip.json"))
    sys.path.insert(0, str(ROOT / "pipeline"))
    import stops_equip as SE
    wh = []
    for f in SE.layer("wartehalle"):
        g = SE.geom_local(f)
        if g and g[0] == "poly":
            c = g[1].centroid
            wh.append((c.x, c.y, str(f["properties"].get("einbaudatum") or "")[:4]))
    wtree = STRtree([Point(a, b) for a, b, _ in wh])
    for x, y, ln, dep, az, s in eq["sh"]:
        i = int(wtree.nearest(Point(x, y)))
        near = wh[i]
        new = math.hypot(near[0] - x, near[1] - y) < 6 and near[2] == "2018"
        v, base = ("H1", 7.0) if new else ("H2", 6.0)
        n = 1 if ln <= 12 else round(ln / 7.0)
        for so in ovr.get("stops", []):   # override: {"x","y","r","variant","base"}: this shelter is one special model (e.g. H8 Schirmdach Letzigrund)
            if math.hypot(so["x"] - x, so["y"] - y) < so.get("r", 3.0):
                v, base, n = so["variant"], ln, 1
        seg = ln / n
        yaw = yaw_of(az, s)
        ax, ay = math.sin(math.radians(az)), math.cos(math.radians(az))    # azimuth = clockwise from north
        for k in range(n):
            o = (k - (n - 1) / 2) * seg
            out_o.append([v, round(x + ax * o, 2), round(y + ay * o, 2), round(yaw, 3), round(seg / base, 3), 0, 1])
            cnt[v] += 1
    # benches: kind 0 only (stehhilfe / single seat have no catalog model); H7 if the VBZ record says long
    bank = []
    for f in SE.layer("sitzgelegenheit"):
        g = SE.geom_local(f)
        if g and g[0] == "pt":
            bank.append((g[1][0], g[1][1], str(f["properties"].get("typ") or "")))
    btree = STRtree([Point(a, b) for a, b, _ in bank])
    for x, y, az, s, kind, inwh in eq["bn"]:
        if kind != 0:
            continue
        i = int(btree.nearest(Point(x, y)))
        v = "H7" if "lang" in bank[i][2] and math.hypot(bank[i][0] - x, bank[i][1] - y) < 1.0 else "H6"
        out_o.append([v, x, y, round(yaw_of(az, s), 3), 1, 0, 1])
        cnt[v] += 1
    for x, y, az, s in eq["tk"]:
        out_o.append(["H3", x, y, round(yaw_of(az, s), 3), 1, 0, 1])
        cnt["H3"] += 1
    for x, y, az, ceil in eq["df"]:
        # same placement as stops_equip.ts: wall display at 2.25 m on a pole, ceiling display hanging from the roof (2.5 m)
        for side in (1, -1):
            out_o.append(["H5" if ceil else "H4", x, y, round(yaw_of(az, side), 3), 1, 2.5 if ceil else 2.25, 1])
        cnt["H5" if ceil else "H4"] += 1
    for x, y, az, s in eq["pl"]:   # VBZ poster panels (M3), replace the old poster boxes in stops_equip.ts
        out_o.append(["M3", x, y, round(yaw_of(az, s), 3), 1, 0, 1])
        cnt["M3"] += 1
    # kiosks M2 (kind 2: ground from Tiles.ground(), collider circle), see assign_kiosk.py
    import assign_kiosk
    rl = []
    for r in json.load(open(WEB / "roads.json"))["cars"]:
        p = r["p"]
        if len(p) >= 4:
            rl.append((LineString(list(zip(p[0::2], p[1::2]))), r.get("w", 6.0) / 2))
    ko, kst = assign_kiosk.rows(area, rl)
    out_o += ko
    cnt["M2"] += len(ko)
    print("kiosks:", kst)
    res = {"src": "WVZ Brunnenkataster, VBZ Infrastruktur OGD (CC0); pipeline/catalog/assign.py", "o": out_o}
    (WEB / "catalog.json").write_text(json.dumps(res, separators=(",", ":")))
    print("fountains in area:", n_in, "stops objs:", sum(1 for o in out_o if o[6]))
    print(dict(sorted(cnt.items())))


if __name__ == "__main__":
    main()
