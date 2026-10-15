#!/bin/bash
# Build the shared animation libraries anims_<class>.glb (reference figure per class). Log: logs/animlib.log
# usage: build_animlib.sh [A_young B_young A_old B_old]     (needs pipeline/mocap/prep.py output in data/cache/mocap)
cd "$(dirname "$0")/../.." || exit 1
B=/opt/homebrew/bin/blender
ref() { case $1 in A_young) echo npc_01;; B_young) echo npc_00;; A_old) echo npc_32;; B_old) echo npc_31;; esac; }
for c in ${@:-A_young B_young A_old B_old}; do
  echo "== $c ($(ref $c))"; ANIMLIB=$c $B -b -P pipeline/blender/build_human.py -- $(ref $c) 2>&1 | grep -E "LIBDONE|rror|Traceback"
done
