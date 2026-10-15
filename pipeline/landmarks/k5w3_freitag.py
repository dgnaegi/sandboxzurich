"""Freitag-Turm (Geroldstrasse 17-21, Hardbruecke): stacked shipping-container tower, ~26 m, 4 red/orange containers at the base,
yellow/white upper levels (SHOP / ZUERICH / cargo lettering), dark FREITAG board on top, rust-steel stair. Photos: research/v3/freitag_turm.md."""
import math
from k5w3_kit import *

CW, CL, CH = 2.44, 6.06, 2.59
COLS = ["#b3322a", "#c9482c", "#d9a526", "#d8b030", "#e4e2da", "#2e5a8a", "#3f7a4e", "#8a8d90"]
LAB = {1: ("CAI", "#f2f0e8"), 2: ("SHOP", "#6a5a30"), 3: ("ZUERICH", "#6a5a30"), 4: ("CARGO LINE", "#c4262e")}
CWPX, CHPX = 256, 112


def atlas():
    """4x2 container sides (1024 x 224) + sign strip 1024 x 64 at the bottom. UV v: sides 0..0.778 (top rows), sign 0.778..1."""
    H = 2 * CHPX + 64
    im = Image.new("RGB", (1024, H), (20, 20, 20)); d = ImageDraw.Draw(im); em = Image.new("RGB", (1024, H), (0, 0, 0)); de = ImageDraw.Draw(em)
    rng = np.random.default_rng(7); f = font("Barlow-Bold", 30)
    for k, col in enumerate(COLS):
        x0, y0 = (k % 4) * CWPX, (k // 4) * CHPX; C = rgb(col)
        d.rectangle([x0, y0, x0 + CWPX, y0 + CHPX], fill=C)
        for xx in range(x0 + 6, x0 + CWPX - 6, 5):   # corrugation
            d.line([xx, y0 + 10, xx, y0 + CHPX - 10], fill=mixc(C, (0, 0, 0), 0.22)); d.line([xx + 2, y0 + 10, xx + 2, y0 + CHPX - 10], fill=mixc(C, (255, 255, 255), 0.07))
        d.rectangle([x0, y0, x0 + CWPX - 1, y0 + 9], fill=mixc(C, (0, 0, 0), 0.35)); d.rectangle([x0, y0 + CHPX - 10, x0 + CWPX - 1, y0 + CHPX - 1], fill=mixc(C, (0, 0, 0), 0.35))
        d.rectangle([x0, y0, x0 + 8, y0 + CHPX], fill=mixc(C, (0, 0, 0), 0.3)); d.rectangle([x0 + CWPX - 9, y0, x0 + CWPX, y0 + CHPX], fill=mixc(C, (0, 0, 0), 0.3))
        for _ in range(7):   # rust/dirt streaks
            xx = int(rng.integers(x0 + 10, x0 + CWPX - 10)); d.line([xx, y0 + 10, xx, y0 + int(rng.integers(30, CHPX - 10))], fill=mixc(C, (110, 60, 30), 0.35))
        if k in LAB:
            t, fg = LAB[k]; f2 = f if len(t) < 8 else font("Barlow-Bold", 24)
            d.text((x0 + CWPX / 2, y0 + CHPX * 0.45), t, font=f2, fill=rgb(fg), anchor="mm")
    # sign
    d.rectangle([0, 2 * CHPX, 1023, H], fill=rgb("#202224")); fs = font("Barlow-Bold", 46)
    ws = [d.textlength(c, font=fs) for c in "FREITAG"]; gap = 14; cx = 512 - (sum(ws) + gap * 6) / 2
    for c, w in zip("FREITAG", ws):
        d.text((cx, 2 * CHPX + 34), c, font=fs, fill=(240, 240, 235), anchor="lm"); de.text((cx, 2 * CHPX + 34), c, font=fs, fill=(150, 150, 140), anchor="lm"); cx += w + gap
    return im.convert("RGBA"), em


def build():
    setup()
    ids = ["ID_EEAB2D69"]
    B = bid(ids[0]); fp = B["fp"]
    c = fp.centroid; ox, oy = round(c.x, 1), round(c.y, 1); oz = ground(ox, oy)
    ang = math.atan2(-4.0, 11.8)           # long axis of the footprint (-18.7 deg)
    ca, sa = math.cos(ang), math.sin(ang)
    m = Model("freitag_turm")
    ma = m.mat("cont", *atlas(), rough=0.55); mf = m.mat("flat", solid((255, 255, 255, 255)))
    rng = np.random.default_rng(21)
    H_SIDES = 2 * CHPX / (2 * CHPX + 64)

    def container(cx, cy, z0, rot, k, long_u=True, door_col=None):
        """box CL x CW rotated; long sides textured with atlas cell k, ends/top flat."""
        hl, hw = CL / 2, CW / 2
        loc = [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)]
        cr, sr = math.cos(rot), math.sin(rot)
        P = [(cx + x * cr - y * sr, cy + x * sr + y * cr) for x, y in loc]
        col = hexl(COLS[k]); z1 = z0 + CH
        Ht = 2 * CHPX + 64
        cu0, cv0 = (k % 4) / 4, 1 - ((k // 4) + 1) * CHPX / Ht      # v up: bottom of the cell
        du, dv = 0.25, CHPX / Ht
        for i in range(4):
            a, b = P[i], P[(i + 1) % 4]
            if i in (0, 2):   # long sides
                m.quad(ma, [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)],
                       [(cu0, cv0), (cu0 + du, cv0), (cu0 + du, cv0 + dv), (cu0, cv0 + dv)], W4)
            else:
                m.wall(mf, a, b, z0, z1, (3, 3), mixcol(col, 0.8))
        m.flat(mf, Polygon(P), z1, mixcol(col, 1.15))

    def mixcol(c, f):
        return tuple(min(255, int(v * f)) for v in c[:3]) + (255,)

    def at(u, v):   # tower-local (along long axis, across) -> model xy (model origin = centroid)
        return (u * ca - v * sa, u * sa + v * ca)

    # base: 2x2 containers, 3 levels (red/orange); above: 1 pair per level, crossing orientation
    layout = []
    base_k = [0, 1, 0, 1]
    for lv in range(3):
        for i, (u, v) in enumerate([(-CL / 2, -CW / 2 - 0.05), (CL / 2, -CW / 2 - 0.05), (-CL / 2, CW / 2 + 0.05), (CL / 2, CW / 2 + 0.05)]):
            layout.append((u + rng.normal(0, 0.1), v + rng.normal(0, 0.05), lv, 0.0, [0, 1, 0, 1][(i + lv) % 4]))
    top_k = [1, 2, 3, 4, 2, 3, 4]
    for j, lv in enumerate(range(3, 10)):
        rot = 0.0 if lv % 2 == 0 else math.pi / 2
        for s in (-1, 1):
            u, v = (0.0 + rng.normal(0, 0.12), s * (CW / 2 + 0.03)) if rot == 0 else (s * (CW / 2 + 0.03), rng.normal(0, 0.12) + 0.0)
            layout.append((u + (CL / 2 - CW) * 0 + (0.9 if lv % 2 == 0 else 0.0), v - (0.0 if lv % 2 == 0 else 0.0), lv, rot, top_k[j] if j != 3 else 4))
    for u, v, lv, rot, k in layout:
        x, y = at(u, v)
        container(x, y, lv * CH, ang + rot, k)
    # roof deck + FREITAG board (double sided slab on the top)
    ztop = 10 * CH
    bx, by = at(0.9, 0.0)
    bw, bh = 5.2, 1.7
    zb = ztop + 0.9
    m.box(mf, bx, by, bw, 0.35, zb, zb + bh, rot=ang, col=hexl("#202224"))
    for side in (-1, 1):
        px, py = bx - math.sin(ang) * side * 0.18, by + math.cos(ang) * side * 0.18
        a0 = (px - math.cos(ang) * bw / 2, py - math.sin(ang) * bw / 2); a1 = (px + math.cos(ang) * bw / 2, py + math.sin(ang) * bw / 2)
        q = [(a0[0], a0[1], zb), (a1[0], a1[1], zb), (a1[0], a1[1], zb + bh), (a0[0], a0[1], zb + bh)]
        uv = [(0.04, 0.02), (0.96, 0.02), (0.96, 62 / (2 * CHPX + 64)), (0.04, 62 / (2 * CHPX + 64))]
        if side < 0: q = [q[1], q[0], q[3], q[2]]
        m.quad(ma, q, uv, W4, n=(-math.sin(ang) * side, math.cos(ang) * side, 0))
    for sx in (-1.9, 1.9):
        x, y = at(0.9 + sx, 0)
        m.box(mf, x, y, 0.12, 0.12, ztop, zb, col=hexl("#2a2a2a"))
    # rust-steel stair on the long side, rising along the tower
    x0, y0 = at(-6.5, -CW - 0.9)
    stair_run(m, mf, x0, y0, ang, 8.5, 1.1, 0.0, 7.8, hexl("#8c4a2a"), steps=26)
    # low corner posts of the base platform / fence
    for u in (-6.4, 6.4):
        for v in (-CW - 0.7, CW + 0.7):
            x, y = at(u, v); m.box(mf, x, y, 0.1, 0.1, 0, 1.2, col=hexl("#6a6a68"))
    # concrete footing
    P = Polygon([at(u, v) for u, v in [(-7.2, -3.2), (7.2, -3.2), (7.2, 3.2), (-7.2, 3.2)]])
    m.extrude(mf, mf, P, -2.0, 0.12, col=hexl("#8e8d88"), rcol=hexl("#8e8d88"))
    hide = hide_pts(ids + ["ID_EEAB2D69"][:0])
    hide += [[207.0, 177.0]]
    finish(m, "freitag_turm", "Freitag-Turm", ox, oy, oz, hide)


if __name__ == "__main__":
    build()
