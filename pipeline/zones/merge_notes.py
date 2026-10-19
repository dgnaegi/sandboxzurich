"""Merge hand-read Zone 4 facade notes (research/zones/z4/notes_raw_z4_*.tsv, same 12-column format as pipeline/photos/facades_notes.py)
into research/buildings/visual_notes_v3.json (read by pipeline/visual_overrides.load_v3 -> build_testarea) and into research/zones/zone4_facades.json.
Only adds addresses that have no note yet (existing, photo-checked notes win). Idempotent. Re-run after pipeline/photos/facades_notes.py (it rewrites v3 from its own TSVs).
Usage: python pipeline/zones/merge_notes.py [--dry]"""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
Z = ROOT / "research/zones"; V3 = ROOT / "research/buildings/visual_notes_v3.json"
MAT = dict(P="putz", K="klinker", S="sandstein", B="beton", G="glas", H="holz")
WIN = dict(r="hoch", a="bogen", h="verdachung", b="band", g="glas", k="klein")
SH = dict(n="keine", g="gruen", s="grau", b="braun", u="blau", r="rot")
FR = dict(w="weiss", d="dunkel", h="holz")
EXT = dict(G="gesims", E="erker", B="balkon", V="verdachung", R="rustika", L="loggia", M="mansarde", D="gauben", A="attika")
ROOF = dict(m="mansard", s="sattel", w="walm", f="flach", t="attika")
STIL = dict(g="gruenderzeit", j="jugendstil", h="heimatstil", **{"5": "50er", "6": "60er", "7": "70er"}, n="neubau", b="buero", w="gewerbe")

def parse(ln):
    c = [x.strip() for x in ln.split("|")]
    if len(c) != 12: return None, "fields=%d" % len(c)
    addr, hx, mat, fl, ax, win, sh, fr, ext, roof, style, txt = c
    if not re.fullmatch(r"#?[0-9a-fA-F]{6}", hx): return None, "hex"
    v = {"hex": "#" + hx.lstrip("#").lower()}
    for key, val, tab in (("material", mat, MAT), ("fenster", win, WIN), ("laeden", sh, SH), ("rahmen", fr, FR), ("dach", roof, ROOF), ("stil", style, STIL)):
        if val:
            if val not in tab: return None, f"{key}={val}"
            v[key] = tab[val]
    if fl: v["geschosse"] = int(fl)
    if ax: v["achsen"] = int(ax)
    e = [EXT[ch] for ch in ext if ch in EXT]
    if len(e) != len(ext): return None, "ext"
    if e: v["details"] = e
    if txt: v["notiz"] = txt
    return addr, v

def main(dry):
    photos = json.load(open(Z / "z4/photos.json")); targets = {t["addr"]: t for t in json.load(open(Z / "z4/targets.json"))}
    new, bad = {}, 0
    for f in sorted((Z / "z4").glob("notes_raw_z4_*.tsv")):
        for ln in f.read_text().splitlines():
            if not ln.strip() or ln.startswith("#"): continue
            a, v = parse(ln)
            if a is None: bad += 1; print("BAD", f.name, v, ln[:70]); continue
            if a not in targets: print("unknown addr", a); continue
            ph = (photos.get(a) or {}).get("photos") or []
            if ph: v["quelle"] = f"{ph[0]['source']}:{ph[0]['id']}"
            new[a] = v
    vn = json.load(open(V3)); zf = json.load(open(Z / "zone4_facades.json"))
    add = {a: v for a, v in new.items() if a not in vn}
    print(len(new), "parsed,", bad, "bad,", len(add), "new to v3 (", len(new) - len(add), "already present)")
    if dry: return
    for a, v in add.items(): vn[a] = v
    meta = {k: v for k, v in vn.items() if k.startswith("_")}
    body = dict(sorted((k, v) for k, v in vn.items() if not k.startswith("_")))
    json.dump({**meta, **body}, open(V3, "w"), ensure_ascii=False, indent=0)
    for a, v in new.items():
        t = targets[a]; zf["entries"][a] = dict(vn.get(a, v), xy=[round(t["x"]), round(t["y"])])
    zf["entries"] = dict(sorted(zf["entries"].items()))
    json.dump(zf, open(Z / "zone4_facades.json", "w"), ensure_ascii=False, indent=1)
main("--dry" in sys.argv)
