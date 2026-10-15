"""Bahnhof Zuerich Hardbruecke: two elevated platforms with long steel/glass canopies, columns, lamps, benches, glazed stair/lift towers."""
import math
from common import *
from lm import *
import detail as D
from shapely.geometry import LineString, Polygon


def build():
    ox, oy = 28.0, 112.0; oz = 0.9   # platform deck level (from rail tiles: rails top ~1.5)
    rng = np.random.default_rng(3)
    m = Model("hardbruecke")
    mg = m.mat("glass", *D.glass_atlas(frame="#dfe3e4", glass="#35505f", sky="#a9c5d3", seed=21, lit_p=0.5, curtains=False, bars=True), rough=0.3)
    mf = m.mat("flat", solid((255, 255, 255, 255)))
    lines = [[(35, 145), (2, 91)], [(20, 80), (54, 133)]]
    STEEL, CONC, ROOF = hexc("#8a9094"), hexc("#b9b6ae"), hexc("#c9d3d8")
    for pts in lines:
        pl = [(x - ox, y - oy) for x, y in pts]
        a, b = pl[0], pl[1]; L, t, n = D.frame_of(a, b); ang = math.atan2(t[1], t[0])
        for (side_off, wd) in ((0.0, 7.0),):
            c0 = (a[0], a[1])
            def Q(u, d, z): return (a[0] + t[0] * u + n[0] * d, a[1] + t[1] * u + n[1] * d, z)
            hw = wd / 2
            # platform slab: top + edge faces
            top = [Q(0, -hw, 0.0), Q(L, -hw, 0.0), Q(L, hw, 0.0), Q(0, hw, 0.0)]
            m.quad(mf, top, col=CONC, n=(0, 0, 1)); m.quad(mf, top[::-1], col=CONC, n=(0, 0, 1))
            for d_, nn in ((hw, n), (-hw, (-n[0], -n[1]))):
                f = [Q(0, d_, -1.0), Q(L, d_, -1.0), Q(L, d_, 0.0), Q(0, d_, 0.0)]
                m.quad(mf, f, col=hexc("#9a978f"), n=(nn[0], nn[1], 0)); m.quad(mf, f[::-1], col=hexc("#9a978f"), n=(nn[0], nn[1], 0))
            for d_ in (hw - 0.55, -hw + 0.55):    # yellow safety lines
                s = [Q(0, d_ - 0.12, 0.02), Q(L, d_ - 0.12, 0.02), Q(L, d_ + 0.12, 0.02), Q(0, d_ + 0.12, 0.02)]
                m.quad(mf, s, col=hexc("#e5c22e"), n=(0, 0, 1)); m.quad(mf, s[::-1], col=hexc("#e5c22e"), n=(0, 0, 1))
            # canopy: central spine of columns, wide roof slab, glass skylight strip, edge beams
            cw = 5.4; zr = 5.3
            roof = [Q(2, -cw / 2, zr), Q(L - 2, -cw / 2, zr), Q(L - 2, cw / 2, zr), Q(2, cw / 2, zr)]
            m.quad(mf, roof, col=ROOF, n=(0, 0, 1)); m.quad(mf, roof[::-1], col=ROOF, n=(0, 0, 1)); m.quad(mf, roof, col=hexc("#757b7f"), n=(0, 0, -1)); m.quad(mf, roof[::-1], col=hexc("#757b7f"), n=(0, 0, -1))
            for d_ in (-cw / 2, cw / 2):
                f = [Q(2, d_, zr - 0.35), Q(L - 2, d_, zr - 0.35), Q(L - 2, d_, zr + 0.12), Q(2, d_, zr + 0.12)]
                nn = n if d_ > 0 else (-n[0], -n[1]); m.quad(mf, f, col=hexc("#e8eaea"), n=(nn[0], nn[1], 0)); m.quad(mf, f[::-1], col=hexc("#e8eaea"), n=(nn[0], nn[1], 0))
            sky = [Q(6, -0.9, zr + 0.14), Q(L - 6, -0.9, zr + 0.14), Q(L - 6, 0.9, zr + 0.14), Q(6, 0.9, zr + 0.14)]
            m.quad(mf, sky, col=hexc("#6f93a3"), n=(0, 0, 1)); m.quad(mf, sky[::-1], col=hexc("#6f93a3"), n=(0, 0, 1))
            for u in np.arange(6.0, L - 4, 12.0):
                q = Q(u, 0, 0); m.cylinder(mf, q[0], q[1], 0.17, 0.0, zr - 0.3, n=8, col=STEEL)
                q2 = Q(u, 2.3, 0); m.box(mf, q2[0], q2[1], 1.7, 0.45, 0.0, 0.45, rot=ang, col=hexc("#7a5a3c"))        # bench
                q3 = Q(u + 6, -2.4, 0); m.box(mf, q3[0], q3[1], 0.8, 0.5, 0.0, 2.3, rot=ang, col=hexc("#d1d4d6"))      # info/ticket stele
                m.quad(mg, [Q(u + 6 - 0.35, -2.4 + 0.27, 1.0), Q(u + 6 + 0.35, -2.4 + 0.27, 1.0), Q(u + 6 + 0.35, -2.4 + 0.27, 1.9), Q(u + 6 - 0.35, -2.4 + 0.27, 1.9)][::1], D.SIGN_UV() if False else [(0, 0.25), (0.125, 0.25), (0.125, 1.0), (0, 1.0)], n=(n[0], n[1], 0))
            # hanging strip lights
            for u in np.arange(4.0, L - 3, 4.0):
                q = Q(u, 0, zr - 0.4); m.box(mf, q[0], q[1], 0.25, 3.0, zr - 0.5, zr - 0.35, rot=ang, col=hexc("#f6f2d8"))
    # glazed stair/lift towers (existing small swissBUILDINGS3D prisms), from street level up to the platform and beyond
    hide = []
    for i in ("ID_A68D0DB4", "ID_B39C7F11"):
        b = bid(i); P = orient(localize(outline(b["fp"], 0.3), ox, oy), 1.0)
        gz = ground(b["c"][0], b["c"][1]) - oz; top = b["zmax"] - oz
        fh = 3.5; nf = max(2, int(round((top - gz) / fh))); fh = (top - gz) / nf
        for a, b2 in zip(list(P.exterior.coords)[:-1], list(P.exterior.coords)[1:]):
            L, t, n = D.frame_of(a, b2)
            if L < 0.5: continue
            for f in range(nf):
                z0 = gz + f * fh
                D.bay(m, mf, mg, mf, a, t, n, 0, L, z0, z0 + fh, D.rect_pts(0.25, z0 + 0.25, L - 0.25, z0 + fh - 0.25), 0.12, int(rng.integers(0, 8)), hexc("#e3e6e7"), hexc("#b9bec0"))
        m.flat(mf, P, top, hexc("#8b9296"))
        hide += [[round(b["c"][0], 1), round(b["c"][1], 1)]]
        fp = b["fp"]; hide = hide[:-1] + [[round(g.representative_point().x, 1), round(g.representative_point().y, 1)] for g in (fp.geoms if hasattr(fp, "geoms") else [fp])]
    finish(m, "bahnhof_hardbruecke", "Bahnhof Hardbruecke", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
