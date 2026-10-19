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
    return sun | shade


def _blobs(mask, ix, iy, roads):
    # stripes: 0.5 m (2 px) wide; kerb/edge lines (0.12-0.3 m) vanish in the opening; closing merges the stripes (gaps 0.5 m)
    m = ndi.binary_opening(mask, structure=np.ones((2, 2)))
    cl = ndi.binary_closing(m, structure=np.ones((3, 3)), iterations=2)
    lab, n = ndi.label(cl)
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        sub = lab[sl] == i
        area = sub.sum() * 0.0625
        if area < 6 or area > 90:
            continue
        rr, cc = np.nonzero(sub)
        pts = np.c_[cc + sl[1].start + .5, -(rr + sl[0].start + .5)] * 0.25
        ctr = pts.mean(0)
        ev, V = np.linalg.eigh(np.cov((pts - ctr).T))
        long, short = 4 * np.sqrt(ev[1]) , 4 * np.sqrt(ev[0])   # rectangle extents ~ 2*sqrt(3)*sigma; 4*sigma is a safe estimate
        if short < 2.2 or long > 16 or long / max(short, 1e-6) > 5.5:
            continue
        mm = m[sl] & sub
        fill = mm.sum() / max(sub.sum(), 1)      # stripes cover ~50 % of the merged blob
        if not 0.30 <= fill <= 0.99:
            continue
        along = V[:, 0]   # short axis of the blob = travel direction (stripes run along it)
        # stripe rhythm: mask pixels projected on the long axis repeat every 1.0 m (0.5 m paint, 0.5 m gap) = 4 px at 0.25 m
        ys_, xs_ = np.nonzero(mm)
        pp = np.c_[xs_ + sl[1].start + .5, -(ys_ + sl[0].start + .5)] * 0.25
        t = (pp - ctr) @ V[:, 1]
        hist, _ = np.histogram(t, bins=np.arange(np.floor(t.min() * 4) / 4, np.ceil(t.max() * 4) / 4 + 0.25, 0.25))
        h0 = hist - hist.mean()
        den = float((h0 ** 2).sum()) + 1e-9
        r = lambda k: float((h0[:-k] * h0[k:]).sum() / den) if len(h0) > k + 2 else 0.0
        r4, r2 = r(4), r(2)
        x, y = ix * TILE + ctr[0], iy * TILE + (PX * 0.25) + ctr[1]
        if roads is not None and not roads.contains(Point(x, y)):
            continue
        out.append(dict(x=float(x), y=float(y), d=[float(along[0]), float(along[1])], half=float(max(long, 3.0) / 2), area=float(area), fill=float(fill), r4=r4, r2=r2))
    return out


def detect(roads=None):
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
        res += _blobs(yellow(a), ix, iy, roads)
    return res


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    else:
        r = detect()
        print(len(r), "zebra-like blobs")
