# Scope report: Geroldrampe (Hardbrücke to Geroldstrasse, by the Freitag tower) (`gerold`)

Generated 2026-10-31 by `pipeline/scopes/score.py`; window (50, 150, 290, 310) (game metres). Columns: live = deployed rows (release 23), v2 = the rows in the tile JSON now. Overlay `preview/scopes/gerold_overlay.png` (left live rows, right v2 rows; orthophoto, cadastre, LiDAR bridge class). Per-station tables `gerold_live_stations.tsv`, `gerold_v2_stations.tsv`.

## Scope B, cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS)

Objects in the fetch box: carriageway 6, deck 13, footway 6, island 8, path 4, pier 34, shelter 13, stairs 3, underpass 1, wall 12.

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Chains / stations in window | 3 / 144 | 3 / 147 | 2 m stations of the modelled axes inside the window |
| Footprint IoU vs AV ramp outline | 0.37 | 0.98 | per ramp station the modelled cross-section against the slice available to this ramp, overlaps over unions; 1 = identical outline |
| Footprint IoU / precision / recall vs all AV bridge polygons | 0.14 / 0.77 / 0.15 | 0.25 / 0.61 / 0.30 | polygons within 25 m of the modelled axes, main deck included; precision = share of the modelled footprint over a real deck |
| Footprint area model / AV outline / AV polygons (m²) | 1031 / 2357 / 5411 | 2630 / 2444 / 5411 |  |
| Structure length model / AV (m) | 282 / 288 | 282 / 294 | along the axis; model = elevated or solid stations, AV = axis inside a bridge polygon or between two thin bridge edge polygons |
| of which both / model only / AV only (m) | 282 / 0 / 6 | 282 / 0 / 12 | model only = modelled structure where AV has no bridge object (embankment, or an error); AV only = real structure modelled at grade |
| AV structure as edge polygons only (m) | 74 | 80 | axis between two thin «Brücke» polygons (< 1.5 m): ramp on fill between edge structures |
| AV structure width p50 (m, ramp stations) | 8.0 m | 8.1 m | stations where the slice available to this ramp (cadastre slice minus other road / foot rows) is 2–24 m wide (live 128, v2 131); slices crossed by another deck's axis: live 31, v2 32 |
| Modelled width p50 (m, same stations) | 3.2 m | 8.1 m | wl + wr (live rows: w) |
| Width error p50 / p95 |err| (m) | -4.4 m / 10.7 m | +0.0 m / 1.0 m | model minus AV structure width |
| Axis offset to AV centre line p50 / p95 (m) | 1.1 m / 3.5 m | 1.1 m / 3.5 m | distance between the modelled axis and the middle of the AV structure at the station |
| Edge overshoot p50 / p95 (m) | -1.5 m / +1.1 m | +0.0 m / +0.0 m | how far the wider modelled edge reaches beyond the AV edge (negative = inside) |
| Uncovered AV width p50 / p95 (m) | 4.4 m / 10.7 m | 0.0 m / 0.5 m | metres of the AV structure across the station covered by no deck row at all (this ramp or any other deck) |
| AV carriageway width p50 (m) | 11.9 m (99 st.) | 12.4 m (102 st.) | Bodenbedeckung «Strasse, Weg» under the axis; only where present (not on decks) |
| Walls at the modelled edge left / right (m) | 0 / 0 | 0 / 0 | AV «Mauer» within 2.5 m of the modelled edge |
| Modelled solid length / with a wall (m) | 22 / 0 | 68 / 0 | solid = underside on the ground (embankment / skirt); a flanking wall confirms it |
| Modelled free deck with a wall at the edge (m) | 0 | 0 | walls flank embankments, not decks on piers: candidates for a solid section |
| AV piers near the axes: under deck / solid / grade / outside | 18: 10 / 0 / 0 / 8 | 18: 11 / 0 / 0 / 7 | piers within 12 m of a modelled axis, by the modelled class above them; outside = not under the modelled footprint |
| Tile pier rows near the axes / at an AV pier | 10 / 2 | 11 / 11 | modelled piers within 2 m of a cadastre pier polygon |
| AV piers with a modelled pier within 2 m | 3 / 18 | 11 / 18 |  |

### Landings (chain ends at grade or in the air, inside the window)

| rows | chain | end | modelled structure ends | AV structure ends | flanking walls end | end above game ground | end above LiDAR ground | terrain game − LiDAR at end |
|---|---|---|---|---|---|---|---|---|
| live | road (91,198)->(243,182) 162 m [junction/grade] | grade | -5.0 m | -5.0 m | – | +0.1 m | +0.0 m | -0.1 m |
| v2 | road (91,198)->(249,180) 168 m [junction/grade] | grade | -11.0 m | -11.0 m | – | +0.0 m | -0.0 m | -0.0 m |

Metres past the chain end along the road graph (negative = before the end; continuation 60 m). The AV structure ends where the axis leaves the last bridge polygon or edge-polygon pair; walls end where no «Mauer» lies within 10 m of the axis any more.

