"""Per-address facade colour/style from photo notes (research/buildings/visual_notes.json, R2 photo research).
Returns {(street, nr): {"tint": (r, g, b), "style": family|None}} for use in build_testarea."""
import json
import re

from config import ROOT

COLOURS = [  # first match in the note wins (order: specific before generic)
    ("lachs", (236, 186, 166)), ("mint", (196, 222, 198)), ("hellgruen", (200, 222, 196)), ("gruen", (186, 206, 176)),
    ("ocker", (226, 192, 128)), ("terrakotta", (210, 138, 98)), ("orange", (226, 160, 100)), ("ziegelrot", (176, 92, 72)),
    ("klinker", (166, 92, 70)), ("backstein", (166, 92, 70)), ("rosa", (236, 198, 196)), ("gelb", (236, 214, 142)),
    ("creme", (240, 228, 200)), ("beige", (230, 214, 182)), ("weiss", (244, 242, 236)), ("blau", (192, 206, 224)),
    ("braun", (168, 130, 102)), ("grau", (198, 198, 196)),
]


SHUTTER_WORDS = [("gruen", "g"), ("grau", "s"), ("braun", "b"), ("blau", "u"), ("rot", "r"), ("weiss", "n")]


def parse_text(note):
    """v2/v1 free-text note -> structured v3 fields (only what the text states)."""
    low = note.lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")
    low = low.split(" gwr:")[0].replace("(unsicher)", "")
    v = {}
    tint = next((c for w, c in COLOURS if w in low), None)
    if tint and "nachbar" not in low:
        v["rgb"] = tint
    if any(w in low for w in ("klinker", "backstein", "ziegelrot")) and "dach" not in low.split("ziegelrot")[0][-6:]:
        v["mat"] = "K"
    elif "sandstein" in low:
        v["mat"] = "S"
    elif "beton" in low:
        v["mat"] = "B"
    m = re.search(r"(gruene|graue|braune|blaue|rote|weisse)[nr]? (fensterl|laeden)", low)
    if m:
        v["shutter"] = dict(gruene="g", graue="s", braune="b", blaue="u", rote="r", weisse="n")[m.group(1)]
    elif "fensterlaeden" in low or "laeden" in low and "laeden:" not in low and "ladenz" not in low and "geschaeft" not in low:
        v["shutter"] = "g"
    ext = [k for k, w in (("balkon", "balkon"), ("erker", "erker"), ("gesims", "gesims")) if w in low]
    if ext:
        v["ext"] = ext
    if "rundbogen" in low or "bogenfenster" in low:
        v["win"] = "a"
    elif "fensterbaend" in low or "fensterreihen" in low:
        v["win"] = "b"
    for w, st in (("jugendstil", "j"), ("gruenderzeit", "g"), ("altbau", "g"), ("blockrand", "g"), ("genossenschaft", "h"), ("heimatstil", "h"),
                  ("nachkrieg", "5"), ("50er", "5"), ("60er", "6"), ("70er", "7"), ("buerobau", "b"), ("neubau", "n"), ("glas", "n"), ("modern", "n")):
        if w in low:
            v["style"] = st
            break
    m = re.search(r"(\d+)\+? gesch", low)
    if m:
        v["floors"] = int(m.group(1))
    return v


MAT = {"putz": "P", "klinker": "K", "sandstein": "S", "beton": "B", "glas": "G", "holz": "H", "stein": "S"}
WIN = {"hoch": "r", "rechteck": "r", "bogen": "a", "rundbogen": "a", "verdachung": "h", "band": "b", "glas": "g", "klein": "s"}
STIL = {"gruenderzeit": "g", "jugendstil": "j", "heimatstil": "h", "genossenschaft": "h", "50er": "5", "60er": "6", "70er": "7",
        "neubau": "n", "buero": "b", "gewerbe": "w", "historismus": "g", "neoklassizismus": "g"}
SHUT = {"gruen": "g", "grau": "s", "braun": "b", "blau": "u", "rot": "r", "weiss": "n", "keine": "n", "-": "n"}


def norm_v3(v):
    """Human-readable v3 note -> short codes used by styles.v3_layer()."""
    o = dict(v)
    o["mat"] = MAT.get(str(v.get("material", "")).lower())
    o["win"] = WIN.get(str(v.get("fenster", "")).lower())
    o["style"] = STIL.get(str(v.get("stil", "")).lower())
    sh = str(v.get("laeden", "")).lower()
    o["shutter"] = SHUT.get(sh) if sh else None
    ext = [str(x).lower() for x in (v.get("details") or [])]
    o["ext"] = [e for e in ext]
    if "verdachung" in ext and not o["win"]:
        o["win"] = "h"
    o["floors"] = v.get("geschosse")
    o["axes"] = v.get("achsen")
    return o


def load_v3():
    """Structured notes research/buildings/visual_notes_v3.json: {addr: {hex, mat, floors, axes, win, shutter, frame, ext, roof, style}}."""
    f = ROOT / "research" / "buildings" / "visual_notes_v3.json"
    out = {}
    if f.exists():
        for addr, v in json.load(open(f)).items():
            if addr.startswith("_") or not isinstance(v, dict):
                continue
            m = re.match(r"(.+?)\s+(\d+[a-zA-Z]?)$", addr.strip())
            if m:
                v = norm_v3(v)
                if v.get("hex"):
                    h = v["hex"].lstrip("#")
                    v["rgb"] = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
                out[(m.group(1).strip(), m.group(2))] = v
    return out


def load():
    notes = {}
    for fn in ("visual_notes_v2.json", "visual_notes.json"):  # v1 listed last: it wins on duplicates, v2 only adds
        f = ROOT / "research" / "buildings" / fn
        if f.exists():
            notes.update(json.load(open(f)))
    out = {}
    for addr, note in notes.items():
        if addr.startswith("_"):
            continue
        m = re.match(r"(.+?)\s+(\d+[a-zA-Z]?)$", addr.strip())
        if not m:
            continue
        low = note.lower().replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")
        tint = next((c for w, c in COLOURS if w in low), None)
        style = None
        if any(w in low for w in ("nachkrieg", "fensterbaend", "buerobau", "50er", "60er", "70er")):
            style = "B50"
        elif any(w in low for w in ("klinker", "backstein")):
            style = "GEW"
        elif "jugendstil" in low:
            style = "JUG"
        elif any(w in low for w in ("gruenderzeit", "erker", "gesims")):
            style = "ALT"
        elif any(w in low for w in ("neubau", "glas", "modern")):
            style = "NEU"
        if tint or style:
            out[(m.group(1).strip(), m.group(2))] = {"tint": tint, "style": style, "v3": parse_text(note)}
    import shopfronts_v3
    for k, v in shopfronts_v3.facade_tints().items():  # venue photo notes: wall tint of the whole house, only where no other note exists
        out.setdefault(k, v)
    for k, v in load_v3().items():  # photo-checked structured notes beat everything
        out[k] = {"tint": v.get("rgb"), "style": None, "v3": v, "photo": True}
    return out


if __name__ == "__main__":
    o = load()
    print(len(o), "addresses with colour/style;", sum(1 for v in o.values() if v["style"]), "with style;",
          sum(1 for v in o.values() if v.get("photo")), "from v3 photo notes")
