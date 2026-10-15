"""Build ONE low-poly car GLB (1 mesh, 1 primitive, 1 material, COLOR_0 + _PAINT).
_PAINT codes: 1 = body paint (tinted by instance colour), 0.3 = glass (reflective), 0.15 = chrome/alloy (reflective), 0 = matte.
    blender -b -P pipeline/cars/build_car.py -- <type>
Blender frame: Y = driving direction (front +Y), Z up. glTF export turns the front into -Z. Own design (WTFPL)."""
import sys, os, math
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from specs import SPECS, COL

ROOT = "/Users/danielgnagi/sandboxzurich"
_A = sys.argv[sys.argv.index("--") + 1:]
TYPE = _A[0]
DRIVE = "drive" in _A[1:]   # drivable variant: body without wheels/lights + separate wheel_* / head / tail objects
S = SPECS[TYPE]
L, W, R, TW = S["L"], S["W"], S["R"], S["tw"]
HW = W / 2

def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def rgb(h): return tuple(lin(((h >> s) & 255) / 255) for s in (16, 8, 0))
C = {k: (rgb(v), 0.0) for k, v in COL.items()}
for _k, _c in (('glass', .3), ('rim', .15), ('chrome', .15), ('steel', .15)): C[_k] = (C[_k][0], _c)
PAINT = ((1.0, 1.0, 1.0), 1.0)

def new_bm():
    bm = bmesh.new(); bm.loops.layers.float_color.new("Col"); bm.loops.layers.float.new("_PAINT"); return bm
def setc(bm, faces, style):
    lc = bm.loops.layers.float_color["Col"]; lp = bm.loops.layers.float["_PAINT"]
    for f in faces:
        for l in f.loops: l[lc] = (*style[0], 1.0); l[lp] = style[1]
def P(u, x, z): return Vector((x, L / 2 - u, z))

def interp(pts, u):   # cosine interpolation through keypoints
    if u <= pts[0][0]: return pts[0][1]
    for (a, za), (b, zb) in zip(pts, pts[1:]):
        if u <= b:
            t = (u - a) / (b - a); t = (1 - math.cos(math.pi * t)) / 2; return za + (zb - za) * t
    return pts[-1][1]
def plin(pts, u):
    if u <= pts[0][0]: return pts[0][1]
    for (a, za), (b, zb) in zip(pts, pts[1:]):
        if u <= b: return za + (zb - za) * (u - a) / (b - a)
    return pts[-1][1]
def fill(keys, gap):
    keys = sorted(set(round(k, 4) for k in keys)); out = []
    for a, b in zip(keys, keys[1:]):
        out.append(a); n = int(math.ceil((b - a) / gap))
        out += [a + (b - a) * i / n for i in range(1, n)]
    return out + [keys[-1]]

def orient(f, ref):
    f.normal_update()
    if f.normal.dot(f.calc_center_median() - ref) < 0: f.normal_flip()

def loft(bm, rings, caps=True):
    vs = [[bm.verts.new(p) for p in r] for r in rings]; n = len(rings[0]); grid = []
    cen = [sum(rings[i], Vector()) / n for i in range(len(rings))]
    for i in range(len(rings) - 1):
        row = []
        for j in range(n):
            f = bm.faces.new((vs[i][j], vs[i][(j + 1) % n], vs[i + 1][(j + 1) % n], vs[i + 1][j]))
            orient(f, (cen[i] + cen[i + 1]) / 2); row.append(f)
        grid.append(row)
    if caps:
        orient(bm.faces.new(vs[0]), cen[-1]); orient(bm.faces.new(vs[-1]), cen[0])
    return grid

def box(bm, c, size, yaw, style):
    vs = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Diagonal((*size, 1)), verts=vs)
    setc(bm, {f for v in vs for f in v.link_faces}, style)
