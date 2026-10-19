"""Zebra crossings (Fussgaengerstreifen) measured from SWISSIMAGE at 0.25 m/px (swisstopo OGD WMS, cached in data/raw/ortho_025/o_<ix>_<iy>.jpg,
250 m boxes of 1000 px, free use with source credit). At 0.5 m/px (data/raw/ortho_wms) stripes are only a yellow tint and sunlit warm asphalt
looks the same, so the node-less zebras were found at 12 % only (research/markings_audit.md); at 0.25 m the 0.5 m stripes are 2 px.
usage: .venv/bin/python pipeline/markings_ortho25.py --fetch     (once, ~200 requests)
       .venv/bin/python pipeline/markings_ortho25.py --check     (detections per box, writes research/zebras_ortho25.json)
Public: detect(roads) -> [{x, y, d (unit vector along travel = along the stripes), half (m, across the road), area}]  local metres"""
import json, sys, time, urllib.request
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import shapely
from shapely.geometry import box, Polygon, Point

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/raw/ortho_025"
OX, OY, TILE, PX = 2681400, 1248700, 250.0, 1000
URL = ("https://wms.geo.admin.ch/?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=ch.swisstopo.swissimage&STYLES=&CRS=EPSG:2056"
       "&BBOX={a},{b},{c},{d}&WIDTH=1000&HEIGHT=1000&FORMAT=image/jpeg")
CACHE = ROOT / "data/build/zebras_ortho25.json"
STRIPE_MIN = -0.1   # T19 knobs (research/markings_audit.md): stripe periodicity score (r4 - r2); -0.2 = +40 % detections at ~10 points lower precision
RESCUE_AREA = 8.0   # smallest blob (m2) that gets the second opinion
AREA_MIN, EXTD_MIN, FILL_MAX, MYB_MAX = 9.0, 3.2, 0.93, 52.0   # paint area (m2), stripe length (m), mask fill, mean yellowness (taxis / vans are saturated)


def boxes():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import POLYGON
    pl = Polygon(POLYGON).buffer(12)
    x0, y0, x1, y1 = pl.bounds
    return [(ix, iy) for ix in range(int(np.floor(x0 / TILE)), int(np.floor(x1 / TILE)) + 1) for iy in range(int(np.floor(y0 / TILE)), int(np.floor(y1 / TILE)) + 1)
            if pl.intersects(box(ix * TILE, iy * TILE, (ix + 1) * TILE, (iy + 1) * TILE))]


def fetch():
    D.mkdir(parents=True, exist_ok=True)
    for ix, iy in boxes():
        f = D / f"o_{ix}_{iy}.jpg"
        if f.exists() and f.stat().st_size > 20000:
            continue
        u = URL.format(a=OX + ix * TILE, b=OY + iy * TILE, c=OX + (ix + 1) * TILE, d=OY + (iy + 1) * TILE)
        for k in range(6):
            try:
                f.write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "sandboxzurich-research/1.0"}), timeout=120).read())
                time.sleep(1.0)
                break
            except Exception as e:
                print("retry", ix, iy, e, flush=True); time.sleep(4 * (k + 1))
        print("fetched", ix, iy, flush=True)


def yellow(a):
    """sunlit / shaded paint yellow at 0.25 m (same colour rules as markings_ortho.yellow_mask, stripe sized smoothing)"""
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    yb = (R + G) / 2 - B; lum = (R + G + B) / 3
    ybs = ndi.gaussian_filter(yb, 0.6)
    loc = ndi.median_filter(ybs[::2, ::2], size=11)
    loc = np.kron(loc, np.ones((2, 2)))[: yb.shape[0], : yb.shape[1]]
    sun = (yb > 24) & (R > 100) & (np.abs(R - G) < 24) & (G >= R - 24) & (ybs - loc > 8)
    shade = (lum < 100) & (lum > 25) & (ybs > np.maximum(8, 0.12 * lum)) & (ybs - loc > 5) & (np.abs(R - G) < 0.25 * lum + 6)
    return sun | shade, ybs, lum


