# Top-down check (`pipeline/scopes/topcheck.py`)

Last run 2026-10-31 on the integrated dev tiles. Drawn decks from above against the cadastre bridge outlines and the LiDAR surface; sheets in `data/build/scopes/topcheck/<site>.png`, finding ids and positions in `<site>.json`. Gating findings as count / m² (steps: count / m).

| site | verdict | AV bridge covered | interior holes | edge holes | below LiDAR | steps | invisible walls | sink | terrain over deck m² | rail-bridge holes | AV bridges not modelled |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_hardbrucke | FAIL | 82% | 5 / 104 | 13 / 3623 | 38 / 1079 | 12 / 174 | 24 / 111 | 7 / 49 | 938 | 46 | 27 |
| auto_kornhausbrucke | FAIL | 82% | – | 1 / 539 | 10 / 683 | – | 2 / 10 | – | 14 | 0 | 6 |
| duttweiler | FAIL | 96% | – | 3 / 23 | 9 / 267 | – | – | – | 0 | 20 | 2 |
| gerold | FAIL | 91% | 2 / 87 | 7 / 256 | 7 / 285 | 2 / 22 | 7 / 53 | 2 / 10 | 328 | 0 | 4 |
