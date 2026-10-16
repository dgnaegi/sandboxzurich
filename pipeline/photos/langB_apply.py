"""Merge research/shops_v3/annotations_langB.jsonl (hand-read from langB photo sheets) into research/shops_v3/shops_v3.json (idempotent;
only touches ids listed in the jsonl; also attaches photos_langB metadata). Quick read-modify-write (other agents edit other entries)."""
import json
from pathlib import Path
R = Path(__file__).resolve().parent.parent.parent / "research/shops_v3"
ann = {}
for l in open(R / "annotations_langB.jsonl"):
    if l.strip():
        a = json.loads(l); ann[a.pop("id")] = a
ph = json.load(open(R / "photos_langB.json"))
d = json.load(open(R / "shops_v3.json")); n = 0
for e in d:
    if e["id"] in ann:
        e.update(ann[e["id"]]); e["photo_ok"] = True; n += 1
    if ph.get(e["id"]):
        e["photos_langB"] = [dict(file=p["shop"], source=p["source"], page=p["page"], date=p["date"], creator=p["creator"], license=p["license"]) for p in ph[e["id"]]]
json.dump(d, open(R / "shops_v3.json.tmp", "w"), ensure_ascii=False, indent=1)
(R / "shops_v3.json.tmp").replace(R / "shops_v3.json")
print("annotated", n, "of", len(ann))
