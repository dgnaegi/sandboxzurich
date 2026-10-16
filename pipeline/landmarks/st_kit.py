"""Station furniture kit (Swiss platform look WITHOUT SBB logo / SBB station clock): signs atlas, benches, bins, departure boards,
neutral clock, sector signs, ticket machine, lamp posts, canopies, stair flights, stair openings, lift towers, bike racks.
All positions are world-local metres (x east, y north, z up); orientation helper `Fr(u, n)` = frame of a platform."""
import math
import numpy as np
from PIL import Image, ImageDraw
import k93_lib as L, k93_kit as K
from k93_lib import hexc, shade

W4 = (255, 255, 255, 255)
STEEL, DKST, CONC, WOOD = hexc("#7d8387"), hexc("#3d4348"), hexc("#a9a8a2"), hexc("#8a6a48")


def _pan(d, w, h, bg, ink, rows, font="Barlow-Bold"):
    d.rectangle([0, 0, w - 1, h - 1], fill=bg)
    n = len(rows); fh = int(h / n * 0.74)
    f = K.font(font, fh)
    for i, (txt, col, x) in enumerate(rows):
        d.text((x, i * h / n + h / n * 0.08), txt, font=f, fill=col)


def make_atlas(perron_refs, station_name):
    """1024x512 atlas, cells 256x128: per-perron number signs (0..), then board, sectors, clock+ticket."""
    A = Image.new("RGB", (1024, 512), (30, 32, 36)); E = Image.new("RGB", (1024, 512), (0, 0, 0)); uv = {}
    da, de = ImageDraw.Draw(A), ImageDraw.Draw(E)
    def cell(i): return (i % 4) * 256, (i // 4) * 128
    for i, ref in enumerate(perron_refs):
        x, y = cell(i)
        for d, em in ((da, False), (de, True)):
            d.rectangle([x, y, x + 255, y + 127], fill=(26, 50, 104) if not em else (0, 0, 0))
            d.rectangle([x + 4, y + 4, x + 251, y + 123], outline=(240, 240, 238) if not em else (70, 70, 70), width=3)
            d.text((x + 12, y + 8), "Gleis", font=K.font("Barlow-Bold", 22), fill=(235, 235, 235) if not em else (60, 60, 60))
            fbig = K.font("Barlow-Bold", 104 if len(ref) < 3 else 76); w = fbig.getlength(ref)
            d.text((x + (256 - w) / 2, y + 2), ref, font=fbig, fill=(255, 255, 255) if not em else (90, 90, 90))
        uv[f"sign{i}"] = (x / 1024, y / 512, (x + 256) / 1024, (y + 128) / 512)
    bx, by = cell(len(perron_refs))   # departure board
    rows = [("S9  Uster", 0), ("S3  Pfäffikon SZ", 0), ("S8  Pfäffikon SZ", 0), ("IR  Chur", 0)]
    for d, em in ((da, False), (de, True)):
        d.rectangle([bx, by, bx + 255, by + 127], fill=(10, 11, 13))
        f = K.font("Barlow-Bold", 27)
        for i, (t, _) in enumerate(rows):
            col = (255, 168, 28) if em else (230, 150, 30)
            d.text((bx + 8, by + 6 + i * 30), t, font=f, fill=col)
            d.text((bx + 200, by + 6 + i * 30), ("%02d" % (4 + i * 7)), font=f, fill=col)
    uv["board"] = (bx / 1024, by / 512, (bx + 256) / 1024, (by + 128) / 512)
    sx, sy = cell(len(perron_refs) + 1)   # sector letters A-F (6 x 42 px)
    for d, em in ((da, False), (de, True)):
        d.rectangle([sx, sy, sx + 255, sy + 127], fill=(26, 50, 104) if not em else (0, 0, 0))
        f = K.font("Barlow-Bold", 96)
        for k, ch in enumerate("ABCDEF"):
            d.text((sx + k * 42 + (42 - f.getlength(ch) * 0.42) / 2 - 2, sy + 4), ch, font=K.font("Barlow-Bold", 62), fill=(255, 255, 255) if not em else (80, 80, 80))
    for k in range(6): uv["sec" + "ABCDEF"[k]] = ((sx + k * 42) / 1024, sy / 512, (sx + (k + 1) * 42) / 1024, (sy + 64) / 512)
    cx, cy = cell(len(perron_refs) + 2)   # neutral clock (white face, black ticks and hands, no red) + ticket machine front
    for d, em in ((da, False), (de, True)):
        d.rectangle([cx, cy, cx + 255, cy + 127], fill=(60, 64, 70) if not em else (0, 0, 0))
        r = 58; mx, my = cx + 64, cy + 64
        d.ellipse([mx - r, my - r, mx + r, my + r], fill=(244, 244, 240) if not em else (60, 60, 56), outline=(20, 20, 20), width=4)
        for k in range(60):
            a = math.radians(k * 6 - 90); l0 = r - (12 if k % 5 == 0 else 6)
            d.line([mx + l0 * math.cos(a), my + l0 * math.sin(a), mx + (r - 3) * math.cos(a), my + (r - 3) * math.sin(a)], fill=(15, 15, 15) if not em else (0, 0, 0), width=3 if k % 5 == 0 else 1)
        d.line([mx, my, mx + 44 * math.cos(math.radians(-60)), my + 44 * math.sin(math.radians(-60))], fill=(15, 15, 15) if not em else (0, 0, 0), width=4)
        d.line([mx, my, mx + 30 * math.cos(math.radians(-150)), my + 30 * math.sin(math.radians(-150))], fill=(15, 15, 15) if not em else (0, 0, 0), width=6)
        tx = cx + 140   # ticket machine front: blue screen + keypad strip
        d.rectangle([tx, cy + 4, tx + 112, cy + 123], fill=(88, 94, 100) if not em else (0, 0, 0))
        d.rectangle([tx + 10, cy + 12, tx + 102, cy + 66], fill=(32, 78, 140) if not em else (40, 90, 150))
        d.rectangle([tx + 14, cy + 72, tx + 98, cy + 84], fill=(30, 30, 32) if not em else (0, 0, 0))
        d.rectangle([tx + 14, cy + 92, tx + 56, cy + 112], fill=(200, 200, 198) if not em else (0, 0, 0))
    uv["clock"] = (cx / 1024, cy / 512, (cx + 128) / 1024, (cy + 128) / 512)
    uv["ticket"] = ((cx + 140) / 1024, cy / 512, (cx + 252) / 1024, (cy + 128) / 512)
    nm = len(perron_refs) + 3; nx, ny = cell(nm)   # station name plate (white on dark grey-blue)
    for d, em in ((da, False), (de, True)):
        d.rectangle([nx, ny, nx + 255, ny + 127], fill=(26, 50, 104) if not em else (0, 0, 0))
        f = K.font("Barlow-Bold", 40); w = f.getlength(station_name)
        s = min(1.0, 232 / w); f = K.font("Barlow-Bold", int(40 * s)); w = f.getlength(station_name)
        d.text((nx + (256 - w) / 2, ny + 38), station_name, font=f, fill=(255, 255, 255) if not em else (80, 80, 80))
    uv["name"] = (nx / 1024, ny / 512, (nx + 256) / 1024, (ny + 128) / 512)
    return A, E, uv


class Kit:
    def __init__(self, M, atlas_img, emis_img, uv, conc=None):
        self.M, self.uv = M, uv
        self.CT = M.mat('concrete', rough=0.9, tex=K.concrete_tex(conc, 256, panel=(1.0, 0.25), board=True), repeat=True) if conc else None
        self.S = M.mat("solid", rough=0.85)
        self.T = M.mat("signs", rough=0.5, tex=atlas_img, emis=emis_img, repeat=False)
        self.LM = K.lamp_mat(M, "stlamps", col="#fff4d6")
        self.GL = M.mat("stglass", rough=0.25, tex=_glass_tex(), repeat=True, double=True)

    def fq(self, mat, pts, col, out, uv=None):
        """Quad p0..p3 (3D) oriented so its normal faces `out` (vector)."""
        p = np.array(pts, float); n = np.cross(p[1] - p[0], p[3] - p[0])
        if np.linalg.norm(n) < 1e-9: n = np.cross(p[2] - p[0], p[3] - p[0])
        self.M.quad(mat, *[tuple(q) for q in p], col, uv, flip=bool(np.dot(n, out) < 0))

    # ---- tiny helpers -------------------------------------------------------------------------------------------
    def vq(self, mat, a, b, z0, z1, uv=None, col=W4):
        """vertical quad a->b (xy) with atlas uv=(u0,v0,u1,v1) (v0 top)."""
        if uv is None: K.quad_tex(self.M, mat, a, b, z0, z1, col=col)
        else: K.quad_tex(self.M, mat, a, b, z0, z1, uv, col)

    def two_sided(self, key, c, ang, w, z0, z1, off=0.03):
        """Atlas plate centred at c=(x,y), plate plane along direction ang, visible from both sides."""
        ux, uy = math.cos(ang), math.sin(ang); nx, ny = uy, -ux
        for s in (1, -1):
            cx, cy = c[0] + nx * off * s, c[1] + ny * off * s
            a = (cx - ux * w / 2 * s, cy - uy * w / 2 * s); b = (cx + ux * w / 2 * s, cy + uy * w / 2 * s)
            self.vq(self.T, a, b, z0, z1, self.uv[key])

    def column(self, c, z0, z1, w, rot, col=None):
        if self.CT is not None: K.box_tex(self.M, self.CT, (c[0], c[1], (z0 + z1) / 2), (w, w, z1 - z0), rot=rot, col=W4, tile=(1.2, 1.2))
        else: self.M.box(self.S, (c[0], c[1], (z0 + z1) / 2), (w, w, z1 - z0), col or hexc('#8f969b'), rot=rot)

    def post(self, c, z0, z1, r=0.045, col=DKST):
        self.M.box(self.S, (c[0], c[1], (z0 + z1) / 2), (r * 2, r * 2, z1 - z0), col)

    # ---- furniture ----------------------------------------------------------------------------------------------
    def bench(self, c, ang, z, long=1.9):
        M = self.M
        M.box(self.S, (c[0], c[1], z + 0.43), (long, 0.46, 0.06), WOOD, rot=ang, top=shade(WOOD, 1.1))
        for s in (-1, 1):
            q = (c[0] + math.cos(ang) * s * (long / 2 - 0.15), c[1] + math.sin(ang) * s * (long / 2 - 0.15))
            M.box(self.S, (q[0], q[1], z + 0.2), (0.07, 0.4, 0.4), DKST, rot=ang)

    def bin(self, c, z):
        self.M.cyl(self.S, (c[0], c[1]), 0.21, z, z + 0.82, hexc("#4d5f55"), n=10, cap=True)
        self.M.cyl(self.S, (c[0], c[1]), 0.22, z + 0.8, z + 0.88, hexc("#2e3430"), n=10, cap=True)

    def board_pylon(self, c, ang, z, clock=True):
        """Mast with two-sided departure board facing along the platform (readable while walking) and a neutral clock across."""
        M = self.M; pa = ang + math.pi / 2
        self.post(c, z - 0.05, z + 3.45, 0.06, STEEL)
        M.box(self.S, (c[0], c[1], z + 2.75), (0.12, 1.54, 0.6), DKST, rot=ang)
        self.two_sided("board", c, pa, 1.5, z + 2.45, z + 3.05, 0.075)
        if clock:
            M.box(self.S, (c[0], c[1], z + 3.43), (0.64, 0.14, 0.64), DKST, rot=ang)
            self.two_sided("clock", c, ang, 0.58, z + 3.14, z + 3.72, 0.09)

    def sector_sign(self, c, ang, z, letter):
        self.post(c, z, z + 2.6, 0.04, STEEL)
        self.M.box(self.S, (c[0], c[1], z + 2.35), (0.06, 0.36, 0.5), DKST, rot=ang + math.pi / 2)
        self.two_sided("sec" + letter, c, ang + math.pi / 2, 0.30, z + 2.12, z + 2.58, 0.05)

    def perron_sign(self, c, ang, z, i, hang=None, rods=False):
        """Number plate 1.5 x 0.75 on two posts (or hung at height `hang`)."""
        zt = z + 2.55 if hang is None else hang
        ux, uy = math.cos(ang), math.sin(ang)
        if hang is None:
            for s in (-1, 1): self.post((c[0] + ux * s * 0.7, c[1] + uy * s * 0.7), z, zt + 0.2, 0.035, STEEL)
        if rods:
            for sx in (-0.6, 0.6): self.post((c[0] + ux * sx, c[1] + uy * sx), zt + 0.7, zt + 1.05, 0.015, STEEL)
        self.M.box(self.S, (c[0], c[1], zt + 0.37), (1.56, 0.07, 0.8), DKST, rot=ang)
        self.two_sided(f"sign{i}", c, ang, 1.5, zt, zt + 0.75, 0.045)

    def ticket_machine(self, c, ang, z):
        M = self.M
        M.box(self.S, (c[0], c[1], z + 0.95), (0.8, 0.5, 1.9), hexc("#58606a"), rot=ang, top=hexc("#3a4046"))
        ux, uy = math.cos(ang), math.sin(ang); nx, ny = uy, -ux
        for s in (1, -1):
            cc = (c[0] + nx * 0.26 * s, c[1] + ny * 0.26 * s)
            a = (cc[0] - ux * 0.35 * s, cc[1] - uy * 0.35 * s); b = (cc[0] + ux * 0.35 * s, cc[1] + uy * 0.35 * s)
            self.vq(self.T, a, b, z + 0.6, z + 1.8, self.uv["ticket"])

    def lamp_post(self, c, z, h=5.2):
        M = self.M
        self.post(c, z - 0.05, z + h, 0.07, STEEL)
        M.box(self.LM, (c[0], c[1], z + h + 0.05), (0.9, 0.3, 0.1), W4)

    def name_plate(self, c, ang, z, hang=3.0):
        self.M.box(self.S, (c[0], c[1], z + hang + 0.25), (2.4, 0.07, 0.62), DKST, rot=ang)
        self.two_sided("name", c, ang, 2.3, z + hang, z + hang + 0.5, 0.045)

    def bike_rack(self, c, ang, z, n=8, pitch=0.7):
        M = self.M; ux, uy = math.cos(ang), math.sin(ang)
        for k in range(n):
            q = (c[0] + ux * (k - n / 2) * pitch, c[1] + uy * (k - n / 2) * pitch)
            K.tube(M, self.S, (q[0], q[1], z), (q[0], q[1], z + 0.8), 0.018, STEEL, 4)
            K.tube(M, self.S, (q[0] + math.cos(ang + math.pi / 2) * 0.35, q[1] + math.sin(ang + math.pi / 2) * 0.35, z), (q[0] + math.cos(ang + math.pi / 2) * 0.35, q[1] + math.sin(ang + math.pi / 2) * 0.35, z + 0.8), 0.018, STEEL, 4)
            K.tube(M, self.S, (q[0], q[1], z + 0.8), (q[0] + math.cos(ang + math.pi / 2) * 0.35, q[1] + math.sin(ang + math.pi / 2) * 0.35, z + 0.8), 0.018, STEEL, 4)

    def waiting_room(self, c, ang, z, w=4.2, d=2.4, h=2.6):
        """Glass waiting shelter with roof and bench inside."""
        M = self.M; ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy, ux
        P = lambda a, b: (c[0] + ux * a + nx * b, c[1] + uy * a + ny * b)
        for a, b in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
            self.post(P(a, b), z, z + h, 0.05, DKST)
        M.box(self.S, (c[0], c[1], z + h + 0.06), (w + 0.3, d + 0.3, 0.12), hexc("#cfd3d6"), rot=ang)
        for (a0, b0), (a1, b1) in (((-w / 2, -d / 2), (w / 2, -d / 2)), ((w / 2, -d / 2), (w / 2, d / 2)), ((w / 2, d / 2), (-w / 2, d / 2)), ((-w / 2, d / 2), (-w / 2, -d / 2))):
            if (a0, b0) == (w / 2, d / 2) and False: continue
            self.vq(self.GL, P(a0, b0), P(a1, b1), z + 0.12, z + h)
            self.vq(self.GL, P(a1, b1), P(a0, b0), z + 0.12, z + h)
        self.bench(P(0, d / 2 - 0.4), ang, z, long=w - 0.8)
        M.box(self.LM, (c[0], c[1], z + h - 0.02), (w * 0.6, 0.2, 0.04), W4, rot=ang)

    def lift(self, c, ang, z, top, w=2.0):
        """Glass lift tower from platform z up to `top`."""
        M = self.M; ux, uy = math.cos(ang), math.sin(ang); nx, ny = -uy, ux
        P = lambda a, b: (c[0] + ux * a + nx * b, c[1] + uy * a + ny * b)
        h = w / 2
        for a, b in ((-h, -h), (h, -h), (h, h), (-h, h)): self.post(P(a, b), z - 0.05, top, 0.07, hexc("#8b9296"))
        cr = [(-h, -h), (h, -h), (h, h), (-h, h)]
        for i in range(4):
            a0, b0 = cr[i]; a1, b1 = cr[(i + 1) % 4]
            if i == 0:   # door side: opaque lower part (steel door) + glass above
                self.vq(self.S, P(a0, b0), P(a1, b1), z, z + 2.1, None, hexc("#a8afb4"))
                self.vq(self.GL, P(a0, b0), P(a1, b1), z + 2.1, top - 0.2)
                continue
            self.vq(self.GL, P(a0, b0), P(a1, b1), z + 0.1, top - 0.2); self.vq(self.GL, P(a1, b1), P(a0, b0), z + 0.1, top - 0.2)
        M.box(self.S, (c[0], c[1], top - 0.1), (w + 0.2, w + 0.2, 0.2), hexc("#6d7479"), rot=ang)
        M.box(self.S, (c[0], c[1], z + 0.05), (w + 0.1, w + 0.1, 0.1), hexc("#6d7479"), rot=ang)

    def stair_flight(self, p0, p1, z0, z1, width=2.4, base_down=0.9):
        """Real stair run rising from p0 (z0) to p1 (z1): treads, risers, concrete stringers, handrails."""
        M = self.M; p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; Ln = float(np.hypot(*d))
        if Ln < 1: return
        u = d / Ln; n = np.array([-u[1], u[0]]); ns = max(3, int(round((z1 - z0) / 0.17))); rise = (z1 - z0) / ns; run = Ln / ns
        TR, RI = hexc("#a9aaa6"), hexc("#8d8e8a")
        UP = (0, 0, 1.0)
        for k in range(ns):
            a = p0 + u * run * k; b = p0 + u * run * (k + 1); zt = z0 + rise * (k + 1)
            pa, pb = a + n * width / 2, a - n * width / 2; qa, qb = b + n * width / 2, b - n * width / 2
            self.fq(self.S, [(*pa, zt), (*pb, zt), (*qb, zt), (*qa, zt)], TR, UP)
            self.fq(self.S, [(*pa, zt - rise), (*pb, zt - rise), (*pb, zt), (*pa, zt)], RI, (-u[0], -u[1], 0))
        for s in (-1, 1):   # stringer walls (solid concrete, top follows the stair, bottom slopes below)
            a = p0 + n * s * (width / 2 + 0.12); b = p1 + n * s * (width / 2 + 0.12)
            a2 = p0 + n * s * (width / 2); b2 = p1 + n * s * (width / 2); o = (n[0] * s, n[1] * s, 0)
            self.fq(self.S, [(*a, z0 - base_down), (*b, z1 - base_down), (*b, z1 + 0.1), (*a, z0 + 0.1)], CONC, o)
            self.fq(self.S, [(*a2, z0 - base_down), (*b2, z1 - base_down), (*b2, z1 + 0.1), (*a2, z0 + 0.1)], shade(CONC, .85), (-o[0], -o[1], 0))
            self.fq(self.S, [(*a, z0 + 0.1), (*b, z1 + 0.1), (*b2, z1 + 0.1), (*a2, z0 + 0.1)], shade(CONC, 1.05), UP)
            K.tube(M, self.S, (*a2, z0 + 1.0), (*b2, z1 + 1.0), 0.03, getattr(self, 'rail_col', STEEL), 5)
            for k in range(0, ns + 1, 4):
                q = p0 + u * run * k + n * s * width / 2
                K.tube(M, self.S, (*q, z0 + rise * k), (*q, z0 + rise * k + 1.0), 0.018, STEEL, 4)
        bot = [p0 + n * width / 2, p0 - n * width / 2, p1 - n * width / 2, p1 + n * width / 2]
        self.fq(self.S, [(*bot[0], z0 - base_down), (*bot[1], z0 - base_down), (*bot[2], z1 - base_down), (*bot[3], z1 - base_down)], shade(CONC, .6), (0, 0, -1))

    def stair_opening(self, p_top, direction, z, width=2.6, length=3.4):
        """Down stair at a platform: dark well with stepped strips, railings both sides and a gate rail at the top end.
        direction = unit xy pointing from the platform surface INTO the well (descending)."""
        M = self.M; u = np.array(direction, float); u /= np.hypot(*u); n = np.array([-u[1], u[0]]); p = np.array(p_top, float)
        zt = z + 0.025
        for k in range(7):   # alternating dark strips, getting darker (steps seen from above)
            a = p + u * length * k / 7; b = p + u * length * (k + 1) / 7; col = shade(hexc("#4a4d50"), 1.0 - 0.09 * k)
            self.fq(self.S, [(*(a + n * width / 2), zt), (*(a - n * width / 2), zt), (*(b - n * width / 2), zt), (*(b + n * width / 2), zt)], col, (0, 0, 1.0))
        for s in (-1, 1):
            a = p + n * s * (width / 2 + 0.06); b = a + u * length
            K.tube(M, self.S, (*a, z + 1.0), (*b, z + 1.0), 0.025, STEEL, 5)
            for t in np.linspace(0, 1, 4):
                q = a + (b - a) * t; K.tube(M, self.S, (*q, z), (*q, z + 1.0), 0.02, STEEL, 4)
            M.box(self.S, ((a + b)[0] / 2, (a + b)[1] / 2, z + 0.05), (length, 0.14, 0.1), hexc("#d8c13a"), rot=math.atan2(u[1], u[0]))
        e = p + u * length
        M.box(self.S, (e[0], e[1], z + 0.04), (0.14, width + 0.3, 0.08), hexc("#d8c13a"), rot=math.atan2(u[1], u[0]))

    def canopy(self, poly, z, th=0.32, col=None, under=hexc("#cdd1d3"), under_tex=False):
        """Flat canopy roof: slab + fascia + underside."""
        M = self.M; col = col or hexc("#9aa1a6")
        pts = list(poly.exterior.coords)[:-1]
        if L.signed_area(pts) < 0: pts = pts[::-1]    # CCW
        M.cap(self.S, pts, z + th, col)
        if under_tex and self.CT is not None: M.cap(self.CT, pts, z, W4, flip=True)
        else: M.cap(self.S, pts, z, under, flip=True)
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 0.1: continue
            M.quad(self.S, (a[0], a[1], z), (b[0], b[1], z), (b[0], b[1], z + th), (a[0], a[1], z + th), hexc("#e8eaeb"))


def _glass_tex():
    im = Image.new("RGB", (64, 64), (118, 150, 160)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 63, 63], outline=(60, 70, 76), width=3)
    for k in range(8): d.line([0, 8 * k + 20, 63, 8 * k - 12], fill=(150, 180, 190), width=1)
    return im
