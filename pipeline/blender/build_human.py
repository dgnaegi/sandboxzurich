"""Build ONE game-ready human GLB (1 SkinnedMesh, 1 material/atlas, idle/walk/run).

    blender -b -P pipeline/blender/build_human.py -- <id>     # id = player | npc_00 .. npc_15
Driven by pipeline/blender/build_humans.sh (one Blender process per figure).
MakeHuman/MPFB assets are CC0.
"""
import sys, os, math, random, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/danielgnagi/gta6/src/blender")
import bpy
from mathutils import Vector
import humans as Hm
import human_specs as SP
_orig_acc = Hm.add_accessories
# only hats survive (skinned to the head bone below); bags/glasses/earrings stay out: one clean mesh
def _acc(rig, body, p, coll):
    """Own beanie/cap (the template hats are too small for hair volume), sized from the real head+hair vertices."""
    if not p.get("hat"): return
    import bmesh
    from mathutils import Matrix
    rig.data.pose_position = "REST"; bpy.context.view_layer.update()   # hat is bone-parented: build it at rest pose
    h0 = rig.data.bones["head"].head_local; dg = bpy.context.evaluated_depsgraph_get(); vs = []
    for c in rig.children:
        n = c.name.lower()
        if c.type != "MESH" or any(k in n for k in ("suit", "shoes", "high-poly", "low-poly", "eyelash", "eyebrow", "teeth", "tongue")): continue
        e = c.evaluated_get(dg); m = e.to_mesh(); vs += [c.matrix_world @ v.co for v in m.vertices]; e.to_mesh_clear()
    vs = [v for v in vs if v.z > h0.z - 0.02 and abs(v.x) < 0.2 and abs(v.y - h0.y) < 0.25]
    top = max(v.z for v in vs); up = [v for v in vs if v.z > top - 0.14]
    ymin, ymax = min(v.y for v in up), max(v.y for v in up); cy = (ymin + ymax) / 2; ry = (ymax - ymin) / 2; rx = max(abs(v.x) for v in up)
    z0 = top - 0.092; k = 0.014; bm = bmesh.new(); col = p["hat_col"]
    if p["hat"] == "beanie":
        Hm.lathe(bm, [(z0 - 0.012, rx + k, ry + k, 0, cy), (z0 + 0.03, rx + k + 0.004, ry + k + 0.004, 0, cy), (top - 0.03, rx + k, ry + k, 0, cy),
                      (top + 0.012, rx * 0.8, ry * 0.8, 0, cy), (top + 0.034, rx * 0.4, ry * 0.4, 0, cy), (top + 0.04, 0.012, 0.012, 0, cy)], 20)
        rough = 0.95
    else:
        Hm.lathe(bm, [(z0 + 0.0, rx + k, ry + k, 0, cy), (top - 0.03, rx + k, ry + k, 0, cy), (top + 0.01, rx * 0.8, ry * 0.8, 0, cy), (top + 0.028, rx * 0.35, ry * 0.35, 0, cy), (top + 0.032, 0.01, 0.01, 0, cy)], 20)
        bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, cy - ry - k - 0.04, z0 + 0.012)) @ Matrix.Rotation(0.18, 4, "X") @ Matrix.Diagonal((rx * 1.6, 0.1, 0.008, 1)))
        rough = 0.8
    o = Hm.mesh_obj(rig.name + "_hat", bm, Hm.col_mat("hat", col, rough), coll); Hm.parent_to_bone(o, rig, "head")
Hm.add_accessories = _acc

ROOT = "/Users/danielgnagi/sandboxzurich"
OUT = f"{ROOT}/web/public/models/humans"
CACHE = f"{ROOT}/data/cache/humans"
FID = sys.argv[sys.argv.index("--") + 1]
CLEAN = f"{CACHE}/clean"
_orig_tint = Hm.tint_material
def _tint(mat, swap=None, **kw):
    """Swap the MakeHuman-logo diffuse for the logo-free (or recoloured) copy, then tint as before."""
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image and "_diffuse" in n.image.filepath:
            base = os.path.basename(n.image.filepath).replace("_diffuse.png", "")
            path = swap or f"{CLEAN}/_logo_{base}.png"
            if os.path.exists(path): n.image = bpy.data.images.load(path, check_existing=True)
    if kw: _orig_tint(mat, **kw)
