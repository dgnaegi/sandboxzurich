"""Minimal glTF 2.0 binary writer: one node per layer, each with a single colored primitive."""
import json
import struct

import numpy as np

FLOAT, UINT32, UBYTE = 5126, 5125, 5121


def write(path, layers):
    """layers: dict name -> Mesh.arrays() dict (pos, nrm, col, idx, uv, layer) in three.js axes, or None."""
    bin_ = bytearray()
    views, accs, meshes, nodes = [], [], [], []

    def add(arr, comp, typ, target, norm=False, minmax=False):
        while len(bin_) % 4:
            bin_.append(0)
        data = arr.tobytes()
        views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data), "target": target})
        bin_.extend(data)
        a = {"bufferView": len(views) - 1, "componentType": comp, "count": len(arr), "type": typ}
        if norm:
            a["normalized"] = True
        if minmax:
            a["min"] = arr.min(0).tolist()
            a["max"] = arr.max(0).tolist()
        accs.append(a)
        return len(accs) - 1

    for name, m in layers.items():
        if m is None:
            continue
        attrs = {
            "POSITION": add(m["pos"].astype(np.float32), FLOAT, "VEC3", 34962, minmax=True),
            "NORMAL": add(m["nrm"].astype(np.float32), FLOAT, "VEC3", 34962),
            "COLOR_0": add(m["col"].astype(np.uint8), UBYTE, "VEC4", 34962, norm=True),
            # standard channels so gltfpack/meshopt keep them: uv = texture repeats, uv1.x = texture-array layer
            "TEXCOORD_0": add(m["uv"].astype(np.float32), FLOAT, "VEC2", 34962),
            "TEXCOORD_1": add(np.column_stack([m["layer"], np.zeros(len(m["layer"]))]).astype(np.float32), FLOAT, "VEC2", 34962),
        }
        ia = add(m["idx"].astype(np.uint32).reshape(-1), UINT32, "SCALAR", 34963)
        meshes.append({"name": name, "primitives": [{"attributes": attrs, "indices": ia}]})
        nodes.append({"name": name, "mesh": len(meshes) - 1})

    gltf = {"asset": {"version": "2.0", "generator": "sandboxzurich"}, "scene": 0,
            "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes,
            "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(bin_)}]}
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    bin_.extend(b"\0" * (-len(bin_) % 4))
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(bin_), 0x004E4942) + bytes(bin_))
