# Improvements log (what got better, per iteration and per bridge)

Kept for the PR text. Ride lines come from `python3 pipeline/scopes/ride_delta.py` (gate log against the committed baseline);
scope numbers from the site reports. Newest first.

## 2026-11-01 · joins, verdicts, first transfer site (commit 3d5128e)
- Geroldrampe: the Hardbrücke's parapet is opened over the two ramp mouths, the fork branches are flush and coplanar, a
  collision post under the fork nose is gone; two uphill car routes (new, local) reach the Hardbrücke with 0 crashes.
- Hohlstrasse / Brauerstrasse (transfer site, builder unchanged): outline IoU 0.53 → 0.99, verdict PASS; the car and bike
  rides that were stuck in the baseline now cross (car 133 → 293 of 298 m, bike 96 → 125 of 130 m).
- Scorer: PASS / REVIEW verdict per site; Duttweiler PASS, Hohlstrasse PASS, Geroldrampe REVIEW (fork gore, 4.2 m uncovered).
- Gate (99 rides): stuck 14 → 12, fell 2 → 1, crashes unchanged; no ride worse than the baseline.

## 2026-11-01 · builder v2 (commit 52e6c0f)
- Duttweilerbrücke south ramp: deck 6.4 → 14.2 m on the cadastre outline, 30 of 30 cadastre piers modelled (live 8 of 68
  rule-spaced tile piers stood at a real pier), the walled abutment modelled instead of a deck ending 4.3 m in the air,
  heights within 0.0 m (95th pct) of the LiDAR deck top (live crest 1.0 m low); the car drives 183 → 632 of 638 m.
- Geroldrampe: 3.2 m lane → full 13.9 m structure, the fill between the thin edge polygons solid, 13 of 13 piers at real
  positions (live 2 of 10); outline IoU 0.35 → 0.91.
- Gate: stuck 14 → 12, fell 2 → 1.

## 2026-10-31 · scope B diagnosis (commit a4219e3)
- Cadastre fetch and scorer; the two site reports showed what LiDAR alone could not: the Geroldrampe is fill between two thin
  edge polygons below x ≈ 176, the Duttweiler deck ends exactly where the live rows ended in the air, the Bodenbedeckung has no
  carriageway polygons on decks.

## 2026-10-31 · LiDAR pilot (commits 12f2ef0, 3027125), superseded
- Widths from the LiDAR bridge class, continuation to grade; "only slightly better" (axis jitter, landings along the road
  graph), kept: central-strip heights, solid skirts, per-vertex `wl`/`wr`, the ride gate and the shot tooling.

## Rides vs the gate baseline, current run
Rides vs baseline base (2026-10-31): 4 better, 0 worse, 2 new

Better:
- Duttweilerbrücke (car): raw → raw, progress 183 → 632 of 638 m
- Hohlstrasse (bike): stuck → jump, progress 96 → 125 of 130 m
- Hohlstrasse (car): stuck → raw, progress 133 → 293 of 298 m
- Stauffacherstrasse (car): fell → raw, progress 218 → 173 of 249 m

New:
- Geroldrampe up via the north branch (car): raw, progress 257 of 262 m (new route)
- Geroldrampe up via the south branch (car): raw, progress 285 of 290 m (new route)
