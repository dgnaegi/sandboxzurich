"""Contact sheet: all cars in different paints, 3/4 view. blender -b -P pipeline/cars/render_sheet.py [-- out.jpg [az_deg]]"""
import bpy, json, math, sys
R = "/Users/danielgnagi/sandboxzurich"
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = args[0] if args else f"{R}/preview/cars_sheet.jpg"
AZ = float(args[1]) if len(args) > 1 else 145.0
ONLY = args[2].split(",") if len(args) > 2 else None
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
man = json.load(open(f"{R}/web/public/models/cars/manifest.json"))
def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def rgb(h): return [lin(((h >> s) & 255) / 255) for s in (16, 8, 0)]
PAL = [0x8c1c22, 0x2d4f7c, 0xe2e2df, 0x24402f, 0x7d8288, 0xf2c200, 0x1a1c20, 0xc8102e]
mat = bpy.data.materials.new("m"); mat.use_nodes = True; nt = mat.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Roughness"].default_value = .45; b.inputs["Metallic"].default_value = .1
vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"; nt.links.new(vc.outputs["Color"], b.inputs["Base Color"])
sx, sy = 5.6, 6.2; i = 0
items = [dict(e, az=AZ) for e in man if not ONLY or e["type"] in ONLY]
if not ONLY: items.append(dict(man[0], az=35.0))   # rear view of the hatch
cols = min(4, len(items))
for e in items:
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=f"{R}/web/public/models/cars/{e['file']}")
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type != "MESH": continue
        me = o.data
        if i == 0: print("ATTRS", [(a.name, a.domain, a.data_type) for a in me.attributes])
        ca = me.color_attributes[0]; pa = me.attributes.get("_PAINT")
        tint = rgb(PAL[i % len(PAL)]); n = len(ca.data)
        for k in range(n):
            p = pa.data[k].value if pa and pa.domain == "CORNER" else (pa.data[me.loops[k].vertex_index].value if pa else 0)
            c = list(ca.data[k].color); ca.data[k].color = [c[0] * (tint[0] if p > .5 else 1), c[1] * (tint[1] if p > .5 else 1), c[2] * (tint[2] if p > .5 else 1), 1]
        me.color_attributes.active_color = ca; me.materials.clear(); me.materials.append(mat)
        # use imported vertex-color layer name
        vc.layer_name = ca.name
    for o in new:
        if o.parent is None:
            o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, math.radians(e['az'])); o.location = ((i % cols) * sx, -(i // cols) * sy, 0)
    i += 1
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.world = bpy.data.worlds.new("w"); sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (.62, .68, .76, 1); sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.1
bpy.ops.mesh.primitive_plane_add(size=80, location=(8, -4, -0.01)); g = bpy.context.object
gm = bpy.data.materials.new("g"); gm.diffuse_color = (.30, .31, .33, 1); gm.use_nodes = True; gm.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (.12, .12, .13, 1); g.data.materials.append(gm)
sun = bpy.data.lights.new("s", "SUN"); sun.energy = 4.0; so = bpy.data.objects.new("s", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
cam = bpy.data.cameras.new("c"); cam.type = "ORTHO"; rows = (len(items) + cols - 1) // cols
cam.ortho_scale = cols * sx * 1.02; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
cx, cy = (cols - 1) * sx / 2, -(rows - 1) * sy / 2 - 0.6
d = 40; el = math.radians(28)
co.location = (cx, cy - d * math.cos(el), d * math.sin(el)); co.rotation_euler = (math.radians(90) - el, 0, 0)
sc.render.resolution_x = 1600; sc.render.resolution_y = int(1600 * (rows * sy * .78 / (cols * sx * 1.02)) + 40)
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 88; sc.render.filepath = OUT
bpy.ops.render.render(write_still=True); print("SHEET", OUT)
