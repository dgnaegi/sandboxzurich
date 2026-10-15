"""Build the accessory GLBs (vertex colours, <=300 tris each) into web/public/models/accessories/.

    blender -b -P pipeline/blender/build_accessories.py
Model space: origin = attach point, +X = character right, +Y = character forward, +Z = up (exports to glTF Y-up, forward -Z).
Placement (bone / offset / rotation) is measured against the real rigs by measure_attach.mjs -> manifest.json.
"""
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix
ROOT = "/Users/danielgnagi/gtazurich"; OUT = f"{ROOT}/web/public/models/accessories"
os.makedirs(OUT, exist_ok=True)
def lin(c): return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
G = (0.62, 0.62, 0.62)   # tintable base grey (set material.color to tint)

class B:
    def __init__(s): s.bm = bmesh.new(); s.lay = s.bm.loops.layers.float_color.new("Col")
    def face(s, vs, col):
        f = s.bm.faces.new([s.bm.verts.new(v) for v in vs]); f.smooth = False
        c = (*lin(col), 1.0)
        for l in f.loops: l[s.lay] = c
    def quadstrip(s, rings, col, close=True, cap0=False, cap1=False):
        n = len(rings[0])
        for a, b in zip(rings, rings[1:]):
            for i in range(n if close else n - 1):
                j = (i + 1) % n; s.face([a[i], a[j], b[j], b[i]], col)
        if cap0: s.face(rings[0][::-1], col)
        if cap1: s.face(rings[-1], col)
    def box(s, c, sz, col, top=(1, 1), rot=None):
        """frustum box centred c, size sz=(x,y,z); top=(tx,ty) scales the top face."""
        hx, hy, hz = sz[0] / 2, sz[1] / 2, sz[2] / 2
        lo = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz)]
        hi = [(-hx * top[0], -hy * top[1], hz), (hx * top[0], -hy * top[1], hz), (hx * top[0], hy * top[1], hz), (-hx * top[0], hy * top[1], hz)]
        M = Matrix.Translation(c) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4))
        lo = [M @ Vector(v) for v in lo]; hi = [M @ Vector(v) for v in hi]
        s.quadstrip([lo, hi], col, True, True, True)
    def cyl(s, p0, p1, r0, r1, n, col, caps=(True, True), squash=1.0):
        p0, p1 = Vector(p0), Vector(p1); d = (p1 - p0).normalized()
        a = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0)); u = d.cross(a).normalized(); v = d.cross(u).normalized() * squash
        ring = lambda p, r: [p + (u * math.cos(2 * math.pi * i / n) + v * math.sin(2 * math.pi * i / n)) * r for i in range(n)]
        s.quadstrip([ring(p0, r0), ring(p1, r1)], col, True, caps[0], caps[1])
    def tube(s, pts, r, col, n=4):
        for a, b in zip(pts, pts[1:]): s.cyl(a, b, r, r, n, col, (False, False))
    def tris(s): return sum(len(f.verts) - 2 for f in s.bm.faces)
    def obj(s, name, parent=None, loc=(0, 0, 0)):
        me = bpy.data.meshes.new(name); s.bm.to_mesh(me); s.bm.free()
        me.color_attributes.active_color = me.color_attributes['Col']; me.color_attributes.render_color_index = 0; me.materials.append(MAT); o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
        o.location = loc
        if parent: o.parent = parent
        return o
MAT = bpy.data.materials.new("acc"); MAT.use_nodes = True
_b = MAT.node_tree.nodes["Principled BSDF"]; _b.inputs["Roughness"].default_value = 0.8; _b.inputs["Base Color"].default_value = (1, 1, 1, 1)

def clear():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
def export(name, objs, anim=False):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=f"{OUT}/{name}.glb", export_format="GLB", use_selection=True, export_vertex_color="ACTIVE",
        export_animations=anim, export_apply=True, export_yup=True, export_cameras=False, export_lights=False, export_extras=False,
        export_image_format="NONE", export_materials="EXPORT", export_animation_mode="ACTIONS" if anim else "ACTIONS")
    return os.path.getsize(f"{OUT}/{name}.glb")

