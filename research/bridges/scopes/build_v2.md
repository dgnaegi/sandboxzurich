# Builder v2 (pipeline/scopes/ramp_build.py): rows from cadastre edges and LiDAR heights

## gerold ('Geroldrampe')
- chain road (91,198)->(243,182) 162 m [junction/grade]
  - 164 m, width 6.1/11.0/13.9 m (min/med/max; live 35 vertices, 3.2 m); cadastre edges at 164 m (edge pairs 74 m); flush left/right 48/0 m; grade/solid/deck 8/66/90 m; ends junction/grade at +8.3/+0.0 m above ground; max slope 7 %
- chain road (160,216)->(142,278) 70 m [fork/junction]
  - 72 m, width 5.6/7.4/10.3 m (min/med/max; live 17 vertices, 3.2 m); cadastre edges at 72 m (edge pairs 0 m); flush left/right 54/0 m; grade/solid/deck 0/0/72 m; ends fork/junction at +5.5/+7.6 m above ground; max slope 7 %
- chain road (160,216)->(115,236) 49 m [fork/junction]
  - 52 m, width 4.2/9.0/9.5 m (min/med/max; live 12 vertices, 6.4 m); cadastre edges at 52 m (edge pairs 0 m); flush left/right 30/32 m; grade/solid/deck 0/0/52 m; ends fork/junction at +5.5/+8.0 m above ground; max slope 9 %
- piers: 13 from the cadastre under elevated deck sections, 10 live rule-spaced piers dropped

## duttweiler ('Duttweilerbrücke')
- chain road (-412,581)->(-603,149) 512 m [grade/air]
  - continuation at end: 30 m along the road graph to grade
  - 544 m, width 9.6/14.0/18.7 m (min/med/max; live 97 vertices, 6.4 m); cadastre edges at 468 m (edge pairs 0 m); flush left/right 2/6 m; grade/solid/deck 6/22/516 m; ends grade/grade at +0.0/+0.0 m above ground; max slope 10 %
- piers: 28 from the cadastre under elevated deck sections, 62 live rule-spaced piers dropped
- footway rows inside the new footprint dropped: 6

- restored t_1_1 from the original (not touched by this run)
- wrote t_0_1: dropped 3 rows, added 3, piers +12, props removed under the new decks 56
- wrote t_1_0: dropped 1 rows, added 1, piers +0, props removed under the new decks 3
- wrote t_0_0: dropped 2 rows, added 2, piers +1, props removed under the new decks 35
- wrote t_-3_0: dropped 2 rows, added 1, piers +1, props removed under the new decks 2
- wrote t_-3_1: dropped 3 rows, added 1, piers +12, props removed under the new decks 13
- wrote t_-3_2: dropped 5 rows, added 1, piers +14, props removed under the new decks 17
- wrote t_-4_0: dropped 1 rows, added 1, piers +1, props removed under the new decks 3
