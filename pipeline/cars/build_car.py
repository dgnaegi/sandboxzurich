"""Build ONE low-poly car GLB (1 mesh, 1 primitive, 1 material, COLOR_0 + _PAINT).
    blender -b -P pipeline/cars/build_car.py -- <type>
Blender frame: Y = driving direction (front +Y), Z up. glTF export turns the front into -Z. Own design (WTFPL)."""
import sys, os, math
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix
from specs import SPECS, COL

ROOT = "/Users/danielgnagi/gtazurich"
TYPE = sys.argv[sys.argv.index("--") + 1]
S = SPECS[TYPE]
L, W, R, TW = S["L"], S["W"], S["R"], S["tw"]
HW = W / 2

def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def rgb(h): return tuple(lin(((h >> s) & 255) / 255) for s in (16, 8, 0))
C = {k: (rgb(v), 0.0) for k, v in COL.items()}
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
    nose = S["nose"]
    d = min(u, L - u)
    return plin([(o, s) for o, s in nose], d)

def body_bm():
    ztp, zbp = S["zt"], S["zb"]
    keys = [0, L, S["uA0"], S["uA1"], S["uC0"], S["uC1"], S["fo"], S["fo"] + S["WB"]] + [k for k, _ in ztp] + [k for k, _ in zbp]
    keys += [o for o, _ in S["nose"]] + [L - o for o, _ in S["nose"]] + [S["fo"] + d for d in (-.5, .5)] + [S["fo"] + S["WB"] + d for d in (-.5, .5)]
    us = fill([k for k in keys if 0 <= k <= L], .38)
    rings = []
    for u in us:
        w = HW * width_scale(u); zb = interp(zbp, u); zt = interp(ztp, u); H = zt - zb
        half = [(.78 * w, zb), (.95 * w, zb + .07), (w, zb + .30 * H), (.995 * w, zb + .80 * H), (.95 * w, zt - .03), (.76 * w, zt)]
        pts = [P(u, x, z) for x, z in half] + [P(u, 0, zt + .025)] + [P(u, -x, z) for x, z in reversed(half)]
        rings.append(pts)
    bm = new_bm(); loft(bm, rings); return bm