Hm.tint_material = _tint

# ---------------------------------------------------------------- specs
# id: (sex, ageclass, race, seed)   Zürich mix: mostly European, some diversity, many age groups
AGE = {"young": (0.42, 0.52), "mid": (0.62, 0.70), "old": (0.85, 0.95)}
NPCS = [
    ("f", "young", "caucasian", 101), ("m", "young", "caucasian", 102), ("f", "mid", "caucasian", 103), ("m", "mid", "caucasian", 104),
    ("f", "old", "caucasian", 105), ("m", "old", "caucasian", 106), ("m", "young", "african", 107), ("f", "young", "asian", 108),
    ("f", "mid", "african", 109), ("m", "mid", "asian", 110), ("f", "young", "caucasian", 111), ("m", "young", "caucasian", 112),
    ("m", "old", "caucasian", 113), ("f", "old", "asian", 114), ("f", "mid", "caucasian", 115), ("m", "mid", "caucasian", 116),
]
OUTF_F = ["female_casualsuit01", "female_casualsuit02", "female_elegantsuit01", "female_sportsuit01", "male_casualsuit01", "male_casualsuit03", "male_casualsuit05"]
OUTF_M = ["male_casualsuit01", "male_casualsuit02", "male_casualsuit03", "male_casualsuit04", "male_casualsuit05", "male_casualsuit06", "male_worksuit01", "male_elegantsuit01"]

def npc_params(idx):
    sex, ac, race, seed = NPCS[idx]
    r = random.Random(seed * 7)
    p = Hm.random_npc(seed, sex=sex)
    g = "female" if sex == "f" else "male"
    cls = {"young": "young", "mid": "middleage", "old": "old"}[ac]
    skin = f"{cls}_{race}_{g}"
    p["skin"] = f"{skin}/{skin}.mhmat"
    p["race"] = {"caucasian": (0.05, 0.9, 0.05), "african": (0.05, 0.1, 0.85), "asian": (0.85, 0.1, 0.05)}[race]
    p["age"] = r.uniform(*AGE[ac])
    hairs = (["long01", "bob01", "bob02", "ponytail01", "braid01"] if sex == "f" else ["short01", "short02", "short03", "short04", None])
    if race == "african": hairs = hairs + ["afro01"] * 2
    if ac == "old" and sex == "m": hairs = ["short01", "short03", None, None]
    h = r.choice(hairs)
    p["hair"] = f"{h}/{h}.mhclo" if h else None
    cols = [(0.08, 0.06, 0.05), (0.3, 0.2, 0.12), (0.55, 0.4, 0.25), (0.8, 0.68, 0.45), (0.6, 0.25, 0.12)]
    if race != "caucasian": cols = cols[:2]
    p["hair_tint"] = (0.62, 0.62, 0.62) if ac == "old" else r.choice(cols)
    o = r.choice(OUTF_F if sex == "f" else OUTF_M)
    if ac == "old": o = r.choice(["male_casualsuit01", "male_casualsuit03", "female_elegantsuit01"] if sex == "f" else ["male_casualsuit03", "male_elegantsuit01", "male_casualsuit06"])
    # muted, city-like clothes colours
    p["clothes"][0] = (f"{o}/{o}.mhclo", dict(hue=r.random(), sat=r.uniform(0.3, 1.1), val=r.uniform(0.6, 1.0)))
    if ac == "old": p["weight"] = r.uniform(0.45, 0.65); p["muscle"] = r.uniform(0.3, 0.45)
    p["sunglasses"] = False; p["bag"] = None; p["hat"] = None; p["glasses"] = False
    return p, dict(sex=sex, age=ac)

