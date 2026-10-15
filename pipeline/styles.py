"""Texture layer indices and building style rules."""
import hashlib

from gen_textures import LAYERS, SHOPS
from gen_shopfronts import BASE

LAYER = {n: i for i, n in enumerate(LAYERS)}

# Zürich plaster tints (sRGB): cream, ochre, light grey, salmon, pale green, white, sand, pale blue
TINTS = [(240, 226, 196), (232, 200, 140), (214, 212, 206), (236, 196, 176), (206, 222, 200),
         (246, 244, 236), (226, 210, 170), (204, 214, 224), (238, 214, 160), (220, 186, 160)]
FLOOR_H = 12.8  # one facade layer covers 4 floors
BAY_W = 12.0    # and 4 window bays
SHOP_H = 4.0


def h32(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def pick(h, table):
    """Weighted choice: table = [(weight, [names])]."""
    tot = sum(w for w, _ in table)
    r = (h >> 8) % tot
    for w, names in table:
        if r < w:
            return LAYER[names[(h >> 16) % len(names)]]
        r -= w


ALT = ["gruender_a", "gruender_b", "gruender_c"]
JUG = ["jugend_a", "jugend_b"]
GEN = ["genoss_a", "genoss_b", "genoss_c"]
B50 = ["block50_a", "block50_b", "block60_a"]
B70 = ["waschbeton_a", "waschbeton_b"]
NEU = ["neubau_a", "neubau_b", "neubau_c"]
GEW = ["gewerbe_a", "gewerbe_b", "gewerbe_c"]
BUR = ["buero_a", "buero_b", "buero_c"]


COLOURS = {"white": (246, 244, 238), "yellow": (236, 214, 150), "beige": (230, 214, 182), "grey": (200, 200, 198),
           "gray": (200, 200, 198), "red": (200, 120, 100), "brown": (170, 130, 100), "pink": (236, 196, 186),
           "orange": (232, 170, 110), "green": (190, 210, 180), "blue": (190, 205, 225), "cream": (240, 228, 200)}


def parse_colour(v):
    v = (v or "").strip().lower()
    if v.startswith("#") and len(v) in (4, 7):
        v = v[1:] if len(v) == 7 else "".join(c * 2 for c in v[1:])
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    return COLOURS.get(v)


import json  # noqa: E402
from pathlib import Path  # noqa: E402

OVERRIDES = json.load(open(Path(__file__).parent / "overrides" / "buildings.json"))["by_name"]
FAMILIES = {"ALT": "ALT", "JUG": "JUG", "GEN": "GEN", "B50": "B50", "B70": "B70", "NEU": "NEU", "GEW": "GEW", "BUR": "BUR"}


def roof_override(osm):
    o = OVERRIDES.get((osm or {}).get("name", ""), {})
    return tuple(o["roof"]) if "roof" in o else None


def building_style(bid, btype, height, osm=None):
    """Return (facade layer, tint) for a building. `osm` = tags of the matching OSM building (use, colour, name)."""
    h = h32(bid)
    osm = osm or {}
    o = OVERRIDES.get(osm.get("name", ""))
    if o:  # hand-checked landmark (pipeline/overrides/buildings.json)
        return pick(h, [(1, globals()[o["style"]])]), tuple(o.get("tint", TINTS[0]))
    vis = osm.get("_visual")
    if vis and vis.get("style"):  # seen on a reference photo (research/buildings/visual_notes.json)
        return pick(h, [(1, globals()[vis["style"]])]), tuple(vis["tint"] or TINTS[(h >> 4) % len(TINTS)])
    vis_tint = (osm.get("_visual") or {}).get("tint")
    tint = tuple(vis_tint) if vis_tint else parse_colour(osm.get("building:colour")) or TINTS[(h >> 4) % len(TINTS)]
    use = osm.get("building", "")
    g = osm.get("_gwr") or {}
    period, cls = int(g.get("period") or 0), int(g.get("class") or 0)
    # official class (GWR GKLAS) first
    if cls in (1220,) and height > 10:
        return pick(h, [(3, BUR), (2, NEU), (1, B70)]), tint
    if cls in (1251, 1252, 1242, 1241):
        return pick(h, [(1, GEW)]), tint
    if cls in (1263, 1264, 1261, 1262, 1265, 1275):
        return pick(h, [(2, GEN), (2, NEU), (1, B50)]), tint
    # construction period (GWR GBAUP) decides the facade family
    if period == 11:   # before 1919: Gründerzeit / Jugendstil Blockrand
        return pick(h, [(78, ALT), (22, JUG)]), tint
    if period == 12:   # 1919–45: Genossenschaft, Neues Bauen
        return pick(h, [(70, GEN), (30, ALT)]), tint
    if period == 13:   # 1946–60
        return pick(h, [(70, B50), (30, GEN)]), tint
    if period in (14, 15):  # 1961–80
        return pick(h, [(50, B50), (50, B70)]), tint
    if period in (16, 17, 18, 19):  # 1981–2000
        return pick(h, [(50, B70), (50, NEU)]), tint
    if period >= 20:   # 21st century
        return pick(h, [(80, NEU), (20, BUR)]), tint
    if use in ("office", "commercial") and height > 12:
        return pick(h, [(3, BUR), (2, NEU), (1, B70)]), tint
    if use in ("industrial", "warehouse", "garages", "garage", "service", "shed"):
        return pick(h, [(1, GEW)]), tint
    if use in ("school", "public", "civic", "hospital", "university", "kindergarten"):
        return pick(h, [(2, GEN), (2, NEU), (1, B50)]), tint
    if use == "retail" and height < 12:
        return pick(h, [(2, NEU), (1, GEW)]), tint
    if btype == "Hochhaus" or height > 40:
        return pick(h, [(1, BUR)]), (255, 255, 255)
    if height > 24:
        return pick(h, [(3, B70), (3, BUR), (2, B50), (2, NEU)]), tint
    if height < 9:  # low sheds, workshops, outbuildings
        return pick(h, [(4, GEW), (2, GEN), (2, ALT), (1, NEU)]), tint
    return pick(h, [(46, ALT), (10, JUG), (14, GEN), (11, B50), (5, B70), (7, NEU), (5, GEW), (2, BUR)]), tint


# POI kind (OSM shop=/amenity=) -> shopfront type (variants a/b picked by hash, see gen_shopfronts.BASE)
KIND_SHOP = {"cafe": "cafe", "ice_cream": "cafe", "restaurant": "restaurant", "bar": "bar", "pub": "bar", "biergarten": "bar",
             "nightclub": "club", "fast_food": "kebab", "food_court": "kebab", "kiosk": "kiosk", "tobacco": "kiosk", "newsagent": "kiosk",
             "convenience": "spaeti", "deli": "spaeti", "supermarket": "super", "greengrocer": "gemuese", "florist": "gemuese",
             "hairdresser": "coiffeur", "beauty": "coiffeur", "massage": "coiffeur", "tattoo": "coiffeur",
             "bicycle": "velo", "bakery": "baeckerei", "pastry": "baeckerei", "confectionery": "baeckerei",
             "pharmacy": "apotheke", "doctors": "apotheke", "dentist": "apotheke", "optician": "apotheke",
             "bank": "bank", "travel_agency": "bank", "government": "bank",
             "clothes": "laden", "shoes": "laden", "books": "laden", "jewelry": "laden", "furniture": "laden", "music": "laden",
             "tailor": "laden", "interior_decoration": "laden",
             "company": "buero", "it": "buero", "architect": "buero", "graphic_design": "buero", "kindergarten": "buero",
             "childcare": "buero", "community_centre": "buero", "car_repair": "buero",
             "vacant": "leer"}
FALLBACK = ["leer"] * 3 + ["buero"] * 3 + ["laden", "laden", "kiosk", "cafe", "coiffeur", "spaeti", "bank", "apotheke"]


def shop_layer(bid, k, kind=None):
    base = KIND_SHOP.get(kind) if kind else None
    h = h32(bid) + k
    if base is None:
        base = FALLBACK[h % len(FALLBACK)]
    names = BASE[base]
    return LAYER[names[(h >> 4) % len(names)]]