def cutters():
    bm = bmesh.new()
    for sg in (-1, 1):
        for uw in (S["fo"], S["fo"] + S["WB"]):
            vs = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=18, radius1=R + .065, radius2=R + .065, depth=.52)["verts"]
            bmesh.ops.transform(bm, matrix=Matrix.Translation(P(uw, sg * (HW - .16), R)) @ Matrix.Rotation(math.pi / 2, 4, 'Y'), verts=vs)
    me = bpy.data.meshes.new("cut"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("cut", me); bpy.context.collection.objects.link(ob); return ob

def color_body(bm):
    walls = (S["fo"], S["fo"] + S["WB"])
    for f in bm.faces:
        c = f.calc_center_median(); u = L / 2 - c.y; z = c.z; style = PAINT
        if f.normal.z < -0.5 or z < S["clad"]: style = C["plastic"]
        for uw in walls:
            if abs(c.x) < HW - .03 and (u - uw) ** 2 + (z - R) ** 2 < (R + .10) ** 2: style = C["plastic"]
        setc(bm, [f], style)

# ------------------------------------------------------------------ cabin
def cabin_bm():
    belt, H = S["belt"], S["H"]
    A0, A1, C0, C1 = S["uA0"], S["uA1"], S["uC0"], S["uC1"]
    roof = [(A0, belt), (A1, H - .035)]
    for f in (.25, .5, .75, 1.0):
        t = 2 * f - 1; roof.append((A1 + (C0 - A1) * f, H - .035 * t * t))
    roof += S["rear"] + [(C1, belt)]
    roof.sort()
    wins = S["windows"]
    keys = [p[0] for p in roof] + [a for a, b in wins] + [b for a, b in wins]
    us = fill(keys, .5)
    wb, wr = HW * S["wb"], HW * S["wb"] * S["wr"]
    fr = [(-0.05, None), (None, .09), (None, .5), (None, .92), (None, 1.0)]
    rings = []; hs = []
    for u in us:
        h = max(plin(roof, u) - belt, 0.0); hs.append(h)
        z = lambda f: belt + h * f
        half = [(wb, belt - .05), (wb * .995, z(.09)), (wb * .93 + wr * .07 + (wr - wb * .93) * 0.0, z(.5)), (wr + (wb - wr) * .12, z(.92)), (wr * .55, z(1.0))]
        # x of p1 interpolated between wb and wr
        half[2] = (wb + (wr - wb) * .5 * 0.8, z(.5))
        pts = [P(u, x, zz) for x, zz in half] + [P(u, 0, z(1.0) + .015)] + [P(u, -x, zz) for x, zz in reversed(half)]
        rings.append(pts)
    bm = new_bm(); grid = loft(bm, rings, caps=False)
    rg = S.get("rear_glass", True)
    for i, row in enumerate(grid):
        um = (us[i] + us[i + 1]) / 2
        inwin = any(a - 1e-3 <= um <= b + 1e-3 for a, b in wins)
        zone = (um < A1) or (C0 < um < S.get('glass_end', 99) and rg)
        for j, f in enumerate(row):
            sd = j in (1, 2, 7, 8); top = j in (3, 4, 5, 6)
            g = (sd and inwin) or (top and zone)
            setc(bm, [f], C["glass"] if g else PAINT)
    return bm, roof

# ------------------------------------------------------------------ details
def wheel(bm, uw, sg):
    cx = sg * (HW - .02 - TW / 2); cy = L / 2 - uw; h = TW / 2; n = 14
    prof = [(.60 * R, .80 * h), (.92 * R, h), (R, .5 * h), (R, -.5 * h), (.92 * R, -h), (.60 * R, -h)]
    vs = [[bm.verts.new((cx + sg * t, cy + r * math.cos(2 * math.pi * k / n), R + r * math.sin(2 * math.pi * k / n))) for k in range(n)] for r, t in prof]
    fl = []
    for i in range(len(prof) - 1):
        for k in range(n):
            f = bm.faces.new((vs[i][k], vs[i][(k + 1) % n], vs[i + 1][(k + 1) % n], vs[i + 1][k]))
            c = f.calc_center_median(); d = Vector((0, c.y - cy, c.z - R)).normalized() * .78 * R
            orient(f, Vector((cx, cy + d.y, R + d.z))); fl.append(f)
    setc(bm, fl, C["tyre"])
    def ring(r, t, k, a0=0): return (cx + sg * t, cy + r * math.cos(a0 + 2 * math.pi * k / k_n), R + r * math.sin(a0 + 2 * math.pi * k / k_n))
    out = Vector((sg, 0, 0))
    k_n = 10
    poly(bm, [ring(.52 * R, .55 * h, k) for k in range(10)], out, C["rimdark"])
    # rim lip annulus
    a = [bm.verts.new(ring(.60 * R, .80 * h, k)) for k in range(10)]; b = [bm.verts.new(ring(.50 * R, .80 * h, k)) for k in range(10)]
    fs = []
    for k in range(10):
        f = bm.faces.new((a[k], a[(k + 1) % 10], b[(k + 1) % 10], b[k])); f.normal_update()
        if f.normal.dot(out) < 0: f.normal_flip()
        fs.append(f)
    setc(bm, fs, C["rim"])
    for s in range(5):
        a0 = math.radians(18 + 72 * s); hw = .045 * R
        d = Vector((math.cos(a0), math.sin(a0))); nrm = Vector((-d.y, d.x))
        def pt(rr, off): return (cx + sg * .74 * h, cy + d.x * rr + nrm.x * off, R + d.y * rr + nrm.y * off)
        poly(bm, [pt(.12 * R, -hw), pt(.54 * R, -hw), pt(.54 * R, hw), pt(.12 * R, hw)], out, C["rim"])
    k_n = 5; poly(bm, [ring(.15 * R, .78 * h, k) for k in range(5)], out, C["rim"])

def details_bm(roof):
    bm = new_bm(); ztp, zbp = S["zt"], S["zb"]
    for sg in (-1, 1):
        for uw in (S["fo"], S["fo"] + S["WB"]): wheel(bm, uw, sg)
    # lights, grille, intake, plates (front)
    zt0, zb0 = interp(ztp, .06), interp(zbp, 0)
    for sg in (-1, 1):
        zl = zt0 - .10; xl = sg * .57 * HW
        if S.get("round_lights"): cyl(bm, P(.05, sg * .60 * HW, zt0 - .09), .095, .09, "y", 10, C["head"])
        else: box(bm, P(.06, xl, zl), (.33, .10, .085), -sg * .38, C["head"])
        tw_, th_, tz = S["tail"]; ztr = interp(ztp, L - .05)
        wr_ = HW * width_scale(L - .06)
        if th_ > .2: box(bm, P(L - .05, sg * (wr_ - tw_ / 2 - .02), tz), (tw_, .09, th_), sg * .25, C["tail"])
        else: box(bm, P(L - .05, sg * (wr_ - tw_ / 2 - .06), ztr - .12), (tw_, .09, th_), sg * .30, C["tail"])
    if S["grille"]:
        gw, gh = S["grille"]; box(bm, P(.0, 0, zt0 - .09 - gh / 2 + .03), (gw * 1.0, .03, gh), 0, C["plastic"])
    box(bm, P(.0, 0, zb0 + .11), (1.05 * HW, .035, .11), 0, C["plastic"])
    ztl, zbl = interp(ztp, L), interp(zbp, L)
    box(bm, P(L, 0, zbl + .11), (1.05 * HW, .035, .10), 0, C["plastic"])
    for uu, zc in ((-.004, zb0 + .21), (L + .004, zbl + .22)):
        box(bm, P(uu, 0, zc), (.34, .03, .15), 0, C["plate"])
    # mirrors
    belt = S["belt"]; um = S["uA0"] + (S["uA1"] - S["uA0"]) * .6
    for sg in (-1, 1):
        box(bm, P(um, sg * (HW * S["wb"] + .06), belt + .13), (.12, .11, .10), 0, PAINT)
    # door seams / handles
    seams = S["seams"]
    for sg in (-1, 1):
        for u in seams:
            zb, zt = interp(zbp, u), interp(ztp, u); H = zt - zb
            box(bm, P(u, sg * HW, zb + .55 * H), (.014, .012, .50 * H), 0, C["seam"])
        for a, b in zip(seams, seams[1:]):
            u = b - .20 if b - a > .5 else None
            if u:
                zb, zt = interp(zbp, u), interp(ztp, u); box(bm, P(u, sg * HW, zb + .76 * (zt - zb)), (.03, .15, .03), 0, PAINT)
    # roof rails
    if S["rails"]:
        for sg in (-1, 1):
            u0, u1 = S["uA1"] + .25, S["uC0"] - .15; zr = S["H"] - .035 * 0.2
            x = sg * HW * S["wb"] * S["wr"] * .72
            box(bm, P((u0 + u1) / 2, x, zr + .005), (.035, u1 - u0, .035), 0, C["plastic"])
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
bpy.ops.object.select_all(action="DESELECT")
for o in (bpo, co, do): o.select_set(True)
bpy.context.view_layer.objects.active = bpo
bpy.ops.object.join()
car = bpo; car.name = TYPE
bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
me = car.data
mat = bpy.data.materials.new("car"); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]; vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = .5; bsdf.inputs["Metallic"].default_value = .1
me.materials.clear(); me.materials.append(mat)
me.color_attributes.active_color = me.color_attributes["Col"]; me.color_attributes.render_color_index = me.color_attributes.find("Col")
bpy.ops.object.select_all(action="DESELECT"); car.select_set(True)
out = f"{ROOT}/web/public/models/cars/{TYPE}.glb"
kw = dict(filepath=out, export_format="GLB", use_selection=True, export_apply=False, export_yup=True, export_cameras=False, export_lights=False, export_animations=False)
for extra in (dict(export_attributes=True, export_vertex_color="ACTIVE"), dict(export_attributes=True), {}):
    try: bpy.ops.export_scene.gltf(**kw, **extra); break
    except TypeError as e: print("opt fail", e)
print("DONE", TYPE, len(me.polygons), "polys")