def new_params(idx):
    sp = SP.SPECS[idx - SP.FIRST]; r = random.Random(sp["seed"]); sex = sp["sex"]
    p = Hm.random_npc(sp["seed"], sex=sex); g = "female" if sex == "f" else "male"; ac = sp["ac"]
    cls = {"child": "young", "young": "young", "mid": "middleage", "old": "old"}[ac]
    skin = f"{cls}_{sp['skin']}_{g}"; p["skin"] = f"{skin}/{skin}.mhmat"; p["race"] = sp["race"]
    p["age"] = sp.get("age") or {"young": r.uniform(0.42, 0.58), "mid": r.uniform(0.62, 0.70), "old": r.uniform(0.85, 0.95)}[ac]
    h = sp["hair"]; p["hair"] = f"{h}/{h}.mhclo" if h else None; p["hair_tint"] = SP.HAIR[sp["hc"]]
    o = sp["outfit"]; swap = f"{CLEAN}/npc_{idx:02d}_{o}.png"
    p["clothes"] = [(f"{o}/{o}.mhclo", dict(swap=swap)), (f"shoes0{sp['shoe']}/shoes0{sp['shoe']}.mhclo", None)]
    if ac == "old": p["weight"] = r.uniform(0.4, 0.6); p["muscle"] = r.uniform(0.3, 0.42); p["height"] = r.uniform(0.3, 0.5)
    if ac == "child": p.update(weight=r.uniform(0.35, 0.5), muscle=0.35, height=0.5, proportions=0.5, cup=0.3)
    p["sunglasses"] = False; p["bag"] = None; p["glasses"] = False
    p["hat"] = sp.get("hat"); p["hat_col"] = SP.C[sp["hatc"]] if sp.get("hat") else None
    return p, dict(sex=sex, age=ac, props=sp.get("props", []))

if FID == "player":
    P = dict(Hm.NICI); P.update(hat=None, sunglasses=False, bag=None, earrings=False)
    META = dict(sex="f", age="young"); TRIS, TEX = 12000, 1024
else:
    _i = int(FID.split("_")[1])
    if _i < SP.FIRST: P, META = npc_params(_i); TRIS, TEX = 4000, 512
    else: P, META = new_params(_i); TRIS, TEX = (3400 if META["age"] == "child" else 3850), 512

# ---------------------------------------------------------------- build
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.name == "Cube": bpy.data.objects.remove(o)
rig = Hm.make_human(FID, P)
bpy.context.view_layer.update()
parts = [o for o in rig.children if o.type == "MESH"]
for o in parts:
    if o.data.shape_keys:
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
for o in parts:
    for m in list(o.modifiers):
        if m.type == "MASK": 
            bpy.context.view_layer.objects.active = o
            # apply mask: move on top so apply works, armature is disabled temporarily
            arm = [x for x in o.modifiers if x.type == "ARMATURE"]
            for a in arm: a.show_viewport = False
            try: bpy.ops.object.modifier_apply(modifier=m.name)
            except Exception as e: print("mask apply fail", e)
            for a in arm: a.show_viewport = True
parts = [o for o in rig.children if o.type == "MESH"]
for o in parts: print("PART", o.name, sum(len(q.vertices) - 2 for q in o.data.polygons))

def tris(o): return sum(len(q.vertices) - 2 for q in o.data.polygons)
# high-poly source: everything. low-poly copy: skip lashes/brows (baked from high), decimate per part.
def kind(o):
    n = o.name.lower().replace("low_", "")
    if "eyelash" in n or "eyebrow" in n: return "skip"
    if "high-poly" in n or "eye" in n: return "eyes"
    if "shoes" in n: return "shoes"
    if "long" in n or "bob" in n or "ponytail" in n or "braid" in n or "short" in n or "afro" in n: return "hair"
    if n == "human": return "body"
    return "cloth"
WEIGHT = {"body": 0.38, "cloth": 0.25, "hair": 0.17, "shoes": 0.10, "eyes": 0.04}
lows = []
present = {kind(o) for o in parts} - {"skip"}
wsum = sum(WEIGHT[k] for k in present)
for o in parts:
    k = kind(o)
    if k == "skip": continue
    c = o.copy(); c.data = o.data.copy(); bpy.context.scene.collection.objects.link(c)
    c.name = "low_" + o.name
    if o.name.endswith("_hat"):   # bone-parented prop -> skinned to the head bone
        mw = c.matrix_world.copy(); c.parent = rig; c.parent_type = "OBJECT"; c.matrix_world = mw
        vg = c.vertex_groups.new(name="head"); vg.add(list(range(len(c.data.vertices))), 1.0, "REPLACE")
        c.modifiers.new("Armature", "ARMATURE").object = rig
    budget = TRIS * WEIGHT[k] / wsum
    t0 = tris(c)
    if t0 > budget:
        m = c.modifiers.new("dec", "DECIMATE"); m.ratio = budget / t0
        # keep armature modifier AFTER decimate: apply decimate first (move to index 0)
        bpy.context.view_layer.objects.active = c
        bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
        for x in c.modifiers:
            if x.type == "ARMATURE": x.show_viewport = False
        bpy.ops.object.modifier_apply(modifier=m.name)
        for x in c.modifiers:
            if x.type == "ARMATURE": x.show_viewport = True
    lows.append(c)

