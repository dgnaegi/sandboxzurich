"""Im Viadukt: stone arcade (1894) along Viaduktstrasse, one round arch per OSM unit footprint, glazed infill."""
import math
from PIL import Image, ImageDraw
from common import *
from lm import *
import osmq
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import nearest_points

PW, PH = 224, 320   # one variant: 7 m x 10 m
NV = 4


def stone_arch(seed):
    rng = np.random.default_rng(seed)
    base = Image.new("RGBA", (PW, PH), hexc("#a79e8e")); d = ImageDraw.Draw(base)
    em = Image.new("RGB", (PW, PH), (0, 0, 0)); de = ImageDraw.Draw(em)
    # ashlar courses
    y = 0; row = 0
    while y < PH:
        h = int(PH * (0.42 / 10) * (1 + rng.random() * 0.25)); x = -int(rng.random() * 30)
        while x < PW:
            w = int(PW * (0.9 / 7) * (1 + rng.random() * 0.9))
            f = 0.88 + rng.random() * 0.2
            d.rectangle([x, y, x + w, y + h], fill=shade(hexc("#a79e8e"), f), outline=shade(hexc("#a79e8e"), 0.72))
            x += w
        y += h
    sc = PW / 7.0
    cx = PW // 2; aw = int(5.2 * sc); spring = PH - int(5.8 * sc); top = spring - aw // 2
    # arch voussoirs ring + opening
    d.pieslice([cx - aw // 2 - 8, top - 8, cx + aw // 2 + 8, top + aw + 8], 180, 360, fill=hexc("#8f877a"))
    d.rectangle([cx - aw // 2 - 8, spring, cx + aw // 2 + 8, PH], fill=hexc("#8f877a"))
    G = hexc("#27343d"); F = hexc("#16181a")
    d.pieslice([cx - aw // 2, top, cx + aw // 2, top + aw], 180, 360, fill=G)
    d.rectangle([cx - aw // 2, spring, cx + aw // 2, PH], fill=G)
    # glazing: mullions, transom, door
    tr = PH - int(3.0 * sc)
    d.line([cx - aw // 2, tr, cx + aw // 2, tr], fill=F, width=4)
    for k in range(-2, 3):
        xx = cx + k * aw // 5
        d.line([xx, top + aw // 4 if abs(k) == 2 else top, xx, PH], fill=F, width=3)
    d.arc([cx - aw // 2, top, cx + aw // 2, top + aw], 180, 360, fill=F, width=4)
    d.rectangle([cx - aw // 2, spring, cx - aw // 2 + 3, PH], fill=F); d.rectangle([cx + aw // 2 - 3, spring, cx + aw // 2, PH], fill=F)
    d.rectangle([cx - 14, PH - int(2.3 * sc), cx + 14, PH], fill=hexc(["#8a2f2a", "#2f5a4a", "#e0b030", "#2a3f6a"][seed % 4]))
    # keystone
    d.rectangle([cx - 7, top - 12, cx + 7, top + 6], fill=hexc("#c1b8a7"))
    # cornice at the top
    d.rectangle([0, 0, PW, 14], fill=hexc("#b9b09f")); d.rectangle([0, 14, PW, 18], fill=hexc("#7d766a"))
    # night: lit glazing on most variants
    if seed % 4 != 3:
        de.pieslice([cx - aw // 2 + 4, top + 4, cx + aw // 2 - 4, top + aw], 180, 360, fill=(255, 205, 135))
        de.rectangle([cx - aw // 2 + 4, spring, cx + aw // 2 - 4, tr - 3], fill=(255, 200, 125))
        de.rectangle([cx - aw // 2 + 4, tr + 3, cx + aw // 2 - 4, PH - 4], fill=(230, 180, 110))
        for k in range(-2, 3):
            xx = cx + k * aw // 5; de.line([xx, top, xx, PH], fill=(0, 0, 0), width=3)
        de.line([cx - aw // 2, tr, cx + aw // 2, tr], fill=(0, 0, 0), width=4)
    return base, em


def build():
    streets = [pts for t, pts in osmq.rows if t.get("name") == "Viaduktstrasse" and "building" not in t]
    street = MultiLineString([LineString(p) for p in streets])
    units = []
    for t, pts in osmq.rows:
        if t.get("addr:street") == "Viaduktstrasse" and t.get("start_date") == "2010" and t.get("building") == "commercial":
            units.append(Polygon(pts).buffer(0))
    cx = float(np.mean([u.centroid.x for u in units])); cy = float(np.mean([u.centroid.y for u in units]))
    ox, oy = round(cx, 1), round(cy, 1); oz = ground(ox, oy)
    # atlas of NV variants side by side
    vs = [stone_arch(i) for i in range(NV)]
    base = Image.new("RGBA", (PW * NV, PH)); em = Image.new("RGB", (PW * NV, PH))
    for i, (b, e) in enumerate(vs): base.paste(b, (i * PW, 0)); em.paste(e, (i * PW, 0))
    m = Model("viadukt"); ms = m.mat("stone", base, em); mf = m.mat("flat", solid((255, 255, 255, 255)))
    H = 10.0; stone = hexc("#9c9384")
    for i, u in enumerate(units):
        r = u.minimum_rotated_rectangle; rc = list(r.exterior.coords)[:4]
        e0 = math.dist(rc[0], rc[1]); e1 = math.dist(rc[1], rc[2])
        # short edges are facade candidates; pick the one nearer to the street
        edges = [(rc[0], rc[1]), (rc[2], rc[3])] if e0 <= e1 else [(rc[1], rc[2]), (rc[3], rc[0])]
        w = min(e0, e1)
        best = min(edges, key=lambda ab: street.distance(Point((ab[0][0] + ab[1][0]) / 2, (ab[0][1] + ab[1][1]) / 2)))
        a, b = best
        c = u.centroid; mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        # orient a->b so the right-hand side is outward (away from the centroid)
        nx_, ny_ = (b[1] - a[1]), -(b[0] - a[0])
        if nx_ * (mid[0] - c.x) + ny_ * (mid[1] - c.y) < 0: a, b = b, a
        gz = ground(c.x, c.y) - oz
        P = localize(Polygon(rc), ox, oy)
        al = (a[0] - ox, a[1] - oy); bl = (b[0] - ox, b[1] - oy)
        k = i % NV
        m.wall(ms, al, bl, gz - 2.0, gz + H, mod=(4 * w, H + 2.0), u0=k / NV, v0=0.0) if False else None
        # facade quad (arch texture covers z gz..gz+H; below gz a stone skirt)
        L = math.dist(al, bl)
        m.quad(ms, [(al[0], al[1], gz), (bl[0], bl[1], gz), (bl[0], bl[1], gz + H), (al[0], al[1], gz + H)],
               [(k / NV, 0), ((k + 1) / NV, 0), ((k + 1) / NV, 1), (k / NV, 1)])
        m.quad(mf, [(al[0], al[1], gz - 2.5), (bl[0], bl[1], gz - 2.5), (bl[0], bl[1], gz), (al[0], al[1], gz)], col=stone)
        # side walls, back wall and roof in flat stone
        def skip(j, p, q):
            return (abs(p[0] - al[0]) < 0.3 and abs(p[1] - al[1]) < 0.3 and abs(q[0] - bl[0]) < 0.3 and abs(q[1] - bl[1]) < 0.3) or \
                   (abs(q[0] - al[0]) < 0.3 and abs(q[1] - al[1]) < 0.3 and abs(p[0] - bl[0]) < 0.3 and abs(p[1] - bl[1]) < 0.3)
        m.extrude(mf, mf, P, gz - 2.5, gz + H, col=stone, rcol=hexc("#6f6a62"), skip=skip)
    hide = []
    finish(m, "viadukt_arches", "Im Viadukt (Bogen)", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
