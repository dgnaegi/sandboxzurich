#!/bin/bash
# Build all human GLBs (one Blender process each), then manifest + sheets. Log: logs/humans.log
# usage: build_humans.sh [id ...]   (default: player + npc_00..npc_39)
cd "$(dirname "$0")/../.." || exit 1
B=/opt/homebrew/bin/blender
ids="player"; for i in $(seq -w 0 39); do ids="$ids npc_$i"; done
python3 pipeline/blender/gen_cloth_tex.py
for id in ${@:-$ids}; do
  echo "== $id" ; $B -b -P pipeline/blender/build_human.py -- $id 2>&1 | grep -E "LOW|DONE|rror|Traceback" 
done
python3 pipeline/blender/make_manifest.py
$B -b -P pipeline/blender/render_sheet.py -- 0 16 humans_sheet 2>&1 | grep -E "rror|Traceback|SHEET"
$B -b -P pipeline/blender/render_sheet.py -- 16 40 humans_sheet2 2>&1 | grep -E "rror|Traceback|SHEET"
python3 pipeline/blender/check_glb.py web/public/models/humans/*.glb
