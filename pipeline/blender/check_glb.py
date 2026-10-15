"""Summarise GLBs: meshes, skins, materials, animations, tris, size. Usage: check_glb.py file.glb ..."""
import sys, json, struct, os
def info(path):
    b = open(path, "rb").read(); L = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + L])
    tris = 0
    for m in j["meshes"]:
        for p in m["primitives"]: tris += j["accessors"][p["indices"]]["count"] // 3
    bv = j["bufferViews"]; sz = {}
    for k, a in enumerate(j["accessors"]): pass
    imgs = [bv[i["bufferView"]]["byteLength"] for i in j.get("images", [])]
    anims = {a["name"]: max(j["accessors"][s["input"]]["max"][0] for s in a["samplers"]) for a in j.get("animations", [])}
    prims = sum(len(m["primitives"]) for m in j["meshes"])
    return dict(file=os.path.basename(path), meshes=len(j["meshes"]), prims=prims, skins=len(j.get("skins", [])), joints=len(j["skins"][0]["joints"]) if j.get("skins") else 0,
                materials=len(j["materials"]), tris=tris, kb=os.path.getsize(path) // 1024, tex_kb=sum(imgs) // 1024, anims={k: round(v, 3) for k, v in anims.items()})
if __name__ == "__main__":
    for f in sys.argv[1:]: print(info(f))
