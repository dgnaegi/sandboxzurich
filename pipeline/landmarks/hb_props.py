"""Zuerich HB: painted sign atlas (neutral lettering, no SBB logo / no SBB clock design) and interior props: departure boards, neutral station clocks,
kiosks and shop fronts, market stalls, Shopville stair wells, benches, the hanging angel sculpture (stylised homage to the Schutzengel), lamps."""
from hb_kit import *
import hb_geom as G

DEST = [("07:12", "Chur", "7"), ("07:15", "Bern", "31"), ("07:17", "Luzern", "12"), ("07:20", "Basel SBB", "16"), ("07:24", "St. Gallen", "9"),
        ("07:26", "Winterthur", "5"), ("07:29", "Genève-Aéroport", "14"), ("07:33", "Zug", "34"), ("07:36", "Stein am Rhein", "6"),
        ("07:40", "Zürich Flughafen", "3"), ("07:44", "Lugano", "10"), ("07:47", "Konstanz", "8")]
SHOPS = [("BÄCKEREI", "#8a4b25"), ("KIOSK", "#b53a2f"), ("APOTHEKE", "#2f7d4c"), ("BUCHHANDLUNG", "#2d4f7a"), ("CAFÉ", "#6b3f2a"),
         ("BLUMEN", "#8e3b73"), ("REISEBÜRO", "#2a6f8f"), ("IMBISS", "#9a6b1c"), ("SCHUHE", "#4a4a4a"), ("MODE", "#6a2d52"), ("FOTO", "#2d6a6a"), ("SNACKS", "#a1481f")]


def make_atlas(kind='inner'):
    A = SignAtlas(*((1024, 576) if kind == 'inner' else (512, 384))); R = A.rects
    f = lambda n, s: font(n, s)

    def board(d, de, x, y, w, h):
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=(18, 40, 120)); ff = f("Barlow-Bold", 24); fs = f("Barlow-Bold", 18)
        d.rectangle([x, y, x + w - 1, y + 32], fill=(190, 30, 36)); d.text((x + 12, y + 16), "ABFAHRT  /  DEPARTURE", font=ff, fill=(255, 255, 255), anchor="lm")
        de.text((x + 12, y + 16), "ABFAHRT  /  DEPARTURE", font=ff, fill=(120, 120, 120), anchor="lm")
        for i, (t, dst, gl) in enumerate(DEST):
            yy = y + 44 + i * 28
            for xx, s_, col in ((x + 12, t, (255, 255, 255)), (x + 100, dst, (255, 255, 255)), (x + w - 60, gl, (255, 255, 255))):
                d.text((xx, yy), s_, font=fs, fill=col, anchor="lm"); de.text((xx, yy), s_, font=fs, fill=tuple(int(v * 0.8) for v in col), anchor="lm")
    A.add("board", 480, 384, board) if kind == "inner" else A.add_scaled("board", 320, 256, board, 480, 384)

    def clock(d, de, x, y, w, h):   # neutral dial (Arabic numerals, classic spade hands) - not the protected SBB station clock
        cx, cy, r = x + w / 2, y + h / 2, w / 2 - 4
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 30, 32)); d.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], fill=(240, 237, 226))
        for i in range(12):
            a = math.radians(i * 30 - 90); d.text((cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a)), str(i or 12), font=f("DMSerifDisplay-Regular", 30), fill=(30, 30, 30), anchor="mm")
        for ang, ln, wd in ((math.radians(-60), r * 0.55, 7), (math.radians(60), r * 0.8, 4)):
            d.line([cx, cy, cx + ln * math.cos(ang), cy + ln * math.sin(ang)], fill=(25, 25, 25), width=wd)
        de.ellipse([cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8], fill=(55, 52, 44))
    A.add("clock", 192, 192, clock) if kind == "inner" else A.add_scaled("clock", 128, 128, clock, 192, 192)
    if kind == 'inner':
        for i, (t, col) in enumerate(SHOPS):
            A.add(f"shop{i}", 160, 40, sign_text(t, "#f4f0e4", col, glow=(255, 232, 190), size=22, frame="#e8dfc8"))
        A.add("shopville", 240, 56, sign_text("SHOPVILLE  ↓", "#ffffff", "#27547a", glow=(200, 220, 255), size=30))
        A.add("gleise", 240, 56, sign_text("GLEISE  ←  PERRONS", "#ffffff", "#2b2e33", glow=(200, 200, 200), size=24))
        A.add("wood", 48, 48, lambda d, de, x, y, w, h: [d.rectangle([x, y + k * 6, x + w - 1, y + k * 6 + 5], fill=(150 - k * 3, 100 - k * 2, 60)) for k in range(8)])
        A.add("lamp", 16, 16, lambda d, de, x, y, w, h: (d.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 250, 235)), de.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 238, 200))))
        return A
    for n in ("3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18"):
        A.add_scaled("gl" + n, 40, 40, sign_text(n, "#ffffff", "#2b2e33", glow=(200, 200, 200), size=34), 48, 48)
    A.add("lamp", 16, 16, lambda d, de, x, y, w, h: (d.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 250, 235)), de.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 238, 200))))
    return A


