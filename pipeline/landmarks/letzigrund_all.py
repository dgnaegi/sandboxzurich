"""Build Stadion Letzigrund: model -> gltfpack -> pipeline/overrides/landmarks_letzigrund.json (hide points kept from the first manifest in pipeline/overrides/letzigrund_hide.json).
Run: .venv/bin/python pipeline/landmarks/letzigrund_all.py && .venv/bin/python pipeline/landmarks/merge.py"""
import sys, os, json, subprocess, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
ROOT = os.path.dirname(os.path.dirname(HERE)); D = ROOT + "/web/public/models/landmarks/"
subprocess.run([sys.executable, os.path.join(HERE, "letzigrund.py")], check=True)
tmp = D + "_tmp_letzi.glb"
r = subprocess.run(["npx", "-y", "gltfpack", "-cc", "-i", D + "letzigrund.glb", "-o", tmp], capture_output=True, text=True)
if r.returncode == 0 and os.path.exists(tmp): shutil.move(tmp, D + "letzigrund.glb")
else: print("gltfpack failed", r.stderr[-200:])
meta = json.load(open(D + "letzigrund.meta.json"))
hide = json.load(open(ROOT + "/pipeline/overrides/letzigrund_hide.json"))
json.dump({"landmarks": [{"name": "Stadion Letzigrund", "model": "/models/landmarks/letzigrund.glb", "x": meta["x"], "y": meta["y"], "z": meta["z"], "heading": 0, "hide": hide}]},
          open(ROOT + "/pipeline/overrides/landmarks_letzigrund.json", "w"), indent=1)
print("letzigrund.glb", os.path.getsize(D + "letzigrund.glb") // 1024, "kB", meta)
