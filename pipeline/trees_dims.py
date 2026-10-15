"""Per-tree dimensions from real data: Baumkataster (species, crown diameter, planting year) + canopy height from
swissSURFACE3D minus swissALTI3D (nDSM, pipeline/trees/ndsm.py). Returns height, crown diameter, crown-base fraction.
Falls back to a species-aware formula when the nDSM has no usable pixels (building-adjacent / OSM-only trees)."""
import json
from functools import lru_cache
import numpy as np
from config import ROOT

E0, N0 = 2681400.0, 1248700.0
NDSM = ROOT / "data/build/ndsm"
# class ids shared with web/src/world/trees.ts CLASSES
BROAD, CHERRY, WHITE, PLANE, LINDEN, MAPLE, CHESTNUT, BIRCH, CONIFER, COLUMNAR, ROBINIA, ASH, OAK, BEECH, PINE = range(15)
GENUS = {"Prunus": CHERRY, "Malus": WHITE, "Pyrus": WHITE, "Crataegus": WHITE, "Sorbus": WHITE, "Platanus": PLANE, "Tilia": LINDEN,
         "Acer": MAPLE, "Aesculus": CHESTNUT, "Betula": BIRCH, "Salix": BIRCH, "Pinus": PINE, "Picea": CONIFER, "Abies": CONIFER,
         "Taxus": CONIFER, "Thuja": CONIFER, "Larix": CONIFER, "Cedrus": CONIFER, "Metasequoia": CONIFER, "Cupressus": CONIFER,
         "Juniperus": CONIFER, "Sequoiadendron": CONIFER, "Carpinus": COLUMNAR, "Populus": COLUMNAR, "Ginkgo": COLUMNAR,
         "Quercus": OAK, "Fraxinus": ASH, "Ulmus": BROAD, "Robinia": ROBINIA, "Gleditsia": ROBINIA, "Sophora": ROBINIA,
         "Fagus": BEECH, "Liquidambar": MAPLE, "Magnolia": CHERRY, "Cercis": CHERRY}
# (typical max height m, crown base fraction of height)
SPEC = {BROAD: (22, .30), CHERRY: (11, .28), WHITE: (8, .25), PLANE: (28, .32), LINDEN: (24, .28), MAPLE: (21, .30),
        CHESTNUT: (22, .24), BIRCH: (20, .36), CONIFER: (22, .06), COLUMNAR: (16, .20), ROBINIA: (20, .36), ASH: (26, .36),
        OAK: (24, .30), BEECH: (26, .28), PINE: (20, .45)}
_cache = {}


