"""Render bikes. blender -b -P pipeline/bikes/render_sheet.py -- sheet <out.jpg> [az] [types,..]
                                                         or  -- each <outdir> [az] [types,..]   (one png per type, for the compare sheet)"""
import bpy, json, math, sys
R = "/Users/danielgnagi/sandboxzurich"; D = f"{R}/web/public/models/bikes"
a = sys.argv[sys.argv.index("--") + 1:]
MODE, OUT = a[0], a[1]; AZ = float(a[2]) if len(a) > 2 else 125.0; ONLY = a[3].split(",") if len(a) > 3 else None
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
man = [e for e in json.load(open(f"{D}/manifest.json")) if not e["type"].endswith("_lean") and e["type"] != "rack"]
if ONLY: man = [e for e in man if e["type"] in ONLY]; man.sort(key=lambda e: ONLY.index(e["type"]))
def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def rgb(h): return [lin(((h >> s) & 255) / 255) for s in (16, 8, 0)]
PAL = [0xa3171f, 0x2d5d9c, 0xe8e8e4, 0x2f6b4a, 0x6b7076, 0xf0b800, 0x15171a, 0x3e8f96, 0xc7603a, 0x8a4f8f]
def setup_scene():
    sc = bpy.context.scene; sc.render.engine = "BLENDER_EEVEE"
    sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (.64, .70, .78, 1); sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.2
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.002)); g = bpy.context.object
    gm = bpy.data.materials.new("g"); gm.use_nodes = True; gm.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (.20, .20, .21, 1); g.data.materials.append(gm)
    sun = bpy.data.lights.new("s", "SUN"); sun.energy = 4.0; so = bpy.data.objects.new("s", sun); sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35)); return sc
def load(e, i, loc, az):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f"{D}/{e['file']}")
    new = [o for o in bpy.data.objects if o not in before]; tint = rgb(PAL[i % len(PAL)])
    img = None
    for o in new:
        if o.type != "MESH": continue
        me = o.data
        for mt in me.materials:
            if mt and mt.use_nodes:
                for n in mt.node_tree.nodes:
                    if n.type == "TEX_IMAGE": img = n.image
        ca = me.color_attributes[0]; pa = me.attributes.get("_PAINT")
        for k in range(len(ca.data)):
            vi = k if ca.domain == "POINT" else me.loops[k].vertex_index
            p = pa.data[vi if pa.domain == "POINT" else k].value
            c = list(ca.data[k].color); ca.data[k].color = [c[0] * (tint[0] if p > .5 else 1), c[1] * (tint[1] if p > .5 else 1), c[2] * (tint[2] if p > .5 else 1), 1]
        mat = bpy.data.materials.new("bm"); mat.use_nodes = True; nt = mat.node_tree; b = nt.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = .5; b.inputs["Metallic"].default_value = .1
        vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = ca.name
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = "Linear"
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1
        uv = nt.nodes.new("ShaderNodeUVMap"); nt.links.new(uv.outputs[0], tx.inputs[0])
        nt.links.new(vc.outputs["Color"], mul.inputs[6]); nt.links.new(tx.outputs["Color"], mul.inputs[7]); nt.links.new(mul.outputs[2], b.inputs["Base Color"])
        # alpha cutoff 0.3 like the game: step via math node
        gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = .3
        nt.links.new(tx.outputs["Alpha"], gt.inputs[0]); nt.links.new(gt.outputs[0], b.inputs["Alpha"])
        mat.surface_render_method = "DITHERED"; mat.use_backface_culling = False
        me.materials.clear(); me.materials.append(mat); me.color_attributes.active_color = ca
    for o in new:
        if o.parent is None: o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, math.radians(az)); o.location = loc
def camera(sc, cx, cy, scale, el=22, d=40, side_az=0):
    cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; cam.ortho_scale = scale; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
    e = math.radians(el); co.location = (cx, cy - d * math.cos(e), d * math.sin(e) + .5); co.rotation_euler = (math.radians(90) - e, 0, 0)
sc = setup_scene(); sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 90
if MODE == "sheet":
    cols = 4; sx, sy = 2.5, 2.6; rows = (len(man) + cols - 1) // cols
    for i, e in enumerate(man): load(e, i, ((i % cols) * sx, -(i // cols) * sy, 0), AZ)
    camera(sc, (cols - 1) * sx / 2, -(rows - 1) * sy / 2 - .6, cols * sx * 0.98)
    sc.render.resolution_x = 1600; sc.render.resolution_y = int(1600 * rows * sy * .74 / (cols * sx)) + 20
    sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
else:
    import os; os.makedirs(OUT, exist_ok=True); sc.render.image_settings.file_format = "PNG"
    for i, e in enumerate(man):
        for o in [o for o in bpy.data.objects if o.type != "LIGHT" and o.name != "Plane" and o.type != "CAMERA"]: o.hide_render = True
        for o in list(bpy.data.objects):
            if o.type == "CAMERA": bpy.data.objects.remove(o)
        before = set(bpy.data.objects); load(e, i, (0, 0, 0), AZ)
        camera(sc, 0, 0, 3.0, el=8); sc.render.resolution_x = 900; sc.render.resolution_y = 600
        sc.render.filepath = f"{OUT}/{e['type']}.png"; bpy.ops.render.render(write_still=True)
        for o in [o for o in bpy.data.objects if o not in before and o.type != "CAMERA"]: o.hide_render = True
print("SHEET", OUT)
