"""Per-cell mismatch classes for the sampled 60 m cells of markings_plaus.py (cells from research/markings_plaus/z<N>_before_cells.tsv).
Detectable classes (counted from the generator data + SWISSIMAGE evidence, not eyeballed):
  C1 bike_solid      yellow bike-lane line drawn continuous (real Radstreifen lines are broken, SSV 6.09; ortho duty 0.2-0.5 on 96 % of 105 pieces)
  C2 bike_inner_no   bike-lane side drawn on a ONE-WAY carriageway although OSM maps cycleway:<side>=no (split roads)
  C3 zebra_shifted   scan zebra drawn ~3-5 m beside the stripes the ortho shows (crossings rescue-branch shift)
  C4 zebra_unproven  OSM-tag zebra with no yellow stripe evidence within +-6 m (shade or wrong node; left as is)
usage: .venv/bin/python pipeline/markings_plaus_classify.py --zone N --tag before|after   -> research/markings_plaus/z<N>_classes_<tag>.tsv
  'before' = generator state of 2026-10-20 (continuous lines, no prune, rescue shift); 'after' = current code (zebra evidence from a fresh crossings.decide run)."""
import sys, argparse, pickle, math
from pathlib import Path
import numpy as np
from shapely.geometry import box
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))


def cells(zid):
    return [tuple(map(float, l.split("\t")[1:3])) for l in open(R / f"research/markings_plaus/z{zid}_before_cells.tsv") if l.strip()]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--zone", type=int, required=True); ap.add_argument("--tag", default="before")
    ap.add_argument("--zev", default=None, help="pickle of zebra evidence {(zone, src): [(f0, best, shift, x, y)]} for this tag (zev.py)")
    a = ap.parse_args()
    import markings_plaus_lines as PL, markings_plaus as MP, streets, markings_lines as ML, markings_bike
    S = PL.load_S()
    cs = cells(a.zone)
    rows = {c: dict(c1=0.0, c2=0.0, c3=0, c4=0) for c in cs}
    boxes = {c: box(c[0] - 30, c[1] - 30, c[0] + 30, c[1] + 30) for c in cs}
    for w in S["ways"]:
        if w["hw"] == "service" or w["zone"] in ("beg", "fuss"):
            continue
        for c, b in boxes.items():
            if not w["line"].intersects(b):
                continue
            L = w["line"].length
            for side in ("left", "right"):
                iv = w["lanes"].get(side, [])
                if not iv:
                    continue
                inner_no = w.get("oneway") and str(w["cyc"][side]).strip().lower() in ("no", "none")
                for s0, s1 in iv:
                    seg = w["line"].intersection(b)
                    ln = seg.length if not seg.is_empty else 0.0
                    share = (min(s1, L) - max(s0, 0)) / max(L, 1e-6)
                    if inner_no:
                        rows[c]["c2"] += ln * share
                    elif a.tag == "before":
                        rows[c]["c1"] += ln * share   # continuous in the before state
    if a.zev:
        zev = pickle.load(open(a.zev, "rb"))
        for (z, src), v in zev.items():
            if z != a.zone:
                continue
            for f0, best, sh, x, y in v:
                for c, b in boxes.items():
                    if b.contains(__import__("shapely").geometry.Point(x, y)):
                        if src == "scan" and f0 < 0.12 and best >= 0.18:
                            rows[c]["c3"] += 1
                        elif src == "tag" and f0 < 0.12 and best < 0.18:
                            rows[c]["c4"] += 1
    if a.tag == "after":
        for c in rows:
            rows[c]["c2"] = 0.0
    out = R / f"research/markings_plaus/z{a.zone}_classes_{a.tag}.tsv"
    ok = 0
    with open(out, "w") as f:
        f.write("x\ty\tC1_bike_solid_m\tC2_bike_inner_no_m\tC3_zebra_shifted\tC4_zebra_unproven\tmatch\n")
        for c, r in rows.items():
            m = int(r["c1"] < 5 and r["c2"] < 5 and r["c3"] == 0 and r["c4"] == 0); ok += m
            f.write(f"{c[0]:.0f}\t{c[1]:.0f}\t{r['c1']:.0f}\t{r['c2']:.0f}\t{r['c3']}\t{r['c4']}\t{m}\n")
    n = len(rows)
    print(f"zone {a.zone} {a.tag}: {ok}/{n} cells without a detectable mismatch; cells with C1 {sum(r['c1']>=5 for r in rows.values())}, C2 {sum(r['c2']>=5 for r in rows.values())}, C3 {sum(r['c3']>0 for r in rows.values())}, C4 {sum(r['c4']>0 for r in rows.values())}")


if __name__ == "__main__":
    main()
