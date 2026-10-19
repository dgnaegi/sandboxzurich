"""Photo-based shopfront notes (research/shops_v3/shops_v3.json, Mapillary/Panoramax sightings) -> compact per-sign style.

Attached to the tile's `signs` rows by props.signs as `v` (only for venues with photo_ok notes); the runtime
(web/src/world/storefront_style.ts) invents plausible values for all other venues. No logos: only colours, style codes
and the real venue name (drawn as free font at runtime).
Keys: b/f sign background/text hex, s style (box|letters|neon|paint|blade|plain), a awning hex (absent = none seen),
as 1 = striped, c facade hex, w window (gross|klein|Sprossen|offen), t 1 = outdoor seating, p 1 = plants, n 1 = neon.
"""
import json
import re

from shapely.geometry import Point

from config import ROOT

SRC = ROOT / "research" / "shops_v3" / "shops_v3.json"
STYLE = {"lightbox": "box", "round": "box", "oval": "box", "sign": "box", "logo": "box", "frame": "box", "vertical": "box", "flag": "box",
         "letters": "letters", "vinyl": "letters", "script": "letters", "graphic": "letters", "canopy": "letters",
         "neon": "neon", "painted": "paint", "band": "paint", "blade": "blade", "none": "plain", "container": "plain"}
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
_cache = {}


def _hex(v):
    return v.lower() if isinstance(v, str) and HEX.match(v) else None


def _norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


def compact(r):
    f = r.get("fascia") or {}
    out = {}
    for k, v in (("b", _hex(f.get("bg"))), ("f", _hex(f.get("text"))), ("s", STYLE.get(f.get("style") or "")),
                 ("c", _hex(r.get("facade_color")))):
        if v:
            out[k] = v
    aw = r.get("awning")
    if isinstance(aw, dict) and _hex(aw.get("color")):
        out["a"] = _hex(aw["color"])
        if aw.get("stripes"):
            out["as"] = 1
    if r.get("shopwindow") in ("gross", "klein", "Sprossen", "offen"):
        out["w"] = r["shopwindow"]
    if r.get("seating") is True:
        out["t"] = 1
    if r.get("plants") is True:
        out["p"] = 1
    if r.get("neon"):
        out["n"] = 1
    return out


def _load():
    if not _cache:
        rows = [r for r in json.load(open(SRC, encoding="utf-8")) if r.get("photo_ok")]
        _cache["id"] = {str(r["id"]).lstrip("nwr"): r for r in rows}
        _cache["rows"] = rows
    return _cache


# --- zone overrides (pipeline/overrides/storefronts_z*.json: {"<osm id>": {"name": display name, "v": {notes}}}) ---
def _overrides():
    if "ovr" not in _cache:
        o = {}
        for f in sorted((ROOT / "pipeline" / "overrides").glob("storefronts_z*.json")):
            o.update({k: v for k, v in json.load(open(f, encoding="utf-8")).items() if not k.startswith("_")})
        _cache["ovr"] = o
    return _cache["ovr"]


def is_closed(poi):
    """Venue confirmed closed (override "closed": true, with source): no sign for it."""
    return bool((_overrides().get(str(poi.get("osm")).lstrip("nwr")) or {}).get("closed"))


def display_name(poi):
    """Venue name for the sign: override (renamed venue) or the OSM name."""
    return (_overrides().get(str(poi.get("osm")).lstrip("nwr")) or {}).get("name", poi["name"])


def notes_for(poi):
    """-> compact dict for a POI (by OSM id, else same normalised name within 40 m), or None. Zone overrides win."""
    base = _notes_photo(poi)
    ov = (_overrides().get(str(poi.get("osm")).lstrip("nwr")) or {}).get("v")
    return {**(base or {}), **ov} if ov else base


def _notes_photo(poi):
    c = _load()
    r = c["id"].get(str(poi.get("osm")))
    if r is None:
        nm = _norm(poi["name"])
        p = Point(poi["x"], poi["y"])
        r = next((q for q in c["rows"] if _norm(q["name"]) == nm and p.distance(Point(q["x"], q["y"])) < 40), None)
    return compact(r) if r else None


def shop_notes(poi):
    """Window/door notes for the shopfront texture choice (styles.shop_layer, facade._wall): {"w": gross|klein|Sprossen, "d": mitte|corner}."""
    c = notes_for(poi)
    if not c:
        return None
    r = _load()["id"].get(str(poi.get("osm")))
    d = (r or {}).get("door")
    return {"w": c.get("w"), "d": d if d in ("mitte", "corner") else None}


def facade_tints():
    """{(street, nr): {"tint": rgb, ...}} whole-building wall tint from shops_v3 facade_color (light enough to be wall, not socle)."""
    out = {}
    for r in _load()["rows"]:
        hx = _hex(r.get("facade_color"))
        m = re.match(r"(.+?)\s+(\d+[a-zA-Z]?)\s*(,.*)?$", (r.get("address") or "").strip())
        if not hx or not m or "unsicher" in (r.get("notes") or "").lower():
            continue  # photo may show the neighbouring house: never tint a whole building from it
        rgb = [int(hx[i:i + 2], 16) for i in (1, 3, 5)]
        lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
        if lum < 0.42:
            continue
        rgb = tuple(int(c * 0.8 + 255 * 0.2) for c in rgb)  # estimated from a distance: pull slightly towards white
        out[(m.group(1).strip(), m.group(2))] = {"tint": rgb, "style": None, "v3": {}}
    return out
