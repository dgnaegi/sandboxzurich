"""Collect player corrections ("Stimmt etwas nicht?" mails) and write versioned overrides.
Input (any mix):
  --csv  FILE   columns: x,y,kind,value,note   (x,y local metres; or lat,lon instead of x,y)
  --json FILE   list of {x,y,kind,value,note}
  --mail FILE   plain text of a received mail (the auto-inserted block is parsed: x=.. y=.. / WGS84 / Spielzeit / Kachel; the text above it becomes `note`)
Output: pipeline/overrides/corrections.json  {"items":[{id,x,y,lat,lon,kind,value,note,status,src}]}   (merged by id, never deletes)
Kinds understood by `--apply` (status 'ok' items only): drop_detail (adds {x,y} to overrides/details.json "drop"), note (log only).
Everything else stays 'open' until a human decides. See research/corrections.md.
Usage: .venv/bin/python pipeline/apply_corrections.py --mail mail1.txt --csv fixes.csv [--apply] [--list]"""
import argparse
import csv
import hashlib
import json
import re

from pyproj import Transformer

from config import ROOT

OV = ROOT / "pipeline" / "overrides"
OUT = OV / "corrections.json"
O = (2681400.0, 1248700.0)
_to_wgs = Transformer.from_crs(2056, 4326, always_xy=True)
_to_lv = Transformer.from_crs(4326, 2056, always_xy=True)


def make(x=None, y=None, lat=None, lon=None, kind="note", value="", note="", src="", status="open"):
    if x is None and lat is not None:
        e, n = _to_lv.transform(float(lon), float(lat))
        x, y = e - O[0], n - O[1]
    x, y = float(x), float(y)
    lon_, lat_ = _to_wgs.transform(x + O[0], y + O[1])
    cid = hashlib.sha1(f"{round(x)}|{round(y)}|{kind}|{value}|{note}".encode()).hexdigest()[:10]
    return {"id": cid, "x": round(x, 1), "y": round(y, 1), "lat": round(lat_, 6), "lon": round(lon_, 6), "kind": kind,
            "value": value, "note": note.strip(), "status": status, "src": src}


def from_mail(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    head = t.split("--- automatisch")[0]
    note = "\n".join(l for l in head.splitlines() if not l.lower().startswith(("von:", "from:", "an:", "to:", "betreff:", "subject:", "datum:", "date:"))
                     and "Was stimmt nicht?" not in l).strip()
    m = re.search(r"x=(-?[\d.]+)\s+y=(-?[\d.]+)", t)
    if not m:
        raise SystemExit(f"{path}: no 'x=.. y=..' block found")
    extra = " | ".join(x.group(0) for x in (re.search(r"Spielzeit: .*", t), re.search(r"Kachel: .*", t), re.search(r"Blickrichtung: .*", t)) if x)
    return make(m.group(1), m.group(2), kind="note", note=f"{note}\n[{extra}]", src=f"mail:{path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", action="append", default=[]); ap.add_argument("--json", action="append", default=[]); ap.add_argument("--mail", action="append", default=[])
    ap.add_argument("--apply", action="store_true"); ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    db = json.load(open(OUT)) if OUT.exists() else {"items": []}
    have = {i["id"]: i for i in db["items"]}
    new = []
    for f in a.csv:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            new.append(make(r.get("x") or None, r.get("y") or None, r.get("lat"), r.get("lon"), r.get("kind") or "note", r.get("value", ""), r.get("note", ""), f"csv:{f}", r.get("status") or "open"))
    for f in a.json:
        for r in json.load(open(f)):
            new.append(make(r.get("x"), r.get("y"), r.get("lat"), r.get("lon"), r.get("kind", "note"), r.get("value", ""), r.get("note", ""), f"json:{f}", r.get("status", "open")))
    new += [from_mail(f) for f in a.mail]
    added = 0
    for c in new:
        if c["id"] not in have:
            have[c["id"]] = c; added += 1
    db["items"] = list(have.values())
    if a.apply:
        dpath = OV / "details.json"
        det = json.load(open(dpath)) if dpath.exists() else {"drop": [], "drop_r": 1.5, "add": []}
        n = 0
        for c in db["items"]:
            if c["status"] == "ok" and c["kind"] == "drop_detail" and [c["x"], c["y"]] not in det["drop"]:
                det["drop"].append([c["x"], c["y"]]); c["status"] = "applied"; n += 1
        if n:
            dpath.write_text(json.dumps(det, ensure_ascii=False))
        print(f"applied {n} drop_detail -> {dpath.relative_to(ROOT)} (rebuild tiles to see it)")
    OUT.write_text(json.dumps(db, ensure_ascii=False, indent=1))
    from collections import Counter
    print(f"{len(db['items'])} corrections ({added} new); status {dict(Counter(i['status'] for i in db['items']))}")
    if a.list:
        for i in db["items"]:
            print(f"  {i['id']} {i['status']:7} {i['kind']:12} x={i['x']} y={i['y']}  {i['note'][:60]!r}")


if __name__ == "__main__":
    main()
