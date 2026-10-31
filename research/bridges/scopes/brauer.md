# Scope report: Hohlstrasse bridge and Brauerstrasse ramp (over the Sihl line tracks) (`brauer`)

Generated 2026-10-31 by `pipeline/scopes/score.py`; window (285, -530, 425, -405) (game metres). Columns: live = deployed rows (release 23), v2 = the rows in the tile JSON now. Overlay `preview/scopes/brauer_overlay.png` (left live rows, right v2 rows; orthophoto, cadastre, LiDAR bridge class). Per-station tables `brauer_live_stations.tsv`, `brauer_v2_stations.tsv`.

## Scope B, cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS)

Objects in the fetch box: carriageway 10, deck 6, footway 14, island 7, path 1, underpass 2, wall 9.

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Chains / stations in window | 3 / 110 | 3 / 110 | 2 m stations of the modelled axes inside the window |
| Footprint IoU vs AV ramp outline | 0.54 | 0.99 | per ramp station the modelled cross-section against the slice available to this ramp, overlaps over unions; 1 = identical outline |
| Footprint IoU / precision / recall vs all AV bridge polygons | 0.28 / 0.37 / 0.53 | 0.43 / 0.44 / 0.93 | polygons within 25 m of the modelled axes, main deck included; precision = share of the modelled footprint over a real deck |
| Footprint area model / AV outline / AV polygons (m²) | 1099 / 648 / 764 | 1596 / 648 / 764 |  |
| Structure length model / AV (m) | 202 / 76 | 206 / 76 | along the axis; model = elevated or solid stations, AV = axis inside a bridge polygon or between two thin bridge edge polygons |
| of which both / model only / AV only (m) | 76 / 126 / 0 | 76 / 130 / 0 | model only = modelled structure where AV has no bridge object (embankment, or an error); AV only = real structure modelled at grade |
| AV structure as edge polygons only (m) | 0 | 0 | axis between two thin «Brücke» polygons (< 1.5 m): ramp on fill between edge structures |
| AV structure width p50 (m, ramp stations) | 8.7 m | 8.7 m | stations where the slice available to this ramp (cadastre slice minus other road / foot rows) is 2–24 m wide (live 38, v2 38); slices crossed by another deck's axis: live 38, v2 38 |
| Modelled width p50 (m, same stations) | 6.4 m | 8.8 m | wl + wr (live rows: w) |
| Width error p50 / p95 |err| (m) | -5.5 m / 6.3 m | +0.0 m / 0.4 m | model minus AV structure width |
| Axis offset to AV centre line p50 / p95 (m) | 1.9 m / 2.4 m | 1.9 m / 2.4 m | distance between the modelled axis and the middle of the AV structure at the station |
| Edge overshoot p50 / p95 (m) | -0.8 m / -0.8 m | -0.0 m / +0.0 m | how far the wider modelled edge reaches beyond the AV edge (negative = inside) |
| Uncovered AV width p50 / p95 (m) | 2.5 m / 3.3 m | 0.0 m / 0.0 m | metres of the AV structure across the station covered by no deck row at all (this ramp or any other deck) |
| AV carriageway width p50 (m) | 20.4 m (110 st.) | 20.4 m (110 st.) | Bodenbedeckung «Strasse, Weg» under the axis; only where present (not on decks) |
| Walls at the modelled edge left / right (m) | 0 / 0 | 8 / 30 | AV «Mauer» within 2.5 m of the modelled edge |
| Modelled solid length / with a wall (m) | 78 / 0 | 128 / 36 | solid = underside on the ground (embankment / skirt); a flanking wall confirms it |
| Modelled free deck with a wall at the edge (m) | 0 | 2 | walls flank embankments, not decks on piers: candidates for a solid section |
| AV piers near the axes: under deck / solid / grade / outside | 0: 0 / 0 / 0 / 0 | 0: 0 / 0 / 0 / 0 | piers within 12 m of a modelled axis, by the modelled class above them; outside = not under the modelled footprint |
| Tile pier rows near the axes / at an AV pier | 16 / 0 | 5 / 0 | modelled piers within 2 m of a cadastre pier polygon |
| AV piers with a modelled pier within 2 m | 0 / 0 | 0 / 0 |  |

### Landings (chain ends at grade or in the air, inside the window)

| rows | chain | end | modelled structure ends | AV structure ends | flanking walls end | end above game ground | end above LiDAR ground | terrain game − LiDAR at end |
|---|---|---|---|---|---|---|---|---|
| live | road (369,-487)->(318,-441) 71 m [junction/grade] | grade | -1.0 m | -18.8 m | -10.9 m | +0.0 m | -0.4 m | -0.4 m |
| live | road (313,-454)->(369,-487) 66 m [grade/junction] | grade | -3.0 m | -16.9 m | -10.9 m | +0.0 m | -0.4 m | -0.4 m |
| v2 | road (369,-487)->(318,-441) 71 m [junction/grade] | grade | -1.0 m | -18.8 m | -10.9 m | +0.0 m | -0.4 m | -0.4 m |
| v2 | road (313,-454)->(369,-487) 66 m [grade/junction] | grade | +1.0 m | -16.9 m | -10.9 m | +0.4 m | +0.0 m | -0.4 m |

