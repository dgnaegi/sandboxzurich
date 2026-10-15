"""blender -b -P build_models.py : builds VBZ vehicle modules -> web/public/models/transit/*.glb + manifest.json"""
import sys, os, json, bpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import geom as G
OUT = os.path.abspath(os.path.join(HERE, '../../web/public/models/transit'))
os.makedirs(OUT, exist_ok=True)

NOSE_TRAM = dict(dz=[0, .45, 1.0, 1.6], sx=[.80, .91, .97, 1.0], back=[.75, .38, .12, 0], drop=[.30, .18, .07, 0],
                 lights=(2, .66), red=.95, glass=.82, display=(3, .55, .12, .88))
NOSE_BUS = dict(dz=[0, .12, .3], sx=[.985, 1.0, 1.0], back=[.35, .1, 0], drop=[.12, .05, 0], lights=(2, .78), red=None, glass=.9, display=(3, .75, .1, .9))
TAIL_BUS = dict(dz=[0, .1, .3], sx=[.985, 1.0, 1.0], back=[.08, .02, 0], drop=[.0, .0, 0])

COBRA = dict(nose_top=G.CBLUE, nose_roof=G.WHITE, hx=1.2, y0=.30, belt=1.05, wtop=2.25, ytop=3.40, r1=.5, rx=.55, blue=G.BLUE, white=G.WHITE, pillar=G.WHITE,
             roof=G.lin((214, 218, 222)), roofbox=G.GREY)
FLEX = dict(frame=G.lin((150, 156, 162)), hx=1.2, y0=.30, belt=1.05, wtop=2.40, ytop=3.40, r1=.38, rx=.5, blue=G.BLUE, white=G.WHITE, pillar=G.WHITE,
            roof=G.lin((205, 210, 216)), roofbox=G.lin((150, 156, 162)))
BUS = dict(hx=1.275, y0=.32, belt=1.0, wtop=2.30, ytop=3.05, r1=.45, rx=.35, blue=G.BLUE, white=G.WHITE, pillar=G.WHITE,
           roof=G.lin((205, 210, 215)), roofbox=G.GREY)

def cobra_ko(): return G.body(COBRA, 7.8, dict(r=[-.2, 2.1], l=[-.2, 2.1][1:]), nose=NOSE_TRAM, bogies=[-1.6])
def cobra_zw(): return G.body(COBRA, 5.2, dict(r=[0], l=[0]), extra=lambda m, P, L: G.roof_boxes(m, P, L, [-1.0], 1.0, .2, 1.8))
def cobra_mi():
    return G.body(COBRA, 10.0, dict(r=[-3.0, 3.0], l=[-3.0, 3.0]), bogies=[0],
                  extra=lambda m, P, L: (G.roof_boxes(m, P, L, [3.3], 1.0, .2, 2.0), G.pantograph(m, P, 0.4)))
def flex_ko(): return G.body(FLEX, 6.9, dict(r=[-.0, 1.9], l=[1.9]), nose=NOSE_TRAM, bogies=[-1.2])
def flex_mi(): return G.body(FLEX, 6.8, dict(r=[0], l=[0]), bogies=[0])
def flex_zw():
    return G.body(FLEX, 4.4, dict(r=[0], l=[0]), extra=lambda m, P, L: (G.roof_boxes(m, P, L, [-1.0], 1.0, .2, 1.4), G.pantograph(m, P, .4)))
def bus_front(): return G.body(BUS, 9.2, dict(r=[-3.0, 0.6], l=[0.6]), nose=NOSE_BUS, bogies=[], wheels_r=.5,
                               extra=lambda m, P, L: (bus_wheels(m, [-2.9, 2.8]), G.roof_boxes(m, P, L, [1.8], 1.4, .18, 2.2)))
def bus_rear(): return G.body(BUS, 8.4, dict(r=[-2.3, 0.6], l=[-2.3]), tail=TAIL_BUS, wheels_r=.5,
                              extra=lambda m, P, L: (bus_wheels(m, [2.3]), G.roof_boxes(m, P, L, [-1.0], 1.4, .18, 2.2), G.trolley_poles(m, 1.6, L/2)))
def bus_wheels(m, zs):
    for z in zs:
        for x0, x1 in ((-1.31, -1.05), (1.05, 1.31)):
            m.wheel(x0, x1, .5, z, .5, G.DARK)
            m.quad([(x0 if x0 < 0 else x1, .5+.5*G.math.sin(a), z+.5*G.math.cos(a)) for a in [i*G.math.pi/4 for i in range(8)]], G.DARK, (0, .5, z)) if False else None
        sx = 1.285
        for s in (-1, 1):
            m.quad([(s*sx, .5+.62*G.math.sin(a), z+.62*G.math.cos(a)) for a in [i*G.math.pi/4 for i in range(8)]], G.DARK, (0, .5, z))
def bus_joint():
    m = G.Mesh(); P = BUS; ref = (0, 1.5, 0); L = 1.1
    zs = [-L/2, -.35, -.18, 0, .18, .35, L/2]; sc = [.93, .93, 1.0, .93, 1.0, .93, .93][:len(zs)]
    sc = [.93, 1.0, .95, 1.0, .95, 1.0, .93]
    rs = [G.ring(P, z, s) for z, s in zip(zs, sc)]
    for a, b in zip(rs, rs[1:]): G.loft(m, a, b, [G.DARK]*6, ref)
    G.cap(m, rs[0], [G.DARK]*6, ref); G.cap(m, rs[-1], [G.DARK]*6, ref)
    return m, []

