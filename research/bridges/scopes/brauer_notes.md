Transfer site 1 (2026-11-01): the Hohlstrasse bridge over the Sihl line tracks with the Brauerstrasse approach, the maintainer's
open item «Brauerstrasse-Rampe (376,−480) braucht Böschung» and two stuck rides in the gate baseline (car and bike at (355,−487)).

- **What the cadastre shows.** One «Brücke» polygon of 26 m across the tracks, about 30 m wide (both carriageways, tram and footways),
  no piers (single span), and «Mauer» retaining walls along both approaches. The live rows are three OSM chains (6.4 / 6.4 / 3.2 m)
  that end at grade on both sides with the approach embankments missing in the game terrain (game − LiDAR ground up to 6.6 m, p95
  5.8 m): that is the «braucht Böschung».
- **What the builder did, unchanged.** The three chains share the deck slice halfway (flush between them, coplanar heights), take
  the wall faces as edges on the approaches (walls at the modelled edge 8 / 30 m) and model the approaches as solid sections
  (126 m, 36 m of them confirmed by walls); the tram rows are opened along the whole bridge (flush inside the road deck, as the
  pipeline does for side-by-side decks).
- **Numbers.** Outline IoU 0.53 → 0.99 at ramp stations, uncovered 7.1 → 0.0 m, overshoot p95 +0.4 m, heights p95 0.1 m on the
  bridge class and 0.3 m on the ground class, verdict PASS. Gate: the car and bike rides over Hohlstrasse that were stuck in the
  baseline now cross (car raw-height jumps max 0.5 m, foot max 0.83 m at the approach kerbs).
- **Rules that had to change for this site:** none in the builder's geometry. Two scorer rules did: the slice available to a
  chain is the cadastre slice minus other road rows and halved towards sibling chains (otherwise the shared 30 m deck counted as
  "uncovered" for every chain), and the outline IoU is station-wise (the walled approaches are longer than the bridge polygon).
- **Open:** the approach surfaces are modelled as solid blocks down to the (too low) game terrain, so the skirts are up to 6 m
  tall where reality has a grass slope: terrain pass.
