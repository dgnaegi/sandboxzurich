#!/bin/bash
# Build the shared animation libraries anims_<class>.glb (reference figure per class). Log: logs/animlib.log
# usage: build_animlib.sh [A_young B_young A_old B_old]     (needs pipeline/mocap/prep.py output in data/cache/mocap)
cd "$(dirname "$0")/../.." || exit 1
B=/opt/homebrew/bin/blender
declare -A REF=([A_young]=npc_01 [B_young]=npc_00 [A_old]=npc_32 [B_old]=npc_31)
for c in ${@:-A_young B_young A_old B_old}; do
  echo "== $c (${REF[$c]})"; ANIMLIB=$c $B -b -P pipeline/blender/build_human.py -- ${REF[$c]} 2>&1 | grep -E "LIBCLIP|LIBDONE|rror|Traceback"
done