MODS = {  # name: (builder, length)
    'cobra_kopf': (cobra_ko, 7.8), 'cobra_zwischen': (cobra_zw, 5.2), 'cobra_mittel': (cobra_mi, 10.0),
    'flexity_kopf': (flex_ko, 6.9), 'flexity_mittel': (flex_mi, 6.8), 'flexity_zwischen': (flex_zw, 4.4),
    'trolley_vorne': (bus_front, 9.2), 'trolley_hinten': (bus_rear, 8.4), 'trolley_gelenk': (bus_joint, 1.1)}

def to_blender(name, mesh, disp):
    verts, faces, cols = [], [], []
    for pts, c in mesh.f:
        i0 = len(verts)
        for p in pts: verts.append((p[0], -p[2], p[1]))
        # fan triangulate
        for k in range(1, len(pts)-1): faces.append((i0, i0+k, i0+k+1)); cols.append(c)
    me = bpy.data.meshes.new(name+'_body'); me.from_pydata(verts, [], faces); me.update()
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    for pi, poly in enumerate(me.polygons):
        for li in poly.loop_indices: ca.data[li].color = (*cols[pi], 1.0)
    ob = bpy.data.objects.new('body', me); bpy.context.collection.objects.link(ob)
    mat = bpy.data.materials.new('body'); mat.use_nodes = True; nt = mat.node_tree
    bs = nt.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value = .55
    cn = nt.nodes.new('ShaderNodeVertexColor'); cn.layer_name = 'Col'; nt.links.new(cn.outputs['Color'], bs.inputs['Base Color'])
    me.materials.append(mat); me.shade_flat()
    objs = [ob]
    if disp:
        v = [(p[0], -p[2], p[1]) for p in disp]
        dm = bpy.data.meshes.new(name+'_display'); dm.from_pydata(v, [], [(0, 1, 2, 3)]); dm.update()
        uv = dm.uv_layers.new(name='UVMap'); uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
        for li, loop in enumerate(dm.polygons[0].loop_indices): uv.data[loop].uv = uvs[li]
        dc = dm.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        for li in range(4): dc.data[li].color = (.3, .14, .0, 1)
        do = bpy.data.objects.new('display', dm); bpy.context.collection.objects.link(do)
        dmat = bpy.data.materials.new('display'); dmat.use_nodes = True
        db = dmat.node_tree.nodes['Principled BSDF']; db.inputs['Base Color'].default_value = (.03, .03, .04, 1); db.inputs['Roughness'].default_value = .4
        dm.materials.append(dmat); objs.append(do)
        # ensure display quad faces outward (-z/front): flip if normal points to +z side
        n = dm.polygons[0].normal
        if n[1] > 0: dm.flip_normals() if hasattr(dm, 'flip_normals') else None
    return objs

def clear():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)

if __name__ == '__main__':
    manifest = {'units': 'm', 'front': '-Z', 'up': '+Y', 'origin': 'module centre, rail top (y=0)',
                'display': 'material "display" on node "display": UV 0..1, aspect ~3.7:1 (front destination sign, sits on sloped cap)', 'modules': {}}
    for name, (fn, L) in MODS.items():
        clear(); mesh, disp = fn(); objs = to_blender(name, mesh, disp)
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name+'.glb'), export_format='GLB', use_selection=True,
                                  export_yup=True, export_attributes=True, export_materials='EXPORT')
        manifest['modules'][name] = {'file': name+'.glb', 'length': L, 'triangles': mesh.tris(), 'has_display': bool(disp)}
        print(name, mesh.tris(), 'tris')
    S = lambda n: manifest['modules'][n]['length']
    def seq(parts):
        out, z = [], 0.0
        for n, flip in parts:
            L = S(n); out.append({'module': n, 'file': n+'.glb', 'rotateY180': flip, 'z_center_from_front': round(z+L/2, 3)}); z += L
        return out, round(z, 3)
    def veh(parts, extra):
        s, L = seq(parts); d = dict(length=L, sequence=s, joints_z_from_front=[round(e['z_center_from_front']+S(e['module'])/2, 3) for e in s[:-1]]); d.update(extra); return d
    manifest['vehicles'] = {
        'tram_cobra': veh([('cobra_kopf', 0), ('cobra_zwischen', 0), ('cobra_mittel', 0), ('cobra_zwischen', 0), ('cobra_kopf', 1)],
            {'bogie_z_local': {'cobra_kopf': [-1.6], 'cobra_mittel': [0.0]}, 'note': 'rotateY180 modules: bogie z sign flips; pantograph head y=5.45 on cobra_mittel; line 8 / Glattal'}),
        'tram_flexity': veh([('flexity_kopf', 0), ('flexity_mittel', 0), ('flexity_zwischen', 0), ('flexity_mittel', 0), ('flexity_zwischen', 0), ('flexity_mittel', 0), ('flexity_kopf', 1)],
            {'bogie_z_local': {'flexity_kopf': [-1.2], 'flexity_mittel': [0.0]}, 'note': 'pantograph head y=5.45 on flexity_zwischen'}),
        'trolleybus': veh([('trolley_vorne', 0), ('trolley_gelenk', 0), ('trolley_hinten', 0)],
            {'axles_z_local': {'trolley_vorne': [-2.9, 2.8], 'trolley_hinten': [2.3]}, 'note': 'poles on trolley_hinten reach y=5.55, tips 3.2 m behind module end; wire spacing 0.6 m, wire y~5.5'})}
    json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
