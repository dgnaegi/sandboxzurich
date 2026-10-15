"""Append manual R3 annotations (from viewing sheets_r3) to research/shops_v3/annotations_r3.jsonl.
Usage: shops_r3_ann.py [alt] < lines;  line: sheet|idx|facade|fascia_bg|fascia_text|style|awning(color[,striped]|-)|window|door|seating(0/1)|plants(0/1)|notes"""
import json, sys
from pathlib import Path
D = Path(__file__).resolve().parent.parent.parent / "research/shops_v3"
idx = json.load(open(D / ("sheets_r3alt" if "alt" in sys.argv else "sheets_r3") / "index.json")); n = 0
with open(D / "annotations_r3.jsonl", "a") as out:
    for l in sys.stdin:
        l = l.strip()
        if not l or l.startswith("#"): continue
        s, i, fc, bg, tx, st, aw, win, door, se, pl, notes = [x.strip() for x in l.split("|")]
        nz = lambda v: None if v in ("-", "") else v
        awn = None if aw == "-" else dict(color=aw.split(",")[0], stripes=aw.endswith(",striped"))
        e = dict(id=idx[f"sheet_{int(s):02d}"][int(i) - 1]["id"], facade_color=nz(fc), fascia=dict(bg=nz(bg), text=nz(tx), style=nz(st)),
                 awning=awn, shopwindow=nz(win), door=nz(door), seating=se == "1", plants=pl == "1", notes=notes)
        out.write(json.dumps(e, ensure_ascii=False) + "\n"); n += 1
print(n, "appended")
