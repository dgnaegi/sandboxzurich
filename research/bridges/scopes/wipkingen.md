# Scope report: Hardbrücke Nord: Hardturmrampe and Sihlquai ramps at the Wipkingerbrücke (`wipkingen`)

Generated 2026-10-31 by `pipeline/scopes/score.py`; window (290, 680, 620, 900) (game metres). Columns: live = deployed rows (release 23), v2 = the rows in the tile JSON now. Overlay `preview/scopes/wipkingen_overlay.png` (left live rows, right v2 rows; orthophoto, cadastre, LiDAR bridge class). Per-station tables `wipkingen_live_stations.tsv`, `wipkingen_v2_stations.tsv`.

## Scope B, cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS)

Objects in the fetch box: carriageway 9, deck 12, footway 17, island 15, path 11, pier 35, shelter 8, stairs 8, underpass 3, wall 16.

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Chains / stations in window | 3 / 269 | 3 / 269 | 2 m stations of the modelled axes inside the window |
| Footprint IoU vs AV ramp outline | 0.45 | 0.98 | per ramp station the modelled cross-section against the slice available to this ramp, overlaps over unions; 1 = identical outline |
| Footprint IoU / precision / recall vs all AV bridge polygons | 0.15 / 0.60 / 0.16 | 0.33 / 0.67 / 0.40 | polygons within 25 m of the modelled axes, main deck included; precision = share of the modelled footprint over a real deck |
| Footprint area model / AV outline / AV polygons (m²) | 1700 / 3364 / 6180 | 3678 / 3364 / 6180 |  |
| Structure length model / AV (m) | 510 / 524 | 508 / 524 | along the axis; model = elevated or solid stations, AV = axis inside a bridge polygon or between two thin bridge edge polygons |
| of which both / model only / AV only (m) | 510 / 0 / 14 | 508 / 0 / 16 | model only = modelled structure where AV has no bridge object (embankment, or an error); AV only = real structure modelled at grade |
| AV structure as edge polygons only (m) | 204 | 204 | axis between two thin «Brücke» polygons (< 1.5 m): ramp on fill between edge structures |
| AV structure width p50 (m, ramp stations) | 6.5 m | 6.5 m | stations where the slice available to this ramp (cadastre slice minus other road / foot rows) is 2–24 m wide (live 243, v2 243); slices crossed by another deck's axis: live 55, v2 55 |
| Modelled width p50 (m, same stations) | 3.2 m | 6.5 m | wl + wr (live rows: w) |
| Width error p50 / p95 |err| (m) | -3.3 m / 6.6 m | +0.0 m / 0.4 m | model minus AV structure width |
| Axis offset to AV centre line p50 / p95 (m) | 0.2 m / 1.9 m | 0.2 m / 1.9 m | distance between the modelled axis and the middle of the AV structure at the station |
| Edge overshoot p50 / p95 (m) | -1.5 m / -1.2 m | +0.0 m / +0.1 m | how far the wider modelled edge reaches beyond the AV edge (negative = inside) |
| Uncovered AV width p50 / p95 (m) | 3.3 m / 6.6 m | 0.0 m / 0.1 m | metres of the AV structure across the station covered by no deck row at all (this ramp or any other deck) |
| AV carriageway width p50 (m) | 5.6 m (155 st.) | 5.6 m (155 st.) | Bodenbedeckung «Strasse, Weg» under the axis; only where present (not on decks) |
| Walls at the modelled edge left / right (m) | 0 / 0 | 0 / 0 | AV «Mauer» within 2.5 m of the modelled edge |
| Modelled solid length / with a wall (m) | 166 / 0 | 188 / 0 | solid = underside on the ground (embankment / skirt); a flanking wall confirms it |
| Modelled free deck with a wall at the edge (m) | 0 | 0 | walls flank embankments, not decks on piers: candidates for a solid section |
| AV piers near the axes: under deck / solid / grade / outside | 18: 12 / 0 / 0 / 6 | 18: 14 / 0 / 0 / 4 | piers within 12 m of a modelled axis, by the modelled class above them; outside = not under the modelled footprint |
| Tile pier rows near the axes / at an AV pier | 23 / 8 | 17 / 15 | modelled piers within 2 m of a cadastre pier polygon |
| AV piers with a modelled pier within 2 m | 8 / 18 | 15 / 18 |  |

