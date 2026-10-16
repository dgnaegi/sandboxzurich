"""Egli-Siedlung (Eglistrasse / Hohlstrasse 315-317, Zuerich-Aussersihl), Ersatzneubau 2022/23 of the 1931-33 estate: two courtyard blocks of
6-storey white-grey plastered houses (flat roof with PV arrays, 20.2 m), tall narrow windows, projecting balconies with light slatted rails on the
courtyard side, two-storey glazed winter-garden bays with white spandrels on the Hohlstrasse side, a few orange timber shutters; one hexagonal
3-storey pavilion with a silver-grey hip roof in each courtyard. North block holds the Zuercher Lighthouse (Eglistrasse 1 / Hohlstrasse 317).
Sources: research/v3/egli_siedlung.md (Commons 'Kindergarten Egli' CC BY-SA 3.0 Tschubby, Mapillary dashcam CC BY-SA 4.0, Panoramax), SWISSIMAGE,
GWR (EGID 3020647xx, built 2022/23), 3D Blockmodell Stadt Zuerich (eave 20.2 m / 10.6 m)."""
from hz_kit import *

WALL = "#e6e3dc"

BLOCKS = {
    "nord": dict(title="Egli-Siedlung Nord (Lighthouse)", name="hz_egli_nord", court=(-395, -52), street=(0.38, 0.92),
                 keys=[("Hohlstrasse", "315"), ("Hohlstrasse", "317"), ("Eglistrasse", "1"), ("Eglistrasse", "5"), ("Eglistrasse", "7"), ("Eglistrasse", "11")],
                 pav=[("Eglistrasse", "9")]),
    "sued": dict(title="Egli-Siedlung Sued", name="hz_egli_sued", court=(-428, -102), street=None,
                 keys=[("Eglistrasse", "19"), ("Eglistrasse", "23"), ("Eglistrasse", "25"), ("Eglistrasse", "27"), ("Eglistrasse", "29"),
                       ("Eichbühlstrasse", "32"), ("Eichbühlstrasse", "34"), ("Eichbühlstrasse", "36")],
                 pav=[("Eglistrasse", "21")]),
}


def build(which):
    B = BLOCKS[which]
    polys = osm_polys(B["keys"] + B["pav"])
    ox, oy = centre_of(polys); oz = ground(ox, oy)
    rng = np.random.default_rng(71 if which == "nord" else 72)
    m = Model(B["name"])
    mw = m.mat("wall", plaster(hexc(WALL)[:3], seed=5 if which == "nord" else 6, stains=0.012))
    sign = strip([(0, 1024, "ZÜRCHER LIGHTHOUSE", "#f4f3ee", "#34373a", None)], size=30, fnt="Barlow-Bold")
    ga = D.glass_atlas_g(frame="#f1f1ee", glass="#2c3943", sky="#8ea3b3", cols=2, rows=3, seed=73, lit_p=0.3, sign=sign,
                         curtain_cols=[(238, 234, 224), (212, 200, 180), (196, 120, 80), (170, 182, 190)])
    mg = m.mat("glass", *ga, rough=0.25); mf = m.mat("flat", solid(W))
    g = 0.3; fh0 = 3.45; fh = 3.1; nf = 6
    cx, cy = B["court"][0] - ox, B["court"][1] - oy
    S = B["street"]
    sign_b = None
    for label, gl in polys:
        is_pav = any(label == " ".join(k) for k in B["pav"])
        Pl = local_ring(gl, ox, oy); mc = Pl.centroid
        m.extrude(mf, mf, Pl, -3, g, col=hx("#9b9a95"), roof=False)
        if is_pav:
            zt = pavilion_hex(m, mw, mg, mf, rng, Pl, g, 3, 3.3, W, "#c4c8cc", rise=3.8)
            continue
        def street(n): return S is not None and n[0] * S[0] + n[1] * S[1] > 0.72
        def court(n, mid):
            d = math.hypot(cx - mid[0], cy - mid[1]) + 1e-6
            return (n[0] * (cx - mid[0]) + n[1] * (cy - mid[1])) / d > 0.55
        zt = facade_building(m, mw, mg, mf, rng, Pl, g, nf, fh0, fh, wall=W, bay=3.2, ww=1.25, wh=1.75, sill=0.9, shutter_p=0.10,
                             balc_pred=lambda i, a, b, n, mid: court(n, mid),
                             oriel_pred=lambda i, a, b, n, mid: street(n),
                             ground_open=lambda i, a, b, n, mid: (dict(w=2.3, h=2.5, lo=0.15, door=True) if street(n) else None),
                             cornice="#f2f0ea", cornice_out=0.1, z_top=g + fh0 + (nf - 1) * fh + 1.0)
        # roof: parapet cap, flat gravel/green roof, PV arrays
        m.flat(mf, Pl.buffer(-0.12, join_style=2), zt - 0.75, hx("#8b8a84"))
        pv_panels(m, mf, Pl, zt - 0.75, rng)
        if label == "Eglistrasse 1":
            sign_b = (Pl, zt)
    # Zuercher Lighthouse plaque beside the entrance of Eglistrasse 1 (entrance point from GWR EGID 149457 / 302064780)
    if which == "nord" and sign_b:
        Pl, zt = sign_b; ex, ey = -409.5 - ox, -21.0 - oy
        best = min(edge_iter(list(Pl.exterior.coords)[:-1]), key=lambda e: Point(ex, ey).distance(LineString([e[1], e[2]])))
        i, a, b, L, t, n = best
        pu = max(0.5, min(L - 0.5, (ex - a[0]) * t[0] + (ey - a[1]) * t[1]))
        txtq(m, mg, a, t, n, max(0.2, pu - 2.0), min(L - 0.2, pu + 2.0), g + 3.0, 0.5, 0, 1024, off=0.1)
    # concrete street-side curb wall along Hohlstrasse is handled by places_detail
    info(m, B["name"])
    finish(m, B["name"], B["title"], ox, oy, oz, hide_union(B["title"], hide_pts(polys)))


if __name__ == "__main__":
    import sys
    for w in (sys.argv[1:] or ["nord", "sued"]):
        build(w)
