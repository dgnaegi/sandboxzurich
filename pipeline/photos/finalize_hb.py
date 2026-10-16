"""Write research/hb/CREDITS.md from research/hb/photos.json (only files that exist) and drop entries whose file is missing."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
M = ROOT / "research/hb/photos.json"
meta = json.load(open(M))
S = ROOT / "research/hb/photos_street.json"
if S.exists():   # Mapillary / Panoramax part (fetch_hb_street.py)
    have = {Path(p["file"]).name for p in meta["photos"]}
    meta["photos"] += [p for p in json.load(open(S))["photos"] if Path(p["file"]).name not in have]
meta["photos"] = [p for p in meta["photos"] if (ROOT / p["file"]).exists()]
json.dump(meta, open(M, "w"), ensure_ascii=False, indent=1)
L = ["# HB photo credits", "", "Reference only (never textures, never redistributed with the game). Sources: Wikimedia Commons (category Zürich Hauptbahnhof + subcategories, geosearch, text search),",
     "Mapillary (CC BY-SA 4.0), Panoramax. Licence strings as given by the source API. Files: `data/raw/photos/hb/`, contact sheets `preview/ref_hb_*.jpg` (numbers = index in photos.json).", "",
     f"{len(meta['photos'])} images.", "", "| # | file | group | source | licence | author | page |", "|---|---|---|---|---|---|---|"]
for i, p in enumerate(meta["photos"]):
    L.append(f"| {i} | {Path(p['file']).name} | {p.get('group','')} | {p['source']} | {p['license']} | {str(p.get('author',''))[:60].replace('|','/')} | {p.get('page','')} |")
(ROOT / "research/hb/CREDITS.md").write_text("\n".join(L) + "\n")
import collections
print(len(meta["photos"]), dict(collections.Counter(p.get("group") for p in meta["photos"])))
