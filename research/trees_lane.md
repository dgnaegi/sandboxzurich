# Trees on the carriageway (agent E, 2026-10-19)
Audit: `.venv/bin/python pipeline/audit_trees_lane.py` (reads the tile road masks, 1 m cells, and the tree rows of web/public/tiles).
Fix: `cityprops.lane_fix` in `city_props` (covers register trees, OSM private trees and yard nDSM trees alike): trunk inside
S["roads"] (AV carriageway + parking bays) -> moved to the nearest kerb edge + 0.4 m if the edge is within 2.5 m, else dropped.
Catalogue lookup (species/year) keeps the original position.
Before (all 615 tiles): 26053 trees, 621 on the carriageway (2.38 %), 360 of them street trees.
Rebuilt the 10 worst tiles (-1_-3,-1_-2,3_-2,-2_-5,-2_-3,4_-7,3_-7,0_-6,2_-5,2_-9): 121 -> 20 on the mask
(the rest sit 0.4 m beside the edge inside a 1 m mask cell; the audit counts the cell, not the exact point).
Whole map after: 26017 trees, 519 (1.99 %); the other 175 tiles change with the next full build.
