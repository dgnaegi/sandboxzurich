"""Road smoothness audit (road_smooth): longitudinal slope, kinks, cross fall, tile-edge steps, carriageway<->sidewalk steps.

  .venv/bin/python pipeline/road_smooth_audit.py [--md research/road_smooth.md]
Measures the raw terrain (pre) and the road_height-smoothed grid (post) in one run. Height = H.at, as in the build.
Thresholds: slope > 8 % over 6 m, kink = slope change > 4 % between consecutive 10 m segments,
cross fall > 3 % over the carriageway width, tile-edge step > 0.1 m across a 200 m tile line, carriageway/sidewalk step > 0.2 m.
Bridges, tunnels and bridge-chain ramps are skipped (real ramps).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import shapely

sys.path.insert(0, str(Path(__file__).resolve().parent))
import road_height  # noqa: E402
import roads_audit as ra  # noqa: E402
from config import ROOT, TILE  # noqa: E402

SL, KINK, CROSS, TSTEP, SWSTEP = 0.08, 0.04, 0.03, 0.10, 0.20


def measure(H, ways, chain, H0=None):
    H0 = H0 or H  # H0 = untouched terrain: a sidewalk step only counts if the smoothing made it worse by > 0.1 m (natural hillside cross slopes are not defects)
    ev, tot = [], 0.0
    cnt = dict(slope=0, kink=0, cross=0, tile=0, sidewalk=0)
    for w in ways:
        t = w.get("tags", {})
        if t.get("bridge") in road_height.SKIP_BRIDGE or t.get("tunnel") in ("yes", "building_passage") or w["id"] in chain:
            continue
        ln = w["line"].intersection(ra.PLAY)
        if ln.geom_type != "LineString" or ln.length < 14:
            continue
        s = np.arange(0, ln.length, 2.0)
        P = shapely.line_interpolate_point(ln, s)
        xy = np.array([(p.x, p.y) for p in P])
        d = np.gradient(xy, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        nrm /= np.maximum(np.hypot(*nrm.T), 1e-9)[:, None]
        hw = w["w"] / 2
        z = H.at(xy[:, 0], xy[:, 1]).astype(float)
        tot += ln.length
        n = len(z)
        sl = np.zeros(n); kk = np.zeros(n)
        sl[3:-3] = np.abs(z[6:] - z[:-6]) / 12.0  # 6 steps x 2 m = 12 m? keep 12 m window
        a = (z[5:] - z[:-5]) / 10.0  # slope per 10 m segment
        kk[5:-5] = np.abs(a[5:] - a[:-5])[: n - 10] if n > 10 else 0
        zl = H.at(*(xy + nrm * hw).T).astype(float); zr = H.at(*(xy - nrm * hw).T).astype(float)
        cr = np.abs(zl - zr) / max(2 * hw, 1.0)
        def _sw(G, sg):
            return np.abs(G.at(*(xy + sg * nrm * (hw + 0.2)).T) - G.at(*(xy + sg * nrm * (hw + 2.0)).T)).astype(float)
        sw = np.maximum(_sw(H, 1), _sw(H, -1))
        if H0 is not H:  # post: only the part the smoothing added counts (excess over natural terrain gradient)
            ex = np.maximum(_sw(H, 1) - _sw(H0, 1), _sw(H, -1) - _sw(H0, -1))
            sw = np.where((sw > SWSTEP) & (ex > 0.1), sw, 0)
        # tile edge: consecutive samples on different sides of a 200 m line
        tx = np.floor(xy[:, 0] / TILE); ty = np.floor(xy[:, 1] / TILE)
        cross_t = np.zeros(n, bool); cross_t[1:] = (tx[1:] != tx[:-1]) | (ty[1:] != ty[:-1])
        ts = np.zeros(n); ts[1:] = np.abs(np.diff(z)) - np.abs(np.median(np.diff(z)))
        sc = {"slope": sl / SL, "kink": kk / KINK, "cross": cr / CROSS, "sidewalk": sw / SWSTEP, "tile": np.where(cross_t, np.abs(ts) / TSTEP, 0)}
        for kind, v in sc.items():
            f = v > 1
            i = 0
            while i < n:
                if f[i]:
                    j = i
                    while j + 1 < n and f[j + 1]:
                        j += 1
                    k = i + int(np.argmax(v[i:j + 1]))
                    cnt[kind] += 1
                    ev.append({"x": float(xy[k, 0]), "y": float(xy[k, 1]), "kind": kind, "score": float(v[k]),
                               "val": float(v[k] * {"slope": SL, "kink": KINK, "cross": CROSS, "sidewalk": SWSTEP, "tile": TSTEP}[kind]),
                               "name": w["name"] or w["hw"]})
                    i = j + 1
                else:
                    i += 1
    return ev, tot / 1000, cnt


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--md"); a = ap.parse_args()
    H, S, EX = ra.load(False)
    ways = [w for w in S["ways"] if w["hw"] != "service"]
    chain = S.get("chain", set())
    res = {}
    import copy
    H0 = copy.deepcopy(H)
    res["pre"] = measure(H, ways, chain)
    road_height.apply(H, S["ways"])
    import terrain_cuts
    terrain_cuts.apply(H, lock_only=True)
    res["post"] = measure(H, ways, chain, H0)
    out = {}
    for k, (ev, km, cnt) in res.items():
        tot = sum(cnt.values())
        out[k] = {"km": round(km, 1), "total": tot, "per_km": round(tot / km, 2), **cnt}
        print(k, json.dumps(out[k]))
    (ROOT / "logs").mkdir(exist_ok=True)
    top_pre = sorted(res["pre"][0], key=lambda e: -e["score"])[:30]
    top_post = sorted(res["post"][0], key=lambda e: -e["score"])[:30]
    json.dump({"summary": out, "pre": top_pre, "post": top_post}, open(ROOT / "logs" / "road_smooth_audit.json", "w"))
    if a.md:
        L = ["# Strassen glätten – Audit", "", f"Schwellen: Steigung > {SL:.0%} (12 m), Knick > {KINK:.0%} (Neigungswechsel 10 m), Querneigung > {CROSS:.0%}, Kachelkante > {TSTEP} m, Fahrbahn/Trottoir > {SWSTEP} m. Brücken/Rampen ausgenommen.", "",
             "| Phase | km | Total | /km | Steigung | Knick | Quer | Kachel | Trottoir |", "|---|---|---|---|---|---|---|---|---|"]
        for k, o in out.items():
            L.append(f"| {k} | {o['km']} | {o['total']} | {o['per_km']} | {o['slope']} | {o['kink']} | {o['cross']} | {o['tile']} | {o['sidewalk']} |")
        for lab, top in (("vorher (Rohgelände)", top_pre), ("nachher", top_post)):
            L += ["", f"## Top 30 {lab}", "", "| # | x | y | Strasse | Art | Wert | Score |", "|---|---|---|---|---|---|---|"]
            L += [f"| {i + 1} | {e['x']:.0f} | {e['y']:.0f} | {e['name'][:28]} | {e['kind']} | {e['val']:.3f} | {e['score']:.1f} |" for i, e in enumerate(top)]
        Path(a.md).write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