class Neighbours:
    """Grid-hashed tree positions: distance from points to the nearest tree other than the one at `self_xy`."""
    def __init__(self, pts, cell=20.0):
        self.cell, self.g = cell, {}
        for x, y in pts:
            self.g.setdefault((int(x // cell), int(y // cell)), []).append((x, y))

    def near(self, x, y, r):
        c, out = self.cell, []
        for i in range(int((x - r) // c), int((x + r) // c) + 1):
            for j in range(int((y - r) // c), int((y + r) // c) + 1):
                out += [p for p in self.g.get((i, j), ()) if abs(p[0] - x) > .05 or abs(p[1] - y) > .05]
        return np.array(out, float).reshape(-1, 2)


def _tile(e, n):
    k = (e, n)
    if k not in _cache:
        f = NDSM / f"{e}-{n}.npy"
        _cache[k] = np.load(f).astype(np.float32) if f.exists() else None
    return _cache[k]


def _window(x, y, r):
    """nDSM pixels (1 m) within square +-r of local (x, y): (xs, ys, h) arrays, NaN-free."""
    E, N = x + E0, y + N0
    xs, ys, hs = [], [], []
    for te in range(int((E - r) // 1000), int((E + r) // 1000) + 1):
        for tn in range(int((N - r) // 1000), int((N + r) // 1000) + 1):
            a = _tile(te, tn)
            if a is None:
                continue
            c0, c1 = int(max(0, E - r - te * 1000)), int(min(1000, E + r - te * 1000 + 1))
            r0, r1 = int(max(0, (tn + 1) * 1000 - (N + r))), int(min(1000, (tn + 1) * 1000 - (N - r) + 1))
            if c1 <= c0 or r1 <= r0:
                continue
            sub = a[r0:r1, c0:c1]
            rr, cc = np.nonzero(np.isfinite(sub))
            xs.append(te * 1000 + c0 + cc + .5 - E0); ys.append((tn + 1) * 1000 - r0 - rr - .5 - N0); hs.append(sub[rr, cc])
    if not xs:
        return np.zeros(0), np.zeros(0), np.zeros(0)
    return np.concatenate(xs), np.concatenate(ys), np.concatenate(hs)


def class_of(genus, species):
    sp = (species or "").lower()
    if genus == "Acer" and sp.startswith(("palmatum", "japonicum")):
        return CHERRY  # small ornamental maples
    return GENUS.get(genus, BROAD)


def formula(cls, cd, year, cat):
    hmax = SPEC[cls][0]
    age = max(0, 2026 - year) if year else 40
    return float(np.clip(cd * (1.55 if cls in (CONIFER, COLUMNAR, PINE) else 1.15) + 2.5, 3, hmax * (0.5 + min(age, 60) / 120)))


def dims(x, y, cls, cd, year, cat, others: Neighbours | None = None):
    """-> (height m, crown diameter m, crown-base fraction, source) for a tree at local (x, y)."""
    cd = float(np.clip(cd or 6, 2, 24))
    rw = max(2.0, cd * .75)
    px, py, ph = _window(x, y, rw + 1)
    src = "formula"
    h = formula(cls, cd, year, cat)
    dcrown = cd
    if len(ph):
        d = np.hypot(px - x, py - y)
        core = ph[d <= max(1.6, cd * .3)]
        if len(core) >= 4 and np.nanmax(core) > 2.0:
            h_ndsm = float(np.percentile(core, 92))
            hmax = SPEC[cls][0] * 1.6
            if h_ndsm > 2.5:
                h = min(h_ndsm, hmax)
                src = "ndsm"
                # crown extent: pixels above 45 % of height nearer to this tree than to any other
                m = (ph > .45 * h) & (d <= cd * .85 + 1)
                nb = others.near(x, y, cd * 2 + 4) if others is not None else np.zeros((0, 2))
                if len(nb) and m.sum():
                    pts = np.c_[px[m], py[m]]
                    dd = np.sqrt(((pts[:, None, :] - nb[None, :, :]) ** 2).sum(-1)).min(1)
                    area = float((d[m] <= dd + .01).sum())
                else:
                    area = float(m.sum())
                if area > 3:
                    de = 2 * np.sqrt(area / np.pi)
                    dcrown = float(np.clip(.5 * cd + .5 * de, .7 * cd, 1.4 * cd))
    ar = h / max(dcrown, .1)
    if ar < .45 or ar > 5:  # implausible: trust the crown, estimate the height
        h = float(np.clip(.5 * h + .5 * formula(cls, dcrown, year, cat), 3, SPEC[cls][0] * 1.6)); src += "~"
    base = SPEC[cls][1]
    if cat == "Strassenbaum" and cls != CONIFER:
        base = max(base, min(3.4 / h, .55))
    elif cls != CONIFER:
        base = base * (.9 if h > 12 else 1)
    return round(h, 1), round(dcrown, 1), round(float(np.clip(base, .03, .6)), 2), src


@lru_cache(maxsize=1)
def catalog():
    """{(x, y) rounded to 1 cm in local metres: (species, planting year)} from the Baumkataster (same transform as citydata)."""
    import sources
    d = json.load(open(ROOT / "data/raw/stadtzh/geo_baumkataster__baumkataster_baumstandorte.geojson"))["features"]
    out = {}
    for f in d:
        if not f.get("geometry"):
            continue
        c = f["geometry"]["coordinates"]
        if abs(c[0]) > 1000:
            x, y = c[0] - sources.geo.ORIGIN_E, c[1] - sources.geo.ORIGIN_N
        else:
            x, y = sources.geo.to_local(c[0], c[1])
        p = f["properties"]
        out[(round(float(x), 2), round(float(y), 2))] = (p.get("baumartlat") or "", p.get("pflanzjahr") or 0)
    return out


_nb = {}


def neighbours(C):
    if id(C) not in _nb:
        _nb[id(C)] = Neighbours([(t[0], t[1]) for t in C.get("trees", [])])
    return _nb[id(C)]


def tree_row(C, x, y, z, genus, crown, cat, heading, guard):
    """Row for the renderer: [x, y, z, cls, crown, height, base fraction, flags, heading].
    flags: 1 street tree (tree pit grate), 2 plus guard hoops (next to parking / carriageway)."""
    species, year = catalog().get((round(x, 2), round(y, 2)), ("", 0))
    cls = class_of(genus, species)
    h, dc, base, _ = dims(x, y, cls, crown, year, cat, neighbours(C))
    flags = (1 + (1 if guard else 0)) if cat == "Strassenbaum" else 0
    return [x, y, z, cls, dc, h, base, flags, round(heading, 2)]
