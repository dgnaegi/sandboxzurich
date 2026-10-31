# Scope report: Hardbrücke access ramp from Pfingstweidstrasse (`pfingstweid`)

Generated 2026-10-31 by `pipeline/scopes/score.py`; window (50, 170, 300, 440) (game metres). Columns: live = deployed rows (release 23), v2 = the rows in the tile JSON now. Overlay `preview/scopes/pfingstweid_overlay.png` (left live rows, right v2 rows; orthophoto, cadastre, LiDAR bridge class). Per-station tables `pfingstweid_live_stations.tsv`, `pfingstweid_v2_stations.tsv`.

## Scope B, cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS)

Objects in the fetch box: carriageway 10, deck 9, footway 16, island 20, path 6, pier 31, shelter 9, stairs 4, wall 10.

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Chains / stations in window | 1 / 74 | 1 / 74 | 2 m stations of the modelled axes inside the window |
| Footprint IoU vs AV ramp outline | 0.33 | 1.00 | per ramp station the modelled cross-section against the slice available to this ramp, overlaps over unions; 1 = identical outline |
| Footprint IoU / precision / recall vs all AV bridge polygons | 0.05 / 0.34 / 0.06 | 0.16 / 0.47 / 0.20 | polygons within 25 m of the modelled axes, main deck included; precision = share of the modelled footprint over a real deck |
| Footprint area model / AV outline / AV polygons (m²) | 509 / 1005 / 2828 | 1199 / 1006 / 2829 |  |
| Structure length model / AV (m) | 148 / 96 | 148 / 96 | along the axis; model = elevated or solid stations, AV = axis inside a bridge polygon or between two thin bridge edge polygons |
| of which both / model only / AV only (m) | 96 / 52 / 0 | 96 / 52 / 0 | model only = modelled structure where AV has no bridge object (embankment, or an error); AV only = real structure modelled at grade |
| AV structure as edge polygons only (m) | 46 | 46 | axis between two thin «Brücke» polygons (< 1.5 m): ramp on fill between edge structures |
| AV structure width p50 (m, ramp stations) | 10.0 m | 10.0 m | stations where the slice available to this ramp (cadastre slice minus other road / foot rows) is 2–24 m wide (live 48, v2 48); slices crossed by another deck's axis: live 18, v2 18 |
| Modelled width p50 (m, same stations) | 3.5 m | 10.0 m | wl + wr (live rows: w) |
| Width error p50 / p95 |err| (m) | -6.5 m / 8.0 m | +0.0 m / 0.0 m | model minus AV structure width |
| Axis offset to AV centre line p50 / p95 (m) | 1.6 m / 1.6 m | 1.6 m / 1.6 m | distance between the modelled axis and the middle of the AV structure at the station |
| Edge overshoot p50 / p95 (m) | -1.7 m / -1.6 m | +0.0 m / +0.0 m | how far the wider modelled edge reaches beyond the AV edge (negative = inside) |
| Uncovered AV width p50 / p95 (m) | 3.5 m / 5.0 m | 0.0 m / 0.0 m | metres of the AV structure across the station covered by no deck row at all (this ramp or any other deck) |
| AV carriageway width p50 (m) | 6.1 m (23 st.) | 6.1 m (23 st.) | Bodenbedeckung «Strasse, Weg» under the axis; only where present (not on decks) |
| Walls at the modelled edge left / right (m) | 0 / 0 | 0 / 0 | AV «Mauer» within 2.5 m of the modelled edge |
| Modelled solid length / with a wall (m) | 38 / 0 | 46 / 0 | solid = underside on the ground (embankment / skirt); a flanking wall confirms it |
| Modelled free deck with a wall at the edge (m) | 0 | 0 | walls flank embankments, not decks on piers: candidates for a solid section |
| AV piers near the axes: under deck / solid / grade / outside | 5: 1 / 0 / 0 / 4 | 5: 1 / 0 / 0 / 4 | piers within 12 m of a modelled axis, by the modelled class above them; outside = not under the modelled footprint |
| Tile pier rows near the axes / at an AV pier | 11 / 0 | 6 / 1 | modelled piers within 2 m of a cadastre pier polygon |
| AV piers with a modelled pier within 2 m | 0 / 5 | 1 / 5 |  |

