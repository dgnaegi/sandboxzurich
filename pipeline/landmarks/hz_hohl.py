"""Hohlstrasse 283-305 (Zuerich-Aussersihl), 1992/93 estate on the south side of Hohlstrasse: 5-storey greige-plastered slabs (eave 15.2 m) with narrow
tall windows, two-storey glazed winter-garden bays on the street front (283-289), balconies on the courtyard sides, steep red-tile hip roof rim
(ridge 20.4 m; the 283-289 slab keeps a flat tar-gravel core). Street trees and a low white boundary wall in front.
Sources: research/v3/hohlstrasse_283_305.md (Mapillary dashcam CC BY-SA 4.0 from Hohlstrasse, SWISSIMAGE roofs, GWR EGID 9011137-41 / 2373641-43 / 302049192
built 1992/93, Blockmodell Stadt Zuerich eave 15.2 m ridge 20.4 m)."""
from hz_kit import *

WALL = "#d6d2c8"
TILE = "#b4563b"
KEYS = [("@", -333, -75), ("Hohlstrasse", "291"), ("Hohlstrasse", "293"), ("Hohlstrasse", "295"), ("Hohlstrasse", "297"), ("Hohlstrasse", "299"),
        ("Hohlstrasse", "301"), ("Hohlstrasse", "303"), ("Hohlstrasse", "305")]
TITLE = "Hohlstrasse 283-305"


def build():
    polys = osm_polys(KEYS, near_xy=(-350, -110), r=120)
    ox, oy = centre_of(polys); oz = ground(ox, oy)
    rng = np.random.default_rng(81)
    m = Model("hz_hohl")
    mw = m.mat("wall", plaster(hexc(WALL)[:3], seed=8, stains=0.015))
    ga = D.glass_atlas_g(frame="#f3f2ee", glass="#2f3b45", sky="#8ea3b3", cols=1, rows=2, seed=82, lit_p=0.3,
                         curtain_cols=[(238, 234, 224), (212, 200, 180), (170, 182, 190), (200, 150, 120)])
    mg = m.mat("glass", *ga, rough=0.25); mf = m.mat("flat", solid(W))
    g = 0.3; fh0 = 3.3; fh = 2.9; nf = 5
    for label, gl in polys:
        Pl = local_ring(gl, ox, oy)
        front = label.startswith("@")
        m.extrude(mf, mf, Pl, -3, g, col=hx("#9b9a95"), roof=False)
        def street(n): return n[1] > 0.7                      # Hohlstrasse lies north of the row
        zt = facade_building(m, mw, mg, mf, rng, Pl, g, nf, fh0, fh, wall=W, bay=2.9, ww=0.95, wh=1.75, sill=0.9,
                             balc_pred=lambda i, a, b, n, mid: (not front) or (not street(n)),
                             oriel_pred=lambda i, a, b, n, mid: front and street(n),
                             ground_open=lambda i, a, b, n, mid: (dict(w=1.6, h=2.2, lo=0.2, door=True) if front and street(n) else None),
                             cornice="#ebe9e3", cornice_out=0.2, shutter_p=0.0)
        slope_roof(m, mf, Pl, zt, 5.0, 5.4, hx(TILE), cap=not front)
        if front:                                              # flat tar-gravel core of the long slab
            Q = Pl.buffer(-5.4, join_style=2)
            for q in ([Q] if Q.geom_type == "Polygon" else list(Q.geoms)):
                if q.area > 4: m.flat(mf, q, zt + 5.0, hx("#5f5e5a"))
    info(m, "hz_hohl")
    finish(m, "hz_hohl", TITLE, ox, oy, oz, hide_union(TITLE, hide_pts(polys)))


if __name__ == "__main__":
    build()
