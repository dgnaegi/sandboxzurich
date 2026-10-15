"""Merge candidates + photos.json + manual annotations (research/shops_v3/annotations.jsonl; sheet/index refs
into sheets/index.json) into research/shops_v3/shops_v3.json, plus CREDITS.md. Venues on sheets <= VIEWED were looked at:
unannotated ones get photo_ok=false; later ones photo_ok=null (not reviewed)."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
D = ROOT / "research/shops_v3"
cand = {c["id"]: c for c in json.load(open(D / "candidates.json"))}
photos = json.load(open(D / "photos.json"))
index = json.load(open(D / "sheets/index.json"))
ann = [json.loads(l) for l in open(D / "annotations.jsonl") if l.strip()]
VIEWED = max(a["s"] for a in ann)
VIEWED = 21
by_id = {}
for a in ann:
    by_id[index[f"sheet_{a['s']:02d}"][a["i"] - 1]] = a
out = []
for k, ph in photos.items():
    if not ph["photos"]: continue
    c = cand[k]; sn = next(int(s[6:]) for s, ids in index.items() if k in ids)
    a = by_id.get(k)
    e = dict(id=k, name=c["name"], address=c["address"], kind=c["kind"], area=c["area"], x=round(c["x"], 1), y=round(c["y"], 1),
             photos=[dict(file=p["file"], mapillary_id=p["mapillary_id"], page=p["page"], year=p["year"], creator=p["creator"], dist_m=p["dist"]) for p in ph["photos"]],
             sheet=sn, photo_ok=(True if a else (False if sn <= VIEWED else None)))
    if a: e.update({f: a[f] for f in a if f not in ("s", "i")})
    out.append(e)
json.dump(out, open(D / "shops_v3.json", "w", ensure_ascii=False and None or None, ) if False else open(D / "shops_v3.json", "w"), ensure_ascii=False, indent=1)
ok = sum(1 for e in out if e["photo_ok"]); rev = sum(1 for e in out if e["photo_ok"] is not None)
print(len(cand), "candidates;", len(out), "with photos;", rev, "reviewed;", ok, "annotated")
cr = ["# Credits shops_v3\n", "Alle Fotos: Mapillary, Lizenz CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), Namensnennung = Mapillary-Nutzername.",
      "Die Bilder in data/raw/photos/shops/ sind nur Referenz (nicht ins Spiel eingebunden, keine Texturen). Google, Laden-Websites und Instagram wurden nicht verwendet.\n",
      "| Lokal | Mapillary-Bild | Urheber | Jahr |", "|---|---|---|---|"]
for e in out:
    for p in e["photos"]: cr.append(f"| {e['name'].replace('|','/')} | {p['page']} | {p['creator']} | {p['year']} |")
(D / "CREDITS.md").write_text("\n".join(cr) + "\n")
