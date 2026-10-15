"""Merge hand-read facade notes (research/buildings/sheets_v3/notes_raw_*.tsv) into research/buildings/visual_notes_v3.json
and write research/buildings/CREDITS_v3.md (Mapillary CC BY-SA 4.0 authors/images) from candidates.json.

TSV columns (| separated, '#' lines ignored): addr | hex | mat | floors | axes | win | shutter | frame | ext | roof | style | free text
  mat   P putz  K klinker  S sandstein  B beton  G glas  H holz
  win   r hoch-rechteckig  a bogen  h verdachung  b fensterband  g glas  k klein/quadratisch
  shutter n keine  g gruen  s grau  b braun  u blau  r rot      (empty = unknown)
  frame w weiss  d dunkel  h holz
  ext   letters: G gesims  E erker  B balkon  V verdachung  R rustika-Sockel  L loggia  M mansarde  D gauben  A attika
  roof  m mansard  s sattel  w walm  f flach  t attika/zurueckversetzt
  style g gruenderzeit  j jugendstil  h heimatstil/genossenschaft  5 50er  6 60er  7 70er  n neubau  b buero  w gewerbe
Empty fields = not visible / uncertain (left out of the JSON)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
D = ROOT / "research" / "buildings"
S = D / "sheets_v3"
MAT = dict(P="putz", K="klinker", S="sandstein", B="beton", G="glas", H="holz")
WIN = dict(r="hoch", a="bogen", h="verdachung", b="band", g="glas", k="klein")
SH = dict(n="keine", g="gruen", s="grau", b="braun", u="blau", r="rot")
FR = dict(w="weiss", d="dunkel", h="holz")
EXT = dict(G="gesims", E="erker", B="balkon", V="verdachung", R="rustika", L="loggia", M="mansarde", D="gauben", A="attika")
ROOF = dict(m="mansard", s="sattel", w="walm", f="flach", t="attika")
STIL = dict(g="gruenderzeit", j="jugendstil", h="heimatstil", **{"5": "50er", "6": "60er", "7": "70er"}, n="neubau", b="buero", w="gewerbe")


def main():
    out = {}
    cand = json.load(open(S / "candidates.json"))
    for f in sorted(S.glob("notes_raw_*.tsv")):
        for ln in f.read_text().splitlines():
            if not ln.strip() or ln.startswith("#"):
                continue
            c = [x.strip() for x in ln.split("|")] + [""] * 12
            addr, hx, mat, fl, ax, win, sh, fr, ext, roof, style, txt = c[:12]
            v = {}
            if re.fullmatch(r"#?[0-9a-fA-F]{6}", hx):
                v["hex"] = "#" + hx.lstrip("#").lower()
            for key, val, tab in (("material", mat, MAT), ("fenster", win, WIN), ("laeden", sh, SH), ("rahmen", fr, FR),
                                  ("dach", roof, ROOF), ("stil", style, STIL)):
                if val in tab:
                    v[key] = tab[val]
            if fl.isdigit():
                v["geschosse"] = int(fl)
            if ax.isdigit():
                v["achsen"] = int(ax)
            e = [EXT[ch] for ch in ext if ch in EXT]
            if e:
                v["details"] = e
            if txt:
                v["notiz"] = txt
            if not v:
                continue
            im = (cand.get(addr, {}).get("imgs") or [{}])[0]
            if im:
                v["quelle"] = f"mapillary:{im['id']}"
            out[addr] = v
    meta = {"_meta": "v3 (2026-10-15): Fassaden aus Mapillary-Fotos (CC BY-SA 4.0, ab 2020), von Hand gelesen; Felder siehe pipeline/photos/facades_notes.py. "
                     "Leere Felder = nicht sichtbar/unsicher. Credits: CREDITS_v3.md"}
    json.dump({**meta, **dict(sorted(out.items()))}, open(D / "visual_notes_v3.json", "w"), ensure_ascii=False, indent=0)
    used = {a: cand[a]["imgs"][0] for a in out if cand.get(a, {}).get("imgs")}
    by = {}
    for a, im in used.items():
        by.setdefault(im["by"], []).append(im["id"])
    lines = ["# Credits visual_notes_v3", "",
             "Fassadenangaben (Farbe, Material, Fensterformen) wurden von Hand aus Strassenfotos auf Mapillary gelesen; es wurden keine Bilder "
             "ins Spiel uebernommen. Fotos: Mapillary-Beitragende, CC BY-SA 4.0 (https://www.mapillary.com).", "",
             f"{len(out)} Adressen, {len(used)} mit Mapillary-Bild. Beitragende (Anzahl Bilder, Beispiel-ID):", ""]
    for u, ids in sorted(by.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"- {u}: {len(ids)} (https://www.mapillary.com/app/?pKey={ids[0]})")
    (D / "CREDITS_v3.md").write_text("\n".join(lines) + "\n")
    print(len(out), "addresses ->", D / "visual_notes_v3.json")


if __name__ == "__main__":
    main()
