# Scope report: Geroldrampe (Hardbrücke to Geroldstrasse, by the Freitag tower) (`gerold`)

Generated 2026-10-31 by `pipeline/scopes/score.py`; window (50, 150, 290, 310) (game metres). Columns: live = deployed rows (release 23), pilot = the rows in the tile JSON now. Overlay `preview/scopes/gerold_overlay.png` (left live rows, right pilot rows; orthophoto, cadastre, LiDAR bridge class). Per-station tables `gerold_live_stations.tsv`, `gerold_pilot_stations.tsv`.

## Scope B, cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS)

Objects in the fetch box: carriageway 6, deck 13, footway 6, island 8, path 4, pier 34, shelter 13, stairs 3, underpass 1, wall 12.

| Measure | live rows | pilot rows | reading |
|---|---|---|---|
| Chains / stations in window | 3 / 144 | 4 / 187 | 2 m stations of the modelled axes inside the window |
| Footprint IoU vs AV ramp outline | 0.31 | 0.64 | AV structure cross-sections along the modelled axes (ramp stations); 1 = identical outline |
| Footprint IoU / precision / recall vs all AV bridge polygons | 0.14 / 0.77 / 0.15 | 0.24 / 0.68 / 0.27 | polygons within 25 m of the modelled axes, main deck included; precision = share of the modelled footprint over a real deck |
| Footprint area model / AV outline / AV polygons (m²) | 1031 / 2250 / 5411 | 2175 / 2254 / 5411 |  |
| Structure length model / AV (m) | 282 / 288 | 358 / 374 | along the axis; model = elevated or solid stations, AV = axis inside a bridge polygon or between two thin bridge edge polygons |
| of which both / model only / AV only (m) | 282 / 0 / 6 | 358 / 0 / 16 | model only = modelled structure where AV has no bridge object (embankment, or an error); AV only = real structure modelled at grade |
| AV structure as edge polygons only (m) | 74 | 142 | axis between two thin «Brücke» polygons (< 1.5 m): ramp on fill between edge structures |
| AV structure width p50 (m, ramp stations) | 13.9 m | 13.9 m | stations where the AV structure is narrower than 24 m (live 109, pilot 152) |
| Modelled width p50 (m, same stations) | 3.2 m | 7.5 m | wl + wr (live rows: w) |
| Width error p50 / p95 |err| (m) | -10.7 m / 19.2 m | -5.5 m / 16.4 m | model minus AV structure width |
| Axis offset to AV centre line p50 / p95 (m) | 3.4 m / 5.9 m | 2.0 m / 5.6 m | distance between the modelled axis and the middle of the AV structure at the station |
| Edge overshoot p50 / p95 (m) | -1.9 m / -1.1 m | -1.1 m / +0.5 m | how far the wider modelled edge reaches beyond the AV edge (negative = inside) |
| Uncovered AV width p50 / p95 (m) | +8.7 m / +15.1 m | +3.5 m / +13.7 m | AV structure left uncovered on the worse side (negative = model wider) |
| AV carriageway width p50 (m) | 11.9 m (99 st.) | 16.8 m (140 st.) | Bodenbedeckung «Strasse, Weg» under the axis; only where present (not on decks) |
| Walls at the modelled edge left / right (m) | 0 / 0 | 0 / 0 | AV «Mauer» within 2.5 m of the modelled edge |
| Modelled solid length / with a wall (m) | 22 / 0 | 126 / 0 | solid = underside on the ground (embankment / skirt); a flanking wall confirms it |
| Modelled free deck with a wall at the edge (m) | 0 | 0 | walls flank embankments, not decks on piers: candidates for a solid section |
| AV piers near the axes: under deck / solid / grade / outside | 18: 10 / 0 / 0 / 8 | 18: 10 / 0 / 0 / 8 | piers within 12 m of a modelled axis, by the modelled class above them; outside = not under the modelled footprint |
| Tile pier rows near the axes / at an AV pier | 10 / 2 | 10 / 2 | modelled piers within 2 m of a cadastre pier polygon |
| AV piers with a modelled pier within 2 m | 3 / 18 | 3 / 18 |  |

