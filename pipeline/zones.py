"""Night-plan zones: polygons, tile lists, camera points -> pipeline/overrides/zones.json (+ preview/zones.jpg).

Usage: python3 pipeline/zones.py [--sheet]
Camera points come from (a) a name query against the OSM name index (data/raw/osm/kreise.json, cached in
data/build/zone_names.json), (b) the street/hub lists of web/public/data/districts.json, or (c) manual local metres.
Tiles are assigned by tile centre; a tile belongs to the first zone whose polygon contains it (backdrop tiles too).
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

ROOT = config.ROOT
OX, OY = 2681400.0, 1248700.0
NAMES = ROOT / "data" / "build" / "zone_names.json"
OUT = ROOT / "pipeline" / "overrides" / "zones.json"


def wgs_to_local(lat, lon):
    """WGS84 -> LV95 (swisstopo approximate formula, ~1 m) -> local metres."""
    p = (lat * 3600 - 169028.66) / 10000
    l = (lon * 3600 - 26782.5) / 10000
    e = 2600072.37 + 211455.93 * l - 10938.51 * l * p - 0.36 * l * p * p - 44.54 * l ** 3
    n = 1200147.07 + 308807.95 * p + 3745.25 * l * l + 76.63 * p * p - 194.56 * l * l * p + 119.79 * p ** 3
    return e - OX, n - OY


def name_index():
    if not NAMES.exists():
        d = json.load(open(ROOT / "data" / "raw" / "osm" / "kreise.json"))["elements"]
        nodes = {x["id"]: (x["lat"], x["lon"]) for x in d if x["type"] == "node"}
        out = []
        for x in d:
            n = x.get("tags", {}).get("name")
            if not n:
                continue
            if x["type"] == "node":
                p = (x["lat"], x["lon"])
            elif x["type"] == "way":
                ps = [nodes[i] for i in x.get("nodes", []) if i in nodes]
                if not ps:
                    continue
                p = (sum(a for a, _ in ps) / len(ps), sum(b for _, b in ps) / len(ps))
            else:
                continue
            out.append([n, round(p[0], 6), round(p[1], 6), x["type"][0]])
        json.dump(out, open(NAMES, "w"), ensure_ascii=False)
    return json.load(open(NAMES))


_idx = None
_dist = None


ANCH = {4: (-100, -1150), 1: (1100, -700), 3: (0, -600), 2: (500, 200), 5: (-1500, 100)}


def _dist_json():
    global _dist
    _dist = _dist or json.load(open(ROOT / "web/public/data/districts.json"))
    return _dist


def _verts(name, near):
    pts = [p for s in _dist_json()["streets"] if s["n"] == name for p in s["p"]]
    return [p for p in pts if math.hypot(p[0] - near[0], p[1] - near[1]) < 700]


def find(q, zone=None):
    """q: (x,y) manual | 'S:Street' (polyline middle nearest the zone anchor) | 'X:A|B' (street crossing)
    | 'L:text' landmark | 'H:name' hub | regex on OSM name (match nearest the zone anchor)."""
    global _idx
    anc = ANCH.get(zone, (0, -500))
    if isinstance(q, (list, tuple)):
        return tuple(q)
    if q.startswith("S:"):
        ms = [s for s in _dist_json()["streets"] if s["n"] == q[2:]]
        if not ms:
            return None
        mids = [s["p"][len(s["p"]) // 2] for s in ms]
        return tuple(min(mids, key=lambda m: math.hypot(m[0] - anc[0], m[1] - anc[1])))
    if q.startswith("X:"):
        a, b = q[2:].split("|")
        pa, pb = _verts(a, anc), _verts(b, anc)
        if not pa or not pb:
            return None
        d, u, v = min((math.hypot(u[0] - v[0], u[1] - v[1]), u, v) for u in pa for v in pb)
        return ((u[0] + v[0]) / 2, (u[1] + v[1]) / 2)
    if q.startswith("L:"):
        for l in json.load(open(ROOT / "web/public/data/landmarks.json"))["landmarks"]:
            if q[2:].lower() in l["name"].lower():
                return (l["x"], l["y"])
        return None
    if q.startswith("H:"):
        for h in _dist_json()["hubs"]:
            if h["n"] == q[2:]:
                return (h["x"], h["y"])
        return None
    _idx = _idx or name_index()
    rx = re.compile(q, re.I)
    hits = [(n, wgs_to_local(a, b)) for n, a, b, _ in _idx if rx.search(n)]
    hits = [(n, p) for n, p in hits if -2700 < p[0] < 2100 and -2000 < p[1] < 1300]
    if not hits:
        return None
    return min(hits, key=lambda h: math.hypot(h[1][0] - anc[0], h[1][1] - anc[1]))[1]


# zone polygons (local metres), coarse, along streets. Order = priority for overlapping tiles.
ZONES = [
    dict(id=4, name="Wiedikon (Kreis 3)", polys=[[[-750, -900], [650, -900], [650, -2200], [-750, -2200]]]),
    dict(id=1, name="HB und Langstrasse", polys=[[[400, -1010], [2000, -1010], [2000, -300], [400, -300]]]),
    dict(id=3, name="Kreis 4 Mitte", polys=[[[-750, -120], [400, -120], [400, -900], [-750, -900]],
                                            [[650, -1010], [1120, -1010], [1120, -1360], [650, -1360]]]),
    # Zone 2 only south-west of the Limmat (river line from OSM, local m); PJZ and Westpark tiles belong to zone 5 (excl)
    dict(id=2, name="Kreis 5 Industrie", polys=[[[-250, -300], [1810, -300], [1771, -209], [1692, -145], [1551, -25], [1382, 117], [1089, 379],
                                                 [985, 484], [254, 915], [-250, 1135]]],
         excl=[[[440, 50], [560, 50], [560, 150], [440, 150]], [[-200, 600], [0, 600], [0, 800], [-200, 800]]]),
    dict(id=5, name="Kreis 9 West", polys=[[[-2700, -2200], [-750, -2200], [-750, -120], [-250, -120], [-250, 1300], [-2700, 1300]],
                                           [[440, 50], [560, 50], [560, 150], [440, 150]], [[-200, 600], [0, 600], [0, 800], [-200, 800]]]),
]

# camera points per zone, from docs/NIGHT_PLAN.md. (label, query)
CAMS = {
    # Zone 4: points that showed only a wall/pole fixed by hand 2026-10-19 (perron dropped: canopies over the cutting)
    4: [("Idaplatz Mitte", "^Idaplatz$"), ("Idaplatz Nord/Zurlindenstrasse", "X:Zurlindenstrasse|Idastrasse"), ("Idastrasse Süd", "S:Idastrasse"),
        ("Bertastrasse", "S:Bertastrasse"), ("Gertrudstrasse", "S:Gertrudstrasse"), ("Aemtler-/Wiesendangerstrasse", "S:Wiesendangerstrasse"),
        ("Zentralstrasse", "S:Zentralstrasse"), ("Zurlindenstrasse West", "S:Zurlindenstrasse"), ("Zurlindenstrasse Ost", (30, -1190, -2.2)),
        ("Thomasweg/Martastrasse", "S:Thomasweg"), ("Schmiede Wiedikon", (265, -1562, 1.57)), ("Bahnhof Wiedikon Vorplatz", (455, -1441, 1.17)),
        ("Goldbrunnenplatz", "^Goldbrunnenplatz"), ("Friedhof Sihlfeld Haupteingang", "Friedhof Sihlfeld|Sihlfeld.*Friedhof"),
        ("Ortsmuseum Wiedikon", (239, -1732, 3.14)), ("Kalkbreite", (355, -1094, 2.77))],
    # Zone 1: manual points (x, y[, yaw]); the name queries hit wrong places (HB node at the platform tips, Volkshaus roof), checked 2026-10-19
    1: [("Bahnhofplatz (Escher)", (1765, -770, 0.37)), ("HB-Halle", (1763, -656, 1.94)), ("Querhalle", (1728, -641, 0.37)),
        ("Europaallee/Lagerstrasse", (1330, -560, 2.1)), ("Sihlpost", (1382, -812, 0.43)), ("Haltestelle Bahnhofplatz/HB", (1700, -748, 1.2)),
        ("Langstrasse/Lagerstrasse", (875, -430, -2.74)), ("Langstrassen-Unterführung", (893, -372, 0.42)), ("Langstrasse/Dienerstrasse", "X:Langstrasse|Dienerstrasse"),
        ("Langstrasse/Militärstrasse", "X:Langstrasse|Militärstrasse"), ("Langstrasse/Brauerstrasse", "X:Langstrasse|Brauerstrasse"), ("Helvetiaplatz (Volkshaus)", (784, -886, 2.48)),
        ("Haltestelle Helvetiaplatz", (743, -888)), ("Kanzlei", (692.9, -973.4, 0.43)), ("Bäckeranlage", (528, -693, 1.89)),
        ("Kasernenstrasse", "S:Kasernenstrasse"), ("Velotunnel-Portal", (1400, -790, 1.07)), ("Langstrasse/Hohlstrasse", (737.2, -738.9, 2.73))],
    # Zone 3: wall/hedge points replaced by checked spawn spots 2026-10-20
    3: [("Stauffacher", (957, -1196, 2.9)), ("Bullingerplatz (Brunnen)", (-41, -496, -0.76)), ("Bullingerhof", "Bullingerhof"),
        ("Hardplatz", "H:Hardplatz"), ("Albisriederplatz", (-471.8, -670.8, -1.99)), ("Lochergut", (68.1, -970.9, 0.44)),
        ("Badenerstrasse/Kalkbreite-Seite", "X:Badenerstrasse|Kalkbreitestrasse"), ("Badenerstrasse/Zypressenstrasse", "X:Badenerstrasse|Zypressenstrasse"),
        ("Hohlstrasse/Hardstrasse", "X:Hohlstrasse|Hardstrasse"), ("Hardstrasse/Bullingerstrasse", "X:Hardstrasse|Bullingerstrasse"), ("Sihlfeldstrasse", "S:Sihlfeldstrasse"),
        ("Zypressenstrasse", "S:Zypressenstrasse"), ("Erismannhof", (200, -530, -2.4)), ("Brauerstrasse West", "S:Brauerstrasse"),
        ("Seebahnstrasse", "S:Seebahnstrasse"), ("Ernastrasse", "S:Ernastrasse")],
    # Zone 2: Markthalle (inside the z2b arcade landmark) -> Ottostrasse; Escher-Wyss (wall), Hardbrücke perron (on the tracks) and deck (beside the bridge), Josefstrasse (post) by hand 2026-10-22;
    # 4th value = height hint for decks (perron ~-5.4 m, Hardbrücke deck +4.0 m)
    2: [("Escher-Wyss-Platz", (452, 750, 1.94)), ("Bahnhof Hardbrücke Perron", (150, 82.1, -1.21, -5)), ("Hardbrücke Fahrbahn", (32, 111, 0.57, 4)),
        ("Turbinenplatz", "Turbinenplatz"), ("Schiffbau", (231, 430)), ("Prime Tower Fuss", (42, 155)), ("Josefwiese", "Josefwiese"),
        ("Viadukt (Markthalle)", (700, 370, 0.3)), ("Limmatplatz", (1131, 74)), ("Röntgenplatz", (759, 126)),
        ("Limmatstrasse/Konradstrasse", (1286, -229)), ("Josefstrasse", (884, 38, -0.95)), ("Heinrichstrasse", "S:Heinrichstrasse"),
        ("Fabrikstrasse", "S:Fabrikstrasse"), ("Sihlquai", (1550, -92)), ("Limmatufer", (1220, 200))],
    # Zone 5: stadium/stop/PJZ/Lindenplatz/Hohl-Flur by hand 2026-10-20 (PJZ was on the wrong building, Rautistrasse point outside the map)
    5: [("Letzigrund Stadion", (-1060, -240, 0.86)), ("Haltestelle Letzigrund", (-970, -330, 1.2)), ("Badenerstrasse West", (-1934, 441, 5.15)),
        ("Hohlstrasse Letzipark", (-1366.9, 411.2)), ("PJZ Ost", (330, -200, -2.3)), ("Bahnhof Altstetten Vorplatz", (-2183, 764, 4.6)),
        ("Bahnhof Altstetten Aufnahmegebäude", (-2040, 747, 6.1)), ("Lindenplatz", (-2344.8, 352.3, 0.53)), ("Altstetterstrasse", "S:Altstetterstrasse"),
        ("Hohlstrasse/Flurstrasse", (-1450, 440, -2.6)), ("Herdernstrasse", "S:Herdernstrasse"), ("Westpark", "L:Westpark"),
        ("Vulkanplatz", (-1972, 925, 4.9)), ("Baslerstrasse", "S:Baslerstrasse")],
}


def inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def build():
    tiles = config.tiles()
    assigned = {}
    for ix, iy in tiles:
        cx, cy = (ix + 0.5) * config.TILE, (iy + 0.5) * config.TILE
        for z in ZONES:
            if any(inside(pl, cx, cy) for pl in z["polys"]) and not any(inside(pl, cx, cy) for pl in z.get("excl", [])):
                assigned[(ix, iy)] = z["id"]
                break
    zones = []
    for z in ZONES:
        ts = sorted(k for k, v in assigned.items() if v == z["id"])
        cams, miss = [], []
        for label, q in CAMS[z["id"]]:
            p = find(q, z["id"])
            if p is None:
                miss.append(label)
            else:
                cams.append(dict(name=label, x=round(p[0], 1), y=round(p[1], 1), **({"yaw": p[2]} if len(p) > 2 else {}), **({"z": p[3]} if len(p) > 3 else {})))
        zones.append(dict(id=z["id"], name=z["name"], polys=z["polys"], tiles=[f"t_{ix}_{iy}" for ix, iy in ts],
                          n_tiles=len(ts), cams=cams, unresolved=miss))
    zones.sort(key=lambda z: z["id"])
    json.dump(dict(tile=config.TILE, note="generated by pipeline/zones.py", zones=zones,
                   unassigned=[f"t_{ix}_{iy}" for ix, iy in tiles if (ix, iy) not in assigned]),
              open(OUT, "w"), ensure_ascii=False, indent=1)
    for z in zones:
        print(z["id"], z["name"], z["n_tiles"], "tiles", len(z["cams"]), "cams; missing:", z["unresolved"])


def sheet():
    from PIL import Image, ImageDraw
    d = json.load(open(OUT))
    x0, y0, x1, y1 = config.AREA
    S = 0.33
    W, H = int((x1 - x0) * S / 1) // 1, int((y1 - y0) * S)
    W, H = int((x1 - x0) / 3.2), int((y1 - y0) / 3.2)
    im = Image.new("RGB", (W, H), (30, 30, 34))
    dr = ImageDraw.Draw(im, "RGBA")
    px = lambda x, y: ((x - x0) / 3.2, (y1 - y) / 3.2)
    cols = {1: (230, 60, 60), 2: (60, 150, 230), 3: (240, 190, 40), 4: (60, 200, 100), 5: (180, 90, 220)}
    for z in d["zones"]:
        for t in z["tiles"]:
            _, ix, iy = t.split("_")
            ix, iy = int(ix), int(iy)
            a = px(ix * config.TILE, (iy + 1) * config.TILE)
            b = px((ix + 1) * config.TILE, iy * config.TILE)
            dr.rectangle([a, b], fill=cols[z["id"]] + (110,), outline=(0, 0, 0, 60))
        for c in z["cams"]:
            X, Y = px(c["x"], c["y"])
            dr.ellipse([X - 2, Y - 2, X + 2, Y + 2], fill=(255, 255, 255))
        cx = sum(c["x"] for c in z["cams"]) / max(1, len(z["cams"]))
        cy = sum(c["y"] for c in z["cams"]) / max(1, len(z["cams"]))
        dr.text(px(cx, cy), f"Z{z['id']}", fill=(255, 255, 255))
    for t in d["unassigned"]:
        _, ix, iy = t.split("_")
        a = px(int(ix) * config.TILE, (int(iy) + 1) * config.TILE)
        b = px((int(ix) + 1) * config.TILE, int(iy) * config.TILE)
        dr.rectangle([a, b], fill=(120, 120, 120, 70))
    (ROOT / "preview").mkdir(exist_ok=True)
    im.save(ROOT / "preview" / "zones.jpg", quality=82)


if __name__ == "__main__":
    build()
    if "--sheet" in sys.argv:
        sheet()
