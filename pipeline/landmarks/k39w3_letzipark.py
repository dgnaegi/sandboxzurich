"""Letzipark (Baslerstrasse 50, Einkaufszentrum): volumes and roof levels straight from swissBUILDINGS3D (main roof 16.7 m above ground,
three 23 m cubes, lower Parkhaus wing east), grey panel facade with ribbon windows, arcade (canopy, blue columns with white globes, shopfronts with
real tenant plates, glazed entrances), sign cube with LETZIPARK roof letters + palm. research/letzipark.md"""
import sys; sys.path.insert(0, __file__.rsplit("/", 1)[0])
import json, math, subprocess
import numpy as np
from k39w3_kit import prep, W4, hexl, Model, panels, ROOT, OVR39
from common import ground
import detail as D
import schlachthof_lp_tex as LT
from schlachthof import load, oq

ID = "ID_9DCBF65B"; SIGN_CUBE = (-1362.0, 203.0)
OUTDIR = ROOT / "web/public/models/landmarks"; RAWDIR = ROOT / "data/build/landmarks"
BLUE, WHITE, GREY = hexl("#3f86d6"), hexl("#f2f2ec"), hexl("#8f959b")


class M8(Model):
    max_mats = 8


def build():
    c = prep([ID], 0.8); ox, oy, oz = c.ox, c.oy, c.oz
    loc = lambda p: p - np.array([ox, oy, oz]); gl = lambda x, y: ground(x + ox, y + oy) - oz
    m = M8("k39w3_letzipark")
    mwl = m.mat("wall_l", panels("#8c9298", nx=4, ny=3, gap="#6c7278", seed=2)); mwd = m.mat("wall_d", panels("#262a30", nx=4, ny=3, gap="#181b1f", seed=3))
    mwb = m.mat("wall_b", panels("#2f77c6", nx=4, ny=3, gap="#1f5a9c", seed=4)); mf = m.mat("flat", None, rough=0.9)
    dc = LT.decals(); mdc = m.mat("decal", dc[0], dc[1], rough=0.6); mdc.alpha_mask = True
    sg = LT.signs(); msg = m.mat("sign", sg[0], sg[1], rough=0.7); msg.alpha_mask = True
    polys = [(k, loc(p)) for k, p in load(ID)]
    sx, sy = SIGN_CUBE[0] - ox, SIGN_CUBE[1] - oy
    nwin = nshop = 0; ground_walls = []
    for k, q in polys:
        if k == 2:
            zz = q[:, 2].mean() + oz
            col = hexl("#7d7a62") if 6.5 < zz < 8 else (hexl("#7e8286") if zz > 8 else hexl("#8a8c8e"))
            n3 = np.cross(q[1] - q[0], q[2] - q[0]); n3 /= (np.linalg.norm(n3) + 1e-9)
            if n3[2] < 0: n3 = -n3
            if len(q) in (3, 4): oq(m, mf, [tuple(x) for x in q], n3, [(0, 0), (1, 0), (1, 1), (0, 1)][:len(q)], col)
    sign_walls = []
    for k, q in polys:
        if k != 1: continue
        z0 = float(q[:, 2].min()); z1 = float(q[:, 2].max()); xy = q[:, :2]
        if len(q) < 4 or z1 - z0 < 0.4: continue
        n3 = np.cross(q[1] - q[0], q[2] - q[0]); nh = n3[:2]; ln = np.hypot(*nh)
        if ln < 1e-6: continue
        nh = nh / ln; tt = np.array([-nh[1], nh[0]]); pr = xy @ tt; ia, ib = int(np.argmin(pr)), int(np.argmax(pr)); a, b = xy[ia], xy[ib]; w = float(pr[ib] - pr[ia])
        if w < 0.3: continue
        mid = (a + b) / 2; g = gl(*mid); z0 = max(z0, g - 1.5) if z0 < g - 1.5 else z0
        H = z1 - g; cube = (z1 + oz) > 12.0
        is_sign = cube and math.hypot(mid[0] - sx, mid[1] - sy) < 22
        mat = mwb if is_sign else (mwd if cube else mwl)
        u0 = float(a @ tt) / 4.0
        oq(m, mat, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], (nh[0], nh[1], 0), [(u0, z0 / 4), (u0 + w / 4, z0 / 4), (u0 + w / 4, z1 / 4), (u0, z1 / 4)])
        if is_sign: sign_walls.append((a, b, nh, tt, w, z0, z1, mid))
        if w < 3 or H < 4.5: continue
        P = lambda u, z, off=0.04: (a[0] + tt[0] * u + nh[0] * off, a[1] + tt[1] * u + nh[1] * off, z)
        def quad(rects, name, uc, zb_, wd, ht, off=0.04, mat_=mdc, W_=512, H_=768):
            oq(m, mat_, [P(uc - wd / 2, zb_, off), P(uc + wd / 2, zb_, off), P(uc + wd / 2, zb_ + ht, off), P(uc - wd / 2, zb_ + ht, off)], (nh[0], nh[1], 0), LT.uvr(rects, name, W_, H_))
        gw = z0 <= g + 1.5 and H >= 9 and w >= 8
        bands = []
        if not cube:
            if H >= 9: bands.append(g + 6.9)
            if H >= 15: bands.append(g + 10.9)
            if H < 9: bands.append(g + 2.2 if not gw else g + 6.9)
        for zb_ in bands:
            nseg = max(1, int((w - 1) // 8)); sw_ = (w - 1) / nseg
            for s in range(nseg): quad(LT.DR, "ribbon", 0.5 + (s + .5) * sw_, zb_, sw_ - 0.1, 2.0); nwin += 1
        D.band(m, mf, tuple(a), tuple(b), z1 - 0.7, z1 + 0.25, 0.25, hexl("#d9dde0"))
        if gw: ground_walls.append((a, b, nh, tt, w, z0, g, H))
    # ---- arcade: shopfronts + plates + entrances, canopy, blue columns with globes --------------------
    pl_i = 0
    for (a, b, nh, tt, w, z0, g, H) in ground_walls:
        P = lambda u, z, off=0.05: (a[0] + tt[0] * u + nh[0] * off, a[1] + tt[1] * u + nh[1] * off, z)
        nsh = max(1, int((w - 1) // 6.0)); sw_ = (w - 1) / nsh; ent = {nsh // 4, (3 * nsh) // 4} if w > 40 else ({nsh // 2} if w > 14 else set())
        for s in range(nsh):
            uc = 0.5 + (s + .5) * sw_
            if s in ent:
                oq(m, mdc, [P(uc - 2.3, g + 0.1), P(uc + 2.3, g + 0.1), P(uc + 2.3, g + 4.6), P(uc - 2.3, g + 4.6)], (nh[0], nh[1], 0), LT.uvr(LT.DR, "door", 512, 768))
            else:
                oq(m, mdc, [P(uc - sw_ / 2 + 0.05, g + 0.3), P(uc + sw_ / 2 - 0.05, g + 0.3), P(uc + sw_ / 2 - 0.05, g + 3.7), P(uc - sw_ / 2 + 0.05, g + 3.7)], (nh[0], nh[1], 0), LT.uvr(LT.DR, "shop", 512, 768)); nshop += 1
            name = f"plate{pl_i % 12}"; pl_i += 1
            oq(m, msg, [P(uc - 2.2, g + 3.85, 0.07), P(uc + 2.2, g + 3.85, 0.07), P(uc + 2.2, g + 4.6, 0.07), P(uc - 2.2, g + 4.6, 0.07)], (nh[0], nh[1], 0), LT.uvr(LT.SR, name, 1024, 1024))
        D.band(m, mf, tuple(a), tuple(b), g + 5.0, g + 5.5, 2.1, hexl("#9aa0a6"))                         # canopy slab
        nc = max(2, int(w // 7));
        for kk in range(nc + 1):
            u = min(w - 0.5, 0.6 + kk * (w - 1.2) / nc); p = P(u, g, 1.9)
            m.cylinder(mf, p[0], p[1], 0.3, g, g + 6.4, n=8, col=BLUE)
            m.cylinder(mf, p[0], p[1], 0.52, g + 6.4, g + 7.1, n=8, col=WHITE)
    # roof-edge poles with globes along the long street facades
    for (a, b, nh, tt, w, z0, g, H) in ground_walls:
        for kk in range(int(w // 12) + 1):
            u = 1.0 + kk * 12.0
            if u > w - 0.5: break
            p = (a[0] + tt[0] * u + nh[0] * 0.4, a[1] + tt[1] * u + nh[1] * 0.4); z1 = g + H
            m.cylinder(mf, p[0], p[1], 0.18, z1, z1 + 2.2, n=8, col=BLUE); m.cylinder(mf, p[0], p[1], 0.4, z1 + 2.2, z1 + 2.9, n=8, col=WHITE)
    # sign cube: LETZIPARK roof letters on the south and east faces, EINKAUFSZENTRUM + hours text, tenant plates
    for (a, b, nh, tt, w, z0, z1, mid) in sign_walls:
        ang = math.degrees(math.atan2(nh[1], nh[0]))
        if w < 15: continue
        P = lambda u, z, off=0.06: (a[0] + tt[0] * u + nh[0] * off, a[1] + tt[1] * u + nh[1] * off, z)
        if abs(ang + 112) < 25 or abs(ang + 22) < 25:
            oq(m, msg, [P(w / 2 - 8.5, z1 + 0.0, 0.25), P(w / 2 + 8.5, z1 + 0.0, 0.25), P(w / 2 + 8.5, z1 + 4.25, 0.25), P(w / 2 - 8.5, z1 + 4.25, 0.25)], (nh[0], nh[1], 0), LT.uvr(LT.SR, "letters", 1024, 1024))
            oq(m, msg, [P(w / 2 - 8.0, z1 - 7.0), P(w / 2 + 8.0, z1 - 7.0), P(w / 2 + 8.0, z1 - 5.0), P(w / 2 - 8.0, z1 - 5.0)], (nh[0], nh[1], 0), LT.uvr(LT.SR, "ekz", 1024, 1024))
            oq(m, msg, [P(w / 2 - 6.0, z1 - 12.0), P(w / 2 + 2.0, z1 - 12.0), P(w / 2 + 2.0, z1 - 8.0), P(w / 2 - 6.0, z1 - 8.0)], (nh[0], nh[1], 0), LT.uvr(LT.SR, "hours", 1024, 1024))
            for i, nm in enumerate(("plate0", "plate1", "plate2", "plate3")):
                oq(m, msg, [P(0.8 + i * 4.2, z1 - 3.4), P(0.8 + i * 4.2 + 4.0, z1 - 3.4), P(0.8 + i * 4.2 + 4.0, z1 - 2.6), P(0.8 + i * 4.2, z1 - 2.6)], (nh[0], nh[1], 0), LT.uvr(LT.SR, nm, 1024, 1024))
    # ---- finish -----------------------------------------------------------------------------------
    OUTDIR.mkdir(parents=True, exist_ok=True); RAWDIR.mkdir(parents=True, exist_ok=True)
    raw = RAWDIR / "k39w3_letzipark.glb"; m.write(str(raw)); out = OUTDIR / "k39w3_letzipark.glb"
    r = subprocess.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(out), "-cc", "-kn"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:])
    print(f"letzipark: {m.tri_count()} tris, " + ", ".join(f"{k}={v.tris()}" for k, v in m.mats.items()) + f", glb {out.stat().st_size // 1024} kB, windows {nwin}, shopfronts {nshop}")
    assert m.tri_count() <= 30000, "tri budget"
    d = json.load(open(OVR39)); old = next((e for e in d["landmarks"] if e["name"] == "Letzipark"), {"hide": []})
    hh = [list(h) for h in old["hide"]]
    for h in c.hide:
        if not any(abs(h[0] - o[0]) < 0.3 and abs(h[1] - o[1]) < 0.3 for o in hh): hh.append(list(h))
    d["landmarks"] = [e for e in d["landmarks"] if e["name"] != "Letzipark"]
    d["landmarks"].append({"name": "Letzipark", "model": "/models/landmarks/k39w3_letzipark.glb", "x": round(ox, 2), "y": round(oy, 2), "z": round(oz, 2), "heading": 0, "hide": hh, "hide_ids": [ID]})
    json.dump(d, open(OVR39, "w"), indent=1, ensure_ascii=False)
    import merge; merge.main()


if __name__ == "__main__":
    build()