### Landings (chain ends at grade or in the air, inside the window)

| rows | chain | end | modelled structure ends | AV structure ends | flanking walls end | end above game ground | end above LiDAR ground | terrain game − LiDAR at end |
|---|---|---|---|---|---|---|---|---|
| live | road (409,697)->(584,732) 189 m [junction/grade] | grade | -5.0 m | -3.0 m | – | +0.1 m | +0.0 m | -0.1 m |
| live | road (461,795)->(301,793) 174 m [junction/grade] | grade | -11.0 m | -3.0 m | – | +0.1 m | +0.0 m | -0.0 m |
| live | road (602,731)->(478,805) 169 m [grade/junction] | grade | -9.0 m | -5.0 m | – | +0.1 m | +0.0 m | -0.1 m |
| v2 | road (409,697)->(584,732) 189 m [junction/grade] | grade | -7.0 m | -3.0 m | – | +0.0 m | -0.1 m | -0.1 m |
| v2 | road (461,795)->(301,793) 174 m [junction/grade] | grade | -11.0 m | -3.0 m | – | +0.0 m | -0.0 m | -0.0 m |
| v2 | road (602,731)->(478,805) 169 m [grade/junction] | grade | -9.0 m | -5.0 m | – | +0.0 m | -0.1 m | -0.1 m |

Metres past the chain end along the road graph (negative = before the end; continuation 60 m). The AV structure ends where the axis leaves the last bridge polygon or edge-polygon pair; walls end where no «Mauer» lies within 10 m of the axis any more.

## Scope A, LiDAR (heights along the modelled axes)

| Measure | live rows | v2 rows | reading |
|---|---|---|---|
| Stations with bridge class / ground class | 161 / 108 | 161 / 108 | central strip of the modelled width: class 17 present, else class 2 |
| Height residual on bridge class p50 / p95 |res| (m) | -0.0 m / 0.0 m | -0.0 m / 0.0 m | model minus LiDAR deck top (35th percentile of the strip) |
| Height residual on ground class p50 / p95 |res| (m) | -0.0 m / 0.0 m | -0.0 m / 0.1 m | model minus LiDAR ground where no deck class: embankment or at grade |
| Terrain game − LiDAR ground p50 / p95 |d| / max (m) | -1.6 m / 3.8 m / 4.5 m (109 st.) | -1.6 m / 3.8 m / 4.5 m (109 st.) | game terrain under the axis vs LiDAR ground where the ground is visible (not under a deck): a terrain error, not a deck error |

## Chains

- live: road (409,697)->(584,732) 189 m [junction/grade]; in window 192 m; outline IoU 0.44; uncovered p95 7.8 m; AV ramp width p50 6.3 m, modelled 3.2 m; axis offset p50 0.2 m, max 4.1 m; kinds grade/solid/deck 6/64/122 m; terrain -3.4 m low at s 122–157
- live: road (461,795)->(301,793) 174 m [junction/grade]; in window 176 m; outline IoU 0.42; uncovered p95 6.4 m; AV ramp width p50 6.8 m, modelled 3.2 m; axis offset p50 0.3 m, max 3.4 m; kinds grade/solid/deck 12/44/120 m; terrain -3.6 m low at s 116–150
- live: road (602,731)->(478,805) 169 m [grade/junction]; in window 170 m; outline IoU 0.44; uncovered p95 4.3 m; AV ramp width p50 6.5 m, modelled 3.2 m; axis offset p50 0.3 m, max 2.9 m; kinds grade/solid/deck 10/58/102 m; terrain -4.5 m low at s 26–86
- v2: road (409,697)->(584,732) 189 m [junction/grade]; in window 192 m; outline IoU 0.90; uncovered p95 0.0 m; AV ramp width p50 6.3 m, modelled 6.3 m; axis offset p50 0.2 m, max 4.1 m; kinds grade/solid/deck 8/62/122 m; terrain -3.4 m low at s 122–157
- v2: road (461,795)->(301,793) 174 m [junction/grade]; in window 176 m; outline IoU 0.92; uncovered p95 0.1 m; AV ramp width p50 6.8 m, modelled 6.9 m; axis offset p50 0.3 m, max 3.4 m; kinds grade/solid/deck 12/48/116 m; terrain -3.6 m low at s 116–150
- v2: road (602,731)->(478,805) 169 m [grade/junction]; in window 170 m; outline IoU 0.89; uncovered p95 0.2 m; AV ramp width p50 6.5 m, modelled 6.5 m; axis offset p50 0.3 m, max 2.9 m; kinds grade/solid/deck 10/78/82 m; terrain -4.5 m low at s 26–86

