"""Texture layer indices and building style rules."""
import hashlib

from gen_textures import LAYERS, SHOPS
from gen_shopfronts import BASE, SPECS
SPECS_WIN = {f"shop_{k}": v.get("win") for k, v in SPECS.items()}

LAYER = {n: i for i, n in enumerate(LAYERS)}
LAYER_NAME = {i: n for n, i in LAYER.items()}

# Zürich plaster tints (sRGB): cream, ochre, light grey, salmon, pale green, white, sand, pale blue
TINTS_RAW = [(240, 226, 196), (232, 200, 140), (214, 212, 206), (236, 196, 176), (206, 222, 200),
             (246, 244, 236), (226, 210, 170), (204, 214, 224), (238, 214, 160), (220, 186, 160)]


def _desat(c, k=0.45):
    """Fidelity S6: generic (not photo-measured) plaster tints are calmer than the old palette (photo comparison: white, light grey, cream)."""
    y = 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    return tuple(int(round(y + (v - y) * (1 - k))) for v in c)


TINTS = [_desat(c) for c in TINTS_RAW]  # only the generic fallback; measured / noted colours stay exact
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
NEU = ["neubau_a", "neubau_a", "neubau_c", "neubau_c", "neubau_b"]  # b (stone panels) is the rarest: it read as a grey window grid
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


import numpy as np  # noqa: E402

GAIN3 = 1.35  # facade v3 layers: the shader multiplies the vertex tint by this (bright neutral base can reach light colours)
_BASE3 = {}


def _lin(a):
    a = np.asarray(a, np.float64)
    return np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4)


def exact_tint(layer_name, rgb):
    """Vertex tint (sRGB 0-255) that makes the neutral v3 layer show colour `rgb` (sRGB) on its tintable pixels."""
    if not _BASE3:
        f = Path(__file__).parent.parent / "data" / "build" / "facades" / "base_means.json"
        _BASE3.update(json.load(open(f)) if f.exists() else {})
    base = _BASE3.get(layer_name)
    if base is None:
        return tuple(rgb)
    t = np.clip(_lin(np.asarray(rgb) / 255) / (np.asarray(base) * GAIN3), 0, 1)
    s = np.where(t <= .0031308, t * 12.92, 1.055 * t ** (1 / 2.4) - .055)
    return tuple(int(round(v * 255)) for v in s)


def v3_layer_name(v, height=20.0, year=None):
    """Facade layer (v3 family) for a structured note, or None when the note does not describe a plaster/brick/stone Altbau."""
    mat, win, sh, ext, st = v.get("mat"), v.get("win"), v.get("shutter"), v.get("ext") or [], v.get("style")
    if st is None and year:
        st = "g" if year < 1919 else "h" if year < 1946 else "5" if year < 1960 else None
    if st in ("g", "j") or (st is None and mat in ("K", "S")):
        if mat == "K":
            return "k3_klinker_" + ("b" if win == "a" else "c" if win == "h" else "a")
        if mat == "S":
            return "k3_sand_" + ("b" if win == "a" else "a")
        if mat not in (None, "P"):
            return None
        bal = "balkon" in ext or "balkone" in ext
        if win == "a" or st == "j":
            return "g3_arch_" + ("g" if sh == "g" else "n")
        if win == "h" or "verdachung" in ext:
            return "g3_hood_" + (sh if sh in ("g", "s") else "n")
        if sh in ("g", "s", "b", "u"):
            return "g3_plain_" + sh
        if sh == "r":
            return "g3_plain_b"
        return "g3_plain_n" if bal else "g3_flat_n"
    if st == "h":
        return "e3_gen_" + (sh if sh in ("g", "b", "u") else "n")
    if st == "5":
        if mat == "K":
            return "k3_klinker_50"
        return "n3_50_" + ("s" if sh == "s" else "n")
    if st == "6" and mat in (None, "P") and win in ("b", None):
        return "n3_band60"
    return None


def building_style(bid, btype, height, osm=None):
    """Return (facade layer, tint) for a building. `osm` = tags of the matching OSM building (use, colour, name)."""
    h = h32(bid)
    osm = osm or {}
    o = OVERRIDES.get(osm.get("name", ""))
    if o:  # hand-checked landmark (pipeline/overrides/buildings.json)
        return pick(h, [(1, globals()[o["style"]])]), tuple(o.get("tint", TINTS[0]))
    vis = osm.get("_visual")
    if vis and vis.get("v3"):  # structured photo / text notes -> v3 layers with exact colour
        v3 = vis["v3"]
        g = osm.get("_gwr") or {}
        nm = v3_layer_name(v3, height, int(g.get("year") or 0) or None) if (vis.get("photo") or v3.get("style") in ("g", "j", "h", "5", "6")
                                                                     or v3.get("mat") in ("K", "S")) else None
        if nm:
            rgb = vis.get("tint") or TINTS[(h >> 4) % len(TINTS)]
            return LAYER[nm], exact_tint(nm, rgb)
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


def shop_layer(bid, k, kind=None, win=None):
    """Shopfront atlas layer; `win` (photo notes: gross|klein|Sprossen) selects the window variant (_c small, _d glazing bars)."""
    base = KIND_SHOP.get(kind) if kind else None
    h = h32(bid) + k
    if base is None:
        base = FALLBACK[h % len(FALLBACK)]
    names = BASE[base]
    want = {"klein": "klein", "Sprossen": "sprossen"}.get(win or "")
    alt = [n for n in names if want and SPECS_WIN.get(n) == want]
    if alt:
        return LAYER[alt[(h >> 4) % len(alt)]]
    plain = [n for n in names if not n.endswith(("_c", "_d"))] or names
    return LAYER[plain[(h >> 4) % len(plain)]]
