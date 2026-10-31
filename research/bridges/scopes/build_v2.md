# Builder v2 (pipeline/scopes/ramp_build.py): rows from cadastre edges and LiDAR heights

## gerold ('Geroldrampe')
- chain road (91,198)->(243,182) 162 m [junction/grade]
  - grade end extended 6 m to the end of the cadastre structure
  - 170 m, width 6.0/12.9/13.9 m (min/med/max; live 35 vertices, 3.2 m); cadastre edges at 170 m (edge pairs 80 m); flush left/right 48/8 m; grade/solid/deck 12/68/90 m; ends junction/grade at +8.3/+0.0 m above ground; max slope 7 %
- chain road (160,216)->(142,278) 70 m [fork/junction]
  - 72 m, width 5.6/7.4/10.3 m (min/med/max; live 17 vertices, 3.2 m); cadastre edges at 72 m (edge pairs 0 m); flush left/right 54/16 m; grade/solid/deck 0/0/72 m; ends fork/junction at +5.5/+7.6 m above ground; max slope 7 %
- chain road (160,216)->(115,236) 49 m [fork/junction]
  - 52 m, width 3.9/9.0/9.5 m (min/med/max; live 12 vertices, 6.4 m); cadastre edges at 52 m (edge pairs 0 m); flush left/right 32/34 m; grade/solid/deck 0/0/52 m; ends fork/junction at +5.5/+8.0 m above ground; max slope 21 %
- piers: 13 from the cadastre under elevated deck sections, 10 live rule-spaced piers dropped
- join: 0 ramp vertex sides flushed on other decks, 1 on sibling chains, 5 other rows and 3 site chains opened at a mouth
  - opened Hardbrücke (t_0_0 row 5) right side over 3.2 m at s 45–48
  - opened Hardbrücke (t_0_1 row 0) right side over 7.1 m at s 0–7
  - opened Hardbrücke (t_0_1 row 0) right side over 20.8 m at s 30–50
  - opened Hardbrücke (t_0_1 row 3) right side over 2.9 m at s 0–3
  - opened Hardbrücke (t_0_1 row 7) right side over 18.2 m at s 0–18
  - opened Hardbrücke (t_0_1 row 7) right side over 4.6 m at s 40–45
  - opened Hardbrücke (t_0_1 row 10) left side over 2.3 m at s 0–2
  - opened Geroldrampe chain 0 left side over 23.0 m at s 50–73
  - opened Geroldrampe chain 1 left side over 22.1 m at s 0–22
  - opened Geroldrampe chain 2 left side over 23.0 m at s 0–23
  - opened Geroldrampe chain 2 right side over 23.0 m at s 0–23

## duttweiler ('Duttweilerbrücke')
- chain road (-412,581)->(-603,149) 512 m [grade/air]
  - continuation at end: 30 m along the road graph to grade
  - 544 m, width 8.7/14.0/18.7 m (min/med/max; live 97 vertices, 6.4 m); cadastre edges at 468 m (edge pairs 0 m); flush left/right 2/6 m; grade/solid/deck 6/22/516 m; ends grade/grade at +0.0/+0.0 m above ground; max slope 10 %
- piers: 28 from the cadastre under elevated deck sections, 62 live rule-spaced piers dropped
- footway rows inside the new footprint dropped: 6
- join: 0 ramp vertex sides flushed on other decks, 0 on sibling chains, 0 other rows and 0 site chains opened at a mouth

## brauer ('Hohlstrasse')
- chain road (369,-487)->(306,-444) 77 m [junction/junction]
  - 78 m, width 6.4/6.4/14.8 m (min/med/max; live 17 vertices, 6.4 m); cadastre edges at 26 m (edge pairs 0 m); flush left/right 36/38 m; grade/solid/deck 8/44/26 m; ends junction/junction at +0.3/+0.1 m above ground; max slope 6 %
- chain road (369,-487)->(318,-441) 71 m [junction/grade]
  - 74 m, width 6.4/11.9/13.2 m (min/med/max; live 19 vertices, 6.4 m); cadastre edges at 26 m (edge pairs 0 m); flush left/right 34/8 m; grade/solid/deck 4/42/28 m; ends junction/grade at +0.3/+0.0 m above ground; max slope 10 %
- chain road (313,-454)->(369,-487) 66 m [grade/junction]
  - 68 m, width 3.2/7.8/9.2 m (min/med/max; live 16 vertices, 3.2 m); cadastre edges at 24 m (edge pairs 0 m); flush left/right 32/8 m; grade/solid/deck 2/42/24 m; ends grade/junction at +0.4/+0.3 m above ground; max slope 6 %
- piers: 0 from the cadastre under elevated deck sections, 11 live rule-spaced piers dropped
- join: 23 ramp vertex sides flushed on other decks, 25 on sibling chains, 2 other rows and 3 site chains opened at a mouth
  - opened tram (t_1_-3 row 5) left side over 78.9 m at s 2–81
  - opened tram (t_1_-3 row 5) right side over 78.6 m at s 2–80
  - opened tram (t_1_-3 row 6) left side over 79.3 m at s 4–83
  - opened tram (t_1_-3 row 6) right side over 80.7 m at s 2–83
  - opened Hohlstrasse chain 0 left side over 65.3 m at s 1–66
  - opened Hohlstrasse chain 0 right side over 14.0 m at s 0–14
  - opened Hohlstrasse chain 0 right side over 25.5 m at s 24–50
  - opened Hohlstrasse chain 1 left side over 14.9 m at s 0–15
  - opened Hohlstrasse chain 1 left side over 26.4 m at s 26–53
  - opened Hohlstrasse chain 1 right side over 1.7 m at s 1–3
  - opened Hohlstrasse chain 2 left side over 65.5 m at s 0–66
  - opened Hohlstrasse chain 2 right side over 6.1 m at s 41–47
  - opened Hohlstrasse chain 2 right side over 6.8 m at s 59–66

- restored t_1_1 from the original (not touched by this run)
- wrote t_1_0: dropped 1 rows, added 1, opened 0, piers +0, props removed under the new decks 3, static colliders 0
- wrote t_0_1: dropped 3 rows, added 3, opened 4, piers +12, props removed under the new decks 56, static colliders 22
- wrote t_0_0: dropped 2 rows, added 2, opened 1, piers +1, props removed under the new decks 35, static colliders 0
- wrote t_-3_2: dropped 5 rows, added 1, opened 0, piers +14, props removed under the new decks 17, static colliders 0
- wrote t_-3_0: dropped 2 rows, added 1, opened 0, piers +1, props removed under the new decks 2, static colliders 0
- wrote t_-3_1: dropped 3 rows, added 1, opened 0, piers +12, props removed under the new decks 13, static colliders 0
- wrote t_-4_0: dropped 1 rows, added 1, opened 0, piers +1, props removed under the new decks 3, static colliders 0
- wrote t_1_-3: dropped 3 rows, added 3, opened 2, piers +0, props removed under the new decks 13, static colliders 0