def _rescue(rej, roads, ix, iy, ctr, area, fill):
    """candidates whose stripe geometry could not be measured (ragged / merged mask) but that are yellow blobs of zebra size on the carriageway:
    crossings._scan25 gives them a second opinion with the 0.5 m mosaic stripe test (ortho_score >= STRONG, the evidence that already decides
    unmarked OSM nodes)."""
    if rej is None or area < RESCUE_AREA or not 0.35 <= fill <= 0.97:
        return
    x, y = ix * TILE + ctr[0], iy * TILE + PX * 0.25 + ctr[1]
    if roads is not None and not roads.contains(Point(x, y)):
        return
    rej.append(dict(x=float(x), y=float(y), area=float(area), fill=float(fill)))


def _blobs(mask, ybs, lum, ix, iy, roads, dbg=None, close_it=2, rej=None):
    """zebra candidates in one 250 m box. T19: the stripe direction comes from the gradient structure tensor of the stripe mask (a
    blob's covariance axes are unstable for 3 x 4 m blobs and were up to 90 degrees off: 339 real zebras failed the direction test),
    stripe pattern quality = tensor coherence + periodicity along the stripe-stack axis (needs to be strong when the geometry is odd)."""
    m = ndi.binary_opening(mask, structure=np.ones((2, 2)))
    cl = ndi.binary_closing(m, structure=np.ones((3, 3)), iterations=close_it)
    lab, n = ndi.label(cl)
    g = ndi.gaussian_filter(ybs.astype(np.float32), 0.7)   # continuous yellowness: the mask itself has merged stripes (fill 0.8)
    gy_, gx_ = np.gradient(g)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        sub = lab[sl] == i
        area = sub.sum() * 0.0625
        if area < 5 or area > 110:
            if dbg is not None and area >= 2:
                dbg.append((ix * TILE + (sl[1].start + sl[1].stop) * 0.125, iy * TILE + PX * 0.25 - (sl[0].start + sl[0].stop) * 0.125, "area %.0f" % area))
            continue
        mm = m[sl] & sub
        fill = mm.sum() / max(sub.sum(), 1)      # stripes cover ~50 % of the merged blob
        if not 0.30 <= fill <= 0.99:
            if dbg is not None:
                dbg.append((ix * TILE + (sl[1].start + sl[1].stop) * 0.125, iy * TILE + PX * 0.25 - (sl[0].start + sl[0].stop) * 0.125, "fill %.2f" % fill))
            continue
        # stripe orientation: search the angle whose across-axis profile (weighted by the continuous yellowness) is most periodic at 1.0 m
        # (0.5 m paint, 0.5 m gap = 4 px). Neither the blob covariance nor a gradient tensor survives merged / ragged stripe masks.
        sdd = ndi.binary_dilation(sub, iterations=1)
        ys_, xs_ = np.nonzero(sdd)
        pp = np.c_[xs_ + sl[1].start + .5, -(ys_ + sl[0].start + .5)] * 0.25
        ctr = pp.mean(0)
        wv = ybs[sl][sdd].astype(np.float64)
        wv = np.clip(wv - np.percentile(wv, 20), 0, None) + 1e-3
        best = (-9.0, 0.0, 0.0, 0.0)
        for th in np.arange(0.0, np.pi, np.pi / 24):
            nv = np.array([np.cos(th), np.sin(th)])
            t = (pp - ctr) @ nv
            lo = np.floor(t.min() * 4) / 4
            bins = np.arange(lo, np.ceil(t.max() * 4) / 4 + 0.25, 0.25)
            if len(bins) < 8:
                continue
            cnt, _ = np.histogram(t, bins=bins)
            hist = np.histogram(t, bins=bins, weights=wv)[0] / np.maximum(cnt, 1)
            h0 = hist - hist.mean()
            den = float((h0 ** 2).sum()) + 1e-9
            q = lambda k: float((h0[:-k] * h0[k:]).sum() / den) if len(h0) > k + 2 else 0.0
            sc = q(4) - q(2)
            if sc > best[0]:
                best = (sc, th, q(4), q(2))
        stripe, th, r4, r2 = best
        nvec = np.array([np.cos(th), np.sin(th)])
        along = np.array([-nvec[1], nvec[0]])
        rr, cc = np.nonzero(mm)
        pm = np.c_[cc + sl[1].start + .5, -(rr + sl[0].start + .5)] * 0.25
        if len(pm) < 8:
            continue
        pn, pd = (pm - ctr) @ nvec, (pm - ctr) @ along
        lo_n, hi_n = np.percentile(pn, [2, 98])
        lo_d, hi_d = np.percentile(pd, [2, 98])
        ext_n, ext_d = float(hi_n - lo_n), float(hi_d - lo_d)
        if ext_d < 1.8 or ext_d > 6.5 or ext_n < 2.0 or ext_n > 18:
            _rescue(rej, roads, ix, iy, ctr, area, fill)
            if dbg is not None:
                dbg.append((ix * TILE + ctr[0], iy * TILE + PX * 0.25 + ctr[1], "ext d %.1f n %.1f" % (ext_d, ext_n)))
            continue
        if stripe < STRIPE_MIN:
            _rescue(rej, roads, ix, iy, ctr, area, fill)
            if dbg is not None:
                dbg.append((ix * TILE + ctr[0], iy * TILE + PX * 0.25 + ctr[1], "stripe %.2f" % stripe))
            continue
        if area < AREA_MIN or ext_d < EXTD_MIN or fill > FILL_MAX:
            _rescue(rej, roads, ix, iy, ctr, area, fill)
            if dbg is not None:
                dbg.append((ix * TILE + ctr[0], iy * TILE + PX * 0.25 + ctr[1], "small/solid a %.0f d %.1f f %.2f" % (area, ext_d, fill)))
            continue
        ctr = ctr + (lo_n + hi_n) / 2 * nvec + (lo_d + hi_d) / 2 * along     # centre of the paint extent
        coh = stripe
        ml = float(lum[sl][mm].mean()) if mm.any() else 0.0
        myb = float(ybs[sl][mm].mean()) if mm.any() else 0.0
        if myb >= MYB_MAX:
            continue
        if ml < 70 and stripe < 0.5:   # tree crowns / dark vegetation pass the shade colour test; real shaded stripes keep their rhythm
            continue
        pts = pm
        x, y = ix * TILE + ctr[0], iy * TILE + (PX * 0.25) + ctr[1]
        inroad = 1.0
        if roads is not None:   # T19: the whole blob has to lie on the carriageway (roofs, tree crowns, garden paths next to a road fail here)
            if not roads.contains(Point(x, y)):
                continue
            q = pts[:: max(1, len(pts) // 60)] - ctr + ctr
            inroad = float(shapely.contains_xy(roads, ix * TILE + q[:, 0], iy * TILE + PX * 0.25 + q[:, 1]).mean())
            if inroad < 0.7:
                continue
        out.append(dict(x=float(x), y=float(y), d=[float(along[0]), float(along[1])], half=float(max(ext_n, 3.0) / 2), area=float(area), fill=float(fill),
                        r4=r4, r2=r2, coh=coh, ext_d=ext_d, inroad=inroad, lum=ml, myb=myb))
    return out


def detect(roads=None, rescue=None):
    if CACHE.exists() and roads is None:
        return json.load(open(CACHE))
    res = []
    if roads is not None:
        roads = roads.buffer(1.0)
        shapely.prepare(roads)
    for ix, iy in boxes():
        f = D / f"o_{ix}_{iy}.jpg"
        if not f.exists():
            continue
        a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
        mk, yb_, lum_ = yellow(a)
        r2 = _blobs(mk, yb_, lum_, ix, iy, roads, rej=rescue)
        # T19: zebras at junctions are merged with stop lines / neighbouring zebras by the closing (extent filter rejects the blob):
        # a lighter closing separates them again; blobs that the strong closing already found are not added twice
        r1 = _blobs(mk, yb_, lum_, ix, iy, roads, close_it=1)
        keep = [z for z in r1 if not any(abs(z["x"] - q["x"]) < 5.0 and abs(z["y"] - q["y"]) < 5.0 for q in r2)]
        res += r2 + keep
    return res


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    else:
        r = detect()
        print(len(r), "zebra-like blobs")