def cyl(bm, c, r, depth, axis, seg, style):
    vs = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=depth)["verts"]
    rot = {"x": Matrix.Rotation(math.pi / 2, 4, 'Y'), "y": Matrix.Rotation(math.pi / 2, 4, 'X'), "z": Matrix.Identity(4)}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ rot, verts=vs)
    setc(bm, {f for v in vs for f in v.link_faces}, style)
def poly(bm, pts, nref, style):
    f = bm.faces.new([bm.verts.new(p) for p in pts]); f.normal_update()
    if f.normal.dot(nref) < 0: f.normal_flip()
    setc(bm, [f], style)

# ------------------------------------------------------------------ body
def width_scale(u):
    return plin([(o, s) for o, s in S["nose"]], min(u, L - u))

def half_body(u):
    """(x, z) half cross-section of the lower body at u: rocker, belly, shoulder crease, hood/deck edge."""
    w = HW * width_scale(u); zb = interp(S["zb"], u); zt = interp(S["zt"], u); H = zt - zb
    return [(.74 * w, zb), (.93 * w, zb + .05), (.995 * w, zb + .15 * H), (w, zb + .38 * H), (.992 * w, zb + .62 * H),
            (.962 * w, zb + .84 * H), (.925 * w, zt - .025), (.70 * w, zt)]
def side_x(u, z):
    h = half_body(u)
    for (x0, z0), (x1, z1) in zip(h, h[1:]):
        if z0 <= z <= z1 and z1 > z0: return x0 + (x1 - x0) * (z - z0) / (z1 - z0)
    return h[3][0]

def body_bm():
    keys = [0, L, S["uA0"], S["uA1"], S["uC0"], S["uC1"], S["fo"], S["fo"] + S["WB"]] + [k for k, _ in S["zt"]] + [k for k, _ in S["zb"]]
    keys += [o for o, _ in S["nose"]] + [L - o for o, _ in S["nose"]] + [S["fo"] + d for d in (-.5, .5)] + [S["fo"] + S["WB"] + d for d in (-.5, .5)]
    us = fill([k for k in keys if 0 <= k <= L], .42)
    rings = []
    for u in us:
        half = half_body(u); zt = half[-1][1]
        rings.append([P(u, x, z) for x, z in half] + [P(u, 0, zt + .012)] + [P(u, -x, z) for x, z in reversed(half)])
    bm = new_bm(); loft(bm, rings); return bm

