"""Write research/buildings/sheets_k4/candidates_k4.json (photo source per address) from k4/photos.json, for facades_notes.py (quelle + credits)."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent.parent
P = json.load(open(ROOT / "research/buildings/k4/photos.json"))
out = {a: {"imgs": [dict(id=v["photos"][0]["id"], src=v["photos"][0]["source"], by=v["photos"][0]["creator"] or "unknown")]}
       for a, v in P.items() if v.get("photos")}
json.dump(out, open(ROOT / "research/buildings/sheets_k4/candidates_k4.json", "w"), ensure_ascii=False)
print(len(out))