def box_uv(m, mat, d0, d1, c0, c1, z0, z1, rect, col=W):
    """Box whose faces all map to one atlas rect (lamps, plain coloured panels)."""
    u0, v0, u1, v1 = rect; uvc = ((u0 + u1) / 2, (v0 + v1) / 2); uv = [uvc] * 4
    for pts, nn in (([(d0, c0, z0), (d1, c0, z0), (d1, c0, z1), (d0, c0, z1)], (0, -1, 0)), ([(d1, c0, z0), (d1, c1, z0), (d1, c1, z1), (d1, c0, z1)], (1, 0, 0)),
                    ([(d1, c1, z0), (d0, c1, z0), (d0, c1, z1), (d1, c1, z1)], (0, 1, 0)), ([(d0, c1, z0), (d0, c0, z0), (d0, c0, z1), (d0, c1, z1)], (-1, 0, 0)),
                    ([(d0, c0, z1), (d1, c0, z1), (d1, c1, z1), (d0, c1, z1)], (0, 0, 1)), ([(d0, c1, z0), (d1, c1, z0), (d1, c0, z0), (d0, c0, z0)], (0, 0, -1))):
        q(m, mat, pts, col, uv, nn)


def board_pair(m, ms, mf, A, d, c, zc, wd=6.4, ht=4.6, rot_axis='c', hang=None):
    """Two-sided hanging departure board, facing +/-d, centre (d, c), vertical centre zc. Hangs from `hang` (ceiling z) on rods."""
    R = A.rects["board"]
    for s in (-1, 1):
        dd = d + s * 0.08
        pts = [(dd, c + s * wd / 2 * -1, zc - ht / 2), (dd, c - s * wd / 2 * -1, zc - ht / 2), (dd, c - s * wd / 2 * -1, zc + ht / 2), (dd, c + s * wd / 2 * -1, zc + ht / 2)]
        # s=+1 faces +d: right-hand side of (c-direction -> +c) ... build explicitly facing s
        a, b = (c - wd / 2, c + wd / 2) if s > 0 else (c + wd / 2, c - wd / 2)
        m.quad(ms, [(dd, a, zc - ht / 2), (dd, b, zc - ht / 2), (dd, b, zc + ht / 2), (dd, a, zc + ht / 2)], uvr(R) if s < 0 else uvr(R), W)
    bx(m, mf, d - 0.1, d + 0.1, c - wd / 2 - 0.1, c + wd / 2 + 0.1, zc - ht / 2 - 0.1, zc + ht / 2 + 0.1, hx("#202226"), top=True, sides=(1, 0, 1, 0))
    if hang:
        for cc in (c - wd / 2 + 0.4, c + wd / 2 - 0.4): bx(m, mf, d - 0.04, d + 0.04, cc - 0.04, cc + 0.04, zc + ht / 2, hang, hx("#303338"), top=False)


def clock_pair(m, ms, mf, A, d, c, zc, r=1.1, hang=None):
    R = A.rects["clock"]
    for s in (-1, 1):
        dd = d + s * 0.1
        a, b = (c - r, c + r) if s > 0 else (c + r, c - r)
        m.quad(ms, [(dd, a, zc - r), (dd, b, zc - r), (dd, b, zc + r), (dd, a, zc + r)], uvr(R), W)
    bx(m, mf, d - 0.09, d + 0.09, c - r - 0.05, c + r + 0.05, zc - r - 0.05, zc + r + 0.05, hx("#25272a"), top=True, sides=(1, 0, 1, 0))
    if hang: bx(m, mf, d - 0.04, d + 0.04, c - 0.04, c + 0.04, zc + r, hang, hx("#303338"), top=False)


