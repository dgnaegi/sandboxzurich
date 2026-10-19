"""Langstrassen-Unterfuehrung (Langstrasse under the SBB track field, Kreis 4 <-> 5): road tunnel (3 lanes) with two narrow pedestrian/bike passages,
approach troughs with retaining walls, portals, deck slab, lamps, graffiti (own designs). Dimensions/photos: research/v3/langstr_unterf.md.
Model z = 0 at the south portal floor; geometry in game axes (x east, y north). Output /models/landmarks/lu_unterfuehrung.glb, entry in overrides/landmarks_lu.json."""
import json, math, sys
import numpy as np
from PIL import Image
from common import *
from lm import *
import lu_geom as G
import lu_tex as T

OX, OY = 913.0, -321.0                       # model origin (landmark anchor, streamed by distance to it)
OZ = G.Z_S                                   # model z origin = floor height at the south portal
NAME, TITLE = "lu_unterfuehrung", "Langstrassen-Unterfuehrung"
L = G.L


def P(s, o, z):
    q = G.xy(s, o)
    return (float(q[0]) - OX, float(q[1]) - OY, float(G.floor_z(s)) - OZ + z)


def ZW(s, o, z_abs):
    q = G.xy(s, o)
    return (float(q[0]) - OX, float(q[1]) - OY, z_abs - OZ)


def light(s):
    """Baked brightness for tunnel interior (daylight fades towards the middle)."""
    d = min(max(s, 0), L - max(s, 0)) if 0 <= s <= L else 0
    if s < 0 or s > L:
        return 1.0
    return 0.78 + 0.22 * math.exp(-d / 9.0)


def quadc(m, mat, p, uv, cols, toward):
    p = np.array(p, float); n = np.cross(p[1] - p[0], p[2] - p[0]); l = np.linalg.norm(n)
    if l < 1e-9:
        return
    n /= l
    if np.dot(n, np.array(toward, float) - p.mean(0)) < 0:
        p = p[::-1]; uv = uv[::-1]; cols = cols[::-1]; n = -n
    mt = mat; b = mt.n
    for i in range(4):
        mt.pos.append(p[i]); mt.nrm.append(n); mt.col.append(cols[i]); mt.uv.append(uv[i])
    mt.idx += [b, b + 1, b + 2, b, b + 2, b + 3]; mt.n += 4


def col(f, tint=(255, 255, 255)):
    f = max(0.0, min(1.4, f))
    return (min(255, int(tint[0] * f)), min(255, int(tint[1] * f)), min(255, int(tint[2] * f)), 255)


class Build:
    def __init__(self):
        self.m = Model(NAME)
        self.mc = self.m.mat("conc", T.conc_tile(), rough=0.95)
        self.ma = self.m.mat("atlas", T.atlas(), rough=0.9)
        sw, em = T.swatches()
        self.mm = self.m.mat("misc", sw, em, rough=0.6)
        self.rng = np.random.default_rng(11)
        self.cols = []  # collider rings

    # ---- generic quad from (s,o,z-relative-to-floor) corner tuples ----------------------------------
    def conc(self, c4, toward, br=(1, 1, 1, 1), tint=(255, 255, 255), mod=3.0):
        """Tiling concrete quad; uv in metres / mod measured along the quad edges."""
        pts = [P(*c) for c in c4]
        e1 = np.linalg.norm(np.array(pts[1]) - np.array(pts[0])); e2 = np.linalg.norm(np.array(pts[3]) - np.array(pts[0]))
        u0 = c4[0][0] / mod if abs(c4[0][0] - c4[1][0]) > 1e-6 else 0.0   # continuous along s
        uv = [(u0, 0), (u0 + e1 / mod, 0), (u0 + e1 / mod, e2 / mod), (u0, e2 / mod)]
        quadc(self.m, self.mc, pts, uv, [col(b, tint) for b in br], toward)

    def at(self, mat, c4, uv, toward, br=(1, 1, 1, 1), tint=(255, 255, 255)):
        quadc(self.m, mat, [P(*c) for c in c4], uv, [col(b, tint) for b in br], toward)

    def box_s(self, s0, s1, o0, o1, z0, z1, mat, cell, br=1.0, toward=None):
        """Axis-aligned (in s,o,z) box with swatch colour `cell` (misc material); all 6 faces, outward normals."""
        u, v = T.uv_swatch(cell)
        c = ((s0 + s1) / 2, (o0 + o1) / 2, (z0 + z1) / 2); ctr = P(*c)
        faces = [[(s0, o0, z0), (s1, o0, z0), (s1, o1, z0), (s0, o1, z0)], [(s0, o0, z1), (s1, o0, z1), (s1, o1, z1), (s0, o1, z1)],
                 [(s0, o0, z0), (s1, o0, z0), (s1, o0, z1), (s0, o0, z1)], [(s0, o1, z0), (s1, o1, z0), (s1, o1, z1), (s0, o1, z1)],
                 [(s0, o0, z0), (s0, o1, z0), (s0, o1, z1), (s0, o0, z1)], [(s1, o0, z0), (s1, o1, z0), (s1, o1, z1), (s1, o0, z1)]]
        for f in faces:
            pts = [P(*q) for q in f]; mid = np.mean(pts, 0)
            out = mid + (mid - np.array(ctr))
            quadc(self.m, mat, pts, [(u, v)] * 4, [col(br)] * 4, out)