def post(name):
    """drop COLOR_1, merge per-node actions into one 'walk' clip, prune unused data."""
    import struct, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import glb_compact
    f = f"{OUT}/{name}.glb"; b = open(f, "rb").read(); L = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + L]); binc = b[28 + L:]
    for m in j["meshes"]:
        for p in m["primitives"]: p["attributes"].pop("COLOR_1", None)
    for m in j["materials"]: m.pop("doubleSided", None)
    if j.get("animations"):
        ch, sm = [], []
        for a in j["animations"]:
            off = len(sm); sm += a["samplers"]
            for c in a["channels"]: ch.append(dict(c, sampler=c["sampler"] + off))
        j["animations"] = [dict(name="walk", channels=ch, samplers=sm)]
    js = json.dumps(j, separators=(",", ":")).encode()
    while len(js) % 4: js += b" "
    open(f, "wb").write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(binc)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binc), 0x004E4942) + binc)
    glb_compact.compact(f); return os.path.getsize(f)
INFO = {}
def finish(name, parts, anim=False, note=""):
    t = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in parts if o.type == "MESH")
    assert t <= 300, (name, t)
    export(name, parts, anim); kb = post(name); INFO[name] = dict(tris=t, bytes=kb); print("ACC", name, t, "tris", kb, "B")

DARK = (0.12, 0.12, 0.13); BLK = (0.04, 0.04, 0.045)
def backpack():
    b = B(); b.box((0, 0, 0), (0.30, 0.15, 0.40), G, top=(0.92, 0.9))
    b.box((0, -0.10, -0.07), (0.23, 0.06, 0.17), (0.45, 0.45, 0.45)); b.box((0, 0, 0.215), (0.10, 0.03, 0.03), DARK)
    b.box((0, 0, -0.208), (0.30, 0.15, 0.015), DARK)
    for sx in (-1, 1): b.box((sx * 0.085, 0.08, 0.0), (0.04, 0.012, 0.34), DARK)   # shoulder straps (front face)
    return [b.obj("backpack")]
def shoulder_bag():
    b = B(); b.box((0, 0, 0), (0.28, 0.09, 0.2), G, top=(1, 1)); b.box((0, 0.0, 0.07), (0.285, 0.092, 0.07), (0.45, 0.45, 0.45))
    b.box((0, 0.0, 0.0), (0.04, 0.095, 0.04), DARK, rot=None)
    b.box((0.0, 0, 0.36), (0.022, 0.012, 0.50), DARK)   # strap up to the shoulder
    return [b.obj("shoulder_bag")]
def tote_bag():
    b = B(); b.box((0, 0, -0.26), (0.34, 0.1, 0.34), (0.7, 0.68, 0.62), top=(1.05, 1.0))
    for sx in (-1, 1): b.tube([(sx * 0.1, 0, -0.1), (sx * 0.06, 0, 0.03), (sx * 0.0, 0, 0.05)], 0.008, (0.55, 0.53, 0.48), 4)
    b.tube([(-0.1, 0, -0.1), (-0.12, 0, -0.04), (-0.06, 0, 0.03), (0, 0, 0.05), (0.06, 0, 0.03), (0.12, 0, -0.04), (0.1, 0, -0.1)], 0.008, (0.55, 0.53, 0.48), 4)
    return [b.obj("tote_bag")]
def shopping_bag(name="shopping_bag", col=(0.72, 0.58, 0.40)):
    b = B(); b.box((0, 0, -0.17), (0.26, 0.14, 0.32), col, top=(1.08, 1.1)); b.box((0, 0, -0.01), (0.22, 0.10, 0.03), tuple(c * 0.85 for c in col))
    pts = [(-0.06, 0, -0.01), (-0.07, 0, 0.0), (-0.02, 0, 0.05), (0.02, 0, 0.05), (0.07, 0, 0.0), (0.06, 0, -0.01)]
    b.tube(pts, 0.008, DARK, 4)
    return [b.obj(name)]
def phone():
    b = B(); b.box((0, 0, 0), (0.07, 0.009, 0.15), BLK); b.box((0, 0.0048, 0.0), (0.064, 0.002, 0.142), (0.1, 0.18, 0.3))
    return [b.obj("phone")]
def umbrella():
    b = B(); L = 0.84
    b.cyl((0, 0, 0.02), (0, 0, -0.74), 0.008, 0.008, 5, (0.3, 0.3, 0.32))
    b.cyl((0, 0, -0.16), (0, 0, -0.74), 0.016, 0.034, 8, G, (False, True))   # furled canopy tapering to the tip
    b.cyl((0, 0, 0.02), (0, 0, -0.1), 0.014, 0.014, 6, DARK)                  # handle
    b.cyl((0, 0, -0.74), (0, 0, -L), 0.006, 0.003, 5, (0.3, 0.3, 0.32))
    b.tube([(0, 0, 0.02), (0.03, 0, 0.06), (0.07, 0, 0.04)], 0.012, DARK, 5)
    return [b.obj("umbrella_closed")]
