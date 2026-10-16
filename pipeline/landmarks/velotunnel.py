"""Velotunnel Stadttunnel (Zuerich HB), south half (160 m): portal with open ramp trench, tunnel tube, closed end wall.
Axis from OSM (research/hb/velotunnel.md). Model frame = world local metres minus ORG, z absolute. Material names hb3_pit/hb3_lit/hb3_mask reuse the hb3
stencil mechanism (landmarks3d.ts). Decks -> web/public/data/velotunnel_decks.json (same format as hb3_decks.json, loaded in tiles.ts // velotunnel).
Does NOT call merge.py (override file pipeline/overrides/landmarks_velotunnel.json is merged by the main session)."""
import sys, json, math
from hb_kit import *
common.OVR = ROOT / "pipeline" / "overrides" / "landmarks_velotunnel.json"

AX = [(1470.5, -724.8), (1489.2, -697.5), (1523.0, -648.3), (1551.7, -578.6)]
LEN, STEP, HW, H = 160.0, 2.0, 3.0, 3.8      # modelled length, sample step, half width (6 m), clear height
GRADE, DEPTH = 0.08, 7.0
ORGV = (1500.0, -680.0)
CONC, CONC_D, FLOOR = hx("#b4b6b4"), hx("#8a8d8e"), hx("#4a4b4f")
LANE = hx("#d8d8d0")


def axis(s):
    """Point and unit tangent at arc length s."""
    a = 0.0
    for p, q_ in zip(AX, AX[1:]):
        l = math.hypot(q_[0] - p[0], q_[1] - p[1])
        if s <= a + l or q_ is AX[-1]:
            t = (s - a) / l; return (p[0] + (q_[0] - p[0]) * t, p[1] + (q_[1] - p[1]) * t), ((q_[0] - p[0]) / l, (q_[1] - p[1]) / l)
        a += l


def atlas():
    img = Image.new("RGBA", (256, 128), (255, 255, 255, 255)); em = Image.new("RGBA", (256, 128), (0, 0, 0, 255))
    d, de = ImageDraw.Draw(img), ImageDraw.Draw(em)
    d.rectangle([0, 0, 63, 63], fill=(255, 255, 255, 255)); de.rectangle([0, 0, 63, 63], fill=(255, 255, 255, 255))
    for dd, col in ((d, (30, 90, 160, 255)), (de, (255, 255, 255, 255))):   # bike pictogram cell (64..127, 0..63)
        dd.rectangle([64, 0, 127, 63], fill=(255, 255, 255, 255) if dd is d else (0, 0, 0, 255))
        for cx in (78, 112):
            dd.ellipse([cx - 9, 36, cx + 9, 54], outline=col, width=3)
        dd.line([78, 45, 92, 28, 108, 28, 112, 45], fill=col, width=3); dd.line([92, 28, 98, 45, 78, 45], fill=col, width=3)
        dd.line([104, 28, 106, 20, 114, 20], fill=col, width=3)
    sign_text("STADTTUNNEL", "#ffffff", "#2a5a8c", glow=(255, 255, 255, 255), size=15, frame="#ffffff")(d, de, 128, 0, 128, 64)
    return img, em


