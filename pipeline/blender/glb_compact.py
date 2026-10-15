"""Shrink a GLB: drop constant (rest-valued) translation/scale animation channels, then remove
unused samplers/accessors/bufferViews and repack the binary chunk."""
import json, struct

def compact(path, keep_rot=None):
    """keep_rot: node names whose rotation channels are kept (animation libraries: unmapped bones stay at rest)."""
    b = open(path, "rb").read(); L = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + L]); off = 20 + L + 8; binc = b[off:]
    acc = j["accessors"]
    # quantise WEIGHTS_0 float32 -> normalized uint8 (sum forced to 255)
    for m in j.get("meshes", []):
        for p in m["primitives"]:
            ai = p["attributes"].get("WEIGHTS_0")
            if ai is None or acc[ai]["componentType"] != 5126: continue
            a = acc[ai]; v = j["bufferViews"][a["bufferView"]]; o = v.get("byteOffset", 0) + a.get("byteOffset", 0)
            fl = struct.unpack(f"<{a['count'] * 4}f", binc[o:o + a["count"] * 16]); q = bytearray()
            for i in range(a["count"]):
                w = fl[i * 4:i * 4 + 4]; t = sum(w) or 1.0
                r = [int(round(x / t * 255)) for x in w]; k = max(range(4), key=lambda z: r[z]); r[k] += 255 - sum(r)
                q += bytes(r)
            while len(binc) % 4: binc += b"\0"
            j["bufferViews"].append({"buffer": 0, "byteOffset": len(binc), "byteLength": len(q), "target": 34962})
            binc += bytes(q)
            a["bufferView"] = len(j["bufferViews"]) - 1; a["byteOffset"] = 0; a["componentType"] = 5121; a["normalized"] = True
            a.pop("min", None); a.pop("max", None)
    for a in j.get("animations", []):
        keep = []
        for ch in a["channels"]:
            s = a["samplers"][ch["sampler"]]
            if ch["target"]["path"] in ("translation", "scale") and acc[s["input"]]["count"] <= 2: continue
            if keep_rot is not None and ch["target"]["path"] == "rotation" and j["nodes"][ch["target"]["node"]].get("name") not in keep_rot: continue
            keep.append(ch)
        a["channels"] = keep
        used = sorted({c["sampler"] for c in keep}); remap = {o: n for n, o in enumerate(used)}
        a["samplers"] = [a["samplers"][o] for o in used]
        for c in keep: c["sampler"] = remap[c["sampler"]]
    # quantise rotation outputs float32 VEC4 -> normalized int16, share identical time accessors
    def raw(a):
        v = j["bufferViews"][a["bufferView"]]; o = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        n = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[a["type"]]; return binc[o:o + a["count"] * n * 4]
    seen = {}
    for a in j.get("animations", []):
        for ch in a["channels"]:
            sm = a["samplers"][ch["sampler"]]
            ia = acc[sm["input"]]
            if ia["componentType"] == 5126:
                k = raw(ia)
                if k in seen: sm["input"] = seen[k]
                else: seen[k] = sm["input"]
            oa = acc[sm["output"]]
            if ch["target"]["path"] == "rotation" and oa["componentType"] == 5126 and not oa.get("normalized"):
                import array
                fl = struct.unpack(f"<{oa['count'] * 4}f", raw(oa)); q = struct.pack(f"<{len(fl)}h", *[max(-32767, min(32767, int(round(x * 32767)))) for x in fl])
                while len(binc) % 4: binc += b"\0"
                j["bufferViews"].append({"buffer": 0, "byteOffset": len(binc), "byteLength": len(q)}); binc += q
                oa["bufferView"] = len(j["bufferViews"]) - 1; oa["byteOffset"] = 0; oa["componentType"] = 5122; oa["normalized"] = True
                oa.pop("min", None); oa.pop("max", None)
    # accessor usage
    used = set()
    def mark(i):
        if i is not None: used.add(i)
    for m in j["meshes"]:
        for p in m["primitives"]:
            for v in p["attributes"].values(): mark(v)
            mark(p.get("indices"))
    for sk in j.get("skins", []): mark(sk.get("inverseBindMatrices"))
    for a in j.get("animations", []):
        for s in a["samplers"]: mark(s["input"]); mark(s["output"])
    order = sorted(used); amap = {o: n for n, o in enumerate(order)}
    newacc = [acc[o] for o in order]
    for m in j["meshes"]:
        for p in m["primitives"]:
            p["attributes"] = {k: amap[v] for k, v in p["attributes"].items()}
            if "indices" in p: p["indices"] = amap[p["indices"]]
    for sk in j.get("skins", []):
        if "inverseBindMatrices" in sk: sk["inverseBindMatrices"] = amap[sk["inverseBindMatrices"]]
    for a in j.get("animations", []):
        for s in a["samplers"]: s["input"] = amap[s["input"]]; s["output"] = amap[s["output"]]
    # bufferViews: those used by accessors or images
    bvs = j["bufferViews"]; ub = {a["bufferView"] for a in newacc if "bufferView" in a} | {i["bufferView"] for i in j.get("images", []) if "bufferView" in i}
    ob = sorted(ub); bmap = {o: n for n, o in enumerate(ob)}
    out = bytearray(); newbv = []
    for o in ob:
        v = dict(bvs[o]); v.pop("byteStride", None) if v.get("target") == 34962 and False else None; data = binc[v.get("byteOffset", 0):v.get("byteOffset", 0) + v["byteLength"]]
        while len(out) % 4: out.append(0)
        v["byteOffset"] = len(out); out += data; newbv.append(v)
    for a in newacc:
        if "bufferView" in a: a["bufferView"] = bmap[a["bufferView"]]
    for i in j.get("images", []):
        if "bufferView" in i: i["bufferView"] = bmap[i["bufferView"]]
    j["accessors"] = newacc; j["bufferViews"] = newbv
    while len(out) % 4: out.append(0)
    j["buffers"] = [{"byteLength": len(out)}]
    js = json.dumps(j, separators=(",", ":")).encode()
    while len(js) % 4: js += b" "
    tot = 12 + 8 + len(js) + 8 + len(out)
    open(path, "wb").write(struct.pack("<III", 0x46546C67, 2, tot) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(out), 0x004E4942) + bytes(out))
