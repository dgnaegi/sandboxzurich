"""Fit a global affine Lab correction auto->hand with cross-validation (by building). Writes research/autofacade/calibration.json (fit on all).
Usage: python calibrate.py [--al 0.0] [--minimgs 1]"""
import json
import sys

import numpy as np

import aggregate as A
from common import OUT, de2000


def fit(X, Y, iters=3):
    Xa = np.hstack([X, np.ones((len(X), 1))])
    w = np.ones(len(X))
    for _ in range(iters):
        Wt = np.sqrt(w)[:, None]
        # ridge towards diagonal-ish map: use lstsq on full (3x4)
        coef, *_ = np.linalg.lstsq(Xa * Wt, Y * Wt, rcond=None)
        r = np.linalg.norm(Xa @ coef - Y, axis=1)
        w = 1 / (1 + (r / 12) ** 2)
    return coef


def apply(coef, X):
    return np.hstack([X, np.ones((len(X), 1))]) @ coef


def main():
    al = float(sys.argv[sys.argv.index("--al") + 1]) if "--al" in sys.argv else 0.0
    bc = A.combine(al)
    tg = json.load(open(OUT / "targets.json"))
    notes = {}
    from common import ROOT, hex2rgb, rgb2lab
    for z in (1, 4):
        notes.update(json.load(open(ROOT / f"research/zones/zone{z}_facades.json"))["entries"])
    rows = [(a, t["zone"], t["b"]) for a, t in tg.items() if a in notes and notes[a].get("hex") and t["b"] in bc and bc[t["b"]]["ids"]]
    X = np.array([bc[b]["lab"] for _, _, b in rows])
    Y = np.array([rgb2lab(hex2rgb(notes[a]["hex"])) for a, _, _ in rows])
    z = np.array([zz for _, zz, _ in rows])
    raw = np.array([de2000(x, y) for x, y in zip(X, Y)])
    rng = np.random.default_rng(0)
    folds = rng.integers(0, 5, len(rows))
    pred = np.zeros_like(Y)
    for k in range(5):
        c = fit(X[folds != k], Y[folds != k])
        pred[folds == k] = apply(c, X[folds == k])
    cv = np.array([de2000(x, y) for x, y in zip(pred, Y)])
    # zone-transfer: fit zone 4 -> test zone 1 and vice versa
    zt = np.zeros(len(rows))
    for zz in (1, 4):
        if (z != zz).sum() > 10 and (z == zz).any():
            c = fit(X[z != zz], Y[z != zz])
            zt[z == zz] = [de2000(x, y) for x, y in zip(apply(c, X[z == zz]), Y[z == zz])]
    st = lambda d: f"n={len(d)} median={np.median(d):.1f} <10 {np.mean(d<10):.0%} <20 {np.mean(d<20):.0%}"
    base = np.array([de2000(np.median(Y, 0), y) for y in Y])
    print("raw  ", st(raw)); print("cv   ", st(cv)); print("const-median baseline", st(base))
    from scipy.stats import spearmanr
    print("spearman cv-pred vs hand  L %.2f a %.2f b %.2f" % tuple(spearmanr(pred[:, k], Y[:, k])[0] for k in range(3)))
    print("spearman raw auto vs hand L %.2f a %.2f b %.2f" % tuple(spearmanr(X[:, k], Y[:, k])[0] for k in range(3)))
    if zt.any():
        print("xzone", st(zt[zt > 0]))
    c = fit(X, Y)
    json.dump({"M": c[:3].T.tolist(), "t": c[3].tolist(), "n": len(rows)}, open(OUT / "calibration.json", "w"))
    print("coef", np.round(c, 2).tolist())


if __name__ == "__main__":
    main()
