Transfer site 2 (2026-11-01): the Hardbrücke access ramp from Pfingstweidstrasse, the ramp the maintainer's first bridge-ramp
round fixed by hand ("graue Platte auf Kopfhöhe, Bäume im Deck, Knick", `research/bridges/ramp_fix.md`). Unnamed OSM rows, so
the site is selected by a seed point (`ramp_sites.py`: `match ""` plus `seed`).

- **What the cadastre shows.** One chain of 145 m from the ramp foot near Pfingstweidstrasse (140, 310), 0.8 m above the terrain,
  up to the Hardbrücke deck at (62, 187), 8.9 m up, along the west side of the viaduct. The lower 46 m lie between two thin
  «Brücke» edge polygons (a ramp on fill between its edge structures, like the lower Geroldrampe), the upper part is a bridge
  polygon on one cadastre pier.
- **What the builder did, unchanged.** Width 3.5 → 10.0 m (p50) from the cadastre, the fill part solid, the upper part a deck,
  both ends joined (the Hardbrücke's parapet opened over the mouth, four rows). Outline IoU 0.84, nothing uncovered, edge
  overshoot p95 within the limit, heights on the LiDAR deck top, verdict PASS.
- **Rules that had to change for this site:** none in the builder; the site registry learnt to select unnamed rows by a seed.
