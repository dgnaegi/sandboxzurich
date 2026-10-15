"""Contact sheet: blender -b -P pipeline/trees/render_sheet.py"""
import bpy, json, math, os
from mathutils import Vector
R = "/Users/danielgnagi/sandboxzurich"
man = json.load(open(f"{R}/web/public/models/trees/manifest.json"))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
cols = 5; rows = (len(man) + cols - 1) // cols
for i, m in enumerate(man):
    bpy.ops.import_scene.gltf(filepath=f"{R}/web/public/models/trees/{m['file']}")
    for o in bpy.context.selected_objects:
        if o.parent is None:
            o.location = ((i % cols) * 1.15, 0, -(i // cols) * 1.15)
    # ground
for mat in bpy.data.materials:
    mat.use_backface_culling = False
    if hasattr(mat, "surface_render_method"): mat.surface_render_method = 'DITHERED'
bpy.ops.mesh.primitive_plane_add(size=1, location=(cols * .55, -rows * .6, -0.001)); g = bpy.context.object
g.scale = (cols * 1.3, rows * 1.5, 1); g.hide_render = True
gm = bpy.data.materials.new("g"); gm.diffuse_color = (.35, .36, .33, 1); g.data.materials.append(gm)
sun = bpy.data.lights.new("s", 'SUN'); sun.energy = 3.5; so = bpy.data.objects.new("s", sun)
so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30)); sc.collection.objects.link(so)
w = bpy.data.worlds.new("w"); w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (.55, .72, .95, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
sc.world = w
cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.ortho_scale = cols * 1.15 + .1
co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
tgt = bpy.data.objects.new("t", None); sc.collection.objects.link(tgt)
tgt.location = ((cols - 1) * .575, 0, -(rows - 1) * .575 + .5 + 0.0 + (rows - 1) * 1.15 * 0 )
co.location = ((cols - 1) * .575, -12, tgt.location.z)
tc = co.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = 1600; sc.render.resolution_y = int(1600 * (rows * 1.15 + .1) / (cols * 1.15 + .1))
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 88
sc.render.filepath = f"{R}/preview/trees_sheet.jpg"
bpy.ops.render.render(write_still=True)