def cbox(b, s0, s1, o0, o1, z0, z1, tint=(214, 214, 208), br=0.95, abs_z=False):
    """Concrete box (tiling concrete texture), faces tinted; z relative to the floor at s0 (or absolute game z with abs_z)."""
    f = (lambda s, o, z: ZW(s, o, z)) if abs_z else P
    ctr = np.array(f((s0 + s1) / 2, (o0 + o1) / 2, (z0 + z1) / 2))
    faces = [[(s0, o0, z0), (s1, o0, z0), (s1, o1, z0), (s0, o1, z0)], [(s0, o0, z1), (s1, o0, z1), (s1, o1, z1), (s0, o1, z1)],
             [(s0, o0, z0), (s1, o0, z0), (s1, o0, z1), (s0, o0, z1)], [(s0, o1, z0), (s1, o1, z0), (s1, o1, z1), (s0, o1, z1)],
             [(s0, o0, z0), (s0, o1, z0), (s0, o1, z1), (s0, o0, z1)], [(s1, o0, z0), (s1, o1, z0), (s1, o1, z1), (s1, o0, z1)]]
    for fc in faces:
        pts = [f(*q) for q in fc]; mid = np.mean(pts, 0)
        e1 = np.linalg.norm(np.array(pts[1]) - np.array(pts[0])); e2 = np.linalg.norm(np.array(pts[3]) - np.array(pts[0]))
        quadc(b.m, b.mc, pts, [(0, 0), (e1 / 3, 0), (e1 / 3, e2 / 3), (0, e2 / 3)], [col(br, tint)] * 4, mid + (mid - ctr))


