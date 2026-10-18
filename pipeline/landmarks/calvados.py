"""Le Calvados (Idaplatz 4, Kreis 3): Jugendstil-Eckhaus, Eckbar mit roter Leuchtroehre und Leuchtschrift 'Le Calvados', weisse Sonnenschirme.
Photo basis: research/calvados.md (Mapillary CC BY-SA 4.0 crops, only read for colours/shapes). Name in free font, no logo."""
import math
import k4w4_kit as _k4
from k4w4_kit import *   # noqa
OVR = ROOT / "pipeline" / "overrides" / "landmarks_calvados.json"
PFX = "ID_7AA763E5"
CORNER = (-166.0, -1105.9)          # N vertex of the footprint = recessed corner entrance (world, local metres)
SHORT = ((-166.0, -1105.9), (-161.3, -1106.0))
EGH = 4.2
signs = [
    dict(text="Le Calvados", fg="#ff4a3c", bg="#2a1c1c", glow="#ff3a2c", w=3.7, h=0.85, z=4.3, size=52, px=512, font="DMSerifDisplay-Regular"),
    dict(text="\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014\u2014", fg="#ff4040", bg="#5a1212", glow="#ff2a2a", px=160, w=0.05, h=0.05, pref="corner"),
    dict(text="MMMMMM", fg="#ffd090", bg="#e0a458", glow="#ffb860", px=160, w=0.05, h=0.05, pref="corner"),
    dict(text=" ", fg="#2e3b46", bg="#34414d", px=96, w=0.05, h=0.05, pref="corner"),
    dict(text="MMMM", fg="#f6d79a", bg="#f2c47c", glow="#ffc070", px=96, w=0.05, h=0.05, pref="corner"),
]
_orig = _k4.pick_edge


def _pick(S, pref, minlen=6.0):
    """Sign 0 goes on the short corner edge (world SHORT), found by nearest edge midpoint."""
    if pref == "corner":
        best = None
        for gp in polys_of(S):
            for a, b in edges_of(orient(gp, 1.0), 3.0):
                d = math.hypot((a[0] + b[0]) / 2 - _pick.cm[0], (a[1] + b[1]) / 2 - _pick.cm[1])
                if best is None or d < best[0]:
                    L, t, n = D.frame_of(a, b); best = (d, a, b, L, t, n)
        return best[1:]
    return _orig(S, pref, minlen)


IRON = "#25262a"; SLATE = "#43444c"; CREAM = "#d9d2bf"


def _balcony(m, mf, a, t, n, uc, z, w=1.8, proj=0.8):
    """Slab + iron railing (top rail, base rail, bars) on the wall frame (a,t,n) at u=uc."""
    ang = math.atan2(t[1], t[0])
    def P(u, o): return (a[0] + t[0] * u + n[0] * o, a[1] + t[1] * u + n[1] * o)
    cx, cy = P(uc, proj / 2 + 0.05)
    rot_box(m, mf, cx, cy, w, proj, z - 0.14, z, ang, hexl("#b8b1a0"))
    for sgn in (-1, 1):                                   # side rails
        sx, sy = P(uc + sgn * (w / 2 - 0.03), proj / 2 + 0.05); rot_box(m, mf, sx, sy, 0.05, proj, z + 0.85, z + 0.92, ang + math.pi / 2 * 0, hexl(IRON))
    fx, fy = P(uc, proj + 0.03)
    rot_box(m, mf, fx, fy, w, 0.05, z + 0.9, z + 0.97, ang, hexl(IRON)); rot_box(m, mf, fx, fy, w, 0.05, z, z + 0.12, ang, hexl(IRON))
    for k in range(6):
        bx, by = P(uc - w / 2 + 0.12 + k * (w - 0.24) / 5, proj + 0.03); rot_box(m, mf, bx, by, 0.035, 0.035, z, z + 0.95, ang, hexl(IRON))


