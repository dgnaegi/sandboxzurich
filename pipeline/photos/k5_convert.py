"""Compact notes -> facades_notes TSV. Line: 'Addr | #hex m:P n:6 a:5 w:r s:g f:w e:GB r:f t:g | text'  (keys: m mat, n floors, a axes, w win, s shutter, f frame, e ext, r roof, t style)
Usage: k5_convert.py in.txt out.tsv"""
import sys
K = "m n a w s f e r t".split()
ORDER = ["hex", "m", "n", "a", "w", "s", "f", "e", "r", "t"]
# facades_notes column order: hex mat floors axes win shutter frame ext roof style
out = []
for ln in open(sys.argv[1]):
    if not ln.strip() or ln.startswith("#"): continue
    p = [x.strip() for x in ln.split("|")] + ["", ""]
    d = {"hex": ""}
    for tok in p[1].split():
        if ":" in tok: k, v = tok.split(":", 1); d[k] = v
        else: d["hex"] = tok.lstrip("#")
    out.append("|".join([p[0]] + [d.get(k, "") for k in ORDER] + [p[2]]))
open(sys.argv[2], "w").write("\n".join(out) + "\n")
print(len(out))