def kiosk(m, ms, mf, A, d, c, w, dp, h, sign_i, rot=0, col="#c9c2b0"):
    """Free-standing kiosk (box) with a roof board and neutral sign on all four sides."""
    bx(m, mf, d - w / 2, d + w / 2, c - dp / 2, c + dp / 2, 0, h, hx(col), top=True)
    bx(m, mf, d - w / 2 - 0.15, d + w / 2 + 0.15, c - dp / 2 - 0.15, c + dp / 2 + 0.15, h, h + 0.5, hx("#33363a"), top=True)
    R = A.rects[f"shop{sign_i % len(SHOPS)}"]
    sign_q(m, ms, (d - w / 2, c - dp / 2 - 0.16), (d + w / 2, c - dp / 2 - 0.16), h + 0.05, h + 0.45, R)
    sign_q(m, ms, (d + w / 2, c + dp / 2 + 0.16), (d - w / 2, c + dp / 2 + 0.16), h + 0.05, h + 0.45, R)
    # counter window band
    q(m, mf, [(d - w / 2 + 0.3, c - dp / 2 - 0.01, 1.0), (d + w / 2 - 0.3, c - dp / 2 - 0.01, 1.0), (d + w / 2 - 0.3, c - dp / 2 - 0.01, h - 0.4), (d - w / 2 + 0.3, c - dp / 2 - 0.01, h - 0.4)], hx("#2b3944"), None, (0, -1, 0))
    q(m, mf, [(d + w / 2 - 0.3, c + dp / 2 + 0.01, 1.0), (d - w / 2 + 0.3, c + dp / 2 + 0.01, 1.0), (d - w / 2 + 0.3, c + dp / 2 + 0.01, h - 0.4), (d + w / 2 - 0.3, c + dp / 2 + 0.01, h - 0.4)], hx("#2b3944"), None, (0, 1, 0))


def stall(m, ms, mf, A, d, c, w=3.2, dp=2.2, h=2.3, seed=0):
    """Wooden market hut with gable roof and striped awning."""
    rng = np.random.default_rng(seed); rc = [hx("#efe3c8"), hx("#e8e0d0"), hx("#f1e8d2"), hx("#e5d8b8")][seed % 4]
    Rw = A.rects["wood"]
    box_uv(m, ms, d - w / 2, d + w / 2, c - dp / 2, c + dp / 2, 0, h, Rw)
    for s in (-1, 1):
        q(m, mf, [(d - w / 2 - 0.2, c + s * (dp / 2 + 0.2), h), (d + w / 2 + 0.2, c + s * (dp / 2 + 0.2), h), (d + w / 2 + 0.2, c, h + 0.9), (d - w / 2 - 0.2, c, h + 0.9)], rc, None, (0, s * 0.6, 1))
    for s in (-1, 1): tri(m, mf, [(d + s * (w / 2 + 0.2), c - dp / 2 - 0.2, h), (d + s * (w / 2 + 0.2), c + dp / 2 + 0.2, h), (d + s * (w / 2 + 0.2), c, h + 0.9)], hx("#6b4a30"), None, (s, 0, 0))
    bx(m, mf, d - w / 2 + 0.2, d + w / 2 - 0.2, c - dp / 2 - 0.02, c - dp / 2 + 0.05, 0.9, 1.0, hx("#caa56a"), top=True)   # counter shelf
    for k in range(5):  # goods
        bx(m, mf, d - w / 2 + 0.4 + k * 0.55, d - w / 2 + 0.75 + k * 0.55, c - dp / 2 - 0.1, c - dp / 2 + 0.2, 1.0, 1.25 + 0.1 * (k % 3), [hx("#d9482b"), hx("#e5c14a"), hx("#7a4a2e"), hx("#4c8a3c"), hx("#c25a8a")][(k + seed) % 5], top=True)


def lamp(m, ms, A, d, c, z, hang_to):
    R = A.rects["lamp"]
    box_uv(m, ms, d - 0.45, d + 0.45, c - 0.45, c + 0.45, z - 0.35, z + 0.05, R)
    bx(m, ms, d - 0.03, d + 0.03, c - 0.03, c + 0.03, z + 0.05, hang_to, hx("#2a2c2f"), top=False)


