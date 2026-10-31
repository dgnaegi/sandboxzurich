What Scope B adds to the pilot verdict (phase 1 diagnosis, 2026-10-31):

- **The cadastre knows the whole ramp, in two kinds of object.** From the Hardbrücke down to x ≈ 176 the ramp is a «Brücke» polygon on
  piers (10 cadastre piers stand under the modelled deck). Below x ≈ 176 it is a pair of thin «Brücke» edge polygons 13.9 m apart with
  a «Strasse, Weg» polygon (11.9 m) between them: a ramp on fill between edge structures. LiDAR agrees: the bridge class ends at the
  same x, the ground class continues on top of the fill, and that fill surface lies up to 4.2 m above the game terrain (main chain
  s 90–140). The pilot's solid skirt below the fork was right; it stops 5–9 m before the modelled grade end while the edge polygons
  run 7 m (main chain) and 13 m (continuation) past it, down to Geroldstrasse. The game terrain under the fill is a terrain-pass issue
  only as long as the skirt is solid.
- **Width and outline.** The structure is 13.9 m wide (p50) along the entire ramp; the live rows model a 3.2 m lane, the pilot 7.5 m
  (8–11 m on the deck, 8 m on the fill). The pilot never leaves the cadastre outline (edge overshoot p95 −0.0 m) but leaves 3.6 m (p50)
  of structure uncovered on one side, because the OSM axis is a one-way lane 2.0 m (p50) off the structure's centre line. Outline IoU
  0.30 → 0.64. Builder v2: edges from the cadastre (per-vertex `wl`/`wr` measured from the OSM axis to the AV edges), axis stays on OSM.
- **Axis.** Offsets above 4 m occur only at the fork (main chain s 50–70, around (147,214)) and where the north branch runs inside the
  Hardbrücke's own polygon (branch s 6–22 and 66–68): there the "centre line" of the merged structure means nothing. Elsewhere the
  offset is a steady 1–3 m lane offset, not jitter; the ±1 m jitter of the pilot tracker is below the 2 m station spacing and shows
  only in the screenshots.
- **Branches onto the Hardbrücke.** Both upper branches lie inside the Hardbrücke bridge polygon (structure 15.8 m and 18 m wide beside
  the main deck, > 24 m where they merge). They should become flush with the Hardbrücke deck (row keys `ol`/`or`), not separate decks
  with their own edges.
- **Piers.** 18 cadastre piers within 12 m of the axes, 10 under the modelled deck, 8 are Hardbrücke piers 4.4–11.6 m off the branch
  axes. Of the 10 tile piers only 2 stand at a real pier; 4 stand under the fill part where there is no pier at all. Builder v2: piers
  from AV «Pfeiler», none under the fill.
- **Walls.** No «Mauer» belongs to the ramp; the edge structures are the thin bridge polygons. The walls at (170–200, 230–235) are a
  neighbouring plot's.
- **What Scope B cannot give.** On the deck proper the Bodenbedeckung is the ground below, so the lane / footway split of the deck
  (footway side, parapet type) has to come from Scope C (imagery) or LiDAR intensity. Heights are already right (Scope A residual
  p95 0.1–0.2 m for both row sets, the live decks use `_lidar_decks`).
