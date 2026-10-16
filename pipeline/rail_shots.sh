#!/bin/bash
# usage: rail_shots.sh prefix   (renders 6 comparison sites)
cd "$(dirname "$0")/../web"
P=${1:-old}
run() { node tests/topdown.mjs ../preview/_rail/${P}_$1.png $2 $3 ${4:-300} 800 && ../.venv/bin/python ../pipeline/rail_cmp.py ${P}_$1 $2 $3 ${4:-300}; }
run hb 1300 -470 &
run herdern 700 -150 &
run hardb 60 110 &
run kohl -1000 500 &
run altst -2080 800 &
run wied 435 -1300 &
wait