bpy.ops.object.select_all(action="DESELECT")
for c in lows: c.select_set(True)
body_low = [c for c in lows if kind(c) == "body"][0]
bpy.context.view_layer.objects.active = body_low
bpy.ops.object.join()
low = bpy.context.view_layer.objects.active
low.name = FID + "_mesh"
# drop old UVs/materials: single new UV + single material
while len(low.data.uv_layers) > 0: low.data.uv_layers.remove(low.data.uv_layers[0])
low.data.materials.clear()
# merge doubles lightly, limit weights
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.remove_doubles(threshold=0.0005)
bpy.ops.mesh.quads_convert_to_tris() if False else None
bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
bpy.ops.mesh.quads_convert_to_tris(); 
bpy.ops.mesh.select_all(action="SELECT")
uv = low.data.uv_layers.new(name="UVMap")
bpy.ops.uv.smart_project(angle_limit=math.radians(85), island_margin=0.003, area_weight=0.6)
bpy.ops.uv.pack_islands(margin=0.004)
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.object.vertex_group_limit_total(limit=4)
print("LOW tris", tris(low), "verts", len(low.data.vertices))

# ---------------------------------------------------------------- bake
img = bpy.data.images.new("atlas", TEX, TEX, alpha=False)
img.generated_color = (0.5, 0.5, 0.5, 1)
mat = bpy.data.materials.new(FID + "_mat"); mat.use_nodes = True
nt = mat.node_tree; tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img
bsdf = nt.nodes["Principled BSDF"]; nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.85
bsdf.inputs["Specular IOR Level"].default_value = 0.15
nt.nodes.active = tn
low.data.materials.append(mat)

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 4; sc.cycles.use_denoising = False
sc.cycles.bake_type = "DIFFUSE"
sc.render.bake.use_pass_direct = False; sc.render.bake.use_pass_indirect = False; sc.render.bake.use_pass_color = True
sc.render.bake.use_selected_to_active = True
sc.render.bake.cage_extrusion = 0.012; sc.render.bake.max_ray_distance = 0.04
sc.render.bake.margin = 6; sc.render.bake.margin_type = "EXTEND"
# high-poly sources must have no armature deform issues: rest pose
rig.data.pose_position = "REST"
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
low.select_set(True); bpy.context.view_layer.objects.active = low
bpy.ops.object.bake(type="DIFFUSE")
os.makedirs(CACHE, exist_ok=True)
img.filepath_raw = f"{CACHE}/{FID}_atlas.png"; img.file_format = "PNG"; img.save()

# remove high-poly parts
for o in parts: bpy.data.objects.remove(o)
rig.data.pose_position = "POSE"

# ---------------------------------------------------------------- ground / orientation
bpy.context.view_layer.update()
minz = min((low.matrix_world @ v.co).z for v in low.data.vertices)
print("minz", minz)
META["height"] = round(max((low.matrix_world @ v.co).z for v in low.data.vertices) - minz, 3)
for v in low.data.vertices: v.co.z -= minz          # feet at z=0 (mesh space; rig is identity)
# shift rig bones too: easier to move rig object up and mesh stays child-less... instead move both via rig.location
for v in low.data.vertices: v.co.z += minz
rig.location = (0, 0, -minz)

# ---------------------------------------------------------------- animations
FPS = 30
bpy.context.scene.render.fps = 30
Pb = rig.pose.bones
FEET = ["foot_l", "foot_r", "ball_l", "ball_r"]
def foot_min():
    bpy.context.view_layer.update()
    return min(min(Pb[b].head.z, Pb[b].tail.z) for b in FEET)
for pb in Pb: pb.rotation_mode = "QUATERNION"
Hm.POSES["idle"](Pb, 0.0); rest_foot = None
for pb in Pb: pb.rotation_quaternion = (1, 0, 0, 0)
Hm._st(Pb).clear()
rest_foot = foot_min()
pel = Pb["pelvis"]; pel_inv = pel.bone.matrix_local.to_3x3().inverted()

