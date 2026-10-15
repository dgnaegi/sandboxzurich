#!/bin/bash
# Build all car GLBs + manifest + contact sheet. Log: logs/cars.log
cd "$(dirname "$0")/../.." || exit 1
B=/opt/homebrew/bin/blender
for t in ${1:-hatch wagon small sedan suv van sport}; do
  echo "== $t"; $B -b -P pipeline/cars/build_car.py -- $t 2>&1 | grep -E "DONE|rror|Traceback|opt fail"
  $B -b -P pipeline/cars/build_car.py -- $t drive 2>&1 | grep -E "DONE|rror|Traceback|opt fail"
done
python3 pipeline/cars/make_manifest.py
python3 pipeline/blender/check_glb.py $(ls web/public/models/cars/*.glb | grep -v _drive)
$B -b -P pipeline/cars/render_sheet.py 2>&1 | grep -E "ATTRS|rror|Traceback|SHEET"
