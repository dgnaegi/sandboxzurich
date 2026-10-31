What the scopes say (phase 1 diagnosis, phase 2 builder v2; 2026-10-31):

- **The deck ends where the live rows end, and the cadastre says what follows.** The «Brücke» polygon is 14.1 m wide along the south
  ramp and ends at (−603, 149): exactly where the live rows stop 4.3 m in the air. Beyond it two «Mauer» wing walls flank the axis
  (abutment); v2 continues 30 m along the road graph to grade, takes its width from the wing walls (about 10 m) where the cadastre has
  no bridge object, and models the abutment as a 22 m solid section: deck → walled abutment → grade. The game terrain at the landing
  is 3.0 m below the LiDAR ground over the last 12 m: terrain pass.
- **Width and outline.** Live 6.4 m vs 14.1 m; v2 14.2 m with edge overshoot p95 +0.0 m and nothing uncovered; outline IoU
  0.43 → 0.77 → 0.88. The pilot's overshoot at the rail flyover crossing (LiDAR bands merging) is gone: v2 casts the normal against
  each cadastre polygon separately and keeps the narrowest one containing the axis.
- **Heights.** Where the ramp passes under the rail flyover the LiDAR bridge class reads the flyover 6 m above; the first v2 run
  inherited a 1.4 m hump behind the crossing. The builder and the scorer now track the running height along the axis and reject
  samples more than 1 m off it, so the two occluded stations are interpolated: residual p95 0.0 m (live 1.0 m, the crest too low;
  pilot 0.1 m).
- **Axis.** The OSM axis is 0.5 m (p50, p95 0.6 m) off the deck's centre line; v2 keeps it.
- **Piers.** 30 cadastre piers within 12 m of the axis, 28 under the v2 deck (2 belong to the flyover); all 30 have a v2 pier row
  within 2 m. The 62 rule-spaced live piers under the deck and the replaced footway are gone.
- **Ride.** The car now reaches 632 of 638 m of the route (live rows: 183 m); the foot ride stepped 1 m down at the landing before
  the tail width came from the wing walls (see the gate run in `ramps_handoff.md`).
- **Stairs.** «Treppe» at the east edge of the deck around (−585, 195) and at (−575, 355): candidates for stair rows later.
- **What Scope B cannot give.** No «Strasse, Weg» polygon lies on the deck: the carriageway / footway split on decks must come from
  Scope C or LiDAR intensity, as at the Geroldrampe.
