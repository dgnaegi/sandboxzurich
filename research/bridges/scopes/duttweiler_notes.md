What Scope B adds to the pilot verdict (phase 1 diagnosis, 2026-10-31):

- **The deck ends where the live rows end, and the cadastre says what follows.** The «Brücke» polygon is 14.0 m wide along the south
  ramp and ends at (−603, 149): exactly the point where the live rows stop 4.3 m in the air. Beyond it two «Mauer» wing walls flank the
  axis (abutment), the walls end 5 m past the pilot's grade end, and the pilot's continuation (26 m of structure past the deck end,
  22 m of it solid, a wall at the right edge over 18 m) reproduces this sequence deck → walled abutment → grade. The live rows have no
  abutment at all. The game terrain at the landing is 3.0 m below the LiDAR ground over the last 12 m (s 522–534): terrain pass.
- **Width and outline.** Live 6.4 m vs 14.0 m (4.4 m uncovered per side); pilot 14.5 m, width error −0.1 m (p50), outline IoU
  0.41 → 0.75. The pilot's overshoot (p95 +1.2 m, max +4.4 m) sits at s 434–436, where the ramp crosses the rail flyover and the LiDAR
  bridge band merges with the other deck, and at the deck end (s 512–514), where the band runs past the polygon corner. The cadastre
  outline has neither problem: builder v2 takes the edges from it.
- **Axis.** The OSM axis is 0.5 m (p50, p95 0.6 m) off the structure's centre line: the axis is right; the jitter the user saw is the
  tracker's, below the station spacing. Offsets above 4 m only at the flyover crossing and the deck end.
- **Piers.** 30 cadastre piers within 12 m of the axis; the live rows (6.4 m) cover 14 of them, the pilot 26; the other 4 belong to the
  crossing flyover. Of the 68 rule-spaced tile piers only 8 stand at a real pier. Builder v2: piers at AV positions (pairs about every
  10 m), the rule spacing goes.
- **Heights.** Live residual p95 1.2 m against the LiDAR deck top (the crest 1.5 m too low, as the pilot report said), pilot 0.2 m.
- **Stairs.** «Treppe» at the east edge of the deck around (−585, 195) and at (−575, 355): candidates for stair rows later.
- **What Scope B cannot give.** No «Strasse, Weg» polygon lies on the deck (0 stations live; the 15 pilot stations are the landing
  junction): the carriageway / footway split on decks must come from Scope C or LiDAR intensity, as at the Geroldrampe.
