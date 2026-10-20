"""Polizei- und Justizzentrum Zuerich (PJZ, Hohlstrasse / Duttweilerstrasse, Theo Hotz Partner, 2022).
Footprint + atrium from swissBUILDINGS3D (ID_3D89E8BB, Güterstrasse 33); heights/facade from photos (research/pjz.md): light green-grey stone grid, tall
dark-metal windows in deep reveals, taller ground floor, recessed glazed entrance with canopy, dark closed prison wing in the west, glazed atrium roof.
Run: .venv/bin/python pipeline/landmarks/pjz_v2.py   (does NOT run merge.py; writes pipeline/overrides/landmarks_pjz.json)"""
import json
from k4w4_kit import *   # noqa (Model4 = up to 6 materials)

ID = "ID_3D89E8BB"   # GWR Güterstrasse 33 (2022, 10 floors); was ID_FEBC2FA3 = Neugasse 145 (wrong building, fixed 2026-10-20)
OVR = ROOT / "pipeline" / "overrides" / "landmarks_pjz.json"
TITLE = "Polizei- und Justizzentrum (PJZ)"
H_RING, H_WING, H_ATRIUM = 23.1, 21.0, 12.6   # photo-derived (swissBUILDINGS3D predates completion: 9-13 m)
H_TOWER = 31.0   # taller block mid-building (3D roof data)


def tree(m, mw, mf, x, y, h=6.5):
    m.cylinder(mw, x, y, 0.17, 0, h * 0.55, n=6, col=hexl("#5a4a3a")) if False else None
    m.cylinder(mf, x, y, 0.17, 0, h * 0.5, n=6, col=hexl("#5a4a3a"))
    m.cylinder(mf, x, y, 1.1, h * 0.35, h, n=8, col=hexl("#5f7f45"), r1=1.7, cap=mf, capcol=hexl("#5f7f45"))