def cane():
    b = B(); b.cyl((0, 0, 0.0), (0, 0, -0.82), 0.015, 0.012, 6, (0.45, 0.3, 0.18)); b.cyl((0, 0, 0.0), (0, 0, 0.0), 0.0, 0.0, 3, DARK, (False, False)) if False else None
    b.tube([(0, 0, 0.0), (0, 0.0, 0.05), (0, -0.04, 0.09), (0, -0.09, 0.07)], 0.014, (0.45, 0.3, 0.18), 6)
    b.cyl((0, 0, -0.8), (0, 0, -0.825), 0.013, 0.013, 6, BLK)
    return [b.obj("cane")]

def stroller():
    """origin = handle centre (where the hands are); pram extends forward (+Y), wheels reach down to z=-HH."""
    HH = 0.88; b = B(); fr = (0.2, 0.2, 0.22)
    b.tube([(-0.2, 0, 0), (0.2, 0, 0)], 0.014, DARK, 5)                                # handle bar
    for sx in (-1, 1):
        b.tube([(sx * 0.2, 0, 0), (sx * 0.2, 0.12, -0.28), (sx * 0.2, 0.55, -0.5)], 0.012, fr, 4)    # side frame
        b.tube([(sx * 0.2, 0.55, -0.5), (sx * 0.2, 0.7, -HH + 0.12)], 0.012, fr, 4)
        b.tube([(sx * 0.2, 0.12, -0.28), (sx * 0.2, 0.0, -HH + 0.13)], 0.012, fr, 4)
        for y, r in ((0.0, 0.13), (0.7, 0.11)):
            b.cyl((sx * 0.22, y, -HH + r), (sx * 0.27, y, -HH + r), r, r, 8, BLK)
    b.box((0, 0.42, -0.4), (0.38, 0.62, 0.14), G, top=(1.12, 1.0))                     # carry cot / seat shell
    b.box((0, 0.56, -0.3), (0.34, 0.34, 0.06), (0.8, 0.78, 0.72))                       # blanket
    b.cyl((0, 0.2, -0.26), (0, 0.5, -0.26), 0.2, 0.2, 6, G, (False, False))              # hood (half-ish tube)
    return [b.obj("stroller")]
def walker():
    """Rollator, origin = midpoint of the two handles (hands), frame extends forward (+Y)."""
    HH = 0.84; b = B(); fr = (0.3, 0.32, 0.36)
    for sx in (-1, 1):
        x = sx * 0.27
        b.tube([(x, -0.04, 0.0), (x, 0.05, 0.0)], 0.017, DARK, 6)                       # grip
        b.tube([(x, 0.05, 0.0), (x, 0.12, -HH + 0.1)], 0.013, fr, 4)                     # rear leg
        b.tube([(x, 0.05, 0.0), (x, 0.6, -0.04), (x, 0.62, -HH + 0.1)], 0.013, fr, 4)    # top bar + front leg
        for y in (0.12, 0.62): b.cyl((x, y, -HH + 0.08), (x + sx * 0.02, y, -HH + 0.08), 0.08, 0.08, 6, BLK)
    b.tube([(-0.27, 0.12, -0.4), (0.27, 0.12, -0.4)], 0.012, fr, 4)
    b.box((0, 0.35, -0.38), (0.4, 0.26, 0.03), (0.55, 0.15, 0.15))                       # seat
    b.box((0, 0.62, -0.28), (0.4, 0.03, 0.2), (0.25, 0.25, 0.3))                         # basket front
    return [b.obj("walker")]

