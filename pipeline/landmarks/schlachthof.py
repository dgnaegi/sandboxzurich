"""Staedtischer Schlachthof Zuerich (1909, Herdernstrasse): yellow brick halls with red brick arches, segmental barrel vault (zinc) with two
arched portal gables (clock, glazed lunette, three gates), 48 m brick chimney, Restaurant Schlachthof (hip roof, green shutters).
Volumes come straight from swissBUILDINGS3D (walls/roofs per polygon, UV-textured); vault and portals are rebuilt from photos
(research/schlachthof.md). Registers pipeline/overrides/landmarks_schlachthof.json (hide ids -> footprints stay colliders)."""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
import glob, json, math, pickle, subprocess
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.strtree import STRtree
from k39w3_kit import prep, W4, hexl, Model, taper, ROOT
from common import ground
import detail as D
import schlachthof_tex as T
from schlachthof_rest import restaurant_extras
from lm import Mat

OVR = ROOT / "pipeline" / "overrides" / "landmarks_schlachthof.json"
OUTDIR = ROOT / "web" / "public" / "models" / "landmarks"; RAWDIR = ROOT / "data" / "build" / "landmarks"
HALL_IDS = ["ID_B529B079", "ID_73904D69"]; REST_ID = "ID_E1E2306E"; GATE_ID = "ID_9B116DAC"; HOUSES = [("ID_E1E2306E", True), ("ID_9B116DAC", False)]; CHIM_ID = "ID_45AE7D98"
A_G, B_G = np.array((-913.0, 50.0)), np.array((-805.0, -25.0))      # vault axis (global local-metres), measured from the roof polygons
S0, S1, OC, HALF, SPRING, RIDGE = 8.2, 134.0, -5.3, 12.1, 10.5, 14.6   # vault s range along the axis, centre offset, half span, abs heights
STONE, GREY, RED = hexl("#b4aea0"), hexl("#8a8883"), hexl("#a8472f")


class M8(Model):
    max_mats = 10


def load(prefix):
    out = []
    for f in sorted(glob.glob(str(ROOT / "data/build/bld/*.pkl"))):
        for b in pickle.load(open(f, "rb")):
            if b["id"].startswith(prefix): out += [(k, np.array(p, float)) for k, p in b["polys"]]
    return out


def oq(m, mat, pts, nrm, uv, col=W4):
    D._oriented(m, mat, [tuple(p) for p in pts], nrm, uv, col)


class Ctx2: pass