## Verdict for the v2 rows: PASS

| Check | value | limit | ok |
|---|---|---|---|
| outline IoU | 0.98 | >= 0.8 | yes |
| edge overshoot p95 (m) | 0.1 | <= 0.5 | yes |
| uncovered width p95 (m, any deck row counts) | 0.1 | <= 2.0 | yes |
| height residual p95 (m, bridge class) | 0.0 | <= 0.3 | yes |
| cadastre piers under the deck with a modelled pier | 15/14 | all | yes |
| landing road (409,697)->(584,732) 18 (grade): cadastre / wall end beyond the modelled structure (m) | 0.0 | <= 5.0 | yes |
| landing road (461,795)->(301,793) 17 (grade): cadastre / wall end beyond the modelled structure (m) | 0.0 | <= 5.0 | yes |
| landing road (602,731)->(478,805) 16 (grade): cadastre / wall end beyond the modelled structure (m) | 0.0 | <= 5.0 | yes |

Thresholds from `README.md`; the ride gate is run separately. REVIEW names the measures to look at, nothing more.

## Scope C, imagery + vision helper

Not run yet (phase 3).

## Reading

Transfer site 3 (2026-11-01): Hardbrücke Nord at the Wipkingerbrücke with three ramps meeting the viaduct: the Hardturmrampe
from the west, the Sihlquai-Südrampe and the Sihlquai-Nordrampe from the east. The LiDAR tiles were ordered with
`pipeline/scopes/lidar_for_sites.py` (three tiles).

- **What the cadastre shows.** Three ramp chains of 170 to 190 m, each from grade up to a junction with the viaduct deck 7 to 8 m
  up; long stretches between thin edge polygons (fill between edge structures: 56 to 82 m per ramp), the rest bridge polygons.
  The two Sihlquai ramps run side by side east of the viaduct at different grades (one climbing, one descending) inside what
  the cadastre merges into one structure.
- **What the builder did, unchanged.** Widths 3.2 → 6.3 to 6.8 m (p50) from the cadastre, fill parts solid, all three mouths
  on the viaduct opened. Outline IoU 0.89 to 0.92, uncovered ≤ 0.2 m, verdict PASS.
- **Rules that had to change for this site:** two, both about neighbours that are not one surface. A sibling chain's height
  is only adopted where the LiDAR on the own axis agrees within 0.35 m (the first run dragged the climbing Nordrampe down to the
  descending Südrampe, a 24 % step); and the main deck's carriageway rows cut a ramp's slice at their edge, so a merge lane
  reaches the carriageway and a station on the main deck itself stays a flush lane (this also closed the Geroldrampe's
  fork gore and junction patches, which the first version of the uncovered measure had blamed on the ramp).
- **Open:** the strip between the two Sihlquai ramps is air in reality but one cadastre structure; the scorer no longer counts
  it (each chain is measured on its own share), the builder leaves it empty, correctly.