Metres past the chain end along the road graph (negative = before the end; continuation 60 m). The AV structure ends where the axis leaves the last bridge polygon or edge-polygon pair; walls end where no «Mauer» lies within 10 m of the axis any more.

## Scope A, LiDAR (heights along the modelled axes)

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Stations with bridge class / ground class | 41 / 69 | 41 / 69 | central strip of the modelled width: class 17 present, else class 2 |
| Height residual on bridge class p50 / p95 |res| (m) | -0.0 m / 0.1 m | +0.0 m / 0.1 m | model minus LiDAR deck top (35th percentile of the strip) |
| Height residual on ground class p50 / p95 |res| (m) | -0.0 m / 0.3 m | +0.0 m / 0.2 m | model minus LiDAR ground where no deck class: embankment or at grade |
| Terrain game − LiDAR ground p50 / p95 |d| / max (m) | -1.2 m / 5.8 m / 6.6 m (71 st.) | -1.2 m / 5.8 m / 6.6 m (71 st.) | game terrain under the axis vs LiDAR ground where the ground is visible (not under a deck): a terrain error, not a deck error |

## Chains

- live: road (369,-487)->(306,-444) 77 m [junction/junction]; in window 78 m; outline IoU 0.27; uncovered p95 0.7 m; AV ramp width p50 6.5 m, modelled 6.4 m; axis offset p50 0.8 m, max 1.8 m; kinds grade/solid/deck 8/26/44 m; terrain -6.2 m low at s 10–22; terrain -5.0 m low at s 51–61
- live: road (369,-487)->(318,-441) 71 m [junction/grade]; in window 74 m; outline IoU 0.25; uncovered p95 3.3 m; AV ramp width p50 12.7 m, modelled 6.4 m; axis offset p50 2.3 m, max 2.4 m; kinds grade/solid/deck 4/30/40 m; terrain -6.6 m low at s 14–26; terrain -6.2 m low at s 53–65
- live: road (313,-454)->(369,-487) 66 m [grade/junction]; in window 68 m; outline IoU 0.21; uncovered p95 2.6 m; AV ramp width p50 8.7 m, modelled 3.2 m; axis offset p50 1.9 m, max 2.0 m; kinds grade/solid/deck 6/22/40 m; terrain -5.7 m low at s 6–16; terrain -5.3 m low at s 44–56
- v2: road (369,-487)->(306,-444) 77 m [junction/junction]; in window 78 m; outline IoU 0.27; uncovered p95 0.0 m; AV ramp width p50 6.5 m, modelled 6.5 m; axis offset p50 0.8 m, max 1.8 m; kinds grade/solid/deck 8/44/26 m; terrain -6.2 m low at s 10–22; terrain -5.0 m low at s 51–61
- v2: road (369,-487)->(318,-441) 71 m [junction/grade]; in window 74 m; outline IoU 0.42; uncovered p95 0.0 m; AV ramp width p50 12.7 m, modelled 12.7 m; axis offset p50 2.3 m, max 2.4 m; kinds grade/solid/deck 4/42/28 m; terrain -6.6 m low at s 14–26; terrain -6.2 m low at s 53–65
- v2: road (313,-454)->(369,-487) 66 m [grade/junction]; in window 68 m; outline IoU 0.44; uncovered p95 0.0 m; AV ramp width p50 8.7 m, modelled 8.8 m; axis offset p50 1.9 m, max 2.0 m; kinds grade/solid/deck 2/42/24 m; terrain -5.7 m low at s 6–16; terrain -5.3 m low at s 44–56

## Verdict for the v2 rows: PASS

| Check | value | limit | ok |
|---|---|---|---|
| outline IoU | 0.99 | >= 0.8 | yes |
| edge overshoot p95 (m) | 0.0 | <= 0.5 | yes |
| uncovered width p95 (m, any deck row counts) | 0.0 | <= 2.0 | yes |
| height residual p95 (m, bridge class) | 0.1 | <= 0.3 | yes |
| cadastre piers under the deck with a modelled pier | 0/0 | all | yes |
| landing road (369,-487)->(318,-441)  (grade): cadastre / wall end beyond the modelled structure (m) | 0.0 | <= 5.0 | yes |
| landing road (313,-454)->(369,-487)  (grade): cadastre / wall end beyond the modelled structure (m) | 0.0 | <= 5.0 | yes |

Thresholds from `README.md`; the ride gate is run separately. REVIEW names the measures to look at, nothing more.

## Scope C, imagery + vision helper

Not run yet (phase 3).

## Reading

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
