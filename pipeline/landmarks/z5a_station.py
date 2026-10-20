"""Bahnhof Altstetten, Aufnahmegebaeude/Sockel (swissBUILDINGS3D ID_3A9B8AC4, one storey): raw white concrete fascia with a thick roof slab over a dark glazed shop
front; the sloped plinth stays hidden. Looks: Mapillary 2015 #1 #7 (east end with planters), 2019 #4 #6, Commons Altstetterplatz #15 (research/zones/z5/area_station.md).
Registers into overrides/landmarks_z5a.json."""
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403
from k45_volkshaus import plaster

ID = "ID_3A9B8AC4"
ZE = 5.9   # fascia top above ground (photo: about three person heights)


def build():
    _k4.setup4(); common.OVR = ROOT / "pipeline" / "overrides" / "landmarks_z5a.json"
    B = bid(ID); Pm = outline(B["fp"], 0.5); c = Pm.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    rng = np.random.default_rng(153); m = Model4("z5a_station")
    mw = m.mat("wall", plaster(hexc("#dedcd4"), seed=5, stains=0.02), rough=0.95)
    ga = D.glass_atlas_g(frame="#3b3f42", glass="#2a3941", sky="#7f95a1", cols=2, rows=1, seed=3, sign=None, cw=128, ch=96, lit_p=0.4,
                         curtain_cols=[(226, 222, 212), (150, 160, 168)])
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W4))
    P = orient(localize(Pm, ox, oy), 1.0)
    for a, b in edges_of(P, 0.3): m.wall(mw, a, b, -3.0, 0.0, (4, 4), hexl("#8d8b84"))

    def hole(u0, u1, f0, f1, fi, L):
        w = u1 - u0 - 0.5; return D.rect_pts(u0 + 0.25, f0 + 0.2, u0 + 0.25 + w, f0 + 3.8)
    facade(m, (mw, mg, mf), P, 0.0, ZE, None, fh=ZE, bayw=4.2, hole=hole, depth=0.35, wall_col=W4, reveal_col=hexl("#3b3f42"), rng=rng, wmod=(4.0, 4.0),
           cornice=(hexl("#ecEAe2"), 0.6, 1.1), wsill=0.1, deep_z=99)
    m.flat(mf, P, ZE + 0.05, hexl("#9a9a96"))
    sinfo(m, "z5a_station")
    finish(m, "z5a_station", "Bahnhof Altstetten Aufnahmegebaeude", ox, oy, oz, hide_pts([ID]))


if __name__ == "__main__":
    build()