## Scope A, LiDAR (heights along the modelled axes)

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Stations with bridge class / ground class | 107 / 37 | 107 / 40 | central strip of the modelled width: class 17 present, else class 2 |
| Height residual on bridge class p50 / p95 |res| (m) | -0.0 m / 0.1 m | -0.0 m / 0.2 m | model minus LiDAR deck top (35th percentile of the strip) |
| Height residual on ground class p50 / p95 |res| (m) | -0.0 m / 0.0 m | -0.0 m / 0.0 m | model minus LiDAR ground where no deck class: embankment or at grade |
| Terrain game − LiDAR ground p50 / p95 |d| / max (m) | -1.3 m / 3.9 m / 4.2 m (46 st.) | -1.1 m / 3.9 m / 4.2 m (49 st.) | game terrain under the axis vs LiDAR ground where the ground is visible (not under a deck): a terrain error, not a deck error |

## Chains

- live: road (91,198)->(243,182) 162 m [junction/grade]; in window 164 m; outline IoU 0.29; uncovered p95 10.7 m; AV ramp width p50 13.0 m, modelled 3.2 m; axis offset p50 3.3 m, max 3.5 m; kinds grade/solid/deck 6/22/136 m; terrain -4.2 m low at s 90–140
- live: road (160,216)->(142,278) 70 m [fork/junction]; in window 72 m; outline IoU 0.37; uncovered p95 6.9 m; AV ramp width p50 7.1 m, modelled 3.2 m; axis offset p50 1.1 m, max 3.6 m; kinds grade/solid/deck 0/0/72 m
- live: road (160,216)->(115,236) 49 m [fork/junction]; in window 52 m; outline IoU 0.60; uncovered p95 4.9 m; AV ramp width p50 9.0 m, modelled 6.4 m; axis offset p50 0.2 m, max 3.8 m; kinds grade/solid/deck 0/0/52 m
- v2: road (91,198)->(249,180) 168 m [junction/grade]; in window 170 m; outline IoU 0.95; uncovered p95 0.1 m; AV ramp width p50 13.9 m, modelled 13.9 m; axis offset p50 3.3 m, max 3.5 m; kinds grade/solid/deck 12/68/90 m; terrain -4.2 m low at s 90–140
- v2: road (160,216)->(142,278) 70 m [fork/junction]; in window 72 m; outline IoU 0.79; uncovered p95 1.7 m; AV ramp width p50 7.1 m, modelled 7.1 m; axis offset p50 1.1 m, max 3.6 m; kinds grade/solid/deck 0/0/72 m
- v2: road (160,216)->(115,236) 49 m [fork/junction]; in window 52 m; outline IoU 0.79; uncovered p95 2.1 m; AV ramp width p50 9.0 m, modelled 8.7 m; axis offset p50 0.2 m, max 3.8 m; kinds grade/solid/deck 0/0/52 m

## Verdict for the v2 rows: PASS

| Check | value | limit | ok |
|---|---|---|---|
| outline IoU | 0.98 | >= 0.8 | yes |
| edge overshoot p95 (m) | 0.0 | <= 0.5 | yes |
| uncovered width p95 (m, any deck row counts) | 0.5 | <= 2.0 | yes |
| height residual p95 (m, bridge class) | 0.2 | <= 0.3 | yes |
| cadastre piers under the deck with a modelled pier | 11/11 | all | yes |
| landing road (91,198)->(249,180) 168 (grade): cadastre / wall end beyond the modelled structure (m) | 0.0 | <= 5.0 | yes |

Thresholds from `README.md`; the ride gate is run separately. REVIEW names the measures to look at, nothing more.

## Scope C, imagery + vision helper

Not run yet (phase 3).

## Reading

What the scopes say (phase 1 diagnosis, phase 2 builder v2; 2026-10-31):

- **The cadastre knows the whole ramp, in two kinds of object.** From the Hardbrücke down to x ≈ 176 the ramp is a «Brücke» polygon on
  piers. Below x ≈ 176 it is a pair of thin «Brücke» edge polygons 13.9 m apart with a «Strasse, Weg» polygon (11.9 m) between them:
  a ramp on fill between edge structures. LiDAR agrees: the bridge class ends at the same x, the ground class continues on top of
  the fill, and that fill surface lies up to 4.2 m above the game terrain (s 90–140). v2 models the fill part as a 66 m solid section
  (skirts to the terrain) and the upper part as a deck with 13 cadastre piers at their real positions.
- **Width and outline.** The structure is 13.9 m wide (p50) along the ramp; the live rows model a 3.2 m lane, the pilot 7.5 m, v2 the
  full width on the main chain (13.9 m) and never leaves the cadastre outline (edge overshoot p95 +0.4 m); station-wise outline IoU
  0.35 → 0.64 → 0.91 against the slice available to each chain (the Hardbrücke's carriageway subtracted, halved towards the sibling
  branch). What stays uncovered (p95 4.2 m, the one REVIEW) is the fork gore: the deck area between the two diverging branches is
  covered by neither row.
- **Joins (2026-11-01).** The pipeline only joins near-parallel decks, so the Hardbrücke's parapet and railing collider ran across
  the ramp mouths. `join.py` now opens the Hardbrücke rows exactly over the mouths (vertices inserted at the mouth edges, five rows,
  openings up to 21 m), opens the main chain where a branch leaves it, flushes both sides within 6 m of the fork, makes the branches
  coplanar with the main chain within 8 m, and removes the static collision posts under the fork nose that stopped the car. Both
  uphill car routes (local `logs/bridge_routes.json`) reach the Hardbrücke with 0 crashes; 0.4 m raw-height steps remain where the
  car changes between overlapping rows.
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
