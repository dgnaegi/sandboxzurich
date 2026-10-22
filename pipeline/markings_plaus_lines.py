"""Per-line evidence: every painted yellow bike-lane piece of the game (streets.bike_lane_pieces) is tested against SWISSIMAGE 0.25 m.
Thin yellow paint is only +5..10 units of (R+G)/2-B in the ortho (JPEG chroma), too weak for a per-pixel mask, so the yellowness ridge
(sigma 0.7 minus sigma 5) is averaged ALONG the piece as a profile over the lateral offset (+-2.5 m, 0.25 m steps): a real line gives a clear peak whose
height says solid (~full) or broken (~half), its position gives the lateral error of the game line.
usage: .venv/bin/python pipeline/markings_plaus_lines.py --zone N   -> research/markings_plaus/z<N>_bikelines.tsv"""
import sys, pickle, math, argparse
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Point
from scipy import ndimage as ndi
from PIL import Image
R = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import streets, streets_rules, markings_lines as ML
import markings_plaus as MP

_om, T = {}, 250.0
OFFS = np.arange(-5.0, 5.01, 0.25)


def ridge_img(ix, iy):
    if (ix, iy) not in _om:
        f = R / "data/raw/ortho_025" / f"o_{ix}_{iy}.jpg"
        if not f.exists():
            _om[(ix, iy)] = None
        else:
            a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
            yb = (a[..., 0] + a[..., 1]) / 2 - a[..., 2]
            _om[(ix, iy)] = ndi.gaussian_filter(yb, 0.7) - ndi.gaussian_filter(yb, 5)
    return _om[(ix, iy)]


def sample(xs, ys):
    """ridge values at local metres (nan outside / missing)"""
    out = np.full(len(xs), np.nan, np.float32)
    ix, iy = np.floor(xs / T).astype(int), np.floor(ys / T).astype(int)
    for k in set(zip(ix.tolist(), iy.tolist())):
        im = ridge_img(*k)
        if im is None:
            continue
        m = (ix == k[0]) & (iy == k[1])
        c = np.clip(((xs[m] - k[0] * T) * 4).astype(int), 0, im.shape[1] - 1); r = np.clip((((k[1] + 1) * T - ys[m]) * 4).astype(int), 0, im.shape[0] - 1)
        out[m] = im[r, c]
    return out


def profile(seg, step=0.5):
    """mean yellowness ridge vs lateral offset along a LineString -> (profile[len(OFFS)], n)"""
    n = max(3, int(seg.length / step))
    s = np.arange(n) * step
    p = shapely.line_interpolate_point(seg, s); q = shapely.line_interpolate_point(seg, np.minimum(s + step, seg.length))
    x, y = shapely.get_x(p), shapely.get_y(p); d = np.c_[shapely.get_x(q) - x, shapely.get_y(q) - y]
    ln = np.hypot(d[:, 0], d[:, 1]); ok = ln > 1e-3; d[ok] /= ln[ok, None]
    nx, ny = -d[:, 1], d[:, 0]
    prof = np.array([np.nanmean(sample(x[ok] + nx[ok] * o, y[ok] + ny[ok] * o)) for o in OFFS])
    return prof, int(ok.sum())


def verdict(prof):
    base = np.median(prof); pk = int(np.argmax(prof)); h = prof[pk] - base
    mad = np.median(np.abs(prof - base)) + 0.3
    return OFFS[pk], float(h), float(h / mad)


def load_S():
    S = pickle.load(open(R / "data/build/lines_S.pkl", "rb"))
    streets_rules.annotate(S); streets.junction_gaps(S)
    return S


def pieces(S, zp):
    """yield (way, side, kind, a, b, seg) for the game's bike-lane pieces inside the zone"""
    for k, w in enumerate(S["ways"]):
        if w["hw"] == "service" or w["zone"] in ("beg", "fuss") or not any(p.intersects(w["line"]) for p in zp):
            continue
        ln, L = ML.way_line(S, w), w["line"].length
        for side, solid, broken in streets.bike_lane_pieces(w):
            off = ln.offset_curve((1 if side == "left" else -1) * (w["w"] / 2 - 1.5))
            if off.is_empty or off.geom_type != "LineString":
                continue
            for kind, ivs in (("solid", solid), ("broken", broken)):
                for a, b in ivs:
                    if b - a >= 8:
                        yield w, side, kind, a, b, streets._sub(off, a, b, L)


def run(zid):
    S = load_S(); zp = MP.zone_polys(zid); rows = []
    for w, side, kind, a, b, seg in pieces(S, zp):
        prof, n = profile(seg)
        o, h, z = verdict(prof)
        mid = seg.interpolate(0.5, normalized=True)
        rows.append((w["name"] or "", w["hw"], side, kind, round(a), round(b), round(seg.length), round(o, 2), round(h, 1), round(z, 1), round(mid.x), round(mid.y)))
    out = R / f"research/markings_plaus/z{zid}_bikelines.tsv"
    out.write_text("name\thw\tside\tkind\ts0\ts1\tlen\tpeak_off\tpeak_h\tpeak_z\tx\ty\n" + "\n".join("\t".join(map(str, r)) for r in rows) + "\n")
    h = np.array([r[8] for r in rows]); L = np.array([r[6] for r in rows]); o = np.array([r[7] for r in rows])
    print(len(rows), "pieces", int(L.sum()), "m; peak height quantiles", np.percentile(h, [10, 25, 50, 75, 90]).round(1))
    print("lateral peak offset histogram (m) for h>3:", np.histogram(o[h > 3], bins=np.arange(-2.75, 2.8, 0.5)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--zone", type=int, required=True); run(ap.parse_args().zone)


def along(seg, off, step=0.25):
    """yellowness ridge along the piece at lateral offset `off` (mean of off-0.25, off, off+0.25 m) -> signal[s]"""
    n = max(3, int(seg.length / step)); s = np.arange(n) * step
    p = shapely.line_interpolate_point(seg, s); q = shapely.line_interpolate_point(seg, np.minimum(s + 0.5, seg.length))
    x, y = shapely.get_x(p), shapely.get_y(p); d = np.c_[shapely.get_x(q) - x, shapely.get_y(q) - y]
    ln = np.hypot(d[:, 0], d[:, 1]) + 1e-9; d /= ln[:, None]
    f = np.mean([sample(x - d[:, 1] * (off + o), y + d[:, 0] * (off + o)) for o in (-0.25, 0.0, 0.25)], axis=0)
    return f


def dashed_score(f):
    """0 = constant (solid), larger = periodic on/off. Fraction of variance explained by the best period 2..8 m (on/off template)."""
    f = f[np.isfinite(f)]
    if len(f) < 40:
        return float("nan"), 0.0
    g = ndi.gaussian_filter1d(f - np.median(f), 1.0)
    base = np.var(g) + 1e-6
    best, bp = 0.0, 0.0
    for P in np.arange(2.0, 8.01, 0.5):
        k = int(round(P / 0.25))
        ph = np.arange(len(g)) % k
        m = np.array([g[ph == i].mean() for i in range(k)])
        best, bp = (np.var(m[ph]) / base, P) if np.var(m[ph]) / base > best else (best, bp)
    return float(best), float(bp)
