"""blender -b -P render_sheet.py : contact sheet of the assembled S-Bahn -> preview/rail_train.jpg"""
import os, json, math, bpy
from mathutils import Vector
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../web/public/models/trains'))
PREV = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../preview'))
man = json.load(open(os.path.join(OUT, 'manifest.json')))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'VERTEX'
sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0.5
sc.world = bpy.data.worlds.new('w'); sc.world.color = (.75, .85, .95)
L = man['car_length']
for i, (m, flip) in enumerate(man['train']):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, man['modules']['sbahn_' + m]['file']))
    root = bpy.data.objects.new('r', None); bpy.context.collection.objects.link(root)
    for o in set(bpy.data.objects) - before:
        if o.parent is None and o is not root: o.parent = root
    root.location = (0, -(i * L + L / 2), 0); root.rotation_euler = (0, 0, math.pi if flip else 0)
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.01))
def cam(loc, tgt, ortho=None):
    c = bpy.data.cameras.new('c'); o = bpy.data.objects.new('c', c); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho: c.type = 'ORTHO'; c.ortho_scale = ortho
    else: c.lens = 40
    sc.camera = o
mid = -L * 2.5
views = [('side', (60, mid, 3), (0, mid, 2.5), 140), ('front', (14, 14, 3.5), (0, -8, 2.2), None), ('rear', (-14, mid * 2 - 14, 4), (0, mid * 2 + 8, 2.2), None)]
os.makedirs(PREV, exist_ok=True)
for n, loc, tgt, o in views:
    cam(loc, tgt, o); sc.render.resolution_x, sc.render.resolution_y = (1600, 400) if o else (800, 500)
    sc.render.filepath = f'/tmp/_rail_{n}.png'; bpy.ops.render.render(write_still=True)
