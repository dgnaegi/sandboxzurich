"""blender -b -P build_trains.py : S-Bahn double-decker modules (head, mid) -> web/public/models/trains/*.glb + manifest.json
Front = -Z, up = +Y, origin = module centre at rail top. White body, red doors, blue skirt, no operator logo."""
import sys, os, json, math, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'transit_models'))
import geom as G
OUT = os.path.abspath(os.path.join(HERE, '../../web/public/models/trains'))
os.makedirs(OUT, exist_ok=True)
WHITE, BLUE, RED, GLASS, GREY, DARK = G.WHITE, G.lin((28, 70, 140)), G.lin((200, 25, 30)), G.GLASS, G.lin((170, 175, 180)), G.DARK
L = 26.4
HX = 1.4
# (y, x) side profile: skirt, lower windows, belt, upper windows, roof curve
PROF = [(0.55, 1.36), (1.05, 1.40), (1.40, 1.40), (2.15, 1.40), (2.75, 1.40), (3.50, 1.40), (3.80, 1.38), (4.10, 1.10), (4.36, 0.0)]

def ring(z, sx=1.0, back=0.0, drop=0.0):
    out = []
    for y, x in PROF:
        fr = max(0.0, (y - 2.25) / 2.1)
        out.append((x * sx, y - drop * fr, z + back * fr))
    return out

def mir(r): return [(-x, y, z) for x, y, z in r]

def cols(t):
    r = GREY
    return {'p': [BLUE, WHITE, WHITE, WHITE, WHITE, WHITE, r, r],
            'w': [BLUE, WHITE, GLASS, WHITE, GLASS, WHITE, r, r],
            'd': [BLUE, RED, RED, RED, GLASS, WHITE, r, r]}[t]

def strips(m, ra, rb, c, ref):
    for A, B in ((ra, rb), (mir(ra), mir(rb))):
        for i in range(len(A) - 1):
            m.quad([A[i], B[i], B[i + 1], A[i + 1]], c[i], ref)

def layout(z0, z1, doors):
    segs, z = [], z0
    for c in sorted(doors):
        a, b = c - 0.7, c + 0.7
        segs += win(z, a - 0.3) + [(a - 0.3, a, 'p'), (a, b, 'd'), (b, b + 0.3, 'p')]
        z = b + 0.3
    return segs + win(z, z1)

def win(a, b):
    n = max(1, round((b - a) / 1.5))
    w = (b - a) / n
    return [(a + i * w, a + (i + 1) * w, 'w' if i % 1 == 0 else 'p') for i in range(n)]

def car(head):
    m = G.Mesh(); ref = (0, 2.2, 0); h = L / 2
    z0, z1 = -h + 0.12, h - 0.12
    if head:
        rs = [ring(-h, 0.80, 2.4, 0.5), ring(-h + 1.0, 0.93, 1.1, 0.15), ring(-h + 2.2)]
        # nose cap: red band + big dark windscreen
        r0 = rs[0]
        WS = G.lin((20, 24, 30)); nose = [BLUE, RED, RED, WHITE, WS, WHITE, GREY, GREY]
        for i in range(len(r0) - 1):
            m.quad([r0[i], mir(r0)[i], mir(r0)[i + 1], r0[i + 1]], nose[i], ref)
        for a, b in zip(rs, rs[1:]): strips(m, a, b, nose, ref)
        z0 = -h + 2.2
    else:
        e, i0 = ring(-h, 0.93), ring(-h + 0.12)
        strips(m, e, i0, [DARK] * 8, ref)
        m.quad([e[0], mir(e)[0], mir(e)[-1], e[-1]], DARK, ref) if False else None
    e, i1 = ring(h, 0.93), ring(h - 0.12)
    strips(m, i1, e, [DARK] * 8, ref)
    rr = ring(0)
    doors = [-8.0, 8.0] if not head else [4.0, 10.0]
    for s in 'rl':
        for za, zb, t in layout(z0, z1, doors):
            A = [(x, y, za) for x, y, _ in rr]; B = [(x, y, zb) for x, y, _ in rr]
            if s == 'l': A, B = mir(A), mir(B)
            c = cols(t)
            for i in range(len(A) - 1): m.quad([A[i], B[i], B[i + 1], A[i + 1]], c[i], ref)
    m.quad([(-1.3, 0.55, -h), (1.3, 0.55, -h), (1.3, 0.55, h), (-1.3, 0.55, h)], DARK, ref)
    for bz in (-9.5, 9.5):
        m.box(-0.95, 0.95, 0.22, 0.6, bz - 1.4, bz + 1.4, DARK)
        for az in (-0.9, 0.9):
            m.wheel(-0.8, -0.65, 0.46, bz + az, 0.46, GREY); m.wheel(0.65, 0.8, 0.46, bz + az, 0.46, GREY)
    if not head:  # pantograph on the middle car
        G.pantograph(m, {'ytop': 4.36}, 3.0, 5.5)
        m.box(-0.8, 0.8, 4.3, 4.55, -4, 2, GREY)
    return m

def to_blender(name, mesh):
    verts, faces, cs = [], [], []
    for pts, c in mesh.f:
        i0 = len(verts)
        for p in pts: verts.append((p[0], -p[2], p[1]))
        for k in range(1, len(pts) - 1): faces.append((i0, i0 + k, i0 + k + 1)); cs.append(c)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ca = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    for pi, poly in enumerate(me.polygons):
        for li in poly.loop_indices: ca.data[li].color = (*cs[pi], 1.0)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    mat = bpy.data.materials.new('body'); mat.use_nodes = True
    bs = mat.node_tree.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value = .5
    cn = mat.node_tree.nodes.new('ShaderNodeVertexColor'); cn.layer_name = 'Col'
    mat.node_tree.links.new(cn.outputs['Color'], bs.inputs['Base Color'])
    me.materials.append(mat); me.shade_flat()
    return ob

if __name__ == '__main__':
    man = {'units': 'm', 'front': '-Z', 'up': '+Y', 'origin': 'module centre, rail top (y=0)', 'modules': {},
           'train': [['head', 0], ['mid', 0], ['mid', 0], ['mid', 0], ['head', 1]], 'car_length': L, 'bogie_z': [-9.5, 9.5]}
    for name, head in (('sbahn_head', True), ('sbahn_mid', False)):
        for o in list(bpy.data.objects): bpy.data.objects.remove(o)
        mesh = car(head); ob = to_blender(name, mesh)
        bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + '.glb'), export_format='GLB', use_selection=True,
                                  export_yup=True, export_attributes=True, export_materials='EXPORT')
        man['modules'][name] = {'file': name + '.glb', 'triangles': mesh.tris()}
        print(name, mesh.tris(), 'tris')
    json.dump(man, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
