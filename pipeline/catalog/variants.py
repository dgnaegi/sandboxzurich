"""Variant rules + counts for the object catalog (Auftrag K1).

Writes research/catalog/variant_counts.json (counts per variant from data rules) and
research/catalog/assign_hints.json (object -> variant, ONLY for objects whose variant was
confirmed by eye on a photo <= 12 m away; list in VISUAL_CONFIRMED below).
Usage: .venv/bin/python pipeline/catalog/variants.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sheets import trog_family  # noqa: E402

ROOT = HERE.parents[1]
CAT = ROOT / "research" / "catalog"

BRUNNEN_VARIANTS = {
    "V8_notwasser": "Notwasserbrunnen (art = Notwasserbrunnen)",
    "V6_figur": "Figurenbrunnen (Figur auf Trog/Saeule, meist Bronze)",
    "V1_saeule_trog": "Saeulenbrunnen (Saeule + Trog, Stein)",
    "V2_stein_trog": "Trogbrunnen Stein (Granit/Kalkstein/Sandstein/Gneis, ohne Saeule)",
    "V3_bronze_trog": "Trog Bronzeguss",
    "V4_beton": "Betontrog / Betonbassin",
    "V5_kunststein": "Kunststein-Trog (flach, rund)",
    "V7_wandbrunnen": "Wandbrunnen in Nische (nicht aus Daten ableitbar, nur Foto)",
    "V9_holz": "Holztrog",
    "V10_ohne_angabe": "ohne Materialangabe (Foto noetig)",
}


def brunnen_variant(a):
    if a.get("art") == "Notwasserbrunnen" or a.get("brunnenart") == "Notwasserbrunnen":   # 27 objects; photos (Hardplatz, Baeckerstrasse) confirm the type
        return "V8_notwasser"
    if a.get("material_figur"):
        return "V6_figur"
    if a.get("material_trog") and a.get("material_saeule"):
        return "V1_saeule_trog"
    if not a.get("material_trog"):
        return "V10_ohne_angabe"
    fam = trog_family(a["material_trog"])
    return {"bronze": "V3_bronze_trog", "beton": "V4_beton", "kunststein": "V5_kunststein",
            "holz": "V9_holz"}.get(fam, "V2_stein_trog")


# Visual confirmations (photo <= 12 m, object clearly in frame). Wall niche fountains are
# not identifiable by the data rule (BR-111/BR-260 carry a Saeule value but are Wandbrunnen).
VISUAL_CONFIRMED = {
    "BR-41": "V4_beton",          # round concrete basin with central jet
    "BR-429": "V5_kunststein",    # flat round Kunststein basin
    "BR-607": "V5_kunststein",    # Kunststein basin with spout, Friedhof Sihlfeld
    "BR-609": "V2_stein_trog",    # oval granite double basin, Feld School
    "BR-278": "V2_stein_trog",    # round granite basin with relief band
    "BR-284": "V6_figur",         # bronze figure in wall niche (Froeschen-Brunnen)
    "BR-111": "V7_wandbrunnen",   # wall niche with shell ornament, Schulhaus Limmat
    "BR-260": "V7_wandbrunnen",   # same site as BR-111
}


def stops_counts(objs):
    out = {}
    wh = [o for o in objs if o.get("layer") == "wartehalle"]
    out["H1_wh_2018"] = sum(1 for o in wh if str(o["attrs"].get("einbaudatum", ""))[:4] == "2018")
    out["H2_wh_aelter_oder_unbekannt"] = len(wh) - out["H1_wh_2018"]
    ta = [o for o in objs if o.get("layer") == "ticketautomat"]
    out["H3_ticketautomat_typ20"] = len(ta)
    dfi = [o for o in objs if o.get("layer") == "dfi_anzeiger"]
    out["H4_dfi_wand"] = sum(1 for o in dfi if o["attrs"].get("typ") == "Info Smart")
    out["H5_dfi_decke"] = sum(1 for o in dfi if o["attrs"].get("typ") != "Info Smart")
    sb = Counter(str(o["attrs"].get("typ")) for o in objs if o.get("layer") == "sitzgelegenheit")
    out["sitzgelegenheit_by_typ"] = dict(sb.most_common())
    out["plakatstelle"] = sum(1 for o in objs if o.get("layer") == "plakatstelle")
    out["kiosk"] = sum(1 for o in objs if o.get("layer") == "kiosk")
    out["leuchte_ewz"] = sum(1 for o in objs if o.get("layer") == "leuchte")
    out["sammelstelle"] = sum(1 for o in objs if o.get("layer") == "sammelstelle")
    return out


def main():
    objs = json.load(open(CAT / "objects.json"))
    br = [o for o in objs if o["kind"] == "brunnen"]
    bcount = Counter(brunnen_variant(o["attrs"]) for o in br)
    art = Counter(o["attrs"].get("art") for o in br)
    counts = {
        "brunnen_total": len(br),
        "brunnen_art": dict(art),
        "brunnen_by_variant": {k: bcount.get(k, 0) for k in BRUNNEN_VARIANTS},
        "haltestellen_and_moebel": stops_counts(objs),
    }
    with open(CAT / "variant_counts.json", "w", encoding="utf-8") as fh:
        json.dump(counts, fh, ensure_ascii=False, indent=1)
    hints = {k: v for k, v in VISUAL_CONFIRMED.items()}
    with open(CAT / "assign_hints.json", "w", encoding="utf-8") as fh:
        json.dump(hints, fh, ensure_ascii=False, indent=1)
    print(json.dumps(counts["brunnen_by_variant"], ensure_ascii=False))
    print(json.dumps(counts["haltestellen_and_moebel"], ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
