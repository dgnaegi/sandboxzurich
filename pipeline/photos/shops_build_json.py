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
# --- round 2 (Panoramax / Mapillary 360 crops): photos_r2.json + annotations_r2.jsonl, never overwrites round-1 annotations ---
R2 = json.load(open(D / "photos_r2.json")) if (D / "photos_r2.json").exists() else {}
ann2 = {}
if (D / "annotations_r2.jsonl").exists():
    for l in open(D / "annotations_r2.jsonl"):
        if l.strip(): a = json.loads(l); ann2[a.pop("id")] = a
byid = {e["id"]: e for e in out}
for k, v in R2.items():
    if not v["photos"]: continue
    c = cand[k]; e = byid.get(k)
    if e is None:
        e = dict(id=k, name=c["name"], address=c["address"], kind=c["kind"], area=c["area"], x=round(c["x"], 1), y=round(c["y"], 1), photos=[], sheet=None, photo_ok=None)
        out.append(e); byid[k] = e
    e["photos_r2"] = [dict(file=p["file"], source=p["source"], pano=p["pano"], page=p["page"], date=p["date"], creator=p["creator"], license=p["license"], dist_m=p["dist_m"]) for p in v["photos"]]
    if k in ann2 and not e["photo_ok"]:
        e.update(ann2[k]); e["photo_ok"] = True; e["annotated_from"] = "r2:" + e["photos_r2"][0]["source"]
    elif k in ann2: e["photo_ok"] = True
    elif e["photo_ok"] is None: e["photo_ok"] = False if R2 else None
for k, a in ann2.items():   # R2 annotations made on an R1 photo (venue without R2 photo)
    e = byid.get(k)
    if e and not e["photo_ok"]: e.update(a); e["photo_ok"] = True; e["annotated_from"] = "r1-sheet22+:mapillary"
json.dump(out, open(D / "shops_v3.json", "w"), ensure_ascii=False, indent=1)
import collections
src = collections.Counter(e.get("annotated_from", "mapillary r1") for e in out if e["photo_ok"])
print("sources of photo_ok:", dict(src))
ok = sum(1 for e in out if e["photo_ok"]); rev = sum(1 for e in out if e["photo_ok"] is not None)
print(len(cand), "candidates;", len(out), "with photos;", rev, "reviewed;", ok, "annotated")
cr = ["# Credits shops_v3\n", "Alle Fotos: Mapillary, Lizenz CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), Namensnennung = Mapillary-Nutzername.",
      "Die Bilder in data/raw/photos/shops/ sind nur Referenz (nicht ins Spiel eingebunden, keine Texturen). Google, Laden-Websites und Instagram wurden nicht verwendet.\n",
      "| Lokal | Mapillary-Bild | Urheber | Jahr |", "|---|---|---|---|"]
for e in out:
    for p in e["photos"]: cr.append(f"| {e['name'].replace('|','/')} | {p['page']} | {p['creator']} | {p['year']} |")
cr += ["", "## Runde 2 (Panoramax und Mapillary-360°, perspektivische Ausschnitte)", "", "Lizenz je Bild CC-BY-SA-4.0 (Panoramax: Feld license); Quelle und Urheber unten. Ausschnitte in data/raw/photos/shops_r2/ sind abgeleitete Referenzbilder (nicht im Spiel).", "",
       "| Lokal | Quelle | Bild | Urheber | Datum | Lizenz |", "|---|---|---|---|---|---|"]
for e in out:
    for p in e.get("photos_r2", []): cr.append(f"| {e['name'].replace('|','/')} | {p['source']} | {p['page']} | {p['creator']} | {p['date']} | {p['license']} |")
(D / "CREDITS.md").write_text("\n".join(cr) + "\n")
