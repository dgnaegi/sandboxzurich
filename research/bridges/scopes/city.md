# City-wide run of the ramp builder

Generated 2026-10-31 by `pipeline/scopes/city.py`: every site built and scored on its own against the live world (scratch copy of the tiles); automatic sites from `pipeline/scopes/discover.py`. Full reports in `data/build/scopes/city/reports/` (not in git; rerun to regenerate).

Count: no LiDAR 23, PASS 7 of 30 sites.

| Site | kind | verdict | outline IoU live → v2 | width live → v2 (cadastre) | piers modelled / under deck | height p95 | failing checks |
|---|---|---|---|---|---|---|---|
| Geroldrampe (Hardbrücke to Geroldstrasse, by the Freitag tower) (`gerold`) | hand | PASS | 0.37 → 0.98 | 3.2 → 8.1 (8.1) m | 11 / 11 | 0.17 m |  |
| Duttweilerbrücke south ramp (`duttweiler`) | hand | PASS | 0.43 → 0.99 | 6.4 → 14.0 (14.1) m | 30 / 28 | 0.01 m |  |
| Hardbrücke access ramp from Pfingstweidstrasse (`pfingstweid`) | hand | PASS | 0.33 → 1.00 | 3.5 → 10.0 (10.0) m | 1 / 1 | 0.02 m |  |
| Hardbrücke Nord: Hardturmrampe and Sihlquai ramps at the Wipkingerbrücke (`wipkingen`) | hand | PASS | 0.45 → 0.99 | 3.2 → 6.5 (6.5) m | 15 / 14 | 0.01 m |  |
| Hohlstrasse bridge and Brauerstrasse ramp (over the Sihl line tracks) (`brauer`) | hand | PASS | 0.54 → 1.00 | 6.4 → 8.8 (8.7) m | 0 / 0 | 0.10 m |  |
| `auto_hardbrucke` | auto | no LiDAR | | | | |  |
| `auto_europabrucke` | auto | no LiDAR | | | | |  |
| `auto_sihlbrucke` | auto | no LiDAR | | | | |  |
| `auto_kornhausbrucke` | auto | no LiDAR | | | | |  |
| `auto_unnamed_m58_m123` | auto | no LiDAR | | | | |  |
| `auto_walchebrucke` | auto | no LiDAR | | | | |  |
| `auto_unnamed_m2000_18` | auto | no LiDAR | | | | |  |
| `auto_unnamed_m845_712` | auto | no LiDAR | | | | |  |
| `auto_gessnerbrucke` | auto | no LiDAR | | | | |  |
| `auto_bahnhofbrucke` | auto | no LiDAR | | | | |  |
| `auto_bandlistrasse` | auto | no LiDAR | | | | |  |
| `auto_unnamed_1069_173` | auto | no LiDAR | | | | |  |
| `auto_unnamed_m960_694` | auto | no LiDAR | | | | |  |
| `auto_militarbrucke` | auto | no LiDAR | | | | |  |
| Remisenstrasse (1 chain, 64 m) (`auto_remisenstrasse`) | auto | PASS | 0.46 → 0.94 | 3.5 → 7.0 (7.0) m | 0 / 0 | 0.07 m |  |
| `auto_pfingstweidbrucke` | auto | no LiDAR | | | | |  |
| `auto_sihlholzlibrucke` | auto | no LiDAR | | | | |  |
| `auto_kanzleistrasse` | auto | no LiDAR | | | | |  |
| Stauffacherstrasse (1 chain, 54 m) (`auto_stauffacherstrasse`) | auto | PASS | 0.31 → 0.97 | 6.4 → 21.0 (21.0) m | 0 / 0 | 0.05 m |  |
| `auto_badenerstrasse` | auto | no LiDAR | | | | |  |
| `auto_sihlhochstrasse` | auto | no LiDAR | | | | |  |
| `auto_sihlholzlibrucke_2` | auto | no LiDAR | | | | |  |
| `auto_zweierstrasse` | auto | no LiDAR | | | | |  |
| `auto_stauffacherbrucke` | auto | no LiDAR | | | | |  |
| `auto_kalkbreitestrasse` | auto | no LiDAR | | | | |  |