def cutters():
    bm = bmesh.new()
    for sg in (-1, 1):
        for uw in (S["fo"], S["fo"] + S["WB"]):
            vs = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=14, radius1=R + .065, radius2=R + .065, depth=.52)["verts"]
            bmesh.ops.transform(bm, matrix=Matrix.Translation(P(uw, sg * (HW - .16), R)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'), verts=vs)
    me = bpy.data.meshes.new("cut"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("cut", me); bpy.context.collection.objects.link(ob); return ob

def color_body(bm):
    walls = (S["fo"], S["fo"] + S["WB"])
    for f in bm.faces:
        c = f.calc_center_median(); u = L / 2 - c.y; z = c.z; style = PAINT
        if f.normal.z < -0.5 or z < S["clad"]: style = C["plastic"]
        for uw in walls:
            rad = Vector((0, c.y - (L / 2 - uw), z - R))
            if abs(c.x) < HW - .03 and rad.length < R + .10 and rad.length > 1e-4 and f.normal.dot(rad.normalized()) < -.25: style = C["plastic"]
        setc(bm, [f], style)

# ------------------------------------------------------------------ cabin (greenhouse)
def cabin_bm():
    belt, H = S["belt"], S["H"]
    A0, A1, C0, C1 = S["uA0"], S["uA1"], S["uC0"], S["uC1"]
    roof = [(A0, belt), (A1, H - .035)]
    for f in (.25, .5, .75, 1.0):
        t = 2 * f - 1; roof.append((A1 + (C0 - A1) * f, H - .035 * t * t))
    roof += S["rear"] + [(C1, belt)]
    roof.sort()
    wins = [(min(S["windows"][0][0], A0 + .62 * (A1 - A0)), S["windows"][0][1])] + list(S["windows"][1:])   # front window reaches up the A-pillar line
    us = fill([p[0] for p in roof] + [a for a, b in wins] + [b for a, b in wins], .5)
    wb, wr = HW * S["wb"], HW * S["wb"] * S["wr"]
    rings = []
    for u in us:
        h = max(plin(roof, u) - belt, 0.0); z = lambda f: belt + h * f
        half = [(wb, belt - .05), (wb * .996, z(.07)), (wb + (wr - wb) * .40, z(.5)), (wr + (wb - wr) * .10, z(.91)), (wr * .85, z(1.0))]
        rings.append([P(u, x, zz) for x, zz in half] + [P(u, 0, z(1.0) + .02)] + [P(u, -x, zz) for x, zz in reversed(half)])
    bm = new_bm(); grid = loft(bm, rings, caps=False)
    rg, ge = S.get("rear_glass", True), S.get('glass_end', 99)
    for i, row in enumerate(grid):
        um = (us[i] + us[i + 1]) / 2
        inwin = any(a - 1e-3 <= um <= b + 1e-3 for a, b in wins)
        between = any(b1 - 1e-3 <= um <= a2 + 1e-3 for (a1, b1), (a2, b2) in zip(wins, wins[1:]))
        front = um < A1; rear = C0 < um < ge and rg
        roofzone = A1 <= um <= C0 and S.get("glass_roof")
        for j, f in enumerate(row):
            if j == 10: st = C["plastic"]                          # hidden underside
            else:
                s_ = j if j < 4 else (9 - j if 5 < j < 10 else None)      # side face index 0..3, None = roof faces 4/5
                if s_ is None: st = C["glass"] if (front or rear or roofzone) else PAINT
                elif inwin and s_ == 0: st = C["trim"]
                elif inwin and s_ in (1, 2): st = C["glass"]
                elif between and s_ in (0, 1, 2): st = C["trim"]
                else: st = PAINT
            setc(bm, [f], st)
    return bm, roof

# ------------------------------------------------------------------ details
def wheel(bm, uw, sg):
    cx = sg * (HW - .02 - TW / 2); cy = L / 2 - uw; h = TW / 2; n = 16
    prof = [(.62 * R, .80 * h), (.92 * R, h), (R, .55 * h), (R, -.55 * h), (.92 * R, -h), (.62 * R, -h)]
    vs = [[bm.verts.new((cx + sg * t, cy + r * math.cos(2 * math.pi * k / n), R + r * math.sin(2 * math.pi * k / n))) for k in range(n)] for r, t in prof]
    for i in range(len(prof) - 1):
        fl = []
        for k in range(n):
            f = bm.faces.new((vs[i][k], vs[i][(k + 1) % n], vs[i + 1][(k + 1) % n], vs[i + 1][k]))
            c = f.calc_center_median(); d = Vector((0, c.y - cy, c.z - R)).normalized() * .78 * R
            orient(f, Vector((cx, cy + d.y, R + d.z))); fl.append(f)
        setc(bm, fl, C["tyre"] if i in (2,) else C["tyre2"])
    k_n = 10
    def ring(r, t, k, a0=0): return (cx + sg * t, cy + r * math.cos(a0 + 2 * math.pi * k / k_n), R + r * math.sin(a0 + 2 * math.pi * k / k_n))
    out = Vector((sg, 0, 0)); steel = S.get("steel")
    poly(bm, [ring(.55 * R, .52 * h, k) for k in range(10)], out, C["rimdark"])      # dish
    a = [bm.verts.new(ring(.62 * R, .80 * h, k)) for k in range(10)]; b = [bm.verts.new(ring(.53 * R, .80 * h, k)) for k in range(10)]
    fs = []
    for k in range(10):
        f = bm.faces.new((a[k], a[(k + 1) % 10], b[(k + 1) % 10], b[k])); f.normal_update()
        if f.normal.dot(out) < 0: f.normal_flip()
        fs.append(f)
    setc(bm, fs, C["steel"] if steel else C["rim"])
    if steel:                                                                 # hub cap + small bolts ring
        k_n = 10; poly(bm, [ring(.30 * R, .70 * h, k) for k in range(10)], out, C["steel"])
        return
    for s in range(5):
        a0 = math.radians(18 + 72 * s); hw = .055 * R
        d = Vector((math.cos(a0), math.sin(a0))); nrm = Vector((-d.y, d.x))
        def pt(rr, off): return (cx + sg * .70 * h, cy + d.x * rr + nrm.x * off, R + d.y * rr + nrm.y * off)
        poly(bm, [pt(.12 * R, -hw * 1.4), pt(.54 * R, -hw), pt(.54 * R, hw), pt(.12 * R, hw * 1.4)], out, C["rim"])
    k_n = 5; poly(bm, [ring(.16 * R, .74 * h, k) for k in range(5)], out, C["rim"])

def hl_pos(sg):
    zt0 = interp(S["zt"], .06)
    return zt0 - (.09 if S.get("round_lights") else .10), sg * (.60 if S.get("round_lights") else .57) * HW

def add_head(bm):
    zl, xl = hl_pos(1); hw_, hh_ = S["hl"]
    for sg in (-1, 1):
        if S.get("round_lights"): cyl(bm, P(.05, sg * xl, zl), hh_ / 2 + .005 if hh_ < .15 else .095, .09, "y", 10, C["head"])
        else: box(bm, P(.06, sg * xl, zl), (hw_, .10, hh_), -sg * .38, C["head"])
def add_tail(bm):
    ztp = S["zt"]
    for sg in (-1, 1):
        tw_, th_, tz = S["tail"]; ztr = interp(ztp, L - .05)
        wr_ = HW * width_scale(L - .06)
        if th_ > .2: box(bm, P(L - .05, sg * (wr_ - tw_ / 2 - .02), tz), (tw_, .09, th_), sg * .25, C["tail"])
        else: box(bm, P(L - .05, sg * (wr_ - tw_ / 2 - .06), ztr - .12), (tw_, .09, th_), sg * .30, C["tail"])

def plate(bm, uu, zc, front):
    """Swiss-style plate: white field, dark digit blocks, small neutral crest square (no real coat of arms)."""
    y = L / 2 - uu; ny = 1 if front else -1; n = Vector((0, ny, 0)); pw, ph = .40, .105
    def quad(x0, x1, z0, z1, off, st): poly(bm, [(x0, y + ny * off, z0), (x1, y + ny * off, z0), (x1, y + ny * off, z1), (x0, y + ny * off, z1)], n, st)
    quad(-pw / 2, pw / 2, zc - ph / 2, zc + ph / 2, .004, C["plate"])
    quad(-pw / 2 + .012, -pw / 2 + .062, zc - .035, zc + .035, .008, C["crest"])
    x = -pw / 2 + .075
    for k in range(8):
        w = .035 if k < 2 else .030
        quad(x, x + w, zc - .030, zc + .030, .008, C["ink"]); x += w + (.012 if k == 1 else .008)

def details_bm(roof):
    bm = new_bm(); ztp, zbp = S["zt"], S["zb"]
    if not DRIVE:
        for sg in (-1, 1):
            for uw in (S["fo"], S["fo"] + S["WB"]): wheel(bm, uw, sg)
        add_head(bm); add_tail(bm)
    zt0, zb0 = interp(ztp, .06), interp(zbp, 0)
    ztl, zbl = interp(ztp, L), interp(zbp, L)
    hw_, hh_ = S["hl"]; zl, xl = hl_pos(1)
    for sg in (-1, 1):   # dark lamp housings behind the lenses, fog/air intakes, bumper corners
        box(bm, P(.075, sg * xl, zl), (hw_ + .04, .09, hh_ + .04), -sg * .38, C["trim"])
        box(bm, P(.03, sg * .66 * HW, zb0 + .14), (.20, .03, .06), 0, C["trim"])
        tw_, th_, tz = S["tail"]; wr_ = HW * width_scale(L - .06)
        box(bm, P(L - .07, sg * (wr_ - tw_ / 2 - (.02 if th_ > .2 else .06)), tz if th_ > .2 else interp(ztp, L - .05) - .12), (tw_ + .035, .08, th_ + .035), sg * (.25 if th_ > .2 else .30), C["trim"])
    if S["grille"]:
        gw, gh = S["grille"]
        box(bm, P(.0, 0, zt0 - .09 - gh / 2 + .03), (gw, .03, gh), 0, C["trim"])
        box(bm, P(-.012, 0, zt0 - .09 - gh / 2 + .03), (gw * .55, .02, .018), 0, C["chrome"])
    box(bm, P(-.004, 0, zb0 + .30), (.62 * HW * 2 * .5, .03, .09), 0, C["trim"])       # lower air intake
    box(bm, P(.0, 0, zb0 + .11), (1.05 * HW, .035, .11), 0, C["plastic"])
    box(bm, P(L, 0, zbl + .11), (1.05 * HW, .035, .10), 0, C["plastic"])
    plate(bm, -.003, zb0 + .20, True); plate(bm, L + .003, zbl + .20, False)
    # mirrors: housing + glass face
    belt = S["belt"]; um = S["uA0"] + (S["uA1"] - S["uA0"]) * .62
    for sg in (-1, 1):
        mx = sg * (HW * S["wb"] + .07)
        box(bm, P(um, mx, belt + .14), (.13, .10, .10), 0, PAINT)
        box(bm, P(um, sg * (HW * S["wb"] + .02), belt + .09), (.05, .06, .03), 0, C["plastic"])
    # door seams (flat quads along the body profile), door handles, roof rails
    seams = S["seams"]
    for sg in (-1, 1):
        for u in seams:
            h = half_body(u)[2:6]
            for (x0, z0), (x1, z1) in zip(h, h[1:]):
                poly(bm, [P(u - .007, sg * (x0 + .004), z0), P(u + .007, sg * (x0 + .004), z0), P(u + .007, sg * (x1 + .004), z1), P(u - .007, sg * (x1 + .004), z1)], Vector((sg, 0, 0)), C["seam"])
        for a, b in zip(seams, seams[1:]):
            if b - a > .5:
                u = b - .20; zb, zt = interp(zbp, u), interp(ztp, u); z = zb + .72 * (zt - zb); x = side_x(u, z) + .008
                poly(bm, [P(u - .075, sg * x, z - .012), P(u + .075, sg * x, z - .012), P(u + .075, sg * x, z + .012), P(u - .075, sg * x, z + .012)], Vector((sg, 0, 0)), C["chrome"])
        if S.get("slide"):   # van: sliding-door rail and rear door seam
            zc = interp(zbp, 3.0) + .78
            poly(bm, [P(2.62, sg * (side_x(2.62, zc) + .005), zc + .05), P(4.2, sg * (side_x(4.2, zc) + .005), zc + .05), P(4.2, sg * (side_x(4.2, zc) + .005), zc + .07), P(2.62, sg * (side_x(2.62, zc) + .005), zc + .07)], Vector((sg, 0, 0)), C["seam"])
    if S["rails"]:
        for sg in (-1, 1):
            u0, u1 = S["uA1"] + .25, S["uC0"] - .15; zr = S["H"] - .035 * 0.2
            x = sg * HW * S["wb"] * S["wr"] * .72
            box(bm, P((u0 + u1) / 2, x, zr + .005), (.035, u1 - u0, .035), 0, C["plastic"])
    if S.get("rear_win"):   # van rear doors: two windows and the centre seam
        z0, z1 = S["rear_win"]; zz = min(z1, ztl - .05)
        for sg in (-1, 1): poly(bm, [(sg * .06, L / 2 - L - .004, z0), (sg * .42 * HW * 1.2, L / 2 - L - .004, z0), (sg * .42 * HW * 1.2, L / 2 - L - .004, zz), (sg * .06, L / 2 - L - .004, zz)], Vector((0, -1, 0)), C["glass"])
        poly(bm, [(-.006, L / 2 - L - .006, zbl + .3), (.006, L / 2 - L - .006, zbl + .3), (.006, L / 2 - L - .006, ztl - .02), (-.006, L / 2 - L - .006, ztl - .02)], Vector((0, -1, 0)), C["seam"])
    if S.get("sign"):       # taxi roof sign
        um = (S["uA1"] + S["uC0"]) / 2; zr = S["H"]
        box(bm, P(um, 0, zr + .01), (.46, .20, .03), 0, C["plastic"])
        box(bm, P(um, 0, zr + .085), (.52, .17, .12), 0, C["sign"])
    return bm

# ------------------------------------------------------------------ assemble
def to_obj(bm, name):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bb = body_bm(); bo = to_obj(bb, "body"); cut = cutters()
m = bo.modifiers.new("b", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = cut; m.solver = "EXACT"
dg = bpy.context.evaluated_depsgraph_get(); me2 = bpy.data.meshes.new_from_object(bo.evaluated_get(dg))
bm2 = new_bm(); bm2.from_mesh(me2)
if "Col" not in bm2.loops.layers.float_color: pass
color_body(bm2); bpo = to_obj(bm2, "body2")
cb, roof = cabin_bm(); co = to_obj(cb, "cabin"); do = to_obj(details_bm(roof), "details")
bpy.data.objects.remove(bo); bpy.data.objects.remove(cut)
extras = []
if DRIVE:
    for name, (sg, uw) in {"wheel_fl": (-1, S["fo"]), "wheel_fr": (1, S["fo"]), "wheel_rl": (-1, S["fo"] + S["WB"]), "wheel_rr": (1, S["fo"] + S["WB"])}.items():
        wb_ = new_bm(); wheel(wb_, uw, sg)
        cx, cy = sg * (HW - .02 - TW / 2), L / 2 - uw
        bmesh.ops.translate(wb_, vec=(-cx, -cy, -R), verts=wb_.verts)
        wo = to_obj(wb_, name); wo.location = (cx, cy, R); extras.append(wo)
    for name, fn in (("head", add_head), ("tail", add_tail)):
        lb = new_bm(); fn(lb); extras.append(to_obj(lb, name))
bpy.ops.object.select_all(action="DESELECT")
for o in (bpo, co, do): o.select_set(True)
bpy.context.view_layer.objects.active = bpo
bpy.ops.object.join()
car = bpo; car.name = TYPE
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
for o in extras: o.select_set(True)
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
me = car.data
mat = bpy.data.materials.new("car"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]; vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = .5; bsdf.inputs["Metallic"].default_value = .1
me.materials.clear(); me.materials.append(mat)
for o in extras:
    o.data.materials.clear(); o.data.materials.append(mat)
    for ca in [c for c in o.data.color_attributes if c.name != "Col"]: o.data.color_attributes.remove(ca)
    o.data.color_attributes.active_color = o.data.color_attributes["Col"]
    o.data.color_attributes.render_color_index = o.data.color_attributes.find("Col")
me.color_attributes.active_color = me.color_attributes["Col"]; me.color_attributes.render_color_index = me.color_attributes.find("Col")
bpy.ops.object.select_all(action="DESELECT"); car.select_set(True)
for o in extras: o.select_set(True)
out = f"{ROOT}/web/public/models/cars/{TYPE}{'_drive' if DRIVE else ''}.glb"
kw = dict(filepath=out, export_format="GLB", use_selection=True, export_apply=False, export_yup=True, export_cameras=False, export_lights=False, export_animations=False)
for extra in (dict(export_attributes=True, export_vertex_color="ACTIVE"), dict(export_attributes=True), {}):
    try: bpy.ops.export_scene.gltf(**kw, **extra); break
    except TypeError as e: print("opt fail", e)
print("DONE", TYPE, len(me.polygons), "polys")
