# Scope report: Duttweilerbrücke south ramp (`duttweiler`)

Generated 2026-10-31 by `pipeline/scopes/score.py`; window (-700, 60, -480, 340) (game metres). Columns: live = deployed rows (release 23), v2 = the rows in the tile JSON now. Overlay `preview/scopes/duttweiler_overlay.png` (left live rows, right v2 rows; orthophoto, cadastre, LiDAR bridge class). Per-station tables `duttweiler_live_stations.tsv`, `duttweiler_v2_stations.tsv`.

## Scope B, cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS)

Objects in the fetch box: carriageway 10, deck 10, footway 21, island 21, path 2, pier 75, shelter 21, stairs 5, underpass 2, wall 33.

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Chains / stations in window | 1 / 98 | 1 / 113 | 2 m stations of the modelled axes inside the window |
| Footprint IoU vs AV ramp outline | 0.43 | 0.99 | per ramp station the modelled cross-section against the slice available to this ramp, overlaps over unions; 1 = identical outline |
| Footprint IoU / precision / recall vs all AV bridge polygons | 0.38 / 1.00 / 0.38 | 0.80 / 0.90 / 0.88 | polygons within 25 m of the modelled axes, main deck included; precision = share of the modelled footprint over a real deck |
| Footprint area model / AV outline / AV polygons (m²) | 1245 / 2870 / 3283 | 3200 / 2877 / 3283 |  |
| Structure length model / AV (m) | 196 / 196 | 222 / 196 | along the axis; model = elevated or solid stations, AV = axis inside a bridge polygon or between two thin bridge edge polygons |
| of which both / model only / AV only (m) | 196 / 0 / 0 | 196 / 26 / 0 | model only = modelled structure where AV has no bridge object (embankment, or an error); AV only = real structure modelled at grade |
| AV structure as edge polygons only (m) | 0 | 0 | axis between two thin «Brücke» polygons (< 1.5 m): ramp on fill between edge structures |
| AV structure width p50 (m, ramp stations) | 14.1 m | 14.1 m | stations where the slice available to this ramp (cadastre slice minus other road / foot rows) is 2–24 m wide (live 98, v2 98); slices crossed by another deck's axis: live 0, v2 0 |
| Modelled width p50 (m, same stations) | 6.4 m | 14.2 m | wl + wr (live rows: w) |
| Width error p50 / p95 |err| (m) | -7.7 m / 11.7 m | -0.0 m / 0.0 m | model minus AV structure width |
| Axis offset to AV centre line p50 / p95 (m) | 0.5 m / 0.6 m | 0.5 m / 0.6 m | distance between the modelled axis and the middle of the AV structure at the station |
| Edge overshoot p50 / p95 (m) | -3.3 m / -3.2 m | +0.0 m / +0.0 m | how far the wider modelled edge reaches beyond the AV edge (negative = inside) |
| Uncovered AV width p50 / p95 (m) | 3.8 m / 9.7 m | 0.0 m / 0.0 m | metres of the AV structure across the station covered by no deck row at all (this ramp or any other deck) |
| AV carriageway width p50 (m) | – (0 st.) | 16.3 m (15 st.) | Bodenbedeckung «Strasse, Weg» under the axis; only where present (not on decks) |
| Walls at the modelled edge left / right (m) | 0 / 0 | 2 / 26 | AV «Mauer» within 2.5 m of the modelled edge |
| Modelled solid length / with a wall (m) | 0 / 0 | 22 / 22 | solid = underside on the ground (embankment / skirt); a flanking wall confirms it |
| Modelled free deck with a wall at the edge (m) | 0 | 2 | walls flank embankments, not decks on piers: candidates for a solid section |
| AV piers near the axes: under deck / solid / grade / outside | 30: 14 / 0 / 0 / 16 | 30: 28 / 0 / 0 / 2 | piers within 12 m of a modelled axis, by the modelled class above them; outside = not under the modelled footprint |
| Tile pier rows near the axes / at an AV pier | 68 / 8 | 34 / 30 | modelled piers within 2 m of a cadastre pier polygon |
| AV piers with a modelled pier within 2 m | 8 / 30 | 30 / 30 |  |

### Landings (chain ends at grade or in the air, inside the window)

