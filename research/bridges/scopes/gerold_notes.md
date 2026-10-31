What the scopes say (phase 1 diagnosis, phase 2 builder v2; 2026-10-31):

- **The cadastre knows the whole ramp, in two kinds of object.** From the Hardbrücke down to x ≈ 176 the ramp is a «Brücke» polygon on
  piers. Below x ≈ 176 it is a pair of thin «Brücke» edge polygons 13.9 m apart with a «Strasse, Weg» polygon (11.9 m) between them:
  a ramp on fill between edge structures. LiDAR agrees: the bridge class ends at the same x, the ground class continues on top of
  the fill, and that fill surface lies up to 4.2 m above the game terrain (s 90–140). v2 models the fill part as a 66 m solid section
  (skirts to the terrain) and the upper part as a deck with 13 cadastre piers at their real positions.
- **Width and outline.** The structure is 13.9 m wide (p50) along the ramp; the live rows model a 3.2 m lane, the pilot 7.5 m, v2 the
  full width on the main chain (13.9 m) and never leaves the cadastre outline (edge overshoot p95 +0.0 m); outline IoU 0.31 → 0.64 →
  0.75. The remaining uncovered width (p95 13.7 m) is at the branch stations inside the Hardbrücke polygon, where the ramp lanes run
  flush beside the main deck and the width is locked to the lane (flagged `ol`/`or`, no parapet): a junction exclusion in the scorer
  is the next step, not a builder change.
- **Axis.** The OSM axis stays (v2 does not track); its offset to the structure's centre line is a steady 1–3 m lane offset and
  peaks only at the fork (s 50–70) and where the north branch runs inside the Hardbrücke polygon.
- **Piers.** 18 cadastre piers within 12 m of the axes, 13 under the v2 deck, 5 are Hardbrücke piers off the branch axes. All 13
  v2 pier rows stand at a real pier; the 10 rule-spaced live piers (4 of them under the fill where there is none) are gone.
- **Walls.** No «Mauer» belongs to the ramp; the edge structures are the thin bridge polygons.
- **Heights.** Residual against the LiDAR deck top p95 0.0 m (live 0.1 m, pilot 0.2 m). The terrain under the fill (−4.2 m) is a
  terrain-pass item hidden by the solid skirt.
- **Blemishes by eye.** A one-station step in the north edge near x ≈ 130 where the slice toggles between the ramp and the
  Hardbrücke polygon; the junction strips on the Hardbrücke deck.
- **What Scope B cannot give.** On the deck proper the Bodenbedeckung is the ground below, so the lane / footway split (footway
  side, parapet type) has to come from Scope C or LiDAR intensity.