def build():
    c = prep(HALL_IDS, 0.6); ox, oy, oz = c.ox, c.oy, c.oz
    loc = lambda p: p - np.array([ox, oy, oz])
    gl = lambda x, y: ground(x + ox, y + oy) - oz
    A = A_G - [ox, oy]; Bv = B_G - [ox, oy]; t = (Bv - A) / np.hypot(*(Bv - A)); nl = np.array([-t[1], t[0]])
    sp_l, rg_l = SPRING - oz, RIDGE - oz
    m = M8("schlachthof"); T0 = T.decals()
    mb = m.mat("brick", T.brick_wall(), rough=0.95)
    mp = m.mat("plaster", T.brick_wall(red=False, seed=5), rough=0.95)
    mf = m.mat("flat", None, rough=0.9)
    mz = m.mat("zinc", T.zinc(), rough=0.55)
    mt = m.mat("tiles", T.tiles(), rough=0.9)
    dec = T0[0].resize((512, 512)); mdc = m.mat("decal", dec, T0[1].resize((512, 512)), rough=0.8); mdc.alpha_mask = True
    # portals: two textures (NW with clock, SE plainer) -> one material each
    ends = [(S0 - 0.0, -1, 1), (S1, +1, 0)]      # photos 7-10: the clock portal is the SE one (chimney far left behind it)
    pm = []
    for s, sg, var in ends:
        p = A + t * s + nl * OC; zg = gl(p[0], p[1]) - sp_l
        tex, em = T.portal(zg, var); pm.append((m.mat(f"portal{var}", tex, em, rough=0.9), zg))
    # ---- data polygons -------------------------------------------------
    polys = []
    for pre in HALL_IDS: polys += load(pre)
    roofs = []; walls = []
    def in_strip(xy, pad=0.5):
        s = (xy - A) @ t; o = (xy - A) @ nl
        return (S0 - 6 < s < S1 + 6) & (OC - HALF - pad < o) & (o < OC + HALF + pad)
    for k, p in polys:
        q = loc(p)
        if k == 2:
            if p[:, 2].mean() > 9.0 and in_strip(q[:, :2].mean(0), 1.0): continue          # replaced by the modelled vault
            roofs.append(q)
        elif k == 1:
            if p[:, 2].max() > SPRING + 0.4 and in_strip(q[:, :2].mean(0), 1.5): continue    # old vault gables
            walls.append(q)
    # roofs: flat gravel/green roofs (vertex colour), data polygons as they are
    for q in roofs:
        zz = q[:, 2].mean() + oz
        col = hexl("#7b7a70") if zz < 7.2 else hexl("#8d9086")
        n3 = np.cross(q[1] - q[0], q[2] - q[0]); n3 = n3 / (np.linalg.norm(n3) + 1e-9)
        if n3[2] < 0: n3 = -n3
        pts = [tuple(x) for x in q]
        if len(pts) == 4: oq(m, mf, pts, n3, [(0, 0), (1, 0), (1, 1), (0, 1)], col)
        elif len(pts) == 3: oq(m, mf, pts, n3, [(0, 0), (1, 0), (0, 1)], col)
    # walls: brick, windows, gates, cornice, plinth
    rng = np.random.default_rng(7); nwin = 0; nwall = 0
    for q in walls:
        z0 = float(q[:, 2].min()); z1 = float(q[:, 2].max()); xy = q[:, :2]
        if len(q) < 4 or z1 - z0 < 0.4: continue
        n3 = np.cross(q[1] - q[0], q[2] - q[0]); nh = n3[:2]; ln = np.hypot(*nh)
        if ln < 1e-6: continue
        nh = nh / ln; tt = np.array([-nh[1], nh[0]])                       # right of a->b is outward
        pr = xy @ tt; ia, ib = int(np.argmin(pr)), int(np.argmax(pr)); a, b = xy[ia], xy[ib]; w = float(pr[ib] - pr[ia])
        if w < 0.3: continue
        g = gl(*(a + b) / 2)
        if z0 < g + 3: z0 = min(z0, g - 1.0)
        h = z1 - z0
        u0 = float(a @ tt) / 4.0; u1 = u0 + w / 4.0
        oq(m, mb, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], (nh[0], nh[1], 0), [(u0, z0 / 4), (u1, z0 / 4), (u1, z1 / 4), (u0, z1 / 4)]); nwall += 1
        if w < 3.0 or h < 3.5: continue
        ground_wall = z0 <= g + 1.0
        if h >= 6: D.band(m, mf, tuple(a), tuple(b), z1 - 0.5, z1 + 0.15, 0.25, STONE)
        if ground_wall and h >= 6: D.band(m, mf, tuple(a), tuple(b), z0 + 0.5 if z0 < g else z0, z0 + 1.2 if z0 < g else z0 + 1.1, 0.07, GREY)
        nb = max(1, int(round((w - 1.0) / 4.2))); bw = (w - 1.0) / nb
        def place(name, cu, zb_, wd, ht, off=0.04):
            P = lambda u, z: (a[0] + tt[0] * u + nh[0] * off, a[1] + tt[1] * u + nh[1] * off, z)
            oq(m, mdc, [P(cu - wd / 2, zb_), P(cu + wd / 2, zb_), P(cu + wd / 2, zb_ + ht), P(cu - wd / 2, zb_ + ht)], (nh[0], nh[1], 0), T.uvr(name))
        for kk in range(nb):
            cu = 0.5 + (kk + 0.5) * bw
            if ground_wall and h >= 11 and kk % 3 == 1 and w >= 7: place("gate", cu, g + 0.15 if z0 < g else z0, 3.0, 4.5)
            if h >= 9: wh = 4.6; zb_ = z1 - 1.5 - wh
            else: wh = h - 2.4; zb_ = z0 + 1.2
            if wh >= 1.8 and not (ground_wall and h >= 11 and kk % 3 == 1 and zb_ < g + 5.0 and False): place("win_arch", cu, zb_, wh / 2, wh); nwin += 1
    # ---- vault ---------------------------------------------------------
    Rv = (HALF ** 2 + (RIDGE - SPRING) ** 2) / (2 * (RIDGE - SPRING)); zc = rg_l - Rv; th = math.asin(HALF / Rv); NS = 10
    La, Lb = S0, S1
    for i in range(NS):
        a0 = -th + 2 * th * i / NS; a1 = -th + 2 * th * (i + 1) / NS
        def P3(s, ang): o = OC + Rv * math.sin(ang); z = zc + Rv * math.cos(ang); p = A + t * s + nl * o; return (p[0], p[1], z)
        nrm = (nl[0] * math.sin((a0 + a1) / 2), nl[1] * math.sin((a0 + a1) / 2), math.cos((a0 + a1) / 2))
        arc0 = Rv * (a0 + th); arc1 = Rv * (a1 + th)
        oq(m, mz, [P3(La, a0), P3(Lb, a0), P3(Lb, a1), P3(La, a1)], nrm, [(arc0 / 0.6, La / 8), (arc0 / 0.6, Lb / 8), (arc1 / 0.6, Lb / 8), (arc1 / 0.6, La / 8)])
    # eave gutter lines
    for sg in (-1, 1):
        p0 = A + t * La + nl * (OC + sg * HALF); p1 = A + t * Lb + nl * (OC + sg * HALF)
        D.band(m, mf, tuple(p0), tuple(p1), sp_l - 0.6, sp_l + 0.1, 0.3, STONE) if sg < 0 else D.band(m, mf, tuple(p1), tuple(p0), sp_l - 0.6, sp_l + 0.1, 0.3, STONE)
    # ---- portals -------------------------------------------------------
    for (s, sg, var), (pmat, zg) in zip(ends, pm):
        p = A + t * s + nl * OC; out = t * sg; tf = np.array([-out[1], out[0]]); org = tuple(p + out * 0.2)
        zb = zg + sp_l - 1.0 + 0.0
        arc = [(HALF * math.cos(math.pi * i / 24), sp_l + HALF * math.sin(math.pi * i / 24)) for i in range(25)]
        pts = [(-15, zb), (15, zb), (15, sp_l + 3.0), (HALF, sp_l + 3.0)] + arc + [(-HALF, sp_l + 3.0), (-15, sp_l + 3.0)]
        poly = Polygon(pts).buffer(0)
        D.poly_wall(m, pmat, poly, org, tuple(tf), (tf[1], -tf[0]), 0.0, W4, lambda u, z, sl=sp_l: ((u + 15) / 30.0, (z - sl + 15) / 28.0))
        # pier caps (pyramids) and cornice along the arch
        for sd in (-1, 1):
            cu = sd * 13.55; q0 = np.array(org[:2]) + tf * cu; n2 = np.array([tf[1], -tf[0]])
            ring = Polygon([q0 + tf * (-1.5) - n2 * 0.9, q0 + tf * 1.5 - n2 * 0.9, q0 + tf * 1.5 + n2 * 0.5, q0 + tf * (-1.5) + n2 * 0.5])
            m.extrude(mb, mf, ring, zb, sp_l + 3.0, mod=(4, 4), col=W4, rcol=STONE, roof=False)
            taper(m, mf, ring.buffer(0.15, join_style=2), sp_l + 3.0, sp_l + 6.0, 0.05, hexl("#6d4a3b"), cap=False)
        # arch moulding: a thin stone half-ring proud of the facade
        ring_pts = [(org[0] + tf[0] * HALF * math.cos(math.pi * i / 24) + out[0] * 0.35, org[1] + tf[1] * HALF * math.cos(math.pi * i / 24) + out[1] * 0.35, sp_l + HALF * math.sin(math.pi * i / 24)) for i in range(25)]
        for i in range(24):
            q1, q2 = ring_pts[i], ring_pts[i + 1]
            top = [(q1[0], q1[1], q1[2]), (q2[0], q2[1], q2[2]), (q2[0] - out[0] * 0.35, q2[1] - out[1] * 0.35, q2[2]), (q1[0] - out[0] * 0.35, q1[1] - out[1] * 0.35, q1[2])]
            oq(m, mf, top, (0, 0, 1), [(0, 0), (1, 0), (1, 1), (0, 1)], STONE)
    # ---- chimney -------------------------------------------------------
    cx, cy = -926.9 - ox, 21.9 - oy; gz = gl(cx, cy); ztop = 44.6 - oz
    mch = m.mat("chimney", T.brick_wall(color=(132, 52, 38), red=False, seed=9), rough=0.95)       # slender tapered brick stack (photo 3/9)
    R0, R1 = 1.55, 0.9; nseg = 8
    rad = lambda z: R0 + (R1 - R0) * (z - gz) / (ztop - 2.2 - gz)
    for i in range(nseg):
        za = gz - 1 + (ztop - 2.2 - gz + 1) * i / nseg; zb_ = gz - 1 + (ztop - 2.2 - gz + 1) * (i + 1) / nseg
        m.cylinder(mch, cx, cy, rad(za), za, zb_, n=16, mod=(3.0, 3.0), col=W4, r1=rad(zb_))
        if i % 3 == 2: m.cylinder(mf, cx, cy, rad(zb_) + 0.1, zb_ - 0.2, zb_ + 0.1, n=16, col=hexl("#c9c0ae"))     # light band
    zh = ztop - 2.2; rh = R1
    m.cylinder(mch, cx, cy, rh, zh, zh + 1.0, n=16, mod=(3.0, 3.0), col=W4)
    m.cylinder(mf, cx, cy, rh + 0.1, zh + 1.0, zh + 1.3, n=16, col=hexl("#c9c0ae"), r1=rh + 0.45)             # head ring (flared cornice)
    m.cylinder(mch, cx, cy, rh + 0.45, zh + 1.3, zh + 2.1, n=16, mod=(3.0, 3.0), col=W4, r1=rh + 0.3)
    m.cylinder(mf, cx, cy, rh + 0.35, zh + 2.1, zh + 2.35, n=16, col=hexl("#a8a396"), cap=mf, capcol=hexl("#2e2e2e"))
    # ---- restaurant ----------------------------------------------------
    for prefix, signed in HOUSES:
        rp = load(prefix); rw = []; RW_info = []
        for k, p in rp:
            q = loc(p)
            if k == 2:
                n3 = np.cross(q[1] - q[0], q[2] - q[0]); n3 = n3 / (np.linalg.norm(n3) + 1e-9)
                if n3[2] < 0: n3 = -n3
                if len(q) in (3, 4): oq(m, mt, [tuple(x) for x in q], n3, [(x[0] * 0.5, x[1] * 0.5) for x in q], W4)
            elif k == 1: rw.append(q)
        eave = float(np.median([q[:, 2].max() for q in rw if len(q) == 4 and q[:, 2].max() - q[:, 2].min() > 3] or [rw[0][:, 2].max()]))
        def front_score(q):
            n3 = np.cross(q[1] - q[0], q[2] - q[0]); nh = n3[:2] / (np.hypot(*n3[:2]) + 1e-9); sc = float(nh @ np.array([0.6, -0.8]))
            return (np.hypot(*(q[:, :2].max(0) - q[:, :2].min(0))) if (q[:, 2].max() - q[:, 2].min()) > 3 and sc > 0.3 else 0.0)
        longest = max(rw, key=front_score)
        for q in rw:
            z0 = float(q[:, 2].min()); z1 = float(q[:, 2].max()); xy = q[:, :2]
            if len(q) < 4 or z1 - z0 < 0.4: continue
            n3 = np.cross(q[1] - q[0], q[2] - q[0]); nh = n3[:2]; ln = np.hypot(*nh)
            if ln < 1e-6: continue
            nh = nh / ln; tt = np.array([-nh[1], nh[0]]); pr = xy @ tt; ia, ib = int(np.argmin(pr)), int(np.argmax(pr)); a, b = xy[ia], xy[ib]; w = float(pr[ib] - pr[ia])
            if w < 0.3: continue
            g = gl(*(a + b) / 2); z0 = min(z0, g - 0.8); u0 = float(a @ tt) / 4
            zz0 = float(q[:, 2].min()); qq = q.copy(); qq[qq[:, 2] <= zz0 + 0.01, 2] = z0     # true quad (gable ends/hips are not rectangles)
            oq(m, mp, [tuple(v) for v in qq], (nh[0], nh[1], 0), [(float(v[:2] @ tt) / 4.0, v[2] / 4.0) for v in qq])
            if w < 3 or z1 - g < 5: continue
            ze = min(z1, eave); D.band(m, mf, tuple(a), tuple(b), ze - 0.35, ze + 0.1, 0.3, hexl("#cfc7b6")); D.band(m, mf, tuple(a), tuple(b), g, g + 0.7, 0.05, GREY)
            nf = max(1, int((ze - g) // 3.3)); nb = max(1, int((w - 0.8) // 3.0)); bw = (w - 0.8) / nb
            P = lambda u, z, off=0.04: (a[0] + tt[0] * u + nh[0] * off, a[1] + tt[1] * u + nh[1] * off, z)
            for f in range(nf):
                for kk in range(nb):
                    cu = 0.4 + (kk + 0.5) * bw
                    if f == 0:
                        if q is longest and kk == nb // 2: wd, ht, nm, zb_ = 2.0, 3.0, "door_arch", g + 0.2
                        else: wd, ht, nm, zb_ = 1.8, 2.7, "win_arch_ws", g + 0.5
                    else: wd, ht, nm, zb_ = 1.4, 2.6, "win_shut", g + f * 3.3 + 0.35
                    if not signed: wd, ht, nm, zb_ = 1.5, 1.7, "win_mod", g + f * 3.3 + 0.9          # plain house: no shutters, no restaurant door
                    oq(m, mdc, [P(cu - wd / 2, zb_), P(cu + wd / 2, zb_), P(cu + wd / 2, zb_ + ht), P(cu - wd / 2, zb_ + ht)], (nh[0], nh[1], 0), T.uvr(nm))
            if signed: RW_info.append((a, b, nh, tt, w, ze, q is longest, g))
        if signed: restaurant_extras(m, mp, mt, mf, mdc, RW_info, rp, loc, oz)
        RW_info = []
    # ---- finish --------------------------------------------------------
    hide = [list(h) for h in c.hide]
    for pre in (REST_ID, GATE_ID, CHIM_ID):
        for k, p in load(pre):
            if k == 0: hide.append([round(float(p[:, 0].mean()), 1), round(float(p[:, 1].mean()), 1)]); break
    OUTDIR.mkdir(parents=True, exist_ok=True); RAWDIR.mkdir(parents=True, exist_ok=True)
    raw = RAWDIR / "schlachthof.glb"; m.write(str(raw)); out = OUTDIR / "schlachthof.glb"
    r = subprocess.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(out), "-cc", "-kn"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:])
    print(f"schlachthof: {m.tri_count()} tris, " + ", ".join(f"{k}={v.tris()}" for k, v in m.mats.items()) + f", glb {out.stat().st_size // 1024} kB, walls {nwall}, windows {nwin}")
    assert m.tri_count() <= 30000, "tri budget"
    ids = HALL_IDS + [REST_ID, GATE_ID, CHIM_ID]
    OVR.write_text(json.dumps({"landmarks": [{"name": "Schlachthof Zuerich (Herdernstrasse)", "model": "/models/landmarks/schlachthof.glb", "x": round(ox, 2), "y": round(oy, 2), "z": round(oz, 2),
                                              "heading": 0, "hide": hide, "hide_ids": ids}]}, indent=1, ensure_ascii=False))
    import merge; merge.main()


if __name__ == "__main__":
    build()