def build():
    common.OVR = OVR
    b = bid(ID); fp = b["fp"]; c = fp.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    L = localize(fp.buffer(0.3).buffer(-0.3), ox, oy)
    # building parts from the 3D roof heights (swissBUILDINGS3D 2022 data): low roofs (<6 m) = prison block in the NW (dark, closed), 31 m = taller block, rest = main ring
    raw = raw_building(ID); lo, hi = [], []
    for k, p in raw["polys"]:
        if k != 2: continue
        hh = p[:, 2].mean() - oz
        try: g = Polygon(p[:, :2]).buffer(0)
        except Exception: continue
        if g.area < 40: continue
        (lo if hh < 6 else hi if hh > H_TOWER - 3 else []).append(g)
    wing = L.intersection(localize(unary_union(lo).buffer(0.6), ox, oy)) if lo else Polygon()
    tower = L.intersection(localize(unary_union(hi).buffer(0.6), ox, oy)).difference(wing) if hi else Polygon()
    east = L.difference(wing.buffer(0.05)).difference(tower.buffer(0.05))
    east = unary_union([q for q in polys_of(east) if q.area > 30])
    wing = unary_union([q for q in polys_of(wing) if q.area > 30]) if not wing.is_empty else wing
    tower = unary_union([q for q in polys_of(tower) if q.area > 30]) if not tower.is_empty else tower
    # atrium = largest inner courtyard of the whole footprint (glazed roof); other courtyards stay open
    holes = [Polygon(r) for q in polys_of(L) for r in q.interiors]
    holes = [h for h in holes if not wing.buffer(1).intersects(h)] if not wing.is_empty else holes
    atrium = max(holes, key=lambda g: g.area).buffer(-0.3) if holes else None
    ring = east
    m = Model4("pjz_v2"); rng = np.random.default_rng(22)
    mw = m.mat("wall", tex_concrete("#a9b4ab", panel=(3, 2), seed=4, joint=0.22), rough=0.9)
    dk = m.mat("dark", tex_corrugated("#34383b", n=24, horizontal=False), rough=0.85)
    sign = text_painter([(0, 1024, "POLIZEI- UND JUSTIZZENTRUM", "#e8ece8", "#2a3034", (150, 156, 150))], size=30)
    ga = D.glass_atlas_g(frame="#8e9690", glass="#2a3238", sky="#6c7c86", cols=2, rows=3, seed=7, lit_p=0.04, curtains=False, sign=sign)
    mg = m.mat("glass", *ga, rough=0.3); mf = m.mat("flat", solid(W4))
    STONE = hexl("#a4aea6"); REV = hexl("#6c726d")

    def hole(u0, u1, f0, f1, fi, Ln):
        w = min(1.6, (u1 - u0) - 0.8); uc = (u0 + u1) / 2; return D.rect_pts(uc - w / 2, f0 + 0.3, uc + w / 2, f1 - 0.4)
    def egh(u0, u1, f0, f1, fi, Ln):
        return D.rect_pts(u0 + 0.35, f0 + 0.15, u1 - 0.35, f0 + 4.0)
    def hole_w(u0, u1, f0, f1, fi, Ln):     # prison wing: few narrow slits
        uc = (u0 + u1) / 2; return D.rect_pts(uc - 0.35, f0 + 1.2, uc + 0.35, f1 - 0.8)
    for S1 in polys_of(ring):
        facade(m, (mw, mg, mf), S1, 0, H_RING, None, fh=3.85, bayw=2.45, hole=hole, depth=0.42, wall_col=W4, reveal_col=REV, rng=rng, wmod=(3.0, 3.0),
               floor_bands=(STONE, 0.12, 0.4), eg_h=5.0, eg_hole=egh, base=-3.0, cornice=(hexl("#8a908a"), 0.3, 0.6), deep_z=2.0)
        roofs(m, mf, S1, H_RING, hexl("#7b7e7a"))
    for S1 in polys_of(tower):
        facade(m, (mw, mg, mf), S1, 0, H_TOWER, None, fh=3.85, bayw=2.45, hole=hole, depth=0.42, wall_col=W4, reveal_col=REV, rng=rng, wmod=(3.0, 3.0),
               floor_bands=(STONE, 0.12, 0.4), eg_h=5.0, eg_hole=egh, base=-3.0, cornice=(hexl("#8a908a"), 0.3, 0.6), deep_z=2.0)
        roofs(m, mf, S1, H_TOWER, hexl("#7b7e7a"))
    for S1 in polys_of(wing):
        facade(m, (dk, mg, mf), S1, 0, H_WING, None, fh=3.5, bayw=6.0, hole=hole_w, depth=0.15, wall_col=W4, reveal_col=hexl("#222"), rng=rng, wmod=(4.0, 4.0),
               base=-3.0, cornice=(hexl("#2a2e30"), 0.2, 0.5), deep_z=1.0)
        roofs(m, mf, S1, H_WING, hexl("#5c5f5e"))
    # atrium: glazed saw-tooth roof over the courtyard
    if atrium is not None:
        roofs(m, mf, atrium, H_ATRIUM, hexl("#6d8794"))
        mnx, mny, mxx, mxy = atrium.bounds
        for i in range(10):
            f = (i + 0.5) / 10; m.box(mf, mnx + (mxx - mnx) * f, (mny + mxy) / 2, 0.25, mxy - mny - 3, H_ATRIUM, H_ATRIUM + 0.9, col=hexl("#555b5e"))
    # entrance: longest southern edge of the ring (Hohlstrasse side) -> recessed dark glazed foyer + canopy + lettering
    best = None
    for S1 in polys_of(ring):
        for a_, b_ in edges_of(S1, 25.0):
            Ln_, t, n = D.frame_of(a_, b_); mid = ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2)
            if n[1] < -0.3 and (best is None or Ln_ > best[0]): best = (Ln_, a_, b_, mid)
    trees = []
    if best:
        Ln_, a, b_, mid = best; Ln_, t, n = D.frame_of(a, b_); u = Ln_ / 2
        D.band(m, mf, D.P3(a, t, n, u - 9, 0)[:2], D.P3(a, t, n, u + 9, 0)[:2], 5.2, 5.6, 4.0, hexl("#6f7571"))          # canopy slab
        D.band(m, mf, D.P3(a, t, n, u - 9, 0)[:2], D.P3(a, t, n, u + 9, 0)[:2], 0.0, 0.1, 0.6, hexl("#40464a"))
        sign_quad(m, mg, a, t, n, u - 8.0, u + 8.0, 5.7, 6.9, 0, 1024, 0.0, 0.25, off=0.12)
        for k in (-8, -4, 0, 4, 8):    # canopy columns
            px, py = D.P3(a, t, n, u + k, 0, 3.5)[:2]; m.cylinder(mf, px, py, 0.22, 0, 5.2, n=8, col=hexl("#8a908a"))
        # forecourt: stone paving plate, bollards, trees, bike racks
        P = [D.P3(a, t, n, u + s, 0, d)[:2] for s, d in ((-22, 0.3), (22, 0.3), (22, 14), (-22, 14))]
        m.flat(mf, Polygon(P), 0.04, hexl("#b5b2aa"))
        for k in range(-20, 21, 5):
            px, py = D.P3(a, t, n, u + k, 0, 13.0)[:2]; m.cylinder(mf, px, py, 0.12, 0, 0.9, n=6, col=hexl("#474b4d"))
        for k in (-26, -16, 16, 26):
            px, py = D.P3(a, t, n, u + k, 0, 7.0)[:2]; trees.append((px, py))
        for k in range(3):
            px, py = D.P3(a, t, n, u + 12 + k * 1.6, 0, 3.0)[:2]; m.box(mf, px, py, 0.5, 2.0, 0, 0.9, col=hexl("#767b7d"))
    # (no forecourt trees: the street-tree layer already plants them; the cone-crown helper looked like floating buckets)
    # roof plant on the ring roof
    pc = ring.representative_point()
    for k, (dx, dy, w, d, h) in enumerate([(-30, 0, 9, 5, 2.6), (20, 8, 7, 4, 2.2), (60, -10, 10, 5, 2.8), (-70, 20, 6, 4, 2.0)]):
        x, y = pc.x + dx, pc.y + dy
        if ring.contains(Point(x, y)): m.box(mf, x, y, w, d, H_RING, H_RING + h, col=hexl("#8b8f8c"))
    hide = hide_pts([ID])
    finish(m, "pjz_v2", TITLE, ox, oy, oz, hide, reg=False)
    json.dump({"landmarks": [{"name": TITLE, "model": "/models/landmarks/pjz_v2.glb", "x": round(ox, 2), "y": round(oy, 2), "z": round(oz, 2), "heading": 0, "hide": hide}]},
              open(OVR, "w"), indent=1)
    print("origin", ox, oy, oz, "ring", round(ring.area), "wing", round(wing.area), "atrium", None if atrium is None else round(atrium.area), "entrance", best and [round(v) for v in best[3]])


if __name__ == "__main__":
    build()
