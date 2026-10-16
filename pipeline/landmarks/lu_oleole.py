"""Ole Ole Bar (Langstrasse 138, OSM node 4424003110): red corner house (EG red with dark-green plinth, arched ground-floor windows, corner door with steps,
three upper floors in orange-red plaster with white-framed windows and green shutters, hip roof with chimney), green corner sign 'OLE OLE BAR'.
Photos: research/v3/oleole.md (Mapillary fcignat 2025, Panoramax paulb_imagery 2024). Footprint = building ID_96E308DB."""
import json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import *
from lm import *
import detail as D
from shapely.geometry import Polygon

NAME, TITLE = "lu_oleole", "Ole Ole Bar (Langstrasse 138)"
BID = "ID_96E308DB"
EG, FH, NF = 4.6, 3.35, 3          # ground floor height, upper floor height, number of upper floors


def plaster(seed=3):
    r = np.random.default_rng(seed); a = np.full((128, 128, 3), 232.0)
    a += r.normal(0, 4, (128, 128, 1)) + np.asarray(Image.fromarray(r.normal(0, 1, (10, 10)).astype(np.float32)).resize((128, 128), Image.BICUBIC))[..., None] * 7
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def sign_tex():
    W, H = 512, 128
    im = Image.new("RGBA", (W, H), hexc("#2c6e3c")); em = Image.new("RGB", (W, H), (0, 0, 0))
    d, de = ImageDraw.Draw(im), ImageDraw.Draw(em)
    d.rectangle([0, 0, W - 1, H - 1], outline=hexc("#1a4126"), width=6); d.rectangle([10, 10, W - 11, H - 11], outline=hexc("#d8d0b0"), width=2)
    f = None
    for p in ("/System/Library/Fonts/Supplemental/Arial Black.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        try: f = ImageFont.truetype(p, 76); break
        except OSError: pass
    txt = "OLÉ OLÉ BAR"; cols = ["#f4f0e0", "#e8c21a", "#e8452b", "#f4f0e0", "#8fd0e8", "#e8c21a", "#e8452b", "#f4f0e0", "#e8c21a", "#8fd0e8", "#e8452b"]
    ws = [d.textlength(c, font=f) for c in txt]; x = (W - sum(ws)) / 2
    for c, w, cl in zip(txt, ws, cols):
        d.text((x + 3, 69), c, font=f, fill=hexc("#10281a"), anchor="lm"); d.text((x, 66), c, font=f, fill=hexc(cl), anchor="lm")
        de.text((x, 66), c, font=f, fill=hexc(cl)[:3], anchor="lm"); x += w
    de.rectangle([0, 0, W - 1, H - 1], outline=(40, 70, 50), width=3)
    return im, em


def build():
    b = bid(BID); fp = outline(b["fp"], 0.3)
    ring = list(fp.exterior.coords)[:-1]
    if not fp.exterior.is_ccw: ring = ring[::-1]
    c = fp.centroid; ox, oy = round(c.x, 1), round(c.y, 1)
    gz = ground(ox, oy); oz = gz
    loc = [(x - ox, y - oy) for x, y in ring]
    n = len(loc); rng = np.random.default_rng(5)
    m = Model(NAME)
    mw = m.mat("wall", plaster(), rough=0.95)
    ga = D.glass_atlas_g(frame="#e9e4d6", glass="#26323d", sky="#8fa9bb", cols=2, rows=3, seed=21, cw=128, ch=96, bar=3, lit_p=0.55, curtains=True)
    mg = m.mat("glass", *ga, rough=0.3)
    st, se = sign_tex(); ms = m.mat("sign", st, se, rough=0.6)
    RED_EG, ORG, GREEN, WHITE, ROOF, GREY = D.hexl("#b0453a"), D.hexl("#c9583b"), D.hexl("#33583f"), D.hexl("#e8e2d2"), D.hexl("#5d3e36"), D.hexl("#8a8780")
    SHUT = D.hexl("#2f5f43")
    wl = lambda i: (loc[i], loc[(i + 1) % n])
    # edge roles by direction (CCW ring): corner cut (shortest edge) = entrance
    lens = [math.dist(*wl(i)) for i in range(n)]
    corner = int(np.argmin(lens))
    top = EG + NF * FH
    for i in range(n):
        a, bb = wl(i); L, t, nn = D.frame_of(a, bb)
        front = i in (corner, (corner + 1) % n, (corner - 1) % n)
        # --- ground floor: arched windows on the street faces, corner door on the cut
        if i == corner:
            uc = L / 2; hole = D.arch_pts(uc - 0.85, 0.55, uc + 0.85, 2.35)
            D.bay(m, mw, mg, mw, a, t, nn, 0, L, 0, EG, hole, 0.3, 1, RED_EG, WHITE, (3.0, 3.0), None)
            D.surround(m, mw, a, t, nn, hole, 0.22, WHITE, 0.06)
            D.poly_wall(m, mw, Polygon(hole), a, t, nn, -0.27, GREEN, lambda u, z: (0.5, 0.5))        # green door leaf
            for q in range(3):   # steps up to the door (q=0 lowest, outermost)
                p = D.P3(a, t, nn, uc, 0, 0.30 + 0.30 * (2 - q)); m.box(mw, p[0], p[1], 1.9, 0.34, -0.3, 0.14 * (q + 1), rot=math.atan2(t[1], t[0]), col=GREY)
        else:
            def eg(u0, u1, z0, z1, f):
                if not front: return D.arch_pts(u0 + 0.5, z0 + 0.9, u1 - 0.5, z0 + 2.9) if u1 - u0 > 2.0 else None
                return D.arch_pts(u0 + 0.45, z0 + 0.85, u1 - 0.45, z0 + 2.7)
            D.wall_run(m, mw, mg, mw, a, bb, 0.0, 1, EG, 2.7, eg, 0.25, RED_EG, WHITE, rng, (3.0, 3.0), 0.12)
        # --- upper floors
        def up(u0, u1, z0, z1, f):
            w = u1 - u0
            if w < 1.6: return None
            cx = (u0 + u1) / 2
            return D.rect_pts(cx - 0.55, z0 + 0.85, cx + 0.55, z0 + 2.55)
        D.wall_run(m, mw, mg, mw, a, bb, EG, NF, FH, 2.7, up, 0.2, ORG, WHITE, rng, (3.0, 3.0), 0.1)
        # shutters (open leaves flanking each window) on the street faces
        nb = max(1, int(round(L / 2.7))); bw = L / nb
        for f in range(NF):
            for k in range(nb):
                if bw < 1.6: continue
                cx = (k + 0.5) * bw; z0 = EG + f * FH + 0.85
                for sg in (-1, 1):
                    p0 = D.P3(a, t, nn, cx + sg * 0.58, z0, 0.04); p1 = D.P3(a, t, nn, cx + sg * 0.58 + sg * 0.5, z0, 0.04)
                    m.quad(mw, [p0, p1, (p1[0], p1[1], z0 + 1.7), (p0[0], p0[1], z0 + 1.7)], [(0.5, 0.5)] * 4, SHUT, n=(nn[0], nn[1], 0)) if sg > 0 else \
                        m.quad(mw, [p1, p0, (p0[0], p0[1], z0 + 1.7), (p1[0], p1[1], z0 + 1.7)], [(0.5, 0.5)] * 4, SHUT, n=(nn[0], nn[1], 0))
        # plinth (dark green) + cornices
        D.band(m, mw, a, bb, -0.3, 0.75, 0.05, GREEN); D.band(m, mw, a, bb, EG - 0.1, EG + 0.12, 0.12, WHITE); D.band(m, mw, a, bb, top - 0.1, top + 0.35, 0.35, WHITE)
    # sign board on the corner cut, above the door (on a small balcony slab)
    a, bb = wl(corner); L, t, nn = D.frame_of(a, bb); uc = L / 2
    z0, z1 = 3.35, 4.25; w = 3.2
    p0 = D.P3(a, t, nn, uc - w / 2, z0, 0.55); p1 = D.P3(a, t, nn, uc + w / 2, z0, 0.55)
    m.quad(ms, [p0, p1, (p1[0], p1[1], z1), (p0[0], p0[1], z1)], [(0, 0), (1, 0), (1, 1), (0, 1)], (255, 255, 255, 255), n=(nn[0], nn[1], 0))
    for sgn in (-1, 1):   # side returns of the board
        pa = D.P3(a, t, nn, uc + sgn * w / 2, z0, 0.55); pb = D.P3(a, t, nn, uc + sgn * w / 2, z0, 0.05)
        m.quad(ms, [pa, pb, (pb[0], pb[1], z1), (pa[0], pa[1], z1)] if sgn < 0 else [pb, pa, (pa[0], pa[1], z1), (pb[0], pb[1], z1)], [(0.02, 0.1)] * 4, (30, 60, 40, 255))
    D.band(m, mw, D.P3(a, t, nn, uc - 1.9, 0, 0)[:2], D.P3(a, t, nn, uc + 1.9, 0, 0)[:2], EG - 0.25, EG - 0.05, 0.75, GREEN)   # balcony slab under the sign
    # hip roof + chimney
    roof_poly = [(x, y) for x, y in Polygon(loc).buffer(0.5, join_style=2).exterior.coords][:-1]
    m.hip(mw, roof_poly, top + 0.35, 3.8, ROOF, ridge_frac=0.55)
    cx_, cy_ = Polygon(loc).centroid.x, Polygon(loc).centroid.y
    m.box(mw, cx_ + 1.2, cy_ - 0.5, 0.9, 0.9, top + 1.2, top + 5.2, col=D.hexl("#7a5a4a"))
    finish_lu(m, ox, oy, oz, [[round(fp.representative_point().x, 1), round(fp.representative_point().y, 1)]])


def finish_lu(m, ox, oy, oz, hide):
    import subprocess
    OUTDIR.mkdir(parents=True, exist_ok=True); RAWDIR.mkdir(parents=True, exist_ok=True)
    raw = RAWDIR / f"{NAME}.glb"; m.write(str(raw)); dst = OUTDIR / f"{NAME}.glb"
    r = subprocess.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(dst), "-cc", "-kn"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:])
    print(f"{NAME}: {m.tri_count()} tris, glb {dst.stat().st_size // 1024} kB, origin {ox},{oy} z {oz:.2f}")
    F = ROOT / "pipeline" / "overrides" / "landmarks_lu.json"
    d = json.load(open(F)) if F.exists() else {"landmarks": []}
    d["landmarks"] = [e for e in d["landmarks"] if e["name"] != TITLE] + [{"name": TITLE, "model": f"/models/landmarks/{NAME}.glb", "x": ox, "y": oy, "z": round(oz, 2), "heading": 0, "hide": hide}]
    json.dump(d, open(F, "w"), separators=(",", ":"))
    import merge; merge.main()


if __name__ == "__main__":
    build()
