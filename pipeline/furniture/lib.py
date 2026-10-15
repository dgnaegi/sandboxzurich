"""Mesh helpers (run inside Blender). Game coords: Y up, front = -Z, metres."""
import math, struct, json
import bmesh
from mathutils import Matrix, Vector

LAMP = 0xfff3c8

class Model:
    def __init__(self): self.tris = []   # (v0,v1,v2,color)
    def _add(self, bm, M, color):
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        for f in bm.faces:
            vs = [M @ v.co for v in f.verts]
            self.tris.append((tuple(vs[0]), tuple(vs[1]), tuple(vs[2]), color))
        bm.free()
    def box(self, c, s, color, rx=0, ry=0, rz=0):
        """centre c, size s=(sx,sy,sz); rotations (deg) about own centre."""
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        M = (Matrix.Translation(c) @ Matrix.Rotation(math.radians(ry), 4, 'Y') @
             Matrix.Rotation(math.radians(rx), 4, 'X') @ Matrix.Rotation(math.radians(rz), 4, 'Z') @
             Matrix.Diagonal((s[0], s[1], s[2], 1)))
        self._add(bm, M, color)
    def cyl(self, x, y0, z, r0, r1, h, color, seg=8, cap0=True, cap1=True, rx=0, rz=0, ry=0):
        """frustum from y0 (radius r0) up to y0+h (radius r1); optional tilt about base."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=seg,
                              radius1=max(r0,1e-4), radius2=max(r1,1e-4), depth=h)
        # blender cone along Z -> up Y (rotation x +90 maps z->-y ... use explicit)
        R = Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))  # (x,y,z)->(x,z,-y)
        bmesh.ops.transform(bm, matrix=R, verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, h/2, 0), verts=bm.verts)
        for top, on, r in ((False, cap0, r0), (True, cap1, r1)):
            if on and r > 1e-3:
                vs = [v for v in bm.verts if abs(v.co.y - (h if top else 0)) < 1e-6]
                vs.sort(key=lambda v: math.atan2(v.co.z, v.co.x))
                if not top: vs.reverse()
                try: bmesh.ops.contextual_create(bm, geom=vs)
                except Exception: pass
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        M = (Matrix.Translation((x, y0, z)) @ Matrix.Rotation(math.radians(ry),4,'Y') @
             Matrix.Rotation(math.radians(rx),4,'X') @ Matrix.Rotation(math.radians(rz),4,'Z'))
        self._add(bm, M, color)
    def bounds(self):
        xs = [v[i] for t in self.tris for v in t[:3] for i in (0,)]
        mn = [min(v[i] for t in self.tris for v in t[:3]) for i in range(3)]
        mx = [max(v[i] for t in self.tris for v in t[:3]) for i in range(3)]
        return mn, mx
    def write_glb(self, path):
        pos, nor, col, idx = [], [], [], []
        for k, (a, b, c, color) in enumerate(self.tris):
            A, B, C = Vector(a), Vector(b), Vector(c)
            n = (B - A).cross(C - A)
            n = n.normalized() if n.length > 1e-12 else Vector((0,1,0))
            rgb = ((color>>16)&255, (color>>8)&255, color&255, 255)
            for v in (a, b, c):
                pos += v; nor += tuple(n); col += rgb
            idx += [3*k, 3*k+1, 3*k+2]
        n = len(pos)//3
        mn, mx = self.bounds()
        pb = struct.pack('<%df' % len(pos), *pos); nb = struct.pack('<%df' % len(nor), *nor)
        cb = bytes(col); ib = struct.pack('<%dH' % len(idx), *idx)
        blob = pb + nb + cb + ib
        while len(blob) % 4: blob += b'\0'
        js = {"asset": {"version": "2.0", "generator": "pipeline/furniture"},
              "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
              "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2}, "indices": 3, "material": 0}]}],
              "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [1,1,1,1], "metallicFactor": 0, "roughnessFactor": 0.85}}],
              "buffers": [{"byteLength": len(blob)}],
              "bufferViews": [{"buffer":0,"byteOffset":0,"byteLength":len(pb),"target":34962},
                              {"buffer":0,"byteOffset":len(pb),"byteLength":len(nb),"target":34962},
                              {"buffer":0,"byteOffset":len(pb)+len(nb),"byteLength":len(cb),"target":34962},
                              {"buffer":0,"byteOffset":len(pb)+len(nb)+len(cb),"byteLength":len(ib),"target":34963}],
              "accessors": [{"bufferView":0,"componentType":5126,"count":n,"type":"VEC3","min":mn,"max":mx},
                            {"bufferView":1,"componentType":5126,"count":n,"type":"VEC3"},
                            {"bufferView":2,"componentType":5121,"normalized":True,"count":n,"type":"VEC4"},
                            {"bufferView":3,"componentType":5123,"count":len(idx),"type":"SCALAR"}]}
        j = json.dumps(js, separators=(',',':')).encode()
        while len(j) % 4: j += b' '
        with open(path, 'wb') as f:
            f.write(struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(j) + 8 + len(blob)))
            f.write(struct.pack('<I4s', len(j), b'JSON') + j)
            f.write(struct.pack('<I4s', len(blob), b'BIN\0') + blob)
        return len(self.tris), [mx[i]-mn[i] for i in range(3)]