def dog(name, s, body_col, belly_col, ear_col, snout_col):
    """Quadruped, origin on the ground under the body centre, faces +Y. Legs/tail are separate nodes with a looping 'walk'."""
    clear(); H = 0.36 * s
    def mk():
        return B()
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    b = B()
    b.box((0, 0, H + 0.02 * s), (0.17 * s, 0.46 * s, 0.17 * s), body_col, top=(0.9, 0.95))              # torso
    b.box((0, 0.02 * s, H - 0.04 * s), (0.15 * s, 0.34 * s, 0.05 * s), belly_col)
    b.box((0, 0.27 * s, H + 0.12 * s), (0.1 * s, 0.14 * s, 0.15 * s), body_col, top=(0.9, 0.8))          # neck
    b.box((0, 0.35 * s, H + 0.17 * s), (0.12 * s, 0.14 * s, 0.12 * s), body_col)                         # head
    b.box((0, 0.45 * s, H + 0.145 * s), (0.065 * s, 0.1 * s, 0.065 * s), snout_col, top=(0.9, 0.9))      # snout
    b.box((0, 0.5 * s, H + 0.16 * s), (0.03 * s, 0.015 * s, 0.025 * s), BLK)                              # nose
    for sx in (-1, 1): b.box((sx * 0.065 * s, 0.32 * s, H + 0.2 * s), (0.03 * s, 0.07 * s, 0.09 * s), ear_col)
    body = b.obj(name + "_body", root)
    parts = [root, body]; legs = []
    for nm, x, y in (("fl", 1, 0.17), ("fr", -1, 0.17), ("bl", 1, -0.17), ("br", -1, -0.17)):
        lb = B(); lb.box((0, 0, -0.1 * s * 1.4), (0.045 * s, 0.05 * s, 0.2 * s * 1.4), body_col, top=(1.15, 1.1))
        lb.box((0, 0.008 * s, -H * 0.5 - 0.145 * s), (0.05 * s, 0.07 * s, 0.03 * s), belly_col)
        o = lb.obj(f"{name}_leg_{nm}", root, (x * 0.065 * s, y * s, H - 0.02 * s)); parts.append(o); legs.append((o, nm))
    tb = B(); tb.box((0, -0.07 * s, 0.0), (0.03 * s, 0.17 * s, 0.03 * s), body_col, top=(0.8, 0.8), rot=Matrix.Rotation(0.5, 3, "X"))
    tail = tb.obj(name + "_tail", root, (0, -0.22 * s, H + 0.08 * s)); parts.append(tail)
    # animation: 24 frames @24fps (1 s) loop; diagonal gait
    sc = bpy.context.scene; sc.render.fps = 24; sc.frame_start = 1; sc.frame_end = 25
    ph = {"fl": 0, "br": 0, "fr": math.pi, "bl": math.pi}
    for o, nm in legs:
        o.rotation_mode = "XYZ"
        for f in range(1, 26):
            a = 0.55 * math.sin((f - 1) / 24 * 2 * math.pi + ph[nm]); o.rotation_euler = (a, 0, 0); o.keyframe_insert("rotation_euler", frame=f)
    for f in range(1, 26):
        w = math.sin((f - 1) / 24 * 2 * math.pi * 2) * 0.5
        tail.rotation_euler = (0, 0, w); tail.keyframe_insert("rotation_euler", frame=f)
        root.location = (0, 0, 0.012 * s * abs(math.sin((f - 1) / 24 * 2 * math.pi))); root.keyframe_insert("location", frame=f)
    root.animation_data.action.name = "walk" if root.animation_data else None
    for o in parts:
        if o.animation_data and o.animation_data.action: o.animation_data.action.name = f"walk_{o.name}"
    return parts
def leash(name, dx, dy, dz):
    b = B(); pts = [(0, 0, 0)]
    for i in range(1, 7):
        t = i / 6; pts.append((dx * t, dy * t, dz * t - 0.09 * math.sin(math.pi * t) + 0.0))
    b.tube(pts, 0.004, (0.55, 0.12, 0.1), 3); return [b.obj(name)]

for name, fn in (("backpack", backpack), ("shoulder_bag", shoulder_bag), ("tote_bag", tote_bag), ("shopping_bag", shopping_bag),
                 ("phone", phone), ("umbrella_closed", umbrella), ("cane", cane), ("stroller", stroller), ("walker", walker)):
    clear(); finish(name, fn())
clear(); finish("shopping_bag_green", shopping_bag("shopping_bag_green", (0.3, 0.5, 0.45)))
for name, s, cols in (("dog_small", 0.62, ((0.78, 0.62, 0.4), (0.92, 0.9, 0.84), (0.45, 0.3, 0.18), (0.2, 0.15, 0.1))),
                      ("dog_medium", 1.0, ((0.25, 0.2, 0.16), (0.3, 0.25, 0.2), (0.12, 0.1, 0.08), (0.35, 0.28, 0.22)))):
    parts = dog(name, s, *cols); finish(name, parts, anim=True)
clear(); finish("leash_small", leash("leash_small", -0.28, 0.7, -0.53))
clear(); finish("leash_medium", leash("leash_medium", -0.38, 0.9, -0.35))
json.dump(INFO, open(f"{ROOT}/data/cache/humans/accessories_info.json", "w"))