def idle_fn(P, t):
    Hm._base(P, t, breathe=True)
    b = math.sin(t * 2 * math.pi / 3.2)
    Hm.R(P, "head", x=-2 + 1.2 * b, z=3 * math.sin(t * 2 * math.pi / 3.2 * 1.0))
    return 0
OLD = META["age"] == "old"; KID = META["age"] == "child"
def hunch(fn, neck=16, spine=6):
    def f(P, t):
        r = fn(P, t); Hm.R(P, "spine_02", x=spine + 3); Hm.R(P, "neck_01", x=neck); Hm.R(P, "head", x=-4); return r
    return f
def gait(period, thigh, knee, sw, el, lean, tw, sway):
    return lambda P, t: Hm._gait(P, t, period, thigh, knee, sw, el, lean, tw, sway)
def phone_fn(P, t):
    Hm.POSES["phone"](P, 0.0); Hm._base(P, t)
    Hm.arm(P, "r", (0.12, 0.35, -1), (-0.42, 0.75, 0.62), hand=(-15, 0, 0)); Hm.arm(P, "l", (0.14, 0.3, -1), (-0.5, 0.72, 0.45))
    Hm.R(P, "neck_01", x=12); Hm.R(P, "head", x=18 + 1.5 * math.sin(t * 2 * math.pi / 3.2)); return 0
if OLD:
    idle_fn = hunch(idle_fn, 14, 5)
    walk_fn = hunch(gait(1.08, 20, 40, 0.22, 0.3, 5, 4, 2.5), 14, 5)
    slow_fn = hunch(gait(1.5, 13, 26, 0.12, 0.2, 7, 2, 2.5), 18, 8)
else:
    walk_fn = Hm.POSES["walk"]; slow_fn = gait(1.5, 16, 32, 0.16, 0.2, 5, 3, 2.5)
if KID: walk_fn = gait(0.9, 26, 50, 0.4, 0.4, 3, 5, 3)
SPEC = {  # name: (fn, seconds in output, seconds of one source cycle, ground lock)
    "idle": (idle_fn, 3.2, 3.2, False),
    "walk": (walk_fn, 1.0, 1.08, True),
    "run": (Hm.POSES["run"], 0.7, 0.62, True),
}
if FID != "player":
    SPEC["walk_slow"] = (slow_fn, 1.5, 1.5, True)
    SPEC["stand_phone"] = (phone_fn, 3.2, 3.2, False)
ad = rig.animation_data_create()
for name, (fn, dur, src, lock) in SPEC.items():
    n = round(dur * FPS)
    act = bpy.data.actions.new(name); ad.action = act
    for i in range(n + 1):
        t = (i % n) / n * dur
        fn(Pb, t * src / dur)
        pel.location = (0, 0, 0)
        if lock:
            bpy.context.view_layer.update()
            dz = rest_foot - foot_min()
            pel.location = pel_inv @ Vector((0, 0, dz))
        for pb in Pb:
            pb.keyframe_insert("rotation_quaternion", frame=i)
        pel.keyframe_insert("location", frame=i)
    act.use_fake_user = True
    ad.action = None
    for pb in Pb: pb.rotation_quaternion = (1, 0, 0, 0)
    pel.location = (0, 0, 0)
    Hm._st(Pb).clear()
rig.rotation_euler = (0, 0, math.pi)     # MPFB faces -Y; glTF/Three forward is -Z => face +Y in Blender

# ---------------------------------------------------------------- export (texture compressed through JPEG)
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True); low.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(
    filepath=f"{OUT}/{FID}.glb", export_format="GLB", use_selection=True,
    export_image_format="JPEG", export_jpeg_quality=74, export_draco_mesh_compression_enable=False,
    export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
    export_optimize_animation_size=True, export_skins=True, export_def_bones=False,
    export_apply=False, export_yup=True, export_cameras=False, export_lights=False,
    export_extras=False, export_morph=False)
import glb_compact; glb_compact.compact(f"{OUT}/{FID}.glb")
json.dump(META, open(f"{CACHE}/{FID}.json", "w"))
print("DONE", FID, os.path.getsize(f"{OUT}/{FID}.glb") // 1024, "KB")
