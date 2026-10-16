#!/bin/zsh
# usage: tests/carriageway_shots.sh <tag>   (top-down 120 m views at the 10 check places via topdown.mjs)
tag=${1:-after}; out=../preview
while read name x y; do node tests/topdown.mjs $out/_carr_${tag}_$name.png $x $y 120 720; done <<'EOF'
langstrasse 740 -540
helvetiaplatz 740 -885
stauffacher 940 -1260
albisriederplatz -495 -668
hardplatz -110 -140
escher_wyss 460 715
lochergut 81 -940
idaplatz -140 -1135
bullingerplatz -60 -522
lindenplatz -2340 340
EOF