def angel(m, mf, d, c, z):
    """Hanging angel sculpture (stylised, ~11 m long): blue body, bright wings, outstretched arms. Colours only, no texture."""
    body, face, wing = hx("#233a8f"), hx("#e8c9a8"), [hx("#d9402b"), hx("#f2c230"), hx("#3b9a4d"), hx("#8a3a9a")]
    n = 10
    for i in range(n):   # torso: tapered capsule along d (head toward -d)
        t0, t1 = i / n, (i + 1) / n
        r0 = 0.9 * math.sin(math.pi * (0.15 + 0.7 * t0)) + 0.15; r1 = 0.9 * math.sin(math.pi * (0.15 + 0.7 * t1)) + 0.15
        d0_, d1_ = d - 4.5 + 9 * t0, d - 4.5 + 9 * t1
        for k in range(8):
            a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
            P = lambda dd, r, a: (dd, c + r * math.cos(a), z + r * math.sin(a))
            q(m, mf, [P(d0_, r0, a0), P(d1_, r1, a0), P(d1_, r1, a1), P(d0_, r0, a1)], body if (i + k) % 5 else hx("#f2c230"), None, (0, math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2)))
    for k in range(8):   # head
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        for j in range(3):
            r0 = 0.7 * math.sin(math.pi * j / 3 + 0.4); r1 = 0.7 * math.sin(math.pi * (j + 1) / 3 + 0.4)
            P = lambda r, a, j_: (d - 5.0 - 0.6 * math.cos(math.pi * j_ / 3), c + r * math.cos(a), z + 0.2 + r * math.sin(a))
            q(m, mf, [P(r0, a0, j), P(r1, a0, j + 1), P(r1, a1, j + 1), P(r0, a1, j)], face, None, (0, math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2)))
    for s in (-1, 1):    # wings: layered feather panels sweeping up and back
        for k in range(6):
            span = 6.5 - 0.5 * k; sw = 1.6
            P0 = (d - 1.0 + k * 0.6, c + s * 0.7, z + 0.8); P1 = (d - 1.0 + k * 0.6 + sw, c + s * 0.7, z + 0.8)
            P2 = (d - 1.0 + k * 0.6 + sw + 0.8, c + s * span, z + 3.0 + 0.5 * k); P3_ = (d - 1.0 + k * 0.6 - 0.2, c + s * (span + 0.4), z + 3.2 + 0.5 * k)
            col = wing[k % 4]
            q(m, mf, [P0, P1, P2, P3_], col, None, (0, 0, 1)); q(m, mf, [P1, P0, P3_, P2], col, None, (0, 0, -1))
        for dz, ln in ((0.0, 3.2), (0.4, 2.4)):   # arms
            q(m, mf, [(d - 3.2, c + s * 0.6, z + dz), (d - 3.2 - 0.9, c + s * ln, z + 0.6 + dz), (d - 3.2 - 0.9, c + s * ln, z + 1.0 + dz), (d - 3.2, c + s * 0.6, z + 0.5 + dz)], body, None, (0, 0, 1))


def bench(m, mf, d, c, rot_c=True, L=2.2, z0=0.0):
    bx(m, mf, d - L / 2, d + L / 2, c - 0.25, c + 0.25, z0 + 0.42, z0 + 0.5, hx("#7a5a3a"), top=True)
    bx(m, mf, d - L / 2 + 0.1, d - L / 2 + 0.2, c - 0.2, c + 0.2, z0, z0 + 0.42, hx("#2a2c2f"), top=False)
    bx(m, mf, d + L / 2 - 0.2, d + L / 2 - 0.1, c - 0.2, c + 0.2, z0, z0 + 0.42, hx("#2a2c2f"), top=False)
    bx(m, mf, d - L / 2, d + L / 2, c - 0.27, c - 0.22, z0 + 0.5, z0 + 0.95, hx("#7a5a3a"), top=True)


def xmas_tree(m, mf, d, c, h=13.0, r=3.4):
    """White-silver Christmas tree (stacked cones), with a gold star."""
    n = 6
    for i in range(n):
        z0 = 1.0 + i * (h - 3.0) / n; z1 = z0 + (h - 3.0) / n * 1.9; r0 = r * (1 - i / (n + 0.5)); r1 = r0 * 0.35
        m.cylinder(mf, d, c, r0, z0, z1 if i == n - 1 else z0 + (h - 3.0) / n * 1.4, n=10, col=hx("#e9f1f2") if i % 2 else hx("#d5e3e4"), r1=r1, mod=(4, 4))
    bx(m, mf, d - 0.2, d + 0.2, c - 0.2, c + 0.2, 0, 1.2, hx("#5a4030"), top=False)
    bx(m, mf, d - 0.3, d + 0.3, c - 0.3, c + 0.3, h - 0.6, h + 0.2, hx("#e8c040"), top=True)
