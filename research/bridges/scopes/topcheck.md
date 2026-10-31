# Top-down check (`pipeline/scopes/topcheck.py`)

Last run 2026-10-31 on the integrated dev tiles. Drawn decks from above against the cadastre bridge outlines and the LiDAR surface; sheets in `data/build/scopes/topcheck/<site>.png`, finding ids and positions in `<site>.json`. Gating findings as count / m² (steps: count / m).

| site | verdict | AV bridge covered | interior holes | edge holes | below LiDAR | steps | invisible walls | sink | terrain over deck m² | rail-bridge holes | AV bridges not modelled |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_hardbrucke | FAIL | 83% | 3 / 18 | 11 / 3438 | 34 / 757 | 15 / 172 | 9 / 25 | 5 / 21 | 955 | 46 | 24 |
| auto_hardbrucke_hardplatz | FAIL | 98% | 1 / 8 | 2 / 25 | 6 / 78 | 4 / 15 | 6 / 10 | 5 / 24 | 64 | 0 | 4 |
| auto_hardbrucke_hardplatz_live | FAIL | 75% | – | 6 / 1448 | 9 / 2068 | 2 / 17 | 6 / 21 | – | 127 | 0 | 7 |
| auto_kornhausbrucke | FAIL | 82% | – | 1 / 539 | 8 / 612 | – | 2 / 10 | – | 14 | 0 | 6 |
| duttweiler | FAIL | 96% | – | 3 / 23 | 9 / 214 | – | – | – | 0 | 20 | 2 |
| gerold | FAIL | 94% | 2 / 9 | 6 / 104 | 5 / 116 | 4 / 32 | 3 / 5 | – | 334 | 0 | 3 |