def _chair_table(m, mf, x, y, ang):
    cone8(m, mf, x, y, 0.42, 0.42, 0.72, 0.76, hexl("#2a2a2a"), n=8); m.box(mf, x, y, 0.07, 0.07, 0.0, 0.72, col=hexl("#2a2a2a"))
    for sgn in (-1, 1):
        cxx, cyy = x + math.cos(ang + math.pi / 2) * 0.75 * sgn, y + math.sin(ang + math.pi / 2) * 0.75 * sgn
        rot_box(m, mf, cxx, cyy, 0.42, 0.42, 0.0, 0.46, ang, hexl("#3a3228"))


def extra(m, ctx):
    mf, mg, ox, oy = ctx["mf"], ctx["mg"], ctx["ox"], ctx["oy"]
    P = orient(ctx["localize"](ctx["P"]), 1.0)
    cx, cy = CORNER[0] - ox, CORNER[1] - oy
    R = lambda i: (signs[i]["x0"], signs[i]["x1"])
    FL0 = EGH; FH = (21.2 - EGH) / 5; ztop = 21.2
    dmin = lambda p: math.hypot(p[0] - cx, p[1] - cy)
    for gp in polys_of(P):
        for a, b in edges_of(orient(gp, 1.0), 3.0):
            L, t, n = D.frame_of(a, b)
            if max(dmin(a), dmin(b)) > 16 or min(dmin(a), dmin(b)) > 1.0: continue
            da, db = dmin(a), dmin(b)
            u0, u1 = 0.0, L
            if da > 1.0: u0 = max(0.0, L - 20.0)
            if db > 1.0: u1 = min(L, 20.0)
            w = u1 - u0
            if w < 1: continue
            mid = (a[0] + t[0] * (u0 + w / 2), a[1] + t[1] * (u0 + w / 2))
            strip_quad(m, mg, mid, t, w, 0.42, EGH - 0.7, *R(1), off=0.17)                                    # red neon band
            D.band(m, mf, a, b, 0.0, 0.55, 0.1, hexl("#6a665e"))                                               # stone plinth
            D.band(m, mf, a, b, EGH - 0.25, EGH + 0.05, 0.22, hexl("#bdb6a4"))                                # EG cornice
            ang = math.atan2(t[1], t[0]); nb = max(1, int(round(L / 2.6))); bw = L / nb
            if L < 6:       # short corner edge: door, lamps, corner balcony, bay
                ux, uy = a[0] + t[0] * L / 2, a[1] + t[1] * L / 2
                rot_box(m, mf, ux + n[0] * 0.12, uy + n[1] * 0.12, 1.5, 0.18, 0.0, 2.45, ang, hexl("#3a2418"))
                strip_quad(m, mg, (ux, uy), t, 1.1, 0.8, 2.5, *R(2), off=0.17)
                for sgn in (-1, 1): strip_quad(m, mg, (ux + t[0] * 1.5 * sgn, uy + t[1] * 1.5 * sgn), t, 0.3, 0.3, 2.55, *R(2), off=0.19)
                _balcony(m, mf, a, t, n, L / 2, FL0 + 0.0, w=3.0, proj=0.9)
                # corner bay from floor 2 to the eave with a dome cap
                bx, by = ux + n[0] * 0.45, uy + n[1] * 0.45
                rot_box(m, mf, bx, by, 3.3, 0.9, FL0 + FH - 0.2, ztop + 0.3, ang, hexl("#cdc6b4"))
                for k in range(1, 5):
                    z = FL0 + k * FH
                    for sgn in (-1, 1):
                        strip_quad(m, mg, (ux + t[0] * 0.8 * sgn, uy + t[1] * 0.8 * sgn), t, 0.85, 1.7, z + 0.5, *R(3 if (k + (sgn > 0)) % 3 else 4), off=0.92)
                    D.band(m, mf, (ux - t[0] * 1.65, uy - t[1] * 1.65), (ux + t[0] * 1.65, uy + t[1] * 1.65), z - 0.08, z + 0.1, 1.0, hexl("#d0c9b6"))
                dome8(m, mf, bx, by, 1.75, ztop + 0.3, 3.6, hexl(SLATE), n=8)
                continue
            for k in (1, 3):                                       # side balconies
                for i in range(nb):
                    if (i + k // 2) % 2 == 0: _balcony(m, mf, a, t, n, (i + 0.5) * bw, FL0 + k * FH, w=1.7, proj=0.75)
            for i in range(1, nb, 2):                              # dormers on the mansard
                u = (i + 0.5) * bw
                if u < 1.2 or u > L - 1.2: continue
                inx, iny = a[0] + t[0] * u - n[0] * 2.0, a[1] + t[1] * u - n[1] * 2.0
                rot_box(m, mf, inx, iny, 1.4, 1.3, ztop + 0.3, ztop + 2.9, ang, hexl("#cdc6b4"))
                fx, fy = a[0] + t[0] * u - n[0] * 1.35, a[1] + t[1] * u - n[1] * 1.35
                strip_quad(m, mg, (fx, fy), t, 0.8, 1.1, ztop + 1.45, *R(3 if i % 3 else 4), off=0.03)
                cone8(m, mf, inx, iny, 1.15, 0.05, ztop + 2.9, ztop + 3.9, hexl(SLATE), n=4, rot=ang + math.pi / 4)
            # parasols + tables on the pavement
            for k in range(4):
                u = u0 + w * (0.14 + 0.24 * k); px_, py_ = a[0] + t[0] * u + n[0] * 2.6, a[1] + t[1] * u + n[1] * 2.6
                cone8(m, mf, px_, py_, 1.35, 0.15, 2.15, 2.6, hexl("#ece8de"), n=8)
                m.box(mf, px_, py_, 0.06, 0.06, 0.0, 2.15, col=hexl("#555")); _chair_table(m, mf, px_, py_, ang)
    for sgn in (-1, 1):                                        # corner terrace
        sx, sy = cx + 0.0, cy + 2.6
    cone8(m, mf, cx, cy + 2.8, 1.35, 0.15, 2.15, 2.6, hexl("#ece8de"), n=8); m.box(mf, cx, cy + 2.8, 0.06, 0.06, 0.0, 2.15, col=hexl("#555")); _chair_table(m, mf, cx, cy + 2.8, 0.0)


def build():
    _k4.pick_edge = _pick
    _pick.cm = (CORNER[0], CORNER[1])
    # corner sign placed via pref="corner" (world midpoint -> local, resolved below)
    b = bid(PFX)
    from shapely.ops import unary_union as _u
    c = _u([outline(b["fp"], 0.6)]).centroid; ox, oy = round(c.x, 1), round(c.y, 1)
    _pick.cm = (SHORT[0][0] / 2 + SHORT[1][0] / 2 - ox, SHORT[0][1] / 2 + SHORT[1][1] / 2 - oy)
    signs[0]["pref"] = "corner"
    _k4.OVR4 = OVR
    _k4.block_model("calvados", "Le Calvados Idaplatz 4", [PFX], wall="#cdc6b4", frame="#efe9da", glass="#2e3b46", sky="#8aa0ae", cols=2, rows=3,
                    fh=3.15, bayw=2.6, win=(1.05, 1.95, 0.55), eg_h=EGH, eg_kind="arch", surround="#e9e3d2", base_col="#8b857a", cornice=("#d9d2bf", 0.6, 0.75),
                    floor_bands=("#c6bfac", 0.1, 0.22), roof=("hip", "#4e4f56", 4.0), roof_d=5.0, eave_rise=4.0, seed=77, lit=0.5, deep_z=6.5,
                    signs=signs, extra=extra, min_area=14.0)


if __name__ == "__main__":
    build()
