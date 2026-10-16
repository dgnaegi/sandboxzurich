"""Meshopt-compress the runtime models (gltfpack) to cut the download.

Run after any model build (Blender scripts write uncompressed GLBs):
    .venv/bin/python pipeline/pack_models.py [dir ...]      default: all dirs below
Originals are kept in data/build/models_raw/<dir>/ so a run can be repeated or undone.
-noq: no quantisation (runtime code reads raw float attributes: trees.ts prepare, tint.ts skin weights, bike rig);
trees are NOT packed: trees.ts merges trunk/leaf meshes by order and attributes, which gltfpack changes.
-kn/-km/-ke: keep node names (bones for accessories/ride pose), materials and extras.
"""
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from config import ROOT

MODELS = ROOT / "web" / "public" / "models"
RAW = ROOT / "data" / "build" / "models_raw"
DIRS = ["humans", "bikes", "cars", "furniture", "transit", "accessories"]


def packed(f: Path) -> bool:
    b = f.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    return "EXT_meshopt_compression" in json.loads(b[20:20 + n]).get("extensionsUsed", [])


def main(dirs):
    before = after = 0
    for d in dirs:
        for f in sorted((MODELS / d).glob("*.glb")):
            raw = RAW / d / f.name
            if packed(f):
                if not raw.exists():
                    continue  # packed and no original: nothing to redo
            else:
                raw.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, raw)  # fresh build output becomes the new original
            tmp = f.with_suffix(".tmp.glb")
            subprocess.run(["npx", "--no-install", "gltfpack", "-i", str(raw), "-o", str(tmp), "-cc", "-noq", "-kn", "-km", "-ke"],
                           cwd=ROOT / "web", check=True, capture_output=True)
            before += raw.stat().st_size
            after += tmp.stat().st_size
            tmp.replace(f)
    print(f"packed {', '.join(dirs)}: {before / 1e6:.2f} MB -> {after / 1e6:.2f} MB")


if __name__ == "__main__":
    main(sys.argv[1:] or DIRS)
