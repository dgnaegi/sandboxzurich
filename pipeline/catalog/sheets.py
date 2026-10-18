"""Contact sheets for the object catalog (Auftrag K1).

Reads research/catalog/objects.json (written by inventory.py) and writes
preview/ref_cat_<art>_<n>.jpg: grid of photo crops, one object per cell, labelled with ID and attributes.
Images are loaded one at a time and downscaled, to keep memory low.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
CAT = ROOT / "research" / "catalog"
PREVIEW = ROOT / "preview"
COLS, ROWS = 6, 5
CELL_W, CELL_H, LABEL_H = 256, 192, 40


FAMILIES = [
    ("bronze", ("bronze", "brozeguss", "bronzenguss", "stahlguss", "eisen", "metall")),
    ("beton", ("beton",)),
    ("kunststein", ("kunststein", "weisszement", "marmorsand")),
    ("holz", ("holz",)),
    ("kalkstein", ("kalk", "muschel", "tryphon", "triphon", "marmor", "jura", "berschis", "sandstein", "quarz", "hartsandstein")),
    ("granit", ("granit", "gneis", "gneiss", "castion", "porphyr", "serizzo", "verrukano", "iragna", "onsernone",
                "cresciano", "segheria", "basalt", "urner", "wassen", "andeer", "gera", "granito")),
    ("findling", ("findling", "ackerstein")),
]


def trog_family(material):
    m = str(material).lower()
    for fam, keys in FAMILIES:
        if any(k in m for k in keys):
            return fam
    return "sonst"


def brunnen_group(a):
    """Hypothesis group from data attributes (to be confirmed by eye)."""
    if a.get("art") == "Notwasserbrunnen":
        return "B0_notwasser"
    if a.get("material_figur"):
        return "B1_figur"
    if a.get("material_trog") and a.get("material_saeule"):
        return "B2_saeule_trog"
    if a.get("material_trog"):
        return "B3_trog_" + trog_family(a["material_trog"])
    return "B4_ohne_trogangabe"


def label_for(o):
    a = o["attrs"]
    if o["kind"] == "brunnen":
        return f"{o['id']} trog={a.get('material_trog')} saeule={a.get('material_saeule')} fig={a.get('material_figur')}"
    if o["kind"] == "haltestellen":
        extra = a.get("typtext") or a.get("typ") or a.get("bezeichnung") or ""
        return f"{o['id']} {o['layer']} {str(extra)[:28]}"
    return f"{o['id']} {o.get('layer')} {str(a.get('name') or a.get('art_txt') or '')[:24]}"


def pick_photo(o):
    """Nearest photo that exists on disk and is a usable raster."""
    for ph in o["photos"]:
        p = ROOT / ph["file"]
        if p.exists() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
            return ph, p
    return None, None


def cell(o, font):
    ph, p = pick_photo(o)
    canvas = Image.new("RGB", (CELL_W, CELL_H + LABEL_H), (30, 30, 30))
    if p is not None:
        try:
            im = Image.open(p)
            im.draft("RGB", (CELL_W * 2, CELL_H * 2))
            im = ImageOps.fit(im.convert("RGB"), (CELL_W, CELL_H), Image.LANCZOS)
            canvas.paste(im, (0, 0))
            im.close()
        except Exception:
            pass
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, CELL_H, CELL_W, CELL_H + LABEL_H], fill=(20, 20, 20))
    txt = label_for(o)
    d.text((4, CELL_H + 3), txt[:44], fill=(240, 240, 240), font=font)
    d.text((4, CELL_H + 20), (f"{ph['dist_m']} m  {Path(ph['file']).name[:30]}" if ph else "kein Foto"),
           fill=(160, 200, 255), font=font)
    return canvas


def sheet(name, objs, out_path, font):
    rows = (len(objs) + COLS - 1) // COLS
    img = Image.new("RGB", (COLS * CELL_W, rows * (CELL_H + LABEL_H)), (10, 10, 10))
    for i, o in enumerate(objs):
        c = cell(o, font)
        img.paste(c, ((i % COLS) * CELL_W, (i // COLS) * (CELL_H + LABEL_H)))
    img.save(out_path, "JPEG", quality=82)
    print(f"{out_path.name}: {len(objs)} cells ({name})")


MAX_DIST_M = 12.0  # beyond this the object is usually not visible in a street photo


def with_photo(objs):
    out = []
    for o in objs:
        ph, p = pick_photo(o)
        if ph is not None and ph["dist_m"] <= MAX_DIST_M:
            out.append(o)
    return out


def make_sheets():
    objs = json.load(open(CAT / "objects.json"))
    font = ImageFont.load_default()
    PREVIEW.mkdir(exist_ok=True)
    groups = {"brunnen": [], "wartehalle": [], "ticketautomat": [], "sitzgelegenheit": [],
              "moebel": [], "dfi_anzeiger": [], "plakatstelle": []}
    for o in objs:
        if o["kind"] == "brunnen":
            groups["brunnen"].append(o)
        elif o["kind"] == "haltestellen" and o["layer"] in groups:
            groups[o["layer"]].append(o)
        elif o["kind"] == "moebel" and o["layer"] in ("kiosk", "sammelstelle", "leuchte"):
            groups["moebel"].append(o)
    plan = []
    # Brunnen: split by hypothesis group, each sheet <= 30 cells
    bg = {}
    for o in with_photo(groups["brunnen"]):
        bg.setdefault(brunnen_group(o["attrs"]), []).append(o)
    small = [o for g in bg if len(bg[g]) <= 5 for o in bg[g]]
    bg = {g: v for g, v in bg.items() if len(v) > 5}
    if small:
        bg["B5_gemischt_klein"] = small
    for g in sorted(bg):
        objs_g = sorted(bg[g], key=lambda o: o["id"])
        for k in range(0, len(objs_g), COLS * ROWS):
            plan.append(("brunnen", g + (f"_{k // (COLS * ROWS) + 1}" if len(objs_g) > COLS * ROWS else ""),
                         objs_g[k:k + COLS * ROWS]))
    # Haltestellen: first 30 with photo per layer, spread over the list
    for layer in ("wartehalle", "ticketautomat", "sitzgelegenheit", "dfi_anzeiger", "plakatstelle"):
        wp = with_photo(groups[layer])
        step = max(1, len(wp) // (COLS * ROWS))
        plan.append(("haltestellen", layer, wp[::step][:COLS * ROWS]))
    mp = [o for o in with_photo(groups["moebel"]) if o["layer"] != "leuchte"]
    plan.append(("moebel", "kiosk_sammel", mp[:COLS * ROWS]))
    for n, (art, name, cells) in enumerate(plan, 1):
        if not cells:
            continue
        sheet(name, cells, PREVIEW / f"ref_cat_{art}_{n}.jpg", font)
