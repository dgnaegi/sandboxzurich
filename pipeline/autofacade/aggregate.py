"""Combine per-image colours to per-building Lab -> auto hex per address; validate against hand hex.
Usage: python aggregate.py [--cal]  writes research/autofacade/bld_colors.json and prints stats."""
import glob
import json
import sys

import numpy as np

from common import CACHE, OUT, ROOT, de2000, hex2rgb, lab2rgb, rgb2hex, rgb2lab


def wmedian(v, w):
    o = np.argsort(v)
    c = np.cumsum(w[o])
    return v[o][np.searchsorted(c, c[-1] / 2)]


def combine(min_al=0.7):
    per = {}
    for f in glob.glob(str(CACHE / "imgres" / "*.json")):
        iid = f.split("/")[-1][:-5]
        for b, v in json.load(open(f)).items():
            if b == "_skip":
                continue
            if v.get("al", 0) >= min_al:
                per.setdefault(int(b), []).append((iid, v))
    out = {}
    for b, lst in per.items():
        lab = np.array([v["lab"] for _, v in lst])
        w = np.array([min(v["n"], 4000) ** 0.5 * v["inc"] / (1 + v["dist"] / 25) / (1 + v["spread"] / 15) for _, v in lst])
        med = np.array([wmedian(lab[:, k], w) for k in range(3)])
        for _ in range(2):
            d = np.linalg.norm(lab - med, axis=1)
            m = d < 12
            if m.sum() == 0:
                break
            med = np.array([wmedian(lab[m, k], w[m]) for k in range(3)])
        d = np.linalg.norm(lab - med, axis=1)
        m = d < 12
        out[b] = dict(lab=[float(x) for x in med], n_imgs=int(m.sum()), n_all=len(lst), agree=float(m.mean()),
                      ids=[lst[i][0] for i in np.nonzero(m)[0][:6]], spread=float(np.median(d[m])) if m.any() else 99.0)
    return out


def main():
    cal = None
    if "--cal" in sys.argv:
        cal = json.load(open(OUT / "calibration.json"))
    bc = combine(float(sys.argv[sys.argv.index('--al') + 1]) if '--al' in sys.argv else 0.7)
    json.dump({str(k): v for k, v in bc.items()}, open(OUT / "bld_colors.json", "w"))
    tg = json.load(open(OUT / "targets.json"))
    notes = {}
    for z in (1, 4):
        notes.update(json.load(open(ROOT / f"research/zones/zone{z}_facades.json"))["entries"])
    rows = []
    for a, t in tg.items():
        if a in notes and notes[a].get("hex") and t["b"] in bc:
            lab = np.array(bc[t["b"]]["lab"])
            hl = rgb2lab(hex2rgb(notes[a]["hex"]))
            rows.append((a, t["zone"], t["b"], lab, hl, bc[t["b"]]["n_imgs"]))
    print("buildings with colour", len(bc), "validation addrs", len(rows), "of", sum(1 for a in tg if a in notes))
    return bc, rows


if __name__ == "__main__":
    bc, rows = main()
    de = np.array([de2000(r[3], r[4]) for r in rows])
    for z in (1, 4):
        d = np.array([de2000(r[3], r[4]) for r in rows if r[1] == z])
        if len(d):
            print(f"zone {z}: n={len(d)} median dE00={np.median(d):.1f} <10: {np.mean(d<10):.0%} <20: {np.mean(d<20):.0%}")
    d = de
    print(f"all: n={len(d)} median={np.median(d):.1f} p25={np.percentile(d,25):.1f} p75={np.percentile(d,75):.1f} <10 {np.mean(d<10):.0%} <20 {np.mean(d<20):.0%}")
    A = np.array([r[3] for r in rows]); Hh = np.array([r[4] for r in rows])
    print("mean bias auto-hand Lab:", np.round((A - Hh).mean(0), 1), "median:", np.round(np.median(A - Hh, 0), 1))
