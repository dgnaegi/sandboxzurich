"""blender -b -P render_sheet.py -- outdir : renders side + 3/4 views of assembled vehicles from the exported GLBs."""
import sys, os, json, math, bpy
from mathutils import Vector
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../web/public/models/transit'))
dst = sys.argv[sys.argv.index('--')+1]; os.makedirs(dst, exist_ok=True)
man = json.load(open(os.path.join(OUT, 'manifest.json')))
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_shadows = True; sh.shadow_intensity = .35; sh.show_cavity = False
sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0.55
sc.render.resolution_x, sc.render.resolution_y = 1000, 340
sc.world = bpy.data.worlds.new('w'); sc.world.color = (.75, .85, .95)
def build(vname):
    v = man['vehicles'][vname]; objs = []
    for e in v['sequence']:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, e['file']))
        new = [o for o in bpy.data.objects if o not in before]
        root = bpy.data.objects.new('r', None); bpy.context.collection.objects.link(root)
        for o in new:
            if o.parent is None: o.parent = root
        # blender coords: three z -> -y
        root.location = (0, -(e['z_center_from_front'] - v['length']/2), 0)
        root.rotation_euler = (0, 0, math.pi if e['rotateY180'] else 0)
        objs.append(root)
    return v
def ground():
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.01)); g = bpy.context.object
    me = g.data; ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    for d in ca.data: d.color = (.12, .12, .13, 1)
def cam(loc, tgt, ortho=None, lens=50):
    c = bpy.data.cameras.new('c'); o = bpy.data.objects.new('c', c); bpy.context.collection.objects.link(o)
    o.location = loc; d = Vector(tgt)-Vector(loc); o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho: c.type = 'ORTHO'; c.ortho_scale = ortho
    else: c.lens = lens
    sc.camera = o; return o
for vname in man['vehicles']:
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    v = build(vname); ground(); L = v['length']
    # side (view from +x), front at left? three front=-z => blender +y; camera at +x looking -x : front on right
    cam((60, 0, 1.7), (0, 0, 1.7), ortho=L*1.08); sc.render.filepath = f'{dst}/{vname}_side.png'; bpy.ops.render.render(write_still=True)
    h = max(L*0.5, 12)
    cam((9, (L/2+10), 2.4), (0, L*0.12, 1.5), lens=40)  # front-right three-quarter
    sc.render.filepath = f'{dst}/{vname}_34.png'; bpy.ops.render.render(write_still=True)
    cam((-(5.5), (L/2+8), 1.9), (0, (L/2-2), 1.6), lens=40); sc.render.filepath = f'{dst}/{vname}_front.png'; bpy.ops.render.render(write_still=True)