def build():
    b = Build(); m = b.m; mc, ma, mm = b.mc, b.ma, b.mm
    rng = b.rng
    NS = 64; ds = L / NS
    sides = (-1, 1)
    # ---------------------------------------------------------------- tunnel interior
    for k in range(NS):
        s0, s1 = k * ds, (k + 1) * ds
        sm = (s0 + s1) / 2; l0, l1 = light(s0), light(s1); lm_ = (l0 + l1) / 2
        cell, sub = divmod(k, 4)            # 6 m floor cell = 4 sub steps
        vv0, vv1 = sub / 4, (sub + 1) / 4
        inside = (0, 0, 0)
        # road floor
        kind = "arrow" if cell in (3, 9, 13) else "road"
        b.at(ma, [(s0, -5.8, 0.03), (s1, -5.8, 0.03), (s1, 5.8, 0.03), (s0, 5.8, 0.03)], T.uv_floor(kind, cell % 2, 0, 1, vv0, vv1), P(sm, 0, 3),
             br=(l0, l1, l1, l0), tint=(255, 214, 168))
        for sg in sides:   # chamfer (kerb stone / concrete)
            b.conc([(s0, sg * 5.8, 0.0), (s1, sg * 5.8, 0.0), (s1, sg * G.KERB_W, G.KERB_H), (s0, sg * G.KERB_W, G.KERB_H)], P(sm, 0, 3), br=(l0 * 1.0, l1 * 1.0, l1 * 1.0, l0 * 1.0), tint=(225, 225, 220))
            b.conc([(s0, sg * G.KERB_W, G.KERB_H), (s1, sg * G.KERB_W, G.KERB_H), (s1, sg * G.KERB_W, G.CLEAR), (s0, sg * G.KERB_W, G.CLEAR)], P(sm, 0, 3),
                   br=(l0 * 1.12, l1 * 1.12, l1 * 1.12, l0 * 1.12), tint=(238, 230, 208))
        b.conc([(s0, -G.KERB_W, G.CLEAR), (s1, -G.KERB_W, G.CLEAR), (s1, G.KERB_W, G.CLEAR), (s0, G.KERB_W, G.CLEAR)], P(sm, 0, 0.5),
               br=(l0 * .85, l1 * .85, l1 * .85, l0 * .85), tint=(190, 186, 176))
        # passage floors, outer slanted wall (painted), inner wall (painted), ceiling
        for sg in sides:
            row = (k // 4) % 2
            b.at(ma, [(s0, sg * G.PED_IN, 0.03), (s1, sg * G.PED_IN, 0.03), (s1, sg * G.PED_FOOT, 0.03), (s0, sg * G.PED_FOOT, 0.03)],
                 T.uv_floor("ped", row, 0, 1, vv0, vv1), P(sm, sg * 9.5, 3), br=(l0, l1, l1, l0), tint=(255, 214, 168))
            wi = 2 if (k // 8) % 4 == 1 else (0 if (k // 2) % 2 == 0 else 1)      # painted cream variants, niche every 4th 12 m
            hz = (k % 2)
            b.at(ma, [(s0, sg * G.PED_IN, 0), (s1, sg * G.PED_IN, 0), (s1, sg * G.PED_IN, G.PED_H), (s0, sg * G.PED_IN, G.PED_H)],
                 T.uv_wall(wi, hz * 0.5, hz * 0.5 + 0.5, 0, 1), P(sm, sg * 9.5, 1.5), br=(l0, l1, l1, l0))
            b.at(ma, [(s0, sg * G.PED_FOOT, 0), (s1, sg * G.PED_FOOT, 0), (s1, sg * G.PED_OUT, G.PED_H), (s0, sg * G.PED_OUT, G.PED_H)],
                 T.uv_wall(3 if (k // 3) % 3 == 0 else 1, hz * 0.5, hz * 0.5 + 0.5, 0, 1), P(sm, sg * 9.5, 1.5), br=(l0 * .95, l1 * .95, l1 * .95, l0 * .95))
            b.conc([(s0, sg * G.PED_IN, G.PED_H), (s1, sg * G.PED_IN, G.PED_H), (s1, sg * G.PED_OUT, G.PED_H), (s0, sg * G.PED_OUT, G.PED_H)], P(sm, sg * 9.5, 1.0),
                   br=(l0 * .85, l1 * .85, l1 * .85, l0 * .85), tint=(225, 222, 212))
    # colourful wedges on the slanted outer wall (own palette, triangular prisms every 1.17 m, as a gradient along s)
    for sg in sides:
        nw = int(L / 1.17)
        for i in range(nw):
            s = 0.6 + i * 1.17; f = i / (nw - 1); ci = 5 + int(f * 7.99)
            u, v = T.uv_swatch(ci); br = 0.55 + 0.45 * light(s)
            za = G.PED_H - 0.02; w = 0.5; zlow = G.PED_H - 1.35
            po = [P(s, sg * G.PED_OUT, za), P(s + w * .8, sg * G.PED_OUT, za), P(s, sg * (G.PED_OUT - 0.55 * 0.0), zlow + 0.0)]
            # triangle standing on the wall: apex at ceiling line, hanging down along the wall
            wall_pt = lambda z: (G.PED_FOOT + (G.PED_OUT - G.PED_FOOT) * z / G.PED_H)
            A0 = P(s, sg * wall_pt(za), za); A1 = P(s + w, sg * wall_pt(za), za); A2 = P(s, sg * wall_pt(zlow), zlow)
            B0 = P(s, sg * (wall_pt(za) - 0.42), za)           # points towards the walker
            toward = P(s, sg * 9.0, 1.5)
            for tri in ([A0, A1, A2], [A0, B0, A2], [A1, B0, A2], [A0, A1, B0]):
                pa = np.array(tri, float); n = np.cross(pa[1] - pa[0], pa[2] - pa[0]); nl = np.linalg.norm(n)
                if nl < 1e-9: continue
                n /= nl
                if np.dot(n, np.array(toward) - pa.mean(0)) < 0 and tri is not None:
                    pa = pa[[0, 2, 1]]; n = -n
                bb = m.mats["misc"]; k0 = bb.n
                for q in pa:
                    bb.pos.append(q); bb.nrm.append(n); bb.col.append(col(br)); bb.uv.append((u, v))
                bb.idx += [k0, k0 + 1, k0 + 2]; bb.n += 3
    # ---------------------------------------------------------------- lamps (tunnel + passages)
    for i in range(int(L // 3.0)):
        s = 1.8 + i * 3.0
        for o in (-3.0, 3.0):   # road: luminaire rows
            b.box_s(s - 0.7, s + 0.7, o - 0.12, o + 0.12, G.CLEAR - 0.14, G.CLEAR - 0.02, mm, 0, 1.0)
        for sg in sides:   # passages: LED panels
            if i % 1 == 0:
                b.box_s(s - 0.6, s + 0.6, sg * 9.2 - 0.12, sg * 9.2 + 0.12, G.PED_H - 0.08, G.PED_H - 0.01, mm, 0, 1.0)
        # wall-top light strip dashes + cable trays
    for i in range(int(L // 6.0) + 1):
        s = 0.6 + i * 6.0
        for sg in sides:
            b.box_s(s, s + 0.35, sg * (G.KERB_W - 0.14), sg * G.KERB_W, 1.9, 4.2, mm, 1, 0.8)       # dark vertical duct covers on the road walls
        b.box_s(s + 2.9, s + 3.4, -G.KERB_W, G.KERB_W, G.CLEAR - 0.28, G.CLEAR, mm, 3, 0.45)             # transverse ceiling ribs
    # ---------------------------------------------------------------- slab top (ballast colour) + portal fascias
    pts_top = []
    for sa, sb in zip(np.linspace(0, L, 9)[:-1], np.linspace(0, L, 9)[1:]):
        za, zb = float(G.deck_z(sa)) - 0.12, float(G.deck_z(sb)) - 0.12
        c4 = [ZW(sa, -G.HALF, za), ZW(sb, -G.HALF, zb), ZW(sb, G.HALF, zb), ZW(sa, G.HALF, za)]
        quadc(m, mc, c4, [(0, 0), (4, 0), (4, 5), (0, 5)], [col(0.85, (150, 140, 128))] * 4, (c4[0][0], c4[0][1], 99))
    for end in (0, 1):
        s = 0.0 if end == 0 else L
        out = -1 if end == 0 else 1                       # outward along the axis
        top = float(G.deck_z(s)) - 0.12 - float(G.floor_z(s))       # relative to floor at s
        rect = [(-G.HALF - 0.6, -1.0), (G.HALF + 0.6, -1.0), (G.HALF + 0.6, top), (-G.HALF - 0.6, top)]
        from shapely.geometry import Polygon
        R = Polygon(rect)
        road = Polygon([(-5.8, 0), (5.8, 0), (6.7, 1.6), (6.7, 4.6), (-6.7, 4.6), (-6.7, 1.6)])
        pe = Polygon([(7.85, 0), (11.5, 0), (12.6, 3.4), (7.85, 3.4)]); pw = Polygon([(-7.85, 0), (-11.5, 0), (-12.6, 3.4), (-7.85, 3.4)])
        poly = R.difference(road).difference(pe).difference(pw)
        pg = poly if poly.geom_type == "Polygon" else max(poly.geoms, key=lambda g: g.area)
        # rect minus openings is one polygon (openings touch the bottom edge z=-1 only through the region below 0): triangulate in (o,z)
        for geom in (poly.geoms if poly.geom_type != "Polygon" else [poly]):
            for g in shapely.constrained_delaunay_triangles(geom).geoms:
                c = list(g.exterior.coords)[:3]
                if not geom.buffer(1e-6).contains(g.representative_point()): continue
                pts = [P(s, o, z) for o, z in c]
                tw = P(s + out * 5, 0, 2)
                pa = np.array(pts); n = np.cross(pa[1] - pa[0], pa[2] - pa[0])
                if np.dot(n, np.array(tw) - pa.mean(0)) < 0: pts = pts[::-1]; c = c[::-1]
                bb = mc; k0 = bb.n
                nn = np.cross(np.array(pts[1]) - np.array(pts[0]), np.array(pts[2]) - np.array(pts[0])); nn /= np.linalg.norm(nn)
                for q, (o, z) in zip(pts, c):
                    bb.pos.append(q); bb.nrm.append(nn); bb.col.append(col(0.95, (214, 214, 208))); bb.uv.append((o / 3.0, z / 3.0))
                bb.idx += [k0, k0 + 1, k0 + 2]; bb.n += 3
        # frames: slightly proud lintel band + chamfer line over the road opening (reads from afar)
        for sg in sides:
            pass
    # portal: massive concrete plate over the opening (projects 0.9 m, 2.1 m deep with a lower lip), solid parapet + steel railing on top, sign field (photos nord:5, sued:5)
    for end in (0, 1):
        s = 0.0 if end == 0 else L; out = -1 if end == 0 else 1
        ztop = float(G.deck_z(s)) - 0.12; fz = float(G.floor_z(s))
        so = s + out * 0.9; sl = s + out * 0.55
        W = G.HALF + 0.6
        cbox(b, min(s, so), max(s, so), -W, W, ztop - 1.5, ztop, abs_z=True, tint=(222, 220, 212), br=1.0)               # main plate
        cbox(b, min(s, sl), max(s, sl), -W + 0.3, W - 0.3, ztop - 2.1, ztop - 1.5, abs_z=True, tint=(205, 203, 196), br=0.9)   # lower lip / haunch
        so2 = s + out * 0.2                                                                                                  # parapet on the plate (0.25 thick, 0.9 high)
        cbox(b, min(so, so2), max(so, so2), -W, W, ztop, ztop + 0.9, abs_z=True, tint=(214, 212, 204), br=0.95)
        ro = so - out * 0.12
        for k in range(int(2 * W / 2.0) + 1):
            o = min(-W + k * 2.0, W)
            b.box_s(ro - 0.04, ro + 0.04, o - 0.04, o + 0.04, ztop - fz + 0.9, ztop - fz + 1.9, mm, 3, 0.9)
        b.box_s(ro - 0.04, ro + 0.04, -W, W, ztop - fz + 1.8, ztop - fz + 1.88, mm, 3, 0.9)
        b.box_s(ro - 0.04, ro + 0.04, -W, W, ztop - fz + 1.35, ztop - fz + 1.40, mm, 3, 0.9)
        # sign field: dark panel with a pale frame, centred over the road opening on the plate front
        sf = so + out * 0.03
        b.box_s(min(so, sf), max(so, sf), -1.6, 1.6, ztop - fz - 1.2, ztop - fz - 0.55, mm, 4, 0.9)
        sf2 = sf + out * 0.03
        b.box_s(min(sf, sf2), max(sf, sf2), -1.5, 1.5, ztop - fz - 1.15, ztop - fz - 0.6, mm, 1, 0.8)
    # ---------------------------------------------------------------- approach troughs (retaining walls with graffiti, floors)
    gz_top = G.GROUND + 0.12
    for side_end in (0, 1):
        n = int(abs((G.S_MIN if side_end == 0 else G.S_MAX - L)) // 3.0)
        for k in range(n):
            if side_end == 0:
                s0, s1 = -(k + 1) * 3.0, -k * 3.0
            else:
                s0, s1 = L + k * 3.0, L + (k + 1) * 3.0
            h0, h1 = gz_top - float(G.floor_z(s0)), gz_top - float(G.floor_z(s1))
            if min(h0, h1) < 0.05 and max(h0, h1) < 0.05:
                continue
            h0, h1 = max(h0, 0.0), max(h1, 0.0); sm = (s0 + s1) / 2
            for sg in sides:
                # floors: road, kerb strips, passage floor, outer strip
                b.at(ma, [(s0, sg * -5.8, 0.03), (s1, sg * -5.8, 0.03), (s1, sg * 5.8, 0.03), (s0, sg * 5.8, 0.03)], T.uv_floor("road", k % 2, 0, 1, 0.0 + (k % 2) * 0.5, 0.5 + (k % 2) * 0.5), P(sm, 0, 5)) if sg == 1 else None
                b.conc([(s0, sg * 5.8, 0.02), (s1, sg * 5.8, 0.02), (s1, sg * G.KERB_W, 0.02), (s0, sg * G.KERB_W, 0.02)], P(sm, 0, 5), tint=(190, 190, 186))
                b.at(ma, [(s0, sg * G.PED_IN, 0.03), (s1, sg * G.PED_IN, 0.03), (s1, sg * G.PED_FOOT, 0.03), (s0, sg * G.PED_FOOT, 0.03)], T.uv_floor("ped", k % 2, 0, 1, 0.0, 0.5), P(sm, 0, 5))
                b.conc([(s0, sg * G.PED_FOOT, 0.02), (s1, sg * G.PED_FOOT, 0.02), (s1, sg * G.PED_OUT, 0.02), (s0, sg * G.PED_OUT, 0.02)], P(sm, 0, 5), tint=(190, 190, 186))
                # walls: divider (6.7 .. 7.85), outer (12.6 .. 13.2): vertical faces + cap
                # divider wall faces
                for o, tw in ((G.KERB_W, 0.0), (G.PED_IN, 9.5)):
                    b.wallq(s0, s1, sg * o, h0, h1, sg * tw, tint=(205, 205, 200), seed=k + (7 if o > 7 else 0))
                b.capq(s0, s1, sg * G.KERB_W, sg * G.PED_IN, h0, h1)
                # outer wall: inner face (toward centre) + outside face
                b.wallq(s0, s1, sg * G.PED_OUT, h0, h1, sg * 9.5, tint=(205, 205, 200), seed=k + 3)
                b.wallq(s0, s1, sg * (G.PED_OUT + 0.6), h0, h1, sg * 40.0, tint=(170, 170, 166), seed=k + 5)
                b.capq(s0, s1, sg * G.PED_OUT, sg * (G.PED_OUT + 0.6), h0, h1)
    # graffiti panels (own pieces) on trough walls and passage walls: (s, side, wall, atlas cell); wall = o of the face, facing 'to' (o)
    gl = [(-30, 1, 12.6, 4), (-52, -1, 12.6, 5), (-18, -1, 6.7, 6), (-44, 1, 6.7, 7), (L + 24, 1, 12.6, 7), (L + 46, -1, 12.6, 4), (L + 14, 1, 6.7, 5),
          (22, 1, 7.85, 5), (41, -1, 7.85, 6), (66, 1, 7.85, 7), (78, -1, 7.85, 4), (14, -1, 7.85, 7)]
    for s, sg, o, cell in gl:
        outside = s < 0 or s > L
        h = float(G.GROUND + 0.12 - G.floor_z(s)) if outside else G.PED_H
        zb, zt = 0.4, 2.0
        if zt + 0.3 > h: continue
        op = o + (0.02 if o == G.PED_IN else -0.02)           # panel plane just in front of the wall face
        to = 9.5 if o in (G.PED_IN, G.PED_OUT) else 0.0       # direction the face looks
        b.at(ma, [(s - 1.5, sg * op, zb), (s + 1.5, sg * op, zb), (s + 1.5, sg * op, zt), (s - 1.5, sg * op, zt)], T.uv_wall(cell, 0, 1, 0.12, 0.12 + (zt - zb) / 3.0),
             P(s, sg * to, 1.5), br=tuple([0.9 if not outside else 1.0] * 4))
    # colliders: wall rings (world coords), chunked 20 m
    for sg in sides:
        for (oa, ob, s_a, s_b) in ((G.KERB_W, G.PED_IN, -63.0, L + 63.0), (G.PED_OUT, G.PED_OUT + 0.6, -68.0, L + 68.0)):
            s = s_a
            while s < s_b - 0.01:
                e = min(s + 20.0, s_b)
                ring = [G.xy(s, sg * oa), G.xy(e, sg * oa), G.xy(e, sg * ob), G.xy(s, sg * ob)]
                b.cols.append([[round(float(p[0]), 2), round(float(p[1]), 2)] for p in ring]); s = e
    return b


def _wallq(self, s0, s1, o, h0, h1, tw, tint, seed):
    """Vertical concrete wall face at offset o from floor to heights h0,h1 (relative to floor at s0/s1), facing toward offset tw (stacked in <=3 m slices)."""
    if max(h0, h1) < 0.05: return
    nsl = int(math.ceil(max(h0, h1) / 3.0))
    sm = (s0 + s1) / 2
    for j in range(nsl):
        za = 3.0 * j; zb0 = min(h0, 3.0 * (j + 1)); zb1 = min(h1, 3.0 * (j + 1))
        if zb0 <= za and zb1 <= za: continue
        zb0 = max(zb0, za); zb1 = max(zb1, za)
        uv = [(0, 0), (3 / 3.0, 0), (3 / 3.0, (zb1 - za) / 3.0), (0, (zb0 - za) / 3.0)]
        br = 0.75 + 0.2 * ((seed + j) % 3) / 2
        quadc(self.m, self.mc, [P(s0, o, za), P(s1, o, za), P(s1, o, zb1), P(s0, o, zb0)], uv, [col(br, tint)] * 4, P(sm, tw, 1.5))


def _capq(self, s0, s1, oa, ob, h0, h1):
    if max(h0, h1) < 0.05: return
    quadc(self.m, self.mc, [P(s0, oa, h0), P(s1, oa, h1), P(s1, ob, h1), P(s0, ob, h0)], [(0, 0), (1, 0), (1, 1), (0, 1)], [col(0.9, (190, 190, 186))] * 4,
          P((s0 + s1) / 2, (oa + ob) / 2, 30))


Build.wallq = _wallq; Build.capq = _capq


def main():
    b = build()
    from common import finish as _f
    out = OUTDIR; out.mkdir(parents=True, exist_ok=True); RAWDIR.mkdir(parents=True, exist_ok=True)
    raw = RAWDIR / f"{NAME}.glb"; b.m.write(str(raw))
    import subprocess
    dst = out / f"{NAME}.glb"
    r = subprocess.run([str(ROOT / "web/node_modules/.bin/gltfpack"), "-i", str(raw), "-o", str(dst), "-cc", "-kn"], capture_output=True, text=True)
    if r.returncode: print(r.stderr[-300:])
    print(f"{NAME}: {b.m.tri_count()} tris, " + ", ".join(f"{k}={mt.tris()}" for k, mt in b.m.mats.items()) + f", glb {dst.stat().st_size // 1024} kB, colliders {len(b.cols)}")
    update_entry(b.cols)


def update_entry(cols):
    F = ROOT / "pipeline" / "overrides" / "landmarks_lu.json"
    d = json.load(open(F)) if F.exists() else {"landmarks": []}
    old = next((e for e in d["landmarks"] if e["name"] == TITLE), {})
    e = {"name": TITLE, "model": f"/models/landmarks/{NAME}.glb", "x": OX, "y": OY, "z": round(OZ, 2), "heading": 0, "hide": old.get("hide", []), "walkable": True, "colliders": cols}
    d["landmarks"] = [x for x in d["landmarks"] if x["name"] != TITLE] + [e]
    json.dump(d, open(F, "w"), separators=(",", ":"))
    import merge; merge.main()


if __name__ == "__main__":
    main()
