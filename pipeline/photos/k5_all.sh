#!/bin/sh
# convert all research/buildings/notes_k5_*.txt -> notes_raw_k5_NNN.tsv
cd "$(dirname "$0")/../.." || exit 1
for f in research/buildings/notes_k5_*.txt; do n=$(basename "$f" .txt | sed 's/notes_k5_//'); .venv/bin/python pipeline/photos/k5_convert.py "$f" research/buildings/notes_raw_k5_$n.tsv >/dev/null; done
