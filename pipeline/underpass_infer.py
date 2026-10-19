"""T22: street sections that run UNDER a railway embankment / bridge / building but are not tagged tunnel in OSM.
swissALTI3D shows the embankment top there (e.g. Bullingerstrasse (-549,-257)..(-492,-290): street -3.0 m, DTM +4.2 m for 35 m, cliff edges of
3-6 m), so the road surface was lifted over the embankment with 40-100 % portal ramps.
Detection on merged street chains (1 m raw DTM samples): a plateau of at most MAX_LEN m that stands >= MIN_UP above the street on BOTH sides, flanked
by cliffs (>= CLIFF m rise within 3 m). The road keeps the line between the portal levels (flat floor), the terrain corridor is carved to it
(road_height.apply). Output spans: [(LineString of the plateau, z_start, z_end)]."""
import numpy as np
import shapely
from shapely.geometry import LineString

CLIFF = 1.5     # m rise within 3 m = edge of the embankment / deck
MIN_UP = 1.2    # plateau stands this far above the portal levels (both sides)
MAX_LEN = 90.0  # longer plateaus are hills, not crossings
MAX_DZ = 3.0    # portal levels of the two sides differ by less than this
SKIP = ("yes", "viaduct", "movable", "boardwalk", "cantilever", "aqueduct")


def _chains(ways):
    ends = {}
    for i, w in enumerate(ways):
        c = list(w["line"].coords)
        for k, p in ((0, c[0]), (1, c[-1])):
            ends.setdefault((round(p[0], 1), round(p[1], 1)), []).append((i, k))
    used, out = set(), []
    for i0 in range(len(ways)):
        if i0 in used:
            continue
        chain = [(i0, False)]
        used.add(i0)
        for forward in (True, False):
            cur = chain[-1] if forward else chain[0]
            while True:
                c = list(ways[cur[0]]["line"].coords)
                p = c[-1] if (cur[1] ^ (not forward)) is False else c[0]
                # end point in walking direction
                end_is_last = (not cur[1]) if forward else cur[1]
                p = c[-1] if end_is_last else c[0]
                nb = [x for x in ends.get((round(p[0], 1), round(p[1], 1)), []) if x[0] not in used]
                allw = ends.get((round(p[0], 1), round(p[1], 1)), [])
                if len(allw) != 2 or len(nb) != 1:
                    break
                j, k = nb[0]
                if ways[j]["tags"].get("name") != ways[cur[0]]["tags"].get("name"):
                    break
                used.add(j)
                if forward:
                    cur = (j, k == 1)       # entering at its last point -> reversed
                    chain.append(cur)
                else:
                    cur = (j, k == 0)       # we walk backwards: the segment is traversed so that it ends where we are
                    chain.insert(0, cur)
        out.append(chain)
    return out


def spans(H, ways):
    ws = [w for w in ways if w["hw"] != "service" and w["tags"].get("bridge") not in SKIP and w["tags"].get("tunnel") not in ("yes", "building_passage")
          and w["line"].length >= 2.0]
    res = []
    for chain in _chains(ws):
        pts = []
        for i, rev in chain:
            c = list(ws[i]["line"].coords)
            c = c[::-1] if rev else c
            pts += c if not pts else c[1:]
        ln = LineString(pts)
        if ln.length < 30:
            continue
        s = np.arange(0.0, ln.length, 1.0)
        xy = np.array([(p.x, p.y) for p in shapely.line_interpolate_point(ln, s)])
        r = H.at(xy[:, 0], xy[:, 1]).astype(float)
        n = len(r)
        st = np.zeros(n)
        st[:-3] = r[3:] - r[:-3]
        ups = np.nonzero(st > CLIFF)[0]
        downs = np.nonzero(st < -CLIFF)[0]
        taken_to = -1
        for a in ups:
            if a < taken_to or a < 8:
                continue
            a0 = a
            while a0 > 0 and st[a0 - 1] > 0.3:    # foot of the rise
                a0 -= 1
            bs = downs[(downs > a + 3) & (downs < a + MAX_LEN)]
            if not len(bs):
                continue
            b = int(bs[0])
            e = b + 3
            while e < n - 1 and st[min(e, n - 1)] < -0.3:
                e += 1
            if e >= n - 8:
                continue
            plateau = r[a + 3: b + 1]
            left = float(np.median(r[max(a0 - 10, 0): a0 + 1]))
            right = float(np.median(r[e: e + 10]))
            if plateau.min() < max(left, right) + MIN_UP or abs(left - right) > MAX_DZ:
                continue
            seg = LineString([tuple(p) for p in xy[a0: e + 1]])
            res.append({"line": seg, "z0": float(r[a0]), "z1": float(r[e]), "len": float(seg.length), "up": float(plateau.mean() - 0.5 * (left + right))})
            taken_to = e
    return res