def build():
    m = Model("velotunnel")
    img, em = atlas()
    P = m.mat("hb3_pit", Image.new("RGBA", (4, 4), (255, 255, 255, 255)), None, 0.9); LIT = m.mat("hb3_lit", img, em, 0.8); MASK = m.mat("hb3_mask", Image.new("RGBA", (4, 4), (255, 255, 255, 255)))
    g0 = common.ground(*AX[0])
    n = int(LEN / STEP); rows = []; PU = [(0.02, 0.02), (0.1, 0.02), (0.1, 0.2), (0.02, 0.2)]
    prof = []
    for i in range(n + 1):
        s = i * STEP; (x, y), (tx, ty) = axis(s); nx, ny = -ty, tx
        zf = g0 - 0.15 - min(s * GRADE, DEPTH)
        gnd = common.ground(x, y)
        prof.append((s, x - ORGV[0], y - ORGV[1], tx, ty, nx, ny, zf, gnd, x, y))
    def at(p, k, z): return (p[1] + p[5] * k, p[2] + p[6] * k, z)
    open_ = []
    for a, b in zip(prof, prof[1:]):
        isopen = max(a[7], b[7]) + H + 0.3 > min(a[8], b[8])
        open_.append(isopen)
        q(m, P, [at(a, -HW, a[7]), at(b, -HW, b[7]), at(b, HW, b[7]), at(a, HW, a[7])], FLOOR, None, (0, 0, 1))
        for k, sg in ((-HW, 1), (HW, -1)):
            ta = max(a[8], a[7] + 1.0) if isopen else a[7] + H; tb = max(b[8], b[7] + 1.0) if isopen else b[7] + H
            q(m, P, [at(a, k, a[7]), at(b, k, b[7]), at(b, k, tb), at(a, k, ta)], CONC, None, (sg * a[5], sg * a[6], 0))
            # lit wall band at 2.5 m (warm), on the lit material, slightly inside
            if not isopen or a[7] + 3.0 < a[8]:
                kk = k + sg * 0.03
                q(m, LIT, [at(a, kk, a[7] + 2.3), at(b, kk, b[7] + 2.3), at(b, kk, b[7] + 2.6), at(a, kk, a[7] + 2.6)], hx("#fff0c8"), PU, (sg * a[5], sg * a[6], 0))
        if not isopen:
            q(m, P, [at(a, -HW, a[7] + H), at(b, -HW, b[7] + H), at(b, HW, b[7] + H), at(a, HW, a[7] + H)], CONC_D, None, (0, 0, -1))
            if int(a[0] / STEP) % 4 == 0:   # ceiling light panel
                q(m, LIT, [at(a, -0.3, a[7] + H - 0.03), at(b, -0.3, b[7] + H - 0.03), at(b, 0.3, b[7] + H - 0.03), at(a, 0.3, a[7] + H - 0.03)], hx("#fff6d8"), PU, (0, 0, -1))
        if int(a[0] / STEP) % 3 == 0:   # dashed centre line
            q(m, P, [at(a, -0.06, a[7] + 0.01), at(b, -0.06, b[7] + 0.01), at(b, 0.06, b[7] + 0.01), at(a, 0.06, a[7] + 0.01)], LANE, None, (0, 0, 1))
        if int(a[0] / STEP) % 4 == 0:      # edge lines
            for k in (-HW + 0.3, HW - 0.3):
                q(m, P, [at(a, k - 0.05, a[7] + 0.01), at(b, k - 0.05, b[7] + 0.01), at(b, k + 0.05, b[7] + 0.01), at(a, k + 0.05, a[7] + 0.01)], LANE, None, (0, 0, 1))
    # pictograms every 24 m, one per lane (cell x 64..127 of 256 wide, y 0..64 of 128)
    for i in range(10, n - 4, 12):
        p, p2 = prof[i], prof[i + 1]
        for k in (-1.5, 1.5):
            c0, c1 = (64 / 256, 64 / 128), (128 / 256, 0)
            a_, b_ = at(p, k, p[7] + 0.02), at(p2, k, p2[7] + 0.02)
            w = (-p[6] * 0.9, p[5] * 0.9)   # across-lane half width direction is tangent-normal swapped: use normal
            nxv, nyv = p[5] * 0.9, p[6] * 0.9
            L = 2.2
            f = (p[3] * L, p[4] * L)
            pts = [(a_[0] - nxv, a_[1] - nyv, a_[2]), (a_[0] + nxv, a_[1] + nyv, a_[2]), (a_[0] + nxv + f[0], a_[1] + nyv + f[1], a_[2]), (a_[0] - nxv + f[0], a_[1] - nyv + f[1], a_[2])]
            q(m, LIT, pts, W, [(c0[0], c0[1]), (c1[0], c0[1]), (c1[0], c1[1]), (c0[0], c1[1])], (0, 0, 1))
    # closed end wall
    e = prof[-1]
    q(m, P, [at(e, -HW, e[7]), at(e, HW, e[7]), at(e, HW, e[7] + H), at(e, -HW, e[7] + H)], CONC_D, None, (-e[3], -e[4], 0))
    q(m, LIT, [at(e, -1.8, e[7] + 1.5), at(e, 1.8, e[7] + 1.5), at(e, 1.8, e[7] + 2.4), at(e, -1.8, e[7] + 2.4)], W, [(128 / 256, 64 / 128), (1, 64 / 128), (1, 0), (128 / 256, 0)], (-e[3] * 1.0, -e[4] * 1.0, 0))
    q(m, LIT, [at(e, -1.8, e[7] + 1.5), at(e, 1.8, e[7] + 1.5), at(e, 1.8, e[7] + 2.4), at(e, -1.8, e[7] + 2.4)], W, [(128 / 256, 64 / 128), (1, 64 / 128), (1, 0), (128 / 256, 0)], (-e[3], -e[4], 0))
    # stencil mask over the open trench (merged runs)
    for (a, b), o in zip(zip(prof, prof[1:]), open_):
        if o:
            m.quad(MASK, [at(a, -HW - 0.2, 0.0), at(b, -HW - 0.2, 0.0), at(b, HW + 0.2, 0.0), at(a, HW + 0.2, 0.0)], None, W)
    return m, prof


def decks(prof):
    pts = [[round(p[9], 2), round(p[10], 2), round(p[7], 2)] for p in prof]
    return {"decks": [{"p": pts, "g": [round(p[8], 2) for p in prof], "b": [round(p[7] - 0.4, 2) for p in prof], "w": 2 * HW - 0.4, "kind": "foot", "name": "Velotunnel Stadttunnel", "sub": True}], "piers": []}


if __name__ == "__main__":
    m, prof = build()
    OUTDIR.mkdir(parents=True, exist_ok=True); RAWDIR.mkdir(parents=True, exist_ok=True)
    raw = RAWDIR / "velotunnel.glb"; m.write(str(raw)); out = OUTDIR / "velotunnel.glb"
    r = common._sp.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(out), "-cc", "-kn"], capture_output=True, text=True)
    print(r.stderr[-300:] if r.returncode else "", m.tri_count(), "tris", out.stat().st_size // 1024, "kB")
    title = "Velotunnel Stadttunnel"
    json.dump({"landmarks": [{"name": title, "model": "/models/landmarks/velotunnel.glb", "x": ORGV[0], "y": ORGV[1], "z": 0.0, "heading": 0.0, "hide": [], "walkable": True, "load_r": 250}]}, open(common.OVR, "w"), indent=1)
    json.dump(decks(prof), open(ROOT / "web/public/data/velotunnel_decks.json", "w"), separators=(",", ":"))
    print("open runs:", sum(1 for p in prof if p[7] + H + 0.3 > p[8]), "of", len(prof), "end", prof[-1][9:], "z", prof[-1][7])
