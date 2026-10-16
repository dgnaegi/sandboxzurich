"""research/sweep.json (web/tests/sweep.mjs) + research/audit_props.json -> research/sweep.md  (usage: sweep_report.py [label])"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path

R = Path("research")
CAUSE = {
    "ground_hole": "Terrain mesh (mesh_0) has no up-face within 0.7 m of tiles.ground (hmap): mesh and walk height differ, or no ground (build_testarea.py ground_tile / drape).",
    "ground_mismatch": "Visible ground differs 0.25-0.7 m from tiles.ground(): player floats/sinks. Rail land: ballast drape at -0.45 (build_testarea.py _ground_base) but hmap/ground() unchanged.",
    "building_no_collider": "Roof >3.5 m above ground without footprint collider: walk through house (pipeline colliders from footprints / landmark colliders).",
    "collider_no_building": "Footprint collider without visible roof (invisible wall).",
    "building_on_road": "Building roof on the carriageway mask (mask vs footprint overlap).",
    "floating_component": "Welded mesh part of mesh_0 whose lowest vertex is >0.6 m above any support (floating geometry).",
    "floating_over_deck": "As floating_component but over a bridge deck row (deck index) - may be the bridge itself.",
    "buried_component": "Mesh part entirely below ground.",
}


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "Lauf"
    d = json.load(open(R / "sweep.json"))
    by = defaultdict(list)
    for r in d["results"]:
        for i in r["issues"]:
            by[i["type"]].append({**i, "tile": r["name"]})
    L = [f"# Sweep ({label})", "", f"{len(d['results'])} Kacheln, {sum(len(v) for v in by.values())} Cluster. Fehler beim Laden: {len(d.get('errs', []))}. Quelle: `web/tests/sweep.mjs` (Szene-Abfragen, 1-m-Raster pro Kachel), `pipeline/audit_props.py` (Prop-Zeilen), `pipeline/sweep_report.py`.", "",
         "## Haeufigkeit nach Typ (Cluster / Zellen m2)", "", "| Typ | Cluster | Flaeche m2 | Ursache |", "|---|---|---|---|"]
    for t, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
        L.append(f"| {t} | {len(v)} | {sum(i.get('n', 1) for i in v)} | {CAUSE.get(t, '')} |")
    for t, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
        L += ["", f"### {t} (Top 12)", ""]
        key = (lambda i: -(i.get("above") or i.get("n") or 0)) if t.startswith("floating") else (lambda i: -i.get("n", 1))
        for i in sorted(v, key=key)[:12]:
            ex = {k: val for k, val in i.items() if k not in ("type", "x", "y", "tile")}
            L.append(f"- {i['tile']} ({i['x']}, {i['y']}) {ex}")
    lm = [m for m in d.get("lms", []) if m["floatAbove"] > 0.4 or m["roadFrac"] > 0.15]
    L += ["", f"## Landmarks (Sockel/Fahrbahn), {len(lm)} von {len(d.get('lms', []))} auffaellig", ""]
    for m in sorted(lm, key=lambda m: -m["floatAbove"])[:40]:
        L.append(f"- {m['name']} ({m['x']}, {m['y']}): Unterkante {m['floatAbove']} m ueber tiefstem Boden, Boden-Spanne {round(m['gmax'] - m['gmin'], 1)} m, {int(m['roadFrac'] * 100)} % der Fusspunkte auf Fahrbahn")
    act = Counter(a["type"] for a in d.get("act", []))
    L += ["", "## Akteure in Gebaeuden (Stichproben je Kachelmitte)", "", str(dict(act))]
    for a in d.get("act", [])[:15]:
        L.append(f"- {a['type']} {a['tile']} ({a['x']}, {a['y']})")
    try:
        ap = json.load(open(R / "audit_props.json")); c = Counter((i["kind"], i["type"]) for i in ap)
        L += ["", "## Props: Hoehe gegen Terrain/Deck (Daten, `audit_props.py`)", "", "| Art | Typ | Anzahl |", "|---|---|---|"] + [f"| {k} | {t} | {n} |" for (k, t), n in c.most_common(25)]
        for i in sorted(ap, key=lambda i: -abs(i["dz"]))[:15]:
            L.append(f"- {i['kind']} {i['type']} {i['tile']} ({i['x']}, {i['y']}) dz={i['dz']} deck={i['deck']}")
    except FileNotFoundError:
        pass
    (R / "sweep.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:14]))


main()