### Landings (chain ends at grade or in the air, inside the window)

| rows | chain | end | modelled structure ends | AV structure ends | flanking walls end | end above game ground | end above LiDAR ground | terrain game − LiDAR at end |
|---|---|---|---|---|---|---|---|---|

Metres past the chain end along the road graph (negative = before the end; continuation 60 m). The AV structure ends where the axis leaves the last bridge polygon or edge-polygon pair; walls end where no «Mauer» lies within 10 m of the axis any more.

## Scope A, LiDAR (heights along the modelled axes)

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Stations with bridge class / ground class | 68 / 6 | 68 / 6 | central strip of the modelled width: class 17 present, else class 2 |
| Height residual on bridge class p50 / p95 |res| (m) | -0.0 m / 0.0 m | -0.0 m / 0.0 m | model minus LiDAR deck top (35th percentile of the strip) |
| Height residual on ground class p50 / p95 |res| (m) | -0.0 m / 0.0 m | -0.0 m / 0.1 m | model minus LiDAR ground where no deck class: embankment or at grade |
| Terrain game − LiDAR ground p50 / p95 |d| / max (m) | -1.1 m / 1.5 m / 1.5 m (6 st.) | -1.1 m / 1.5 m / 1.5 m (6 st.) | game terrain under the axis vs LiDAR ground where the ground is visible (not under a deck): a terrain error, not a deck error |

## Chains

- live: road (140,310)->(62,187) 145 m [junction/junction]; in window 148 m; outline IoU 0.28; uncovered p95 5.0 m; AV ramp width p50 10.0 m, modelled 3.5 m; axis offset p50 1.6 m, max 2.5 m; kinds grade/solid/deck 0/38/110 m; terrain -1.5 m low at s 4–10
- v2: road (140,310)->(62,187) 145 m [junction/junction]; in window 148 m; outline IoU 0.84; uncovered p95 0.0 m; AV ramp width p50 10.0 m, modelled 10.0 m; axis offset p50 1.6 m, max 2.5 m; kinds grade/solid/deck 0/46/102 m; terrain -1.5 m low at s 4–10

## Verdict for the v2 rows: PASS

| Check | value | limit | ok |
|---|---|---|---|
| outline IoU | 1.00 | >= 0.8 | yes |
| edge overshoot p95 (m) | 0.0 | <= 0.5 | yes |
| uncovered width p95 (m, any deck row counts) | 0.0 | <= 2.0 | yes |
| height residual p95 (m, bridge class) | 0.0 | <= 0.3 | yes |
| cadastre piers under the deck with a modelled pier | 1/1 | all | yes |

Thresholds from `README.md`; the ride gate is run separately. REVIEW names the measures to look at, nothing more.

## Scope C, imagery + vision helper

Not run yet (phase 3).

## Reading

Transfer site 2 (2026-11-01): the Hardbrücke access ramp from Pfingstweidstrasse, the ramp the maintainer's first bridge-ramp
round fixed by hand ("graue Platte auf Kopfhöhe, Bäume im Deck, Knick", `research/bridges/ramp_fix.md`). Unnamed OSM rows, so
the site is selected by a seed point (`ramp_sites.py`: `match ""` plus `seed`).

- **What the cadastre shows.** One chain of 145 m from the ramp foot near Pfingstweidstrasse (140, 310), 0.8 m above the terrain,
  up to the Hardbrücke deck at (62, 187), 8.9 m up, along the west side of the viaduct. The lower 46 m lie between two thin
  «Brücke» edge polygons (a ramp on fill between its edge structures, like the lower Geroldrampe), the upper part is a bridge
  polygon on one cadastre pier.
- **What the builder did, unchanged.** Width 3.5 → 10.0 m (p50) from the cadastre, the fill part solid, the upper part a deck,
  both ends joined (the Hardbrücke's parapet opened over the mouth, four rows). Outline IoU 0.84, nothing uncovered, edge
  overshoot p95 within the limit, heights on the LiDAR deck top, verdict PASS.
- **Rules that had to change for this site:** none in the builder; the site registry learnt to select unnamed rows by a seed.