| rows | chain | end | modelled structure ends | AV structure ends | flanking walls end | end above game ground | end above LiDAR ground | terrain game − LiDAR at end |
|---|---|---|---|---|---|---|---|---|
| live | road (-412,581)->(-603,149) 512 m [grade/air] | air | +1.0 m | +1.0 m | +34.7 m | +4.3 m | – | – |
| v2 | road (-412,581)->(-617,123) 541 m [grade/grade] | grade | -3.0 m | -29.0 m | +5.0 m | +0.0 m | -0.2 m | -0.2 m |

Metres past the chain end along the road graph (negative = before the end; continuation 60 m). The AV structure ends where the axis leaves the last bridge polygon or edge-polygon pair; walls end where no «Mauer» lies within 10 m of the axis any more.

## Scope A, LiDAR (heights along the modelled axes)

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Stations with bridge class / ground class | 98 / 0 | 101 / 12 | central strip of the modelled width: class 17 present, else class 2 |
| Height residual on bridge class p50 / p95 |res| (m) | -0.0 m / 1.0 m | -0.0 m / 0.0 m | model minus LiDAR deck top (35th percentile of the strip) |
| Height residual on ground class p50 / p95 |res| (m) | – / – | -0.0 m / 0.2 m | model minus LiDAR ground where no deck class: embankment or at grade |
| Terrain game − LiDAR ground p50 / p95 |d| / max (m) | – / – / – (0 st.) | -1.3 m / 2.9 m / 3.0 m (12 st.) | game terrain under the axis vs LiDAR ground where the ground is visible (not under a deck): a terrain error, not a deck error |

## Chains

- live: road (-412,581)->(-603,149) 512 m [grade/air]; in window 196 m; outline IoU 0.41; uncovered p95 9.7 m; AV ramp width p50 14.1 m, modelled 6.4 m; axis offset p50 0.5 m, max 4.5 m; kinds grade/solid/deck 0/0/196 m
- v2: road (-412,581)->(-617,123) 541 m [grade/grade]; in window 226 m; outline IoU 0.88; uncovered p95 0.0 m; AV ramp width p50 14.1 m, modelled 14.2 m; axis offset p50 0.5 m, max 4.2 m; kinds grade/solid/deck 4/22/200 m; terrain -3.0 m low at s 519–531

## Verdict for the v2 rows: PASS

| Check | value | limit | ok |
|---|---|---|---|
| outline IoU | 0.99 | >= 0.8 | yes |
| edge overshoot p95 (m) | 0.0 | <= 0.5 | yes |
| uncovered width p95 (m, any deck row counts) | 0.0 | <= 2.0 | yes |
| height residual p95 (m, bridge class) | 0.0 | <= 0.3 | yes |
| cadastre piers under the deck with a modelled pier | 30/28 | all | yes |
| landing road (-412,581)->(-617,123)  (grade): cadastre / wall end beyond the modelled structure (m) | 5.0 | <= 5.0 | yes |

Thresholds from `README.md`; the ride gate is run separately. REVIEW names the measures to look at, nothing more.

## Scope C, imagery + vision helper

Not run yet (phase 3).

## Reading

What the scopes say (phase 1 diagnosis, phase 2 builder v2; 2026-10-31):

- **The deck ends where the live rows end, and the cadastre says what follows.** The «Brücke» polygon is 14.1 m wide along the south
  ramp and ends at (−603, 149): exactly where the live rows stop 4.3 m in the air. Beyond it two «Mauer» wing walls flank the axis
  (abutment); v2 continues 30 m along the road graph to grade, takes its width from the wing walls (about 10 m) where the cadastre has
  no bridge object, and models the abutment as a 22 m solid section: deck → walled abutment → grade. The game terrain at the landing
  is 3.0 m below the LiDAR ground over the last 12 m: terrain pass.
- **Width and outline.** Live 6.4 m vs 14.1 m; v2 14.2 m with edge overshoot p95 +0.0 m and nothing uncovered; station-wise outline IoU
  0.43 → 0.77 → 0.99, verdict PASS. The pilot's overshoot at the rail flyover crossing (LiDAR bands merging) is gone: v2 casts the normal against
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
