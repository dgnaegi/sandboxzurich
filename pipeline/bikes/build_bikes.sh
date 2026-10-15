#!/bin/bash
# Build all bike GLBs + manifest, validate, render preview/bikes_sheet.jpg (+ compare sheet). Pure python + Blender for renders only.
cd "$(dirname "$0")/../.." || exit 1
python3 -I pipeline/bikes/build_bikes.py && python3 pipeline/blender/check_glb.py web/public/models/bikes/*.glb
B=/opt/homebrew/bin/blender
$B -b -P pipeline/bikes/render_sheet.py -- sheet preview/bikes_sheet.jpg 125 2>&1 | grep -E "rror|Traceback|SHEET"
D=$(mktemp -d); $B -b -P pipeline/bikes/render_sheet.py -- each "$D" 90 2>&1 | grep -E "rror|Traceback"; python3 -I pipeline/bikes/make_compare.py "$D"
