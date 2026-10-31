# Scope report: Geroldrampe (Hardbrücke to Geroldstrasse, by the Freitag tower) (`gerold`)

Generated 2026-10-31 by `pipeline/scopes/score.py`; window (50, 150, 290, 310) (game metres). Overlay `preview/scopes/gerold_overlay.png` (left live rows, right pilot rows; orthophoto, cadastre, LiDAR bridge class). Per-station tables `gerold_live_stations.tsv`, `gerold_pilot_stations.tsv`.

## Scope B, cadastre (Amtliche Vermessung, Kanton Zürich OGD-WFS)

Objects in the fetch box: carriageway 6, deck 13, footway 6, island 8, path 4, pier 34, shelter 13, stairs 3, underpass 1, wall 12.

| Measure | live rows | pilot rows | reading |
|---|---|---|---|
| Chains / stations in window | 3 / 144 | 4 / 187 | 2 m stations of the modelled axes inside the window |
| Footprint IoU vs AV ramp outline | 0.30 | 0.64 | AV structure cross-sections along the modelled axes (ramp stations); 1 = identical outline |
| Footprint IoU / precision / recall vs all AV bridge polygons | 0.14 / 0.77 / 0.15 | 0.24 / 0.68 / 0.27 | polygons within 25 m of the modelled axes, main deck included; precision = share of the modelled footprint over a real deck |
| Footprint area model / AV outline / AV polygons (m²) | 1031 / 2266 / 5411 | 2175 / 2245 / 5411 |  |
| Structure length model / AV (m) | 282 / 288 | 358 / 374 | along the axis; model = elevated or solid stations, AV = axis inside a bridge polygon or between two thin bridge edge polygons |
| of which both / model only / AV only (m) | 282 / 0 / 6 | 358 / 0 / 16 | model only = modelled structure where AV has no bridge object (embankment, or an error); AV only = real structure modelled at grade |
| AV structure as edge polygons only (m) | 74 | 142 | axis between two thin «Brücke» polygons (< 1.5 m): ramp on fill between edge structures |
| AV structure width p50 (m, ramp stations) | 13.9 m | 13.9 m | stations where the AV structure is narrower than 24 m (live 106, pilot 148) |
| Modelled width p50 (m, same stations) | 3.2 m | 7.5 m | wl + wr (live rows: w) |
| Width error p50 / p95 |err| (m) | -10.7 m / 18.3 m | -5.5 m / 15.1 m | model minus AV structure width |
| Axis offset to AV centre line p50 / p95 (m) | 3.4 m / 5.7 m | 2.0 m / 5.5 m | distance between the modelled axis and the middle of the AV structure at the station |
| Edge overshoot p50 / p95 (m) | -2.0 m / -1.7 m | -1.3 m / -0.0 m | how far the wider modelled edge reaches beyond the AV edge (negative = inside) |
| Uncovered AV width p50 / p95 (m) | +8.7 m / +14.6 m | +3.6 m / +13.5 m | AV structure left uncovered on the worse side (negative = model wider) |
| AV carriageway width p50 (m) | 11.9 m (99 st.) | 16.8 m (140 st.) | Bodenbedeckung «Strasse, Weg» under the axis; only where present (not on decks) |
| Walls at the modelled edge left / right (m) | 0 / 0 | 0 / 0 | AV «Mauer» within 2.5 m of the modelled edge |
| Modelled solid length / with a wall (m) | 22 / 0 | 126 / 0 | solid = underside on the ground (embankment / skirt); a flanking wall confirms it |
| Modelled free deck with a wall at the edge (m) | 0 | 0 | walls flank embankments, not decks on piers: candidates for a solid section |
| AV piers near the axes: under deck / solid / grade / outside | 18: 10 / 0 / 0 / 8 | 18: 10 / 0 / 0 / 8 | piers within 12 m of a modelled axis, by the modelled class above them; outside = not under the modelled footprint |
| Tile pier rows near the axes / at an AV pier | 10 / 2 | 10 / 2 | modelled piers within 2 m of a cadastre pier polygon (the pilot kept the live piers) |
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

