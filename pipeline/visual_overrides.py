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
            out[(m.group(1).strip(), m.group(2))] = {"tint": tint, "style": style}
    return out


if __name__ == "__main__":
    o = load()
    print(len(o), "addresses with colour/style;", sum(1 for v in o.values() if v["style"]), "with style")
