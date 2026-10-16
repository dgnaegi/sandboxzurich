"""Validate/repair notes_raw_k4_*.tsv (12 '|' fields; 13-field lines get one empty field removed so every slot validates)."""
import re, sys
from pathlib import Path
D = Path(__file__).resolve().parent.parent.parent / "research/buildings"
VAL = {2: "PKSBGH", 5: "rahbgk", 6: "ngsubr", 7: "wdh", 9: "msfwt", 10: "gjh567nbw"}
def ok(c):
    if not re.fullmatch(r"#?[0-9a-fA-F]{6}", c[1] or "x"): return False
    for i, s in VAL.items():
        if c[i] and (len(c[i]) > 1 and i != 5 or any(ch not in s for ch in c[i])): return False
    if c[3] and not c[3].isdigit(): return False
    if c[4] and not c[4].isdigit(): return False
    if c[8] and any(ch not in "GEVRLMDAB" for ch in c[8]): return False
    return True
def main(write):
    bad = 0
    for f in sorted(D.glob("notes_raw_k4_*.tsv")):
        out = []
        for ln in f.read_text().splitlines():
            if not ln.strip() or ln.startswith("#"): out.append(ln); continue
            c = [x.strip() for x in ln.split("|")]
            if len(c) == 13:
                fix = None
                for i in range(3, 11):
                    if c[i] == "":
                        t = c[:i] + c[i + 1:]
                        if ok(t): fix = t; break
                c = fix or c
            if len(c) != 12 or not ok(c): bad += 1; print("BAD", f.name, ln[:90])
            out.append("|".join(c))
        if write: f.write_text("\n".join(out) + "\n")
    print("bad", bad)
main("--write" in sys.argv)