- live: road (91,198)->(243,182) 162 m [junction/grade]; in window 164 m; AV ramp width p50 13.9 m, modelled 3.2 m; axis offset p50 3.4 m, max 6.7 m; kinds grade/solid/deck 6/22/136 m; terrain -4.2 m low at s 90–140
- live: road (160,216)->(142,278) 70 m [fork/junction]; in window 72 m; AV ramp width p50 18.0 m, modelled 3.2 m; axis offset p50 3.3 m, max 7.7 m; kinds grade/solid/deck 0/0/72 m
- live: road (160,216)->(115,236) 49 m [fork/junction]; in window 52 m; AV ramp width p50 15.8 m, modelled 6.4 m; axis offset p50 0.8 m, max 5.4 m; kinds grade/solid/deck 0/0/52 m
- pilot: road (91,198)->(243,182) 162 m [junction/grade]; in window 164 m; AV ramp width p50 13.9 m, modelled 7.5 m; axis offset p50 2.1 m, max 6.6 m; kinds grade/solid/deck 10/64/90 m; terrain -4.2 m low at s 90–140
- pilot: road (160,216)->(240,189) 84 m [fork/grade]; in window 86 m; AV ramp width p50 13.9 m, modelled 8.1 m; axis offset p50 2.0 m, max 2.4 m; kinds grade/solid/deck 6/62/18 m; terrain -4.2 m low at s 18–68
- pilot: road (160,216)->(142,278) 70 m [fork/junction]; in window 72 m; AV ramp width p50 18.0 m, modelled 4.9 m; axis offset p50 3.3 m, max 7.7 m; kinds grade/solid/deck 0/0/72 m
- pilot: road (160,216)->(115,236) 49 m [fork/junction]; in window 52 m; AV ramp width p50 15.8 m, modelled 11.1 m; axis offset p50 0.8 m, max 5.4 m; kinds grade/solid/deck 0/0/52 m

## Scope C, imagery + vision helper

Not run yet (phase 3).

## Reading

What Scope B adds to the pilot verdict (phase 1 diagnosis, 2026-10-31):

- **The cadastre knows the whole ramp, in two kinds of object.** From the Hardbrücke down to x ≈ 176 the ramp is a «Brücke» polygon on
  piers (10 cadastre piers stand under the modelled deck). Below x ≈ 176 it is a pair of thin «Brücke» edge polygons 13.9 m apart with
  a «Strasse, Weg» polygon (11.9 m) between them: a ramp on fill between edge structures. LiDAR agrees: the bridge class ends at the
  same x, the ground class continues on top of the fill, and that fill surface lies up to 4.2 m above the game terrain (main chain
  s 90–140). The pilot's solid skirt below the fork was right; it stops 5–9 m before the modelled grade end while the edge polygons
  run 7 m (main chain) and 13 m (continuation) past it, down to Geroldstrasse. The game terrain under the fill is a terrain-pass issue
  only as long as the skirt is solid.
- **Width and outline.** The structure is 13.9 m wide (p50) along the entire ramp; the live rows model a 3.2 m lane, the pilot 7.5 m
  (8–11 m on the deck, 8 m on the fill). The pilot never leaves the cadastre outline (edge overshoot p95 −0.0 m) but leaves 3.6 m (p50)
  of structure uncovered on one side, because the OSM axis is a one-way lane 2.0 m (p50) off the structure's centre line. Outline IoU
  0.30 → 0.64. Builder v2: edges from the cadastre (per-vertex `wl`/`wr` measured from the OSM axis to the AV edges), axis stays on OSM.
- **Axis.** Offsets above 4 m occur only at the fork (main chain s 50–70, around (147,214)) and where the north branch runs inside the
  Hardbrücke's own polygon (branch s 6–22 and 66–68): there the "centre line" of the merged structure means nothing. Elsewhere the
  offset is a steady 1–3 m lane offset, not jitter; the ±1 m jitter of the pilot tracker is below the 2 m station spacing and shows
  only in the screenshots.
- **Branches onto the Hardbrücke.** Both upper branches lie inside the Hardbrücke bridge polygon (structure 15.8 m and 18 m wide beside
  the main deck, > 24 m where they merge). They should become flush with the Hardbrücke deck (row keys `ol`/`or`), not separate decks
  with their own edges.
- **Piers.** 18 cadastre piers within 12 m of the axes, 10 under the modelled deck, 8 are Hardbrücke piers 4.4–11.6 m off the branch
  axes. Of the 10 tile piers only 2 stand at a real pier; 4 stand under the fill part where there is no pier at all. Builder v2: piers
  from AV «Pfeiler», none under the fill.
- **Walls.** No «Mauer» belongs to the ramp; the edge structures are the thin bridge polygons. The walls at (170–200, 230–235) are a
  neighbouring plot's.
- **What Scope B cannot give.** On the deck proper the Bodenbedeckung is the ground below, so the lane / footway split of the deck
  (footway side, parapet type) has to come from Scope C (imagery) or LiDAR intensity. Heights are already right (Scope A residual
  p95 0.1–0.2 m for both row sets, the live decks use `_lidar_decks`).