### Landings (chain ends at grade or in the air, inside the window)

| rows | chain | end | modelled structure ends | AV structure ends | flanking walls end | end above game ground | end above LiDAR ground | terrain game − LiDAR at end |
|---|---|---|---|---|---|---|---|---|
| live | road (91,198)->(243,182) 162 m [junction/grade] | grade | -5.0 m | +7.0 m | – | +0.1 m | +0.0 m | -0.1 m |
| pilot | road (91,198)->(243,182) 162 m [junction/grade] | grade | -9.0 m | +7.0 m | – | +0.0 m | -0.1 m | -0.1 m |
| pilot | road (160,216)->(240,189) 84 m [fork/grade] | grade | -5.0 m | +13.0 m | – | +0.0 m | -0.3 m | -0.3 m |

Metres past the chain end along the road graph (negative = before the end; continuation 60 m). The AV structure ends where the axis leaves the last bridge polygon or edge-polygon pair; walls end where no «Mauer» lies within 10 m of the axis any more.

## Scope A, LiDAR (heights along the modelled axes)

| Measure | live rows | pilot rows | reading |
|---|---|---|---|
| Stations with bridge class / ground class | 107 / 37 | 116 / 71 | central strip of the modelled width: class 17 present, else class 2 |
| Height residual on bridge class p50 / p95 |res| (m) | -0.0 m / 0.1 m | +0.0 m / 0.2 m | model minus LiDAR deck top (35th percentile of the strip) |
| Height residual on ground class p50 / p95 |res| (m) | -0.0 m / 0.0 m | -0.0 m / 0.1 m | model minus LiDAR ground where no deck class: embankment or at grade |
| Terrain game − LiDAR ground p50 / p95 |d| / max (m) | -1.3 m / 3.9 m / 4.2 m (46 st.) | -1.7 m / 4.0 m / 4.2 m (80 st.) | game terrain under the axis vs LiDAR ground where the ground is visible (not under a deck): a terrain error, not a deck error |

## Chains

- live: road (91,198)->(243,182) 162 m [junction/grade]; in window 164 m; AV ramp width p50 13.9 m, modelled 3.2 m; axis offset p50 3.4 m, max 8.1 m; kinds grade/solid/deck 6/22/136 m; terrain -4.2 m low at s 90–140
- live: road (160,216)->(142,278) 70 m [fork/junction]; in window 72 m; AV ramp width p50 16.8 m, modelled 3.2 m; axis offset p50 3.3 m, max 7.6 m; kinds grade/solid/deck 0/0/72 m
- live: road (160,216)->(115,236) 49 m [fork/junction]; in window 52 m; AV ramp width p50 11.8 m, modelled 6.4 m; axis offset p50 0.5 m, max 1.4 m; kinds grade/solid/deck 0/0/52 m
- pilot: road (91,198)->(243,182) 162 m [junction/grade]; in window 164 m; AV ramp width p50 13.9 m, modelled 7.5 m; axis offset p50 2.1 m, max 7.9 m; kinds grade/solid/deck 10/64/90 m; terrain -4.2 m low at s 90–140
- pilot: road (160,216)->(240,189) 84 m [fork/grade]; in window 86 m; AV ramp width p50 13.9 m, modelled 8.1 m; axis offset p50 2.0 m, max 2.4 m; kinds grade/solid/deck 6/62/18 m; terrain -4.2 m low at s 18–68
- pilot: road (160,216)->(142,278) 70 m [fork/junction]; in window 72 m; AV ramp width p50 16.8 m, modelled 4.5 m; axis offset p50 3.3 m, max 7.6 m; kinds grade/solid/deck 0/0/72 m
- pilot: road (160,216)->(115,236) 49 m [fork/junction]; in window 52 m; AV ramp width p50 11.8 m, modelled 11.1 m; axis offset p50 0.5 m, max 1.4 m; kinds grade/solid/deck 0/0/52 m

## Scope C, imagery + vision helper

Not run yet (phase 3).
